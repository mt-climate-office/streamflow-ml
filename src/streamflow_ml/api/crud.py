from fastapi import HTTPException, status
from streamflow_ml.db import AsyncSession, models
from streamflow_ml.api import schemas
from sqlalchemy import select, func
from collections import defaultdict


def remap_keys(data: dict, required: list[str]) -> dict[str, str]:
    found_substrings = {key: False for key in required}

    for key in data.keys():
        for substring in required:
            if substring in key:
                if found_substrings[substring]:
                    raise HTTPException(
                        415,
                        f".geojson properties has multiple substrings with '{substring}'. Please ensure each property only contains this substring once.",
                    )
                found_substrings[substring] = data[key]

    for substring, found in found_substrings.items():
        if not found:
            raise HTTPException(
                415,
                f"'{substring}' not found in .geojson properties. Please ensure '{substring}' is contained in one of the properties.",
            )

    return found_substrings


def compress_models(
    models: list[schemas.RawReturnPredictions],
) -> schemas.ReturnPredictions:
    compressed_data = defaultdict(list)

    for model in models:
        for field_name, field_value in model.model_dump().items():
            compressed_data[field_name].append(field_value)

    return schemas.ReturnPredictions(**compressed_data)


async def read_predictions(
    predictions: schemas.GetPredictions, async_session: AsyncSession
) -> schemas.ReturnPredictions:
    async with async_session.begin() as session:
        table = models.Data if predictions.units.value == "mm" else models.CFS
        q = (
            select(table)
            .where(
                table.location.in_(predictions.locations),
                table.date <= predictions.date_end,
                table.date >= predictions.date_start,
                table.version == predictions.version.value,
            )
            .order_by(table.location, table.date)
        )

        result = await session.execute(q)
        data_rows = result.scalars().all()
        if len(data_rows) == 0:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "No data available for requested location and time range.",
            )
        data_schemas = [
            schemas.RawReturnPredictions.model_validate(row) for row in data_rows
        ]

        return compress_models(data_schemas)


async def spatial_query(
    predictions: schemas.GetPredictionsSpatially,
    async_session: AsyncSession,
    lat: float = None,
    lon: float = None
) -> schemas.ReturnLocation:
    async with async_session.begin() as session:
        if lat is None and lon is None:
            points = f"MULTIPOINT({", ".join(f"({lon} {lat})" for lat, lon in list(zip(predictions.latitude, predictions.longitude)))})"
        else:
            assert (lat is not None) and (lon is not None), "If only querying one point, both lat and lon must be specified"
            points = f"POINT({lon} {lat})"

        # First get the location_id from spatial query
        # location_subq = (
        #     select(models.Locations.id)
        #     .where(
        #         func.ST_Intersects(
        #             models.Locations.geometry, func.ST_GeomFromText(points, 4326)
        #         )
        #     )
        #     .scalar_subquery()
        # )

        # Then use that id to query the right table
        table = models.Data if predictions.units.value == "mm" else models.CFS
        stmt = (
            select(table)
            .join(models.Locations, table.location == models.Locations.id)
            .where(
                func.ST_Intersects(
                    models.Locations.geometry,
                    func.ST_SetSRID(func.ST_GeomFromText(points), 4326)
                ),
                table.date <= predictions.date_end,
                table.date >= predictions.date_start,
                table.version == predictions.version.value
            )
        )
        result = await session.execute(stmt)
        data_rows = result.scalars().all()
        if len(data_rows) == 0:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "No data available for requested location and time range.",
            )
        data_schemas = [
            schemas.RawReturnPredictions.model_validate(row) for row in data_rows
        ]

        return compress_models(data_schemas)

# This is fast but the sqlalchemy query is slow...

# SELECT l.*, d.*
# FROM flow.locations l
# JOIN flow.data d
#     ON l.id = d."location" 
# WHERE ST_Intersects(
#     l.geometry,
#     ST_GeomFromText('MULTIPOINT((-120.4194 41.0), (-119.0 40.0))', 4326)
# ) and d.date > '2025-01-01';

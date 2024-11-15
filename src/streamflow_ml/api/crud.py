from fastapi import HTTPException, status
from streamflow_ml.db import AsyncSession, models
from streamflow_ml.api import schemas
from sqlalchemy import select
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

from fastapi import HTTPException
from streamflow_ml.api import schemas
from streamflow_ml.db import basins
import polars as pl
import geopandas as gpd


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


AGGREGATIONS = {
    "min": pl.min("value").alias("min"),
    "max": pl.max("value").alias("max"),
    "mean": pl.mean("value").alias("mean"),
    "median": pl.median("value").alias("median"),
    "iqr": (pl.quantile("value", 0.75) - pl.quantile("value", 0.25)).alias("iqr"),
    "stddev": pl.std("value").alias("stddev"),
}


def calc_cfs(dat: pl.DataFrame, basins: gpd.GeoDataFrame) -> pl.DataFrame:
    query_basins = basins[basins["location"].isin(dat["location"].unique().to_list())]
    query_basins = pl.from_pandas(query_basins.drop(columns="geometry"))
    return (
        dat.join(query_basins, on="location")
        .with_columns(
            value=pl.col("value") / 86400 / 304.8 * (pl.col("area") * 10.7639)
        )
        .drop("area")
    )


async def read_predictions(
    predictions: schemas.GetPredictionsByLocations, frame: pl.LazyFrame
) -> pl.DataFrame:
    if predictions.latitude and predictions.longitude:
        points = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(
                x=predictions.longitude, y=predictions.latitude, crs="EPSG:4326"
            ),
            crs="EPSG:4326",
        )
        filtered_basins = gpd.sjoin(basins, points, how="inner", predicate="contains")
        if filtered_basins.empty:
            raise HTTPException(
                404, "No basins found containing the given latitude and longitude."
            )

        new_locs = filtered_basins["location"].values.tolist()
        predictions.locations = list(set(predictions.locations or []) | set(new_locs))

    dat = frame.filter(
        pl.col("location").is_in(predictions.locations),
        pl.col("date").le(predictions.date_end),
        pl.col("date").ge(predictions.date_start),
        pl.col("version").eq(predictions.version),
    )

    try:
        agg_funcs = [AGGREGATIONS[x.value] for x in predictions.aggregations]
        dat = dat.group_by("location", "version", "date").agg(*agg_funcs)
        dat = dat.melt(
            id_vars=["location", "version", "date"],
            value_vars=[agg_func.value for agg_func in predictions.aggregations],
            variable_name="metric",
            value_name="value",
        ).sort("location", "version", "metric", "date")
    except AttributeError:
        dat = dat.sort("location", "model_no", "version", "date")

    dat = dat.collect()
    if predictions.units.value == "cfs":
        dat = calc_cfs(dat, basins)

    return dat.with_columns(pl.col("value").round(4))

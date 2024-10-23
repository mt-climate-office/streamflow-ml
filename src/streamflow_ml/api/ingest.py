import polars as pl
from pathlib import Path

def parse_observations(data: Path | str, version: str="v1.0") -> pl.DataFrame:
    return pl.read_parquet(data).select([
        "basin_id", "time", "mm_d"
    ]).rename({
        "basin_id": "id",
        "time": "date",
        "mm_d": "value",
    }).with_columns([
        pl.lit(version).alias("version")
    ])



data = parse_observations(
    Path('/home/cbrust/data/streamflow/historical/streamflow_ml_operational_inference_huc10_historical.parquet')
)
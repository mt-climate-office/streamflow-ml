# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "polars",
#     "pyarrow",
# ]
# ///
import argparse
import polars as pl
from pathlib import Path
import pyarrow.parquet as pq
import datetime as dt


def parse_observations(data: Path | str, version: str = "v1.0", model_no: int = 0) -> pl.DataFrame:
    this_year = dt.datetime.now().date().year

    return (
        pl.read_parquet(data)
        .select(["basin_id", "time", "mm_d"])
        .rename(
            {
                "basin_id": "location",
                "time": "date",
                "mm_d": "value",
            }
        )
        .with_columns([
            pl.lit(version).alias("version"),
            pl.lit(model_no).alias("model_no"),
        ])
        .filter(
            pl.col("date") >= dt.date(this_year, 1, 1)
        )
    )

def create_hive_partition(pth: Path, out_pth: Path, version: str) -> None:
    for f in pth.iterdir():
        print(f"Processing {f.name}")
        fold = int(f.name.split("-")[-2])
        dat = parse_observations(f, version, fold)
        ar = dat.to_arrow()

        pq.write_to_dataset(
            ar, 
            out_pth,
            partition_cols=[
                "date",
                "version"
            ],
            existing_data_behavior="overwrite_or_ignore",
            basename_template=f"fold={fold:02d}-{{i}}",
        )



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir", type=str, help="Output directory for partitioned current year data.")
    args = parser.parse_args()

    create_hive_partition(
        Path("/data/ssd2/streamflow-ml-data-operational/operational-output/current-k-fold/"),
        Path(args.out_dir),
        "vPUB2025"
    )
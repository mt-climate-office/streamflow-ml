import polars as pl
from pathlib import Path
import pyarrow.parquet as pq


def parse_observations(
    data: Path | str, version: str = "v1.0", model_no: int = 0
) -> pl.DataFrame:
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
        .with_columns(
            [
                pl.lit(version).alias("version"),
                pl.lit(model_no).alias("model_no"),
            ]
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
            partition_cols=["location", "version"],
            existing_data_behavior="overwrite_or_ignore",
            basename_template=f"fold={fold:02d}-{{i}}",
        )


if __name__ == "__main__":
    import argparse


    parser = argparse.ArgumentParser(description="Partition Parquet files into Hive-style partitions.")
    parser.add_argument("pth", type=Path, help="Input directory path")
    parser.add_argument("out_pth", type=Path, help="Output directory path")
    parser.add_argument("version", type=str, help="Version string")

    args = parser.parse_args()

    create_hive_partition(
        args.pth,
        args.out_pth,
        args.version,
    )

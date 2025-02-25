import polars as pl
import geopandas as gpd


class ParquetConn:
    def __init__(self, f):
        self.f = f
        self.df = pl.scan_parquet(
            self.f,
            hive_partitioning=True,
            schema={
                "date": pl.Date,
                "value": pl.Float64,
                "model_no": pl.Int32,
                "location": pl.String,
                "version": pl.String,
            },
        )

    def __call__(self) -> pl.LazyFrame:
        return self.df


pq_conn = ParquetConn(f="/data/flow")
basins = gpd.read_file("/data/basins.geojson")
# pq_conn = ParquetConn(f="/home/cbrust/data/streamflow/flow")
# basins = gpd.read_file("/home/cbrust/data/streamflow/basins.geojson")

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


pq_location_partition = ParquetConn(f="/data/flow")
pq_date_partition = ParquetConn(f="/data/current")
basins = gpd.read_file("/data/basins.geojson")
# pq_location_partition = ParquetConn(f="/home/cbrust/data/streamflow/flow")
# pq_date_partition = ParquetConn(f="/home/cbrust/data/streamflow/current")
# basins = gpd.read_file("/home/cbrust/data/streamflow/basins.geojson")

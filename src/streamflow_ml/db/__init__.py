import polars as pl
import geopandas as gpd
import time


class ParquetConn:
    def __init__(self, f):
        self.f = f
        self.schema = {
            "date": pl.Date,
            "value": pl.Float64,
            "model_no": pl.Int32,
            "location": pl.String,
            "version": pl.String,
        }
        self.last_refresh = 0
        self.refresh_interval = 15 * 60  # 15 minutes in seconds
        self.df = self._scan_parquet()

    def _scan_parquet(self):
        self.last_refresh = time.time()
        return pl.scan_parquet(
            self.f,
            hive_partitioning=True,
            schema=self.schema
        )
    
    def __call__(self) -> pl.LazyFrame:
        if time.time() - self.last_refresh > self.refresh_interval:
            self.df = self._scan_parquet()
        return self.df


pq_location_partition = ParquetConn(f="/data/flow")
pq_date_partition = ParquetConn(f="/data/current")
basins = gpd.read_file("/data/basins.geojson")
# pq_location_partition = ParquetConn(f="/home/cbrust/data/streamflow/flow")
# pq_date_partition = ParquetConn(f="/home/cbrust/data/streamflow/current")
# basins = gpd.read_file("/home/cbrust/data/streamflow/basins.geojson")

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "asyncio",
#     "httpx",
#     "polars",
#     "tqdm",
# ]
# ///
import asyncio
import argparse
import httpx
import polars as pl
from pathlib import Path
from tqdm.asyncio import tqdm


def parse_observations(data: Path | str, version: str = "v1.0") -> pl.DataFrame:
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
            pl.col("date").cast(pl.Utf8),
            pl.lit(version).alias("version")
        ])
    )

async def post_to_api(data: pl.DataFrame, api_url: str = "http://127.0.0.1:8000/prediction", chunk_size: int = 1000):
    async with httpx.AsyncClient() as client:

        for chunk in tqdm(range(0, data.height, chunk_size), total=(data.height // chunk_size), desc="Posting chunks"):
            chunk_data = data[chunk : chunk + chunk_size]
            json_data = chunk_data.to_dicts()

            try:
                response = await client.post(api_url, json=json_data)
                response.raise_for_status()

            except httpx.HTTPStatusError as exc:
                print(f"Error response {exc.response.status_code} while posting chunk: {exc.response.text}")

def main():

    parser = argparse.ArgumentParser(description="Post observation data to an API.")
    parser.add_argument("data", type=str, help="Path to the parquet data file")
    parser.add_argument(
        "--api-url", 
        type=str, 
        default="http://127.0.0.1:8000/predictions", 
        help="API URL to post the data (default: http://127.0.0.1:8000/predictions)"
    )
    parser.add_argument(
        "--chunk-size", 
        type=int, 
        default=1000, 
        help="Number of rows to send per request (default: 1000)"
    )
    args = parser.parse_args()

    data = parse_observations(args.data)

    asyncio.run(post_to_api(data, args.api_url, args.chunk_size))

if __name__ == "__main__":
    main()
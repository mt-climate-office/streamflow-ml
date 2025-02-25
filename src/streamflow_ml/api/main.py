from typing import Annotated
from urllib.parse import parse_qs as parse_query_string
from urllib.parse import urlencode as encode_query_string

from fastapi import FastAPI, Request, Depends, status, Query, Response
from fastapi.responses import RedirectResponse
from fastapi.security.api_key import APIKeyHeader
from streamflow_ml.db import pq_conn
from streamflow_ml.api import crud, schemas
from fastapi.exceptions import HTTPException
import os
import polars as pl
from starlette.types import ASGIApp, Receive, Scope, Send


description = """
An API to deliver streamflow predicted by an ML model in ungaged basins across
the contiguous USA.
"""


SFML_KEY = os.getenv("SFML_KEY")
sfml_key_header = APIKeyHeader(name="X-SFML-KEY", auto_error=False)


class QueryStringFlatteningMiddleware:
    # Credit to: https://github.com/tiangolo/fastapi/discussions/8225#discussioncomment-5149939
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        query_string = scope.get("query_string", None).decode()
        if scope["type"] == "http" and query_string:
            parsed = parse_query_string(query_string)
            flattened = {}
            for name, values in parsed.items():
                all_values = []
                for value in values:
                    all_values.extend(value.split(","))

                flattened[name] = all_values

            # doseq: Turn lists into repeated parameters, which is better for FastAPI
            scope["query_string"] = encode_query_string(flattened, doseq=True).encode(
                "utf-8"
            )

            await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)


def authenticate_sfml(api_key: str = Depends(sfml_key_header)):
    if api_key != SFML_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-SFML-KEY header.",
            headers={"WWW-Authenticate": "Bearer"},
        )


app = FastAPI(
    title="MCO — Streamflow ML API",
    version="0.0.1",
    terms_of_service="https://climate.umt.edu/about/agreement/",
    contact={
        "name": "Colin Brust",
        "url": "https://climate.umt.edu",
        "email": "colin.brust@umt.edu",
    },
    description=description,
    root_path="/streamflow-api",
)

app.add_middleware(QueryStringFlatteningMiddleware)


@app.get("/", include_in_schema=False)
async def get_root(request: Request):
    return RedirectResponse("/streamflow-api/docs")

@app.get("/predictions", tags=["Get Streamflow Data"])
@app.get("/predictions/", include_in_schema=False)
async def get_predictions(
    predictions: Annotated[schemas.GetPredictionsByLocations, Query()],
    frame: Annotated[pl.LazyFrame, Depends(pq_conn)],
) -> schemas.ReturnPredictions:
    if (
        predictions.locations is None
        and predictions.longitude is None
        and predictions.latitude is None
    ):
        raise HTTPException(
            422,
            "Either the `locations` or `latitude` and `longitude` query parameters must be specified to retrieve data.",
        )
    data = await crud.read_predictions(predictions, frame)
    if predictions.as_csv:
        return Response(
            content=data.write_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=basins_{'_'.join(data['location'].unique().to_list())}_predictions.csv"
            },
        )

    out_dict = {col: data[col].to_list() for col in data.columns}
    return schemas.ReturnPredictions(**out_dict)


@app.get("/predictions/raw", tags=["Get Streamflow Data"])
@app.get("/predictions/raw/", include_in_schema=False)
async def get_predictions_raw(
    predictions: Annotated[schemas.GetPredictionsRaw, Query()],
    frame: Annotated[pl.LazyFrame, Depends(pq_conn)],
) -> schemas.RawReturnPredictions:
    if (
        predictions.locations is None
        and predictions.longitude is None
        and predictions.latitude is None
    ):
        raise HTTPException(
            422,
            "Either the `locations` or `latitude` and `longitude` query parameters must be specified to retrieve data.",
        )
    data = await crud.read_predictions(predictions, frame)
    if predictions.as_csv:
        return Response(
            content=data.write_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=basins_{'_'.join(data['location'].unique().to_list())}_predictions.csv"
            },
        )

    out_dict = {col: data[col].to_list() for col in data.columns}
    return schemas.RawReturnPredictions(**out_dict)


# TODO: Need to have a separate partition to do this effectively.
# @app.get("/predictions/latest")
# @app.get("/predictions/latest/", include_in_schema=False)
# async def get_latest_preds(
#     frame: Annotated[pl.LazyFrame, Depends(pq_conn)]
# ):
#     ...

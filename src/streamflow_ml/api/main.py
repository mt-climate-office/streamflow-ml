from typing import Annotated, List

from fastapi import FastAPI, Request, UploadFile, Depends, status, Query, Path
from fastapi.security.api_key import APIKeyHeader
from streamflow_ml.db import async_engine, init_db, models, AsyncSession, get_session
from streamflow_ml.api import crud, schemas
from contextlib import asynccontextmanager
from geoalchemy2.functions import ST_GeomFromGeoJSON
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.dialects.postgresql import insert
from fastapi.exceptions import HTTPException
import json
import os

description = """
An API to deliver streamflow predicted by an ML model in ungaged basins across
the contiguous USA.
"""


SFML_KEY = os.getenv("SFML_KEY")
sfml_key_header = APIKeyHeader(name="X-SFML-KEY", auto_error=False)


def authenticate_sfml(api_key: str = Depends(sfml_key_header)):
    if api_key != SFML_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-SFML-KEY header.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(async_engine, models.Base)
    yield
    await async_engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    title="MCO — Streamflow ML API",
    version="0.0.1",
    terms_of_service="https://climate.umt.edu/about/agreement/",
    contact={
        "name": "Colin Brust",
        "url": "https://climate.umt.edu",
        "email": "colin.brust@umt.edu",
    },
    root_path="/streamflow-api",
)


@app.get("/")
async def get_root(request: Request):
    return {"working": "mmhm"}


# Can post with curl -X POST "http://127.0.0.1:8000/locations" -F "file=@./streamflow_ml_operational_inference_huc10_simple.geojson"
@app.post("/locations")
@app.post("/locations/", include_in_schema=False)
async def post_locations(
    file: UploadFile,
    async_session: Annotated[AsyncSession, Depends(get_session)],
    api_key: Annotated[authenticate_sfml, Depends()],
):
    """Post a set of data to the"""
    if not file.filename.endswith(".geojson"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Invalid file type. Only .geojson files are supported.",
        )

    contents = await file.read()
    data = json.loads(contents)

    locations = []

    for feature in data["features"]:
        props = feature.get("properties")
        props = crud.remap_keys(props, ["id", "name", "group"])
        geom = feature.get("geometry")
        geom = json.dumps(geom)

        location = models.Locations(geometry=ST_GeomFromGeoJSON(geom), **props)
        locations.append(location)

    try:
        async with async_session.begin() as session:
            session.add_all(locations)
    except (SQLAlchemyError, IntegrityError) as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Error while saving locations: {str(e)}",
        )

    return {"message": f"Successfully added {len(locations)} locations."}


@app.post("/prediction")
async def post_prediction(
    prediction: schemas.CreatePredictions,
    async_session: Annotated[AsyncSession, Depends(get_session)],
    api_key: Annotated[authenticate_sfml, Depends()],
):
    try:
        async with async_session.begin() as session:
            prediction = models.Data(**prediction.__dict__)
            # merge does an insert if data don't exist, upsert if they do.
            session.merge(prediction)
            await session.commit()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{prediction} already exists.")

    return 1


@app.post("/predictions")
async def post_predictions(
    predictions: List[schemas.CreatePredictions],
    async_session: Annotated[AsyncSession, Depends(get_session)],
    api_key: Annotated[authenticate_sfml, Depends()],
):
    try:
        async with async_session.begin() as session:
            # Convert list of Pydantic objects to list of model instances
            # prediction_models = [
            #     models.Data(**prediction.__dict__) for prediction in predictions
            # ]
            stmt = insert(models.Data).values(
                [pred.model_dump() for pred in predictions]
            )
            indices = ["location", "date", "version"]
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=indices,
                set_={
                    key: stmt.excluded[key]
                    for key in models.Data.__table__.columns.keys()
                    if key not in indices
                },
            )

            await session.execute(upsert_stmt)
            await session.commit()
    except IntegrityError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Some or all of the predictions already exist."
        )

    return len(predictions)


@app.get("/predictions")
@app.get("/predictions/", include_in_schema=False)
async def get_predictions(
    predictions: Annotated[schemas.GetPredictionsLocations, Query()],
    async_session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.ReturnPredictions:
    data = await crud.read_predictions(predictions, async_session)
    return data


@app.get("/predictions/{latitude}/{longitude}")
async def get_predictions_from_point(
    latitude: Annotated[
        float,
        Path(
            title="Latitude",
            description="Latitude of the region of interest.",
            ge=24,
            le=50,
        ),
    ],
    longitude: Annotated[
        float,
        Path(
            title="Longitude",
            description="Longitude of the region of interest.",
            ge=-125.0,
            le=-66.0,
        ),
    ],
    predictions: Annotated[schemas.GetPredictions, Query()],
    async_session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.ReturnPredictions:
    return await crud.spatial_query(latitude, longitude, predictions, async_session)

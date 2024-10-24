from typing import Annotated

from fastapi import FastAPI, Request, UploadFile, Depends
from streamflow_ml.db import async_engine, init_db, models, AsyncSession, get_session
from streamflow_ml.api import crud, schemas
from contextlib import asynccontextmanager
from geoalchemy2.functions import ST_GeomFromGeoJSON
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi.exceptions import HTTPException
import json

description = """
An API to deliver streamflow predicted by an ML model in ungaged basins across
the contiguous USA.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(async_engine, models.Base)
    yield
    async_engine.dispose()


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
)


@app.get("/")
async def get_root(request: Request):
    return {"working": "mmhm"}


# Can post with curl -X POST "http://127.0.0.1:8000/locations" -F "file=@./streamflow_ml_operational_inference_huc10_simple.geojson"
@app.post("/locations")
async def post_locations(
    file: UploadFile, async_session: Annotated[AsyncSession, Depends(get_session)]
):
    """Post a set of data to the"""
    if not file.filename.endswith(".geojson"):
        raise HTTPException(
            415, "Invalid file type. Only .geojson files are supported."
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
        raise HTTPException(500, f"Error while saving locations: {str(e)}")

    return {"message": f"Successfully added {len(locations)} locations."}


@app.post("/prediction")
async def post_predictions(
    prediction: schemas.CreatePredictions,
    async_session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        async with async_session.begin() as session:
            prediction = models.Data(**prediction.__dict__)
            session.add(prediction)
            await session.commit()
    except IntegrityError:
        raise HTTPException(409, f"{prediction} already exists.")

    return 1

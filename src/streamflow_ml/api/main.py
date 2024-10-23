from fastapi import FastAPI, Request, UploadFile
from streamflow_ml.db import async_engine, init_db, models
from contextlib import asynccontextmanager

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
async def post_locations(file: UploadFile):
    return {"filename": file.filename}
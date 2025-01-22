from enum import Enum

from pydantic import BaseModel, Field, AfterValidator
from datetime import date

from typing import Any, Optional, Literal, List, Dict, Union, Annotated


class StreamflowUnits(Enum):
    MM = "mm"
    CFS = "cfs"


class Type(Enum):
    JSON = "json"
    GEOJSON = "geojson"


class Version(Enum):
    V1 = "v1.0"


class CreatePredictions(BaseModel):
    location: str
    date: date
    version: str
    value: float


class GetLocations(BaseModel):
    location: str | None = None
    type: Type = Type.GEOJSON


class ReturnLocation(BaseModel):
    location: str
    name: str
    geometry: Optional[dict[str, Any]]

    class Config:
        json_encoders = {dict: lambda v: v}


class GetPredictions(BaseModel):
    date_start: date = Field(
        date(1980, 1, 1),
        ge=date(1980, 1, 1),
        le=date(2100, 1, 1),
        description="Start date to get predictions for.",
    )
    date_end: date = Field(
        date(2100, 1, 1),
        ge=date(1980, 1, 1),
        le=date(2100, 1, 1),
        description="End date to get predictions for.",
    )
    units: StreamflowUnits = Field(
        StreamflowUnits.CFS,
        description="Units of streamflow output. Can either be cubic feet per second or millimeters.",
    )
    version: Version = Field(
        Version.V1,
        description="Model version to use. Currently, only model v1.0 exists.",
        title="Model Version",
    )


class GetPredictionsByLocations(GetPredictions):
    locations: str | list[str]


def validate_lat_lon(vals: list[float], which: Literal["latitude", "longitude"]) -> list[float]:
    if which == "latitude":
        for v in vals:
            if (v < 24) or (v > 50):
                raise ValueError("Latitude must be between 24.0 and 50.0")
        return vals
    else:
        for v in vals:
            if (v < -125) or (v > -66):
                raise ValueError("Longitude must be between -125.0 and -66.0")
        return vals

class GetPredictionsSpatially(GetPredictions):
    latitude: Annotated[list[float] | None, Field(
        None, description="Latitude of the region of interest."
    ), AfterValidator(lambda x: validate_lat_lon(x, "latitude"))]
    longitude: Annotated[list[float] | None, Field(
        None,
        title="Longitude",
        description="Longitude of the region of interest.",
    ), AfterValidator(lambda x: validate_lat_lon(x, "longitude"))]

class RawReturnPredictions(BaseModel):
    location: str
    date: date
    version: str
    value: float

    class Config:
        from_attributes = True


class ReturnPredictions(BaseModel):
    location: list[str]
    date: list[date]
    version: list[str]
    value: list[float]

    class Config:
        from_attributes = True


class Geometry(BaseModel):
    type: Literal[
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
    ]
    coordinates: Union[
        List[float],  # Point
        List[List[float]],  # LineString/MultiPoint
        List[List[List[float]]],  # Polygon/MultiLineString
        List[List[List[List[float]]]],  # MultiPolygon
    ]


class Feature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: Geometry
    properties: Optional[Dict] = Field(default_factory=dict)
    id: Optional[Union[str, int]] = None


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[Feature]

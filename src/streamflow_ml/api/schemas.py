from enum import Enum

from pydantic import BaseModel, Field
from datetime import date

from typing import Any, Optional, Literal, List, Dict, Union


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
    date_start: date = date(1980, 1, 1)
    date_end: date = date(2100, 1, 1)
    units: StreamflowUnits = StreamflowUnits.CFS
    version: Version = Version.V1


class GetPredictionsLocations(GetPredictions):
    locations: str | list[str]


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

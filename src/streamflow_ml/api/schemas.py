from enum import Enum

from pydantic import BaseModel
from datetime import date


class StreamflowUnits(Enum):
    MM = "mm"
    CFS = "cfs"


class Version(Enum):
    V1 = "v1.0"


class CreatePredictions(BaseModel):
    location: str
    date: date
    version: str
    value: float


class GetPredictions(BaseModel):
    locations: str | list[str]
    date_start: date
    date_end: date
    units: StreamflowUnits = StreamflowUnits.CFS
    version: Version = Version.V1


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

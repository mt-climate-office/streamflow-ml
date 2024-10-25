from pydantic import BaseModel
from datetime import date


class CreatePredictions(BaseModel):
    location: str
    date: date
    version: str
    value: float


class GetPredictions(BaseModel):
    locations: str | list[str]
    date_start: date
    date_end: date


class ReturnPredictions(BaseModel):
    location: str
    date: date
    version: str
    value: float

    class Config:
        from_attributes = True

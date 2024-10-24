from pydantic import BaseModel
from datetime import date


class CreatePredictions(BaseModel):
    location: str
    date: date
    version: str
    value: float

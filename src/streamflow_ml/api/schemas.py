from enum import Enum
from typing_extensions import Self

from pydantic import BaseModel, Field, AfterValidator, model_validator
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
    VPUB2025 = "vPUB2025"


class AggregationTypes(Enum):
    MIN = "min"
    MAX = "max"
    MEAN = "mean"
    MEDIAN = "median"
    STDDEV = "stddev"
    IQR = "iqr"


class CreatePredictions(BaseModel):
    location: str
    date: date
    version: str
    model_no: int
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


def validate_lat_lon(
    vals: list[float], which: Literal["latitude", "longitude"]
) -> list[float]:
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


class GetPredictionsBase(BaseModel):
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
        Version.VPUB2025,
        description="Model version to use. Currently, only model vPUB2025 exists.",
        title="Model Version",
    )
    as_csv: bool = Field(
        False,
        description="Should data be returned as a .csv (defaults to False. Data returned in json)?",
        title="As .CSV",
    )


class Locations(BaseModel):
    locations: str | list[str] = Field(
        None, description="The HUC10 ID(s) to gather data for.", title="HUC10 ID(s)"
    )
    latitude: Annotated[
        list[float] | None,
        Field(None, description="Latitude of the region of interest."),
        AfterValidator(lambda x: validate_lat_lon(x, "latitude")),
    ]
    longitude: Annotated[
        list[float] | None,
        Field(
            None,
            title="Longitude",
            description="Longitude of the region of interest.",
        ),
        AfterValidator(lambda x: validate_lat_lon(x, "longitude")),
    ]

    @model_validator(mode="after")
    def validate_lat_lon_length(self) -> Self:
        if self.latitude and self.longitude is None:
            raise ValueError(
                "Longitude not specified. If latitude is specified, longitude must also be specified."
            )

        if self.longitude and self.latitude is None:
            raise ValueError(
                "Latitude not specified. If longitude is specified, latitude must also be specified."
            )

        try:
            if len(self.longitude) != len(self.latitude):
                raise ValueError(
                    "Latitude and Longitude are not the same length. The two query parameters must be the same length."
                )
        except TypeError:
            ...

        return self


class Aggregations(BaseModel):
    aggregations: list[AggregationTypes] = Field(
        default_factory=lambda: [AggregationTypes.MEDIAN],
        description="The aggregation(s) to perform on the ensemble of models. If set to None, the raw results from the whole suite of models will be returned",
        title="Aggregation Functions",
    )


class GetLatestPredictions(Aggregations):
    as_csv: bool = Field(
        False,
        description="Should data be returned as a .csv (defaults to False. Data returned in json)?",
        title="As .CSV",
    )

class GetPredictionsRaw(GetPredictionsBase, Locations): ...


class GetPredictionsByLocations(GetPredictionsBase, Locations, Aggregations): ...


class RawReturnPredictions(BaseModel):
    location: list[str]
    date: list[date]
    version: list[str]
    model_no: list[int]
    value: list[float]

    class Config:
        from_attributes = True


class ReturnPredictions(BaseModel):
    location: list[str]
    date: list[date]
    version: list[str]
    metric: list[str]
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

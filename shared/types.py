from pydantic import BaseModel


class GeodataObservation(BaseModel):
    lon: float
    lat: float
    value: float

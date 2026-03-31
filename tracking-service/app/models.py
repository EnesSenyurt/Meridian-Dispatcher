from pydantic import BaseModel

class LocationUpdate(BaseModel):
    lat: float
    lng: float
    status: str

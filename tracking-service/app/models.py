from pydantic import BaseModel, Field

class LocationUpdate(BaseModel):
    lat: float
    lng: float
    status: str

class LocationResponse(BaseModel):
    model_config = {"populate_by_name": True}
    lat: float
    lng: float
    status: str
    links: dict = Field(default_factory=dict, alias="_links")

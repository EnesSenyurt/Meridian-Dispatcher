import json
from fastapi import HTTPException
from .repository import BaseTrackingRepository
from .models import LocationUpdate, LocationResponse

class TrackingService:
    def __init__(self, repository: BaseTrackingRepository):
        self.repository = repository

    async def update_location(self, tracking_id: str, location: LocationUpdate) -> dict:
        loc_data = json.dumps(location.model_dump())
        result = await self.repository.save_location(tracking_id, loc_data)
        if result == "OK" or result is True or result:
            return {
                "message": "Location updated successfully",
                "_links": {
                    "self": f"/tracking/{tracking_id}/location",
                    "delivery": f"/delivery/{tracking_id}"
                }
            }
        raise HTTPException(status_code=500, detail="Could not save location")

    async def get_location(self, tracking_id: str) -> LocationResponse:
        loc_data = await self.repository.get_location(tracking_id)
        if not loc_data:
            raise HTTPException(status_code=404, detail="Location not found")
            
        data = json.loads(loc_data)
        return LocationResponse(
            lat=data["lat"],
            lng=data["lng"],
            status=data["status"],
            links={
                "self": f"/tracking/{tracking_id}/location",
                "delivery": f"/delivery/{tracking_id}"
            }
        )

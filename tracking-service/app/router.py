import json
from fastapi import APIRouter, HTTPException
from .database import db
from .models import LocationUpdate

router = APIRouter(prefix="/tracking", tags=["tracking"])

@router.post("/{tracking_id}/location", status_code=200)
async def update_location(tracking_id: str, location: LocationUpdate):
    loc_data = json.dumps(location.model_dump())
    result = await db.execute("set", f"loc_{tracking_id}", loc_data)
    # Redis typically returns "OK" for set, mocked as "OK" or True
    if result == "OK" or result is True or result:
        return {"message": "Location updated successfully"}
    raise HTTPException(status_code=500, detail="Could not save location")

@router.get("/{tracking_id}/location", status_code=200)
async def get_location(tracking_id: str):
    loc_data = await db.execute("get", f"loc_{tracking_id}")
    if not loc_data:
        raise HTTPException(status_code=404, detail="Location not found")
    return json.loads(loc_data)

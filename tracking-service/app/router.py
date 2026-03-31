from fastapi import APIRouter, Depends
from .models import LocationUpdate, LocationResponse
from .repository import BaseTrackingRepository, get_tracking_repository
from .service import TrackingService

router = APIRouter(prefix="/tracking", tags=["tracking"])

def get_tracking_service(repo: BaseTrackingRepository = Depends(get_tracking_repository)) -> TrackingService:
    return TrackingService(repo)

@router.post("/{tracking_id}/location", status_code=200)
async def update_location(tracking_id: str, location: LocationUpdate, service: TrackingService = Depends(get_tracking_service)):
    return await service.update_location(tracking_id, location)

@router.get("/{tracking_id}/location", status_code=200, response_model=LocationResponse)
async def get_location(tracking_id: str, service: TrackingService = Depends(get_tracking_service)):
    return await service.get_location(tracking_id)

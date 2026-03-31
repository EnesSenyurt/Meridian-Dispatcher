from fastapi import APIRouter, Depends
from .models import DeliveryCreate, DeliveryResponse, DeliveryUpdate
from .repository import BaseDeliveryRepository, get_delivery_repository
from .service import DeliveryService

router = APIRouter(prefix="/delivery", tags=["delivery"])

def get_delivery_service(repo: BaseDeliveryRepository = Depends(get_delivery_repository)) -> DeliveryService:
    return DeliveryService(repo)

@router.post("", status_code=201, response_model=DeliveryResponse)
async def create_delivery(body: DeliveryCreate, service: DeliveryService = Depends(get_delivery_service)):
    return await service.create_delivery(body)

@router.get("", status_code=200)
async def list_deliveries(service: DeliveryService = Depends(get_delivery_service)):
    return await service.list_deliveries()

@router.get("/{delivery_id}", status_code=200, response_model=DeliveryResponse)
async def get_delivery(delivery_id: str, service: DeliveryService = Depends(get_delivery_service)):
    return await service.get_delivery(delivery_id)

@router.put("/{delivery_id}", status_code=200, response_model=DeliveryResponse)
async def update_delivery(delivery_id: str, body: DeliveryUpdate, service: DeliveryService = Depends(get_delivery_service)):
    return await service.update_delivery(delivery_id, body)

@router.delete("/{delivery_id}", status_code=204)
async def delete_delivery(delivery_id: str, service: DeliveryService = Depends(get_delivery_service)):
    return await service.delete_delivery(delivery_id)

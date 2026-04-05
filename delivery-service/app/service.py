from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from .repository import BaseDeliveryRepository
from .models import DeliveryCreate, DeliveryUpdate, DeliveryResponse

class DeliveryService:
    def __init__(self, repository: BaseDeliveryRepository):
        self.repository = repository

    def _parse_id(self, delivery_id: str) -> ObjectId:
        try:
            return ObjectId(delivery_id)
        except (InvalidId, Exception):
            raise HTTPException(status_code=400, detail="Invalid delivery ID format")

    def _serialize(self, doc: dict) -> DeliveryResponse:
        did = str(doc["_id"])
        return DeliveryResponse(
            id=did,
            sender_id=doc["sender_id"],
            recipient_name=doc["recipient_name"],
            recipient_address=doc["recipient_address"],
            recipient_phone=doc["recipient_phone"],
            package_description=doc["package_description"],
            status=doc["status"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            links={
                "self": f"/delivery/{did}",
                "collection": "/delivery",
                "update": f"/delivery/{did}",
                "delete": f"/delivery/{did}",
                "tracking": f"/tracking/{did}/location"
            }
        )

    async def create_delivery(self, body: DeliveryCreate) -> DeliveryResponse:
        now = datetime.now(timezone.utc)
        doc = {
            **body.model_dump(),
            "created_at": now,
            "updated_at": now,
        }
        result = await self.repository.create_delivery(doc)
        doc["_id"] = result.inserted_id
        return self._serialize(doc)

    async def list_deliveries(self, limit: int = 20, skip: int = 0) -> list[DeliveryResponse]:
        docs = await self.repository.get_deliveries(limit=limit, skip=skip)
        return [self._serialize(d) for d in docs]

    async def get_delivery(self, delivery_id: str) -> DeliveryResponse:
        oid = self._parse_id(delivery_id)
        doc = await self.repository.get_delivery_by_id(oid)
        if not doc:
            raise HTTPException(status_code=404, detail="Delivery not found")
        return self._serialize(doc)

    async def update_delivery(self, delivery_id: str, body: DeliveryUpdate) -> DeliveryResponse:
        oid = self._parse_id(delivery_id)
        changes = {k: v for k, v in body.model_dump().items() if v is not None}
        if not changes:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        changes["updated_at"] = datetime.now(timezone.utc)

        result = await self.repository.update_delivery(oid, changes)
        if not result:
            raise HTTPException(status_code=404, detail="Delivery not found")
        return self._serialize(result)

    async def delete_delivery(self, delivery_id: str) -> None:
        oid = self._parse_id(delivery_id)
        deleted_count = await self.repository.delete_delivery(oid)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Delivery not found")

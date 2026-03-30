from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from .database import db
from .models import DeliveryCreate, DeliveryResponse, DeliveryUpdate

router = APIRouter(prefix="/delivery", tags=["delivery"])

COLLECTION = "deliveries"


def _serialize(doc: dict) -> DeliveryResponse:
    return DeliveryResponse(
        id=str(doc["_id"]),
        sender_id=doc["sender_id"],
        recipient_name=doc["recipient_name"],
        recipient_address=doc["recipient_address"],
        recipient_phone=doc["recipient_phone"],
        package_description=doc["package_description"],
        status=doc["status"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _parse_id(delivery_id: str) -> ObjectId:
    try:
        return ObjectId(delivery_id)
    except (InvalidId, Exception):
        raise HTTPException(status_code=400, detail="Invalid delivery ID format")


@router.post("", status_code=201, response_model=DeliveryResponse)
async def create_delivery(body: DeliveryCreate):
    now = datetime.now(timezone.utc)
    doc = {
        **body.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    result = await db.execute(COLLECTION, "insert_one", doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


@router.get("", status_code=200)
async def list_deliveries():
    cursor = await db.execute(COLLECTION, "find", {})
    docs = await cursor.to_list(length=1000)
    return [_serialize(doc) for doc in docs]


@router.get("/{delivery_id}", status_code=200, response_model=DeliveryResponse)
async def get_delivery(delivery_id: str):
    oid = _parse_id(delivery_id)
    doc = await db.execute(COLLECTION, "find_one", {"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return _serialize(doc)


@router.put("/{delivery_id}", status_code=200, response_model=DeliveryResponse)
async def update_delivery(delivery_id: str, body: DeliveryUpdate):
    oid = _parse_id(delivery_id)
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    if not changes:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    changes["updated_at"] = datetime.now(timezone.utc)

    result = await db.execute(
        COLLECTION,
        "find_one_and_update",
        {"_id": oid},
        {"$set": changes},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return _serialize(result)


@router.delete("/{delivery_id}", status_code=204)
async def delete_delivery(delivery_id: str):
    oid = _parse_id(delivery_id)
    result = await db.execute(COLLECTION, "delete_one", {"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Delivery not found")

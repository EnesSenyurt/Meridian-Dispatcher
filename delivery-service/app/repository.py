from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from bson import ObjectId
from .database import db

class BaseDeliveryRepository(ABC):
    @abstractmethod
    async def create_delivery(self, doc: dict) -> Any:
        pass

    @abstractmethod
    async def get_deliveries(self, limit: int = 20, skip: int = 0) -> List[dict]:
        pass

    @abstractmethod
    async def get_delivery_by_id(self, oid: ObjectId) -> Optional[dict]:
        pass

    @abstractmethod
    async def update_delivery(self, oid: ObjectId, changes: dict) -> Optional[dict]:
        pass

    @abstractmethod
    async def delete_delivery(self, oid: ObjectId) -> int:
        pass

class MongoDeliveryRepository(BaseDeliveryRepository):
    COLLECTION = "deliveries"

    async def create_delivery(self, doc: dict) -> Any:
        return await db.execute(self.COLLECTION, "insert_one", doc)

    async def get_deliveries(self, limit: int = 20, skip: int = 0) -> List[dict]:
        cursor = db.db[self.COLLECTION].find({}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_delivery_by_id(self, oid: ObjectId) -> Optional[dict]:
        return await db.execute(self.COLLECTION, "find_one", {"_id": oid})

    async def update_delivery(self, oid: ObjectId, changes: dict) -> Optional[dict]:
        return await db.execute(
            self.COLLECTION,
            "find_one_and_update",
            {"_id": oid},
            {"$set": changes},
            return_document=True,
        )

    async def delete_delivery(self, oid: ObjectId) -> int:
        result = await db.execute(self.COLLECTION, "delete_one", {"_id": oid})
        return result.deleted_count

def get_delivery_repository() -> BaseDeliveryRepository:
    return MongoDeliveryRepository()

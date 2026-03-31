from abc import ABC, abstractmethod
from typing import Optional, Any
from .database import db

class BaseTrackingRepository(ABC):
    @abstractmethod
    async def save_location(self, tracking_id: str, location_json: str) -> Any:
        pass

    @abstractmethod
    async def get_location(self, tracking_id: str) -> Optional[str]:
        pass

class RedisTrackingRepository(BaseTrackingRepository):
    async def save_location(self, tracking_id: str, location_json: str) -> Any:
        return await db.execute("set", f"loc_{tracking_id}", location_json)

    async def get_location(self, tracking_id: str) -> Optional[str]:
        return await db.execute("get", f"loc_{tracking_id}")

def get_tracking_repository() -> BaseTrackingRepository:
    return RedisTrackingRepository()

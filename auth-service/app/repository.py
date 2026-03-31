from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .database import db

class BaseUserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_user(self, user_doc: Dict[str, Any]) -> Any:
        pass

class MongoUserRepository(BaseUserRepository):
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await db.execute("users", "find_one", {"email": email})

    async def create_user(self, user_doc: Dict[str, Any]) -> Any:
        return await db.execute("users", "insert_one", user_doc)

def get_user_repository() -> BaseUserRepository:
    return MongoUserRepository()

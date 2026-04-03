from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorClient
import os

class AbstractDatabaseAdapter(ABC):
    @abstractmethod
    async def connect(self):
        pass
        
    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def execute(self, collection: str, operation: str, *args, **kwargs):
        pass

class MongoDBAdapter(AbstractDatabaseAdapter):
    def __init__(self, url: str = "mongodb://localhost:27017", db_name: str = "delivery_db"):
        self.url = os.getenv("MONGO_URL", url)
        self.db_name = os.getenv("MONGO_DB", db_name)
        self.client = None
        self.db = None

    async def connect(self):
        if not self.client:
            self.client = AsyncIOMotorClient(self.url)
            self.db = self.client[self.db_name]

    async def disconnect(self):
        if self.client:
            self.client.close()

    async def execute(self, collection: str, operation: str, *args, **kwargs):
        if not self.client:
            await self.connect()
        col = self.db[collection]
        method = getattr(col, operation)
        
        # 'find' ve 'aggregate' gibi metodlar coroutine değil, direkt cursor döner
        if operation in ("find", "aggregate"):
            return method(*args, **kwargs)
            
        return await method(*args, **kwargs)

db = MongoDBAdapter()

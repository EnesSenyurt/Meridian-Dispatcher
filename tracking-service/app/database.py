from abc import ABC, abstractmethod
import redis.asyncio as redis
import os

class AbstractDatabaseAdapter(ABC):
    @abstractmethod
    async def connect(self):
        pass
        
    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def execute(self, command: str, *args, **kwargs):
        pass

class RedisAdapter(AbstractDatabaseAdapter):
    def __init__(self, url: str = "redis://localhost:6379/0"):
        self.url = os.getenv("REDIS_URL", url)
        self.client = None

    async def connect(self):
        if not self.client:
            self.client = redis.from_url(self.url, decode_responses=True)

    async def disconnect(self):
        if self.client:
            await self.client.close()

    async def execute(self, command: str, *args, **kwargs):
        if not self.client:
            await self.connect()
        method = getattr(self.client, command)
        return await method(*args, **kwargs)

db = RedisAdapter()

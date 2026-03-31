import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.database import RedisAdapter

@pytest.mark.asyncio
async def test_redis_adapter_connection():
    with patch("app.database.redis.from_url") as mock_redis:
        mock_redis.return_value = AsyncMock()
        adapter = RedisAdapter(url="redis://fake")
        await adapter.connect()
        assert adapter.client is not None
        mock_redis.assert_called_once_with("redis://fake", decode_responses=True)

@pytest.mark.asyncio
async def test_redis_adapter_execution():
    with patch("app.database.redis.from_url") as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        
        mock_operation = AsyncMock(return_value="OK")
        setattr(mock_client, "set", mock_operation)
        
        adapter = RedisAdapter(url="redis://fake")
        result = await adapter.execute("set", "loc_1", "40.1,29.1")
        
        assert result == "OK"
        mock_operation.assert_called_once_with("loc_1", "40.1,29.1")

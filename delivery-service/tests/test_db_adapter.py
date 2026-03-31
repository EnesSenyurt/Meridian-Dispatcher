import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.database import MongoDBAdapter

@pytest.mark.asyncio
async def test_mongodb_adapter_connection():
    with patch("app.database.AsyncIOMotorClient") as mock_motor:
        mock_motor.return_value = AsyncMock()
        adapter = MongoDBAdapter(url="mongodb://fake", db_name="test_db")
        await adapter.connect()
        assert adapter.client is not None
        mock_motor.assert_called_once_with("mongodb://fake")

@pytest.mark.asyncio
async def test_mongodb_adapter_execution():
    with patch("app.database.AsyncIOMotorClient") as mock_motor:
        mock_client = AsyncMock()
        mock_motor.return_value = mock_client
        mock_db = MagicMock()
        mock_col = MagicMock()
        
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_col
        
        mock_operation = AsyncMock(return_value={"inserted_id": "123"})
        setattr(mock_col, "insert_one", mock_operation)
        
        adapter = MongoDBAdapter(url="mongodb://fake", db_name="test_db")
        result = await adapter.execute("deliveries", "insert_one", {"pkg": "box"})
        
        assert result == {"inserted_id": "123"}
        mock_operation.assert_called_once_with({"pkg": "box"})

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from swiftatlas.clients.mongo_client import MongoMotorClient


@pytest.fixture
def mock_collection():
    """Fixture for a mocked collection object."""
    collection = AsyncMock()
    collection.find = MagicMock(spec=callable, name="find_mock")
    return collection


@pytest.fixture
def mock_db(mock_collection):
    """Fixture for a mocked database object that returns the mock_collection."""
    db = MagicMock()
    db.__getitem__.return_value = mock_collection
    return db


@pytest.fixture
def mongo_client(mock_db):
    return MongoMotorClient(mongo_db=mock_db, collection_name="test_collection")


@pytest.mark.asyncio
async def test_find(mongo_client, mock_collection):
    query = {"key": "value"}
    mock_cursor = MagicMock()
    mock_collection.find.return_value = mock_cursor
    result = await mongo_client.find(query)
    mock_collection.find.assert_called_once_with(query)
    assert result == mock_cursor


@pytest.mark.asyncio
async def test_put_item(mongo_client, mock_collection):
    item = {"_id": ObjectId(), "key": "value"}
    mock_result = MagicMock()
    mock_collection.insert_one.return_value = mock_result
    result = await mongo_client.put_item(item)
    mock_collection.insert_one.assert_awaited_once_with(item)
    assert result == mock_result


@pytest.mark.asyncio
async def test_get_item(mongo_client, mock_collection):
    query = {"key": "value"}
    mock_item = {"_id": ObjectId(), "key": "value"}
    mock_collection.find_one.return_value = mock_item
    result = await mongo_client.get_item(query)
    mock_collection.find_one.assert_awaited_once_with(query)
    assert result == mock_item


@pytest.mark.asyncio
async def test_update_item(mongo_client, mock_collection):
    query = {"key": "value"}
    update = {"$set": {"new_key": "new_value"}}
    mock_result = MagicMock()
    mock_collection.update_one.return_value = mock_result
    result = await mongo_client.update_item(query, update)
    mock_collection.update_one.assert_awaited_once_with(query, update)
    assert result == mock_result


@pytest.mark.asyncio
@patch("swiftatlas.clients.mongo_client.ObjectId", return_value="mock_object_id")
async def test_replace_item(mock_objectid, mongo_client, mock_collection):
    obj_id_str = "some_object_id_string"
    item = {"key": "new_value"}
    mock_result = MagicMock()
    mock_collection.replace_one.return_value = mock_result
    result = await mongo_client.replace_item(obj_id_str, item)
    mock_objectid.assert_called_once_with(obj_id_str)
    expected_query = {"_id": "mock_object_id"}
    mock_collection.replace_one.assert_awaited_once_with(expected_query, item)
    assert result == mock_result


@pytest.mark.asyncio
async def test_delete_item(mongo_client, mock_collection):
    query = {"key": "value"}
    mock_result = MagicMock()
    mock_collection.delete_one.return_value = mock_result
    result = await mongo_client.delete_item(query)
    mock_collection.delete_one.assert_awaited_once_with(query)
    assert result == mock_result


@pytest.mark.asyncio
async def test_scan(mongo_client, mock_collection):
    mock_cursor = MagicMock()
    mock_collection.find.return_value = mock_cursor
    result = await mongo_client.scan()
    mock_collection.find.assert_called_once_with({})
    assert result == mock_cursor

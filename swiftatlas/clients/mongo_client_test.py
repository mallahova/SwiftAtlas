import pytest
import pytest_asyncio
from bson import ObjectId
import motor.motor_asyncio
from swiftatlas.clients.mongo_client import MongoMotorClient
from swiftatlas.settings import MONGODB_URL

TEST_COLLECTION = "test_items"
TEST_DB_NAME = "swift_codes_db_test"


@pytest_asyncio.fixture(scope="function")
async def test_mongo_client():
    motor_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
    test_db = motor_client[TEST_DB_NAME]
    client = MongoMotorClient(test_db, TEST_COLLECTION)
    await test_db[TEST_COLLECTION].delete_many({})
    yield client
    motor_client.close()


@pytest.mark.asyncio
async def test_put_item(test_mongo_client: MongoMotorClient):
    item = {"name": "test_item", "value": 123}
    result = await test_mongo_client.put_item(item)
    assert result.inserted_id is not None
    inserted_item = await test_mongo_client.db[TEST_COLLECTION].find_one(
        {"_id": result.inserted_id}
    )
    assert inserted_item is not None
    assert inserted_item["name"] == "test_item"


@pytest.mark.asyncio
async def test_put_and_get_item(test_mongo_client: MongoMotorClient):
    """Test putting an item and then retrieving it."""
    item_to_insert = {"name": "put_and_get", "value": 789}
    insert_result = await test_mongo_client.put_item(item_to_insert)
    assert insert_result.inserted_id is not None

    retrieved_item = await test_mongo_client.get_item(
        {"_id": insert_result.inserted_id}
    )
    assert retrieved_item is not None
    assert retrieved_item["name"] == "put_and_get"
    assert retrieved_item["value"] == 789
    # Ensure the _id matches and is of the correct type
    assert retrieved_item["_id"] == insert_result.inserted_id
    assert isinstance(retrieved_item["_id"], ObjectId)


@pytest.mark.asyncio
async def test_get_item(test_mongo_client: MongoMotorClient):
    item = {"name": "get_me", "value": 456}
    insert_result = await test_mongo_client.db[TEST_COLLECTION].insert_one(item)
    retrieved_item = await test_mongo_client.get_item(
        {"_id": insert_result.inserted_id}
    )
    assert retrieved_item is not None
    assert retrieved_item["name"] == "get_me"
    assert retrieved_item["value"] == 456


@pytest.mark.asyncio
async def test_find(test_mongo_client: MongoMotorClient):
    await test_mongo_client.db[TEST_COLLECTION].insert_many(
        [
            {"name": "find_me", "category": "A"},
            {"name": "find_me_too", "category": "A"},
            {"name": "dont_find_me", "category": "B"},
        ]
    )
    cursor = test_mongo_client.find({"category": "A"})
    results = await cursor.to_list(length=100)
    assert len(results) == 2
    assert all(item["category"] == "A" for item in results)


@pytest.mark.asyncio
async def test_update_item(test_mongo_client: MongoMotorClient):
    item = {"name": "update_me", "value": 1}
    insert_result = await test_mongo_client.db[TEST_COLLECTION].insert_one(item)
    update_query = {"_id": insert_result.inserted_id}
    update_data = {"$set": {"value": 2, "updated": True}}
    result = await test_mongo_client.update_item(update_query, update_data)
    assert result.modified_count == 1
    updated_item = await test_mongo_client.db[TEST_COLLECTION].find_one(update_query)
    assert updated_item is not None
    assert updated_item["value"] == 2
    assert updated_item["updated"] is True


@pytest.mark.asyncio
async def test_replace_item(test_mongo_client: MongoMotorClient):
    item = {"name": "replace_me", "value": 1}
    insert_result = await test_mongo_client.db[TEST_COLLECTION].insert_one(item)
    obj_id_str = str(insert_result.inserted_id)
    new_item = {"name": "replaced_item", "new_value": 999}
    result = await test_mongo_client.replace_item(obj_id_str, new_item)
    assert result.modified_count == 1
    replaced_item = await test_mongo_client.db[TEST_COLLECTION].find_one(
        {"_id": insert_result.inserted_id}
    )
    assert replaced_item is not None
    assert replaced_item["name"] == "replaced_item"
    assert replaced_item["new_value"] == 999
    assert "value" not in replaced_item


@pytest.mark.asyncio
async def test_delete_item(test_mongo_client: MongoMotorClient):
    item = {"name": "delete_me", "value": 1}
    insert_result = await test_mongo_client.db[TEST_COLLECTION].insert_one(item)
    delete_query = {"_id": insert_result.inserted_id}
    result = await test_mongo_client.delete_item(delete_query)
    assert result.deleted_count == 1
    deleted_item = await test_mongo_client.db[TEST_COLLECTION].find_one(delete_query)
    assert deleted_item is None


@pytest.mark.asyncio
async def test_scan(test_mongo_client: MongoMotorClient):
    await test_mongo_client.db[TEST_COLLECTION].insert_many(
        [
            {"name": "item1"},
            {"name": "item2"},
            {"name": "item3"},
        ]
    )
    cursor = await test_mongo_client.scan()
    results = await cursor.to_list(length=100)
    assert len(results) == 3
    names = {item["name"] for item in results}
    assert names == {"item1", "item2", "item3"}


@pytest.mark.asyncio
async def test_get_item_not_found(test_mongo_client: MongoMotorClient):
    non_existent_id = ObjectId()
    retrieved_item = await test_mongo_client.get_item({"_id": non_existent_id})
    assert retrieved_item is None


@pytest.mark.asyncio
async def test_update_item_not_found(test_mongo_client: MongoMotorClient):
    non_existent_id = ObjectId()
    update_query = {"_id": non_existent_id}
    update_data = {"$set": {"value": 2}}
    result = await test_mongo_client.update_item(update_query, update_data)
    assert result.modified_count == 0
    assert result.matched_count == 0


@pytest.mark.asyncio
async def test_replace_item_not_found(test_mongo_client: MongoMotorClient):
    non_existent_id_str = str(ObjectId())
    new_item = {"name": "replaced_item"}
    result = await test_mongo_client.replace_item(non_existent_id_str, new_item)
    assert result.modified_count == 0
    assert result.matched_count == 0


@pytest.mark.asyncio
async def test_delete_item_not_found(test_mongo_client: MongoMotorClient):
    non_existent_id = ObjectId()
    delete_query = {"_id": non_existent_id}
    result = await test_mongo_client.delete_item(delete_query)
    assert result.deleted_count == 0

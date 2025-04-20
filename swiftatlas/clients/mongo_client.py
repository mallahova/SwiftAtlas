import logging
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


logger = logging.getLogger(__name__)


class MongoMotorClient:

    def __init__(self, mongo_db: AsyncIOMotorDatabase, collection_name: str):
        self.db = mongo_db
        self.collection = collection_name

    async def find(self, query: dict):
        return self.db[self.collection].find(query)

    async def put_item(self, item: dict):
        return await self.db[self.collection].insert_one(item)

    async def get_item(self, query: dict):
        return await self.db[self.collection].find_one(query)

    async def update_item(self, query: dict, update: dict):
        return await self.db[self.collection].update_one(query, update)

    async def replace_item(self, obj_id: str, item: dict):
        return await self.db[self.collection].replace_one(
            {"_id": ObjectId(obj_id)}, item
        )

    async def delete_item(self, query: dict):
        return await self.db[self.collection].delete_one(query)

    async def scan(self):
        # Pass empty dict to find all documents
        return self.db[self.collection].find({})

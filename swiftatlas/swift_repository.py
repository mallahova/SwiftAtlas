import logging

from swiftatlas.swift_schemas import (
    SwiftCodeBase,
    SwiftCodeHeadquarter,
    SwiftCodeWithBranches,
    CountrySwiftCodes,
)
from swiftatlas.mongo_client import MongoMotorClient

logger = logging.getLogger(__name__)


class SwiftRepository:
    def __init__(self, db):
        self.client = MongoMotorClient(db, "swift_codes")

    async def create_swift(self, swift: SwiftCodeHeadquarter):
        if old_swift := await self.get_swift({"swiftCode": swift.swiftCode}):
            return old_swift

        return await self.client.put_item(swift.model_dump())

    async def get_swift_with_branches(self, swift_code: str) -> SwiftCodeWithBranches:
        swift_dict = await self.client.get_item({"swiftCode": swift_code})
        if not swift_dict:
            return None  # Let the API layer raise 404

        if swift_dict.get("isHeadquarter"):
            cursor = await self.client.find_cursor(
                {"bankName": swift_dict["bankName"], "isHeadquarter": False}
            )
            branches = [SwiftCodeBase.model_validate(b) async for b in cursor]
            return SwiftCodeWithBranches(**swift_dict, branches=branches)

        return SwiftCodeWithBranches(**swift_dict)

    async def get_swift(self, query):
        res = await self.client.get_item(query)
        logger.info(f"Got swift: {res}")
        return SwiftCodeHeadquarter.model_validate(res)

    async def update_swift(self, query: dict, update):
        return await self.client.update_item(query, update)

    async def delete_swift(self, query):
        return await self.client.delete_item(query)

    async def get_all_swifts(self) -> list[SwiftCodeHeadquarter]:
        return [
            SwiftCodeHeadquarter.model_validate(swift)
            async for swift in await self.client.scan()
        ]

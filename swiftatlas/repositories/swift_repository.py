import logging

from swiftatlas.schemas.swift_schemas import (
    SwiftCodeBase,
    SwiftCodeDetailed,
    SwiftCodeHeadquarterGroup,
    SwiftCodeCountryGroup,
)
from swiftatlas.clients.mongo_client import MongoMotorClient

logger = logging.getLogger(__name__)


class SwiftRepository:

    def __init__(self, db: MongoMotorClient):
        self.client = db

    async def create_swift(self, swift: SwiftCodeDetailed):
        if await self.get_swift({"swiftCode": swift.swiftCode}):
            return False
        swift_dict = swift.model_dump()
        swift_dict["swiftCodePrefix8"] = swift.swiftCode[:8]
        return await self.client.put_item(swift_dict)

    async def get_swift(self, query):
        res = await self.client.get_item(query)
        return res

    async def get_swift_with_branches(
        self, swift_code: str
    ) -> SwiftCodeHeadquarterGroup:
        swift_dict = await self.get_swift({"swiftCode": swift_code})
        if not swift_dict:
            return None

        if swift_dict.get("isHeadquarter"):
            cursor = self.client.find(
                {
                    "swiftCodePrefix8": swift_dict["swiftCode"][:8],
                    "isHeadquarter": False,
                }
            )
            branches = []
            async for b in cursor:
                branches.append(SwiftCodeBase.model_validate(b))
            return SwiftCodeHeadquarterGroup(**swift_dict, branches=branches)

        return SwiftCodeDetailed(**swift_dict)

    async def get_swifts_by_country(
        self, country_iso2_code: str
    ) -> SwiftCodeCountryGroup | None:
        cursor = self.client.find({"countryISO2": country_iso2_code})
        swift_codes = []

        # Process the first item separately to get country name
        try:
            first_swift_doc = await anext(cursor)
            first_swift_base = SwiftCodeBase.model_validate(first_swift_doc)
            swift_codes.append(first_swift_base)
            country_name = first_swift_doc.get("countryName")

        except StopAsyncIteration:
            logger.info(f"No SWIFT codes found for country: {country_iso2_code}")
            return None

        # Process remaining items
        async for s in cursor:
            swift_base = SwiftCodeBase.model_validate(s)
            swift_codes.append(swift_base)

        return SwiftCodeCountryGroup(
            countryISO2=country_iso2_code,
            countryName=country_name,
            swiftCodes=swift_codes,
        )

    async def update_swift(self, query: dict, update):
        return await self.client.update_item(query, update)

    async def delete_swift(self, query):
        return await self.client.delete_item(query)

import sys
import pandas as pd
import asyncio
import logging
import argparse
from swiftatlas import settings

from swiftatlas.schemas.swift_schemas import SwiftCodeDetailed
from motor.motor_asyncio import AsyncIOMotorClient
from swiftatlas.repositories.swift_repository import SwiftRepository
from swiftatlas.clients.mongo_client import MongoMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def import_data(file_path: str):
    try:
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongodb = mongodb_client[settings.MONGODB_DB_NAME]
        swift_repo = SwiftRepository(MongoMotorClient(mongodb, "swift_codes"))

        df = pd.read_excel(file_path)
        df.drop(columns=["CODE TYPE", "TOWN NAME", "TIME ZONE"], inplace=True)
        df.rename(
            columns={
                "ADDRESS": "address",
                "NAME": "bankName",
                "COUNTRY ISO2 CODE": "countryISO2",
                "COUNTRY NAME": "countryName",
                "SWIFT CODE": "swiftCode",
            },
            inplace=True,
        )
        df["isHeadquarter"] = df["swiftCode"].apply(
            lambda x: x[8:11] == "XXX" if isinstance(x, str) and len(x) >= 11 else False
        )

        inserted_count = 0
        for _, row in df.iterrows():
            swift_code = SwiftCodeDetailed(**row.to_dict())
            result = await swift_repo.create_swift(swift_code)
            if result:
                inserted_count += 1

        logger.info(
            f"Inserted {inserted_count} swift codes into 'swift_codes_db.swift_codes'"
        )

    except Exception as e:
        logger.error(f"Error importing data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import SWIFT code data from an Excel file."
    )
    parser.add_argument(
        "--file-path",
        type=str,
        help="Path to the Excel file containing SWIFT codes.",
        default="swiftatlas/data/Interns_2025_SWIFT_CODES.xlsx",
    )
    args = parser.parse_args()

    asyncio.run(import_data(args.file_path))

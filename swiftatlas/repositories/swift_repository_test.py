import pytest
from swiftatlas.repositories.swift_repository import SwiftRepository
from swiftatlas.clients.mongo_client import MongoMotorClient
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mongo_client():
    return MagicMock(spec=MongoMotorClient)


@pytest.fixture
def swift_repository(mongo_client):
    return SwiftRepository(db=mongo_client)


@pytest.mark.asyncio
async def test_get_swift(mongo_client, swift_repository):
    mongo_client.get_item.return_value = {
        "swiftCode": "TESTCODE",
        "countryISO2": "US",
        "isHeadquarter": True,
    }
    result = await swift_repository.get_swift({"swiftCode": "TESTCODE"})
    assert result["swiftCode"] == "TESTCODE"
    assert result["countryISO2"] == "US"
    assert result["isHeadquarter"] is True

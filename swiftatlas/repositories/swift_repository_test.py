import pytest
from unittest.mock import AsyncMock, MagicMock
from swiftatlas.repositories.swift_repository import SwiftRepository
from swiftatlas.clients.mongo_client import MongoMotorClient
from swiftatlas.schemas.swift_schemas import (
    SwiftCodeDetailed,
    SwiftCodeBase,
    SwiftCodeHeadquarterGroup,
    SwiftCodeCountryGroup,
)


@pytest.fixture
def mock_mongo_client():
    client = MagicMock(spec=MongoMotorClient)
    client.get_item = AsyncMock()
    client.put_item = AsyncMock()
    client.find = MagicMock()
    client.update_item = AsyncMock()
    client.delete_item = AsyncMock()
    client.scan = AsyncMock()
    return client


@pytest.fixture
def swift_repository(mock_mongo_client):
    return SwiftRepository(db=mock_mongo_client)


@pytest.fixture
def sample_swift_detailed_obj():
    return SwiftCodeDetailed(
        swiftCode="BANKUS33XXX",
        bankName="Test Bank",
        address="123 Main St, New York",
        countryName="United States",
        countryISO2="US",
        isHeadquarter=True,
    )


@pytest.fixture
def sample_swift_detailed_dict(sample_swift_detailed_obj):
    return sample_swift_detailed_obj.model_dump()


@pytest.fixture
def sample_swift_branch_obj():
    return SwiftCodeDetailed(
        swiftCode="BANKUS33BRC",
        bankName="Test Bank Branch",
        address="456 Branch Ave, Los Angeles",
        countryName="United States",
        countryISO2="US",
        isHeadquarter=False,
    )


@pytest.fixture
def sample_swift_branch_dict(sample_swift_branch_obj):
    swift_code = sample_swift_branch_obj.model_dump()
    swift_code["swiftCodePrefix8"] = swift_code["swiftCode"][:8]
    return swift_code


@pytest.mark.asyncio
async def test_create_swift_new(
    mock_mongo_client, swift_repository, sample_swift_detailed_obj
):
    mock_mongo_client.get_item.return_value = None
    mock_mongo_client.put_item.return_value = MagicMock(inserted_id="some_id")

    result = await swift_repository.create_swift(sample_swift_detailed_obj)

    mock_mongo_client.get_item.assert_awaited_once_with({"swiftCode": "BANKUS33XXX"})
    expected_dict = sample_swift_detailed_obj.model_dump()
    expected_dict["swiftCodePrefix8"] = "BANKUS33"
    mock_mongo_client.put_item.assert_awaited_once_with(expected_dict)
    assert result is not False
    assert result.inserted_id == "some_id"


@pytest.mark.asyncio
async def test_create_swift_existing(
    mock_mongo_client, swift_repository, sample_swift_detailed_obj
):
    mock_mongo_client.get_item.return_value = {"swiftCode": "BANKUS33XXX"}
    result = await swift_repository.create_swift(sample_swift_detailed_obj)

    mock_mongo_client.get_item.assert_awaited_once_with({"swiftCode": "BANKUS33XXX"})
    mock_mongo_client.put_item.assert_not_awaited()
    assert result is False


@pytest.mark.asyncio
async def test_get_swift(
    mock_mongo_client, swift_repository, sample_swift_detailed_dict
):
    mock_mongo_client.get_item.return_value = sample_swift_detailed_dict
    query = {"swiftCode": "TESTCODE"}
    result = await swift_repository.get_swift(query)
    mock_mongo_client.get_item.assert_awaited_once_with(query)
    assert result["swiftCode"] == "BANKUS33XXX"
    assert result["isHeadquarter"] is True


@pytest.mark.asyncio
async def test_get_swift_with_branches_headquarter(
    mock_mongo_client,
    swift_repository,
    sample_swift_detailed_dict,
    sample_swift_branch_dict,
):
    hq_dict = sample_swift_detailed_dict
    branch_dict = sample_swift_branch_dict
    mock_mongo_client.get_item.return_value = hq_dict

    items = [branch_dict]

    async def async_gen():
        for item in items:
            yield item

    mock_mongo_client.find.return_value = async_gen()

    result = await swift_repository.get_swift_with_branches("BANKUS33XXX")

    mock_mongo_client.get_item.assert_awaited_once_with({"swiftCode": "BANKUS33XXX"})
    mock_mongo_client.find.assert_called_once_with(
        {"swiftCodePrefix8": "BANKUS33", "isHeadquarter": False}
    )

    assert result is not None
    assert isinstance(result, SwiftCodeHeadquarterGroup)
    assert result.swiftCode == "BANKUS33XXX"
    assert result.isHeadquarter is True
    assert len(result.branches) == 1, f"Expected 1 branch, got {len(result.branches)}"
    assert isinstance(result.branches[0], SwiftCodeBase)
    assert result.branches[0].swiftCode == "BANKUS33BRC"


@pytest.mark.asyncio
async def test_get_swift_with_branches_branch(
    mock_mongo_client, swift_repository, sample_swift_branch_dict
):
    branch_dict = sample_swift_branch_dict
    mock_mongo_client.get_item.return_value = branch_dict

    result = await swift_repository.get_swift_with_branches("BANKUS33BRC")

    mock_mongo_client.get_item.assert_awaited_once_with({"swiftCode": "BANKUS33BRC"})
    mock_mongo_client.find.assert_not_called()
    assert isinstance(result, SwiftCodeDetailed)
    assert result.swiftCode == "BANKUS33BRC"
    assert result.isHeadquarter is False


@pytest.mark.asyncio
async def test_get_swift_with_branches_not_found(mock_mongo_client, swift_repository):
    mock_mongo_client.get_item.return_value = None

    result = await swift_repository.get_swift_with_branches("NOTFOUND")

    mock_mongo_client.get_item.assert_awaited_once_with({"swiftCode": "NOTFOUND"})
    assert result is None


@pytest.mark.asyncio
async def test_get_swifts_by_country(
    mock_mongo_client,
    swift_repository,
    sample_swift_detailed_dict,
    sample_swift_branch_dict,
):
    hq_dict = sample_swift_detailed_dict
    branch_dict = sample_swift_branch_dict

    items = [hq_dict, branch_dict]

    async def async_gen():
        for item in items:
            yield item

    mock_mongo_client.find.return_value = async_gen()

    result = await swift_repository.get_swifts_by_country("US")

    mock_mongo_client.find.assert_called_once_with({"countryISO2": "US"})
    assert result is not None
    assert isinstance(result, SwiftCodeCountryGroup)
    assert result.countryISO2 == "US"
    assert result.countryName == hq_dict["countryName"]

    assert (
        len(result.swiftCodes) == 2
    ), f"Expected 2 swift codes, got {len(result.swiftCodes)}"
    assert isinstance(result.swiftCodes[0], SwiftCodeBase)
    assert isinstance(result.swiftCodes[1], SwiftCodeBase)
    assert result.swiftCodes[0].swiftCode == hq_dict["swiftCode"]
    assert result.swiftCodes[1].swiftCode == branch_dict["swiftCode"]


@pytest.mark.asyncio
async def test_get_swifts_by_country_not_found(mock_mongo_client, swift_repository):
    mock_cursor = AsyncMock()
    mock_cursor.__anext__.side_effect = StopAsyncIteration
    mock_mongo_client.find.return_value = mock_cursor

    result = await swift_repository.get_swifts_by_country("XX")

    mock_mongo_client.find.assert_called_once_with({"countryISO2": "XX"})
    assert result is None


@pytest.mark.asyncio
async def test_update_swift(mock_mongo_client, swift_repository):
    query = {"swiftCode": "TESTCODE"}
    update = {"$set": {"bankName": "Updated Bank"}}
    mock_result = MagicMock(modified_count=1)
    mock_mongo_client.update_item.return_value = mock_result

    result = await swift_repository.update_swift(query, update)

    mock_mongo_client.update_item.assert_awaited_once_with(query, update)
    assert result.modified_count == 1


@pytest.mark.asyncio
async def test_delete_swift(mock_mongo_client, swift_repository):
    query = {"swiftCode": "TESTCODE"}
    mock_result = MagicMock(deleted_count=1)
    mock_mongo_client.delete_item.return_value = mock_result

    result = await swift_repository.delete_swift(query)

    mock_mongo_client.delete_item.assert_awaited_once_with(query)
    assert result.deleted_count == 1

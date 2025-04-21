import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from swiftatlas.main import app
from swiftatlas.repositories.swift_repository import SwiftRepository
from swiftatlas.schemas.swift_schemas import (
    SwiftCodeDetailed,
    SwiftCodeHeadquarterGroup,
    SwiftCodeCountryGroup,
    SwiftCodeBase,
)
from swiftatlas.clients.mongo_client import MongoMotorClient
from pymongo.results import InsertOneResult, DeleteResult

TEST_SWIFT_CODE_HQ = "AAAABBCCXXX"
TEST_SWIFT_CODE_BRANCH = "AAAABBCCDDD"
TEST_COUNTRY_ISO = "IT"
TEST_NONEXISTENT_CODE = "AAAABBCCEEE"
TEST_NONEXISTENT_COUNTRY = "XX"


@pytest.fixture
def mock_mongo_client():
    """Fixture for a mocked MongoMotorClient."""
    client = MagicMock(spec=MongoMotorClient)
    client.get_item = AsyncMock()
    client.put_item = AsyncMock()
    client.find = MagicMock()  # find returns a cursor-like object
    client.delete_item = AsyncMock()
    return client


@pytest.fixture
def mock_swift_repository(mock_mongo_client):
    """Fixture for SwiftRepository with a mocked client."""
    return SwiftRepository(db=mock_mongo_client)


@pytest.fixture
def client(mock_swift_repository):
    """Provides a TestClient instance with mocked repository dependency."""

    async def override_get_swift_repository():
        return mock_swift_repository

    app.dependency_overrides[get_swift_repository] = (
        override_get_swift_repository  # get_swift_repository needs to be imported
    )
    with TestClient(app) as c:
        yield c
    # Clean up overrides after tests
    app.dependency_overrides = {}


# Need to import the dependency function to override it
from swiftatlas.routers.swift_codes import get_swift_repository


@pytest.fixture
def hq_swift_detailed():
    return SwiftCodeDetailed(
        swiftCode=TEST_SWIFT_CODE_HQ,
        bankName="Integration Test Bank HQ",
        address="1 Integration Test St",
        countryName="IntegrationTestland",
        countryISO2=TEST_COUNTRY_ISO,
        isHeadquarter=True,
    )


@pytest.fixture
def branch_swift_detailed():
    return SwiftCodeDetailed(
        swiftCode=TEST_SWIFT_CODE_BRANCH,
        bankName="Integration Test Bank Branch",
        address="2 Integration Branch Ln",
        countryName="IntegrationTestland",
        countryISO2=TEST_COUNTRY_ISO,
        isHeadquarter=False,
    )


@pytest.fixture
def hq_swift_dict(hq_swift_detailed):
    d = hq_swift_detailed.model_dump()
    d["swiftCodePrefix8"] = d["swiftCode"][:8]
    return d


@pytest.fixture
def branch_swift_dict(branch_swift_detailed):
    d = branch_swift_detailed.model_dump()
    d["swiftCodePrefix8"] = d["swiftCode"][:8]
    return d


def test_add_swift_code_hq_success(
    client, mock_swift_repository, hq_swift_detailed, hq_swift_dict
):
    """Test adding a new headquarter SWIFT code successfully."""
    mock_swift_repository.client.get_item.return_value = None  # Simulate not found
    mock_swift_repository.client.put_item.return_value = InsertOneResult(
        inserted_id="some_id", acknowledged=True
    )

    payload = hq_swift_detailed.model_dump()
    response = client.post("/v1/swift-codes", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["message"]
        == f"SWIFT code {TEST_SWIFT_CODE_HQ} added successfully."
    )
    mock_swift_repository.client.get_item.assert_awaited_once_with(
        {"swiftCode": TEST_SWIFT_CODE_HQ}
    )
    mock_swift_repository.client.put_item.assert_awaited_once_with(hq_swift_dict)


def test_add_swift_code_branch_success(
    client, mock_swift_repository, branch_swift_detailed, branch_swift_dict
):
    """Test adding a new branch SWIFT code successfully."""
    mock_swift_repository.client.get_item.return_value = None  # Simulate not found
    mock_swift_repository.client.put_item.return_value = InsertOneResult(
        inserted_id="some_other_id", acknowledged=True
    )

    payload = branch_swift_detailed.model_dump()
    response = client.post("/v1/swift-codes", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["message"]
        == f"SWIFT code {TEST_SWIFT_CODE_BRANCH} added successfully."
    )
    mock_swift_repository.client.get_item.assert_awaited_once_with(
        {"swiftCode": TEST_SWIFT_CODE_BRANCH}
    )
    mock_swift_repository.client.put_item.assert_awaited_once_with(branch_swift_dict)


def test_add_swift_code_conflict(
    client, mock_swift_repository, hq_swift_detailed, hq_swift_dict
):
    """Test adding a SWIFT code that already exists."""
    mock_swift_repository.client.get_item.return_value = (
        hq_swift_dict  # Simulate already exists
    )

    payload = hq_swift_detailed.model_dump()
    response = client.post("/v1/swift-codes", json=payload)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {
        "detail": f"Attempted to add duplicate SWIFT code {TEST_SWIFT_CODE_HQ}."
    }
    mock_swift_repository.client.get_item.assert_awaited_once_with(
        {"swiftCode": TEST_SWIFT_CODE_HQ}
    )
    mock_swift_repository.client.put_item.assert_not_awaited()


def test_get_swift_code_details_hq(
    client, mock_swift_repository, hq_swift_dict, branch_swift_dict
):
    """Test retrieving details for the headquarter SWIFT code."""
    mock_swift_repository.client.get_item.return_value = hq_swift_dict

    async def mock_cursor_iter():
        yield branch_swift_dict

    mock_swift_repository.client.find.return_value = mock_cursor_iter()

    response = client.get(f"/v1/swift-codes/{TEST_SWIFT_CODE_HQ}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["swiftCode"] == TEST_SWIFT_CODE_HQ
    assert data["isHeadquarter"] is True
    assert data["countryISO2"] == TEST_COUNTRY_ISO
    assert "branches" in data
    assert len(data["branches"]) == 1
    assert data["branches"][0]["swiftCode"] == TEST_SWIFT_CODE_BRANCH

    mock_swift_repository.client.get_item.assert_awaited_once_with(
        {"swiftCode": TEST_SWIFT_CODE_HQ}
    )
    mock_swift_repository.client.find.assert_called_once_with(
        {"swiftCodePrefix8": TEST_SWIFT_CODE_HQ[:8], "isHeadquarter": False}
    )


def test_get_swift_code_details_branch(
    client, mock_swift_repository, branch_swift_dict
):
    """Test retrieving details for the branch SWIFT code."""
    mock_swift_repository.client.get_item.return_value = branch_swift_dict

    response = client.get(f"/v1/swift-codes/{TEST_SWIFT_CODE_BRANCH}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["swiftCode"] == TEST_SWIFT_CODE_BRANCH
    assert data["isHeadquarter"] is False
    assert data["countryISO2"] == TEST_COUNTRY_ISO
    assert "branches" not in data  # Branches don't have branches list

    mock_swift_repository.client.get_item.assert_awaited_once_with(
        {"swiftCode": TEST_SWIFT_CODE_BRANCH}
    )
    mock_swift_repository.client.find.assert_not_called()


def test_get_swift_codes_by_country(
    client, mock_swift_repository, hq_swift_dict, branch_swift_dict
):
    """Test retrieving all SWIFT codes for the test country."""

    async def asyc_gen():
        yield hq_swift_dict
        yield branch_swift_dict

    mock_swift_repository.client.find.return_value = asyc_gen()

    response = client.get(f"/v1/swift-codes/country/{TEST_COUNTRY_ISO}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["countryISO2"] == TEST_COUNTRY_ISO
    assert data["countryName"] == hq_swift_dict["countryName"].upper()
    assert len(data["swiftCodes"]) == 2
    codes_found = {code["swiftCode"] for code in data["swiftCodes"]}
    assert TEST_SWIFT_CODE_HQ in codes_found
    assert TEST_SWIFT_CODE_BRANCH in codes_found

    mock_swift_repository.client.find.assert_called_once_with(
        {"countryISO2": TEST_COUNTRY_ISO}
    )


def test_get_swift_code_details_not_found(client, mock_swift_repository):
    """Test retrieving a SWIFT code that does not exist."""
    mock_swift_repository.client.get_item.return_value = None

    response = client.get("/v1/swift-codes/ZZZZZZZZXXX")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "SWIFT code not found"}
    mock_swift_repository.client.get_item.assert_awaited_once_with(
        {"swiftCode": "ZZZZZZZZXXX"}
    )


@pytest.mark.parametrize(
    "invalid_swift_code",
    ["INVALID", "TOOLONG12345", "BANKUS3!"],
)
def test_get_swift_code_details_invalid_format(
    client, mock_swift_repository, invalid_swift_code
):
    """Test retrieving a SWIFT code with an invalid format."""
    response = client.get(f"/v1/swift-codes/{invalid_swift_code}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid SWIFT code format" in response.json()["detail"]
    mock_swift_repository.client.get_item.assert_not_awaited()


def test_get_swift_codes_by_country_not_found(client, mock_swift_repository):
    """Test retrieving SWIFT codes for a country with no entries."""
    # Mock the cursor to be empty
    mock_cursor = AsyncMock()
    mock_cursor.__anext__.side_effect = StopAsyncIteration
    mock_swift_repository.client.find.return_value = mock_cursor

    response = client.get(f"/v1/swift-codes/country/{TEST_NONEXISTENT_COUNTRY}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "No SWIFT codes found for this country"}
    mock_swift_repository.client.find.assert_called_once_with(
        {"countryISO2": TEST_NONEXISTENT_COUNTRY}
    )


@pytest.mark.parametrize(
    "invalid_country_code",
    ["X", "XYZ", "12"],
)
def test_get_swift_codes_by_country_invalid_format(
    client, mock_swift_repository, invalid_country_code
):
    """Test retrieving SWIFT codes for an invalid-format country code."""
    response = client.get(f"/v1/swift-codes/country/{invalid_country_code}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid Country ISO2 code format" in response.json()["detail"]
    mock_swift_repository.client.find.assert_not_called()


def test_add_swift_code_validation_error(client, mock_swift_repository):
    """Test adding a SWIFT code with invalid data (missing required field)."""
    invalid_payload = {
        # Missing bankName
        "swiftCode": "VALIDCDEXXX",
        "address": "Invalid St",
        "countryName": "Invalidland",
        "countryISO2": "IV",
        "isHeadquarter": True,
    }
    response = client.post("/v1/swift-codes", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()
    assert isinstance(response.json()["detail"], list)
    assert any(
        err["msg"] == "Field required" and err["loc"][-1] == "bankName"
        for err in response.json()["detail"]
    )
    # Validation happens before repository call
    mock_swift_repository.client.get_item.assert_not_awaited()
    mock_swift_repository.client.put_item.assert_not_awaited()


def test_delete_swift_code_success(client, mock_swift_repository):
    """Test successfully deleting a SWIFT code."""
    mock_swift_repository.client.delete_item.return_value = DeleteResult(
        {"n": 1}, acknowledged=True
    )

    response = client.delete(f"/v1/swift-codes/{TEST_SWIFT_CODE_HQ}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": f"SWIFT code {TEST_SWIFT_CODE_HQ} deleted successfully."
    }
    mock_swift_repository.client.delete_item.assert_awaited_once_with(
        {"swiftCode": TEST_SWIFT_CODE_HQ}
    )


def test_delete_swift_code_not_found(client, mock_swift_repository):
    """Test deleting a SWIFT code that does not exist."""
    mock_swift_repository.client.delete_item.return_value = DeleteResult(
        {"n": 0}, acknowledged=True
    )

    response = client.delete(f"/v1/swift-codes/{TEST_NONEXISTENT_CODE}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": f"SWIFT code {TEST_NONEXISTENT_CODE} not found."
    }
    mock_swift_repository.client.delete_item.assert_awaited_once_with(
        {"swiftCode": TEST_NONEXISTENT_CODE}
    )


@pytest.mark.parametrize(
    "invalid_swift_code",
    ["INVALID", "TOOLONG12345", "BANKUS3!"],
)
def test_delete_swift_code_invalid_format(
    client, mock_swift_repository, invalid_swift_code
):
    """Test deleting a SWIFT code with an invalid format."""
    response = client.delete(f"/v1/swift-codes/{invalid_swift_code}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid SWIFT code format" in response.json()["detail"]
    mock_swift_repository.client.delete_item.assert_not_awaited()

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from swiftatlas.repositories.swift_repository import SwiftRepository
from swiftatlas.schemas.swift_schemas import (
    SwiftCodeDetailed,
    SwiftCodeHeadquarterGroup,
    SwiftCodeCountryGroup,
    SwiftCodeBase,
)
from swiftatlas.routers.swift_codes import get_swift_repository
from swiftatlas.main import app

# Sample data for testing
sample_hq_swift = SwiftCodeHeadquarterGroup(
    swiftCode="BANKUS33XXX",
    bankName="Test Bank HQ",
    address="123 Main St",
    city="New York",
    countryName="United States",
    countryISO2="US",
    isHeadquarter=True,
    branches=[
        SwiftCodeBase(
            swiftCode="BANKUS33BRC",
            bankName="Test Bank Branch",
            address="456 Branch Ave",
            countryISO2="US",
            isHeadquarter=False,
        )
    ]
)

sample_branch_swift = SwiftCodeDetailed(
    swiftCode="BANKUS33BRC",
    bankName="Test Bank Branch",
    address="456 Branch Ave",
    city="Los Angeles",
    countryName="United States",
    countryISO2="US",
    isHeadquarter=False,
)

sample_country_group = SwiftCodeCountryGroup(
    countryISO2="US",
    countryName="United States",
    swiftCodes=[
        SwiftCodeBase(
            swiftCode="BANKUS33XXX",
            bankName="Test Bank HQ",
            address="123 Main St",
            countryISO2="US",
            isHeadquarter=True,
        ),
        SwiftCodeBase(
            swiftCode="BANKUS33BRC",
            bankName="Test Bank Branch",
            address="456 Branch Ave",
            countryISO2="US",
            isHeadquarter=False,
        )
    ]
)

sample_new_swift_payload = {
    "swiftCode": "NEWCGBR1XXX",
    "bankName": "New Bank",
    "address": "1 New Street",
    "city": "London",
    "countryName": "United Kingdom",
    "countryISO2": "GB",
    "isHeadquarter": True,
}

# Mock repository fixture
@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=SwiftRepository)
    repo.get_swift_with_branches = AsyncMock()
    repo.get_swifts_by_country = AsyncMock()
    repo.create_swift = AsyncMock()
    repo.delete_swift = AsyncMock()
    return repo

# Override dependency for testing
@pytest.fixture(autouse=True)
def override_dependency(mock_repo):
    app.dependency_overrides[get_swift_repository] = lambda: mock_repo
    yield
    app.dependency_overrides = {}

@pytest.fixture
def client():
    return TestClient(app)

# --- Test Cases --- #

# GET /v1/swift-codes/{swift_code}
def test_get_swift_code_details_hq(client, mock_repo):
    mock_repo.get_swift_with_branches.return_value = sample_hq_swift
    response = client.get("/v1/swift-codes/BANKUS33XXX")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_hq_swift.model_dump()
    mock_repo.get_swift_with_branches.assert_awaited_once_with("BANKUS33XXX")

def test_get_swift_code_details_branch(client, mock_repo):
    mock_repo.get_swift_with_branches.return_value = sample_branch_swift
    response = client.get("/v1/swift-codes/BANKUS33BRC")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["swiftCode"] == sample_branch_swift.swiftCode
    assert response.json()["isHeadquarter"] == sample_branch_swift.isHeadquarter
    mock_repo.get_swift_with_branches.assert_awaited_once_with("BANKUS33BRC")

def test_get_swift_code_details_not_found(client, mock_repo):
    mock_repo.get_swift_with_branches.return_value = None
    response = client.get("/v1/swift-codes/NOTFOUND")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "SWIFT code not found"}
    mock_repo.get_swift_with_branches.assert_awaited_once_with("NOTFOUND")

# GET /v1/swift-codes/country/{country_iso2_code}
def test_get_swift_codes_by_country_found(client, mock_repo):
    mock_repo.get_swifts_by_country.return_value = sample_country_group
    response = client.get("/v1/swift-codes/country/US")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_country_group.model_dump()
    mock_repo.get_swifts_by_country.assert_awaited_once_with("US")

def test_get_swift_codes_by_country_not_found(client, mock_repo):
    mock_repo.get_swifts_by_country.return_value = None
    response = client.get("/v1/swift-codes/country/XX")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "No SWIFT codes found for this country"}
    mock_repo.get_swifts_by_country.assert_awaited_once_with("XX")

# POST /v1/swift-codes
def test_add_swift_code_success(client, mock_repo):
    mock_repo.create_swift.return_value = True
    response = client.post("/v1/swift-codes", json=sample_new_swift_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "SWIFT code NEWCGBR1XXX added successfully."}
    mock_repo.create_swift.assert_awaited_once()
    call_args, _ = mock_repo.create_swift.call_args
    assert isinstance(call_args[0], SwiftCodeDetailed)
    assert call_args[0].swiftCode == "NEWCGBR1XXX"

def test_add_swift_code_conflict(client, mock_repo):
    mock_repo.create_swift.return_value = False
    response = client.post("/v1/swift-codes", json=sample_new_swift_payload)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": "Attempted to add duplicate SWIFT code NEWCGBR1XXX."}
    mock_repo.create_swift.assert_awaited_once()

# DELETE /v1/swift-codes/{swift_code}
def test_delete_swift_code_success(client, mock_repo):
    mock_repo.delete_swift.return_value = MagicMock(deleted_count=1)
    response = client.delete("/v1/swift-codes/BANKUS33XXX")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "SWIFT code BANKUS33XXX deleted successfully."}
    mock_repo.delete_swift.assert_awaited_once_with({"swiftCode": "BANKUS33XXX"})

def test_delete_swift_code_not_found(client, mock_repo):
    mock_repo.delete_swift.return_value = MagicMock(deleted_count=0)
    response = client.delete("/v1/swift-codes/NOTFOUND")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "SWIFT code NOTFOUND not found."}
    mock_repo.delete_swift.assert_awaited_once_with({"swiftCode": "NOTFOUND"})

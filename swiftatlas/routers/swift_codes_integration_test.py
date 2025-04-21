import pytest
from fastapi import status
from fastapi.testclient import TestClient

from swiftatlas.main import app

TEST_SWIFT_CODE_HQ = "AAAABBCCXXX"
TEST_SWIFT_CODE_BRANCH = "AAAABBCCDDD"
TEST_COUNTRY_ISO = "IT"
TEST_NONEXISTENT_CODE = "NONEXISTENTCODE"
TEST_NONEXISTENT_COUNTRY = "XX"


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def setup_test_swift_codes(client):
    """Fixture to add HQ and Branch SWIFT codes and clean them up afterwards."""
    hq_payload = {
        "swiftCode": TEST_SWIFT_CODE_HQ,
        "bankName": "Integration Test Bank HQ",
        "address": "1 Integration Test St",
        "countryName": "IntegrationTestland",
        "countryISO2": TEST_COUNTRY_ISO,
        "isHeadquarter": True,
    }
    client.post("/v1/swift-codes", json=hq_payload)

    branch_payload = {
        "swiftCode": TEST_SWIFT_CODE_BRANCH,
        "bankName": "Integration Test Bank Branch",
        "address": "2 Integration Branch Ln",
        "countryName": "IntegrationTestland",
        "countryISO2": TEST_COUNTRY_ISO,
        "isHeadquarter": False,
    }
    client.post("/v1/swift-codes", json=branch_payload)

    yield

    client.delete(f"/v1/swift-codes/{TEST_SWIFT_CODE_BRANCH}")
    client.delete(f"/v1/swift-codes/{TEST_SWIFT_CODE_HQ}")


def test_add_swift_code_hq_integration(client):
    """Test adding a new headquarter SWIFT code. Assumes it might already exist."""
    payload = {
        "swiftCode": TEST_SWIFT_CODE_HQ,
        "bankName": "Integration Test Bank HQ",
        "address": "1 Integration Test St",
        "countryName": "IntegrationTestland",
        "countryISO2": TEST_COUNTRY_ISO,
        "isHeadquarter": True,
    }
    response = client.post("/v1/swift-codes", json=payload)
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_409_CONFLICT]
    if response.status_code == status.HTTP_201_CREATED:
        assert (
            response.json()["message"]
            == f"SWIFT code {TEST_SWIFT_CODE_HQ} added successfully."
        )


def test_add_swift_code_branch_integration(client):
    """Test adding a new branch SWIFT code. Assumes it might already exist."""
    payload = {
        "swiftCode": TEST_SWIFT_CODE_BRANCH,
        "bankName": "Integration Test Bank Branch",
        "address": "2 Integration Branch Ln",
        "countryName": "IntegrationTestland",
        "countryISO2": TEST_COUNTRY_ISO,
        "isHeadquarter": False,
    }
    response = client.post("/v1/swift-codes", json=payload)
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_409_CONFLICT]
    if response.status_code == status.HTTP_201_CREATED:
        assert (
            response.json()["message"]
            == f"SWIFT code {TEST_SWIFT_CODE_BRANCH} added successfully."
        )


def test_get_swift_code_details_hq_integration(client):
    """Test retrieving details for the headquarter SWIFT code."""
    response = client.get(f"/v1/swift-codes/{TEST_SWIFT_CODE_HQ}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["swiftCode"] == TEST_SWIFT_CODE_HQ
    assert data["isHeadquarter"] is True
    assert data["countryISO2"] == TEST_COUNTRY_ISO
    assert "branches" in data
    branch_found = any(
        b["swiftCode"] == TEST_SWIFT_CODE_BRANCH for b in data.get("branches", [])
    )
    assert branch_found, f"Branch {TEST_SWIFT_CODE_BRANCH} not found in HQ details"


def test_get_swift_code_details_branch_integration(client):
    """Test retrieving details for the branch SWIFT code."""
    response = client.get(f"/v1/swift-codes/{TEST_SWIFT_CODE_BRANCH}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["swiftCode"] == TEST_SWIFT_CODE_BRANCH
    assert data["isHeadquarter"] is False
    assert data["countryISO2"] == TEST_COUNTRY_ISO
    assert "branches" not in data


def test_get_swift_codes_by_country_integration(client):
    """Test retrieving all SWIFT codes for the test country."""
    response = client.get(f"/v1/swift-codes/country/{TEST_COUNTRY_ISO}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["countryISO2"] == TEST_COUNTRY_ISO
    assert len(data["swiftCodes"]) >= 2
    codes_found = {code["swiftCode"] for code in data["swiftCodes"]}
    assert TEST_SWIFT_CODE_HQ in codes_found
    assert TEST_SWIFT_CODE_BRANCH in codes_found


def test_get_swift_code_details_valid_format_not_found_integration(client):
    """Test retrieving a valid-format SWIFT code that does not exist."""
    response = client.get("/v1/swift-codes/ZZZZZZZZXXX")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "SWIFT code not found"}


@pytest.mark.parametrize(
    "invalid_swift_code",
    ["INVALID", "TOOLONG12345", "BANKUS3!"],
)
def test_get_swift_code_details_invalid_format_integration(client, invalid_swift_code):
    """Test retrieving a SWIFT code with an invalid format."""
    response = client.get(f"/v1/swift-codes/{invalid_swift_code}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid SWIFT code format" in response.json()["detail"]


def test_get_swift_codes_by_country_valid_format_not_found_integration(client):
    """Test retrieving SWIFT codes for a valid-format country code with no entries."""
    response = client.get("/v1/swift-codes/country/XX")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "No SWIFT codes found for this country"}


@pytest.mark.parametrize(
    "invalid_country_code",
    ["X", "XYZ", "12"],
)
def test_get_swift_codes_by_country_invalid_format_integration(
    client, invalid_country_code
):
    """Test retrieving SWIFT codes for an invalid-format country code."""
    response = client.get(f"/v1/swift-codes/country/{invalid_country_code}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid Country ISO2 code format" in response.json()["detail"]


def test_add_swift_code_conflict_integration(client):
    """Test adding a SWIFT code that already exists by adding it twice."""
    temp_conflict_code = "CONFLICTXXX"
    payload = {
        "swiftCode": temp_conflict_code,
        "bankName": "Conflict Test Bank",
        "address": "1 Conflict St",
        "countryName": "Conflictland",
        "countryISO2": "CF",
        "isHeadquarter": True,
    }

    response1 = client.post("/v1/swift-codes", json=payload)
    assert response1.status_code == status.HTTP_201_CREATED
    assert (
        response1.json()["message"]
        == f"SWIFT code {temp_conflict_code} added successfully."
    )

    response2 = client.post("/v1/swift-codes", json=payload)
    assert response2.status_code == status.HTTP_409_CONFLICT
    assert response2.json() == {
        "detail": f"Attempted to add duplicate SWIFT code {temp_conflict_code}."
    }

    delete_response = client.delete(f"/v1/swift-codes/{temp_conflict_code}")
    assert delete_response.status_code == status.HTTP_200_OK


def test_add_swift_code_validation_error_integration(client):
    """Test adding a SWIFT code with invalid data (missing required field)."""
    invalid_payload = {
        "swiftCode": "INVALIDCODE",
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


def test_delete_swift_code_hq_success_integration(client):
    """Test successfully deleting a headquarter SWIFT code."""
    temp_hq_code = "DELMEHQXXXX"
    payload = {
        "swiftCode": temp_hq_code,
        "bankName": "Delete Me Bank HQ",
        "address": "1 Delete St",
        "countryName": "Deleteland",
        "countryISO2": "DL",
        "isHeadquarter": True,
    }
    add_response = client.post("/v1/swift-codes", json=payload)
    assert add_response.status_code == status.HTTP_201_CREATED

    delete_response = client.delete(f"/v1/swift-codes/{temp_hq_code}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json() == {
        "message": f"SWIFT code {temp_hq_code} deleted successfully."
    }

    get_response = client.get(f"/v1/swift-codes/{temp_hq_code}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_swift_code_branch_success_integration(client):
    """Test successfully deleting a branch SWIFT code."""
    temp_branch_code = "DELMEBRYYYY"
    payload = {
        "swiftCode": temp_branch_code,
        "bankName": "Delete Me Bank Branch",
        "address": "2 Delete Ln",
        "countryName": "Deleteland",
        "countryISO2": "DL",
        "isHeadquarter": False,
    }
    add_response = client.post("/v1/swift-codes", json=payload)
    assert add_response.status_code == status.HTTP_201_CREATED

    delete_response = client.delete(f"/v1/swift-codes/{temp_branch_code}")
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json() == {
        "message": f"SWIFT code {temp_branch_code} deleted successfully."
    }

    get_response = client.get(f"/v1/swift-codes/{temp_branch_code}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_swift_code_valid_format_not_found_integration(client):
    """Test deleting a valid-format SWIFT code that does not exist."""
    response = client.delete("/v1/swift-codes/ZZZZZZZZXXX")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": f"SWIFT code ZZZZZZZZXXX not found."}


@pytest.mark.parametrize(
    "invalid_swift_code",
    ["INVALID", "TOOLONG12345", "BANKUS3!"],
)
def test_delete_swift_code_invalid_format_integration(client, invalid_swift_code):
    """Test deleting a SWIFT code with an invalid format."""
    response = client.delete(f"/v1/swift-codes/{invalid_swift_code}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid SWIFT code format" in response.json()["detail"]

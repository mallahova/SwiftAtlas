import pytest
from pydantic import ValidationError

from swiftatlas.schemas.swift_schemas import (
    SwiftCodeBase,
    SwiftCodeDetailed,
    SwiftCodeHeadquarterGroup,
    SwiftCodeCountryGroup,
)

# --- Helper Fixtures for Test Data ---


@pytest.fixture
def base_data():
    """Provides default valid data for SwiftCodeBase."""
    return {
        "address": " 123 Main St ",
        "bankName": " Test Bank ",
        "countryISO2": "us",
        "isHeadquarter": True,
        "swiftCode": " testcode ",  # Will be normalized to TESTCODEXXX
    }


@pytest.fixture
def base_data_branch():
    """Provides default valid branch data for SwiftCodeBase."""
    return {
        "address": "456 Branch Ave",
        "bankName": "Branch Bank",
        "countryISO2": "GB",
        "isHeadquarter": False,
        "swiftCode": "branchcode1",  # 11 chars, will be normalized
    }


@pytest.fixture
def detailed_data(base_data):
    """Provides default valid data for SwiftCodeDetailed."""
    data = base_data.copy()
    data.update(
        {
            "address": " 789 Detail Rd ",
            "bankName": " Detailed Bank ",
            "countryISO2": "de",
            "swiftCode": " detailcd ",  # Will be normalized to DETAILCDXXX
            "countryName": " germany ",
        }
    )
    return data


@pytest.fixture
def hq_group_data():
    """Provides default valid data for SwiftCodeHeadquarterGroup."""
    branch_data = {
        "address": "Branch St",
        "bankName": "Branch Bank",
        "countryISO2": "fr",
        "isHeadquarter": False,
        "swiftCode": "hqcodefrert",  # Matches prefix HQCODEFR
    }
    return {
        "address": " HQ Ave ",
        "bankName": " HQ Bank ",
        "countryISO2": "fr",
        "isHeadquarter": True,
        "swiftCode": " hqcodefr ",  # Will be normalized to HQCODEFRXXX
        "countryName": " france ",
        "branches": [branch_data],
    }


@pytest.fixture
def country_group_data():
    """Provides default valid data for SwiftCodeCountryGroup."""
    swift_code_data_1 = {
        "address": "1 Rue",
        "bankName": "Bank One",
        "countryISO2": "ca",
        "isHeadquarter": True,
        "swiftCode": "bankone1",  # Will be normalized to BANKONE1XXX
    }
    swift_code_data_2 = {
        "address": "2 Ave",
        "bankName": "Bank Two",
        "countryISO2": "ca",
        "isHeadquarter": False,
        "swiftCode": "BANKTWOADFS",  # 11 chars, valid
    }
    return {
        "countryISO2": "CA",
        "countryName": "Canada",
        "swiftCodes": [swift_code_data_1, swift_code_data_2],
    }


# --- Tests for SwiftCodeBase ---


def test_swift_code_base_valid(base_data):
    model = SwiftCodeBase(**base_data)
    assert model.address == "123 Main St"
    assert model.bankName == "Test Bank"
    assert model.countryISO2 == "US"
    assert model.isHeadquarter is True
    assert model.swiftCode == "TESTCODEXXX"


def test_swift_code_base_valid_11_char(base_data_branch):
    model = SwiftCodeBase(**base_data_branch)
    assert model.countryISO2 == "GB"
    assert model.swiftCode == "BRANCHCODE1"
    assert model.isHeadquarter is False


def test_swift_code_base_invalid_country_iso2_length(base_data):
    invalid_data = base_data.copy()
    invalid_data["countryISO2"] = "USA"
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeBase(**invalid_data)
    assert "countryISO2 must be 2 characters long" in str(excinfo.value)


def test_swift_code_base_invalid_swift_code_length(base_data):
    invalid_data_short = base_data.copy()
    invalid_data_short["swiftCode"] = "SHORT"
    with pytest.raises(ValidationError) as excinfo_short:
        SwiftCodeBase(**invalid_data_short)
    assert "SWIFT code 'SHORT' must be 8 or 11 characters long." in str(
        excinfo_short.value
    )


def test_swift_code_base_invalid_swift_code_format(base_data):
    invalid_data = base_data.copy()
    invalid_data["swiftCode"] = "INVALIDFORMAT"  # 13 chars, invalid format
    with pytest.raises(ValidationError) as excinfo:
        # This will likely fail length validation first if length check happens before format
        # Or format validation if format check is robust enough for length
        SwiftCodeBase(**invalid_data)
    # Check for either length or format error depending on validation order
    assert "must be 8 or 11 characters long" in str(
        excinfo.value
    ) or "invalid SWIFT code format" in str(excinfo.value)


def test_swift_code_base_invalid_swift_code_format_11_chars(base_data):
    invalid_data = base_data.copy()
    invalid_data["swiftCode"] = "ABCD!FGH123"  # 11 chars, invalid char '!'
    invalid_data["isHeadquarter"] = False  # Make consistent with non-XXX ending
    with pytest.raises(ValidationError) as excinfo:
        SwiftCodeBase(**invalid_data)
    assert "Input 'ABCD!FGH123' has an invalid SWIFT code format." in str(excinfo.value)


def test_swift_code_base_headquarter_consistency_fail_1(base_data):
    invalid_data = base_data.copy()
    invalid_data["swiftCode"] = "BANKUS33XXX"  # Ends in XXX
    invalid_data["isHeadquarter"] = False  # But HQ is False
    with pytest.raises(ValidationError) as excinfo:
        SwiftCodeBase(**invalid_data)
    assert "If swiftCode ends with 'XXX', isHeadquarter must be True" in str(
        excinfo.value
    )


def test_swift_code_base_headquarter_consistency_fail_2(base_data_branch):
    invalid_data = base_data_branch.copy()
    invalid_data["swiftCode"] = "BANKUS33BRC"  # Does not end in XXX
    invalid_data["isHeadquarter"] = True  # But HQ is True
    with pytest.raises(ValidationError) as excinfo:
        SwiftCodeBase(**invalid_data)
    assert "If isHeadquarter is True, swiftCode must end with 'XXX'" in str(
        excinfo.value
    )


# --- Tests for SwiftCodeDetailed ---


def test_swift_code_detailed_valid(detailed_data):
    model = SwiftCodeDetailed(**detailed_data)
    assert model.address == "789 Detail Rd"
    assert model.bankName == "Detailed Bank"
    assert model.countryISO2 == "DE"
    assert model.isHeadquarter is True
    assert model.swiftCode == "DETAILCDXXX"
    assert model.countryName == "GERMANY"


def test_swift_code_detailed_inherits_validation(detailed_data):
    invalid_data = detailed_data.copy()
    invalid_data["countryISO2"] = "DEU"  # Invalid length
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeDetailed(**invalid_data)
    assert "countryISO2 must be 2 characters long" in str(excinfo.value)


# --- Tests for SwiftCodeHeadquarterGroup ---


def test_swift_code_headquarter_group_valid(hq_group_data):
    model = SwiftCodeHeadquarterGroup(**hq_group_data)
    assert model.address == "HQ Ave"
    assert model.bankName == "HQ Bank"
    assert model.countryISO2 == "FR"
    assert model.isHeadquarter is True
    assert model.swiftCode == "HQCODEFRXXX"
    assert model.countryName == "FRANCE"
    assert len(model.branches) == 1
    branch = model.branches[0]
    assert isinstance(branch, SwiftCodeBase)
    assert branch.swiftCode == "HQCODEFRERT"
    assert branch.countryISO2 == "FR"


def test_swift_code_headquarter_group_invalid_branch_prefix(hq_group_data):
    invalid_data = hq_group_data.copy()
    # Keep the valid branch, add an invalid one
    branch_data_invalid = {
        "address": "Branch St 2",
        "bankName": "Branch Bank 2",
        "countryISO2": "fr",
        "isHeadquarter": False,
        "swiftCode": "wrongprefrt",  # Does not match HQ prefix HQCODEFR
    }
    # Ensure branches is mutable if copying from fixture
    invalid_data["branches"] = list(invalid_data["branches"])
    invalid_data["branches"].append(branch_data_invalid)

    with pytest.raises(ValueError) as excinfo:
        SwiftCodeHeadquarterGroup(**invalid_data)
    assert (
        "Branch swiftCode 'WRONGPREFRT' does not match the headquarter prefix 'HQCODEFR'"
        in str(excinfo.value)
    )


# --- Tests for SwiftCodeCountryGroup ---


def test_swift_code_country_group_valid(country_group_data):
    model = SwiftCodeCountryGroup(**country_group_data)
    assert model.countryISO2 == "CA"
    assert model.countryName == "Canada"
    assert len(model.swiftCodes) == 2
    assert isinstance(model.swiftCodes[0], SwiftCodeBase)
    assert isinstance(model.swiftCodes[1], SwiftCodeBase)
    assert model.swiftCodes[0].swiftCode == "BANKONE1XXX"
    assert model.swiftCodes[1].swiftCode == "BANKTWOADFS"


def test_swift_code_country_group_invalid_country_mismatch(country_group_data):
    invalid_data = country_group_data.copy()
    # Ensure swiftCodes is mutable if copying from fixture
    invalid_data["swiftCodes"] = list(invalid_data["swiftCodes"])
    # Modify the second swift code to have the wrong country
    invalid_data["swiftCodes"][1]["countryISO2"] = "us"  # Mismatched country

    with pytest.raises(ValueError) as excinfo:
        SwiftCodeCountryGroup(**invalid_data)
    assert (
        "Swift code 'BANKTWOADFS' countryISO2 'US' does not match the country group 'CA'"
        in str(excinfo.value)
    )

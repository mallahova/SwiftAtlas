import pytest

from swiftatlas.schemas.swift_schemas import (
    SwiftCodeBase,
    SwiftCodeDetailed,
    SwiftCodeHeadquarterGroup,
    SwiftCodeCountryGroup,
)


# Tests for SwiftCodeBase
def test_swift_code_base_valid():
    data = {
        "address": " 123 Main St ",
        "bankName": " Test Bank ",
        "countryISO2": "us",
        "isHeadquarter": True,
        "swiftCode": " testcode ",
    }
    model = SwiftCodeBase(**data)
    assert model.address == "123 Main St"
    assert model.bankName == "Test Bank"
    assert model.countryISO2 == "US"
    assert model.isHeadquarter is True
    assert model.swiftCode == "TESTCODEXXX"  # 8 chars + XXX


def test_swift_code_base_valid_11_char():
    data = {
        "address": "456 Branch Ave",
        "bankName": "Branch Bank",
        "countryISO2": "GB",
        "isHeadquarter": False,
        "swiftCode": "branchcode1",
    }
    model = SwiftCodeBase(**data)
    assert model.countryISO2 == "GB"
    assert model.swiftCode == "BRANCHCODE1"


def test_swift_code_base_invalid_country_iso2_length():
    data = {
        "address": "123 Main St",
        "bankName": "Test Bank",
        "countryISO2": "USA",
        "isHeadquarter": True,
        "swiftCode": "TESTCODE",
    }
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeBase(**data)
    assert "countryISO2 must be 2 characters long" in str(excinfo.value)


def test_swift_code_base_invalid_swift_code_length():
    data = {
        "address": "123 Main St",
        "bankName": "Test Bank",
        "countryISO2": "US",
        "isHeadquarter": True,
        "swiftCode": "SHORT",
    }
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeBase(**data)
    assert "swiftCode must be 8 or 11 characters long" in str(excinfo.value)

    data["swiftCode"] = "TOOLONGCODE123"
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeBase(**data)
    assert "swiftCode must be 8 or 11 characters long" in str(excinfo.value)


def test_swift_code_base_invalid_is_headquarter_mismatch_false():
    """Test validation error when swiftCode ends with XXX but isHeadquarter is False."""
    data = {
        "address": "123 Main St",
        "bankName": "Test Bank",
        "countryISO2": "US",
        "isHeadquarter": False,  # Should be True
        "swiftCode": "TESTCODEXXX",
    }
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeBase(**data)
    assert "If swiftCode ends with 'XXX', isHeadquarter must be True" in str(
        excinfo.value
    )


def test_swift_code_base_invalid_is_headquarter_mismatch_true():
    """Test validation error when swiftCode doesn't end with XXX but isHeadquarter is True."""
    data = {
        "address": "456 Branch Ave",
        "bankName": "Branch Bank",
        "countryISO2": "GB",
        "isHeadquarter": True,  # Should be False
        "swiftCode": "BRANCHCODE1",
    }
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeBase(**data)
    assert "If isHeadquarter is True, swiftCode must end with 'XXX'" in str(
        excinfo.value
    )


# Tests for SwiftCodeDetailed
def test_swift_code_detailed_valid():
    data = {
        "address": " 789 Detail Rd ",
        "bankName": " Detailed Bank ",
        "countryISO2": "de",
        "isHeadquarter": True,
        "swiftCode": " detailcd ",
        "countryName": " germany ",
    }
    model = SwiftCodeDetailed(**data)
    assert model.address == "789 Detail Rd"
    assert model.bankName == "Detailed Bank"
    assert model.countryISO2 == "DE"
    assert model.isHeadquarter is True
    assert model.swiftCode == "DETAILCDXXX"
    assert model.countryName == "GERMANY"


def test_swift_code_detailed_inherits_validation():
    data = {
        "address": "789 Detail Rd",
        "bankName": "Detailed Bank",
        "countryISO2": "DEU",  # Invalid
        "isHeadquarter": True,
        "swiftCode": "DETAILCD",
        "countryName": "Germany",
    }
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeDetailed(**data)
    assert "countryISO2 must be 2 characters long" in str(excinfo.value)


# Tests for SwiftCodeHeadquarterGroup
def test_swift_code_headquarter_group_valid():
    branch_data = {
        "address": "Branch St",
        "bankName": "Branch Bank",
        "countryISO2": "fr",
        "isHeadquarter": False,
        "swiftCode": "hqcodefrert",
    }
    hq_data = {
        "address": " HQ Ave ",
        "bankName": " HQ Bank ",
        "countryISO2": "fr",
        "isHeadquarter": True,
        "swiftCode": " hqcodefr ",
        "countryName": " france ",
        "branches": [branch_data],
    }
    model = SwiftCodeHeadquarterGroup(**hq_data)
    assert model.address == "HQ Ave"
    assert model.bankName == "HQ Bank"
    assert model.countryISO2 == "FR"
    assert model.isHeadquarter is True
    assert model.swiftCode == "HQCODEFRXXX"
    assert model.countryName == "FRANCE"
    assert len(model.branches) == 1
    assert isinstance(model.branches[0], SwiftCodeBase)
    assert model.branches[0].swiftCode == "HQCODEFRERT"
    assert model.branches[0].countryISO2 == "FR"


def test_swift_code_headquarter_group_invalid_branch_prefix():
    """Test validation error when a branch swiftCode prefix doesn't match the HQ."""
    branch_data_valid = {
        "address": "Branch St 1",
        "bankName": "Branch Bank 1",
        "countryISO2": "fr",
        "isHeadquarter": False,
        "swiftCode": "hqcodefrbr1",  # Matches HQ prefix 'HQCODEFR'
    }
    branch_data_invalid = {
        "address": "Branch St 2",
        "bankName": "Branch Bank 2",
        "countryISO2": "fr",
        "isHeadquarter": False,
        "swiftCode": "wrongprefrt",  # Does not match HQ prefix 'HQCODEFR'
    }
    hq_data = {
        "address": "HQ Ave",
        "bankName": "HQ Bank",
        "countryISO2": "fr",
        "isHeadquarter": True,
        "swiftCode": "hqcodefr",  # Becomes HQCODEFRXXX
        "countryName": "france",
        "branches": [branch_data_valid, branch_data_invalid],
    }
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeHeadquarterGroup(**hq_data)
    assert (
        "Branch swiftCode 'WRONGPREFRT' does not match the headquarter prefix 'HQCODEFR'"
        in str(excinfo.value)
    )


# Tests for SwiftCodeCountryGroup
def test_swift_code_country_group_valid():
    swift_code_data_1 = {
        "address": "1 Rue",
        "bankName": "Bank One",
        "countryISO2": "ca",
        "isHeadquarter": True,
        "swiftCode": "bankone1",
    }
    swift_code_data_2 = {
        "address": "2 Ave",
        "bankName": "Bank Two",
        "countryISO2": "ca",
        "isHeadquarter": False,
        "swiftCode": "BANKTWOADFS",
    }
    country_data = {
        "countryISO2": "CA",
        "countryName": "Canada",
        "swiftCodes": [swift_code_data_1, swift_code_data_2],
    }
    model = SwiftCodeCountryGroup(**country_data)
    assert model.countryISO2 == "CA"
    assert model.countryName == "Canada"
    assert len(model.swiftCodes) == 2
    assert isinstance(model.swiftCodes[0], SwiftCodeBase)
    assert isinstance(model.swiftCodes[1], SwiftCodeBase)
    assert model.swiftCodes[0].swiftCode == "BANKONE1XXX"
    assert model.swiftCodes[1].swiftCode == "BANKTWOADFS"


def test_swift_code_country_group_invalid_country_mismatch():
    """Test validation error when a swift code countryISO2 doesn't match the group."""
    swift_code_data_valid = {
        "address": "1 Rue",
        "bankName": "Bank One",
        "countryISO2": "ca",  # Matches group
        "isHeadquarter": True,
        "swiftCode": "bankone1",
    }
    swift_code_data_invalid = {
        "address": "2 Ave",
        "bankName": "Bank Two",
        "countryISO2": "us",  # Does not match group
        "isHeadquarter": False,
        "swiftCode": "BANKTWOADFS",
    }
    country_data = {
        "countryISO2": "CA",
        "countryName": "Canada",
        "swiftCodes": [swift_code_data_valid, swift_code_data_invalid],
    }
    with pytest.raises(ValueError) as excinfo:
        SwiftCodeCountryGroup(**country_data)
    assert (
        "Swift code 'BANKTWOADFS' countryISO2 'US' does not match the country group 'CA'"
        in str(excinfo.value)
    )

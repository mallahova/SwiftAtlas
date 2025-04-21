import re
from pydantic import (
    BaseModel,
    field_validator,
    model_validator,
)
from typing import List


class SwiftCodeBase(BaseModel):
    address: str
    bankName: str
    countryISO2: str
    isHeadquarter: bool
    swiftCode: str

    @field_validator("address", "bankName", "swiftCode")
    @classmethod
    def strip_strings(cls, v):
        return v.strip()

    @field_validator("countryISO2")
    @classmethod
    def validate_country_iso2(cls, v):
        v = v.strip().upper()
        if len(v) != 2:
            raise ValueError("countryISO2 must be 2 characters long")
        if not re.match(r"^[A-Z]{2}$", v):
            raise ValueError("countryISO2 must contain only uppercase letters")
        return v

    @field_validator("swiftCode")
    @classmethod
    def validate_swift_code(cls, v):
        v = v.strip().upper()
        original_input = v
        length = len(v)

        if length != 8 and length != 11:
            raise ValueError(
                f"SWIFT code '{original_input}' must be 8 or 11 characters long."
            )

        if length == 8:
            padded_v = v + "XXX"
        else:
            padded_v = v

        pattern_11 = r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}[A-Z0-9]{3}$"
        if not re.match(pattern_11, padded_v):
            raise ValueError(
                f"Input '{original_input}' has an invalid SWIFT code format."
            )

        return padded_v

    @model_validator(mode="after")
    def check_headquarter_swift_code_consistency(self) -> "SwiftCodeBase":
        if self.swiftCode.endswith("XXX") and not self.isHeadquarter:
            raise ValueError("If swiftCode ends with 'XXX', isHeadquarter must be True")
        if not self.swiftCode.endswith("XXX") and self.isHeadquarter:
            raise ValueError("If isHeadquarter is True, swiftCode must end with 'XXX'")
        return self


class SwiftCodeDetailed(SwiftCodeBase):
    countryName: str

    @field_validator("countryName")
    @classmethod
    def validate_countryName(cls, v):
        v = v.strip()
        return v.upper()


class SwiftCodeHeadquarterGroup(SwiftCodeDetailed):
    branches: List[SwiftCodeBase]

    @model_validator(mode="after")
    def check_branches_swift_prefix(self) -> "SwiftCodeHeadquarterGroup":
        if self.branches:
            parent_prefix = self.swiftCode[:8]
            for branch in self.branches:
                branch_prefix = branch.swiftCode[:8]
                if branch_prefix != parent_prefix:
                    raise ValueError(
                        f"Branch swiftCode '{branch.swiftCode}' does not match the headquarter prefix '{parent_prefix}'"
                    )
        return self


class SwiftCodeCountryGroup(BaseModel):
    countryISO2: str
    countryName: str
    swiftCodes: List[SwiftCodeBase]

    @model_validator(mode="after")
    def check_country_iso2(self) -> "SwiftCodeCountryGroup":
        for swift_code in self.swiftCodes:
            if swift_code.countryISO2 != self.countryISO2:
                raise ValueError(
                    f"Swift code '{swift_code.swiftCode}' countryISO2 '{swift_code.countryISO2}' does not match the country group '{self.countryISO2}'"
                )
        return self

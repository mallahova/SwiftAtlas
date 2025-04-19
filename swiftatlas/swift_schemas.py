from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


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
        if len(v) != 2:
            raise ValueError("countryISO2 must be 2 characters long")
        return v.upper()

    @field_validator("swiftCode")
    @classmethod
    def validate_swift_code(cls, v):
        if len(v) == 8:
            v = v + "XXX"
        if len(v) != 11:
            raise ValueError("swiftCode must be 8 or 11 characters long")
        return v.upper()


class SwiftCodeDetailed(SwiftCodeBase):
    countryName: str

    @field_validator("countryName")
    @classmethod
    def strip_countryName(cls, v):
        return v.strip()


class SwiftCodeHeadquarterGroup(SwiftCodeDetailed):
    branches: List[SwiftCodeBase]


class SwiftCodeCountryGroup(BaseModel):
    countryISO2: str
    countryName: str
    swiftCodes: List[SwiftCodeBase]

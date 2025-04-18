from pydantic import BaseModel, Field
from typing import List, Optional


class SwiftCodeBase(BaseModel):
    address: str
    bankName: str
    countryISO2: str
    isHeadquarter: bool
    swiftCode: str


class SwiftCodeHeadquarter(SwiftCodeBase):
    countryName: str


class SwiftCodeWithBranches(SwiftCodeHeadquarter):
    branches: List[SwiftCodeBase]


class CountrySwiftCodes(BaseModel):
    countryISO2: str
    countryName: str
    swiftCodes: List[SwiftCodeBase]

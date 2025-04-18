from pydantic import BaseModel, Field
from typing import List, Optional


class SwiftCodeBase(BaseModel):
    address: str
    bankName: str
    countryISO2: str
    isHeadquarter: bool
    swiftCode: str


class SwiftCodeBranch(SwiftCodeBase):
    countryName: str


class SwiftCodeHeadquarterResponse(SwiftCodeBranch):
    branches: List[SwiftCodeBase]


class CountrySwiftCodesResponse(BaseModel):
    countryISO2: str
    countryName: str
    swiftCodes: List[SwiftCodeBase]

from pydantic import BaseModel, Field
from typing import List, Optional


class SwiftCodeBase(BaseModel):
    address: str
    bankName: str
    countryISO2: str
    isHeadquarter: bool
    swiftCode: str


class SwiftCodeDetailed(SwiftCodeBase):
    countryName: str


class SwiftCodeHeadquarterGroup(SwiftCodeDetailed):
    branches: List[SwiftCodeBase]


class SwiftCodeCountryGroup(BaseModel):
    countryISO2: str
    countryName: str
    swiftCodes: List[SwiftCodeBase]

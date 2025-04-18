import logging
from bson import ObjectId
from fastapi import APIRouter, HTTPException


from swiftatlas.swift_repository import SwiftRepository
from swiftatlas.swift_schemas import (
    SwiftCodeBase,
    SwiftCodeHeadquarter,
    SwiftCodeWithBranches,
    CountrySwiftCodes,
)

router = APIRouter(prefix="/v1/swift-codes", tags=["swift-codes"])
logger = logging.getLogger(__name__)


async def get_swift_repository() -> SwiftRepository:
    from swiftatlas.main import app

    return SwiftRepository(app.mongodb)


@router.get("/v1/swift-codes/{swift_code}", response_model=SwiftCodeWithBranches)
async def get_swift_code_details(swift_code: str, repo: SwiftRepository):
    swift = await repo.get_swift_with_branches(swift_code)
    if not swift:
        raise HTTPException(status_code=404, detail="SWIFT code not found")
    return swift

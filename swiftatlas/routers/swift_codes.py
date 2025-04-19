import logging
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, status

from typing import Union

from swiftatlas.swift_repository import SwiftRepository
from swiftatlas.swift_schemas import (
    SwiftCodeBase,
    SwiftCodeDetailed,
    SwiftCodeHeadquarterGroup,
    SwiftCodeCountryGroup,
)

router = APIRouter(prefix="/v1/swift-codes", tags=["swift-codes"])
logger = logging.getLogger(__name__)


async def get_swift_repository() -> SwiftRepository:
    from swiftatlas.main import app

    return SwiftRepository(app.mongodb)


@router.get(
    "/{swift_code}", response_model=Union[SwiftCodeBase, SwiftCodeHeadquarterGroup]
)
async def get_swift_code_details(
    swift_code: str, repo: SwiftRepository = Depends(get_swift_repository)
):

    swift = await repo.get_swift_with_branches(swift_code)
    if not swift:
        logger.error("SWIFT code not found", extra={"swift_code": swift_code})
        raise HTTPException(status_code=404, detail="SWIFT code not found")
    logger.info(f"Retrieved SWIFT code details for {swift_code}")
    return swift


@router.get("/country/{country_iso2_code}", response_model=SwiftCodeCountryGroup)
async def get_swift_codes_by_country(
    country_iso2_code: str, repo: SwiftRepository = Depends(get_swift_repository)
):
    """
    Retrieve all SWIFT codes (headquarters and branches) for a specific country.
    """
    result = await repo.get_swifts_by_country(country_iso2_code)
    if not result:
        logger.error(
            "No SWIFT codes found for country",
            extra={"country_iso2_code": country_iso2_code},
        )
        raise HTTPException(
            status_code=404, detail="No SWIFT codes found for this country"
        )
    logger.info(f"Retrieved SWIFT codes for country {country_iso2_code}")
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_swift_code(
    swift_code_data: SwiftCodeDetailed,
    repo: SwiftRepository = Depends(get_swift_repository),
):
    """
    Adds a new SWIFT code entry to the database.
    """
    success = await repo.create_swift(swift_code_data)
    if not success:
        logger.warning(
            "Attempted to add duplicate SWIFT code",
            extra={"swift_code": swift_code_data.swiftCode},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Attempted to add duplicate SWIFT code {swift_code_data.swiftCode}.",
        )
    logger.info(
        f"Successfully added SWIFT code {swift_code_data.swiftCode}",
        extra={"swift_code": swift_code_data.swiftCode},
    )
    return {"message": f"SWIFT code {swift_code_data.swiftCode} added successfully."}


@router.delete("/{swift_code}", status_code=status.HTTP_200_OK)
async def delete_swift_code(
    swift_code: str, repo: SwiftRepository = Depends(get_swift_repository)
):
    """
    Deletes a SWIFT code entry from the database.
    """
    result = await repo.delete_swift({"swiftCode": swift_code})
    if result.deleted_count == 0:
        logger.warning(
            "Attempted to delete non-existent SWIFT code",
            extra={"swift_code": swift_code},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SWIFT code {swift_code} not found.",
        )
    logger.info(
        f"Successfully deleted SWIFT code {swift_code}",
        extra={"swift_code": swift_code},
    )
    return {"message": f"SWIFT code {swift_code} deleted successfully."}

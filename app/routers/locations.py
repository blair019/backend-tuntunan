from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from app.services.nominatim import (
    NominatimRateLimitError,
    NominatimUnavailableError,
    search_locations,
)


router = APIRouter(
    prefix="/api/locations",
    tags=["Locations"],
)


@router.get("/search")
async def location_search(
        q: str = Query(
            ...,
            min_length=2,
            max_length=150,
            description="Location search query",
        ),
        limit: int = Query(
            default=5,
            ge=1,
            le=10,
            description=(
                    "Maximum number of "
                    "location suggestions"
            ),
        ),
):
    try:
        locations = await search_locations(
            query=q,
            limit=limit,
        )

        return {
            "success": True,
            "count": len(locations),
            "locations": locations,
        }

    except NominatimRateLimitError as error:
        raise HTTPException(
            status_code=429,
            detail=(
                "Location search is temporarily busy. "
                "Please wait a moment and try again."
            ),
        ) from error

    except NominatimUnavailableError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Location search is temporarily unavailable. "
                "Please try again shortly."
            ),
        ) from error

    except Exception as error:
        print(
            "[LOCATIONS] "
            f"Unexpected search error: "
            f"{type(error).__name__}: "
            f"{str(error)}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred "
                "while searching locations."
            ),
        ) from error
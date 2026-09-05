from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

import httpx

from app.services.nominatim import (
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

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "OpenStreetMap location "
                "search failed: "
                f"{error.response.status_code}"
            ),
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not connect to "
                "OpenStreetMap location search."
            ),
        )
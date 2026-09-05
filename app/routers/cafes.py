from fastapi import APIRouter, HTTPException, Query
import httpx

from app.services.openstreetmap import search_nearby_cafes


router = APIRouter(
    prefix="/api/cafes",
    tags=["Cafes"],
)


@router.get("/nearby")
async def nearby_cafes(
        lat: float = Query(
            ...,
            ge=-90,
            le=90,
            description="Latitude",
        ),
        lng: float = Query(
            ...,
            ge=-180,
            le=180,
            description="Longitude",
        ),
        radius: int = Query(
            default=3000,
            gt=0,
            le=10000,
            description="Search radius in meters",
        ),
):
    try:
        cafes = await search_nearby_cafes(
            latitude=lat,
            longitude=lng,
            radius=radius,
        )

        return {
            "success": True,
            "count": len(cafes),
            "cafes": cafes,
        }

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"OpenStreetMap request failed: {error.response.status_code}",
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to OpenStreetMap.",
        )
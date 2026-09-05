import httpx


NOMINATIM_SEARCH_URL = (
    "https://nominatim.openstreetmap.org/search"
)

HEADERS = {
    "User-Agent": (
        "TuntunanCafeFinder/1.0 "
        "(development)"
    ),
    "Accept": "application/json",
}


async def search_locations(
        query: str,
        limit: int = 5,
):
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": limit,
        "countrycodes": "ph",
    }

    async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0),
            headers=HEADERS,
    ) as client:
        response = await client.get(
            NOMINATIM_SEARCH_URL,
            params=params,
        )

        response.raise_for_status()

        data = response.json()

    locations = []

    for result in data:
        latitude = result.get("lat")
        longitude = result.get("lon")

        if latitude is None or longitude is None:
            continue

        address = result.get(
            "address",
            {},
        )

        locations.append(
            {
                "place_id": result.get(
                    "place_id"
                ),
                "osm_id": result.get(
                    "osm_id"
                ),
                "osm_type": result.get(
                    "osm_type"
                ),

                "name": get_location_name(
                    result
                ),

                "display_name": result.get(
                    "display_name"
                ),

                "latitude": float(
                    latitude
                ),
                "longitude": float(
                    longitude
                ),

                "type": result.get(
                    "type"
                ),

                "category": result.get(
                    "category"
                ),

                "city": (
                        address.get("city")
                        or address.get("town")
                        or address.get("municipality")
                        or address.get("village")
                ),

                "province": (
                        address.get("state")
                        or address.get("province")
                ),

                "country": address.get(
                    "country"
                ),

                "source": "openstreetmap",
            }
        )

    return locations


def get_location_name(
        result: dict,
):
    name = result.get("name")

    if name:
        return name

    display_name = result.get(
        "display_name",
        "",
    )

    if display_name:
        return display_name.split(",")[0]

    return "Unknown Location"
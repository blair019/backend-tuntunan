import asyncio

import httpx


NOMINATIM_SEARCH_URL = (
    "https://nominatim.openstreetmap.org/search"
)

HEADERS = {
    "User-Agent": (
        "TuntunanCafeFinder/1.0 "
        "(https://tuntunan.vercel.app)"
    ),
    "Accept": "application/json",
}

REQUEST_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=20.0,
    write=10.0,
    pool=10.0,
)

MAX_RETRIES = 2


async def search_locations(
        query: str,
        limit: int = 5,
):
    query = query.strip()

    if not query:
        return []

    # Keep result count reasonable.
    limit = max(
        1,
        min(limit, 10),
    )

    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": limit,
        "countrycodes": "ph",
    }

    data = await request_nominatim(
        params=params,
    )

    locations = []

    for result in data:
        latitude = result.get("lat")
        longitude = result.get("lon")

        if (
                latitude is None
                or longitude is None
        ):
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
                        or address.get(
                    "municipality"
                )
                        or address.get(
                    "village"
                )
                ),

                "province": (
                        address.get("state")
                        or address.get(
                    "province"
                )
                ),

                "country": address.get(
                    "country"
                ),

                "source": "openstreetmap",
            }
        )

    return locations


async def request_nominatim(
        params: dict,
):
    last_error = None

    async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
            follow_redirects=True,
    ) as client:

        for attempt in range(
                1,
                MAX_RETRIES + 1,
        ):
            try:
                print(
                    "[NOMINATIM] "
                    f"Search attempt "
                    f"{attempt}/{MAX_RETRIES}"
                )

                response = await client.get(
                    NOMINATIM_SEARCH_URL,
                    params=params,
                )

                print(
                    "[NOMINATIM] "
                    f"Response: "
                    f"{response.status_code}"
                )

                if response.status_code == 429:
                    print(
                        "[NOMINATIM] "
                        "Rate limited by server."
                    )

                    response.raise_for_status()

                if response.status_code in {
                    502,
                    503,
                    504,
                }:
                    last_error = (
                        httpx.HTTPStatusError(
                            "Temporary Nominatim "
                            "server error",
                            request=response.request,
                            response=response,
                        )
                    )

                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(2)
                        continue

                    raise last_error

                response.raise_for_status()

                data = response.json()

                if not isinstance(
                        data,
                        list,
                ):
                    raise RuntimeError(
                        "Invalid Nominatim response."
                    )

                print(
                    "[NOMINATIM] "
                    f"Success: "
                    f"{len(data)} results"
                )

                return data

            except httpx.TimeoutException as error:
                print(
                    "[NOMINATIM] "
                    f"Timeout: {error}"
                )

                last_error = error

                if attempt < MAX_RETRIES:
                    await asyncio.sleep(2)
                    continue

            except httpx.HTTPStatusError as error:
                print(
                    "[NOMINATIM] "
                    f"HTTP error: {error}"
                )

                last_error = error

                break

            except httpx.RequestError as error:
                print(
                    "[NOMINATIM] "
                    f"Connection error: {error}"
                )

                last_error = error

                if attempt < MAX_RETRIES:
                    await asyncio.sleep(2)
                    continue

            except (
                    ValueError,
                    RuntimeError,
            ) as error:
                print(
                    "[NOMINATIM] "
                    f"Invalid response: {error}"
                )

                last_error = error

                break

    if last_error:
        raise last_error

    raise RuntimeError(
        "Nominatim request failed."
    )


def get_location_name(
        result: dict,
):
    name = result.get("name")

    if name:
        return name.strip()

    display_name = result.get(
        "display_name",
        "",
    )

    if display_name:
        return (
            display_name
            .split(",")[0]
            .strip()
        )

    return "Unknown Location"
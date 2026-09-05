import asyncio
import time

import httpx


# ============================================================
# NOMINATIM CONFIGURATION
# ============================================================

NOMINATIM_SEARCH_URL = (
    "https://nominatim.openstreetmap.org/search"
)

HEADERS = {
    "User-Agent": (
        "TuntunanCafeFinder/1.0 "
        "(https://frontend-tuntunan.vercel.app)"
    ),
    "Accept": "application/json",
}

REQUEST_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=20.0,
    write=10.0,
    pool=10.0,
)


# ============================================================
# RATE LIMITING
# ============================================================

# Public Nominatim requires no more than
# approximately one request per second.
MIN_REQUEST_INTERVAL = 1.1

_request_lock = asyncio.Lock()
_last_request_time = 0.0


# ============================================================
# SIMPLE IN-MEMORY CACHE
# ============================================================

CACHE_TTL_SECONDS = 60 * 60

_location_cache: dict[
    str,
    tuple[float, list]
] = {}


def get_cache_key(
        query: str,
        limit: int,
) -> str:
    return (
        f"{query.strip().lower()}"
        f":{limit}"
    )


def get_cached_result(
        key: str,
):
    cached = _location_cache.get(
        key
    )

    if not cached:
        return None

    created_at, data = cached

    age = (
            time.monotonic()
            - created_at
    )

    if age > CACHE_TTL_SECONDS:
        _location_cache.pop(
            key,
            None,
        )

        return None

    return data


def set_cached_result(
        key: str,
        data: list,
):
    _location_cache[key] = (
        time.monotonic(),
        data,
    )


# ============================================================
# SEARCH
# ============================================================

async def search_locations(
        query: str,
        limit: int = 5,
):
    query = query.strip()

    if not query:
        return []

    limit = max(
        1,
        min(limit, 10),
    )

    cache_key = get_cache_key(
        query,
        limit,
    )

    cached = get_cached_result(
        cache_key
    )

    if cached is not None:
        print(
            "[NOMINATIM] "
            f"Cache hit: {query}"
        )

        return cached

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
        latitude = result.get(
            "lat"
        )

        longitude = result.get(
            "lon"
        )

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

    set_cached_result(
        cache_key,
        locations,
    )

    return locations


# ============================================================
# NOMINATIM REQUEST
# ============================================================

async def request_nominatim(
        params: dict,
):
    global _last_request_time

    async with _request_lock:

        # ----------------------------------------------------
        # Respect Nominatim rate limit
        # ----------------------------------------------------

        now = time.monotonic()

        elapsed = (
                now
                - _last_request_time
        )

        wait_time = (
                MIN_REQUEST_INTERVAL
                - elapsed
        )

        if wait_time > 0:
            print(
                "[NOMINATIM] "
                f"Rate-limit wait: "
                f"{wait_time:.2f}s"
            )

            await asyncio.sleep(
                wait_time
            )

        try:
            async with httpx.AsyncClient(
                    timeout=REQUEST_TIMEOUT,
                    headers=HEADERS,
                    follow_redirects=True,
            ) as client:

                print(
                    "[NOMINATIM] "
                    f"Searching: "
                    f"{params.get('q')}"
                )

                response = await client.get(
                    NOMINATIM_SEARCH_URL,
                    params=params,
                )

                _last_request_time = (
                    time.monotonic()
                )

                print(
                    "[NOMINATIM] "
                    f"Response: "
                    f"{response.status_code}"
                )

                # ------------------------------------------------
                # Rate limited
                # ------------------------------------------------

                if response.status_code == 429:
                    retry_after = (
                        response.headers.get(
                            "Retry-After"
                        )
                    )

                    print(
                        "[NOMINATIM] "
                        "Rate limited."
                    )

                    if retry_after:
                        print(
                            "[NOMINATIM] "
                            f"Retry-After: "
                            f"{retry_after}"
                        )

                    raise NominatimRateLimitError(
                        "Location search is temporarily "
                        "rate limited."
                    )

                # ------------------------------------------------
                # Temporary upstream failure
                # ------------------------------------------------

                if response.status_code in {
                    502,
                    503,
                    504,
                }:
                    raise NominatimUnavailableError(
                        "Location search provider "
                        "is temporarily unavailable."
                    )

                response.raise_for_status()

                data = response.json()

                if not isinstance(
                        data,
                        list,
                ):
                    raise NominatimUnavailableError(
                        "Invalid response from "
                        "location search provider."
                    )

                print(
                    "[NOMINATIM] "
                    f"Success: "
                    f"{len(data)} results"
                )

                return data

        except NominatimRateLimitError:
            raise

        except NominatimUnavailableError:
            raise

        except httpx.TimeoutException as error:
            print(
                "[NOMINATIM] "
                f"Timeout: {error}"
            )

            raise NominatimUnavailableError(
                "Location search timed out."
            ) from error

        except httpx.HTTPStatusError as error:
            print(
                "[NOMINATIM] "
                f"HTTP error: {error}"
            )

            raise NominatimUnavailableError(
                "Location search provider "
                "returned an error."
            ) from error

        except httpx.RequestError as error:
            print(
                "[NOMINATIM] "
                f"Connection error: {error}"
            )

            raise NominatimUnavailableError(
                "Could not connect to "
                "location search provider."
            ) from error

        except ValueError as error:
            print(
                "[NOMINATIM] "
                f"Invalid JSON: {error}"
            )

            raise NominatimUnavailableError(
                "Invalid location search response."
            ) from error


# ============================================================
# CUSTOM ERRORS
# ============================================================

class NominatimRateLimitError(
    RuntimeError
):
    pass


class NominatimUnavailableError(
    RuntimeError
):
    pass


# ============================================================
# LOCATION NAME
# ============================================================

def get_location_name(
        result: dict,
):
    name = result.get(
        "name"
    )

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
import math

import httpx


OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

HEADERS = {
    "User-Agent": "TuntunanCafeFinder/1.0 (development)",
    "Accept": "application/json",
}


async def search_nearby_cafes(
        latitude: float,
        longitude: float,
        radius: int = 3000,
):
    query = f"""
    [out:json][timeout:25];

    (
      node["amenity"="cafe"](around:{radius},{latitude},{longitude});
      way["amenity"="cafe"](around:{radius},{latitude},{longitude});
      relation["amenity"="cafe"](around:{radius},{latitude},{longitude});
    );

    out center tags;
    """

    data = await request_overpass(query)

    cafes = []
    seen = set()

    for element in data.get("elements", []):
        tags = element.get("tags", {})

        latitude_value = element.get("lat")
        longitude_value = element.get("lon")

        if latitude_value is None or longitude_value is None:
            center = element.get("center", {})

            latitude_value = center.get("lat")
            longitude_value = center.get("lon")

        if latitude_value is None or longitude_value is None:
            continue

        name = tags.get("name", "Unnamed Cafe").strip()

        distance_meters = calculate_distance(
            latitude,
            longitude,
            latitude_value,
            longitude_value,
        )

        address = build_address(tags)

        phone = (
                tags.get("contact:phone")
                or tags.get("phone")
        )

        website = (
                tags.get("contact:website")
                or tags.get("website")
        )

        facebook = (
                tags.get("contact:facebook")
                or tags.get("facebook")
        )

        instagram = (
                tags.get("contact:instagram")
                or tags.get("instagram")
        )

        duplicate_key = (
            name.lower(),
            round(latitude_value, 5),
            round(longitude_value, 5),
        )

        if duplicate_key in seen:
            continue

        seen.add(duplicate_key)

        has_contact_info = any([
            phone,
            website,
            facebook,
            instagram,
        ])

        cafe = {
            "osm_id": element.get("id"),
            "osm_type": element.get("type"),

            "name": name,

            "latitude": latitude_value,
            "longitude": longitude_value,

            "distance_meters": round(
                distance_meters
            ),

            "distance_km": round(
                distance_meters / 1000,
                2,
                ),

            "display_distance": format_distance(
                distance_meters
            ),

            "address": address,

            "phone": phone,
            "website": website,
            "facebook": facebook,
            "instagram": instagram,

            "has_contact_info": has_contact_info,

            "opening_hours": tags.get(
                "opening_hours"
            ),

            "cuisine": tags.get(
                "cuisine"
            ),

            "wifi": parse_boolean(
                tags.get("internet_access")
            ),

            "outdoor_seating": parse_boolean(
                tags.get("outdoor_seating")
            ),

            "wheelchair": tags.get(
                "wheelchair"
            ),

            "takeaway": parse_boolean(
                tags.get("takeaway")
            ),

            "delivery": parse_boolean(
                tags.get("delivery")
            ),

            "source": "openstreetmap",
        }

        cafes.append(cafe)

    cafes.sort(
        key=lambda cafe: (
            cafe["name"] == "Unnamed Cafe",
            cafe["distance_meters"],
        )
    )

    return cafes


async def request_overpass(
        query: str,
):
    last_error = None

    async with httpx.AsyncClient(
            timeout=httpx.Timeout(35.0),
            headers=HEADERS,
    ) as client:

        for url in OVERPASS_URLS:

            try:
                print(
                    f"Trying Overpass server: {url}"
                )

                response = await client.post(
                    url,
                    data={
                        "data": query,
                    },
                )

                print(
                    f"Overpass response: "
                    f"{response.status_code} "
                    f"from {url}"
                )

                response.raise_for_status()

                return response.json()

            except (
                    httpx.HTTPStatusError,
                    httpx.RequestError,
            ) as error:

                print(
                    f"Overpass server failed: "
                    f"{url} -> {error}"
                )

                last_error = error

    if last_error:
        raise last_error

    raise RuntimeError(
        "No Overpass servers were available."
    )


def calculate_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
):
    earth_radius = 6371000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad)
            * math.cos(lat2_rad)
            * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return earth_radius * c


def format_distance(
        distance_meters: float,
):
    if distance_meters < 1000:
        return f"{round(distance_meters)} m"

    return f"{distance_meters / 1000:.1f} km"


def build_address(
        tags: dict,
):
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
        tags.get("addr:province"),
    ]

    parts = [
        str(part).strip()
        for part in parts
        if part
    ]

    if not parts:
        return None

    return ", ".join(parts)


def parse_boolean(
        value,
):
    if not value:
        return None

    value = str(value).lower().strip()

    if value in [
        "yes",
        "true",
        "1",
        "wlan",
        "free",
    ]:
        return True

    if value in [
        "no",
        "false",
        "0",
    ]:
        return False

    return None
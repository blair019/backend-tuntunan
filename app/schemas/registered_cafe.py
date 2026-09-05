from typing import Literal

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class DayHours(BaseModel):
    enabled: bool = True
    open: str = "08:00"
    close: str = "20:00"
    is_24_hours: bool = False


class OpeningHours(BaseModel):
    monday: DayHours
    tuesday: DayHours
    wednesday: DayHours
    thursday: DayHours
    friday: DayHours
    saturday: DayHours
    sunday: DayHours


class CafeAmenities(BaseModel):
    wifi: bool = False
    outlets: bool = False
    outdoor_seating: bool = False
    work_friendly: bool = False
    pet_friendly: bool = False
    wheelchair_accessible: bool = False


class CafeRegistrationCreate(BaseModel):
    cafe_name: str = Field(
        min_length=2,
        max_length=255,
    )

    city: str = Field(
        min_length=2,
        max_length=255,
    )

    area: str | None = None

    address: str = Field(
        min_length=3,
    )

    latitude: float | None = None
    longitude: float | None = None

    amenities: CafeAmenities

    opening_hours: OpeningHours

    instagram: str | None = None
    website: str | None = None

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    owner_name: str = Field(
        min_length=2,
        max_length=255,
    )

    owner_email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


# =========================================================
# UPDATE
# =========================================================

class RegisteredCafeUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=255,
    )

    city: str = Field(
        min_length=2,
        max_length=255,
    )

    area: str | None = None

    address: str = Field(
        min_length=3,
    )

    latitude: float | None = None
    longitude: float | None = None

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    instagram: str | None = None
    website: str | None = None

    amenities: CafeAmenities

    opening_hours: OpeningHours


class RegisteredCafeResponse(BaseModel):
    id: int
    slug: str

    name: str
    city: str
    area: str | None
    address: str

    latitude: float | None
    longitude: float | None

    description: str | None

    instagram: str | None
    website: str | None

    amenities: dict
    opening_hours: dict

    cover_image_url: str | None

    gallery_image_urls: list[str]

    status: Literal[
                "pending",
                "approved",
                "rejected",
            ] | str

    model_config = {
        "from_attributes": True,
    }
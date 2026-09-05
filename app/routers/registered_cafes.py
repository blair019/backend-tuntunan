import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cafe import RegisteredCafe

from app.schemas.registered_cafe import (
    CafeRegistrationCreate,
    RegisteredCafeResponse,
    RegisteredCafeUpdate,
)

from app.services.registered_cafes import (
    generate_unique_slug,
    hash_password,
    save_uploaded_image,
)


router = APIRouter(
    prefix="/api/cafes",
    tags=["Registered Cafes"],
)


# =========================================================
# REGISTER
# =========================================================

@router.post(
    "/register",
    response_model=RegisteredCafeResponse,
    status_code=201,
)
async def register_cafe(
        payload: str = Form(...),
        cover_image: UploadFile | None = File(default=None),
        gallery_images: list[UploadFile] | None = File(default=None),
        db: Session = Depends(get_db),
):
    try:
        raw_payload = json.loads(
            payload
        )

        registration = (
            CafeRegistrationCreate.model_validate(
                raw_payload
            )
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        )

    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail=error.errors(),
        )


    gallery_images = (
            gallery_images or []
    )


    if len(gallery_images) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum of 5 gallery images allowed.",
        )


    slug = generate_unique_slug(
        db,
        registration.cafe_name,
    )


    cafe = RegisteredCafe(
        slug=slug,

        name=registration.cafe_name,

        city=registration.city,
        area=registration.area,
        address=registration.address,

        latitude=registration.latitude,
        longitude=registration.longitude,

        description=registration.description,

        instagram=registration.instagram,
        website=registration.website,

        amenities=(
            registration
            .amenities
            .model_dump()
        ),

        opening_hours=(
            registration
            .opening_hours
            .model_dump()
        ),

        owner_name=registration.owner_name,

        owner_email=(
            str(
                registration.owner_email
            )
            .strip()
            .lower()
        ),

        password_hash=hash_password(
            registration.password
        ),

        status="approved",
    )


    db.add(cafe)
    db.commit()
    db.refresh(cafe)


    try:
        if cover_image:
            cafe.cover_image_url = (
                await save_uploaded_image(
                    cafe_id=cafe.id,
                    image=cover_image,
                    prefix="cover",
                )
            )


        gallery_urls: list[str] = []


        for index, image in enumerate(
                gallery_images
        ):
            image_url = (
                await save_uploaded_image(
                    cafe_id=cafe.id,
                    image=image,
                    prefix=f"gallery-{index + 1}",
                )
            )

            gallery_urls.append(
                image_url
            )


        cafe.gallery_image_urls = (
            gallery_urls
        )


        db.commit()
        db.refresh(cafe)


    except ValueError as error:
        db.delete(cafe)
        db.commit()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


    return cafe


# =========================================================
# GET ALL
# =========================================================

@router.get(
    "/registered",
    response_model=list[
        RegisteredCafeResponse
    ],
)
def get_registered_cafes(
        db: Session = Depends(get_db),
):
    cafes = db.scalars(
        select(
            RegisteredCafe
        )
        .where(
            RegisteredCafe.status
            == "approved"
        )
        .order_by(
            RegisteredCafe
            .created_at
            .desc()
        )
    ).all()


    return list(cafes)


# =========================================================
# UPDATE
# =========================================================

@router.put(
    "/registered/{cafe_id}",
    response_model=RegisteredCafeResponse,
)
def update_registered_cafe(
        cafe_id: int,
        payload: RegisteredCafeUpdate,
        db: Session = Depends(get_db),
):
    cafe = db.scalar(
        select(
            RegisteredCafe
        ).where(
            RegisteredCafe.id
            == cafe_id
        )
    )


    if cafe is None:
        raise HTTPException(
            status_code=404,
            detail="Cafe not found.",
        )


    cafe.name = (
        payload.name
    )


    cafe.city = (
        payload.city
    )


    cafe.area = (
        payload.area
    )


    cafe.address = (
        payload.address
    )


    cafe.latitude = (
        payload.latitude
    )


    cafe.longitude = (
        payload.longitude
    )


    cafe.description = (
        payload.description
    )


    cafe.instagram = (
        payload.instagram
    )


    cafe.website = (
        payload.website
    )


    cafe.amenities = (
        payload
        .amenities
        .model_dump()
    )


    cafe.opening_hours = (
        payload
        .opening_hours
        .model_dump()
    )


    db.commit()
    db.refresh(cafe)


    return cafe


# =========================================================
# GET ONE
# =========================================================

@router.get(
    "/registered/{slug}",
    response_model=RegisteredCafeResponse,
)
def get_registered_cafe(
        slug: str,
        db: Session = Depends(get_db),
):
    cafe = db.scalar(
        select(
            RegisteredCafe
        ).where(
            RegisteredCafe.slug
            == slug
        )
    )


    if cafe is None:
        raise HTTPException(
            status_code=404,
            detail="Cafe not found.",
        )


    if (
            cafe.status
            != "approved"
    ):
        raise HTTPException(
            status_code=404,
            detail="Cafe not found.",
        )


    return cafe
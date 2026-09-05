import hashlib
import os
import re
import secrets
import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cafe import RegisteredCafe


UPLOAD_ROOT = os.path.join(
    "uploads",
    "cafes",
)


def slugify(value: str) -> str:
    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )

    return value.strip("-")


def generate_unique_slug(
        db: Session,
        cafe_name: str,
) -> str:
    base_slug = slugify(
        cafe_name
    )

    if not base_slug:
        base_slug = "cafe"

    slug = base_slug
    counter = 2

    while True:
        existing = db.scalar(
            select(
                RegisteredCafe
            ).where(
                RegisteredCafe.slug
                == slug
            )
        )

        if existing is None:
            return slug

        slug = (
            f"{base_slug}-{counter}"
        )

        counter += 1


def hash_password(
        password: str,
) -> str:
    salt = secrets.token_bytes(16)

    hashed = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=64,
    )

    return (
        f"{salt.hex()}"
        f"${hashed.hex()}"
    )


def verify_password(
        password: str,
        stored_hash: str,
) -> bool:
    try:
        salt_hex, hash_hex = (
            stored_hash.split(
                "$",
                1,
            )
        )

        salt = bytes.fromhex(
            salt_hex
        )

        expected_hash = bytes.fromhex(
            hash_hex
        )

        actual_hash = hashlib.scrypt(
            password.encode(
                "utf-8"
            ),
            salt=salt,
            n=16384,
            r=8,
            p=1,
            dklen=64,
        )

        return secrets.compare_digest(
            actual_hash,
            expected_hash,
        )

    except (
            ValueError,
            TypeError,
    ):
        return False


async def save_uploaded_image(
        cafe_id: int,
        image: UploadFile,
        prefix: str,
) -> str:
    if not image.content_type:
        raise ValueError(
            "Image content type is missing."
        )

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    extension = allowed_types.get(
        image.content_type
    )

    if extension is None:
        raise ValueError(
            "Only JPG, PNG, and WEBP images are allowed."
        )

    cafe_folder = os.path.join(
        UPLOAD_ROOT,
        str(cafe_id),
    )

    os.makedirs(
        cafe_folder,
        exist_ok=True,
    )

    filename = (
        f"{prefix}-"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    path = os.path.join(
        cafe_folder,
        filename,
    )

    contents = await image.read()

    max_size = (
            10 * 1024 * 1024
    )

    if len(contents) > max_size:
        raise ValueError(
            "Each image must be smaller than 10 MB."
        )

    with open(
            path,
            "wb",
    ) as file:
        file.write(contents)

    return (
        f"/uploads/cafes/"
        f"{cafe_id}/"
        f"{filename}"
    )
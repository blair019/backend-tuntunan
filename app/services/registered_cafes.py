import asyncio
import hashlib
import os
import re
import secrets
import uuid

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cafe import RegisteredCafe


# ============================================================
# CLOUDINARY CONFIGURATION
# ============================================================

CLOUDINARY_CLOUD_NAME = os.getenv(
    "CLOUDINARY_CLOUD_NAME"
)

CLOUDINARY_API_KEY = os.getenv(
    "CLOUDINARY_API_KEY"
)

CLOUDINARY_API_SECRET = os.getenv(
    "CLOUDINARY_API_SECRET"
)


def configure_cloudinary():
    if not CLOUDINARY_CLOUD_NAME:
        raise RuntimeError(
            "CLOUDINARY_CLOUD_NAME "
            "environment variable is missing."
        )

    if not CLOUDINARY_API_KEY:
        raise RuntimeError(
            "CLOUDINARY_API_KEY "
            "environment variable is missing."
        )

    if not CLOUDINARY_API_SECRET:
        raise RuntimeError(
            "CLOUDINARY_API_SECRET "
            "environment variable is missing."
        )

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )


# ============================================================
# SLUG HELPERS
# ============================================================

def slugify(
        value: str,
) -> str:
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


# ============================================================
# PASSWORD HELPERS
# ============================================================

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


# ============================================================
# CLOUDINARY IMAGE UPLOAD
# ============================================================

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
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if image.content_type not in allowed_types:
        raise ValueError(
            "Only JPG, PNG, and WEBP "
            "images are allowed."
        )

    contents = await image.read()

    max_size = (
            10 * 1024 * 1024
    )

    if len(contents) > max_size:
        raise ValueError(
            "Each image must be "
            "smaller than 10 MB."
        )

    if len(contents) == 0:
        raise ValueError(
            "Uploaded image is empty."
        )

    configure_cloudinary()

    public_id = (
        f"{prefix}-"
        f"{uuid.uuid4().hex}"
    )

    folder = (
        f"tuntunan/cafes/"
        f"{cafe_id}"
    )

    try:
        print(
            "[CLOUDINARY] "
            f"Uploading image for "
            f"cafe {cafe_id}"
        )

        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            contents,
            folder=folder,
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )

        secure_url = result.get(
            "secure_url"
        )

        if not secure_url:
            raise RuntimeError(
                "Cloudinary did not return "
                "an image URL."
            )

        print(
            "[CLOUDINARY] "
            f"Upload successful: "
            f"{secure_url}"
        )

        return secure_url

    except Exception as error:
        print(
            "[CLOUDINARY] "
            f"Upload failed: {error}"
        )

        raise RuntimeError(
            "Unable to upload image "
            "to Cloudinary."
        ) from error
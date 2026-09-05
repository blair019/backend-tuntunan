from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import (
    BaseModel,
    EmailStr,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cafe import RegisteredCafe
from app.services.registered_cafes import verify_password


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# =========================================================
# REQUEST / RESPONSE SCHEMAS
# =========================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool

    cafe_id: int
    slug: str
    cafe_name: str

    owner_name: str
    owner_email: str

    status: str


# =========================================================
# LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
        credentials: LoginRequest,
        db: Session = Depends(get_db),
):
    email = str(
        credentials.email
    ).strip().lower()


    cafe = db.scalar(
        select(
            RegisteredCafe
        ).where(
            RegisteredCafe.owner_email
            == email
        )
    )


    # Do not reveal whether the email exists.
    if cafe is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )


    password_is_valid = verify_password(
        credentials.password,
        cafe.password_hash,
    )


    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )


    if cafe.status == "rejected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This café registration has been rejected.",
        )


    return LoginResponse(
        success=True,

        cafe_id=cafe.id,
        slug=cafe.slug,
        cafe_name=cafe.name,

        owner_name=cafe.owner_name,
        owner_email=cafe.owner_email,

        status=cafe.status,
    )
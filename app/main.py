from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db

from app.routers.auth import (
    router as auth_router,
)
from app.routers.cafes import (
    router as cafes_router,
)
from app.routers.locations import (
    router as locations_router,
)
from app.routers.registered_cafes import (
    router as registered_cafes_router,
)


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    yield


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Tuntunan API",
    description="Backend API for Tuntunan Cafe Finder",
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================================
# CORS
# =========================================================

allowed_origins = [
    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    # Production frontend
    "https://frontend-tuntunan.vercel.app",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(
    cafes_router
)

app.include_router(
    locations_router
)

app.include_router(
    registered_cafes_router
)

app.include_router(
    auth_router
)


# =========================================================
# BASE ROUTES
# =========================================================

@app.get("/")
def root():
    return {
        "app": "Tuntunan",
        "message": "Tuntunan API is running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }
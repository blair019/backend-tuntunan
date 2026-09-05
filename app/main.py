from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    yield


app = FastAPI(
    title="Tuntunan API",
    description="Backend API for Tuntunan Cafe Finder",
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://frontend-tuntunan.vercel.app/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STATIC UPLOADS
# =========================================================

app.mount(
    "/uploads",
    StaticFiles(
        directory="uploads"
    ),
    name="uploads",
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
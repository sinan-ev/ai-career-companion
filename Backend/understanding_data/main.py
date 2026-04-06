from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import router
from config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{settings.app_name} starting...")
    print(f"Docs: http://localhost:8000/docs")
    yield
    print("🛑 Shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Universal Data Understanding Agent",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["Analysis"])


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
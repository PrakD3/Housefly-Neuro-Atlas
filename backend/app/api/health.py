"""Health check endpoint for Drosophila-NeuroAtlas."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Return the current health status of the backend service."""
    return {"status": "ok"}

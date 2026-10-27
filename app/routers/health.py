"""Health check router for monitoring and pre-warming."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = "ok"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Lightweight health probe for uptime monitors and client cold-start mitigation. Never queries PostgreSQL.",
)
async def get_health() -> HealthResponse:
    """Return 200 OK immediately without database queries."""
    return HealthResponse(status="ok")

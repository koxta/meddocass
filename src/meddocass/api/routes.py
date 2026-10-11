from fastapi import APIRouter

from meddocass.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
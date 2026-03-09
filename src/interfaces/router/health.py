from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/livez")
def liveness_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readiness_check() -> dict[str, str]:
    return {"status": "ready"}

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check() -> dict[str, Any]:
    return {"status": "healthy"}

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/api/v1/version")
async def version():
    return {"version": "0.1.0"} 
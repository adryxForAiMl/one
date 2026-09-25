from fastapi import APIRouter

router = APIRouter()

@router.get("/health", response_model=dict)
async def health_check():
    return {"status": "healthy"}
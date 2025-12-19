from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_kyc_status():
    return {"message": "KYC module"}

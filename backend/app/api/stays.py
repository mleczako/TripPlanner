from fastapi import APIRouter

router = APIRouter()


@router.get("/stays")
def list_stays():
    return {"stays": []}

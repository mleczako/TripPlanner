from fastapi import APIRouter

router = APIRouter()


@router.get("/alerts")
def list_alerts():
    return {"alerts": []}

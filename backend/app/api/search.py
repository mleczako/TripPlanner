from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.search import SearchPreferences, SearchResponse
from app.packages.stays.search_service import search_stays

router = APIRouter(prefix="/search", tags=["Search"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=SearchResponse)
def search(prefs: SearchPreferences, db: Session = Depends(get_db)):
    items = search_stays(db, prefs)
    return SearchResponse(items=items)

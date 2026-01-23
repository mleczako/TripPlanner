from models.event import Event
from datetime import date
from sqlalchemy.orm import Session

def has_blocking_event(
    db: Session,
    city_name: str,
    start_date: date,
    end_date: date
):
    return db.query(Event).filter(
        Event.city == city_name,
        Event.date_from <= end_date,
        Event.date_to >= start_date,
        Event.severity.in_(["HIGH", "CRITICAL"])
    ).order_by(Event.severity.desc()).first()
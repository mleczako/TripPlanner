from sqlalchemy.orm import Session
from typing import List

from app.models.entities import Transfer


def get_transfers(
    db: Session,
    locations: set[str],
) -> List[Transfer]:
    return (
        db.query(Transfer)
        .filter(
            Transfer.location.in_(locations),
            Transfer.available.is_(True),
        )
        .all()
    )

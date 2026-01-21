from sqlalchemy import Column, DateTime, Integer, String, Date
from database import Base
from datetime import datetime

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    type = Column(String)           # WEATHER, SECURITY, etc.
    severity = Column(String)       # LOW / MEDIUM / HIGH / CRITICAL
    city = Column(String, nullable=True)

    date_from = Column(Date)
    date_to = Column(Date)

    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

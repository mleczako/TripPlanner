from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Date,
    Boolean,
    ForeignKey,
    CheckConstraint,
    func,
)
from app.database import Base


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True)

    from_airport = Column(String(10), nullable=False)
    to_airport = Column(String(10), nullable=False)

    date = Column(Date, nullable=False)

    price = Column(Numeric(10, 2), nullable=False)

    status = Column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('SCHEDULED', 'DELAYED', 'CANCELLED')",
            name="flight_status_check",
        ),
    )


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True)

    name = Column(String(255), nullable=False)
    location = Column(String(100), nullable=False)
    standard = Column(Integer, nullable=False)

    price_per_night = Column(Numeric(10, 2), nullable=False)

    has_wifi = Column(Boolean, nullable=False, default=False)
    has_pool = Column(Boolean, nullable=False, default=False)
    has_parking = Column(Boolean, nullable=False, default=False)


class HotelAvailability(Base):
    __tablename__ = "hotel_availability"

    id = Column(Integer, primary_key=True)

    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)

    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)

    max_guests = Column(Integer, nullable=False)
    is_available = Column(Boolean, nullable=False)


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True)

    type = Column(String(20), nullable=False)
    location = Column(String(100), nullable=False)

    price = Column(Numeric(10, 2), nullable=False)
    available = Column(Boolean, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "type IN ('BUS', 'TAXI', 'TRAIN')",
            name="transfer_type_check",
        ),
    )



class NewsEvent(Base):
    __tablename__ = "news_events"

    id = Column(Integer, primary_key=True)

    type = Column(String(30), nullable=False)

    location = Column(String(100), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    severity = Column(String(10), nullable=False)

    processed = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH')",
            name="news_severity_check",
        ),
    )


class Stay(Base):
    __tablename__ = "stays"

    id = Column(Integer, primary_key=True)

    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False)

    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)

    total_price = Column(Numeric(10, 2), nullable=False)

    status = Column(String(20), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('PROPOSED', 'RESERVED', 'CANCELLED')",
            name="stay_status_check",
        ),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)

    stay_id = Column(Integer, ForeignKey("stays.id"), nullable=False)

    news_event_id = Column(Integer, nullable=True)

    message = Column(String, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    read = Column(Boolean, nullable=False, default=False)

from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    status = Column(String) # "special", "booked", "canceled", "prepared"
    hotel_id = Column(Integer, ForeignKey("hotels.id"))
    start_transfer_id = Column(Integer, ForeignKey("transfers.id"))
    end_transfer_id = Column(Integer, ForeignKey("transfers.id"))
    start_flight_id = Column(Integer, ForeignKey("flights.id"))
    end_flight_id = Column(Integer, ForeignKey("flights.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    guests = Column(Integer)
    start_city_id = Column(Integer, ForeignKey("cities.id"))
    visited_city_id = Column(Integer, ForeignKey("cities.id"))
    total_price = Column(Float)
    rating = Column(Float, default=0.0)
    discount = Column(Float, nullable=True)
    hotel = relationship("Hotel")
    start_flight = relationship("Flight", foreign_keys=[start_flight_id])
    end_flight = relationship("Flight", foreign_keys=[end_flight_id])
    start_transfer = relationship("Transfer", foreign_keys=[start_transfer_id])
    end_transfer = relationship("Transfer", foreign_keys=[end_transfer_id])
    start_city = relationship("City", foreign_keys=[start_city_id])
    visited_city = relationship("City", foreign_keys=[visited_city_id],lazy="joined")
    disruption_type = Column(String, nullable=True)
    disruption_severity = Column(String, nullable=True)
    disruption_message = Column(String, nullable=True)
    parent_booking_id = Column(Integer, nullable=True)

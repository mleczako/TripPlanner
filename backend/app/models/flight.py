from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    start_city_id = Column(Integer, ForeignKey("cities.id"))
    end_city_id = Column(Integer, ForeignKey("cities.id"))
    date = Column(Date)
    price = Column(Float)
    start_city = relationship("City", foreign_keys=[start_city_id])
    end_city = relationship("City", foreign_keys=[end_city_id])
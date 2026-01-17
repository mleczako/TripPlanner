from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Hotel(Base):
    __tablename__ = "hotels"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    capacity = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    rating = Column(Float)
    price = Column(Float)
    city_id = Column(Integer, ForeignKey("cities.id"))
    city = relationship("City")
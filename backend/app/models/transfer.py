from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Transfer(Base):
    __tablename__ = "transfers"
    id = Column(Integer, primary_key=True)
    type = Column(String) 
    name = Column(String)
    date = Column(Date)
    rating = Column(Float)
    price = Column(Float)
    city_id = Column(Integer, ForeignKey("cities.id"))
    city = relationship("City")
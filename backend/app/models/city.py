from sqlalchemy import Column, Integer, String
from database import Base

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    image_url = Column(String)
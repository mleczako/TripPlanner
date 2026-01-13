from pydantic import BaseModel


class BookingCreate(BaseModel):
    stay_id: int
    user_id: int


class BookingRead(BookingCreate):
    id: int

    class Config:
        orm_mode = True

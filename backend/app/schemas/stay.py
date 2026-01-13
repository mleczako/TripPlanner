from pydantic import BaseModel


class Stay(BaseModel):
    id: int
    name: str
    location: str

    class Config:
        orm_mode = True

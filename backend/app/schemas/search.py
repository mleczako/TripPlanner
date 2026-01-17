from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class SearchPreferences(BaseModel):
    date_from: date
    date_to: date
    budget: float = Field(gt=0)
    guests: int = Field(ge=1)

    from_location: str = Field(min_length=2)
    to_location: Optional[str] = None

    min_hotel_standard: Optional[int] = Field(default=None, ge=1, le=5)
    require_wifi: Optional[bool] = None
    require_pool: Optional[bool] = None
    require_parking: Optional[bool] = None

    limit: int = Field(default=10, ge=1, le=50)

class ProposedStay(BaseModel):
    outbound_flight_id: int
    return_flight_id: int
    hotel_id: int
    transfer_id: int

    date_from: date
    date_to: date

    total_price: float
    currency: str = "PLN"


class SearchResponse(BaseModel):
    items: List[ProposedStay]

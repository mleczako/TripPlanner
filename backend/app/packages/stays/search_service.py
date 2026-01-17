from __future__ import annotations
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.entities import (
    Flight,
    Hotel,
    HotelAvailability,
    Transfer,
)
from app.schemas.search import SearchPreferences, ProposedStay
from app.packages.stays.filter_service import apply_hotel_filters, nights_between


def search_stays(db: Session, prefs: SearchPreferences) -> List[ProposedStay]:
    outbound_flights = (
        db.query(Flight)
        .filter(
            Flight.from_airport == prefs.from_location,
            Flight.date == prefs.date_from,
            Flight.status == "SCHEDULED",
        )
        .all()
    )

    if prefs.to_location:
        outbound_flights = [
            f for f in outbound_flights if f.to_airport == prefs.to_location
        ]

    if not outbound_flights:
        return []

    destinations = {f.to_airport for f in outbound_flights}

    return_flights = (
        db.query(Flight)
        .filter(
            Flight.to_airport == prefs.from_location,
            Flight.date == prefs.date_to,
            Flight.status == "SCHEDULED",
        )
        .all()
    )

    if not return_flights:
        return []

    return_by_city: Dict[str, List[Flight]] = {}
    for rf in return_flights:
        return_by_city.setdefault(rf.from_airport, []).append(rf)

    transfers = (
        db.query(Transfer)
        .filter(
            Transfer.location.in_(destinations),
            Transfer.available.is_(True),
        )
        .all()
    )

    if not transfers:
        return []

    transfers_by_city: Dict[str, List[Transfer]] = {}
    for t in transfers:
        transfers_by_city.setdefault(t.location, []).append(t)

    hotels_q = db.query(Hotel).filter(Hotel.location.in_(destinations))
    hotels_q = apply_hotel_filters(
        hotels_q,
        prefs.min_hotel_standard,
        prefs.require_wifi,
        prefs.require_pool,
        prefs.require_parking,
    )
    hotels = hotels_q.all()

    if not hotels:
        return []

    hotels_by_city: Dict[str, List[Hotel]] = {}
    for h in hotels:
        hotels_by_city.setdefault(h.location, []).append(h)

    availabilities = (
        db.query(HotelAvailability)
        .filter(
            HotelAvailability.is_available.is_(True),
            HotelAvailability.max_guests >= prefs.guests,
            HotelAvailability.date_from <= prefs.date_from,
            HotelAvailability.date_to >= prefs.date_to,
        )
        .all()
    )

    if not availabilities:
        return []

    avail_by_hotel = {a.hotel_id for a in availabilities}

    nights = nights_between(prefs.date_from, prefs.date_to)
    results: List[ProposedStay] = []

    for out_flight in outbound_flights:
        city = out_flight.to_airport

        if city not in hotels_by_city:
            continue
        if city not in transfers_by_city:
            continue
        if city not in return_by_city:
            continue

        city_hotels = sorted(
            hotels_by_city[city],
            key=lambda h: float(h.price_per_night),
        )[:5]

        city_transfers = sorted(
            transfers_by_city[city],
            key=lambda t: float(t.price),
        )[:2]

        for return_flight in return_by_city[city]:
            for hotel in city_hotels:
                if hotel.id not in avail_by_hotel:
                    continue

                hotel_cost = float(hotel.price_per_night) * nights

                for transfer in city_transfers:
                    total_price = (
                        float(out_flight.price)
                        + float(return_flight.price)
                        + hotel_cost
                        + float(transfer.price)
                    )

                    if total_price > prefs.budget:
                        continue

                    results.append(
                        ProposedStay(
                            outbound_flight_id=out_flight.id,
                            return_flight_id=return_flight.id,
                            hotel_id=hotel.id,
                            transfer_id=transfer.id,
                            date_from=prefs.date_from,
                            date_to=prefs.date_to,
                            total_price=round(total_price, 2),
                        )
                    )

                    if len(results) >= prefs.limit:
                        return sorted(results, key=lambda r: r.total_price)

    return sorted(results, key=lambda r: r.total_price)

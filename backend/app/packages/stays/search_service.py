from __future__ import annotations
from typing import List, Dict

from sqlalchemy.orm import Session

from app.schemas.search import SearchPreferences, ProposedStay
from app.packages.stays.filter_service import nights_between

from app.external.flights_adapter import (
    get_outbound_flights,
    get_return_flights,
)
from app.external.hotels_adapter import get_hotels
from app.external.availability_adapter import get_available_hotels
from app.external.transfers_adapter import get_transfers


def search_stays(db: Session, prefs: SearchPreferences) -> List[ProposedStay]:
    # loty wylotowe
    outbound_flights = get_outbound_flights(
        db=db,
        from_airport=prefs.from_location,
        date_from=prefs.date_from,
        to_airport=prefs.to_location,
    )

    if not outbound_flights:
        return []

    destinations = {f.to_airport for f in outbound_flights}

    # loty powrotne
    return_flights = get_return_flights(
        db=db,
        to_airport=prefs.from_location,
        date_to=prefs.date_to,
    )

    if not return_flights:
        return []

    return_by_city: Dict[str, List] = {}
    for rf in return_flights:
        return_by_city.setdefault(rf.from_airport, []).append(rf)

    #transfery
    transfers = get_transfers(
        db=db,
        locations=destinations,
    )

    if not transfers:
        return []

    transfers_by_city: Dict[str, List] = {}
    for t in transfers:
        transfers_by_city.setdefault(t.location, []).append(t)

    #hotele i filtry
    hotels = get_hotels(
        db=db,
        locations=destinations,
        min_standard=prefs.min_hotel_standard,
        require_wifi=prefs.require_wifi,
        require_pool=prefs.require_pool,
        require_parking=prefs.require_parking,
    )

    if not hotels:
        return []

    hotels_by_city: Dict[str, List] = {}
    for h in hotels:
        hotels_by_city.setdefault(h.location, []).append(h)

    #dostepnosc hotelu
    available_hotel_ids = get_available_hotels(
        db=db,
        date_from=prefs.date_from,
        date_to=prefs.date_to,
        guests=prefs.guests,
    )

    if not available_hotel_ids:
        return []
    #skladanie kombinacji
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
                if hotel.id not in available_hotel_ids:
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

                   # if len(results) >= prefs.limit:
                     #   return sorted(results, key=lambda r: r.total_price)

    #brak miejsca docelowego - propozycje z roznymi miastami
    results = sorted(results, key=lambda r: r.total_price)

    if prefs.to_location is None:
        selected: List[ProposedStay] = []
        cities_used: Dict[str, int] = {}

        flight_city_map = {
            f.id: f.to_airport for f in outbound_flights
        }

        for r in results:
            city = flight_city_map.get(r.outbound_flight_id)
            if city is None:
                continue

            if city not in cities_used and len(cities_used) >= 5:
                continue

            cities_used.setdefault(city, 0)
            if cities_used[city] >= 2:
                continue

            selected.append(r)
            cities_used[city] += 1

            if len(selected) == 10:
                break

        return selected

    return results[:5]


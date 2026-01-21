import asyncio
import requests
from datetime import date
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Booking, City
from services.alternative_service import create_alternatives_for_disrupted_booking
from models.event import Event

MOCK_API_URL = "http://localhost:8001"
CHECK_INTERVAL_SECONDS = 15

_last_event_id = 0  


def _parse_iso(d: str) -> date:
    return date.fromisoformat(d)


def overlaps(b: Booking, e_from: date, e_to: date) -> bool:
    return b.start_date <= e_to and b.end_date >= e_from


def match_event_to_bookings(event: dict, bookings: list[Booking]) -> list[Booking]:
    etype = event["type"]
    e_from = _parse_iso(event["date_from"])
    e_to = _parse_iso(event["date_to"])

    affected = []

    for b in bookings:
        if b.status != "booked":
            continue

        if not overlaps(b, e_from, e_to):
            continue

        if etype in ["WEATHER", "SECURITY"]:
            if event.get("city") and b.visited_city and b.visited_city.name == event["city"]:
                affected.append(b)

        elif etype == "HOTEL":
            if event.get("hotel_id") is not None and b.hotel_id == event["hotel_id"]:
                affected.append(b)

        elif etype == "FLIGHT":
            if event.get("flight_id") is not None and event["flight_id"] in [b.start_flight_id, b.end_flight_id]:
                affected.append(b)

        elif etype == "TRANSFER":
            if event.get("transfer_id") is not None and event["transfer_id"] in [b.start_transfer_id, b.end_transfer_id]:
                affected.append(b)

    return affected


def mark_disrupted(db: Session, b: Booking, event: dict):
    b.status = "disrupted"
    b.disruption_type = event["type"]
    b.disruption_severity = event["severity"]
    b.disruption_message = event["message"]
    db.add(b)


async def watchdog_loop():
    global _last_event_id
    print("[WATCHDOG] Started (event-driven)")

    while True:
        db: Session = SessionLocal()
        try:
            bookings = db.query(Booking).filter(Booking.status == "booked").all()

            resp = requests.get(f"{MOCK_API_URL}/external/events", params={"since": _last_event_id}, timeout=2)
            if resp.status_code != 200:
                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
                continue

            events = resp.json()
            if events:
                _last_event_id = max(_last_event_id, max(e["id"] for e in events))
            for e in events:
                if e["type"] in ["WEATHER", "SECURITY"]:
                    event_row = Event(
                        type=e["type"],
                        severity=e["severity"],
                        city=e.get("city"),
                        date_from=_parse_iso(e["date_from"]),
                        date_to=_parse_iso(e["date_to"]),
                        message=e["message"]
                    )
                    db.add(event_row)
                    db.commit() 
                affected = match_event_to_bookings(e, bookings)

                for b in affected:
                    mark_disrupted(db, b, e)
                    db.commit()

                    create_alternatives_for_disrupted_booking(db, b)

        except Exception as ex:
            print(f"[WATCHDOG] ERROR: {ex}")
        finally:
            db.close()

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

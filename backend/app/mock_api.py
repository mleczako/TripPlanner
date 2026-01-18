from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
import random

app = FastAPI(title="External Providers Mock API")

class PaymentRequest(BaseModel):
    amount: float
    currency: str
    method: str  
    token: str   

@app.post("/external/payment")
def process_payment(payment: PaymentRequest):
    print(f"[BANK API] Przetwarzanie płatności: {payment.amount} {payment.currency} metodą {payment.method}")
    
    if payment.method == 'blik':
        if len(payment.token) != 6 or not payment.token.isdigit():
             print("[BANK API] Błąd: Nieprawidłowy kod BLIK")
             raise HTTPException(status_code=402, detail="Nieprawidłowy kod BLIK (musi mieć 6 cyfr)")
    
    if payment.method == 'card':
        if len(payment.token) < 16:
             print("[BANK API] Błąd: Numer karty za krótki")
             raise HTTPException(status_code=402, detail="Odrzucono: Brak środków lub błędny numer karty")

    if random.randint(1, 10) == 1:
        print("[BANK API] Awaria systemu bankowego")
        raise HTTPException(status_code=503, detail="Błąd bramki płatniczej. Spróbuj później.")

    print(f"[BANK API] Płatność zaakceptowana! Transakcja ID: TRX-{random.randint(10000,99999)}")
    return {"status": "success", "transaction_id": f"TRX-{random.randint(100000,999999)}"}


@app.get("/external/hotels")
def get_external_hotels(city: str, date_from: date, date_to: date, guests: int):
    print(f"[EXTERNAL API] Szukanie hoteli w: {city} dla {guests} osób")
    hotels = []
    types = ['Grand', 'Resort', 'Standard', 'Hostel']
    for i, type_name in enumerate(types):
        capacity = guests + random.choice([0, 1, 2]) 
        hotels.append({
            "external_id": f"ext_hotel_{city}_{i}",
            "name": f"Hotel {city} {type_name}",
            "address": f"ul. Turystyczna {random.randint(1, 100)}, {city}",
            "capacity": capacity,
            "rating": round(random.uniform(7.0, 9.9), 1),
            "price_per_night": random.randint(200, 800) * guests
        })
    return hotels

@app.get("/external/flights")
def get_external_flights(origin: str, destination: str, date: date):
    print(f"[EXTERNAL API] Szukanie lotu {origin} -> {destination} na {date}")
    flights = []
    flight_hours = ["08:00", "18:00"]
    for i, hour in enumerate(flight_hours):
        flights.append({
            "external_id": f"ext_flight_{origin}_{destination}_{date}_{i}",
            "flight_number": f"FL-{origin[:3].upper()}{destination[:3].upper()}-{random.randint(100,999)}",
            "airline": f"Air {destination} Express",
            "departure_time": hour,
            "price": random.randint(300, 1200)
        })
    return flights

@app.get("/external/transfers")
def get_external_transfers(city: str):
    print(f"[EXTERNAL API] Szukanie transferów w: {city}")
    return [
        {
            "external_id": f"ext_trans_{city}_taxi",
            "type": "Taxi",
            "name": f"Taxi {city} Express",
            "rating": 9.0,
            "price": 50.0
        },
        {
            "external_id": f"ext_trans_{city}_bus",
            "type": "Bus",
            "name": f"Bus {city} Public",
            "rating": 7.5,
            "price": 15.0
        }
    ]


class BookingConfirmation(BaseModel):
    booking_reference: str 
    items: list[str]     

@app.post("/external/finalize")
def finalize_booking(confirmation: BookingConfirmation):
    print(f"[EXTERNAL API] 🛒 Otrzymano potwierdzenie rezerwacji nr {confirmation.booking_reference}")
    print(f"[EXTERNAL API]    Zablokowano zasoby: {confirmation.items}")
    return {"status": "confirmed", "provider_id": f"EXT-{random.randint(1000,9999)}"}
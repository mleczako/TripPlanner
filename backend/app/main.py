from fastapi import FastAPI
from database import engine, Base
from routers import api, payments, bookings, stays

from services.watchdog_service import watchdog_loop
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(watchdog_loop())
    yield
  
app = FastAPI(lifespan=lifespan)
Base.metadata.create_all(bind=engine)

app.include_router(api.router)
app.include_router(payments.router)
app.include_router(bookings.router)
app.include_router(stays.router)
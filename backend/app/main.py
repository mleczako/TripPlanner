from fastapi import FastAPI
from app.api.search import router as search_router


app = FastAPI()
app.include_router(search_router)

@app.get("/")
def read_root():
    return {"message": "TripPlanner backend running"}

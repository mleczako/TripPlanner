# TripPlanner

Instruction how to run this code:

```
cd backend

# environment
python -m venv venv

# activation (Windows)
venv\Scripts\activate

# activation (Mac/Linux)
source venv/bin/activate

# install libraries
pip install -r requirements.txt

cd app
python seed.py
python seed_data.py

uvicorn main:app --reload
```

Second terminal:

```
cd backend

# environment
python -m venv venv

# activation (Windows)
venv\Scripts\activate

# activation (Mac/Linux)
source venv/bin/activate

# install libraries
pip install -r requirements.txt

cd app

uvicorn mock_api:app --port 8001 --reload

# unit testing

cd backend/app
python -m pytest .\test\test_stay_service.py

# functional testing

cd backend/app
python -m pytest .\test\test_special_offers.py
```

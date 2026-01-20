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

uvicorn main:app --port 8000 --reload
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
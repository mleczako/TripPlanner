import pytest
from datetime import date, timedelta
from services.validators import validate_search_input

def test_validate_search_input_missing_dates():
    error = validate_search_input(None, None, 2, 5000.0, "Warszawa")
    assert error == "Data początkowa i końcowa są wymagane"

def test_validate_search_input_past_date():
    past_date = date.today() - timedelta(days=1)
    error = validate_search_input(past_date, date.today() + timedelta(days=5), 2, 5000.0, "Warszawa")
    assert "muszą być w przyszłości" in error

def test_validate_search_input_invalid_budget():
    error = validate_search_input(date.today() + timedelta(days=1), date.today() + timedelta(days=5), 2, 0, "Warszawa")
    assert "Budżet musi być większy od zera" in error
import pytest
import math
from services.alternative_service import min_rating_floor
from types import SimpleNamespace

def test_min_rating_logic_for_alternatives():
    mock_booking = SimpleNamespace(rating=8.5)
    
    result = min_rating_floor(mock_booking)
    assert result == 8.0

    
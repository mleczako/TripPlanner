from datetime import date

def validate_search_input(
    start_date: date | None,
    end_date: date | None,
    guests: int | None,
    budget: float | None,
    start_city: str | None
) -> str | None:
    if not start_date or not end_date:
        return "Data początkowa i końcowa są wymagane"
    if start_date< date.today():
        return "Daty podróży muszą być w przyszłości"
    if start_date >= end_date:
        return "Data końcowa musi być po dacie początkowej"

    if not guests or guests <= 0:
        return "Liczba gości musi być większa od zera"

    if not budget or budget <= 0:
        return "Budżet musi być większy od zera"

    if not start_city or start_city.strip() == "":
        return "Miejsce rozpoczęcia podróży jest wymagane"

    return None
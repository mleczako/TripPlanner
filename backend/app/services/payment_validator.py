def validate_payment_details(method: str, token: str) -> str | None:
    if not method or not token:
        return "Musisz wybrać metodę płatności i wpisać kod/numer karty."
    
    if method == "blik":
        if len(token) != 6 or not token.isdigit():
             return "Nieprawidłowy kod BLIK (wymagane 6 cyfr)."
             
    if method == "card":
        clean_token = token.replace(" ", "")
        if len(clean_token) < 16:
             return "Numer karty jest za krótki."

    return None
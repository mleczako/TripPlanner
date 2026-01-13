class PaymentService:
    def charge(self, amount_cents: int, payment_method: dict) -> dict:
        return {"status": "ok", "amount": amount_cents}

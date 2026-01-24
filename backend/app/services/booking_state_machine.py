def get_next_booking_status(current_status: str, action: str) -> str:

    if current_status == "prepared" and action == "start_payment":
        return "pending"
    
    if current_status == "pending" and action == "payment_success":
        return "booked"

    if current_status == "pending" and action == "payment_failed":
        return "prepared"
        
    if action == "cancel":
        return "canceled"

    return current_status
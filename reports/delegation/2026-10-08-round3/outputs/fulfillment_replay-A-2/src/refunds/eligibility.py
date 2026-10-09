from src.checkout.states import REFUNDABLE

def allowed(order):
    return order is not None and order['status'] in REFUNDABLE

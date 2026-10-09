from .requirements import required_holds

def readiness(order, holds):
    if order['status'] not in ('paid', 'shipped'):
        return False
    return all(holds.get(key, 0) >= qty for key, qty in required_holds(order).items())

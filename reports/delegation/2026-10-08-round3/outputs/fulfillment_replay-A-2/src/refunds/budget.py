def reserve(order, spent, amount):
    if spent + amount > order['captured_minor']:
        return False
    return True

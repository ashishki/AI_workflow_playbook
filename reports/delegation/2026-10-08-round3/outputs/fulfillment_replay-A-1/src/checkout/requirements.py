def required_holds(order):
    result = {}
    for line in order['lines']:
        key = order['tenant'], line['warehouse'], order['order_id'], line['sku']
        result[key] = result.get(key, 0) + line['qty']
    return result

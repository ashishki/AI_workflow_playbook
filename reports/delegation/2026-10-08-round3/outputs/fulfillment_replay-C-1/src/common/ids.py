def identifier(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('nonblank string identifier required')
    return value.strip()

def order_key(row):
    return identifier(row['tenant']), identifier(row['order_id'])

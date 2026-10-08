from src.common.ids import order_key
from src.common.errors import conflict

def select(rows):
    chosen, identities = {}, {}
    for row in rows:
        key = order_key(row)
        identity = key + (row['revision'],)
        payload = (row['status'], row['captured_minor'], row['lines'])
        if identity in identities and identities[identity] != payload:
            conflict('checkout', identity)
        identities[identity] = payload
        old = chosen.get(key)
        if old is None or row['revision'] > old['revision']:
            chosen[key] = row
    return chosen

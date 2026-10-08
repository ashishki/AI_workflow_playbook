from src.common.ids import identifier
from src.common.numbers import whole

def stock_key(row):
    return tuple(identifier(row[k]) for k in ('tenant', 'warehouse', 'sku'))

def load(rows):
    result = {}
    for row in rows:
        key = stock_key(row)
        if key in result:
            raise ValueError('duplicate opening stock bucket')
        result[key] = whole(row['qty'])
    return result

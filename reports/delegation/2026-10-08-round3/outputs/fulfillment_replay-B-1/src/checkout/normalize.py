from src.common.ids import identifier
from src.common.numbers import whole
from src.common.time import instant
from src.common.records import event_id
from .states import STATES

def snapshot(row):
    result = dict(row)
    for key in ('tenant', 'order_id'):
        result[key] = identifier(row[key])
    result['event_id'] = event_id(row)
    result['revision'] = whole(row['revision'], 1)
    result['captured_minor'] = whole(row['captured_minor'])
    result['delivered_at'] = instant(row['delivered_at'])
    if row['status'] not in STATES:
        raise ValueError('unsupported order status')
    result['lines'] = [dict(warehouse=identifier(line['warehouse']),
                          sku=identifier(line['sku']), qty=whole(line['qty'], 1))
                       for line in row['lines']]
    return result

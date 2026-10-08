from src.common.ids import identifier
from src.common.numbers import whole
from src.common.records import event_id

def refund(row):
    result = {k: identifier(row[k]) for k in
              ('tenant', 'order_id', 'refund_id', 'attempt_id', 'provider')}
    result['event_id'] = event_id(row)
    result['amount_minor'] = whole(row['amount_minor'], 1)
    if row['status'] != 'succeeded':
        raise ValueError('only settled refund deliveries belong in this replay')
    return result

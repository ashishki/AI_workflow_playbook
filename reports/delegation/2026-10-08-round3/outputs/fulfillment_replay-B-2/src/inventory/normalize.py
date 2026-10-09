from src.common.ids import identifier
from src.common.numbers import whole
from src.common.records import event_id

def operation(row):
    out = {key: identifier(row[key]) for key in
           ('tenant', 'warehouse', 'operation_id', 'order_id', 'sku')}
    out.update(event_id=event_id(row), action=row['action'], qty=whole(row['qty'], 1))
    if out['action'] not in ('reserve', 'release'):
        raise ValueError('unknown warehouse action')
    return out

from .buckets import stock_key
from .holds import hold_key, reserved_for_stock

def apply(row, opening, holds):
    bucket, hold = stock_key(row), hold_key(row)
    if bucket not in opening:
        raise ValueError('unknown stock bucket')
    previous = holds.get(hold, 0)
    if row['action'] == 'reserve':
        available = opening[bucket] - reserved_for_stock(holds, bucket)
        if available < row['qty']:
            raise ValueError('insufficient stock')
        holds[hold] = previous + row['qty']
    else:
        if previous < row['qty']:
            raise ValueError('release exceeds own hold')
        holds[hold] = previous - row['qty']

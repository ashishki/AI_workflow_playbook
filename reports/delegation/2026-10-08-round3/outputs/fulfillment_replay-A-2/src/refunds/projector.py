from src.common.ids import order_key
from .normalize import refund
from .ledger import Ledger
from .eligibility import allowed
from .budget import reserve
from .summary import view

def project(deliveries, orders):
    by_order = {order_key(row): row for row in orders}
    ledger, totals, accepted, rejected = Ledger(), {}, [], []
    replayed = 0
    for delivery in deliveries:
        row = refund(delivery)
        if not ledger.accept(row):
            replayed += 1
            continue
        key = order_key(row)
        order, spent = by_order.get(key), totals.get(key, 0)
        reason = None
        if not allowed(order):
            reason = 'order_not_refundable'
        elif not reserve(order, spent, row['amount_minor']):
            reason = 'exceeds_capture'
        if reason:
            rejected.append(dict(event_id=row['event_id'], reason=reason))
        else:
            totals[key] = spent + row['amount_minor']
            accepted.append(dict(tenant=row['tenant'], provider=row['provider'],
                refund_id=row['refund_id'], order_id=row['order_id'], amount_minor=row['amount_minor']))
    return view(totals, accepted, rejected, replayed)

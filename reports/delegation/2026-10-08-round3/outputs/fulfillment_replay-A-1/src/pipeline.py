from src.common.records import require_build
from src.adapters import decode
from src.inventory.projector import project as stock
from src.checkout.projector import project as checkout
from src.refunds.projector import project as refunds
from src.reporting.join import join
from src.reporting.metrics import summarize

def replay(document):
    document = decode(document)
    require_build(document)
    inventory = stock(document['opening_stock'], document['inventory_events'])
    orders = checkout(document['checkout_events'], inventory)
    refund_view = refunds(document['refund_events'], orders)
    return {'inventory': inventory, 'orders': join(orders, refund_view),
            'refunds': refund_view, 'metrics': summarize(inventory, orders, refund_view)}

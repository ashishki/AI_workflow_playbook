def summarize(inventory, orders, refunds):
    return {'ready_orders': sum(row['ready'] for row in orders),
            'reserved_units': sum(row['reserved'] for row in inventory['stock']),
            'refunded_minor': sum(row['refunded_minor'] for row in refunds['totals']),
            'rejected_refunds': len(refunds['rejected'])}

from .fulfillment import readiness

def view(rows, inventory):
    holds = {(r['tenant'], r['warehouse'], r['order_id'], r['sku']): r['qty']
             for r in inventory['holds']}
    return [dict(tenant=t, order_id=o, revision=r['revision'], status=r['status'],
                 captured_minor=r['captured_minor'], ready=readiness(r, holds))
            for (t, o), r in sorted(rows.items())]

def view(totals, accepted, rejected, replayed):
    return {'totals': [dict(tenant=t, order_id=o, refunded_minor=q)
                       for (t,o), q in sorted(totals.items())],
            'accepted': sorted(accepted, key=lambda r:
                              (r['tenant'], r['provider'], r['refund_id'])),
            'rejected': rejected, 'replayed': replayed}

from .holds import reserved_for_stock

def view(opening, holds, accepted, replayed):
    return {'stock': [dict(tenant=t, warehouse=w, sku=s, on_hand=qty,
                reserved=reserved_for_stock(holds, (t, w, s)),
                available=qty-reserved_for_stock(holds, (t, w, s)))
            for (t, w, s), qty in sorted(opening.items())],
            'holds': [dict(tenant=t, warehouse=w, order_id=o, sku=s, qty=q)
                      for (t,w,o,s), q in sorted(holds.items()) if q],
            'accepted': accepted, 'replayed': replayed}

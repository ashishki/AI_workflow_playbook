def hold_key(row):
    return row['tenant'], row['warehouse'], row['order_id'], row['sku']

def reserved_for_stock(holds, stock):
    tenant, warehouse, sku = stock
    return sum(qty for (t, w, _order, s), qty in holds.items()
               if (t, w, s) == (tenant, warehouse, sku))

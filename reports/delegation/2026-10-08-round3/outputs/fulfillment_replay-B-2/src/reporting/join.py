from src.common.ids import order_key

def join(orders, refunds):
    amounts = {order_key(row): row['refunded_minor'] for row in refunds['totals']}
    return [dict(row, refunded_minor=amounts.get(order_key(row), 0),
                 net_minor=row['captured_minor']-amounts.get(order_key(row), 0))
            for row in orders]

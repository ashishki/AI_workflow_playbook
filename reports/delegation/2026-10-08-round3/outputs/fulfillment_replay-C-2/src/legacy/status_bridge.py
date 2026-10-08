def from_poll(row):
    # r29 polling feed had no source revision.
    return {'order_id': row['order_id'], 'status': row['remote_status'],
            'observed_at': row['polled_at']}

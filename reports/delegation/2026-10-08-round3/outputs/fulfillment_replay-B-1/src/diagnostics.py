"""Offline source-record index for incident triage, never cause inference."""
from src.adapters import decode

def record_index(document):
    streams = decode(document)
    index = {}
    for channel in ('inventory_events','checkout_events','refund_events'):
        for position, row in enumerate(streams[channel]):
            entry = {'channel':channel, 'position':position,
                     'tenant':row['tenant'].strip(), 'order_id':row['order_id'].strip()}
            index.setdefault(row['event_id'].strip(), []).append(entry)
    return index

def order_sources(document, tenant, order_id):
    result = []
    for event_id, positions in record_index(document).items():
        for position in positions:
            if (position['tenant'], position['order_id']) == (tenant, order_id):
                result.append(dict(position, event_id=event_id))
    return sorted(result, key=lambda row:(row['channel'],row['position'],row['event_id']))

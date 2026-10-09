"""Validate transport containers before domain-specific normalization."""
from src.common.ids import identifier
from src.common.numbers import whole
from src.common.time import instant

CHANNELS = ('inventory_events', 'checkout_events', 'refund_events')
REQUIRED = {
    'inventory_events': {'event_id','tenant','warehouse','operation_id',
                         'order_id','sku','action','qty'},
    'checkout_events': {'event_id','tenant','order_id','revision','status',
                        'captured_minor','lines','delivered_at'},
    'refund_events': {'event_id','tenant','order_id','refund_id','attempt_id',
                      'provider','amount_minor','status'},
}

def mapping(value, label):
    if not isinstance(value, dict):
        raise ValueError(label + ' must be an object')
    return value

def array(value, label):
    if not isinstance(value, list):
        raise ValueError(label + ' must be an array')
    return value

def exact_keys(value, allowed, required, label):
    mapping(value, label)
    if set(value) - allowed or required - set(value):
        raise ValueError(label + ' unsupported or missing fields')
    return value

def event(row, channel):
    mapping(row, channel + ' event')
    if channel not in REQUIRED or REQUIRED[channel] - set(row):
        raise ValueError('event fields do not satisfy channel schema')
    for key in ('event_id','tenant','order_id'):
        identifier(row[key])
    if channel == 'inventory_events':
        for key in ('warehouse','operation_id','sku'):
            identifier(row[key])
        whole(row['qty'], 1)
    elif channel == 'checkout_events':
        whole(row['revision'], 1)
        whole(row['captured_minor'])
        instant(row['delivered_at'])
        for line in array(row['lines'], 'order lines'):
            mapping(line, 'order line')
            identifier(line['warehouse'])
            identifier(line['sku'])
            whole(line['qty'], 1)
    else:
        for key in ('refund_id','attempt_id','provider'):
            identifier(row[key])
        whole(row['amount_minor'], 1)
    return row

def opening(rows):
    for row in array(rows, 'opening stock'):
        mapping(row, 'opening stock row')
        for key in ('tenant','warehouse','sku'):
            identifier(row[key])
        whole(row['qty'])
    return rows

def canonical(document):
    exact_keys(document, {'build','opening_stock',*CHANNELS},
               {'build','opening_stock',*CHANNELS}, 'canonical replay')
    if document['build'] != 'r31':
        raise ValueError('unsupported replay build')
    opening(document['opening_stock'])
    for channel in CHANNELS:
        for row in array(document[channel], channel):
            event(row, channel)
    return document

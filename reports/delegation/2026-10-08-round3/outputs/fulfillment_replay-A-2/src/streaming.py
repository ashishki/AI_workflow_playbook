"""Deterministic batch delivery reconstruction, independent of wall clock."""
import json
from src.common.ids import identifier
from src.common.numbers import whole
from src.common.time import instant
from src.common.errors import conflict
from src.validation import CHANNELS, array, exact_keys, event

def payload(batch):
    # delivered_at and batch_id describe transport, not logical payload.
    return json.dumps({'channel':batch['channel'], 'ordinal':batch['ordinal'],
                       'records':batch['records']}, sort_keys=True,
                      separators=(',', ':'))

def reconstruct(batches):
    unique, channel_ordinals = {}, {}
    for raw in array(batches, 'batches'):
        exact_keys(raw, {'batch_id','channel','ordinal','delivered_at','records'},
                   {'batch_id','channel','ordinal','delivered_at','records'}, 'batch')
        batch_id = identifier(raw['batch_id'])
        channel = raw['channel']
        if channel not in CHANNELS:
            raise ValueError('unknown batch channel')
        ordinal = whole(raw['ordinal'])
        instant(raw['delivered_at'])
        for row in array(raw['records'], 'batch records'):
            event(row, channel)
        signature = payload(raw)
        if batch_id in unique:
            if unique[batch_id][1] != signature:
                conflict('transport batch', batch_id)
            continue
        slot = channel, ordinal
        if slot in channel_ordinals:
            raise ValueError('multiple batch IDs claim one channel ordinal')
        unique[batch_id] = raw, signature
        channel_ordinals[slot] = batch_id
    result = {channel:[] for channel in CHANNELS}
    for channel in CHANNELS:
        ordinals = sorted(ordinal for (name, ordinal) in channel_ordinals if name == channel)
        if ordinals != list(range(len(ordinals))):
            raise ValueError('batch channel has an ordinal gap')
        for ordinal in ordinals:
            batch_id = channel_ordinals[channel, ordinal]
            result[channel].extend(unique[batch_id][0]['records'])
    return result

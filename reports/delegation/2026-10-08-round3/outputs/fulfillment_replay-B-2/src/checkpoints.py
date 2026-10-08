"""Content-digested event checkpoints, not derived/projection snapshots."""
import copy
import hashlib
import json
from src.common.ids import identifier
from src.validation import CHANNELS, canonical, exact_keys

def digest(document):
    body = json.dumps(document, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(body).hexdigest()

def seal(document, checkpoint_id):
    canonical(document)
    identifier(checkpoint_id)
    events = copy.deepcopy(document)
    return {'checkpoint_id':checkpoint_id, 'events':events, 'sha256':digest(events)}

def restore(checkpoint):
    exact_keys(checkpoint, {'checkpoint_id','events','sha256'},
               {'checkpoint_id','events','sha256'}, 'checkpoint')
    identifier(checkpoint['checkpoint_id'])
    events = canonical(checkpoint['events'])
    checksum = checkpoint['sha256']
    if not isinstance(checksum, str) or checksum != digest(events):
        raise ValueError('checkpoint content digest mismatch')
    # Application replay is pure; none of its callers may alias this seed.
    return copy.deepcopy(events)

def append(checkpoint, suffix):
    result = restore(checkpoint)
    for channel in CHANNELS:
        result[channel].extend(copy.deepcopy(suffix[channel]))
    return canonical(result)

def empty(opening_stock):
    result = {'build':'r31','opening_stock':copy.deepcopy(opening_stock)}
    result.update({channel:[] for channel in CHANNELS})
    return canonical(result)

"""Decode the supported current transport formats into event streams."""
import copy
from src.validation import CHANNELS, canonical, exact_keys, mapping, opening
from src.streaming import reconstruct
from src.checkpoints import append, empty

def decode(document):
    mapping(document, 'input document')
    # A canonical document is supported for small offline reproductions.
    # Batch adapters are transport-only and never select domain revisions.
    if 'format' not in document:
        return copy.deepcopy(canonical(document))
    if document.get('build') != 'r31':
        raise ValueError('unsupported replay build')
    format_name = document['format']
    if format_name == 'batches-v1':
        exact_keys(document, {'build','format','opening_stock','batches'},
                   {'build','format','opening_stock','batches'}, 'batch replay')
        opening(document['opening_stock'])
        result = empty(document['opening_stock'])
        result.update(copy.deepcopy(reconstruct(document['batches'])))
        return canonical(result)
    if format_name == 'checkpoint-v1':
        exact_keys(document, {'build','format','checkpoint','batches'},
                   {'build','format','checkpoint','batches'}, 'checkpoint replay')
        suffix = reconstruct(document['batches'])
        return append(document['checkpoint'], suffix)
    raise ValueError('unsupported transport format')

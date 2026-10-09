from .ids import identifier

def require_build(document, build='r31'):
    if document.get('build') != build:
        raise ValueError('unsupported replay build')
    return document

def event_id(row):
    return identifier(row['event_id'])

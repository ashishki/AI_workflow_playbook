from .normalize import operation
from .registry import Registry
from .buckets import load
from .apply import apply
from .export import view

def project(opening_rows, deliveries):
    opening, holds, registry = load(opening_rows), {}, Registry()
    accepted = replayed = 0
    for delivery in deliveries:
        row = operation(delivery)
        if registry.accept(row):
            apply(row, opening, holds)
            accepted += 1
        else:
            replayed += 1
    return view(opening, holds, accepted, replayed)

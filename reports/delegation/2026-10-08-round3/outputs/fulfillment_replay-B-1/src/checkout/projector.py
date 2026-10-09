from .normalize import snapshot
from .revisions import select
from .export import view

def project(deliveries, inventory):
    return view(select(snapshot(row) for row in deliveries), inventory)

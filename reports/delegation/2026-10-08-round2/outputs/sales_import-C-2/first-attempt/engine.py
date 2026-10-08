"""Atomic, exact-cent sales imports backed by a local SQLite database."""

from contextlib import closing
import sqlite3

from money_exact import to_minor_units


_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY NOT NULL,
    customer_id TEXT NOT NULL,
    amount_minor TEXT NOT NULL,
    region TEXT NOT NULL,
    existing_route TEXT NOT NULL,
    route TEXT NOT NULL
)
"""


def _canonical_event(event):
    if not isinstance(event, dict):
        raise ValueError('each event must be a dict')
    for key in ('event_id', 'customer_id', 'amount', 'region'):
        if key not in event or not isinstance(event[key], str):
            raise ValueError(f'{key} must be a string')

    event_id = event['event_id'].strip()
    customer_id = event['customer_id'].strip()
    if not event_id or not customer_id:
        raise ValueError('IDs must not be empty')
    amount_minor = to_minor_units(event['amount'])
    region = event['region'].strip().upper()
    existing_route = event.get('existing_route')
    if existing_route is None:
        existing_route = ''
    elif not isinstance(existing_route, str):
        raise ValueError('existing_route must be a string or None')
    else:
        existing_route = existing_route.strip()

    if existing_route:
        route = existing_route
    elif not region:
        route = 'manual_review'
    elif amount_minor >= 1_000_000:
        route = 'senior'
    else:
        route = 'standard'

    # Bind cents as text: SQLite integers cannot hold every valid amount.
    payload = (customer_id, str(amount_minor), region, existing_route)
    return event_id, payload, route


def ingest(db_path, events):
    """Import one batch, rolling back every new row on any batch error."""
    try:
        batch = iter(events)
    except TypeError as exc:
        raise ValueError('events must be an iterable of dicts') from exc

    created = replayed = 0
    with closing(sqlite3.connect(db_path, timeout=10.0)) as db:
        with db:
            # Acquire the write lock before schema creation and replay checks.
            db.execute('BEGIN IMMEDIATE')
            db.execute(_SCHEMA)
            for event in batch:
                event_id, payload, route = _canonical_event(event)
                previous = db.execute(
                    'SELECT customer_id, amount_minor, region, existing_route '
                    'FROM events WHERE event_id = ?', (event_id,)
                ).fetchone()
                if previous is not None:
                    if previous != payload:
                        raise ValueError(f'conflicting payload for event {event_id!r}')
                    replayed += 1
                else:
                    db.execute(
                        'INSERT INTO events '
                        '(event_id, customer_id, amount_minor, region, existing_route, route) '
                        'VALUES (?, ?, ?, ?, ?, ?)',
                        (event_id, *payload, route)
                    )
                    created += 1
    return {'created': created, 'replayed': replayed}


def export(db_path):
    """Return canonical rows in ID order and their exact Python integer sum."""
    with closing(sqlite3.connect(db_path, timeout=10.0)) as db:
        with db:
            db.execute(_SCHEMA)
            stored = db.execute(
                'SELECT event_id, customer_id, amount_minor, region, existing_route, route '
                'FROM events ORDER BY event_id COLLATE BINARY'
            ).fetchall()

    rows = []
    total_minor = 0
    for event_id, customer_id, amount, region, existing_route, route in stored:
        amount_minor = int(amount)
        rows.append({
            'event_id': event_id,
            'customer_id': customer_id,
            'amount_minor': amount_minor,
            'region': region,
            'existing_route': existing_route,
            'route': route,
        })
        total_minor += amount_minor
    return {'events': rows, 'total_minor': total_minor}

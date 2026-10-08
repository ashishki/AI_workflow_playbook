"""Atomic, exact-cent sales imports backed by a local SQLite database."""

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


def _canonical(event):
    if not isinstance(event, dict):
        raise ValueError('each event must be a dict')
    normalized = {}
    for field in ('event_id', 'customer_id', 'region'):
        value = event.get(field)
        if not isinstance(value, str):
            raise ValueError(f'{field} must be a string')
        value = value.strip()
        if field != 'region' and not value:
            raise ValueError(f'{field} must not be empty')
        normalized[field] = value

    region = normalized['region'].upper()
    existing_route = event.get('existing_route')
    if existing_route is None:
        existing_route = ''
    elif not isinstance(existing_route, str):
        raise ValueError('existing_route must be a string or None')
    else:
        existing_route = existing_route.strip()

    amount_minor = to_minor_units(event.get('amount'))
    payload = (normalized['customer_id'], str(amount_minor), region, existing_route)
    if existing_route:
        route = existing_route
    elif not region:
        route = 'manual_review'
    elif amount_minor >= 1000000:
        route = 'senior'
    else:
        route = 'standard'
    return normalized['event_id'], payload, route


def ingest(db_path, events):
    """Import one batch; invalid events or conflicting IDs undo the whole batch."""
    try:
        batch = iter(events)
    except TypeError as exc:
        raise ValueError('events must be iterable') from exc

    db = sqlite3.connect(db_path, timeout=10, isolation_level=None)
    try:
        # Acquire the writer lock before either schema creation or replay lookup.
        db.execute('BEGIN IMMEDIATE')
        db.execute(_SCHEMA)
        created = replayed = 0
        for event in batch:
            event_id, payload, route = _canonical(event)
            previous = db.execute(
                'SELECT customer_id, amount_minor, region, existing_route '
                'FROM events WHERE event_id = ?', (event_id,)
            ).fetchone()
            if previous is not None:
                if previous != payload:
                    raise ValueError(f'conflicting payload for event_id {event_id!r}')
                replayed += 1
            else:
                db.execute(
                    'INSERT INTO events '
                    '(event_id, customer_id, amount_minor, region, existing_route, route) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (event_id, *payload, route)
                )
                created += 1
        db.commit()
        return {'created': created, 'replayed': replayed}
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def export(db_path):
    """Return canonical rows in ID order and their exact Python integer total."""
    db = sqlite3.connect(db_path, timeout=10, isolation_level=None)
    try:
        db.execute(_SCHEMA)
        stored = db.execute(
            'SELECT event_id, customer_id, amount_minor, region, existing_route, route '
            'FROM events ORDER BY event_id COLLATE BINARY'
        ).fetchall()
    finally:
        db.close()

    rows = [
        dict(event_id=event_id, customer_id=customer_id, amount_minor=int(amount_minor),
             region=region, existing_route=existing_route, route=route)
        for event_id, customer_id, amount_minor, region, existing_route, route in stored
    ]
    return {'events': rows, 'total_minor': sum(row['amount_minor'] for row in rows)}

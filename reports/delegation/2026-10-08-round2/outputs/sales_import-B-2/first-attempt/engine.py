"""Atomic, exact-cent sales imports into a local SQLite database."""

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
    for field in ('event_id', 'customer_id', 'amount', 'region'):
        if field not in event or not isinstance(event[field], str):
            raise ValueError(f'{field} must be a string')

    event_id = event['event_id'].strip()
    customer_id = event['customer_id'].strip()
    if not event_id or not customer_id:
        raise ValueError('IDs must not be empty')

    amount_minor = to_minor_units(event['amount'])
    region = event['region'].strip().upper()
    existing_route = event.get('existing_route')
    if existing_route is None:
        existing_route = ''
    elif isinstance(existing_route, str):
        existing_route = existing_route.strip()
    else:
        raise ValueError('existing_route must be a string or None')

    if existing_route:
        route = existing_route
    elif not region:
        route = 'manual_review'
    elif amount_minor >= 1000000:
        route = 'senior'
    else:
        route = 'standard'

    # Canonical integer text avoids SQLite's bounded INTEGER representation.
    payload = (customer_id, str(amount_minor), region, existing_route)
    return event_id, payload, route


def ingest(db_path, events):
    """Import one iterable of events; any failure rolls back the whole batch."""
    try:
        iterator = iter(events)
    except TypeError as exc:
        raise ValueError('events must be iterable') from exc

    db = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    try:
        # Take the writer lock before schema creation or replay checks.
        db.execute('BEGIN IMMEDIATE')
        db.execute(_SCHEMA)
        created = replayed = 0
        for event in iterator:
            event_id, payload, route = _canonical_event(event)
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
    """Return a consistent, sorted snapshot and an exact Python integer total."""
    db = sqlite3.connect(db_path, timeout=30, isolation_level=None)
    try:
        db.execute('BEGIN')
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'events'"
        ).fetchone()
        rows = []
        total_minor = 0
        if exists:
            for event_id, customer_id, amount, region, existing_route, route in db.execute(
                'SELECT event_id, customer_id, amount_minor, region, existing_route, route '
                'FROM events ORDER BY event_id COLLATE BINARY'
            ):
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
        db.commit()
        return {'events': rows, 'total_minor': total_minor}
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()

"""Atomic, exact-cent sales imports backed by a local SQLite database.

Regression: amounts beyond Python's decimal integer string conversion limit
must import, replay from an equivalent decimal string, and export exactly.
Decimal construction and formatting are exact even with low context precision.

>>> import tempfile
>>> from pathlib import Path
>>> from decimal import localcontext
>>> with tempfile.TemporaryDirectory() as directory, localcontext() as context:
...     context.prec = 6
...     db_path = Path(directory) / 'sales.db'
...     amount = '1' + '0' * 5000
...     event = dict(event_id='large', customer_id='customer', amount=amount, region='eu')
...     assert ingest(db_path, [event]) == {'created': 1, 'replayed': 0}
...     event['amount'] = amount + '.00'
...     assert ingest(db_path, [event, event]) == {'created': 0, 'replayed': 2}
...     result = export(db_path)
...     assert len(result['events']) == 1
...     assert type(result['events'][0]['amount_minor']) is int
...     assert result['events'][0]['amount_minor'] == 10 ** 5002
...     assert result['total_minor'] == 10 ** 5002
"""

from contextlib import closing
from decimal import Decimal
import sqlite3

from money_exact import to_minor_units


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sales_events (
    event_id TEXT PRIMARY KEY NOT NULL COLLATE BINARY,
    customer_id TEXT NOT NULL,
    amount_minor TEXT NOT NULL,
    region TEXT NOT NULL,
    existing_route TEXT NOT NULL,
    route TEXT NOT NULL
)
"""


def _required_string(event, name):
    value = event.get(name)
    if not isinstance(value, str):
        raise ValueError(f'{name} must be a string')
    return value.strip()


def _canonicalize(event):
    if not isinstance(event, dict):
        raise ValueError('each event must be a dict')
    event_id = _required_string(event, 'event_id')
    customer_id = _required_string(event, 'customer_id')
    if not event_id or not customer_id:
        raise ValueError('event_id and customer_id must be nonempty')
    amount_minor = to_minor_units(event.get('amount'))
    region = _required_string(event, 'region').upper()
    existing_route = event.get('existing_route')
    if existing_route is None:
        existing_route = ''
    elif not isinstance(existing_route, str):
        raise ValueError('existing_route must be a string or None')
    else:
        existing_route = existing_route.strip()
    return event_id, customer_id, amount_minor, region, existing_route


def _route(amount_minor, region, existing_route):
    if existing_route:
        return existing_route
    if not region:
        return 'manual_review'
    if amount_minor >= 1_000_000:
        return 'senior'
    return 'standard'


def ingest(db_path, events):
    """Import one batch; roll back every insertion on any error."""
    try:
        batch = iter(events)
    except TypeError as exc:
        raise ValueError('events must be iterable') from exc

    created = replayed = 0
    with closing(sqlite3.connect(db_path, timeout=30)) as db:
        with db:
            # Reserve the writer before reading IDs or initializing the table.
            db.execute('BEGIN IMMEDIATE')
            db.execute(_SCHEMA)
            for event in batch:
                event_id, customer_id, amount_minor, region, existing_route = (
                    _canonicalize(event)
                )
                # Canonical decimal text keeps cents outside SQLite's int range.
                # Decimal bypasses Python's decimal int/string digit limit;
                # construction and fixed-point formatting do not round.
                payload = (customer_id, format(Decimal(amount_minor), 'f'), region, existing_route)
                stored = db.execute(
                    'SELECT customer_id, amount_minor, region, existing_route '
                    'FROM sales_events WHERE event_id = ?', (event_id,)
                ).fetchone()
                if stored is not None:
                    if stored != payload:
                        raise ValueError(f'conflicting payload for event_id {event_id!r}')
                    replayed += 1
                    continue
                db.execute(
                    'INSERT INTO sales_events '
                    '(event_id, customer_id, amount_minor, region, existing_route, route) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (event_id, *payload, _route(amount_minor, region, existing_route))
                )
                created += 1
    return {'created': created, 'replayed': replayed}


def export(db_path):
    """Return a deterministic snapshot with Python integers and an exact total."""
    with closing(sqlite3.connect(db_path, timeout=30)) as db:
        with db:
            # Keep the table check and data read in the same snapshot.
            db.execute('BEGIN')
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                ('sales_events',)
            ).fetchone()
            if exists is None:
                return {'events': [], 'total_minor': 0}
            records = db.execute(
                'SELECT event_id, customer_id, amount_minor, region, existing_route, route '
                'FROM sales_events ORDER BY event_id COLLATE BINARY'
            ).fetchall()

    rows = []
    total_minor = 0
    for event_id, customer_id, amount_text, region, existing_route, route in records:
        amount_minor = int(Decimal(amount_text))
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

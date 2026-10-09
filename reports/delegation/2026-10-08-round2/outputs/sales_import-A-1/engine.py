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


def _minor_units_text(amount):
    """Encode nonnegative cents without Python's decimal digit limit.

    >>> _minor_units_text(to_minor_units('1e4300')) == '1' + '0' * 4302
    True
    """
    chunks = []
    while amount >= 1_000_000_000:
        amount, remainder = divmod(amount, 1_000_000_000)
        chunks.append(f'{remainder:09d}')
    return str(amount) + ''.join(reversed(chunks))


def _minor_units_int(text):
    """Decode stored cents using only bounded decimal conversions.

    >>> _minor_units_int('1' + '0' * 4302) == to_minor_units('1e4300')
    True
    """
    amount = 0
    for start in range(0, len(text), 9):
        chunk = text[start:start + 9]
        amount = amount * 10 ** len(chunk) + int(chunk)
    return amount


def _canonical_event(event):
    if not isinstance(event, dict):
        raise ValueError('each event must be a dict')

    ids = []
    for field in ('event_id', 'customer_id'):
        value = event.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{field} must be a nonempty string')
        ids.append(value.strip())

    region = event.get('region')
    if not isinstance(region, str):
        raise ValueError('region must be a string')
    region = region.strip().upper()

    existing_route = event.get('existing_route')
    if existing_route is None:
        existing_route = ''
    elif not isinstance(existing_route, str):
        raise ValueError('existing_route must be a string or None')
    else:
        existing_route = existing_route.strip()

    amount_minor = to_minor_units(event.get('amount'))
    if existing_route:
        route = existing_route
    elif not region:
        route = 'manual_review'
    elif amount_minor >= 1000000:
        route = 'senior'
    else:
        route = 'standard'

    # Bind cents as text: SQLite integers cannot represent every valid amount.
    return (ids[0], ids[1], _minor_units_text(amount_minor), region, existing_route, route)


def ingest(db_path, events):
    """Import one batch, rolling back every change if any event is invalid."""
    if isinstance(events, (str, bytes, dict)):
        raise ValueError('events must be an iterable of event dicts')
    try:
        events = iter(events)
    except TypeError as exc:
        raise ValueError('events must be an iterable of event dicts') from exc

    created = replayed = 0
    with closing(sqlite3.connect(db_path, timeout=30, isolation_level=None)) as db:
        with db:
            # Acquire the writer lock before checking IDs, including on a new DB.
            db.execute('BEGIN IMMEDIATE')
            db.execute(_SCHEMA)
            for event in events:
                row = _canonical_event(event)
                previous = db.execute(
                    'SELECT customer_id, amount_minor, region, existing_route '
                    'FROM events WHERE event_id = ?', (row[0],)
                ).fetchone()
                if previous is not None:
                    if previous != row[1:5]:
                        raise ValueError(f'conflicting payload for event_id {row[0]!r}')
                    replayed += 1
                else:
                    db.execute(
                        'INSERT INTO events '
                        '(event_id, customer_id, amount_minor, region, existing_route, route) '
                        'VALUES (?, ?, ?, ?, ?, ?)', row
                    )
                    created += 1
    return {'created': created, 'replayed': replayed}


def export(db_path):
    """Return a consistent, sorted snapshot with exact Python integer totals."""
    with closing(sqlite3.connect(db_path, timeout=30, isolation_level=None)) as db:
        with db:
            db.execute('BEGIN')
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'events'"
            ).fetchone() is None:
                return {'events': [], 'total_minor': 0}
            records = db.execute(
                'SELECT event_id, customer_id, amount_minor, region, existing_route, route '
                'FROM events ORDER BY event_id COLLATE BINARY ASC'
            ).fetchall()

    fields = ('event_id', 'customer_id', 'amount_minor', 'region', 'existing_route', 'route')
    rows = []
    total_minor = 0
    for record in records:
        row = dict(zip(fields, record))
        row['amount_minor'] = _minor_units_int(row['amount_minor'])
        total_minor += row['amount_minor']
        rows.append(row)
    return {'events': rows, 'total_minor': total_minor}

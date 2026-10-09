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
_COLUMNS = ("event_id", "customer_id", "amount_minor", "region",
            "existing_route", "route")


def _canonical(event):
    if not isinstance(event, dict):
        raise ValueError("each event must be a dict")
    try:
        event_id = event["event_id"]
        customer_id = event["customer_id"]
        amount = event["amount"]
        region = event["region"]
    except KeyError as exc:
        raise ValueError(f"missing required field: {exc.args[0]}") from exc

    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("event_id must be a nonempty string")
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise ValueError("customer_id must be a nonempty string")
    if not isinstance(region, str):
        raise ValueError("region must be a string")
    existing_route = event.get("existing_route")
    if existing_route is None:
        existing_route = ""
    elif not isinstance(existing_route, str):
        raise ValueError("existing_route must be a string or None")

    amount_minor = to_minor_units(amount)
    payload = (customer_id.strip(), str(amount_minor), region.strip().upper(),
               existing_route.strip())
    if payload[3]:
        route = payload[3]
    elif not payload[2]:
        route = "manual_review"
    elif amount_minor >= 1000000:
        route = "senior"
    else:
        route = "standard"
    return event_id.strip(), payload, route


def ingest(db_path, events):
    """Import a batch atomically, counting canonical-identical IDs as replays."""
    if isinstance(events, (str, bytes, dict)):
        raise ValueError("events must be an iterable of event dicts")
    try:
        batch = iter(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable of event dicts") from exc

    created = replayed = 0
    with closing(sqlite3.connect(db_path, timeout=30, isolation_level=None)) as db:
        # The context manager commits on success and rolls back on any exception.
        with db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(_SCHEMA)
            for event in batch:
                event_id, payload, route = _canonical(event)
                stored = db.execute(
                    "SELECT customer_id, amount_minor, region, existing_route "
                    "FROM events WHERE event_id = ?", (event_id,)
                ).fetchone()
                if stored is not None:
                    if stored != payload:
                        raise ValueError(f"conflicting payload for event_id {event_id!r}")
                    replayed += 1
                else:
                    db.execute(
                        "INSERT INTO events "
                        "(event_id, customer_id, amount_minor, region, existing_route, route) "
                        "VALUES (?, ?, ?, ?, ?, ?)", (event_id, *payload, route)
                    )
                    created += 1
    return {"created": created, "replayed": replayed}


def export(db_path):
    """Return sorted events and an exact Python-integer total."""
    with closing(sqlite3.connect(db_path, timeout=30)) as db:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'events'"
        ).fetchone()
        if exists is None:
            return {"events": [], "total_minor": 0}
        stored = db.execute(
            "SELECT event_id, customer_id, amount_minor, region, existing_route, route "
            "FROM events ORDER BY event_id COLLATE BINARY"
        ).fetchall()

    rows = []
    total_minor = 0
    for values in stored:
        row = dict(zip(_COLUMNS, values))
        row["amount_minor"] = int(row["amount_minor"])
        total_minor += row["amount_minor"]
        rows.append(row)
    return {"events": rows, "total_minor": total_minor}

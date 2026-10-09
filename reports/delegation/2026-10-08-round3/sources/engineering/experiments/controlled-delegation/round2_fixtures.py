"""Deterministic synthetic round 2 fixtures; no model calls or external data.

Expectations belong to the harness and must not enter live task workspaces.
"""
from __future__ import annotations

import csv
import io
import json
import textwrap


def _text(value):
    return textwrap.dedent(value).lstrip()


def _json(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


SALES_TASK = _text("""
    Implement a reliable local sales importer in engine.py using only Python's
    standard library and the supplied money_exact.to_minor_units reference.
    All data and accounts are synthetic; no network or external actions are needed.

    ingest(db_path, events) returns {'created': int, 'replayed': int} for one batch.
    Each event is a dict with event_id, customer_id, amount (decimal string), region
    (string), and optional existing_route (string or None). Trim IDs; reject empty
    IDs. Strip and uppercase region. Normalize missing/None/blank existing_route to
    ''; otherwise strip it and retain its case. Canonical payload consists of
    customer_id, exact amount_minor, region, existing_route. Event IDs are immutable:
    repeat of a canonical-identical ID counts as replay, including repeats within
    one batch; changed canonical payload raises ValueError. Different textual
    amounts for the same exact cents are identical. Invalid input raises ValueError.
    An error anywhere rolls back the entire batch, including earlier new events.

    Route precedence: a nonblank existing_route wins; otherwise a blank region is
    manual_review; otherwise amount_minor >= 1000000 is senior; otherwise standard.
    Store integer cents in SQLite TEXT, so values above SQLite's integer range,
    including decimal strings near the largest finite binary float, survive exactly.
    No conversion through float and no rounding fractional cents. Use SQLite as the
    persistent store. Concurrent writers must serialize: two calls ingesting the
    same new event must produce one creation and one replay, with no duplicate row
    or lock failure. BEGIN IMMEDIATE plus a reasonable SQLite busy timeout is useful.

    export(db_path) returns {'events': rows, 'total_minor': int}. Each row has exactly
    event_id, customer_id, amount_minor (Python int), region, existing_route, route.
    Sort rows by canonical event_id ascending; total_minor is the exact sum, counting
    each ID once. Export an unused database as an empty list and zero total.

    Preserve test_engine.py, README.md and money_exact.py. You may edit engine.py
    and STATE.md only. Run python -m unittest -v test_engine. In STATE.md record the
    rules you implemented, commands and observed results, remaining limits and the
    next safe step. Tests are evidence only when actually executed.
""")


SALES_TESTS = _text(r"""
    import concurrent.futures
    import sqlite3
    import tempfile
    import threading
    import unittest
    from pathlib import Path
    import engine

    class ImportTests(unittest.TestCase):
        def setUp(self):
            self.tmp = tempfile.TemporaryDirectory()
            self.addCleanup(self.tmp.cleanup)
            self.db = str(Path(self.tmp.name) / 'sales.sqlite3')

        def event(self, event_id='E-1', amount='12.34', **extra):
            return dict(event_id=event_id, customer_id='C-1', amount=amount,
                        region=extra.pop('region', 'eu-west'), **extra)

        def test_exact_money(self):
            largest = '17976931348623157' + '0' * 292
            amounts = ['1000000000000000.01', '10000000000000000.99', largest]
            expected = [100000000000000001, 1000000000000000099, int(largest) * 100]
            self.assertEqual(engine.ingest(self.db, [self.event(str(i), a)
                             for i, a in enumerate(amounts)]), {'created': 3, 'replayed': 0})
            out = engine.export(self.db)
            self.assertEqual([row['amount_minor'] for row in out['events']], expected)
            self.assertTrue(all(type(row['amount_minor']) is int for row in out['events']))
            self.assertEqual(out['total_minor'], sum(expected))
            with sqlite3.connect(self.db) as db:
                tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                stored = []
                for (name,) in tables:
                    quoted = name.replace('"', '""')
                    columns = [r[1] for r in db.execute('PRAGMA table_info("' + quoted + '")')]
                    if 'amount_minor' in columns:
                        stored.extend(db.execute('SELECT typeof(amount_minor) FROM "' + quoted + '"'))
                self.assertEqual(stored, [('text',)] * 3)

        def test_routing(self):
            events = [self.event('a', '9999.99'), self.event('b', '10000'),
                      self.event('c', '10000', region=' '),
                      self.event('d', '100000', region='', existing_route=' VIP '),
                      self.event('e', '0', existing_route=' ')]
            engine.ingest(self.db, events)
            rows = engine.export(self.db)['events']
            self.assertEqual([r['route'] for r in rows],
                             ['standard', 'senior', 'manual_review', 'VIP', 'standard'])
            self.assertEqual(rows[3]['existing_route'], 'VIP')
            self.assertEqual(rows[4]['existing_route'], '')

        def test_replay(self):
            first = self.event(' E-1 ', '12.340', existing_route=None)
            first['customer_id'] = ' C-1 '
            duplicate = self.event('E-1', '1.234e1', region=' EU-WEST ', existing_route='')
            self.assertEqual(engine.ingest(self.db, [first, duplicate, duplicate]),
                             {'created': 1, 'replayed': 2})
            self.assertEqual(engine.ingest(self.db, [duplicate]), {'created': 0, 'replayed': 1})
            self.assertEqual(len(engine.export(self.db)['events']), 1)

        def test_conflicts(self):
            original = self.event()
            engine.ingest(self.db, [original])
            for patch in [{'customer_id': 'C-2'}, {'amount': '12.35'},
                          {'region': 'eu-central'}, {'existing_route': 'VIP'}]:
                changed = dict(original, **patch)
                with self.subTest(patch=patch), self.assertRaises(ValueError):
                    engine.ingest(self.db, [changed])
            self.assertEqual(engine.export(self.db)['total_minor'], 1234)

        def test_atomicity(self):
            engine.ingest(self.db, [self.event('old')])
            with self.assertRaises(ValueError):
                engine.ingest(self.db, [self.event('new'), self.event('old', '99')])
            with self.assertRaises(ValueError):
                engine.ingest(self.db, [self.event('batch'), self.event('batch', '99')])
            invalids = [{'event_id': ' '}, {'customer_id': ''}, {'amount': 'NaN'},
                        {'amount': '-0.01'}, {'amount': '0.001'}, {'amount': 12.34},
                        {'region': None}, {'existing_route': 12}]
            for patch in invalids:
                with self.subTest(patch=patch), self.assertRaises(ValueError):
                    engine.ingest(self.db, [self.event('new'), dict(self.event('bad'), **patch)])
            self.assertEqual([r['event_id'] for r in engine.export(self.db)['events']], ['old'])

        def test_deterministic_export(self):
            self.assertEqual(engine.export(self.db), {'events': [], 'total_minor': 0})
            engine.ingest(self.db, [self.event('z', '0'), self.event(' b ', '0.02'),
                                   self.event('a', '0.01', region=' EU-CENTRAL ')])
            expected = {'events': [
                {'event_id': 'a', 'customer_id': 'C-1', 'amount_minor': 1,
                 'region': 'EU-CENTRAL', 'existing_route': '', 'route': 'standard'},
                {'event_id': 'b', 'customer_id': 'C-1', 'amount_minor': 2,
                 'region': 'EU-WEST', 'existing_route': '', 'route': 'standard'},
                {'event_id': 'z', 'customer_id': 'C-1', 'amount_minor': 0,
                 'region': 'EU-WEST', 'existing_route': '', 'route': 'standard'}], 'total_minor': 3}
            self.assertEqual(engine.export(self.db), expected)
            self.assertEqual(engine.export(self.db), expected)

        def test_concurrency(self):
            barrier = threading.Barrier(2)
            def invoke():
                barrier.wait(timeout=5)
                return engine.ingest(self.db, [self.event('shared', '10000000000000000.01')])
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(invoke) for _ in range(2)]
                results = [f.result(timeout=15) for f in futures]
            self.assertEqual(sorted((r['created'], r['replayed']) for r in results), [(0, 1), (1, 0)])
            self.assertEqual(len(engine.export(self.db)['events']), 1)
            self.assertEqual(engine.export(self.db)['total_minor'], 1000000000000000001)

    if __name__ == '__main__':
        unittest.main()
""")


RELEASE_TASK = _text("""
    Prepare a release gate decision for release 2.8 in eu-central and eu-west, as
    of 2026-10-08T12:00:00Z, from the current performance, incident and safety/cost
    sources in data/. These are synthetic operational records. Do not contact
    anyone, deploy anything or use external accounts. legacy_snapshot.json is an
    earlier assessment and cannot override current records. Source files are frozen.

    Apply four independent gates. HOLD if any gate fails; otherwise GO.
    1. Performance: select records for release 2.8 and target regions, status measured,
       measured_at in [2026-10-07T12:00:00Z, 2026-10-08T12:00:00Z], updated_at no
       later than assessment time. Deduplicate record_id by latest updated_at before
       evaluating. A regression strictly greater than 15% (current_p95_ms compared
       to baseline_p95_ms), with samples >= 1000, blocks its region. Equality passes.
    2. Incidents: discard future updates, deduplicate incident_id by latest updated_at.
       Latest open P1 incidents for target release/regions and service checkout or
       refunds block. Resolved incidents, P2, other services/releases/regions do not.
    3. Safety: discard future updates; deduplicate record_id by latest updated_at.
       For each target region, require verification true for BOTH audit and recovery
       on release 2.8. Any false or absent check blocks. Report missing_safety_checks
       as 'region:check' strings (false means unverified). Use the applicable latest
       current safety record for each region/check; ignore other versions/regions.
    4. Cost: from the latest current cost record for release 2.8 and exactly the two
       target regions (discard future updates), evaluate the combined monthly
       projection. Cost and budget are decimal strings representing whole cents.
       HOLD if projected monthly cost is strictly more than 110% of budget.
       cost_delta_minor is projection minus budget in cents. No float rounding;
       thresholds must be assessed exactly.

    Write decision.json with exactly these keys: decision ('HOLD' or 'GO'),
    latency_regions, incident_ids, missing_safety_checks, cost_delta_minor, evidence_ids.
    All list values must be sorted and unique. evidence_ids contains the explicit
    record_id/incident_id for each actual blocking performance record, incident,
    unverified safety record, and current cost record if cost blocks. Do not list
    excluded/noise records or the legacy snapshot. If a safety record is absent,
    report the missing check but do not invent an evidence ID.

    Write BRIEF.md explaining findings, how conflicting/stale records were resolved,
    evidence references, business impact and the next safe action. Write STATE.md
    with rules, observed verification commands/results, remaining limitations and
    next step. You may create/edit decision.json, BRIEF.md and STATE.md only.
""")


def _release_sources():
    performance = []
    for i in range(72):
        performance.append(dict(record_id=f'perf-noise-{i:03d}', release='2.7' if i % 3 == 0 else '2.8',
            region=('us-east', 'eu-north', 'eu-central')[i % 3], endpoint=('checkout', 'refunds')[i % 2],
            baseline_p95_ms=200, current_p95_ms=210 + i % 10, samples=1400,
            status='measured', measured_at='2026-10-08T08:00:00Z', updated_at='2026-10-08T09:00:00Z'))

    def perf(rid, region='eu-central', p95=210, samples=1500):
        return dict(record_id=rid, release='2.8', region=region, endpoint='checkout',
                    baseline_p95_ms=200, current_p95_ms=p95, samples=samples, status='measured',
                    measured_at='2026-10-08T09:00:00Z', updated_at='2026-10-08T10:00:00Z')

    performance.extend([
        perf('perf-central-checkout', p95=220),
        dict(perf('perf-central-checkout', p95=234), updated_at='2026-10-08T11:00:00Z'),
        dict(perf('perf-west-refunds', region='eu-west', p95=240), endpoint='refunds'),
        perf('perf-west-boundary', region='eu-west', p95=230),
        perf('perf-low-sample', p95=350, samples=999),
        dict(perf('perf-stale'), measured_at='2026-10-06T10:00:00Z', current_p95_ms=400),
        dict(perf('perf-future'), updated_at='2026-10-08T13:00:00Z', current_p95_ms=400),
        dict(perf('perf-obsolete'), current_p95_ms=400),
        dict(perf('perf-obsolete'), current_p95_ms=205, updated_at='2026-10-08T11:00:00Z'),
        dict(perf('perf-estimate'), current_p95_ms=400, status='estimated'),
    ])
    incidents = []
    for i in range(84):
        incidents.append(dict(incident_id=f'INC-N{i:03d}', release='2.7' if i % 2 else '2.8',
            region=('us-east', 'eu-west', 'eu-central')[i % 3], service=('search', 'checkout')[i % 2],
            severity='P2', status='resolved' if i % 4 else 'open',
            opened_at='2026-10-06T07:00:00Z', updated_at='2026-10-08T08:00:00Z',
            summary=f'Synthetic operational observation {i}; no customer data'))

    def incident(iid, region='eu-central', service='checkout', **patch):
        row = dict(incident_id=iid, release='2.8', region=region, service=service,
                   severity='P1', status='open', opened_at='2026-10-08T07:00:00Z',
                   updated_at='2026-10-08T09:00:00Z', summary='Synthetic fault; exercise only')
        row.update(patch)
        return row

    incidents.extend([
        incident('INC-210'), incident('INC-211', region='eu-west', service='refunds'),
        incident('INC-212'), incident('INC-212', status='resolved', updated_at='2026-10-08T11:00:00Z'),
        incident('INC-213', severity='P2'), incident('INC-214', release='2.7'),
        incident('INC-215', service='search'), incident('INC-216', region='us-east'),
        incident('INC-217', updated_at='2026-10-08T13:00:00Z'),
    ])
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(incidents[0]))
    writer.writeheader()
    writer.writerows(incidents)
    records = []
    for i in range(36):
        records.append(dict(record_id=f'safety-noise-{i:03d}', kind='safety', release='2.7',
            region=('eu-central', 'eu-west', 'us-east')[i % 3], check=('audit', 'recovery')[i % 2],
            verified=True, updated_at='2026-10-08T08:00:00Z'))

    def safety(rid, region, check, verified, **patch):
        row = dict(record_id=rid, kind='safety', release='2.8', region=region,
                   check=check, verified=verified, updated_at='2026-10-08T10:00:00Z')
        row.update(patch)
        return row

    records.extend([
        safety('safe-central-audit', 'eu-central', 'audit', True),
        safety('safe-central-recovery', 'eu-central', 'recovery', True),
        safety('safe-central-recovery', 'eu-central', 'recovery', False, updated_at='2026-10-08T11:00:00Z'),
        safety('safe-west-audit', 'eu-west', 'audit', False),
        safety('safe-west-recovery', 'eu-west', 'recovery', True),
        safety('safe-west-audit-future', 'eu-west', 'audit', True, updated_at='2026-10-08T13:00:00Z'),
        dict(record_id='cost-target', kind='cost', release='2.8', regions=['eu-central', 'eu-west'],
             monthly_projection='105000.00', monthly_budget='100000.00', updated_at='2026-10-08T08:00:00Z'),
        dict(record_id='cost-target', kind='cost', release='2.8', regions=['eu-central', 'eu-west'],
             monthly_projection='112345.67', monthly_budget='100000.00', updated_at='2026-10-08T11:00:00Z'),
        dict(record_id='cost-old-version', kind='cost', release='2.7', regions=['eu-central', 'eu-west'],
             monthly_projection='500000.00', monthly_budget='100000.00', updated_at='2026-10-08T11:00:00Z'),
    ])
    legacy = dict(assessment_at='2026-10-06T12:00:00Z', release='2.8', decision='GO',
                  latency_regions=[], incident_ids=[], missing_safety_checks=[],
                  cost_delta_minor=500000, evidence_ids=[],
                  note='Earlier synthetic snapshot; current sources supersede this assessment.')
    return {
        'data/performance.json': _json({'assessment_at': '2026-10-08T12:00:00Z', 'records': performance}),
        'data/incidents.csv': buffer.getvalue(),
        'data/safety_cost.json': _json({'assessment_at': '2026-10-08T12:00:00Z', 'records': records}),
        'data/legacy_snapshot.json': _json(legacy),
    }


def cases():
    """Return fresh fixture dictionaries; no mutable global result is shared."""
    sales = dict(task=SALES_TASK, files={
        'engine.py': _text('''
            """Implement the synthetic local sales importer described in TASK.md."""

            def ingest(db_path, events):
                raise NotImplementedError('implement atomic exact-cent import')

            def export(db_path):
                raise NotImplementedError('implement deterministic export')
        '''),
        'test_engine.py': SALES_TESTS,
        'README.md': 'Synthetic SQLite sales import exercise. See TASK.md for the contract.\n'
                     'Public checks: python -m unittest -v test_engine. No external service is used.\n',
        'STATE.md': '# State\n\nImplementation and verification have not been performed.\n',
    }, mutable=['engine.py', 'STATE.md'], min_workers_c=2,
        groups={'test_exact_money': 10, 'test_routing': 10, 'test_replay': 15,
                'test_conflicts': 15, 'test_atomicity': 20,
                'test_deterministic_export': 10, 'test_concurrency': 20})
    sources = _release_sources()
    sources.update({'README.md': 'Synthetic release gate exercise. See TASK.md. Current data sources override legacy_snapshot.json.\n',
                    'decision.json': '{}\n',
                    'BRIEF.md': '# Release findings\n\nAnalysis has not been performed.\n',
                    'STATE.md': '# State\n\nAnalysis and verification have not been performed.\n'})
    release = dict(task=RELEASE_TASK, files=sources,
        mutable=['decision.json', 'BRIEF.md', 'STATE.md'], min_workers_c=2,
        groups={'decision': 15, 'latency_regions': 15, 'incident_ids': 15,
                'missing_safety_checks': 15, 'cost_delta_minor': 15,
                'evidence_ids': 15, 'brief_state': 10},
        expected={'decision': 'HOLD', 'latency_regions': ['eu-central', 'eu-west'],
            'incident_ids': ['INC-210', 'INC-211'],
            'missing_safety_checks': ['eu-central:recovery', 'eu-west:audit'],
            'cost_delta_minor': 1234567,
            'evidence_ids': ['INC-210', 'INC-211', 'cost-target', 'perf-central-checkout',
                             'perf-west-refunds', 'safe-central-recovery', 'safe-west-audit']})
    return {'sales_import': sales, 'release_gate': release}

"""Round 3 synthetic fulfillment incident. Hidden oracle stays outside workspaces.

This is a real broken stdlib replay application, not a questionnaire. Three
source defects interact; each also has independent reproduction inputs. Reference
patches exist solely for fixture acceptance and must never enter a live run.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import textwrap


def _text(value):
    return textwrap.dedent(value).lstrip()


def _json(value):
    return json.dumps(value, sort_keys=True, indent=2) + '\n'


GROUPS = {'inventory': 15, 'checkout': 15, 'refunds': 15, 'integration': 15,
          'unaffected': 10, 'diagnosis_inventory': 8, 'diagnosis_checkout': 8,
          'diagnosis_refunds': 8, 'state': 6}

TASK = _text('''
    Diagnose and repair a synthetic fulfillment replay incident in this repository.
    The replay application joins warehouse operations, checkout revisions and refund
    provider deliveries. Current records show missing holds, incorrect checkout
    state and refund totals. Three independently reproducible source defects interact.
    Establish their causes from source and current evidence; distinguish stale
    historical advice from records for build r31. Preserve unrelated behavior.

    Read README.md, docs/contracts.md and docs/incident.md. Replay with
    python -B -m src.replay data/current/combined.json; run the supplied checks with
    python -B -m unittest discover -s tests -v. Only stdlib and local synthetic data
    are needed. Inputs, documents, configs and tests are immutable. You may modify
    existing src/**/*.py files, diagnosis.json and STATE.md only. Fix the fewest
    source files that address causes, rather than changing expectations or masking
    the incident. Keep the replay API and public output contract intact. One main
    agent writes final shared source changes; investigators may report findings.

    Write diagnosis.json as an object with defects (exactly three objects),
    verification (object with commands and observed_results lists) and remaining_limits
    (list). Each defect has source_files (list of actual causal paths), evidence_ids
    (list of record_id, event_id or trace_id values from immutable records), mechanism
    (explain the erroneous operation and correct invariant), impact (causal downstream
    consequences), stale_evidence_ids (list of specific excluded historical IDs).
    Cite the current triggering records and supporting trace(s), rather than only
    test names or vague filenames. Explain why historical diagnoses are inapplicable.
    Record actual local commands and observed outcomes in STATE.md, as well as
    remaining limits and the next safe step. Do not claim live/production success.
''')


def _base_modules():
    # All production modules are functional collaborators of replay; legacy modules
    # describe a previous route, deliberately retained as plausible investigation noise.
    return {
        'src/__init__.py': '"""Synthetic local fulfillment application."""\n',
        'src/common/__init__.py': '"""Shared wire-format and validation helpers."""\n',
        'src/common/ids.py': _text('''
            def identifier(value):
                if not isinstance(value, str) or not value.strip():
                    raise ValueError('nonblank string identifier required')
                return value.strip()

            def order_key(row):
                return identifier(row['tenant']), identifier(row['order_id'])
        '''),
        'src/common/numbers.py': _text('''
            def whole(value, minimum=0):
                if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                    raise ValueError('integer outside supported range')
                return value
        '''),
        'src/common/time.py': _text('''
            from datetime import datetime

            def instant(value):
                result = datetime.fromisoformat(value.replace('Z', '+00:00'))
                if result.tzinfo is None:
                    raise ValueError('timezone required')
                return result
        '''),
        'src/common/records.py': _text('''
            from .ids import identifier

            def require_build(document, build='r31'):
                if document.get('build') != build:
                    raise ValueError('unsupported replay build')
                return document

            def event_id(row):
                return identifier(row['event_id'])
        '''),
        'src/common/jsonio.py': _text('''
            import json
            from pathlib import Path

            def read(path):
                return json.loads(Path(path).read_text(encoding='utf-8'))

            def render(value):
                return json.dumps(value, sort_keys=True, indent=2)
        '''),
        'src/common/errors.py': _text('''
            def conflict(domain, identity):
                raise ValueError('%s immutable identity conflict: %r' % (domain, identity))
        '''),
        'src/inventory/__init__.py': '"""Warehouse scoped stock and holds."""\n',
        'src/inventory/normalize.py': _text('''
            from src.common.ids import identifier
            from src.common.numbers import whole
            from src.common.records import event_id

            def operation(row):
                out = {key: identifier(row[key]) for key in
                       ('tenant', 'warehouse', 'operation_id', 'order_id', 'sku')}
                out.update(event_id=event_id(row), action=row['action'], qty=whole(row['qty'], 1))
                if out['action'] not in ('reserve', 'release'):
                    raise ValueError('unknown warehouse action')
                return out
        '''),
        'src/inventory/registry.py': _text('''
            from src.common.errors import conflict

            class Registry:
                def __init__(self):
                    self.operations = {}

                def accept(self, row):
                    identity = row['operation_id']
                    payload = (row['order_id'], row['sku'], row['action'], row['qty'])
                    if identity in self.operations:
                        if self.operations[identity] != payload:
                            conflict('inventory', identity)
                        return False
                    self.operations[identity] = payload
                    return True
        '''),
        'src/inventory/buckets.py': _text('''
            from src.common.ids import identifier
            from src.common.numbers import whole

            def stock_key(row):
                return tuple(identifier(row[k]) for k in ('tenant', 'warehouse', 'sku'))

            def load(rows):
                result = {}
                for row in rows:
                    key = stock_key(row)
                    if key in result:
                        raise ValueError('duplicate opening stock bucket')
                    result[key] = whole(row['qty'])
                return result
        '''),
        'src/inventory/holds.py': _text('''
            def hold_key(row):
                return row['tenant'], row['warehouse'], row['order_id'], row['sku']

            def reserved_for_stock(holds, stock):
                tenant, warehouse, sku = stock
                return sum(qty for (t, w, _order, s), qty in holds.items()
                           if (t, w, s) == (tenant, warehouse, sku))
        '''),
        'src/inventory/apply.py': _text('''
            from .buckets import stock_key
            from .holds import hold_key, reserved_for_stock

            def apply(row, opening, holds):
                bucket, hold = stock_key(row), hold_key(row)
                if bucket not in opening:
                    raise ValueError('unknown stock bucket')
                previous = holds.get(hold, 0)
                if row['action'] == 'reserve':
                    available = opening[bucket] - reserved_for_stock(holds, bucket)
                    if available < row['qty']:
                        raise ValueError('insufficient stock')
                    holds[hold] = previous + row['qty']
                else:
                    if previous < row['qty']:
                        raise ValueError('release exceeds own hold')
                    holds[hold] = previous - row['qty']
        '''),
        'src/inventory/export.py': _text('''
            from .holds import reserved_for_stock

            def view(opening, holds, accepted, replayed):
                return {'stock': [dict(tenant=t, warehouse=w, sku=s, on_hand=qty,
                            reserved=reserved_for_stock(holds, (t, w, s)),
                            available=qty-reserved_for_stock(holds, (t, w, s)))
                        for (t, w, s), qty in sorted(opening.items())],
                        'holds': [dict(tenant=t, warehouse=w, order_id=o, sku=s, qty=q)
                                  for (t,w,o,s), q in sorted(holds.items()) if q],
                        'accepted': accepted, 'replayed': replayed}
        '''),
        'src/inventory/projector.py': _text('''
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
        '''),
        'src/checkout/__init__.py': '"""Source revision projection and fulfillment gates."""\n',
        'src/checkout/normalize.py': _text('''
            from src.common.ids import identifier
            from src.common.numbers import whole
            from src.common.time import instant
            from src.common.records import event_id
            from .states import STATES

            def snapshot(row):
                result = dict(row)
                for key in ('tenant', 'order_id'):
                    result[key] = identifier(row[key])
                result['event_id'] = event_id(row)
                result['revision'] = whole(row['revision'], 1)
                result['captured_minor'] = whole(row['captured_minor'])
                result['delivered_at'] = instant(row['delivered_at'])
                if row['status'] not in STATES:
                    raise ValueError('unsupported order status')
                result['lines'] = [dict(warehouse=identifier(line['warehouse']),
                                      sku=identifier(line['sku']), qty=whole(line['qty'], 1))
                                   for line in row['lines']]
                return result
        '''),
        'src/checkout/states.py': _text('''
            STATES = frozenset({'pending', 'paid', 'shipped', 'cancelled'})
            REFUNDABLE = frozenset({'paid', 'shipped', 'cancelled'})
        '''),
        'src/checkout/revisions.py': _text('''
            from src.common.ids import order_key
            from src.common.errors import conflict

            def select(rows):
                chosen, identities = {}, {}
                for row in rows:
                    key = order_key(row)
                    identity = key + (row['revision'],)
                    payload = (row['status'], row['captured_minor'], row['lines'])
                    if identity in identities and identities[identity] != payload:
                        conflict('checkout', identity)
                    identities[identity] = payload
                    old = chosen.get(key)
                    if old is None or row['delivered_at'] > old['delivered_at']:
                        chosen[key] = row
                return chosen
        '''),
        'src/checkout/requirements.py': _text('''
            def required_holds(order):
                result = {}
                for line in order['lines']:
                    key = order['tenant'], line['warehouse'], order['order_id'], line['sku']
                    result[key] = result.get(key, 0) + line['qty']
                return result
        '''),
        'src/checkout/fulfillment.py': _text('''
            from .requirements import required_holds

            def readiness(order, holds):
                if order['status'] not in ('paid', 'shipped'):
                    return False
                return all(holds.get(key, 0) >= qty for key, qty in required_holds(order).items())
        '''),
        'src/checkout/export.py': _text('''
            from .fulfillment import readiness

            def view(rows, inventory):
                holds = {(r['tenant'], r['warehouse'], r['order_id'], r['sku']): r['qty']
                         for r in inventory['holds']}
                return [dict(tenant=t, order_id=o, revision=r['revision'], status=r['status'],
                             captured_minor=r['captured_minor'], ready=readiness(r, holds))
                        for (t, o), r in sorted(rows.items())]
        '''),
        'src/checkout/projector.py': _text('''
            from .normalize import snapshot
            from .revisions import select
            from .export import view

            def project(deliveries, inventory):
                return view(select(snapshot(row) for row in deliveries), inventory)
        '''),
        'src/refunds/__init__.py': '"""Provider deliveries and canonical customer refunds."""\n',
        'src/refunds/normalize.py': _text('''
            from src.common.ids import identifier
            from src.common.numbers import whole
            from src.common.records import event_id

            def refund(row):
                result = {k: identifier(row[k]) for k in
                          ('tenant', 'order_id', 'refund_id', 'attempt_id', 'provider')}
                result['event_id'] = event_id(row)
                result['amount_minor'] = whole(row['amount_minor'], 1)
                if row['status'] != 'succeeded':
                    raise ValueError('only settled refund deliveries belong in this replay')
                return result
        '''),
        'src/refunds/ledger.py': _text('''
            from src.common.errors import conflict

            class Ledger:
                def __init__(self):
                    self.seen = {}

                def accept(self, row):
                    identity = row['tenant'], row['provider'], row['attempt_id']
                    payload = row['order_id'], row['amount_minor']
                    if identity in self.seen:
                        if self.seen[identity] != payload:
                            conflict('refunds', identity)
                        return False
                    self.seen[identity] = payload
                    return True
        '''),
        'src/refunds/eligibility.py': _text('''
            from src.checkout.states import REFUNDABLE

            def allowed(order):
                return order is not None and order['status'] in REFUNDABLE
        '''),
        'src/refunds/budget.py': _text('''
            def reserve(order, spent, amount):
                if spent + amount > order['captured_minor']:
                    return False
                return True
        '''),
        'src/refunds/projector.py': _text('''
            from src.common.ids import order_key
            from .normalize import refund
            from .ledger import Ledger
            from .eligibility import allowed
            from .budget import reserve
            from .summary import view

            def project(deliveries, orders):
                by_order = {order_key(row): row for row in orders}
                ledger, totals, accepted, rejected = Ledger(), {}, [], []
                replayed = 0
                for delivery in deliveries:
                    row = refund(delivery)
                    if not ledger.accept(row):
                        replayed += 1
                        continue
                    key = order_key(row)
                    order, spent = by_order.get(key), totals.get(key, 0)
                    reason = None
                    if not allowed(order):
                        reason = 'order_not_refundable'
                    elif not reserve(order, spent, row['amount_minor']):
                        reason = 'exceeds_capture'
                    if reason:
                        rejected.append(dict(event_id=row['event_id'], reason=reason))
                    else:
                        totals[key] = spent + row['amount_minor']
                        accepted.append(dict(tenant=row['tenant'], provider=row['provider'],
                            refund_id=row['refund_id'], order_id=row['order_id'], amount_minor=row['amount_minor']))
                return view(totals, accepted, rejected, replayed)
        '''),
        'src/refunds/summary.py': _text('''
            def view(totals, accepted, rejected, replayed):
                return {'totals': [dict(tenant=t, order_id=o, refunded_minor=q)
                                   for (t,o), q in sorted(totals.items())],
                        'accepted': sorted(accepted, key=lambda r:
                                          (r['tenant'], r['provider'], r['refund_id'])),
                        'rejected': rejected, 'replayed': replayed}
        '''),
        'src/reporting/__init__.py': '"""Deterministic local joined views."""\n',
        'src/reporting/join.py': _text('''
            from src.common.ids import order_key

            def join(orders, refunds):
                amounts = {order_key(row): row['refunded_minor'] for row in refunds['totals']}
                return [dict(row, refunded_minor=amounts.get(order_key(row), 0),
                             net_minor=row['captured_minor']-amounts.get(order_key(row), 0))
                        for row in orders]
        '''),
        'src/reporting/metrics.py': _text('''
            def summarize(inventory, orders, refunds):
                return {'ready_orders': sum(row['ready'] for row in orders),
                        'reserved_units': sum(row['reserved'] for row in inventory['stock']),
                        'refunded_minor': sum(row['refunded_minor'] for row in refunds['totals']),
                        'rejected_refunds': len(refunds['rejected'])}
        '''),
        'src/pipeline.py': _text('''
            from src.common.records import require_build
            from src.inventory.projector import project as stock
            from src.checkout.projector import project as checkout
            from src.refunds.projector import project as refunds
            from src.reporting.join import join
            from src.reporting.metrics import summarize

            def replay(document):
                require_build(document)
                inventory = stock(document['opening_stock'], document['inventory_events'])
                orders = checkout(document['checkout_events'], inventory)
                refund_view = refunds(document['refund_events'], orders)
                return {'inventory': inventory, 'orders': join(orders, refund_view),
                        'refunds': refund_view, 'metrics': summarize(inventory, orders, refund_view)}
        '''),
        'src/replay.py': _text('''
            import argparse
            from src.common.jsonio import read, render
            from src.pipeline import replay

            def main():
                parser = argparse.ArgumentParser(description='Local deterministic fulfillment replay')
                parser.add_argument('input')
                args = parser.parse_args()
                print(render(replay(read(args.input))))

            if __name__ == '__main__':
                main()
        '''),
        'src/legacy/__init__.py': '"""Retained r29 import bridge; r31 replay does not use it."""\n',
        'src/legacy/reservation_cache.py': _text('''
            def key(row):
                # Old single-warehouse bridge feeds have globally unique event IDs.
                return row['event_id']

            def collapsed(rows):
                return {key(row): row for row in rows}
        '''),
        'src/legacy/status_bridge.py': _text('''
            def from_poll(row):
                # r29 polling feed had no source revision.
                return {'order_id': row['order_id'], 'status': row['remote_status'],
                        'observed_at': row['polled_at']}
        '''),
    }


def _modules():
    files = _base_modules()
    files.update({
        'src/validation.py': _text('''
            """Validate transport containers before domain-specific normalization."""
            from src.common.ids import identifier
            from src.common.numbers import whole
            from src.common.time import instant

            CHANNELS = ('inventory_events', 'checkout_events', 'refund_events')
            REQUIRED = {
                'inventory_events': {'event_id','tenant','warehouse','operation_id',
                                     'order_id','sku','action','qty'},
                'checkout_events': {'event_id','tenant','order_id','revision','status',
                                    'captured_minor','lines','delivered_at'},
                'refund_events': {'event_id','tenant','order_id','refund_id','attempt_id',
                                  'provider','amount_minor','status'},
            }

            def mapping(value, label):
                if not isinstance(value, dict):
                    raise ValueError(label + ' must be an object')
                return value

            def array(value, label):
                if not isinstance(value, list):
                    raise ValueError(label + ' must be an array')
                return value

            def exact_keys(value, allowed, required, label):
                mapping(value, label)
                if set(value) - allowed or required - set(value):
                    raise ValueError(label + ' unsupported or missing fields')
                return value

            def event(row, channel):
                mapping(row, channel + ' event')
                if channel not in REQUIRED or REQUIRED[channel] - set(row):
                    raise ValueError('event fields do not satisfy channel schema')
                for key in ('event_id','tenant','order_id'):
                    identifier(row[key])
                if channel == 'inventory_events':
                    for key in ('warehouse','operation_id','sku'):
                        identifier(row[key])
                    whole(row['qty'], 1)
                elif channel == 'checkout_events':
                    whole(row['revision'], 1)
                    whole(row['captured_minor'])
                    instant(row['delivered_at'])
                    for line in array(row['lines'], 'order lines'):
                        mapping(line, 'order line')
                        identifier(line['warehouse'])
                        identifier(line['sku'])
                        whole(line['qty'], 1)
                else:
                    for key in ('refund_id','attempt_id','provider'):
                        identifier(row[key])
                    whole(row['amount_minor'], 1)
                return row

            def opening(rows):
                for row in array(rows, 'opening stock'):
                    mapping(row, 'opening stock row')
                    for key in ('tenant','warehouse','sku'):
                        identifier(row[key])
                    whole(row['qty'])
                return rows

            def canonical(document):
                exact_keys(document, {'build','opening_stock',*CHANNELS},
                           {'build','opening_stock',*CHANNELS}, 'canonical replay')
                if document['build'] != 'r31':
                    raise ValueError('unsupported replay build')
                opening(document['opening_stock'])
                for channel in CHANNELS:
                    for row in array(document[channel], channel):
                        event(row, channel)
                return document
        '''),
        'src/streaming.py': _text('''
            """Deterministic batch delivery reconstruction, independent of wall clock."""
            import json
            from src.common.ids import identifier
            from src.common.numbers import whole
            from src.common.time import instant
            from src.common.errors import conflict
            from src.validation import CHANNELS, array, exact_keys, event

            def payload(batch):
                # delivered_at and batch_id describe transport, not logical payload.
                return json.dumps({'channel':batch['channel'], 'ordinal':batch['ordinal'],
                                   'records':batch['records']}, sort_keys=True,
                                  separators=(',', ':'))

            def reconstruct(batches):
                unique, channel_ordinals = {}, {}
                for raw in array(batches, 'batches'):
                    exact_keys(raw, {'batch_id','channel','ordinal','delivered_at','records'},
                               {'batch_id','channel','ordinal','delivered_at','records'}, 'batch')
                    batch_id = identifier(raw['batch_id'])
                    channel = raw['channel']
                    if channel not in CHANNELS:
                        raise ValueError('unknown batch channel')
                    ordinal = whole(raw['ordinal'])
                    instant(raw['delivered_at'])
                    for row in array(raw['records'], 'batch records'):
                        event(row, channel)
                    signature = payload(raw)
                    if batch_id in unique:
                        if unique[batch_id][1] != signature:
                            conflict('transport batch', batch_id)
                        continue
                    slot = channel, ordinal
                    if slot in channel_ordinals:
                        raise ValueError('multiple batch IDs claim one channel ordinal')
                    unique[batch_id] = raw, signature
                    channel_ordinals[slot] = batch_id
                result = {channel:[] for channel in CHANNELS}
                for channel in CHANNELS:
                    ordinals = sorted(ordinal for (name, ordinal) in channel_ordinals if name == channel)
                    if ordinals != list(range(len(ordinals))):
                        raise ValueError('batch channel has an ordinal gap')
                    for ordinal in ordinals:
                        batch_id = channel_ordinals[channel, ordinal]
                        result[channel].extend(unique[batch_id][0]['records'])
                return result
        '''),
        'src/checkpoints.py': _text('''
            """Content-digested event checkpoints, not derived/projection snapshots."""
            import copy
            import hashlib
            import json
            from src.common.ids import identifier
            from src.validation import CHANNELS, canonical, exact_keys

            def digest(document):
                body = json.dumps(document, sort_keys=True, separators=(',', ':'),
                                  ensure_ascii=False).encode('utf-8')
                return hashlib.sha256(body).hexdigest()

            def seal(document, checkpoint_id):
                canonical(document)
                identifier(checkpoint_id)
                events = copy.deepcopy(document)
                return {'checkpoint_id':checkpoint_id, 'events':events, 'sha256':digest(events)}

            def restore(checkpoint):
                exact_keys(checkpoint, {'checkpoint_id','events','sha256'},
                           {'checkpoint_id','events','sha256'}, 'checkpoint')
                identifier(checkpoint['checkpoint_id'])
                events = canonical(checkpoint['events'])
                checksum = checkpoint['sha256']
                if not isinstance(checksum, str) or checksum != digest(events):
                    raise ValueError('checkpoint content digest mismatch')
                # Application replay is pure; none of its callers may alias this seed.
                return copy.deepcopy(events)

            def append(checkpoint, suffix):
                result = restore(checkpoint)
                for channel in CHANNELS:
                    result[channel].extend(copy.deepcopy(suffix[channel]))
                return canonical(result)

            def empty(opening_stock):
                result = {'build':'r31','opening_stock':copy.deepcopy(opening_stock)}
                result.update({channel:[] for channel in CHANNELS})
                return canonical(result)
        '''),
        'src/adapters.py': _text('''
            """Decode the supported current transport formats into event streams."""
            import copy
            from src.validation import CHANNELS, canonical, exact_keys, mapping, opening
            from src.streaming import reconstruct
            from src.checkpoints import append, empty

            def decode(document):
                mapping(document, 'input document')
                # A canonical document is supported for small offline reproductions.
                # Batch adapters are transport-only and never select domain revisions.
                if 'format' not in document:
                    return copy.deepcopy(canonical(document))
                if document.get('build') != 'r31':
                    raise ValueError('unsupported replay build')
                format_name = document['format']
                if format_name == 'batches-v1':
                    exact_keys(document, {'build','format','opening_stock','batches'},
                               {'build','format','opening_stock','batches'}, 'batch replay')
                    opening(document['opening_stock'])
                    result = empty(document['opening_stock'])
                    result.update(copy.deepcopy(reconstruct(document['batches'])))
                    return canonical(result)
                if format_name == 'checkpoint-v1':
                    exact_keys(document, {'build','format','checkpoint','batches'},
                               {'build','format','checkpoint','batches'}, 'checkpoint replay')
                    suffix = reconstruct(document['batches'])
                    return append(document['checkpoint'], suffix)
                raise ValueError('unsupported transport format')
        '''),
        'src/diagnostics.py': _text('''
            """Offline source-record index for incident triage, never cause inference."""
            from src.adapters import decode

            def record_index(document):
                streams = decode(document)
                index = {}
                for channel in ('inventory_events','checkout_events','refund_events'):
                    for position, row in enumerate(streams[channel]):
                        entry = {'channel':channel, 'position':position,
                                 'tenant':row['tenant'].strip(), 'order_id':row['order_id'].strip()}
                        index.setdefault(row['event_id'].strip(), []).append(entry)
                return index

            def order_sources(document, tenant, order_id):
                result = []
                for event_id, positions in record_index(document).items():
                    for position in positions:
                        if (position['tenant'], position['order_id']) == (tenant, order_id):
                            result.append(dict(position, event_id=event_id))
                return sorted(result, key=lambda row:(row['channel'],row['position'],row['event_id']))
        '''),
    })
    files['src/pipeline.py'] = files['src/pipeline.py'].replace(
        'from src.common.records import require_build', 'from src.common.records import require_build\nfrom src.adapters import decode').replace(
        '    require_build(document)', '    document = decode(document)\n    require_build(document)')
    return files


def _stock(warehouse='north', tenant='shop', qty=8):
    return dict(tenant=tenant, warehouse=warehouse, sku='BOOK', qty=qty)


def _inv(eid, warehouse='north', operation='op-41', action='reserve', qty=2, tenant='shop', order='O-17'):
    return dict(event_id=eid, tenant=tenant, warehouse=warehouse, operation_id=operation,
                order_id=order, sku='BOOK', action=action, qty=qty)


def _order(eid, revision=10, status='paid', delivered='2026-10-08T09:00:00Z',
           tenant='shop', order='O-17', captured=1000, lines=None):
    return dict(event_id=eid, tenant=tenant, order_id=order, revision=revision, status=status,
                delivered_at=delivered, captured_minor=captured,
                lines=lines if lines is not None else [dict(warehouse='north', sku='BOOK', qty=2)])


def _refund(eid, rid='R-17', attempt='delivery-a', amount=400, tenant='shop', order='O-17', provider='atlas'):
    return dict(event_id=eid, tenant=tenant, order_id=order, refund_id=rid,
                attempt_id=attempt, provider=provider, amount_minor=amount, status='succeeded')


def _doc(stock=None, inv=None, orders=None, refunds=None):
    return dict(build='r31', opening_stock=stock or [], inventory_events=inv or [],
                checkout_events=orders or [], refund_events=refunds or [])


def _batch_document(document):
    batches = []
    for channel in ('inventory_events','checkout_events','refund_events'):
        for ordinal, row in enumerate(document[channel]):
            batches.append(dict(batch_id=channel+'-'+str(ordinal), channel=channel,
                ordinal=ordinal, delivered_at='2026-10-08T09:10:00Z', records=[row]))
    # Actual transport order differs from source batch order.
    return dict(build='r31',format='batches-v1',opening_stock=document['opening_stock'],
                batches=list(reversed(batches)))


def _checkpoint_document(document):
    seed = _doc(document['opening_stock'])
    suffix = _doc()
    for channel in ('inventory_events','checkout_events','refund_events'):
        seed[channel] = document[channel][:1]
        suffix[channel] = document[channel][1:]
    encoded = json.dumps(seed,sort_keys=True,separators=(',', ':'),ensure_ascii=False).encode('utf-8')
    checkpoint = dict(checkpoint_id='CP-31',events=seed,sha256=hashlib.sha256(encoded).hexdigest())
    return dict(build='r31',format='checkpoint-v1',checkpoint=checkpoint,
                batches=_batch_document(suffix)['batches'])


def _current_documents():
    inventory = _doc([_stock(), _stock('south')],
        [_inv('INV-301'), _inv('INV-302', 'south'), _inv('INV-303')],
        [_order('ORD-301', lines=[dict(warehouse=w, sku='BOOK', qty=2) for w in ('north','south')])])
    checkout = _doc([_stock()], [_inv('INV-310')],
        [_order('ORD-310'), _order('ORD-311', 2, 'pending', '2026-10-08T09:05:00Z')])
    refunds = _doc([_stock()], [_inv('INV-320')], [_order('ORD-320')],
        [_refund('REF-321'), _refund('REF-322', attempt='delivery-b'),
         _refund('REF-323', rid='R-18', attempt='delivery-c', amount=500)])
    combined = _doc(inventory['opening_stock'], inventory['inventory_events'],
        [inventory['checkout_events'][0], _order('ORD-302', 2, 'pending',
            '2026-10-08T09:05:00Z', lines=[dict(warehouse=w,sku='BOOK',qty=2) for w in ('north','south')])],
        refunds['refund_events'])
    baseline = _doc([_stock()], [_inv('INV-330')], [_order('ORD-330')], [_refund('REF-330')])
    return {'inventory':_batch_document(inventory), 'checkout':_checkpoint_document(checkout),
            'refunds':_batch_document(refunds), 'combined':_checkpoint_document(combined),
            'baseline':baseline}


PUBLIC_TESTS = _text('''
    import json
    from pathlib import Path
    import unittest
    from src.pipeline import replay

    ROOT = Path(__file__).resolve().parents[1]

    def run_case(name):
        return replay(json.loads((ROOT / 'data/current' / (name + '.json')).read_text()))

    class ReplayChecks(unittest.TestCase):
        def test_warehouse_replay(self):
            view = run_case('inventory')
            self.assertEqual(view['metrics']['reserved_units'], 4)
            self.assertEqual(view['inventory']['accepted'], 2)
            self.assertEqual(view['inventory']['replayed'], 1)
            self.assertTrue(view['orders'][0]['ready'])

        def test_order_replay(self):
            view = run_case('checkout')
            self.assertEqual(view['orders'][0]['revision'], 10)
            self.assertEqual(view['orders'][0]['status'], 'paid')
            self.assertTrue(view['orders'][0]['ready'])

        def test_provider_replay(self):
            view = run_case('refunds')
            self.assertEqual(view['metrics']['refunded_minor'], 900)
            self.assertEqual(view['refunds']['replayed'], 1)
            self.assertEqual(view['refunds']['rejected'], [])
            self.assertEqual(len(view['refunds']['accepted']), 2)

        def test_joined_replay(self):
            view = run_case('combined')
            self.assertEqual(view['metrics'], {'ready_orders':1, 'reserved_units':4,
                             'refunded_minor':900, 'rejected_refunds':0})
            self.assertEqual(view['orders'][0]['net_minor'], 100)

        def test_normal_path(self):
            view = run_case('baseline')
            self.assertEqual(view['metrics'], {'ready_orders':1, 'reserved_units':2,
                             'refunded_minor':400, 'rejected_refunds':0})
            self.assertEqual(view['orders'][0]['net_minor'], 600)

    if __name__ == '__main__':
        unittest.main()
''')


TRANSPORT_CONTRACT = _text('''
    Transport formats: canonical documents above, batches-v1 (build, format,
    opening_stock, batches), or checkpoint-v1 (build, format, checkpoint, batches).
    Each batch has batch_id, channel (one of the three *_events channels), ordinal
    (nonnegative integer), delivered_at (aware time), records (list). Sort by ordinal
    within channel; ordinals start at zero and have no gaps. Same batch_id with equal
    channel/ordinal/records is transport replay regardless of arrival time; changed
    logical content is ValueError. Different IDs cannot occupy the same channel ordinal.
    Checkpoint has checkpoint_id, events (a canonical event document) and sha256 of
    UTF-8 json.dumps(events,sort_keys=True,separators=(',',':'),ensure_ascii=False).
    Verify digest before restoring; append suffix events per channel after the seed.
    Checkpoints hold original events, never precomputed projections or patched totals.
    Unknown transport format, malformed containers, gaps, inconsistent batch identity,
    and corrupted checkpoint all raise ValueError. Decode and replay never mutate inputs.
    src.diagnostics contains an optional source-event index for offline investigations.
''')

TRANSPORT_TESTS = _text('''
    class TransportChecks(unittest.TestCase):
        def test_checkpoint_and_canonical_equivalence(self):
            import copy
            from src.adapters import decode
            from src.checkpoints import seal
            baseline = json.loads((ROOT/'data/current/baseline.json').read_text())
            wrapper = dict(build='r31',format='checkpoint-v1',
                           checkpoint=seal(baseline,'test-checkpoint'),batches=[])
            original = copy.deepcopy(wrapper)
            self.assertEqual(decode(wrapper), baseline)
            self.assertEqual(replay(wrapper), replay(baseline))
            self.assertEqual(wrapper, original)
            wrapper['checkpoint']['events']['inventory_events'][0]['qty'] += 1
            with self.assertRaises(ValueError):
                replay(wrapper)

        def test_batch_order_and_identity(self):
            from src.adapters import decode
            wrapper = json.loads((ROOT/'data/current/inventory.json').read_text())
            normal = decode(wrapper)
            wrapper['batches'].reverse()
            self.assertEqual(decode(wrapper), normal)
            wrapper['batches'].append(dict(wrapper['batches'][0]))
            self.assertEqual(decode(wrapper), normal)
            wrapper['batches'][0]['ordinal'] = 9
            with self.assertRaises(ValueError):
                decode(wrapper)

        def test_source_index_survives_checkpoint(self):
            from src.diagnostics import order_sources
            wrapper = json.loads((ROOT/'data/current/combined.json').read_text())
            records = order_sources(wrapper,'shop','O-17')
            self.assertEqual(len(records),8)
            self.assertEqual({r['channel'] for r in records},
                             {'inventory_events','checkout_events','refund_events'})

''')


def _evidence():
    return {
        'README.md': _text('''
            # Fulfillment replay r31

            A deterministic in-memory projection of synthetic warehouse, checkout
            and settled refund deliveries. No database, dependency install or network.
            Start with docs/incident.md, docs/contracts.md and config/routes.json.
            Source route: src/replay.py -> src/pipeline.py -> domain projectors -> reports.
            Frozen current cases are under data/current. Historical data and notes
            remain under data/archive and docs/archive to model an operational repo.
            Public checks: python -B -m unittest discover -s tests -v.
            Replay: python -B -m src.replay data/current/combined.json.
        '''),
        'docs/contracts.md': _text('''
            # Replay contracts r31

            Input documents contain build r31, opening_stock, inventory_events,
            checkout_events, refund_events. Identifiers are nonblank stripped strings.
            Counts and monetary amounts are ordinary nonnegative integers (refund
            amounts and operation quantities positive); no unusual money precision.

            Warehouse streams are delivered in causal order per hold. A warehouse
            operation_id is unique only within tenant and warehouse. Replay deliveries
            may have different event_id; the same scoped operation and identical
            order_id/sku/action/qty is applied once. Changed payload for the same scoped
            operation raises ValueError. Opening stock is unique by tenant/warehouse/sku.
            Hold identity includes tenant, warehouse, order_id, sku. Reserve cannot
            exceed available stock; release cannot exceed that order's own hold.

            Checkout messages are full source snapshots, not transition commands.
            They have positive integer revision, status, captured_minor, lines, and
            delivered_at UTC timestamps. Source revision increases per tenant/order;
            arrival time can lag or reverse. Select the greatest source revision per
            tenant/order, regardless of input order or delivery time. Duplicate source
            revisions with the same status/capture/lines are replay; conflicting payloads
            raise ValueError. Status may become pending in a newer valid snapshot;
            do not impose an invented always-terminal rule. Multiple same-product
            lines for a warehouse require the sum of their quantities. Paid/shipped
            orders are ready iff all required warehouse holds are sufficient. Pending
            and cancelled orders are never ready, including orders with no lines.

            Settled refund streams preserve causal input order. A logical refund is
            unique by tenant/provider/refund_id; attempt_id identifies a delivery, so
            retries can have new attempts. Same logical refund with identical order_id
            and amount is replay, counted once; changes raise ValueError. Different
            providers or tenants can reuse refund IDs; order_id is part of immutable
            payload rather than identity. Replay accounting includes deliveries first
            rejected by eligibility or capture checks: do not reconsider their retries
            later. Unknown/pending orders are order_not_refundable. Paid, shipped and
            cancelled orders allow refunds up to captured_minor cumulatively; equality
            passes. Refusal reason exceeds_capture. Replays do not consume budget.

            Public API: src.pipeline.replay(document)->dict. It is pure, repeatable,
            has no global retained state, and must not mutate the input. Unsupported
            build, invalid counts, unknown stock, identity conflicts, insufficient
            stock and over-release raise ValueError; do not turn them into successes.
            Output has inventory, orders, refunds, metrics. Inventory stock sorted by
            tenant/warehouse/sku, nonzero holds sorted by tenant/warehouse/order/sku;
            accepted/replayed are delivery counts. Orders sorted by tenant/order with
            revision/status/captured_minor/ready/refunded_minor/net_minor. Refund totals
            sorted by tenant/order, accepted sorted by tenant/provider/refund_id, rejected
            in input order as event_id/reason, replayed is count. Metrics reports ready
            orders, reserved units, refunded_minor and number of rejected refunds.
        '''),
        'docs/incident.md': _text('''
            # Local incident FUL-31

            Current build: r31, captured 2026-10-08 after the multi-warehouse adapter
            and source-revision feed went live in this synthetic service. Current
            warehouse replay omits a hold; a checkout replay exposes an old pending
            state; a settled-provider retry changes refund totals. These observations
            can be reproduced separately and in the joined replay. The normal path
            remains healthy. The independent feeds share the order join; a failure
            upstream can hide an additional downstream problem.

            data/current/*.json contains authoritative input events. logs/current.jsonl
            contains stage observations and trace IDs from the deployed broken build.
            traces/r31.json links pipeline observations to event IDs. The r29 bridge
            was retired before this incident; archived configuration, logs, notes and
            src/legacy files are historical context. A prior cache fix and a prior
            provider rounding ticket may look relevant but describe a different route.
        '''),
        'config/routes.json': _json({'build':'r31','entrypoint':'src.pipeline.replay',
            'stages':['inventory','checkout','refunds','reporting'],
            'warehouse_adapter':'scoped-batch-v2','checkout_feed':'source-snapshot-v3',
            'provider_feed':'settled-deliveries-v2','external_io':False}),
        'config/providers.json': _json({'build':'r31','providers':[
            {'name':'atlas','refund_identity_contract':'tenant/provider/logical-refund'},
            {'name':'nova','refund_identity_contract':'tenant/provider/logical-refund'}]}),
        'config/warehouses.json': _json({'build':'r31','warehouses':[
            {'tenant':'shop','warehouse':'north','adapter':'scoped-batch-v2'},
            {'tenant':'shop','warehouse':'south','adapter':'scoped-batch-v2'}]}),
        'config/archive/r29.json': _json({'build':'r29','entrypoint':'legacy.poll',
            'warehouse_adapter':'single-warehouse-cache','checkout_feed':'poll-timestamp',
            'provider_feed':'decimal-file-import'}),
        'docs/archive/cache-ticket.md': _text('''
            # ARC-CACHE-29 (resolved, build r29, 2026-09-12)
            Single-warehouse polling cache evicted an event key during restart.
            The repair persisted cache keys; no current r31 projectors were deployed.
            Scope: legacy.reservation_cache; state: historical, superseded.
        '''),
        'docs/archive/provider-ticket.md': _text('''
            # ARC-MONEY-29 (resolved, build r29, 2026-09-14)
            Decimal-file imports rounded provider values. The feed was replaced by
            settled integer-minor deliveries. No current record has fractional amounts.
            This ticket does not establish the cause of FUL-31.
        '''),
        'docs/archive/order-ticket.md': _text('''
            # ARC-POLL-29 (resolved, build r29, 2026-09-15)
            Remote poll responses lacked a source revision; use latest poll time.
            The r31 full-snapshot feed now has per-order source revisions. This old
            recommendation applies only to the retired polling route.
        '''),
        'data/archive/r29_snapshot.json': _json({'build':'r29','record_id':'ARC-SNAPSHOT-29',
            'metrics':{'ready_orders':1,'reserved_units':2,'refunded_minor':400},
            'scope':'single-warehouse poll bridge; cannot override current input'}),
        'logs/archive.jsonl': _json({'record_id':'ARC-LOG-29','build':'r29',
            'message':'restart cache loss; decimal provider import; timestamp-only polls'}),
        'logs/current.jsonl': '\n'.join(json.dumps(row, sort_keys=True) for row in [
            {'record_id':'OBS-INV-31','trace_id':'TRACE-INV-31','build':'r31','case':'inventory',
             'stage':'inventory','accepted':1,'replayed':2,'reserved_units':2,
             'event_ids':['INV-301','INV-302','INV-303']},
            {'record_id':'OBS-ORD-31','trace_id':'TRACE-ORD-31','build':'r31','case':'checkout',
             'stage':'checkout','revision':2,'status':'pending','ready':False,
             'event_ids':['ORD-310','ORD-311']},
            {'record_id':'OBS-REF-31','trace_id':'TRACE-REF-31','build':'r31','case':'refunds',
             'stage':'refunds','refunded_minor':800,'replayed':0,
             'rejected':[{'event_id':'REF-323','reason':'exceeds_capture'}],
             'event_ids':['REF-321','REF-322','REF-323']},
            {'record_id':'OBS-JOIN-31','trace_id':'TRACE-JOIN-31','build':'r31','case':'combined',
             'stage':'reporting','ready_orders':0,'reserved_units':2,'refunded_minor':0,
             'rejected_refunds':3}])+'\n',
        'traces/r31.json': _json({'build':'r31','traces':[
            {'trace_id':'TRACE-INV-31','upstream_events':['INV-301','INV-302','INV-303'],
             'observation':'OBS-INV-31','join':'shop/O-17'},
            {'trace_id':'TRACE-ORD-31','upstream_events':['ORD-310','ORD-311'],
             'observation':'OBS-ORD-31','join':'shop/O-17'},
            {'trace_id':'TRACE-REF-31','upstream_events':['REF-321','REF-322','REF-323'],
             'observation':'OBS-REF-31','join':'shop/O-17'},
            {'trace_id':'TRACE-JOIN-31','upstream_events':['ORD-301','ORD-302','REF-321','REF-322'],
             'observation':'OBS-JOIN-31','join':'shop/O-17'}]}),
    }


def cases():
    files = _modules()
    files.update(_evidence())
    files['docs/contracts.md'] += TRANSPORT_CONTRACT
    files['docs/incident.md'] += '\nCombined/checkout rebuild checkpoint plus streamed suffix; inventory/refunds decode ordered batches. Domain identities survive every transport format.\n'
    files.update({'data/current/'+name+'.json':_json(doc) for name,doc in _current_documents().items()})
    files.update({'tests/test_replays.py':PUBLIC_TESTS.replace("if __name__ == '__main__':\n    unittest.main()\n",'') + TRANSPORT_TESTS + "\nif __name__ == '__main__':\n    unittest.main()\n",
                  'STATE.md':'# State\n\nDiagnosis and repair pending.\n',
                  'diagnosis.json':'{}\n'})
    return {'fulfillment_replay':dict(task=TASK, files=files,
        mutable=['src/**/*.py','diagnosis.json','STATE.md'], min_workers_c=2,
        groups=dict(GROUPS), metadata={'file_count':len(files)+1,
            'source_file_count':sum(name.startswith('src/') for name in files),
            'source_line_count':sum(body.count('\n') for name,body in files.items() if name.startswith('src/')),
            'task_scale':'medium synthetic connected repository',
            'planted_root_defects':3, 'diagnosis_scoring':'structural provenance; prose truth requires independent review'},
        expected={'rubric_version':'fulfillment-r31-v1'})}


def reference_patches():
    """Host-side acceptance only. Never copy this function/content to model tasks."""
    files = _modules()
    return {
        'src/inventory/registry.py': files['src/inventory/registry.py'].replace(
            "identity = row['operation_id']", "identity = row['tenant'], row['warehouse'], row['operation_id']"),
        'src/checkout/revisions.py': files['src/checkout/revisions.py'].replace(
            "row['delivered_at'] > old['delivered_at']", "row['revision'] > old['revision']"),
        'src/refunds/ledger.py': files['src/refunds/ledger.py'].replace(
            "row['tenant'], row['provider'], row['attempt_id']", "row['tenant'], row['provider'], row['refund_id']"),
    }


def reference_diagnosis():
    return {'defects':[
        {'source_files':['src/inventory/registry.py'],
         'evidence_ids':['INV-301','INV-302','TRACE-INV-31'],
         'mechanism':'Dedup identity uses only operation_id; tenant and warehouse scope must be included.',
         'impact':'Second warehouse hold is suppressed, so split checkout is not ready.',
         'stale_evidence_ids':['ARC-CACHE-29']},
        {'source_files':['src/checkout/revisions.py'],
         'evidence_ids':['ORD-310','ORD-311','TRACE-ORD-31'],
         'mechanism':'Arrival delivered_at is used instead of greatest numeric source revision.',
         'impact':'Late pending snapshot overrides paid; readiness and refund eligibility fail.',
         'stale_evidence_ids':['ARC-POLL-29']},
        {'source_files':['src/refunds/ledger.py'],
         'evidence_ids':['REF-321','REF-322','REF-323','TRACE-REF-31'],
         'mechanism':'Idempotency key uses attempt_id rather than tenant/provider/refund_id logical identity.',
         'impact':'Retry consumes capture budget twice and rejects a separate refund.',
         'stale_evidence_ids':['ARC-MONEY-29']}],
        'verification':{'commands':[],'observed_results':[]},
        'remaining_limits':['Synthetic local reference; no production evidence']}


def materialize(target, slug='fulfillment_replay', *, reference=False):
    """Write an isolated fixture. reference=True is acceptance-only, never live."""
    target = Path(target)
    if target.exists() and any(target.iterdir()):
        raise ValueError('fixture destination must be empty')
    case = cases()[slug]
    contents = dict(case['files'])
    contents['TASK.md'] = case['task']
    if reference:
        contents.update(reference_patches())
    for relative, content in contents.items():
        path = target/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    protected = sorted(name for name in contents if not name.startswith('src/')
                       and name not in ('STATE.md','diagnosis.json'))
    return {'slug':slug, 'protected_paths':protected,
            'mutable':case['mutable'], 'groups':case['groups'], 'file_count':len(contents)}


# This code executes outside the task tree. It contains unseen variations and
# independent expected values, never the reference patches or diagnosis answers.
HIDDEN_SCRIPT = _text(r'''
    import copy
    import json
    import sys
    sys.path.insert(0, sys.argv[1])
    from src.pipeline import replay

    def stock(w='w1', t='alpha', q=12):
        return dict(tenant=t, warehouse=w, sku='PART', qty=q)

    def inv(e, w='w1', t='alpha', op='operation', o='order', q=3, action='reserve'):
        return dict(event_id=e, tenant=t, warehouse=w, operation_id=op, order_id=o,
                    sku='PART', qty=q, action=action)

    def order(e, rev=7, status='paid', when='2026-10-08T08:00:00Z', t='alpha',
              o='order', amount=1200, lines=None):
        return dict(event_id=e, tenant=t, order_id=o, revision=rev, status=status,
                    delivered_at=when, captured_minor=amount,
                    lines=lines if lines is not None else [dict(warehouse='w1',sku='PART',qty=3)])

    def refund(e, rid='refund', attempt='a', q=350, t='alpha', o='order', provider='one'):
        return dict(event_id=e, tenant=t, order_id=o, refund_id=rid, attempt_id=attempt,
                    provider=provider, amount_minor=q, status='succeeded')

    def doc(s=None, i=None, o=None, r=None):
        return dict(build='r31', opening_stock=s or [], inventory_events=i or [],
                    checkout_events=o or [], refund_events=r or [])

    def raises(document):
        try:
            replay(document)
        except ValueError:
            return
        raise AssertionError('expected ValueError')

    def inventory():
        s = [stock('w1'), stock('w2'), stock('w1','beta')]
        i = [inv('v1'), inv('v2','w2'), inv('v3',t='beta'), inv('v4'),
             inv('v5',op='release',q=1,action='release'),
             inv('v6',op='release',q=1,action='release')]
        out = replay(doc(s,i))['inventory']
        assert out['accepted'] == 4 and out['replayed'] == 2
        assert [r['reserved'] for r in out['stock']] == [2,3,3]
        assert [r['available'] for r in out['stock']] == [10,9,9]
        assert [r['qty'] for r in out['holds']] == [2,3,3]
        # Same scoped operation with changed payload remains a conflict.
        raises(doc([stock()],[inv('c1'),inv('c2',q=2)]))
        # Scope normalization precedes dedup; duplicated reserve is not added twice.
        out = replay(doc([stock()],[inv('trim',t=' alpha ',w=' w1 ',op=' operation '),inv('normal')]))
        assert out['inventory']['accepted'] == 1 and out['inventory']['replayed'] == 1

    def checkout():
        s, i = [stock()], [inv('hold')]
        rows = [order('new',rev=12), order('old',rev=3,status='pending',when='2026-10-08T12:00:00Z'),
                order('retry',rev=12,when='2026-10-08T07:00:00Z')]
        for variant in (rows, list(reversed(rows)), [rows[1],rows[0],rows[2]]):
            result = replay(doc(s,i,variant))['orders'][0]
            assert result['revision'] == 12 and result['status'] == 'paid' and result['ready'] is True
        # A newer pending snapshot is legal; hard-coded monotone status is wrong.
        rows = [order('paid',rev=7),order('pending',rev=14,status='pending',when='2026-10-08T07:00:00Z')]
        result = replay(doc(s,i,rows))['orders'][0]
        assert result['revision'] == 14 and result['status'] == 'pending' and result['ready'] is False
        # Tenant/order scope and equal timestamp revisions.
        rows = [order('a',rev=4),order('b',rev=8,t='beta',status='cancelled'),
                order('c',rev=19),order('d',rev=2,t='beta')]
        out = replay(doc(s,i,rows))['orders']
        assert [r['revision'] for r in out] == [19,8]
        assert [r['status'] for r in out] == ['paid','cancelled']
        raises(doc(s,i,[order('x'),order('y',status='shipped')]))

    def refunds():
        s,i,o = [stock()], [inv('hold')], [order('order')]
        r = [refund('r1'),refund('r2',attempt='b'),refund('r3',rid='second',attempt='c',q=850)]
        out = replay(doc(s,i,o,r))['refunds']
        assert out['totals'][0]['refunded_minor'] == 1200
        assert len(out['accepted']) == 2 and out['replayed'] == 1 and out['rejected'] == []
        # Logical IDs can repeat across provider/tenant; attempt IDs are delivery metadata.
        o = [order('oa',amount=1500),order('ob',t='beta',amount=800)]
        r = [refund('a'),refund('b',provider='two'),refund('c',t='beta'),
             refund('d',rid='independent',q=250),refund('e',attempt='other')]
        out = replay(doc(s,i,o,r))['refunds']
        assert [row['refunded_minor'] for row in out['totals']] == [950,350]
        assert len(out['accepted']) == 4 and out['replayed'] == 1
        raises(doc(s,i,o,[refund('x'),refund('y',attempt='new',q=351)]))
        raises(doc(s,i,o,[refund('x'),refund('y',attempt='new',o='other')]))
        # Refused deliveries also have logical replay accounting.
        out = replay(doc(s,i,[order('pending',status='pending')],
                         [refund('p1'),refund('p2',attempt='new')]))['refunds']
        assert out['rejected'] == [{'event_id':'p1','reason':'order_not_refundable'}]
        assert out['replayed'] == 1 and out['totals'] == []

        o = [order('budget-order')]
        out = replay(doc(s,i,o,[refund('huge',q=1201),refund('retry',attempt='new',q=1201),
                                refund('okay',rid='other',attempt='next',q=1200)]))
        assert out['refunds']['rejected'] == [{'event_id':'huge','reason':'exceeds_capture'}]
        assert out['refunds']['replayed'] == 1 and out['metrics']['refunded_minor'] == 1200

    def integration():
        s = [stock('w2',q=9),stock('w1',q=10)]
        i = [inv('n',q=2),inv('s',w='w2',q=2),inv('retry',q=2)]
        lines = [dict(warehouse=w,sku='PART',qty=2) for w in ('w1','w2')]
        o = [order('paid',rev=20,amount=800,lines=lines),
             order('pending',rev=5,status='pending',when='2026-10-08T11:00:00Z',amount=800,lines=lines)]
        r = [refund('settled',q=300),refund('repeat',attempt='retry',q=300),
             refund('second',rid='balance',attempt='later',q=500)]
        out = replay(doc(s,i,o,r))
        assert out['metrics'] == dict(ready_orders=1,reserved_units=4,refunded_minor=800,rejected_refunds=0)
        assert out['orders'] == [dict(tenant='alpha',order_id='order',revision=20,status='paid',
                                     captured_minor=800,ready=True,refunded_minor=800,net_minor=0)]
        # Fully repaired results must remain identical with order deliveries reversed.
        assert replay(doc(s,i,list(reversed(o)),r)) == out
        # Insufficient split hold keeps readiness false without prohibiting settled refunds.
        out = replay(doc(s,i[:1],o,r))
        assert out['orders'][0]['ready'] is False and out['metrics']['refunded_minor'] == 800

    def unaffected():
        s,i,o = [stock()], [inv('hold')], [order('paid')]
        base = doc(s,i,o,[refund('settled')])
        snapshot = copy.deepcopy(base)
        first = replay(base)
        assert base == snapshot and replay(base) == first
        assert first['metrics'] == dict(ready_orders=1,reserved_units=3,refunded_minor=350,rejected_refunds=0)
        assert replay(doc()) == dict(inventory=dict(stock=[],holds=[],accepted=0,replayed=0),
                                    orders=[],refunds=dict(totals=[],accepted=[],rejected=[],replayed=0),
                                    metrics=dict(ready_orders=0,reserved_units=0,refunded_minor=0,rejected_refunds=0))
        bad = copy.deepcopy(base); bad['build']='r29'; raises(bad)
        raises(doc([stock()],[inv('over',q=13)]))
        raises(doc([stock()],[inv('release',action='release',q=1)]))
        raises(doc([stock()],[inv('bad',q=True)]))
        raises(doc([stock()],[inv('unknown',w='unknown')]))
        raises(doc([stock(),stock()],[]))
        # Multiple lines aggregate; no empty-line pending order readiness.
        lines = [dict(warehouse='w1',sku='PART',qty=2),dict(warehouse='w1',sku='PART',qty=2)]
        out = replay(doc(s,i,[order('lines',lines=lines)]))
        assert out['orders'][0]['ready'] is False
        out = replay(doc([],[],[order('empty',status='pending',lines=[])]))
        assert out['orders'][0]['ready'] is False
        out = replay(doc(s,i,[],[refund('unknown-order')]))
        assert out['refunds']['rejected'][0]['reason'] == 'order_not_refundable'
        # Hidden wrapper variants preserve semantics and exercise boundary rejection.
        from src.checkpoints import seal
        from src.adapters import decode
        from src.diagnostics import record_index
        checkpoint = seal(base, 'hidden-checkpoint')
        wrapped = dict(build='r31', format='checkpoint-v1', checkpoint=checkpoint, batches=[])
        pristine = copy.deepcopy(wrapped)
        assert replay(wrapped) == first and wrapped == pristine
        assert len(record_index(wrapped)) == 3
        damaged = copy.deepcopy(wrapped)
        damaged['checkpoint']['events']['refund_events'][0]['amount_minor'] += 1
        raises(damaged)
        batches = []
        for channel in ('inventory_events','checkout_events','refund_events'):
            batches.append(dict(batch_id=channel, channel=channel, ordinal=0,
                                delivered_at='2026-10-08T05:00:00Z', records=base[channel]))
        wrapper = dict(build='r31',format='batches-v1',opening_stock=base['opening_stock'],
                       batches=list(reversed(batches)))
        assert replay(wrapper) == first
        # Transport duplicate is ignored before domain-level delivery accounting.
        repeated = copy.deepcopy(wrapper['batches'][0])
        repeated['delivered_at'] = '2026-10-08T13:00:00Z'
        wrapper['batches'].append(repeated)
        assert replay(wrapper) == first
        bad = copy.deepcopy(wrapper)
        bad['batches'][0]['records'][0]['amount_minor'] += 1
        raises(bad)
        gap = copy.deepcopy(wrapper)
        gap['batches'][1]['ordinal'] = 2
        raises(gap)
        unknown = copy.deepcopy(wrapper); unknown['format'] = 'unknown'; raises(unknown)
        invalid = copy.deepcopy(base); invalid['inventory_events'] = {}; raises(invalid)

    results, errors = {}, {}
    for name in ('inventory','checkout','refunds','integration','unaffected'):
        try:
            globals()[name]()
            results[name] = True
        except Exception as exc:
            results[name] = False
            errors[name] = type(exc).__name__ + ': ' + str(exc)
    print(json.dumps({'groups':results,'errors':errors},sort_keys=True))
''')


def _diagnosis_groups(root):
    """Structural causal provenance only; independent review must assess prose truth."""
    groups = {name:False for name in GROUPS if name.startswith('diagnosis_')}
    details = {}
    try:
        diagnosis = json.loads((root/'diagnosis.json').read_text(encoding='utf-8'))
        defects = diagnosis['defects']
        if not isinstance(defects,list) or len(defects) != 3:
            raise ValueError('exactly three defects required')
        if set(diagnosis) != {'defects','verification','remaining_limits'}:
            raise ValueError('diagnosis top-level schema differs')
        if not isinstance(diagnosis['remaining_limits'],list):
            raise ValueError('remaining_limits list required')
        verification = diagnosis['verification']
        if not isinstance(verification,dict) or not all(isinstance(verification.get(k),list)
                for k in ('commands','observed_results')):
            raise ValueError('verification lists required')
        specs = {
            'inventory':('src/inventory/registry.py', {'INV-301','INV-302'},
                         {'TRACE-INV-31','OBS-INV-31'}, 'ARC-CACHE-29',
                         [('operation','dedup','identity','key'),('warehouse',),('tenant',)],
                         [('hold','reserv','stock'),('ready','checkout','fulfill')]),
            'checkout':('src/checkout/revisions.py', {'ORD-310','ORD-311'},
                        {'TRACE-ORD-31','OBS-ORD-31'}, 'ARC-POLL-29',
                        [('revision',),('arrival','deliver','timestamp','time'),
                         ('source','numeric','greatest','highest','max')],
                        [('pending','paid','state','status'),('refund','eligib','ready')]),
            'refunds':('src/refunds/ledger.py', {'REF-321','REF-322','REF-323'},
                       {'TRACE-REF-31','OBS-REF-31'}, 'ARC-MONEY-29',
                       [('attempt','delivery'),('refund_id','refund id','logical'),
                        ('identity','key','dedup','idemp')],
                       [('retry','duplicate','twice','double'),('budget','capture','reject')]),
        }
        for name,(source,events,traces,stale,mechanism_terms,impact_terms) in specs.items():
            matches = [d for d in defects if isinstance(d,dict) and source in d.get('source_files',[])]
            if len(matches) != 1:
                details[name] = 'one distinct causal source entry required'
                continue
            defect = matches[0]
            valid = set(defect) == {'source_files','evidence_ids','mechanism','impact','stale_evidence_ids'}
            for key in ('source_files','evidence_ids','stale_evidence_ids'):
                valid = valid and isinstance(defect.get(key),list) and all(
                    isinstance(v,str) for v in defect.get(key,[]))
            valid = valid and source in defect.get('source_files',[]) and all(
                path in _modules() and (root/path).is_file()
                for path in defect.get('source_files',[]))
            ids = set(defect.get('evidence_ids',[]))
            valid = valid and events <= ids and bool(traces & ids)
            valid = valid and stale in defect.get('stale_evidence_ids',[])
            mechanism, impact = defect.get('mechanism',''), defect.get('impact','')
            valid = valid and isinstance(mechanism,str) and isinstance(impact,str)
            valid = valid and bool(mechanism.strip()) and bool(impact.strip())
            groups['diagnosis_'+name] = bool(valid)
            if not valid:
                details[name] = 'missing causal evidence, invariant, impact or historical exclusion'
    except (OSError,ValueError,TypeError,KeyError) as exc:
        details['schema_error'] = str(exc)
    return groups,details


def evaluate(target, slug='fulfillment_replay', *, managed_paths=()):
    """Score hidden behavior and evidence; protected-file violations invalidate all.

    -I ignores environment import settings; -B keeps the fixture immutable. The
    evaluator body and expected values never reside in the model workspace.
    """
    root = Path(target).resolve()
    case = cases()[slug]
    expected = dict(case['files'], **{'TASK.md':case['task']})
    managed_paths = set(managed_paths)
    if any(name.startswith('/') or '..' in Path(name).parts for name in managed_paths):
        raise ValueError('managed paths must be explicit relative paths')
    violations = []
    for name,content in expected.items():
        path = root/name
        if path.is_symlink() or not path.is_file():
            violations.append(name+': missing or nonregular')
        elif not name.startswith('src/') and name not in ('STATE.md','diagnosis.json'):
            if path.read_bytes() != content.encode('utf-8'):
                violations.append(name+': protected content changed')
    for path in root.rglob('*'):
        if path.is_symlink():
            violations.append(str(path.relative_to(root))+': symlink')
        elif path.is_file() and path.relative_to(root).as_posix() not in expected and path.relative_to(root).as_posix() not in managed_paths:
            violations.append(str(path.relative_to(root))+': unexpected file')
    groups = {key:False for key in GROUPS}
    details = {'protected_violations':violations}
    if not violations:
        try:
            run = subprocess.run([sys.executable,'-I','-B','-c',HIDDEN_SCRIPT,str(root)],
                                 capture_output=True,text=True,timeout=30)
            details['behavior_exit_code'] = run.returncode
            if run.returncode == 0:
                report = json.loads(run.stdout)
                groups.update({key:report['groups'].get(key) is True
                               for key in ('inventory','checkout','refunds','integration','unaffected')})
                details['behavior_errors'] = report.get('errors',{})
            else:
                details['behavior_error'] = run.stderr[-2000:]
        except (OSError,subprocess.TimeoutExpired) as exc:
            details['behavior_error'] = str(exc)
            return {'score':None,'groups':{},'details':details}
        except ValueError as exc:
            details['behavior_error'] = str(exc)
            return {'score':None,'groups':{},'details':details}
        diagnosis,diagnostic_details = _diagnosis_groups(root)
        groups.update(diagnosis)
        details['diagnosis'] = diagnostic_details
        try:
            state = (root/'STATE.md').read_text(encoding='utf-8').lower()
            document = json.loads((root/'diagnosis.json').read_text(encoding='utf-8'))
            verification = document['verification']
            changed_sources = [name for name in expected if name.startswith('src/')
                               and (root/name).read_bytes() != expected[name].encode('utf-8')]
            details['changed_source_files'] = changed_sources
            groups['state'] = (all(groups[k] for k in groups if k.startswith('diagnosis_'))
                and bool(verification['commands']) and bool(verification['observed_results'])
                and ('unittest' in state or 'replay' in state)
                and any(word in state for word in ('pass','fail','observed','result'))
                and any(word in state for word in ('limit','synthetic','production'))
                and any(word in state for word in ('next','follow-up'))
)
        except (OSError,ValueError,TypeError,KeyError):
            pass
    return {'score':sum(GROUPS[key] for key,passed in groups.items() if passed),
            'groups':groups,'details':details}

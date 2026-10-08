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

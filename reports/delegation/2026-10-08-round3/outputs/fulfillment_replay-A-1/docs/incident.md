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

Combined/checkout rebuild checkpoint plus streamed suffix; inventory/refunds decode ordered batches. Domain identities survive every transport format.

# Diagnose

Start with the symptom and scope: what failed, since when, what still works, which
users/data/operations may be affected. Read permitted minimized logs and recent
changes; do not export secrets, customer records or provider credentials. Separate
observed facts, hypotheses and unknowns. Reproduce safely rather than experimenting
on production. Respect check-only; diagnose is not permission to patch or restart.

Before retrying an external operation distinguish failed from unknown. Check provider
receipts/idempotency state; a timeout may have completed a send. Do not blindly repeat
messages, payments or destructive jobs. Preserve useful failure evidence and current
state before any approved fix. Do not kill an unknown process merely because of a port.

Deliver probable cause with evidence, affected scope, data integrity status (or unknown),
manual fallback and a bounded repair/recovery recommendation. Stop for appropriate
specialist help when the risk exceeds available competence or authority. Repeated
nonprogress is an environment/assumption signal, not a reason for unlimited retries.

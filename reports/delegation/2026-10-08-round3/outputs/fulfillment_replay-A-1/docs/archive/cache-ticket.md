# ARC-CACHE-29 (resolved, build r29, 2026-09-12)
Single-warehouse polling cache evicted an event key during restart.
The repair persisted cache keys; no current r31 projectors were deployed.
Scope: legacy.reservation_cache; state: historical, superseded.

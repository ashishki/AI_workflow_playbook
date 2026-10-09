# Fulfillment replay r31

A deterministic in-memory projection of synthetic warehouse, checkout
and settled refund deliveries. No database, dependency install or network.
Start with docs/incident.md, docs/contracts.md and config/routes.json.
Source route: src/replay.py -> src/pipeline.py -> domain projectors -> reports.
Frozen current cases are under data/current. Historical data and notes
remain under data/archive and docs/archive to model an operational repo.
Public checks: python -B -m unittest discover -s tests -v.
Replay: python -B -m src.replay data/current/combined.json.

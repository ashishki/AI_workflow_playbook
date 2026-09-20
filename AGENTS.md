# Working in this repository

This is one Playbook with two user entrypoints, not two permanent Git branches.
- Engineering use (new/existing real projects and experiments): `engineering/README.md`.
- Product work (a process owner's full solution lifecycle): `product/README.md`.
- Shared implementations and ownership: `shared/README.md` and `shared/ownership.json`.
- Current migration/evidence/next work: `docs/vnext/STATUS.md`.

Read only the relevant route. Existing Governed downstream contracts remain
binding; Product is not a downgrade. Product work follows
`docs/native/DEVELOPMENT_RU.md`; do not import the full Governed ritual merely
because its source is in this repo. Preserve source paths, frozen evidence and
unrelated changes. No main/master writes, rollout, account use, paid trials or
external sends without applicable authority. A request to improve documentation
is not approval of new permissions. Do not invent reviewer or pilot results.

Relevant offline checks: `python -m unittest discover -s tests/vnext -v`,
`python tools/vnext_check.py --root .`, plus the existing affected Native/package
or Governed tests. Use `distribution/native/sync_runtime.py --check` for bundled
copies. Check explicit evidence, not test-count growth. No recursive reviewer.

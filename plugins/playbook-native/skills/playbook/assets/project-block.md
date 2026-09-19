<!-- playbook-native:begin v0.1.0-preview.4 -->
## Playbook Native

- Deliver the requested outcome using this repository's conventions and tools.
  Inspect relevant code and checks first. Keep small tasks small; use a short
  plan for multi-step work, and save it only when it helps continuation.
- Continue through implementation, verification, and fixes within the authorized
  scope. Ask when missing intent changes the result or when new authority is
  needed; do not add approvals for routine reversible work.
- Use relevant installed skills. For rendered UI changes, use
  `playbook-frontend` when available. Run the app, exercise the changed user
  flow, and inspect current screenshots before calling the UI verified.
- Run meaningful existing checks; add regression coverage when the changed
  behavior warrants it. Inspect the diff. Do not weaken tests or regenerate
  visual baselines just to obtain a pass.
- Report what changed, what actually ran and passed/failed, and what remains
  unverified, with useful evidence links. Missing tools/access mean an explicit
  limitation. A self-check is not independent review.
- Preserve unrelated work and existing project policies. Do not expand access,
  publish, deploy, spend money, or mutate production without authorization.
  Stop repeating an unchanged failing approach; diagnose or report the blocker.
<!-- playbook-native:end -->

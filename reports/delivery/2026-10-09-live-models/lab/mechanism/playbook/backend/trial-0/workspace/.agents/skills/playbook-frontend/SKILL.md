---
name: playbook-frontend
description: Implement or fix rendered web UI and verify the changed user journey in the running application. Use for pages, components, forms, responsive layouts, and UI interactions; not for backend-only changes, prose, or research without implementation.
---

Deliver a working, visually inspected user journey. Adapt the depth to the
change; a small CSS repair does not need a design phase. Respect the project's
existing release, accessibility, and review requirements.

## Establish the intended result

Read the relevant screen, components, styles, and tests. Use the existing stack,
tokens, and design system. Identify what a person needs to do and what should
happen. For a new screen, state a brief visual direction and key states in the
conversation, then build. Ask only if an unresolved choice would materially
change the product; use a sensible stated assumption for ordinary details.

Use supplied designs and real content where available. Distinguish a marketing
page from a working application. Do not add decorative effects, dependencies,
or a different framework merely to make the result look more elaborate.
If a specialist design or framework skill is already available and appropriate,
use it selectively rather than reproducing its full guidance here.

## Implement and check

Use the project's run and verification commands. For behavior changes, choose
regression coverage that exercises the actual failure or acceptance criterion.
Reuse the existing test runner; do not introduce a new framework for a trivial
change. A build passing does not prove that the user flow works.

Follow [browser verification](references/browser-check.md) when starting the
app and testing the change. The browser interface may be native, CLI, or MCP;
choose an available capability that can reach this app. Use one interface
unless a specific missing diagnostic justifies another.

Exercise the changed flow, its relevant failure state, and the layouts affected
by the change. Inspect fresh screenshots at the relevant wide and narrow
viewports for a responsive web UI; for a fixed-size surface, use its supported
size. Look for overflow, clipping, hierarchy, text legibility, focus visibility,
and overlap. Check keyboard operation and labels for changed controls. Use
automated accessibility checks if available, without calling them a complete
accessibility audit.

Fix observed issues and recheck the affected flow and relevant project checks.
If two attempts make no progress on the same blocker, diagnose the environment
or ask for the specific missing input. This is a prompt heuristic, not an
enforced retry budget. Do not cycle indefinitely or broaden the task silently.

## Present the result

Give a short outcome, actual check results, the preview or useful screenshot
links, and any remaining limitation. Include the checked route/state and
viewport when they clarify coverage. Distinguish test success, observed browser
behavior, visual inspection, and unverified areas. Do not say "verified" when
the browser never opened, screenshots were not inspected, or data was mocked
where the acceptance criterion requires the real integration.

The user sees the working result and meaningful tradeoffs, not a packet of
process forms. Follow an existing visual-baseline policy; do not invent a new
approval cycle for an ordinary change. New golden baselines are candidates
for review, never evidence of their own correctness. If external publishing
or production actions are needed, finish the locally reviewable work first.

# AI Workflow Playbook

An AI-assisted delivery playbook for developers and workflow owners: understand
the problem, choose a focused change, implement it, verify the result, and
maintain or hand it over.

One Playbook has two entry paths and shared engineering mechanisms:

| Entry | Who it serves |
|---|---|
| [Engineering](engineering/README.md) | Developers working on new or existing projects, independent reviews, and experiments |
| [Product](product/README.md) | Workflow owners who need to understand a problem, choose a change, observe its effect, and maintain or hand over the result |

## Representative use

A workflow owner describes recurring work and where it goes wrong. The Product
path helps clarify the problem and choose an appropriate intervention: a process
change, configuration, spreadsheet, or software. The owner decides about their
work, data, expenses, and consequences; engineering checks support those decisions.

The Engineering path is the author's working method for implementation,
verification, review, and handoff. Existing projects retain their pinned version
and contract; trying a new method does not migrate them automatically.

## Current stage

**24 October 2026: public reference material; Product/Desktop tools remain a
private evaluation preview (`0.2.0-preview.4`).**
[Desktop delivery status](docs/delivery/DESKTOP_SETUP_PREVIEW_RU.md) ·
[Delivery programme](docs/delivery/PLAN_RU.md).

Installation checks, frozen self-tests, and CI do not establish clean-machine
operation, user benefit, or business impact. The
[historical results](reports/native/README.md) retain the trial that did not
establish an advantage over ordinary Codex. Packaging and the complete user
journey require separate evidence.

## What is available

- Engineering routes for continuing a project, starting one, or testing a method.
- A Product workflow spanning problem framing through maintenance and handoff.
- The canonical Native kit, with a conversational entry, frontend, all 13 lifecycle
  stages, the existing Role Runner, and an optional state/handoff tool.
- OS-specific Playbook Desktop setup for installing, updating, removing, and
  restoring a prior installation of managed Playbook files.

Desktop setup connects the Native kit to a chosen working folder. Preparing a
per-user independent-review runtime requires its own confirmation. Git, GitHub,
a VPS, Docker, API keys, and system Python are not universal requirements for
the first Product discussion.

## Start and inspect

- **Engineering:** [usage guide (Russian)](engineering/USAGE_RU.md).
- **Product private preview:** [first-run guide (Russian)](docs/native/QUICKSTART_RU.md).
- **Manual portable path:** [Native ZIP kit](distribution/native/README.md).
- **Desktop:** [setup preview](distribution/desktop/README.md).
- [Capability catalogue](product/CAPABILITIES.md),
  [architecture](docs/vnext/ARCHITECTURE_RU.md),
  [shared mechanisms](shared/README.md), and [documentation index](docs/README.md).

The `playbook-native` plugin retains its compatible route. A small request uses
the relevant parts of the library; it does not require every stage or skill.

## Rights and distribution

This repository has no project-level open-source license and grants
no additional copyright permission beyond the GitHub Terms, applicable law, and
file-specific licenses. See [Legal Status](docs/LEGAL_STATUS.md).
Public source visibility does not turn the private preview into a public product
release or authorize distribution of the package.

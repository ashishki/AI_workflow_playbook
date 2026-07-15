from __future__ import annotations

import runpy
from pathlib import Path

import pytest


def test_guard_accepts_approved_workflow_and_rejects_every_unapproved_reference() -> None:
    namespace = runpy.run_path("tests/test_ci_supply_chain.py")
    assert_approved = namespace.get("assert_approved_action_references")
    assert callable(assert_approved), "extract a reusable all-uses allowlist guard"

    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    checkout = "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0"
    setup_python = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
    marker = "          persist-credentials: false"
    assert all(value in workflow for value in (checkout, setup_python, marker))

    assert_approved(workflow)
    assert_approved(workflow.replace("name: CI", "name: CI audit fixture", 1))

    mutations = {
        "third-party action": workflow.replace(
            marker,
            f"{marker}\n      - uses: untrusted/example@0123456789abcdef",
            1,
        ),
        "wrong immutable revision": workflow.replace(checkout, f"actions/checkout@{'0' * 40}", 1),
        "mutable major tag": workflow.replace(setup_python, "actions/setup-python@v6", 1),
        "missing revision": workflow.replace(checkout, "actions/checkout", 1),
    }

    for case, mutated in mutations.items():
        assert mutated != workflow, case
        try:
            assert_approved(mutated)
        except AssertionError:
            continue
        pytest.fail(f"guard accepted {case}")

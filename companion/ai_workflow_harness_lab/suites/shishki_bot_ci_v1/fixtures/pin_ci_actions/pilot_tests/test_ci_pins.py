from __future__ import annotations

import hashlib
import re
from pathlib import Path


WORKFLOW = Path(".github/workflows/ci.yml")
CANONICAL_WORKFLOW_SHA256 = "5a0e83cc77c460093ea59e51979cef2e042e87fe938f2056bb194d6e1df11aba"
APPROVED = {
    "actions/checkout": "9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
    "actions/setup-python": "ece7cb06caefa5fff74198d8649806c4678c61a1",
}


def test_ci_uses_only_approved_immutable_action_revisions() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    references = re.findall(r"(?m)^[ \t]*(?:-[ \t]*)?uses:[ \t]+([^\s#]+)", text)

    assert references
    assert len(references) == len(APPROVED)
    for reference in references:
        action, separator, revision = reference.partition("@")
        assert separator == "@"
        assert action in APPROVED
        assert revision == APPROVED[action]
    assert hashlib.sha256(WORKFLOW.read_bytes()).hexdigest() == CANONICAL_WORKFLOW_SHA256


def test_ci_keeps_read_only_permissions_and_checkout_credentials_disabled() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert re.findall(r"(?m)^permissions:\s*\n\s+contents:\s+read\s*$", text)
    checkout = re.search(
        r"(?ms)^\s*- uses: actions/checkout@[^\n]+\n(?P<body>.*?)(?=^\s*- (?:name|uses):)",
        text,
    )
    assert checkout is not None
    assert "persist-credentials: false" in checkout.group("body")

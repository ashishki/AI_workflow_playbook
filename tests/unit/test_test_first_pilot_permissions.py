from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/verify_test_first_pilot_permissions.py"


def test_frozen_permission_profile_denies_sibling_auth_and_network_access() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-X",
            "pycache_prefix=/dev/null/test-first-pilot-pycache",
            str(PROBE),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=40,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "workspace-only write, bounded read, network denied" in result.stdout

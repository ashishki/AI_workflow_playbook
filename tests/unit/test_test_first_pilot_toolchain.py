from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import verify_test_first_pilot_toolchain


VERIFIER = ROOT / "tools/verify_test_first_pilot_toolchain.py"
LOCK = ROOT / "reports/test_first_pilot/shishki_bot_v1/TOOLCHAIN.json"
RUNNER = ROOT / "tools/run_test_first_pilot.sh"
BWRAP = Path("/usr/bin/bwrap")
ISOLATED_FLAGS = [
    "-I",
    "-S",
    "-B",
    "-X",
    "pycache_prefix=/dev/null/test-first-pilot-pycache",
]


def verifier_command(lock: Path) -> list[str]:
    return [sys.executable, *ISOLATED_FLAGS, str(VERIFIER), "--lock", str(lock)]


def test_frozen_toolchain_matches_current_pilot_environment() -> None:
    result = subprocess.run(
        verifier_command(LOCK),
        cwd=ROOT,
        env={
            "HOME": str(Path.home()),
            "PATH": "/untrusted/bin",
            "PYTHONPATH": "/untrusted/python",
            "PYTHONPYCACHEPREFIX": "/untrusted/cache",
            "PYTEST_ADDOPTS": "-p untrusted_plugin",
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "ok"


def test_toolchain_verifier_fails_closed_on_drift(tmp_path: Path) -> None:
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    payload["pytest_version"] = "0.0-drift"
    drifted = tmp_path / "toolchain.json"
    drifted.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        verifier_command(drifted),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert json.loads(result.stderr)["status"] == "drift"


def test_toolchain_lock_pins_import_closure_and_absolute_executables() -> None:
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    verifier = VERIFIER.read_text(encoding="utf-8")

    assert payload["schema_version"] == "test_first_pilot.toolchain.v2"
    assert payload["site_packages"]["file_count"] > 1000
    assert len(payload["site_packages"]["manifest_sha256"]) == 64
    codex = payload["codex_cli"]
    assert Path(codex["entrypoint_path"]).is_absolute()
    assert Path(codex["entrypoint_path"]).name == "codex"
    assert len(codex["entrypoint_sha256"]) == 64
    for name in ("bash", "cp", "git", "mkdir", "sha256sum", "sh"):
        binary = payload["runner_binaries"][name]
        assert Path(binary["path"]).is_absolute()
        assert Path(binary["realpath"]).is_absolute()
        assert len(binary["sha256"]) == 64
    assert payload["runner_binaries"]["sh"]["realpath"] == "/usr/bin/dash"
    assert "subprocess" not in verifier
    assert "shutil.which" not in verifier


def test_toolchain_rejects_special_site_package_entries(tmp_path: Path) -> None:
    site_packages = tmp_path / "site-packages"
    site_packages.mkdir()
    os.mkfifo(site_packages / "injected.pth")

    with pytest.raises(RuntimeError, match="must be a regular file"):
        verify_test_first_pilot_toolchain.site_packages_state(site_packages)


def test_toolchain_rejects_symlinked_site_package_ancestor(tmp_path: Path) -> None:
    real = tmp_path / "real/site-packages"
    real.mkdir(parents=True)
    (real / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    linked = tmp_path / "linked"
    linked.symlink_to(tmp_path / "real", target_is_directory=True)

    with pytest.raises(RuntimeError, match="symlink is not allowed"):
        verify_test_first_pilot_toolchain.site_packages_state(
            linked / "site-packages"
        )


def test_runner_gates_frozen_python_and_uses_clean_pinned_commands() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    frozen_gate = runner.split("verify_frozen_assets() {", 1)[1].split("\n}", 1)[0]
    checksum = frozen_gate.index('"$SHA256SUM" -c -- "$ASSET_MANIFEST"')
    toolchain = frozen_gate.index(
        '"$PYTHON" "${TOOLCHAIN_PYTHON_FLAGS[@]}" "$TOOLCHAIN_VERIFIER"'
    )
    closure = frozen_gate.index(
        '"$PYTHON" "${PYTHON_FLAGS[@]}" "$MANIFEST_BUILDER" --check'
    )
    authorization = runner.index("\n  authorize_full_run\n")
    main_gate = runner.index("\nverify_frozen_assets\n")
    harness = runner.index("\nharness validate-suite")
    pytest = runner.index('\n"$PYTHON" "${PYTHON_FLAGS[@]}" -m pytest')

    assert checksum < toolchain < closure
    assert authorization < main_gate
    assert main_gate < harness < pytest
    assert runner.startswith("#!/usr/bin/bash -p\n")
    assert 'TOOLCHAIN_PYTHON_FLAGS=(-I -S -B -X ' in runner
    assert "pycache_prefix=/dev/null/test-first-pilot-pycache" in runner
    assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1" in runner
    assert "-p no:cacheprovider --noconftest" in runner
    assert "PYTEST_ADDOPTS" not in runner
    assert "PYTHONPATH" not in runner
    assert r'--codex-bin \"$CODEX\"' in runner
    assert '"$CODEX" --version' in runner
    assert r'\"$BWRAP\" --die-with-parent --new-session --unshare-pid' in runner
    assert '--bind / / --proc /proc --dev-bind /dev /dev --' in runner
    assert "pilot output directory is missing or linked" in runner
    assert "approval record is missing or linked" in runner
    assert len(re.findall(r"^run_one ", runner, re.MULTILINE)) == 12


def test_runner_requires_one_terminal_critic_allow(tmp_path: Path) -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^require_terminal_critic_allow\(\) \{\n.*?^\}\n",
        runner,
    )
    assert match is not None
    probe = tmp_path / "critic-gate.sh"
    probe.write_text(
        "#!/usr/bin/bash -p\nset -euo pipefail\n"
        + match.group(0)
        + '\nCRITIC_RECORD=$1\nrequire_terminal_critic_allow\n',
        encoding="utf-8",
    )
    probe.chmod(0o700)

    cases = {
        "allow.md": ("review\nDecision: ALLOW\n", 0),
        "block.md": ("review\nDecision: BLOCK\n", 2),
        "both.md": ("Decision: ALLOW\nDecision: BLOCK\n", 2),
        "not-terminal.md": ("Decision: ALLOW\nmore text\n", 2),
    }
    for name, (content, expected) in cases.items():
        critic = tmp_path / name
        critic.write_text(content, encoding="utf-8")
        result = subprocess.run(
            ["/usr/bin/bash", "-p", str(probe), str(critic)],
            cwd=ROOT,
            env={"PATH": "/usr/bin:/bin"},
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == expected, (name, result.stderr)


def test_runner_requires_one_terminal_approval_decision(tmp_path: Path) -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    match = re.search(
        r"(?ms)^require_terminal_approval\(\) \{\n.*?^\}\n",
        runner,
    )
    assert match is not None
    probe = tmp_path / "approval-gate.sh"
    probe.write_text(
        "#!/usr/bin/bash -p\nset -euo pipefail\n"
        + match.group(0)
        + "\nTFA_PILOT_APPROVAL_RECORD=$1\nrequire_terminal_approval\n",
        encoding="utf-8",
    )
    probe.chmod(0o700)

    cases = {
        "approved.md": ("approval\nDecision: approved\n", 0),
        "denied.md": ("approval\nDecision: denied\n", 2),
        "both.md": ("Decision: approved\nDecision: denied\n", 2),
        "not-terminal.md": ("Decision: approved\nmore text\n", 2),
    }
    for name, (content, expected) in cases.items():
        approval = tmp_path / name
        approval.write_text(content, encoding="utf-8")
        result = subprocess.run(
            ["/usr/bin/bash", "-p", str(probe), str(approval)],
            cwd=ROOT,
            env={"PATH": "/usr/bin:/bin"},
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == expected, (name, result.stderr)


def test_runner_pid_namespace_stops_detached_descendants(tmp_path: Path) -> None:
    heartbeat = tmp_path / "heartbeat"
    probe = r"""
import os
import sys
import time

heartbeat = sys.argv[1]
if os.fork():
    time.sleep(10)
    raise SystemExit(0)
os.setsid()
if os.fork():
    os._exit(0)
fd = os.open(heartbeat, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
deadline = time.monotonic() + 10
while time.monotonic() < deadline:
    os.write(fd, b"x")
    os.fsync(fd)
    time.sleep(0.02)
"""
    process = subprocess.Popen(
        [
            str(BWRAP),
            "--die-with-parent",
            "--new-session",
            "--unshare-pid",
            "--bind",
            "/",
            "/",
            "--proc",
            "/proc",
            "--dev-bind",
            "/dev",
            "/dev",
            "--",
            sys.executable,
            "-I",
            "-S",
            "-c",
            probe,
            str(heartbeat),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if heartbeat.exists() and heartbeat.stat().st_size > 0:
                break
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise AssertionError(
                    f"PID namespace probe exited early: {stdout!r} {stderr!r}"
                )
            time.sleep(0.02)
        else:
            raise AssertionError("detached PID namespace probe did not start")

        process.terminate()
        process.wait(timeout=5)
        size_after_stop = heartbeat.stat().st_size
        time.sleep(0.2)
        assert heartbeat.stat().st_size == size_after_stop
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)

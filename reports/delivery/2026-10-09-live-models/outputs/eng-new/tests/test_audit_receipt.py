import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import audit_receipt


ROOT = Path(__file__).resolve().parents[1]


class ReceiptAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".receipt-audit-test-", dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.path = self.directory / "receipt.json"
        self.receipt = {
            "schema_version": "playbook.command_receipt.v1",
            "exit_code": 0,
            "command_argv": ["saved-command", "argument with spaces"],
            "environment_summary": {"timed_out": False},
        }
        for stream, data in (("stdout", b"saved output\n"), ("stderr", b"")):
            (self.directory / (stream + ".txt")).write_bytes(data)
            self.receipt[stream + "_artifact_path"] = stream + ".txt"
            self.receipt[stream + "_sha256"] = hashlib.sha256(data).hexdigest()
        self.write_receipt()

    def write_receipt(self, receipt=None):
        self.path.write_text(json.dumps(self.receipt if receipt is None else receipt), encoding="utf-8")

    def cli(self, *args):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "audit_receipt.py"), *map(str, args)],
            capture_output=True, text=True, timeout=5, check=False,
        )
        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        result = json.loads(completed.stdout)
        self.assertEqual(set(result), {"status", "reason", "exit_code", "command_argv"})
        self.assertTrue(result["reason"])
        return completed.returncode, result

    def test_classifications_and_cli_exit_codes(self):
        for exit_code, timed_out, status in ((0, False, "PASS"), (7, False, "FAIL"),
                                           (-9, False, "FAIL"), (0, True, "FAIL"),
                                           (124, True, "FAIL")):
            with self.subTest(exit_code=exit_code, timed_out=timed_out):
                self.receipt["exit_code"] = exit_code
                self.receipt["environment_summary"]["timed_out"] = timed_out
                self.write_receipt()
                code, result = self.cli(self.path)
                self.assertEqual((code, result["status"]), (0, status))
                self.assertEqual(result["exit_code"], exit_code)
                self.assertEqual(result["command_argv"], self.receipt["command_argv"])

    def test_missing_evidence_prevents_pass_and_fail(self):
        (self.directory / "stdout.txt").unlink()
        for exit_code, timed_out in ((0, False), (1, False), (124, True)):
            with self.subTest(exit_code=exit_code):
                self.receipt["exit_code"] = exit_code
                self.receipt["environment_summary"]["timed_out"] = timed_out
                self.write_receipt()
                code, result = self.cli(self.path)
                self.assertEqual((code, result["status"]), (0, "NOT_RUN"))
                self.assertIn("stdout", result["reason"])

    def test_mismatch_is_invalid_even_with_failure_or_missing_other_stream(self):
        for stream in ("stdout", "stderr"):
            for other_missing in (False, True):
                with self.subTest(stream=stream, other_missing=other_missing):
                    for name, data in (("stdout", b"saved output\n"), ("stderr", b"")):
                        (self.directory / (name + ".txt")).write_bytes(data)
                    (self.directory / (stream + ".txt")).write_bytes(b"tampered")
                    if other_missing:
                        other = "stderr" if stream == "stdout" else "stdout"
                        (self.directory / (other + ".txt")).unlink()
                    self.receipt["exit_code"] = 124
                    self.receipt["environment_summary"]["timed_out"] = True
                    self.write_receipt()
                    code, result = self.cli(self.path)
                    self.assertEqual((code, result["status"]), (2, "INVALID"))
                    self.assertIn(stream + " SHA256 mismatch", result["reason"])

    def test_invalid_receipt_fields(self):
        bad_fields = {
            "schema_version": [None, "other", 1],
            "exit_code": [None, True, False, 0.0, "0"],
            "command_argv": [None, "echo hello", [], ["echo", 1]],
            "environment_summary": [None, [], {}, {"timed_out": 0}, {"timed_out": "false"}],
            "stdout_artifact_path": [None, "", 1],
            "stderr_sha256": [None, "", "x" * 64, "0" * 63, 1],
        }
        for key, values in bad_fields.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    receipt = copy.deepcopy(self.receipt)
                    receipt[key] = value
                    self.write_receipt(receipt)
                    self.assertEqual(audit_receipt.inspect_receipt(self.path)["status"], "INVALID")
            with self.subTest(missing=key):
                receipt = copy.deepcopy(self.receipt)
                del receipt[key]
                self.write_receipt(receipt)
                self.assertEqual(audit_receipt.inspect_receipt(self.path)["status"], "INVALID")

    def test_invalid_json_and_input_are_reported_as_one_json_object(self):
        for data in (b"{", b"[]", b"null", b"\xff", b'{"exit_code":0,"exit_code":1}',
                     b'{"exit_code":NaN}', b"[" * 2000 + b"]" * 2000):
            with self.subTest(data=data[:40]):
                self.path.write_bytes(data)
                code, result = self.cli(self.path)
                self.assertEqual((code, result["status"]), (2, "INVALID"))
        for args in ((), (self.path, self.path), (self.directory / "absent.json",)):
            with self.subTest(args=args):
                code, result = self.cli(*args)
                self.assertEqual((code, result["status"]), (2, "INVALID"))

    def test_unsafe_artifact_paths_are_invalid_even_when_other_evidence_missing(self):
        (self.directory / "stdout.txt").unlink()
        paths = ("../outside.txt", "nested/../../outside.txt", str(self.directory / "stderr.txt"),
                 "https://example.invalid/evidence", "C:/evidence.txt", "C:evidence.txt",
                 "..\\outside.txt", "\\\\server\\evidence", "bad\x00name", ".")
        for path in paths:
            with self.subTest(path=path):
                self.receipt["stderr_artifact_path"] = path
                self.write_receipt()
                self.assertEqual(audit_receipt.inspect_receipt(self.path)["status"], "INVALID")

    def test_safe_nested_artifact_and_uppercase_digest(self):
        nested = self.directory / "nested"
        nested.mkdir()
        (self.directory / "stdout.txt").rename(nested / "stdout.txt")
        self.receipt["stdout_artifact_path"] = "./nested/stdout.txt"
        self.receipt["stdout_sha256"] = self.receipt["stdout_sha256"].upper()
        self.write_receipt()
        self.assertEqual(audit_receipt.inspect_receipt(self.path)["status"], "PASS")

    def test_file_links_are_invalid_including_dangling_symlinks(self):
        for filename in ("receipt.json", "stdout.txt", "stderr.txt"):
            for kind in ("symlink", "dangling", "hardlink"):
                with self.subTest(filename=filename, kind=kind):
                    path = self.directory / filename
                    original = path.read_bytes()
                    target = self.directory / "target"
                    path.rename(target)
                    if kind == "hardlink":
                        os.link(target, path)
                    else:
                        path.symlink_to(target if kind == "symlink" else self.directory / "absent")
                    self.assertEqual(audit_receipt.inspect_receipt(self.path)["status"], "INVALID")
                    path.unlink()
                    target.unlink()
                    path.write_bytes(original)

    def test_symlink_directory_components_are_invalid(self):
        linked = self.directory / "linked"
        linked.symlink_to(self.directory, target_is_directory=True)
        self.assertEqual(audit_receipt.inspect_receipt(linked / "receipt.json")["status"], "INVALID")
        self.receipt["stdout_artifact_path"] = "linked/stdout.txt"
        self.write_receipt()
        self.assertEqual(audit_receipt.inspect_receipt(self.path)["status"], "INVALID")

    def test_nonregular_files_are_invalid_without_blocking(self):
        for filename in ("receipt.json", "stdout.txt", "stderr.txt"):
            for kind in ("directory", "fifo"):
                with self.subTest(filename=filename, kind=kind):
                    path = self.directory / filename
                    original = path.read_bytes()
                    path.unlink()
                    if kind == "directory":
                        path.mkdir()
                    else:
                        os.mkfifo(path)
                    code, result = self.cli(self.path)
                    self.assertEqual((code, result["status"]), (2, "INVALID"))
                    if kind == "directory":
                        path.rmdir()
                    else:
                        path.unlink()
                    path.write_bytes(original)

    def test_per_file_size_limit_includes_exact_boundary(self):
        for filename in ("receipt.json", "stdout.txt", "stderr.txt"):
            with self.subTest(filename=filename):
                self.write_receipt()
                path = self.directory / filename
                original = path.read_bytes()
                if filename == "receipt.json":
                    boundary_data = original + b" " * (audit_receipt.MAX_BYTES - len(original))
                else:
                    boundary_data = b"x" * audit_receipt.MAX_BYTES
                    self.receipt[filename[:-4] + "_sha256"] = hashlib.sha256(boundary_data).hexdigest()
                    self.write_receipt()
                path.write_bytes(boundary_data)
                self.assertEqual(audit_receipt.inspect_receipt(self.path)["status"], "PASS")
                path.write_bytes(boundary_data + b" ")
                self.assertEqual(audit_receipt.inspect_receipt(self.path)["status"], "INVALID")
                path.write_bytes(original)
                if filename != "receipt.json":
                    self.receipt[filename[:-4] + "_sha256"] = hashlib.sha256(original).hexdigest()

    def test_command_is_returned_as_data_and_never_executed(self):
        marker = self.directory / "executed"
        self.receipt["command_argv"] = [sys.executable, "-c",
                                      "from pathlib import Path; Path(" + repr(str(marker)) + ").touch()"]
        self.write_receipt()
        before = {path: path.read_bytes() for path in self.directory.iterdir()}
        code, result = self.cli(self.path)
        self.assertEqual((code, result["status"]), (0, "PASS"))
        self.assertEqual(result["command_argv"], self.receipt["command_argv"])
        self.assertFalse(marker.exists())
        self.assertEqual(before, {path: path.read_bytes() for path in self.directory.iterdir()})

    def test_real_supplied_receipt_and_owner_notes_remain_unchanged(self):
        expected = {
            "owner-notes.txt": "6ffd440c786b1e71065e280b1bc5b47dd90c672638357c1e6837efe3871f8e36",
            "examples/actual-pass/receipt.json": "c3c5580f3b93cec6c86d654c112d4da4633990bb8d04402ec487a6b3948888f6",
            "examples/actual-pass/stderr.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "examples/actual-pass/stdout.txt": "1be15eac1c1ff01d77252b2c289c56e6fb68946b5a43b751044d45aa4dc333c9",
        }
        code, result = self.cli(ROOT / "examples/actual-pass/receipt.json")
        self.assertEqual((code, result["status"]), (0, "PASS"))
        for filename, digest in expected.items():
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256((ROOT / filename).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Inspect saved command evidence without executing the recorded command."""

import hashlib
import json
import os
from pathlib import PurePosixPath, PureWindowsPath
import re
import stat
import sys


MAX_BYTES = 1024 * 1024
SCHEMA_VERSION = "playbook.command_receipt.v1"


def _check_file(info):
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("file must be regular (no symbolic links)")
    if info.st_nlink != 1:
        raise ValueError("hard links are forbidden")
    if info.st_size > MAX_BYTES:
        raise ValueError("file exceeds 1 MiB")


def _open_directory(parts, root_fd=None):
    """Walk directory descriptors so no path component follows a symlink."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(".", flags, dir_fd=root_fd)
    try:
        for part in parts:
            next_fd = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read_file(root_fd, parts):
    directory = _open_directory(parts[:-1], root_fd)
    try:
        name = parts[-1]
        _check_file(os.stat(name, dir_fd=directory, follow_symlinks=False))
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        fd = os.open(name, flags, dir_fd=directory)
        with os.fdopen(fd, "rb") as handle:
            _check_file(os.fstat(handle.fileno()))
            data = handle.read(MAX_BYTES + 1)
            _check_file(os.fstat(handle.fileno()))
        if len(data) > MAX_BYTES:
            raise ValueError("file exceeds 1 MiB")
        return data
    finally:
        os.close(directory)


def _artifact_parts(value):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("artifact path must be a nonempty local path")
    path = PurePosixPath(value)
    if (path.is_absolute() or ".." in path.parts or "\\" in value
            or ":" in value or PureWindowsPath(value).drive or not path.parts):
        raise ValueError("artifact path must stay inside the receipt directory")
    return path.parts


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("invalid JSON constant: " + value)


def inspect_receipt(path):
    """Return a classification; INVALID takes precedence over missing evidence."""
    result = {"status": "INVALID", "reason": "", "exit_code": None,
              "command_argv": None}
    directory = None
    try:
        receipt_path = PurePosixPath(os.fspath(path))
        if not receipt_path.name:
            raise ValueError("receipt path must name a file")
        directory = _open_directory(receipt_path.parts[:-1])
        data = _read_file(directory, (receipt_path.name,))
        receipt = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
        if not isinstance(receipt, dict):
            raise ValueError("receipt must be a JSON object")
        if type(receipt.get("exit_code")) is int:
            result["exit_code"] = receipt["exit_code"]
        argv = receipt.get("command_argv")
        if isinstance(argv, list) and argv and all(isinstance(arg, str) for arg in argv):
            result["command_argv"] = argv
        if receipt.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported schema_version")
        if result["exit_code"] is None:
            raise ValueError("exit_code must be an integer excluding bool")
        if result["command_argv"] is None:
            raise ValueError("command_argv must be a nonempty list of strings")
        environment = receipt.get("environment_summary")
        if not isinstance(environment, dict) or type(environment.get("timed_out")) is not bool:
            raise ValueError("environment_summary.timed_out must be a boolean")

        artifacts = []
        for stream in ("stdout", "stderr"):
            parts = _artifact_parts(receipt.get(stream + "_artifact_path"))
            digest = receipt.get(stream + "_sha256")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
                raise ValueError(stream + "_sha256 must be a 64-digit SHA256 hex digest")
            artifacts.append((stream, parts, digest.lower()))

        missing = []
        for stream, parts, digest in artifacts:
            try:
                evidence = _read_file(directory, parts)
            except FileNotFoundError:
                missing.append(stream)
                continue
            if hashlib.sha256(evidence).hexdigest() != digest:
                raise ValueError(stream + " SHA256 mismatch")
        if missing:
            result.update(status="NOT_RUN", reason="missing evidence: " + ", ".join(missing))
        elif environment["timed_out"]:
            result.update(status="FAIL", reason="command timed out; stdout/stderr SHA256 verified")
        elif receipt["exit_code"] != 0:
            result.update(status="FAIL", reason="nonzero exit_code; stdout/stderr SHA256 verified")
        else:
            result.update(status="PASS", reason="zero exit_code; stdout/stderr SHA256 verified")
    except (OSError, ValueError, RecursionError) as exc:
        result.update(status="INVALID", reason=str(exc))
    finally:
        if directory is not None:
            os.close(directory)
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        result = {"status": "INVALID", "reason": "usage: python3 audit_receipt.py RECEIPT.json",
                  "exit_code": None, "command_argv": None}
    else:
        result = inspect_receipt(args[0])
    print(json.dumps(result))
    return 2 if result["status"] == "INVALID" else 0


if __name__ == "__main__":
    sys.exit(main())

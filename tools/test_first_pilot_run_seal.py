#!/usr/bin/env python3
"""Create or verify the deterministic local seal for a completed pilot run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


SEAL_NAME = "COMPLETED_RUN.json"
SCHEMA_VERSION = "test_first_pilot.completed_run.v1"
OPEN_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
OPEN_CLOEXEC = getattr(os, "O_CLOEXEC", 0)


class SealError(RuntimeError):
    """The run cannot be sealed or does not match its seal."""


class MutationError(SealError):
    """The run changed while a snapshot or seal operation was in progress."""


@dataclass(frozen=True)
class SealResult:
    path: Path
    seal_sha256: str
    entry_count: int


def _stable_stat(file_stat: os.stat_result) -> tuple[int, ...]:
    return (
        file_stat.st_dev,
        file_stat.st_ino,
        file_stat.st_mode,
        file_stat.st_size,
        file_stat.st_mtime_ns,
        file_stat.st_ctime_ns,
    )


def _same_object(first: os.stat_result, second: os.stat_result) -> bool:
    return (
        first.st_dev,
        first.st_ino,
        stat.S_IFMT(first.st_mode),
    ) == (
        second.st_dev,
        second.st_ino,
        stat.S_IFMT(second.st_mode),
    )


def _entry_path(parts: tuple[str, ...]) -> str:
    return PurePosixPath(*parts).as_posix()


def _entry_mode(file_stat: os.stat_result) -> str:
    return f"{stat.S_IMODE(file_stat.st_mode):04o}"


def _special_type(mode: int) -> str:
    if stat.S_ISFIFO(mode):
        return "fifo"
    if stat.S_ISSOCK(mode):
        return "socket"
    if stat.S_ISCHR(mode):
        return "character_device"
    if stat.S_ISBLK(mode):
        return "block_device"
    return f"special_{stat.S_IFMT(mode):o}"


def _directory_names(directory_fd: int, *, top_level: bool) -> list[str]:
    try:
        names = os.listdir(directory_fd)
    except OSError as exc:
        raise SealError(f"cannot list run directory: {exc}") from exc
    if top_level:
        names = [name for name in names if name != SEAL_NAME]
    return sorted(names)


def _hash_regular_file(
    directory_fd: int,
    name: str,
    observed: os.stat_result,
    relative: str,
) -> dict[str, Any]:
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | OPEN_NOFOLLOW | OPEN_CLOEXEC,
            dir_fd=directory_fd,
        )
    except OSError as exc:
        raise MutationError(
            f"cannot open regular run entry without following links: {relative}: {exc}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not _same_object(observed, before):
            raise MutationError(f"run entry changed type or identity while opening: {relative}")
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        if _stable_stat(before) != _stable_stat(after):
            raise MutationError(f"run file changed while hashing: {relative}")
        return {
            "mode": _entry_mode(before),
            "sha256": digest.hexdigest(),
            "size": before.st_size,
            "type": "file",
        }
    finally:
        os.close(descriptor)


def _read_symlink(
    directory_fd: int,
    name: str,
    observed: os.stat_result,
    relative: str,
) -> dict[str, Any]:
    try:
        target = os.readlink(name, dir_fd=directory_fd)
        after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except OSError as exc:
        raise MutationError(f"cannot read workspace symlink: {relative}: {exc}") from exc
    if _stable_stat(observed) != _stable_stat(after):
        raise MutationError(f"workspace symlink changed while reading: {relative}")
    return {
        "mode": _entry_mode(observed),
        "target": target,
        "type": "symlink",
    }


def _special_entry(file_stat: os.stat_result) -> dict[str, Any]:
    result: dict[str, Any] = {
        "mode": _entry_mode(file_stat),
        "type": _special_type(file_stat.st_mode),
    }
    if stat.S_ISCHR(file_stat.st_mode) or stat.S_ISBLK(file_stat.st_mode):
        result["device"] = file_stat.st_rdev
    return result


def _is_arm_workspace(parts: tuple[str, ...]) -> bool:
    return (
        len(parts) == 4
        and parts[0] in {"baseline", "playbook"}
        and bool(parts[1])
        and parts[2].startswith("trial-")
        and parts[2].removeprefix("trial-").isdigit()
        and parts[3] == "workspace"
    )


def _scan_directory(
    directory_fd: int,
    parts: tuple[str, ...],
    inside_workspace: bool,
    entries: dict[str, dict[str, Any]],
) -> None:
    top_level = not parts
    before_directory = os.fstat(directory_fd)
    before_names = _directory_names(directory_fd, top_level=top_level)

    for name in before_names:
        child_parts = (*parts, name)
        relative = _entry_path(child_parts)
        try:
            observed = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as exc:
            raise MutationError(f"run entry changed while scanning: {relative}: {exc}") from exc

        mode = observed.st_mode
        if stat.S_ISDIR(mode):
            try:
                child_fd = os.open(
                    name,
                    os.O_RDONLY | os.O_DIRECTORY | OPEN_NOFOLLOW | OPEN_CLOEXEC,
                    dir_fd=directory_fd,
                )
            except OSError as exc:
                raise MutationError(
                    f"cannot open run directory without following links: {relative}: {exc}"
                ) from exc
            try:
                opened = os.fstat(child_fd)
                if not _same_object(observed, opened):
                    raise MutationError(f"run directory changed while opening: {relative}")
                entries[relative] = {
                    "mode": _entry_mode(opened),
                    "type": "directory",
                }
                _scan_directory(
                    child_fd,
                    child_parts,
                    inside_workspace or _is_arm_workspace(child_parts),
                    entries,
                )
                after_open = os.fstat(child_fd)
                if _stable_stat(opened) != _stable_stat(after_open):
                    raise MutationError(f"run directory changed while scanning: {relative}")
            finally:
                os.close(child_fd)
        elif stat.S_ISREG(mode):
            entries[relative] = _hash_regular_file(directory_fd, name, observed, relative)
        elif stat.S_ISLNK(mode):
            if not inside_workspace:
                raise SealError(f"symbolic link outside workspace is forbidden: {relative}")
            entries[relative] = _read_symlink(directory_fd, name, observed, relative)
        else:
            if not inside_workspace:
                entry_type = _special_type(mode)
                raise SealError(
                    f"special entry outside workspace is forbidden: {relative} ({entry_type})"
                )
            entries[relative] = _special_entry(observed)

        try:
            after_entry = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as exc:
            raise MutationError(f"run entry disappeared while scanning: {relative}: {exc}") from exc
        if _stable_stat(observed) != _stable_stat(after_entry):
            raise MutationError(f"run entry changed while scanning: {relative}")

    after_names = _directory_names(directory_fd, top_level=top_level)
    after_directory = os.fstat(directory_fd)
    if (
        before_names != after_names
        or _stable_stat(before_directory) != _stable_stat(after_directory)
    ):
        location = _entry_path(parts) if parts else "."
        raise MutationError(f"run directory changed while scanning: {location}")


def _snapshot_fd(root_fd: int) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    _scan_directory(root_fd, (), False, entries)
    return dict(sorted(entries.items()))


def _open_root(root: Path) -> tuple[Path, int]:
    absolute = Path(os.path.abspath(root))
    try:
        descriptor = os.open(
            absolute.anchor,
            os.O_RDONLY | os.O_DIRECTORY | OPEN_NOFOLLOW | OPEN_CLOEXEC,
        )
    except OSError as exc:
        raise SealError(f"cannot open run-root anchor: {absolute.anchor}: {exc}") from exc
    try:
        for index, component in enumerate(absolute.parts[1:], start=1):
            try:
                child_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | OPEN_NOFOLLOW | OPEN_CLOEXEC,
                    dir_fd=descriptor,
                )
            except OSError as exc:
                lexical = Path(*absolute.parts[: index + 1])
                raise SealError(
                    f"run root has a symlink, missing, or non-directory component: "
                    f"{lexical}: {exc}"
                ) from exc
            os.close(descriptor)
            descriptor = child_fd
    except BaseException:
        os.close(descriptor)
        raise
    return absolute, descriptor


def snapshot_run(root: Path) -> dict[str, dict[str, Any]]:
    """Return the deterministic no-follow entry inventory beneath ``root``."""
    _absolute, root_fd = _open_root(root)
    try:
        return _snapshot_fd(root_fd)
    finally:
        os.close(root_fd)


def _seal_bytes(entries: dict[str, dict[str, Any]]) -> bytes:
    payload = {
        "entries": entries,
        "entry_count": len(entries),
        "schema_version": SCHEMA_VERSION,
    }
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _seal_exists(root_fd: int) -> bool:
    try:
        os.stat(SEAL_NAME, dir_fd=root_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise SealError(f"cannot inspect {SEAL_NAME}: {exc}") from exc
    return True


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError("short write while creating completed-run seal")
        offset += written


def _remove_created_seal(root_fd: int, seal_stat: os.stat_result) -> None:
    try:
        current = os.stat(SEAL_NAME, dir_fd=root_fd, follow_symlinks=False)
    except OSError:
        return
    if _same_object(current, seal_stat):
        try:
            os.unlink(SEAL_NAME, dir_fd=root_fd)
            os.fsync(root_fd)
        except OSError:
            pass


def write_seal(root: Path) -> SealResult:
    """Create ``COMPLETED_RUN.json`` once and fail if the run is unstable."""
    absolute, root_fd = _open_root(root)
    try:
        if _seal_exists(root_fd):
            raise SealError(f"completed-run seal already exists: {absolute / SEAL_NAME}")
        initial = _snapshot_fd(root_fd)
        confirmed = _snapshot_fd(root_fd)
        if initial != confirmed:
            raise MutationError("run root changed between pre-seal snapshots")
        payload = _seal_bytes(initial)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | OPEN_NOFOLLOW | OPEN_CLOEXEC
        seal_stat: os.stat_result | None = None
        try:
            seal_fd = os.open(SEAL_NAME, flags, 0o600, dir_fd=root_fd)
        except FileExistsError as exc:
            raise SealError(f"completed-run seal already exists: {absolute / SEAL_NAME}") from exc
        except OSError as exc:
            raise SealError(f"cannot create completed-run seal: {exc}") from exc
        try:
            seal_stat = os.fstat(seal_fd)
            os.fchmod(seal_fd, 0o600)
            _write_all(seal_fd, payload)
            os.fsync(seal_fd)
            seal_stat = os.fstat(seal_fd)
            if not stat.S_ISREG(seal_stat.st_mode):
                raise SealError("completed-run seal is not a regular file")
            os.fsync(root_fd)
            try:
                final = _snapshot_fd(root_fd)
            except SealError as exc:
                raise MutationError(
                    "run root became invalid between snapshot and final seal write"
                ) from exc
            if initial != final:
                raise MutationError(
                    "run root changed between snapshot and final seal write"
                )
        except OSError as exc:
            if seal_stat is not None:
                _remove_created_seal(root_fd, seal_stat)
            try:
                os.close(seal_fd)
            except OSError:
                pass
            raise SealError(f"cannot write completed-run seal: {exc}") from exc
        except BaseException:
            if seal_stat is not None:
                _remove_created_seal(root_fd, seal_stat)
            try:
                os.close(seal_fd)
            except OSError:
                pass
            raise
        try:
            os.close(seal_fd)
        except OSError as exc:
            _remove_created_seal(root_fd, seal_stat)
            raise SealError(f"cannot close completed-run seal: {exc}") from exc
        return SealResult(
            path=absolute / SEAL_NAME,
            seal_sha256=_sha256_bytes(payload),
            entry_count=len(initial),
        )
    finally:
        os.close(root_fd)


def _read_seal(root_fd: int) -> tuple[bytes, os.stat_result]:
    try:
        descriptor = os.open(
            SEAL_NAME,
            os.O_RDONLY | OPEN_NOFOLLOW | OPEN_CLOEXEC,
            dir_fd=root_fd,
        )
    except FileNotFoundError as exc:
        raise SealError(f"completed-run seal is missing: {SEAL_NAME}") from exc
    except OSError as exc:
        raise SealError(f"cannot open completed-run seal without following links: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise SealError("completed-run seal must be a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if _stable_stat(before) != _stable_stat(after):
            raise MutationError("completed-run seal changed while reading")
        return b"".join(chunks), after
    finally:
        os.close(descriptor)


def verify_seal(root: Path) -> SealResult:
    """Verify the exact run closure against ``COMPLETED_RUN.json``."""
    absolute, root_fd = _open_root(root)
    try:
        first_seal, first_seal_stat = _read_seal(root_fd)
        first = _snapshot_fd(root_fd)
        second = _snapshot_fd(root_fd)
        second_seal, second_seal_stat = _read_seal(root_fd)
        if first != second:
            raise MutationError("run root changed while verifying its completed-run seal")
        if first_seal != second_seal or not _same_object(first_seal_stat, second_seal_stat):
            raise MutationError("completed-run seal changed while verifying the run")
        expected = _seal_bytes(first)
        if first_seal != expected:
            raise SealError("completed-run seal does not match the exact run closure")
        return SealResult(
            path=absolute / SEAL_NAME,
            seal_sha256=_sha256_bytes(first_seal),
            entry_count=len(first),
        )
    finally:
        os.close(root_fd)


def _result_payload(status: str, result: SealResult) -> dict[str, Any]:
    return {
        "entry_count": result.entry_count,
        "path": str(result.path),
        "seal_sha256": result.seal_sha256,
        "status": status,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("write", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("root", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = write_seal(args.root) if args.command == "write" else verify_seal(args.root)
    except SealError as exc:
        print(f"completed-run seal: error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(_result_payload(args.command, result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

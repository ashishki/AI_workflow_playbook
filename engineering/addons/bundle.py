#!/usr/bin/env python3
"""Offline, opt-in Engineering skill packaging for Codex and Claude Code.

No downloads, subprocesses, account/config reads, agent runs or automatic updates.
Install is create-only and defaults to a plan. Existing skill directories stop it.
An interrupted copy is not a transaction: verify before use, preserve any edits,
and remove only the known partial addon directories before retrying. Not a sandbox.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'skills'
HOSTS = {'codex': '.agents/skills', 'claude': '.claude/skills'}
SKILLS = ('playbook-change-intelligence', 'playbook-decision-clarification',
          'playbook-browser-check', 'playbook-heavy-checks')
MAX_BYTES = 32768


class BundleError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def linked(path: Path) -> bool:
    return path.is_symlink() or (path.exists() and bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400))


def directory(path: Path) -> Path:
    path = path.expanduser()
    if linked(path):
        raise BundleError('Choose a real directory, not a link/junction')
    root = path.resolve(strict=True)
    if not root.is_dir() or root in (Path(root.anchor), Path.home().resolve()):
        raise BundleError('Choose a dedicated directory, not home or disk root')
    return root


def bounded(root: Path, relative: str) -> Path:
    parts = relative.split('/')
    if not relative or any(p in ('', '.', '..') for p in parts) or '\\' in relative or ':' in relative:
        raise BundleError('Invalid relative path')
    current = root
    for part in parts:
        current = current / part
        if linked(current):
            raise BundleError('Linked managed paths are not supported')
    return current


def selection(names: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    chosen = tuple(names) if names else SKILLS
    if len(set(chosen)) != len(chosen) or not set(chosen).issubset(SKILLS):
        raise BundleError('Unknown or duplicate skill selection')
    return chosen


def source_bytes(name: str, source: Path = SOURCE) -> bytes:
    if name not in SKILLS:
        raise BundleError('Unknown skill')
    path = bounded(directory(source), name + '/SKILL.md')
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise BundleError('Missing or oversized skill')
    data = path.read_bytes()
    text = data.decode('utf-8')
    match = re.fullmatch(r'---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n(.+)', text, re.S)
    if not match or match[1] != name or not 20 <= len(match[2]) <= 1024:
        raise BundleError('Expected portable name/description frontmatter')
    if len(match[3].strip()) < 200 or any(x in text for x in ('${CLAUDE', 'allowed-tools:', 'context: fork', '!`', 'Task tool', 'Skill tool')):
        raise BundleError('Empty skill or host-specific dependency in canonical source')
    return data


def payload(host: str, names=None, source: Path = SOURCE) -> dict[str, bytes]:
    if host not in HOSTS:
        raise BundleError('Unsupported host')
    files = {}
    for name in selection(names):
        data = source_bytes(name, source)
        prefix = HOSTS[host] + '/' + name + '/'
        if host == 'claude':
            data_for_host = data.replace(b'\n---\n', b'\ndisable-model-invocation: true\n---\n', 1)
        else:
            data_for_host = data
            files[prefix + 'agents/openai.yaml'] = b'policy:\n  allow_implicit_invocation: false\n'
        files[prefix + 'SKILL.md'] = data_for_host
        files[prefix + 'PLAYBOOK_ADDON.json'] = encoded({
            'schema': 'playbook.engineering-addon.v1', 'host': host, 'skill': name,
            'source_sha256': sha(data), 'invocation': 'explicit_only',
            'runtime_dependencies': 'not_installed', 'live_compatibility': 'not_tested_by_packager'})
    return files


def check() -> dict:
    result = {}
    for name in SKILLS:
        result[name] = sha(source_bytes(name))
    return {'status': 'source_contracts_valid', 'source_sha256': result,
            'live_hosts': 'NOT_RUN', 'usefulness': 'NOT_ESTABLISHED'}


def verify(root: Path, host: str, names=None) -> dict:
    root = directory(root)
    expected = payload(host, names)
    for relative, value in expected.items():
        path = bounded(root, relative)
        if not path.is_file() or path.stat().st_size > MAX_BYTES or path.read_bytes() != value:
            raise BundleError('Missing or changed addon file: ' + relative)
    for name in selection(names):
        folder = bounded(root, HOSTS[host] + '/' + name)
        actual = set()
        for path in folder.rglob('*'):
            relative = path.relative_to(root).as_posix()
            bounded(root, relative)
            if path.is_file():
                actual.add(relative)
            elif not path.is_dir():
                raise BundleError('Unexpected addon entry')
        wanted = {p for p in expected if p.startswith(HOSTS[host] + '/' + name + '/')}
        if actual != wanted:
            raise BundleError('Unexpected files in managed addon: ' + name)
    return {'status': 'files_match', 'host': host, 'skills': list(selection(names)),
            'live_host_execution': 'NOT_RUN'}


def install(root: Path, host: str, names=None, *, apply: bool = False) -> dict:
    root = directory(root)
    if root == HERE or root.is_relative_to(SOURCE):
        raise BundleError('Do not install into canonical addon sources')
    files = payload(host, names)
    for name in selection(names):
        dest = bounded(root, HOSTS[host] + '/' + name)
        if dest.exists():
            raise BundleError('Existing addon preserved; no overwrite: ' + name)
    for relative in files:
        path = bounded(root, relative)
        for parent in path.parents:
            if parent == root:
                break
            if parent.exists() and not parent.is_dir():
                raise BundleError('A required parent is not a directory')
    result = {'status': 'planned', 'host': host, 'skills': list(selection(names)),
              'paths': sorted(files), 'downloads': False, 'global_changes': False}
    if not apply:
        return result
    # Exclusive creation preserves unknown data. Concurrent editing/installing is
    # unsupported. A crash may leave a partial install; never claim it is atomic.
    for name in selection(names):
        dest = bounded(root, HOSTS[host] + '/' + name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        bounded(root, HOSTS[host])
        dest.mkdir(exist_ok=False)
        prefix = HOSTS[host] + '/' + name + '/'
        for relative, data in files.items():
            if relative.startswith(prefix):
                path = bounded(root, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(data)
    verify(root, host, names)
    return {**result, 'status': 'installed_files_verified', 'live_host_execution': 'NOT_RUN'}


def build(output: Path, host: str, names=None) -> dict:
    output = output.expanduser()
    if output.exists() or linked(output):
        raise BundleError('Output already exists; choose a fresh directory')
    # Validate first. This creates only a caller-chosen export, never host config.
    files = payload(host, names)
    parent = directory(output.parent)
    target = parent / output.name
    if target.is_relative_to(SOURCE):
        raise BundleError('Do not export into canonical sources')
    target.mkdir(exist_ok=False)
    install(target, host, names, apply=True)
    manifest = {'schema': 'playbook.engineering-bundle.v1', 'host': host,
                'files': {k: sha(v) for k, v in sorted(files.items())},
                'live_compatibility': 'NOT_RUN'}
    with (target / 'BUNDLE.json').open('xb') as stream:
        stream.write(encoded(manifest))
    return {'status': 'exported', 'host': host, 'files': len(files), 'manifest_sha256': sha(encoded(manifest))}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('check')
    sub.add_parser('doctor')
    for action in ('build', 'install', 'verify'):
        p = sub.add_parser(action)
        p.add_argument('--host', choices=tuple(HOSTS), required=True)
        p.add_argument('--skill', choices=SKILLS, action='append')
        p.add_argument('--output' if action == 'build' else '--project', type=Path, required=True)
        if action == 'install':
            p.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.action == 'check':
            result = check()
        elif args.action == 'doctor':
            result = {'status': 'presence_only', 'os': platform.system(),
                      'tools': {n: shutil.which(n) is not None for n in ('codex', 'claude', 'agent-browser', 'heavy')},
                      'auth': 'NOT_CHECKED', 'execution': 'NOT_RUN'}
        elif args.action == 'build':
            result = build(args.output, args.host, args.skill)
        elif args.action == 'install':
            result = install(args.project, args.host, args.skill, apply=args.apply)
        else:
            result = verify(args.project, args.host, args.skill)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({'status': 'blocked', 'reason': str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

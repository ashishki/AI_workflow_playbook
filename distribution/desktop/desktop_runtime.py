"""Opt-in, pinned Codex provisioning. Never changes global PATH, model or credentials.

Hashes are release-asset digests from openai/codex rust-v0.160.1, checked 2026-10-06.
Downloaded executable capability is separate from login, inference and review.
"""
from __future__ import annotations
import contextlib
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request

from setup_core import SetupError, digest, json_bytes, portable, strict_json, locked

VERSION = '0.160.1'
SOURCE = 'https://github.com/openai/codex/releases/download/rust-v0.160.1/'
ASSETS = {
    ('Darwin', 'arm64'): ('aarch64-apple-darwin', 129977637, 'f73527ee09c6db869acbb37b709866b339ea74ef91d2de255e9c74ec960c6314'),
    ('Darwin', 'x86_64'): ('x86_64-apple-darwin', 141316108, 'a98f330c9b1652cef2edc7bc2ee4c47a0fe19fa098b686381be3c8842abf0ac0'),
    ('Windows', 'x86_64'): ('x86_64-pc-windows-msvc', 157434529, '25c6fe4e46d5bff939312fc46de67ace37561f6f1f89b409af63fd8cc6098425'),
    ('Windows', 'arm64'): ('aarch64-pc-windows-msvc', 145421581, '844e17c492175ec62f8c11890ed89ef208d3502d2c79622c3be9876d2755f085'),
    ('Linux', 'x86_64'): ('x86_64-unknown-linux-musl', 160785122, '340801565906a7028f6baaa9ab6853addaef221f0016a1417a7c1ffdd96c21f0'),
    ('Linux', 'arm64'): ('aarch64-unknown-linux-musl', 150931915, 'dff0954438fa455c2197ddb1f421d8d68625d98de610f76bedb6e5bc837ea35b'),
}


def platform_key() -> tuple[str, str]:
    machine = platform.machine().lower()
    return platform.system(), {'amd64': 'x86_64', 'aarch64': 'arm64'}.get(machine, machine)


def base_dir() -> Path:
    # Fixed per-user area, deliberately not a configurable project path.
    if os.name == 'nt':
        return Path.home() / 'AppData' / 'Local' / 'Playbook' / 'tools'
    return Path.home() / '.local' / 'share' / 'playbook' / 'tools'


def checked_dir(path: Path) -> Path:
    for candidate in (path, *path.parents):
        if candidate.is_symlink() or (hasattr(candidate, 'is_junction') and candidate.is_junction()):
            raise SetupError('Runtime directory cannot contain links')
    return path


def target_dir() -> Path:
    system, arch = platform_key()
    if (system, arch) not in ASSETS:
        raise SetupError('No pinned Codex package for this OS/architecture')
    return checked_dir(base_dir() / f'codex-{VERSION}-{system}-{arch}')


def asset_plan() -> dict:
    spec, size, sha = ASSETS.get(platform_key(), (None, None, None))
    if spec is None:
        raise SetupError('Unsupported OS/architecture')
    return {'version': VERSION, 'url': SOURCE + 'codex-package-' + spec + '.tar.gz',
            'bytes': size, 'sha256': sha, 'destination': str(target_dir()),
            'scope': 'per-user, no administrator rights; no global PATH/config changes',
            'login': 'separate owner action', 'inference': 'not_started'}


class HTTPSOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        host = urllib.parse.urlparse(newurl)
        if host.scheme != 'https' or host.hostname not in {'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}:
            raise SetupError('Unexpected download redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url: str, dest: Path, size: int, sha: str) -> None:
    if not url.startswith(SOURCE) or size > 200 * 1024 * 1024:
        raise SetupError('Unsupported download')
    opener = urllib.request.build_opener(HTTPSOnly())
    count, value = 0, hashlib.sha256()
    deadline = time.monotonic() + 600
    with opener.open(url, timeout=30) as response, dest.open('xb') as output:
        while chunk := response.read(1024 * 1024):
            count += len(chunk)
            if time.monotonic() > deadline:
                raise SetupError('Download timed out; retry without changing protection')
            if count > size:
                raise SetupError('Download exceeds pinned size')
            output.write(chunk); value.update(chunk)
    if count != size or value.hexdigest() != sha:
        raise SetupError('Codex download failed checksum/size verification')


def extract_package(archive: Path, destination: Path) -> dict[str, str]:
    """No extractall: refuse links, devices, aliases and traversal before writing."""
    entries, keys, total = [], set(), 0
    with tarfile.open(archive, 'r:gz') as tar:
        for info in tar:
            name = info.name
            if name.startswith('./'):
                name = name[2:]
            name = name.rstrip('/') if info.isdir() else name
            if not name and info.isdir():
                continue
            key = portable(name)
            if key in keys or not (info.isfile() or info.isdir()) or info.size > 512 * 1024 * 1024:
                raise SetupError('Unsafe Codex archive entry')
            total += info.size
            if total > 1024 * 1024 * 1024 or len(entries) >= 5000:
                raise SetupError('Codex archive exceeds extraction bounds')
            keys.add(key); entries.append((info, name))
        files = {}
        for info, name in entries:
            path = destination / name
            if info.isdir():
                path.mkdir(parents=True, exist_ok=True, mode=0o700)
                continue
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            content = tar.extractfile(info)
            if content is None:
                raise SetupError('Unreadable archive entry')
            h = hashlib.sha256()
            with path.open('xb') as out:
                while chunk := content.read(1024 * 1024):
                    out.write(chunk); h.update(chunk)
            os.chmod(path, 0o700 if info.mode & 0o111 else 0o600)
            files[name] = h.hexdigest()
    return files


def provision(*, consent: bool = False) -> dict:
    if not consent:
        raise SetupError('Download and installation require explicit confirmation')
    details = asset_plan()
    target = target_dir()
    if target.exists():
        verified_binary()
        return {'status': 'already_installed', 'version': VERSION}
    parent = checked_dir(target.parent)
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # OS lock is released after a crash. A partial staging folder is never used.
    with locked(parent):
        if target.exists():
            verified_binary()
            return {'status': 'already_installed', 'version': VERSION}
        with tempfile.TemporaryDirectory(prefix='.download-', dir=parent) as tmp:
            tmp = Path(tmp)
            archive = tmp / 'codex.tar.gz'
            download(details['url'], archive, details['bytes'], details['sha256'])
            payload = tmp / 'payload'; payload.mkdir(mode=0o700)
            files = extract_package(archive, payload)
            wanted = 'codex.exe' if os.name == 'nt' else 'codex'
            binaries = [n for n in files if Path(n).name == wanted]
            if len(binaries) != 1:
                raise SetupError('Codex package layout is not supported')
            receipt = {'schema': 'playbook.runtime.v1', 'version': VERSION, 'archive_sha256': details['sha256'],
                       'source': details['url'], 'binary': binaries[0], 'files': files}
            (payload / 'PLAYBOOK-RUNTIME.json').write_bytes(json_bytes(receipt))
            if target.exists():
                raise SetupError('Runtime destination appeared during setup')
            os.rename(payload, target)
        verified_binary()
        return {'status': 'installed', 'version': VERSION, 'login': 'not_assessed', 'review': 'not_assessed'}



def verified_binary() -> Path | None:
    target = target_dir()
    if not target.exists():
        return None
    receipt_path = checked_dir(target / 'PLAYBOOK-RUNTIME.json')
    if not receipt_path.is_file() or receipt_path.stat().st_size > 2 * 1024 * 1024:
        raise SetupError('Missing runtime receipt')
    receipt = strict_json(receipt_path.read_bytes())
    details = asset_plan()
    if (receipt.get('schema') != 'playbook.runtime.v1' or receipt.get('archive_sha256') != details['sha256']
            or receipt.get('version') != VERSION or receipt.get('source') != details['url']):
        raise SetupError('Runtime receipt does not match the pinned release')
    files = receipt.get('files')
    if not isinstance(files, dict) or not files or len(files) > 5000 or receipt.get('binary') not in files:
        raise SetupError('Invalid runtime inventory')
    for name, expected in files.items():
        portable(name)
        path = checked_dir(target / name)
        if not path.is_file() or path.stat().st_nlink > 1:
            raise SetupError('Runtime file missing or linked')
        h = hashlib.sha256()
        with path.open('rb') as stream:
            while chunk := stream.read(1024 * 1024):
                h.update(chunk)
        if h.hexdigest() != expected:
            raise SetupError('Runtime file changed; do not execute it')
    actual = set()
    for path in target.rglob('*'):
        checked_dir(path)
        if path.is_file(): actual.add(path.relative_to(target).as_posix())
        elif not path.is_dir(): raise SetupError('Unexpected runtime entry')
    if actual != set(files) | {'PLAYBOOK-RUNTIME.json'}:
        raise SetupError('Unexpected runtime files')
    return target / receipt['binary']


def process_environment(binary: Path) -> dict[str, str]:
    env = os.environ.copy()
    env['PATH'] = str(binary.parent) + os.pathsep + env.get('PATH', '')
    # Do not override the user's model, permissions or auth configuration.
    return env


def probe() -> dict:
    binary = verified_binary()
    if binary is None:
        return {'codex': 'not_managed', 'auth': 'unknown', 'review': 'not_run', 'browser': 'not_run'}
    with tempfile.TemporaryDirectory(prefix='playbook-probe-') as cwd:
        try:
            run = subprocess.run([str(binary), '--version'], cwd=cwd, capture_output=True, timeout=15,
                                 env=process_environment(binary), check=False)
            if run.returncode:
                return {'codex': 'launch_failed', 'auth': 'unknown', 'review': 'not_run', 'browser': 'not_run'}
            auth = subprocess.run([str(binary), 'login', 'status'], cwd=cwd, capture_output=True, timeout=15,
                                  env=process_environment(binary), check=False)
            return {'codex': 'launched', 'version': VERSION,
                    'auth': 'cli_reports_login' if auth.returncode == 0 else 'not_confirmed',
                    'review': 'not_run', 'browser': 'not_run'}
        except (OSError, subprocess.TimeoutExpired):
            return {'codex': 'probe_failed', 'auth': 'unknown', 'review': 'not_run', 'browser': 'not_run'}


def login(*, consent: bool = False) -> dict:
    if not consent:
        raise SetupError('Login needs owner confirmation')
    binary = verified_binary()
    if binary is None:
        raise SetupError('Prepare the managed Codex runtime first')
    if probe().get('auth') == 'cli_reports_login':
        return {'login': 'cli_completed', 'review': 'not_run', 'account': 'existing_login_preserved'}
    # The standard CLI opens the provider's browser login. Never read auth.json,
    # copy tokens, change accounts or pass an API key on behalf of the owner.
    with tempfile.TemporaryDirectory(prefix='playbook-login-') as cwd:
        try:
            result = subprocess.run([str(binary), 'login'], cwd=cwd, env=process_environment(binary),
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=180, check=False)
        except subprocess.TimeoutExpired:
            return {'login': 'not_confirmed', 'next': 'Retry login; do not disable account restrictions'}
    return {'login': 'cli_completed' if result.returncode == 0 else 'not_confirmed', 'review': 'not_run'}

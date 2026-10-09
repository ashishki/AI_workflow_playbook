"""Bounded, offline project-local installer. No model, network or system configuration.

Only the two shipped skill namespaces and marked project instructions are managed.
The journal is an installation rollback, NOT a backup of the user's solution/data.
Do not run this concurrently with edits. Symlinks/junctions/hardlinks are refused;
a hostile process with the same OS identity is outside this local-user contract.
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from typing import Iterator

STATE = '.playbook-setup'
RECORD = STATE + '/install.json'
JOURNAL = STATE + '/journal.json'
RUNTIME = STATE + '/runtime.json'
PREFIXES = ('.agents/skills/playbook/', '.agents/skills/playbook-frontend/')
BEGIN = '<!-- PLAYBOOK-SETUP:BEGIN -->'
END = '<!-- PLAYBOOK-SETUP:END -->'
MAX_FILE = 4 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
MAX_FILES = 600
MAX_JOURNAL = 4 * MAX_TOTAL
VERSION = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
RESERVED = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)),
            *(f'lpt{i}' for i in range(1, 10))}


class SetupError(ValueError):
    """A safe stop; the caller should show the reason, never retry with force."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def strict_json(data: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise SetupError('Duplicate JSON key')
            result[key] = value
        return result
    try:
        value = json.loads(data, object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as exc:
        raise SetupError('Invalid JSON') from exc
    if not isinstance(value, dict):
        raise SetupError('Expected a JSON object')
    return value


def portable(name: str) -> str:
    if not isinstance(name, str) or not name or len(name) > 240 or '\\' in name:
        raise SetupError('Unsafe path')
    p = PurePosixPath(name)
    if p.is_absolute() or name != p.as_posix():
        raise SetupError('Non-canonical path')
    for part in p.parts:
        if part in {'.', '..'} or part.endswith((' ', '.')) or part.split('.')[0].casefold() in RESERVED:
            raise SetupError('Non-portable path')
        if any(c in '<>:"|?*' or unicodedata.category(c).startswith('C') for c in part):
            raise SetupError('Unsafe path character')
    return unicodedata.normalize('NFC', name).casefold()


def managed(name: str) -> bool:
    portable(name)
    return name in {'AGENTS.md', '.gitignore', RECORD, RUNTIME} or name.startswith(PREFIXES)


def project(path: Path) -> Path:
    path = Path(path).expanduser()
    if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
        raise SetupError('Choose a real project folder, not a link')
    root = path.resolve(strict=True)
    if not root.is_dir() or root == Path(root.anchor) or root == Path.home().resolve():
        raise SetupError('Choose a dedicated project folder, not home or a disk root')
    return root


def safe_path(root: Path, name: str) -> Path:
    portable(name)
    current = root
    for part in PurePosixPath(name).parts:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise SetupError('A managed path is a symlink or reparse point')
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise SetupError('A managed path is not a regular file/folder')
        if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
            raise SetupError('A managed file has hard links')
    return current


def read(root: Path, name: str) -> bytes | None:
    path = safe_path(root, name)
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > (MAX_JOURNAL if name == JOURNAL else MAX_FILE):
        raise SetupError('A managed file is a directory or too large')
    return path.read_bytes()


def atomic(root: Path, name: str, data: bytes | None) -> None:
    path = safe_path(root, name)
    if data is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = safe_path(root, name)
    old_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, temp = tempfile.mkstemp(prefix='.playbook-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, old_mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def privacy_guard(root: Path, directory: str) -> None:
    # Keep private diagnostics ignored even after uninstall/rollback restores the
    # owner's original top-level .gitignore. Never replace an unknown ignore file.
    path = directory + '/.gitignore'
    current = read(root, path)
    if current is not None and current.strip() != b'*':
        raise SetupError('Private metadata has custom ignore rules; review them before setup')
    if current is None:
        atomic(root, path, b'*\n')


@contextlib.contextmanager
def locked(root: Path) -> Iterator[None]:
    directory = safe_path(root, STATE)
    directory.mkdir(exist_ok=True, mode=0o700)
    privacy_guard(root, STATE)
    path = safe_path(root, STATE + '/lock')
    flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags, 0o600)
    stream = os.fdopen(fd, 'r+b')
    acquired = False
    try:
        if os.name == 'nt':
            import msvcrt
            if not path.stat().st_size:
                stream.write(b'0'); stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        acquired = True
        yield
    except OSError as exc:
        if not acquired:
            raise SetupError('Another setup operation is running') from exc
        raise
    finally:
        if acquired:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


@dataclass(frozen=True)
class Kit:
    version: str
    sha256: str
    files: dict[str, bytes]

    @classmethod
    def load(cls, source: Path, expected_sha256: str) -> 'Kit':
        # The pinned hash must come from the trusted distribution, not this ZIP.
        if not HASH.fullmatch(expected_sha256) or source.stat().st_size > MAX_TOTAL:
            raise SetupError('Invalid archive identity or size')
        raw = source.read_bytes()
        if digest(raw) != expected_sha256:
            raise SetupError('Archive checksum mismatch')
        content, keys = {}, set()
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                entries = z.infolist()
                if len(entries) > MAX_FILES or sum(i.file_size for i in entries) > MAX_TOTAL:
                    raise SetupError('Archive exceeds extraction limits')
                for info in entries:
                    if not info.filename.startswith('Playbook/') or info.is_dir():
                        raise SetupError('Unexpected archive layout')
                    name = info.filename[len('Playbook/'):]
                    key = portable(name)
                    mode = info.external_attr >> 16
                    if key in keys or (stat.S_IFMT(mode) not in {0, stat.S_IFREG}):
                        raise SetupError('Duplicate or non-regular archive entry')
                    if info.file_size > MAX_FILE or info.flag_bits & 1:
                        raise SetupError('Large or encrypted archive entry')
                    keys.add(key)
                    content[name] = z.read(info)
        except (zipfile.BadZipFile, RuntimeError) as exc:
            raise SetupError('Invalid archive') from exc
        manifest = strict_json(content.get('PACKAGE.json', b''))
        hashes = manifest.get('files')
        version = manifest.get('version')
        if manifest.get('product') != 'Playbook' or not isinstance(version, str) or len(version) > 80 or not VERSION.fullmatch(version):
            raise SetupError('Invalid Playbook manifest')
        if not isinstance(hashes, dict) or set(hashes) != set(content) - {'PACKAGE.json'}:
            raise SetupError('Manifest does not cover the exact archive')
        for name, value in hashes.items():
            if not isinstance(value, str) or digest(content[name]) != value:
                raise SetupError('Manifest file checksum mismatch')
        for name in ('Мой проект/AGENTS.md', 'RIGHTS.txt',
                     'Мой проект/.agents/skills/playbook/SKILL.md',
                     'Мой проект/.agents/skills/playbook-frontend/SKILL.md'):
            if name not in content:
                raise SetupError('Missing starter/rights file')
        # Reject file/directory aliases before writing anything.
        for name in content:
            parent = PurePosixPath(name).parent
            while parent != PurePosixPath('.'):
                if portable(parent.as_posix()) in keys:
                    raise SetupError('File/directory collision')
                parent = parent.parent
        return cls(version, expected_sha256, content)

    def skills(self) -> dict[str, bytes]:
        return {k[len('Мой проект/'):]: v for k, v in self.files.items()
                if k.startswith(tuple('Мой проект/' + p for p in PREFIXES))}


def version_key(value: str) -> tuple:
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        raise SetupError('Invalid installed version')
    core, separator, pre = value.split('+')[0].partition('-')
    parts = tuple((0, int(p)) if p.isdigit() else (1, p) for p in pre.split('.'))
    return (*map(int, core.split('.')), 0 if separator else 1, parts)


def block(text: bytes, old: bytes | None, new: bytes | None) -> bytes:
    """Replace only an exact previously-owned block, keeping surrounding bytes."""
    if old is not None:
        if text.count(old) != 1:
            raise SetupError('Managed instructions changed; resolve manually, never force')
        return text.replace(old, new or b'', 1)
    if BEGIN.encode() in text or END.encode() in text:
        raise SetupError('Unmanaged Playbook block already exists')
    return text + (new or b'')


def decode(value: str | None) -> bytes | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > MAX_FILE * 2:
        raise SetupError('Invalid journal content')
    try:
        data = base64.b64decode(value, validate=True)
    except ValueError as exc:
        raise SetupError('Invalid journal encoding') from exc
    if len(data) > MAX_FILE:
        raise SetupError('Oversized journal content')
    return data


def encode(value: bytes | None) -> str | None:
    return None if value is None else base64.b64encode(value).decode('ascii')


def installed(root: Path) -> dict | None:
    raw = read(root, RECORD)
    if raw is None:
        return None
    obj = strict_json(raw)
    if obj.get('schema') != 'playbook.install.v1' or not isinstance(obj.get('files'), dict):
        raise SetupError('Invalid installation record')
    for name, sha in obj['files'].items():
        if not name.startswith(PREFIXES) or not managed(name) or not isinstance(sha, str) or not HASH.fullmatch(sha):
            raise SetupError('Invalid owned file record')
    if len(obj['files']) > MAX_FILES or not isinstance(obj.get('preexisting'), dict):
        raise SetupError('Invalid installation inventory')
    for key in ('agents_block', 'ignore_block'):
        if not isinstance(obj.get(key), str):
            raise SetupError('Missing owned instruction block')
    if 'runtime_sha256' in obj and (not isinstance(obj['runtime_sha256'], str)
                                   or not HASH.fullmatch(obj['runtime_sha256'])):
        raise SetupError('Invalid helper pointer identity')
    return obj


def transaction_phase(root: Path) -> str:
    raw = read(root, JOURNAL)
    if raw is None:
        return 'missing'
    journal = strict_json(raw)
    phase = journal.get('status')
    if (journal.get('schema') != 'playbook.setup-transaction.v1'
            or journal.get('root') != str(root)
            or phase not in {'pending', 'complete', 'rolling_back', 'rolled_back'}):
        return 'invalid'
    return phase


def require_completed_transaction(root: Path, old: dict | None) -> None:
    phase = transaction_phase(root)
    if phase == 'missing' and old is None:
        return  # A genuinely unmanaged initial install has no journal yet.
    if phase not in {'complete', 'rolled_back'}:
        raise SetupError('An interrupted, missing or invalid transaction exists; preserve and resolve it before setup')


def runtime_pointer_status(root: Path, record: dict, expected_command: list[str] | None = None,
                           expected_kit_sha256: str | None = None) -> str:
    raw = read(root, RUNTIME)
    if raw is None:
        return 'missing'
    expected = record.get('runtime_sha256')
    if expected is None:
        # Older previews kept the exact owned bytes in their transaction only.
        # A completed rollback owns the BEFORE bytes; never trust a pending one.
        journal = strict_json(read(root, JOURNAL) or b'{}')
        phase = journal.get('status')
        entry = journal.get('changes', {}).get(RUNTIME) if isinstance(journal.get('changes'), dict) else None
        if (journal.get('schema') == 'playbook.setup-transaction.v1'
                and journal.get('root') == str(root) and phase in {'complete', 'rolled_back'}
                and isinstance(entry, dict)):
            previous = decode(entry.get('after' if phase == 'complete' else 'before'))
            expected = digest(previous) if previous is not None else None
    if expected is None:
        return 'unverified'
    if digest(raw) != expected:
        return 'modified'
    try:
        pointer = strict_json(raw)
    except SetupError:
        return 'modified'
    command = pointer.get('command')
    if (pointer.get('schema') != 'playbook.local-helper.v1' or pointer.get('version') != record['version']
            or not isinstance(command, list)
            or any(not isinstance(part, str) or not part.strip() or '\x00' in part for part in command)):
        return 'modified'
    if expected_command is not None and command != expected_command:
        return 'mismatch'
    if expected_kit_sha256 is not None and record.get('kit_sha256') != expected_kit_sha256:
        return 'mismatch'
    return 'verified' if command else 'not_configured'


@dataclass
class Plan:
    root: Path
    action: str
    before: dict[str, bytes | None]
    after: dict[str, bytes | None]

    def summary(self) -> dict:
        changes = [n for n in self.after if self.before[n] != self.after[n]]
        return {'action': self.action, 'files_changed': len(changes), 'paths': changes,
                'network': False, 'system_settings': False, 'solution_data': 'not_managed',
                'private_metadata': 'Local rollback journal and persistent privacy .gitignore guards remain'}


def plan(root: Path, kit: Kit, action: str, runtime_command: list[str] | None = None) -> Plan:
    root = project(root)
    if action not in {'install', 'update', 'remove'}:
        raise SetupError('Unsupported setup action')
    if action != 'remove' and safe_path(root, 'AGENTS.override.md').exists():
        raise SetupError('AGENTS.override.md is present; resolve the host instruction conflict first')
    old = installed(root)
    require_completed_transaction(root, old)
    if (action == 'install' and old) or (action != 'install' and not old):
        raise SetupError('Choose install for a new project, update/remove for a managed installation')
    if old:
        for name, sha in old['files'].items():
            value = read(root, name)
            if value is None or digest(value) != sha:
                raise SetupError('A Playbook file was modified or removed; preserve and resolve it first')
        if runtime_pointer_status(root, old) not in {'verified', 'not_configured'}:
            raise SetupError('The local helper pointer is missing, modified or unverified; preserve and resolve it first')
    # A foreign file in our skill namespace can affect host behavior. Preserve it
    # and stop rather than claiming an exact or complete installation/removal.
    for prefix in PREFIXES:
        namespace = safe_path(root, prefix.rstrip('/'))
        if namespace.exists():
            if not namespace.is_dir():
                raise SetupError('A skill namespace is not a directory')
            for entry in namespace.rglob('*'):
                name = entry.relative_to(root).as_posix()
                safe_path(root, name)
                if entry.is_file() and (not old or name not in old['files']):
                    raise SetupError('Unmanaged files exist in a Playbook skill; preserve and resolve them first')
    if old and action == 'update':
        if old['version'] == kit.version and old['kit_sha256'] != kit.sha256:
            raise SetupError('Different payload has the same version; obtain a new version')
        if version_key(kit.version) < version_key(old['version']):
            raise SetupError('Downgrade refused; use explicit installation rollback')
    new_skills = {} if action == 'remove' else kit.skills()
    before, after = {}, {}
    for name in sorted(set(new_skills) | set(old['files'] if old else {})):
        before[name] = read(root, name)
        if (not old or name not in old['files']) and before[name] is not None:
            raise SetupError('An unmanaged skill would be overwritten')
        after[name] = new_skills.get(name)
    # Unknown files are preserved, but may conflict with a new file/directory.
    for name in after:
        safe_path(root, name)
    agents = read(root, 'AGENTS.md')
    ignore = read(root, '.gitignore')
    agents_block = ('\n' + BEGIN + '\n' + kit.files['Мой проект/AGENTS.md'].decode('utf-8').rstrip()
                    + '\nSetup/continuation: read `.agents/skills/playbook/references/setup.md` when needed.\n'
                    + 'Local helper location (not authorization): `.playbook-setup/runtime.json`.\n'
                    + END + '\n').encode('utf-8')
    ignore_block = b'\n# PLAYBOOK-SETUP:BEGIN\n.playbook-setup/\n.playbook-artifacts/\n# PLAYBOOK-SETUP:END\n'
    for name, current, key, replacement in [('AGENTS.md', agents, 'agents_block', agents_block),
                                          ('.gitignore', ignore, 'ignore_block', ignore_block)]:
        old_block = old[key].encode('utf-8') if old else None
        result = block(current or b'', old_block, None if action == 'remove' else replacement)
        before[name] = current
        # Delete only a file which was absent before installation and now empty.
        existed = old.get('preexisting', {}).get(name, True) if old else current is not None
        after[name] = None if action == 'remove' and not existed and not result else result
    before[RECORD], before[RUNTIME] = read(root, RECORD), read(root, RUNTIME)
    if action == 'remove':
        after[RECORD] = after[RUNTIME] = None
    else:
        runtime_bytes = json_bytes({'schema': 'playbook.local-helper.v1',
                                   'command': runtime_command or [], 'version': kit.version,
                                   'meaning': 'Machine-local location, not action authority; reconfigure after transfer.'})
        info = {'schema': 'playbook.install.v1', 'version': kit.version, 'kit_sha256': kit.sha256,
                'files': {n: digest(v) for n, v in new_skills.items()},
                'runtime_sha256': digest(runtime_bytes),
                'agents_block': agents_block.decode('utf-8'), 'ignore_block': ignore_block.decode('utf-8'),
                'preexisting': old['preexisting'] if old else {'AGENTS.md': agents is not None, '.gitignore': ignore is not None}}
        after[RECORD] = json_bytes(info)
        after[RUNTIME] = runtime_bytes
    return Plan(root, action, before, after)


def apply(proposal: Plan, *, consent: bool = False) -> dict:
    if not consent:
        raise SetupError('Explicit confirmation is required')
    root = project(proposal.root)
    if set(proposal.before) != set(proposal.after) or any(not managed(n) for n in proposal.after):
        raise SetupError('Invalid setup plan')
    with locked(root):
        require_completed_transaction(root, installed(root))
        for name, expected in proposal.before.items():
            if read(root, name) != expected:
                raise SetupError('Project changed after the plan; inspect and plan again')
        changes = {n: {'before': encode(proposal.before[n]), 'after': encode(v)}
                   for n, v in proposal.after.items() if proposal.before[n] != v}
        if not changes:
            return {'status': 'unchanged', 'action': proposal.action}
        privacy_guard(root, '.playbook-artifacts')
        journal = {'schema': 'playbook.setup-transaction.v1', 'root': str(root),
                   'action': proposal.action, 'status': 'pending', 'changes': changes,
                   'meaning': 'Installation files only; not user data recovery.'}
        if len(json_bytes(journal)) > MAX_JOURNAL:
            raise SetupError('Setup transaction exceeds the rollback budget')
        atomic(root, JOURNAL, json_bytes(journal))
        # A crash/failure leaves a journal. Rollback is explicit, never destructive retry.
        for name in changes:
            if read(root, name) != proposal.before[name]:
                raise SetupError('Concurrent edit; stop and inspect the setup journal')
            atomic(root, name, proposal.after[name])
        for name in changes:
            if read(root, name) != proposal.after[name]:
                raise SetupError('Post-install verification failed')
        journal['status'] = 'complete'
        atomic(root, JOURNAL, json_bytes(journal))
    return {'status': 'complete', **proposal.summary(), 'application_readiness': 'not_assessed'}


def rollback(root: Path, *, consent: bool = False) -> dict:
    if not consent:
        raise SetupError('Explicit confirmation is required')
    root = project(root)
    with locked(root):
        j = strict_json(read(root, JOURNAL) or b'')
        if j.get('schema') != 'playbook.setup-transaction.v1' or j.get('root') != str(root):
            raise SetupError('Transaction belongs to another project or is invalid')
        if j.get('status') not in {'pending', 'complete', 'rolling_back', 'rolled_back'}:
            raise SetupError('Invalid transaction status')
        if j.get('status') == 'rolled_back':
            return {'status': 'already_rolled_back'}
        changes = j.get('changes')
        if not isinstance(changes, dict) or not changes or len(changes) > MAX_FILES:
            raise SetupError('Invalid transaction')
        decoded = {}
        for name, values in changes.items():
            if not managed(name) or not isinstance(values, dict) or set(values) != {'before', 'after'}:
                raise SetupError('Invalid transaction entry')
            before, after = decode(values['before']), decode(values['after'])
            if read(root, name) not in (before, after):
                raise SetupError('A file changed after setup; rollback would overwrite work')
            decoded[name] = before, after
        j['status'] = 'rolling_back'
        atomic(root, JOURNAL, json_bytes(j))
        for name, (before, after) in reversed(list(decoded.items())):
            if read(root, name) not in (before, after):
                raise SetupError('Concurrent edit during rollback')
            atomic(root, name, before)
        if any(read(root, n) != pair[0] for n, pair in decoded.items()):
            raise SetupError('Rollback verification failed')
        j['status'] = 'rolled_back'
        atomic(root, JOURNAL, json_bytes(j))
    return {'status': 'rolled_back', 'solution_data': 'not_restored_or_modified'}


def installation_status(root: Path, *, expected_command: list[str] | None = None,
                        expected_kit_sha256: str | None = None) -> dict:
    root = project(root)
    raw = read(root, JOURNAL)
    phase = transaction_phase(root)
    interrupted = phase not in {'complete', 'rolled_back'}
    old = installed(root)
    if not old:
        return {'installation': 'interrupted' if raw and interrupted else 'not_managed',
                'version': None, 'setup_transaction': phase, 'setup_readiness': 'not_ready'}
    modified = [n for n, sha in old['files'].items() if (value := read(root, n)) is None or digest(value) != sha]
    for name, key in (('AGENTS.md', 'agents_block'), ('.gitignore', 'ignore_block')):
        value = read(root, name)
        if value is None or value.count(old[key].encode('utf-8')) != 1:
            modified.append(name)
    for prefix in PREFIXES:
        namespace = safe_path(root, prefix.rstrip('/'))
        if namespace.is_dir():
            for entry in namespace.rglob('*'):
                name = entry.relative_to(root).as_posix()
                safe_path(root, name)
                if entry.is_file() and name not in old['files']:
                    modified.append(name)
    pointer = runtime_pointer_status(root, old, expected_command, expected_kit_sha256)
    if pointer in {'missing', 'modified', 'mismatch'}:
        modified.append(RUNTIME)
    status = ('interrupted' if interrupted else 'modified' if modified else
              'unverified' if pointer == 'unverified' else 'files_verified')
    return {'installation': status, 'version': old['version'],
            'modified_count': len(modified), 'setup_transaction': phase, 'helper_pointer': pointer,
            'setup_readiness': 'installation_verified' if status == 'files_verified' and pointer == 'verified' else 'not_ready',
            'model_browser_review': 'not_assessed', 'business_effect': 'not_assessed'}

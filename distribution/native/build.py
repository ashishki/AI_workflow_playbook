#!/usr/bin/env python3
"""Build a small, offline pilot kit. No installation, network or publication."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import tempfile
import unicodedata
import zipfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_runtime import sync

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'plugins/playbook-native'
WINDOWS_ILLEGAL_MEMBER_CHARS = frozenset('<>:"|?*')
VERSION_IDENTIFIER = re.compile(r'[0-9A-Za-z-]+')
FIRST_README = '''# Мой первый проект

Эту папку можно открыть в Codex и описать свою задачу. Playbook уже находится
в папке проекта. Настраивать инструменты или копировать скрытые файлы не нужно.

Пока здесь нет приложения. Попросите Codex сделать первый полезный результат.
После работы попросите показать, что получилось, что проверено и что осталось.
Чтобы продолжить завтра, откройте эту же папку в Codex.
'''


def validate_member_name(name):
    """Reject a generated ZIP member name that is unsafe for any extractor.

    ``ZipFile`` writes names verbatim. A backslash is an ordinary character on
    this host but can be a directory separator for a recipient on Windows, so
    checking ``Path.relative_to`` here would not be sufficient. Every payload
    member is deliberately relative to the single ``Playbook`` extraction root
    added by ``build`` below.
    """
    if not isinstance(name, str) or not name:
        raise ValueError('Archive member name must be a non-empty string')
    if '\\' in name or '\x00' in name:
        raise ValueError(f'Unsafe archive member name: {name!r}')
    posix = PurePosixPath(name)
    windows = PureWindowsPath(name)
    if posix.is_absolute() or windows.root or windows.drive:
        raise ValueError(f'Archive member name must be relative: {name!r}')
    parts = name.split('/')
    # Win32 removes trailing spaces and dots from a component. On this host
    # ``".. "`` is a legal literal name, but a Windows extractor can read it as
    # ``".."`` and thereby traverse outside the archive root.
    if (any(part in ('', '.', '..') or part.startswith(' ') or part.endswith(('.', ' ')) for part in parts)
            or any(WINDOWS_ILLEGAL_MEMBER_CHARS.intersection(part) for part in parts)
            or any(ord(character) < 32 for part in parts for character in part)
            or any(PureWindowsPath(part).is_reserved() for part in parts)):
        raise ValueError(f'Unsafe archive member name: {name!r}')
    # With the checks above, this construction cannot escape its only intended
    # root. Keep the assertion explicit so future callers cannot silently add
    # an absolute or traversal name to the payload.
    final = PurePosixPath('Playbook', *parts)
    if final.parts[0] != 'Playbook':
        raise ValueError(f'Archive member escapes package root: {name!r}')


def validate_payload_names(payload):
    """Validate portable ZIP names and reject cross-platform collisions."""
    destinations = {}
    for name in payload:
        validate_member_name(name)
        # Illegal Win32 characters, trailing dots/spaces and alternate
        # separators have already been rejected. The remaining common
        # cross-platform destination mapping is Unicode normalization plus
        # case-insensitivity; retaining two names would silently overwrite one
        # member after extraction on macOS or Windows.
        destination = tuple(unicodedata.normalize('NFC', part).casefold() for part in name.split('/'))
        for existing, previous in destinations.items():
            overlap = min(len(existing), len(destination))
            if existing[:overlap] == destination[:overlap]:
                raise ValueError(f'Archive members collide after extraction: {previous!r} and {name!r}')
        destinations[destination] = name


def open_checksum(path):
    """Create the sidecar exclusively, ready for binary reproducible output."""
    return path.open('x+b')


def write_checksum(handle, contents):
    """Write the ASCII checksum through the exclusively-created descriptor."""
    handle.write(contents.encode('ascii'))
    handle.flush()


def hash_open_file(handle):
    """Return the digest and size of the same file descriptor we just wrote."""
    handle.flush()
    size = handle.seek(0, 2)
    handle.seek(0)
    digest = hashlib.sha256()
    while chunk := handle.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest(), size


def verify_archive_identity(path, expected):
    """Refuse to publish a checksum if the exclusive archive was replaced."""
    try:
        current = os.stat(path, follow_symlinks=False)
    except FileNotFoundError as error:
        raise RuntimeError('Archive disappeared before checksum publication') from error
    if not os.path.samestat(current, expected):
        raise RuntimeError('Archive was replaced before checksum publication')


def read_open_file(handle):
    """Read the complete contents through the already-open file descriptor."""
    handle.flush()
    handle.seek(0)
    return handle.read()


def publish_staged_file(source, target):
    """Link a completed staged artifact into place without replacing a target."""
    os.link(source, target)



def validate_version(value):
    """Return a bounded portable SemVer token suitable for a filename."""
    if not isinstance(value, str) or len(value) > 80:
        raise ValueError(f'Plugin version is not a portable SemVer token: {value!r}')
    core_and_pre,separator,build=value.partition('+')
    if value.count('+') > 1 or (separator and (not build or any(not VERSION_IDENTIFIER.fullmatch(part) for part in build.split('.')))):
        raise ValueError(f'Plugin version is not a portable SemVer token: {value!r}')
    core,separator,prerelease=core_and_pre.partition('-')
    numeric=core.split('.')
    if len(numeric) != 3 or any(not part.isascii() or not part.isdigit() or (len(part) > 1 and part.startswith('0')) for part in numeric):
        raise ValueError(f'Plugin version is not a portable SemVer token: {value!r}')
    if separator:
        identifiers=prerelease.split('.')
        if (not prerelease or any(not VERSION_IDENTIFIER.fullmatch(part) or (part.isdigit() and len(part) > 1 and part.startswith('0')) for part in identifiers)):
            raise ValueError(f'Plugin version is not a portable SemVer token: {value!r}')
    return value


def remove_staging_directory(staging):
    """Remove only the two private staging aliases before public revalidation."""
    for entry in staging.iterdir():
        entry.chmod(0o600)
        entry.unlink()
    staging.rmdir()


def collect():
    if sync(check=True):
        raise ValueError('Packaged Role Runner is stale; run distribution/native/sync_runtime.py')
    payload = {}
    for p in sorted(PACKAGE.rglob('*')):
        if p.is_symlink():
            raise ValueError(f'Symlink is not a distributable package file: {p}')
        if p.is_file():
            if '__pycache__' in p.parts or p.suffix == '.pyc':
                continue
            relative = p.relative_to(PACKAGE).as_posix()
            if relative != '.codex-plugin/plugin.json' and not relative.startswith('skills/'):
                continue
            payload['plugins/playbook-native/' + relative] = p.read_bytes()
            if relative.startswith('skills/'):
                payload['Мой проект/.agents/' + relative] = p.read_bytes()
    payload['Мой проект/AGENTS.md'] = (PACKAGE / 'skills/playbook/assets/project-block.md').read_bytes()
    payload['Мой проект/README.md'] = FIRST_README.encode()
    payload['Мой проект/.gitignore'] = b'.playbook-artifacts/\n__pycache__/\n'
    payload['START.html'] = (ROOT / 'docs/native/start.html').read_text(encoding='utf-8').replace('data-kit="source"', 'data-kit="archive"').encode()
    payload['RIGHTS.txt'] = (ROOT / 'docs/LEGAL_STATUS.md').read_bytes()
    payload['НАЧНИТЕ ЗДЕСЬ.txt'] = '''Откройте Codex, выберите папку «Мой проект» и опишите свою задачу.
Нужно приложение ChatGPT на компьютере: войдите в аккаунт и выберите Codex.
Для первой пробы выберите в Codex папку «Мой проект» из этого распакованного архива.
Playbook уже лежит внутри этой папки. Опишите задачу в чате Codex.
START.html — необязательная помощь с запуском и примерами задач.
Копировать запрос со страницы не требуется: можно сразу написать его в Codex.

Это пробный комплект для разрешённого тестирования. Публичный выпуск и права
распространения ещё не оформлены. См. RIGHTS.txt. Архив ничего не устанавливает
глобально, не запускает код автоматически и не содержит учётных данных.
'''.encode()
    # Validate every future archive member before the manifest is constructed.
    validate_payload_names((*payload, 'PACKAGE.json'))
    version = validate_version(json.loads((PACKAGE / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))['version'])
    manifest = {'product':'Playbook','version':version,'status':'private-evaluation-preview',
                'files':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(payload.items())}}
    payload['PACKAGE.json'] = (json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    return version,payload

def build(output):
    version,payload = collect()
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    archive = output / f'Playbook-{version}.zip'
    checksum_path = archive.with_suffix('.zip.sha256')
    if archive.parent != output or checksum_path.parent != output:
        raise ValueError('Derived archive paths must remain directly under the output directory')
    if archive.exists() or checksum_path.exists():
        raise FileExistsError('Refusing to replace an existing archive or checksum')
    # Build and validate both artifacts in a private staging directory. Final
    # names appear only after both descriptor-bound validations have passed.
    staging = Path(tempfile.mkdtemp(prefix=f'.{archive.name}.',dir=output))
    published = False
    try:
        staged_archive = staging / archive.name
        staged_checksum = staging / checksum_path.name
        with staged_archive.open('x+b') as dest:
            with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
                for name,content in sorted(payload.items()):
                    info=zipfile.ZipInfo('Playbook/'+name,date_time=(2026,9,19,0,0,0))
                    info.create_system=3  # Stable Unix metadata, also when built on Windows.
                    info.compress_type=zipfile.ZIP_DEFLATED
                    info.external_attr=0o100644 << 16
                    z.writestr(info,content)
            sha,archive_bytes=hash_open_file(dest)
        checksum_bytes=f'{sha}  {archive.name}\n'.encode('ascii')
        with open_checksum(staged_checksum) as sidecar:
            write_checksum(sidecar, checksum_bytes.decode('ascii'))
        # Do not expose write-capable descriptors or writable inodes at the
        # publication boundary. The final validation uses read-only handles.
        staged_archive.chmod(0o444)
        staged_checksum.chmod(0o444)
        with staged_archive.open('rb') as dest, staged_checksum.open('rb') as sidecar:
            expected_archive=os.fstat(dest.fileno())
            expected_checksum=os.fstat(sidecar.fileno())
            final_sha,final_bytes=hash_open_file(dest)
            if (final_sha,final_bytes) != (sha,archive_bytes):
                raise RuntimeError('Archive changed before publication')
            verify_archive_identity(staged_archive, expected_archive)
            verify_archive_identity(staged_checksum, expected_checksum)
            if read_open_file(sidecar) != checksum_bytes:
                raise RuntimeError('Checksum changed before publication')
            # Hold validated read-only descriptors open until their links are
            # created. A failed second link deliberately leaves no rollback
            # race that could delete a file created by somebody else.
            if archive.exists() or checksum_path.exists():
                raise FileExistsError('Refusing to replace an existing archive or checksum')
            publish_staged_file(staged_archive, archive)
            verify_archive_identity(archive, expected_archive)
            try:
                publish_staged_file(staged_checksum, checksum_path)
                verify_archive_identity(checksum_path, expected_checksum)
            except Exception:
                raise RuntimeError('Archive published but checksum publication failed; preserving both paths')
            # A hard link shares the inode. Revalidate descriptor-bound bytes
            # after both public names exist, not merely their identities.
            published_sha,published_bytes=hash_open_file(dest)
            if (published_sha,published_bytes) != (sha,archive_bytes):
                raise RuntimeError('Archive changed after publication')
            verify_archive_identity(archive, expected_archive)
            if read_open_file(sidecar) != checksum_bytes:
                raise RuntimeError('Checksum changed after publication')
            verify_archive_identity(checksum_path, expected_checksum)
        published = True
    finally:
        remove_staging_directory(staging)
    if not published:
        raise RuntimeError('Artifacts were not published')
    # On Windows, a hard link shares the read-only attribute with the staging
    # alias. Explicit cleanup above can temporarily clear it, so restore it on
    # final paths and then perform the last public-path validation.
    archive.chmod(0o444)
    checksum_path.chmod(0o444)
    with archive.open('rb') as final_archive, checksum_path.open('rb') as final_checksum:
        final_sha,final_bytes=hash_open_file(final_archive)
        if (final_sha,final_bytes) != (sha,archive_bytes):
            raise RuntimeError('Archive changed after staging cleanup')
        if read_open_file(final_checksum) != checksum_bytes:
            raise RuntimeError('Checksum changed after staging cleanup')
        verify_archive_identity(archive, os.fstat(final_archive.fileno()))
        verify_archive_identity(checksum_path, os.fstat(final_checksum.fileno()))
    return {'archive':str(archive.resolve()),'sha256':sha,'files':len(payload),'bytes':archive_bytes}

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    print(json.dumps(build(ap.parse_args().output),ensure_ascii=False))

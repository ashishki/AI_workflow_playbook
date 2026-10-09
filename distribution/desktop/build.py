#!/usr/bin/env python3
"""Build OS-specific private-evaluation desktop setup bundles."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NATIVE = ROOT / 'distribution' / 'native' / 'build.py'
FIXED_TIME = (2026, 10, 6, 0, 0, 0)


def load_native():
    spec = importlib.util.spec_from_file_location('desktop_native_build', NATIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def linux_tk_binaries() -> list[Path]:
    """Resolve Tcl/Tk even when standalone Python keeps them outside ldconfig."""
    if platform.system() != 'Linux':
        return []
    import _tkinter
    from PyInstaller.depend.bindepend import get_imports
    imports = get_imports(_tkinter.__file__, search_paths=[str(Path(sys.base_prefix) / 'lib')])
    libraries = []
    for name, source in sorted(imports):
        if not Path(name).name.lower().startswith(('libtcl', 'libtk')):
            continue
        if source is None:
            raise RuntimeError(f'Cannot bundle a required Tcl/Tk library: {name}')
        libraries.append(Path(source))
    return libraries


def run_pyinstaller(name: str, *, windowed: bool, data: Path, stage: Path) -> None:
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
            '--name', name, '--distpath', str(stage / 'dist'),
            '--workpath', str(stage / ('work-' + name)),
            '--specpath', str(stage / ('spec-' + name)),
            '--add-data', str(data / 'Playbook.zip') + os.pathsep + 'data',
            '--add-data', str(data / 'bundle.json') + os.pathsep + 'data',
            '--hidden-import', 'secrets', '--hidden-import', 'signal',
            '--hidden-import', 'dataclasses', '--hidden-import', 'datetime',
            '--hidden-import', 'typing', '--hidden-import', 'importlib.util']
    for library in linux_tk_binaries():
        args += ['--add-binary', str(library) + os.pathsep + '.']
    if windowed:
        args.append('--windowed')
    args.append(str(HERE / 'desktop_setup.py'))
    subprocess.run(args, cwd=ROOT, check=True, timeout=900)


def safe_link_target(path: Path, root: Path) -> bytes:
    target = os.readlink(path)
    candidate = (path.parent / target).resolve(strict=False)
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f'Bundle symlink escapes artifact root: {path}') from exc
    return target.encode('utf-8')


def collect_artifact(path: Path, prefix: str) -> list[tuple[str, bytes, int]]:
    result = []
    if path.is_symlink():
        return [(prefix, safe_link_target(path, path.parent), stat.S_IFLNK | 0o777)]
    if path.is_file():
        return [(prefix, path.read_bytes(), stat.S_IFREG | (0o755 if os.access(path, os.X_OK) else 0o644))]
    if not path.is_dir():
        raise ValueError(f'Unsupported build artifact: {path}')
    root = path.parent
    for item in sorted(path.rglob('*')):
        relative = item.relative_to(root).as_posix()
        if item.is_symlink():
            result.append((relative, safe_link_target(item, root), stat.S_IFLNK | 0o777))
        elif item.is_file():
            result.append((relative, item.read_bytes(), stat.S_IFREG | (0o755 if os.access(item, os.X_OK) else 0o644)))
    return result


def build(output: Path) -> dict:
    native = load_native()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='playbook-desktop-build-') as tmp:
        stage = Path(tmp)
        native_result = native.build(stage / 'native')
        native_zip = Path(native_result['archive'])
        data = stage / 'data'
        data.mkdir()
        shutil.copy2(native_zip, data / 'Playbook.zip')
        with zipfile.ZipFile(native_zip) as native_archive:
            version = json.loads(native_archive.read('Playbook/PACKAGE.json'))['version']
        (data / 'bundle.json').write_text(json.dumps({
            'schema': 'playbook.desktop-bundle.v1',
            'version': version,
            'sha256': native_result['sha256'],
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

        run_pyinstaller('playbook-helper', windowed=False, data=data, stage=stage)
        run_pyinstaller('Playbook-Setup', windowed=True, data=data, stage=stage)

        dist = stage / 'dist'
        helper = dist / ('playbook-helper.exe' if os.name == 'nt' else 'playbook-helper')
        app = dist / 'Playbook-Setup.app'
        setup = app if app.exists() else dist / ('Playbook-Setup.exe' if os.name == 'nt' else 'Playbook-Setup')
        if not helper.is_file() or not setup.exists():
            raise RuntimeError('PyInstaller did not produce the expected setup artifacts')

        smoke = subprocess.run([str(helper), 'self-test'], cwd=stage, capture_output=True,
                               text=True, encoding='utf-8', timeout=120, check=True)
        smoke_result = json.loads(smoke.stdout.strip().splitlines()[-1])
        if smoke_result.get('status') != 'passed':
            raise RuntimeError('Frozen helper self-test did not pass')

        system = platform.system().lower()
        arch = platform.machine().lower().replace('amd64', 'x86_64').replace('aarch64', 'arm64')
        archive = output / f'Playbook-Desktop-{version}-{system}-{arch}.zip'
        checksum = archive.with_suffix('.zip.sha256')
        if archive.exists() or checksum.exists():
            raise FileExistsError('Refusing to overwrite a desktop bundle')

        files = []
        files += collect_artifact(helper, helper.name)
        files += collect_artifact(setup, setup.name)
        files.append((native_zip.name, native_zip.read_bytes(), stat.S_IFREG | 0o644))
        files.append(('RIGHTS.txt', (ROOT / 'docs' / 'LEGAL_STATUS.md').read_bytes(), stat.S_IFREG | 0o644))
        readme = (
            'Playbook — private evaluation preview\n\n'
            '1. Keep all files from this archive together.\n'
            '2. Open Playbook-Setup and select a dedicated work folder.\n'
            '3. The setup window does not run a model or publish anything by itself.\n'
            '4. The included Playbook ZIP is a manual fallback, not a second installation source.\n\n'
            'The binaries are preview artifacts and are not code-signed/notarized here. '
            'Do not weaken operating-system security to run them.\n'
        ).encode('utf-8')
        files.append(('README.txt', readme, stat.S_IFREG | 0o644))
        keys = [name.casefold() for name, _, _ in files]
        if len(keys) != len(set(keys)):
            raise RuntimeError('Desktop bundle contains colliding paths')

        manifest = {'schema': 'playbook.desktop-artifact.v1', 'version': version,
                    'os': system, 'arch': arch, 'native_kit_sha256': native_result['sha256'],
                    'frozen_self_test': smoke_result,
                    'files': {name: hashlib.sha256(data_bytes).hexdigest()
                              for name, data_bytes, _ in files}}
        files.append(('DESKTOP.json',
                      (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'),
                      stat.S_IFREG | 0o644))

        with archive.open('xb') as raw:
            with zipfile.ZipFile(raw, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for name, data_bytes, mode in sorted(files):
                    info = zipfile.ZipInfo(name, FIXED_TIME)
                    info.create_system = 3
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = mode << 16
                    z.writestr(info, data_bytes)

        archive_sha = sha(archive)
        checksum.write_text(f'{archive_sha}  {archive.name}\n', encoding='ascii')
        return {'archive': str(archive.resolve()), 'sha256': archive_sha, 'version': version,
                'os': system, 'arch': arch, 'frozen_self_test': smoke_result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), ensure_ascii=False))

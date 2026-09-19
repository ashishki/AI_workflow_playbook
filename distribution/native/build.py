#!/usr/bin/env python3
"""Build a small, offline pilot kit. No installation, network or publication."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_runtime import sync

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'plugins/playbook-native'
FIRST_README = '''# Мой первый проект

Эту папку можно открыть в Codex и описать свою задачу. Playbook уже находится
в папке проекта. Настраивать инструменты или копировать скрытые файлы не нужно.

Пока здесь нет приложения. Попросите Codex сделать первый полезный результат.
После работы попросите показать, что получилось, что проверено и что осталось.
Чтобы продолжить завтра, откройте эту же папку в Codex.
'''

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
    payload['НАЧНИТЕ ЗДЕСЬ.txt'] = '''Откройте START.html двойным щелчком.
Нужно приложение ChatGPT на компьютере: войдите в аккаунт и выберите Codex.
Для первой пробы выберите в Codex папку «Мой проект» из этого распакованного архива.
Playbook уже лежит внутри этой папки. Опишите задачу в чате Codex.
START.html — инструкция; сама страница не запускает агента.

Это пробный комплект для разрешённого тестирования. Публичный выпуск и права
распространения ещё не оформлены. См. RIGHTS.txt. Архив ничего не устанавливает
глобально, не запускает код автоматически и не содержит учётных данных.
'''.encode()
    version = json.loads((PACKAGE / '.codex-plugin/plugin.json').read_text(encoding='utf-8'))['version']
    manifest = {'product':'Playbook','version':version,'status':'private-evaluation-preview',
                'files':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(payload.items())}}
    payload['PACKAGE.json'] = (json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    return version,payload

def build(output):
    version,payload = collect()
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    archive = output / f'Playbook-{version}.zip'
    if archive.with_suffix('.zip.sha256').exists():
        raise FileExistsError('Refusing to replace an existing archive checksum')
    # Exclusive creation protects previously shared pilot artifacts.
    with archive.open('xb') as dest:
        with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name,content in sorted(payload.items()):
                info=zipfile.ZipInfo('Playbook/'+name,date_time=(2026,9,19,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644 << 16
                z.writestr(info,content)
    sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{sha}  {archive.name}\n')
    return {'archive':str(archive.resolve()),'sha256':sha,'files':len(payload),'bytes':archive.stat().st_size}

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    print(json.dumps(build(ap.parse_args().output),ensure_ascii=False))

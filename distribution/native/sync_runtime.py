#!/usr/bin/env python3
"""Ship exact canonical helper copies; never maintain a second engine."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'plugins/playbook-native/skills/playbook/scripts'
FILES = ('run_codex_role.py', 'codex_role_run_lib.py', 'solution_record.py')


def sync(check=False):
    stale = []
    for name in FILES:
        source, target = ROOT / 'tools' / name, SCRIPTS / name
        content = source.read_bytes()
        if target.is_symlink():
            raise ValueError(f'Refusing a symlinked runtime file: {target}')
        if not target.exists() or target.read_bytes() != content:
            stale.append(name)
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    return stale


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = sync(args.check)
    print('Runtime copies: ' + (', '.join(stale) if stale else 'current'))
    raise SystemExit(bool(stale) if args.check else 0)

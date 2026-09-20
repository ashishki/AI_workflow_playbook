#!/usr/bin/env python3
"""Check vNext ownership, lifecycle delivery and compatibility, without inference.

This validates source/package contracts, not agent behavior or business usefulness.
The inventory uses all Git tracked paths. It never scans a home directory or moves files.
Preservation locks cover this migration; an intentional future upgrade must revise
its corresponding lock and evidence explicitly, not silently bypass this check.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

STAGES = ('discover', 'decide', 'design', 'build', 'verify', 'introduce', 'observe',
          'change', 'diagnose', 'recover', 'transfer', 'grow', 'retire')
ZONES = {'engineering', 'engineering_experiments', 'product', 'shared', 'author_eval', 'archive'}
SKILL = 'plugins/playbook-native/skills/playbook'
LOCKS = {
    'PLAYBOOK.md': '3bdf380c2e9d66193fac1b49caa00e273b23842d',
    'docs/governed/README.md': '49790edf73b5dbe21ba06db65b00a43be57c2547',
    'tools/run_codex_role.py': 'b4989e4f478360b1ad7af5b956e1d57351317f39',
    'tools/codex_role_run_lib.py': 'fb59c0a08d8817220d6c48d52fd7696c60a0d7b8',
    'plugins/playbook-native/skills/playbook-frontend/SKILL.md': 'f72de173b1d427ae703e707e0511af410215b360',
}


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def validate_rules(payload: dict) -> list[dict]:
    if not isinstance(payload, dict) or payload.get('schema_version') != 'playbook.ownership.v1':
        raise ValueError('Unsupported ownership schema')
    rules = payload.get('rules')
    if not isinstance(rules, list) or not rules:
        raise ValueError('Ownership needs rules')
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get('path'), str) or rule.get('zone') not in ZONES:
            raise ValueError('Invalid ownership rule')
        p = rule['path']; rel = PurePosixPath(p)
        if not p or p in seen or rel.is_absolute() or '..' in rel.parts or '\\' in p or '*' in p:
            raise ValueError('Ambiguous ownership path')
        seen.add(p)
    return rules


def classify(path: str, rules: list[dict]) -> str:
    matches = [r for r in rules if path == r['path'] or (r['path'].endswith('/') and path.startswith(r['path']))]
    if not matches:
        raise ValueError(f'Unclassified tracked file: {path}')
    return max(matches, key=lambda r: len(r['path']))['zone']


def check_catalogue(root: Path, catalogue: dict) -> list[str]:
    errors = []
    if not isinstance(catalogue, dict) or catalogue.get('schema_version') != 'playbook.lifecycle.v1':
        return ['Unsupported lifecycle schema']
    if catalogue.get('order') != list(STAGES): errors.append('Lifecycle order does not cover all 13 stages')
    entries = catalogue.get('capabilities', [])
    if not isinstance(entries, list) or any(not isinstance(c, dict) for c in entries):
        return errors + ['Invalid capabilities']
    if [c.get('id') for c in entries] != list(STAGES): errors.append('Missing/duplicate/out-of-order capability')
    for c in entries:
        name = c.get('id')
        for field in ('title_ru', 'outcome', 'inputs', 'permission_topics', 'engineering_sources'):
            if not c.get(field): errors.append(f'{name}: missing {field}')
        reference = c.get('reference', '')
        if reference != f'references/lifecycle/{name}.md':
            errors.append(f'{name}: invalid reference'); continue
        path = root / SKILL / reference
        if not path.is_file() or path.is_symlink(): errors.append(f'{name}: missing procedure')
        elif len(path.read_text(encoding='utf-8').strip()) < 200: errors.append(f'{name}: empty procedure')
        maturity = c.get('maturity', {})
        if not isinstance(maturity, dict) or maturity.get('user_benefit') != 'not_established':
            errors.append(f'{name}: this migration may not manufacture empirical acceptance')
        sources = c.get('engineering_sources', [])
        if not isinstance(sources, list): errors.append(f'{name}: invalid sources'); continue
        for source in sources:
            if not isinstance(source, str) or '..' in PurePosixPath(source).parts or PurePosixPath(source).is_absolute():
                errors.append(f'{name}: invalid source'); continue
            if not (root / source).is_file(): errors.append(f'{name}: missing source {source}')
    return errors


def check(root: Path) -> tuple[list[str], list[dict]]:
    errors = []
    rules = validate_rules(json.loads((root/'shared/ownership.json').read_text(encoding='utf-8')))
    result = subprocess.run(['git','ls-files','-z'], cwd=root, capture_output=True, check=False)
    if result.returncode: raise ValueError('A Git checkout is required for complete tracked-file inventory')
    paths = sorted(set(result.stdout.decode('utf-8').rstrip('\0').split('\0')))
    if paths == ['']: raise ValueError('No tracked inventory')
    inventory = []
    for path in paths:
        try: inventory.append({'path':path, 'zone':classify(path, rules)})
        except ValueError as exc: errors.append(str(exc))
    for path, expected in LOCKS.items():
        current = root/path
        if not current.is_file() or blob_sha(current.read_bytes()) != expected:
            errors.append(f'Preserved Engineering source changed/missing: {path}')
    catalogue = json.loads((root/SKILL/'assets/lifecycle.json').read_text(encoding='utf-8'))
    errors.extend(check_catalogue(root, catalogue))
    mapping = json.loads((root/'shared/component_map.json').read_text(encoding='utf-8'))
    components = mapping.get('components', [])
    if [c.get('id') for c in components] != [f'PB-{n:02}' for n in range(1,51)]:
        errors.append('The 50-component provenance inventory is incomplete')
    for c in components:
        if c.get('zone') not in ZONES or not set(c.get('lifecycle', [])).issubset(STAGES):
            errors.append(f'Invalid component assignment: {c.get("id")}')
        for source in c.get('source_paths', []):
            path = source.split(' §')[0]
            if not list(root.glob(path)):
                errors.append(f'Missing source in component {c["id"]}: {path}')
    for name in ('run_codex_role.py','codex_role_run_lib.py','solution_record.py'):
        source, target = root/'tools'/name, root/SKILL/'scripts'/name
        if not source.is_file() or not target.is_file() or target.is_symlink() or source.read_bytes() != target.read_bytes():
            errors.append(f'Shared packaged helper drift: {name}')
    for path in ('engineering/README.md','engineering/USAGE_RU.md','product/README.md',
                 'product/CAPABILITIES.md','product/pilots/README.md','docs/vnext/STATUS.md'):
        if not (root/path).is_file(): errors.append(f'Missing user/maintainer route: {path}')
    return errors, inventory


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.')); p.add_argument('--inventory', action='store_true')
    args = p.parse_args(argv)
    try:
        errors, inventory = check(args.root.resolve())
        out = {'status': 'fail' if errors else 'contracts_valid', 'errors':errors,
               'tracked_files':len(inventory), 'lifecycle_stages':13,
               'meaning':'Source/delivery checks only; no live model or user-benefit verdict.'}
        if args.inventory: out['inventory'] = inventory
        print(json.dumps(out, ensure_ascii=False, indent=2)); return bool(errors)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'vnext_check: {exc}', file=sys.stderr); return 2

if __name__ == '__main__': raise SystemExit(main())

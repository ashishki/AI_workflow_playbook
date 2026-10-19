"""A deliberately tiny synthetic consumer, NOT a secret broker or sandbox."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True)
    parser.add_argument('--mode', choices=('check', 'raw', 'encoded', 'split', 'file'), default='check')
    args = parser.parse_args(argv)
    value = os.environ.get('PB_TEST_TOKEN', '')
    # Refuse real credentials even during a deliberate redaction-boundary test.
    if not re.fullmatch(r'PB_SYNTH_[0-9a-f]{64}', value):
        print(json.dumps({'ok': False, 'reason': 'missing_or_non_synthetic_token'}))
        return 3
    if hashlib.sha256(value.encode()).hexdigest() != args.expected:
        print(json.dumps({'ok': False, 'reason': 'wrong_version'}))
        return 4
    if args.mode == 'check':
        ok = 'PB_UNRELATED_SECRET' not in os.environ
        print(json.dumps({'ok': ok, 'unrelated_key_received': not ok}))
        return 0 if ok else 5
    if args.mode == 'file':
        # Only for disposable workspaces. Never accepts an arbitrary output path.
        with Path('synthetic-leak.txt').open('x', encoding='utf-8') as stream:
            stream.write(value)
        print(json.dumps({'synthetic_file_created': True}))
    else:
        transformed = value if args.mode == 'raw' else base64.b64encode(value.encode()).decode() if args.mode == 'encoded' else '|'.join(value)
        print(transformed)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Synthetic application loading a narrow .env format before using the probe.

This fixture models the owner's described workflow. It is not a general dotenv
parser and refuses non-synthetic values; existing environment values take priority.
The explicit injection-only mode refuses fallback to .env in condition C.
"""
from __future__ import annotations
import os
from pathlib import Path
import re
import sys

import probe


def load_dotenv(path: Path) -> bool:
    if not path.exists():
        return True
    values = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'(PB_[A-Z0-9_]+)=(PB_SYNTH_[0-9a-f]{64})', line)
        if not match or match[1] in values:
            return False
        values[match[1]] = match[2]
    for name, value in values.items():
        os.environ.setdefault(name, value)
    return True


def main() -> int:
    require_injected = '--require-injected' in sys.argv[1:]
    if require_injected:
        sys.argv.remove('--require-injected')
        if not os.environ.get('PB_TEST_TOKEN'):
            print('{"ok": false, "reason": "missing_injected_token"}')
            return 3
    elif not load_dotenv(Path('.env')):
        print('{"ok": false, "reason": "invalid_synthetic_dotenv"}')
        return 3
    return probe.main()


if __name__ == '__main__':
    sys.exit(main())

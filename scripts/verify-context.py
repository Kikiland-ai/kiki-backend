#!/usr/bin/env python3
"""Verify the pinned product snapshot without freezing mutable backend code."""
import hashlib
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1] / 'context/design-thinking'
try:
    manifest = json.loads((root / 'SOURCE.json').read_text())
    if manifest['schema_version'] != 1 or not re.fullmatch(r'[0-9a-f]{40}', manifest['source_revision']):
        raise ValueError('Invalid source manifest')
    for name, expected in manifest['files'].items():
        path = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Source path escapes snapshot')
        if path.is_symlink():
            raise ValueError('Symlinked source: ' + name)
        raw = path.read_bytes()
        if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
            raise ValueError('Source changed: ' + name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(manifest['files']) | {'SOURCE.json'}:
        raise ValueError('Unexpected or missing source files')
    print(f"PASS: {len(manifest['files'])} source files at {manifest['source_revision']}")
except (OSError, ValueError, KeyError, TypeError) as error:
    print('FAIL: ' + str(error), file=sys.stderr)
    raise SystemExit(1)

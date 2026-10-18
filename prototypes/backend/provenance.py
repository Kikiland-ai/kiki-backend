"""Non-secret runtime source receipts and stopped-service SQLite upgrade backups."""

import hashlib
import json
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

PR7 = 'f2dca8b806e4002411b5704e19f0f40681093298'


def source_receipt(checkout):
    root = Path(checkout).resolve()

    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])

    paths = set(git('ls-files', '-z', '--cached', '--others', '--exclude-standard')
                .decode('utf-8').strip('\0').split('\0'))
    hashes = {}
    for name in sorted(paths):
        relative = Path(name)
        if not (name.startswith(('prototypes/', 'contracts/')) or name == 'scripts/smoke-lab-upstream.py'):
            continue
        if relative.suffix not in {'.py', '.js', '.mjs', '.json', '.html', '.css'}:
            continue
        if any(part.startswith('.') or part in {'work', 'node_modules', '__pycache__'} for part in relative.parts):
            continue
        path = root / relative
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            raise ValueError('Runtime source must stay inside its checkout')
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'git_head': git('rev-parse', 'HEAD').decode().strip(),
            'pr7_ancestor': subprocess.run(['git', '-C', str(root), 'merge-base',
                                           '--is-ancestor', PR7, 'HEAD'], check=False,
                                          capture_output=True).returncode == 0,
            'git_dirty': bool(git('status', '--porcelain')),
            'runtime_source_sha256': digest, 'runtime_source_files': len(hashes),
            'runtime_files': hashes}


def verify_source(receipt, expected):
    if receipt['git_head'] != expected['git_head'] or receipt['runtime_source_sha256'] != expected['runtime_source_sha256']:
        raise ValueError('Runtime source differs from the verified candidate; repeat readiness checks')
    if not receipt['pr7_ancestor']:
        raise ValueError('Runtime source must include reviewed PR #7')


def backup_lab_databases(directory, destination):
    """Run only after all old writers have stopped. Never delete or rewrite originals."""
    directory, destination = Path(directory).resolve(), Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    copied = {}
    for name in ('labs.sqlite', 'lab-idempotency.sqlite'):
        source, target = directory / name, destination / name
        if not source.exists():
            continue
        with (closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as original,
              closing(sqlite3.connect(target)) as backup):
            original.backup(backup)
            if backup.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Upgrade backup failed its SQLite integrity check')
        copied[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = {'schema': 'kiki-lab-upgrade-backup/v1', 'directory': str(destination),
                'databases': copied, 'requires_stopped_writers': True}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest

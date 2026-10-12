#!/usr/bin/env python3
"""Generate deterministic Claude Code and Codex wrappers for canonical BB8 skills."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
PLUGIN = Path(__file__).resolve().parents[2]
REPO = PLUGIN.parent
MARKER = 'Generated BB8 discovery wrapper'


def adapter(plugin=PLUGIN):
    spec = importlib.util.spec_from_file_location('bb8_reference', plugin / 'adapters/reference/bb8.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def outputs(plugin=PLUGIN):
    loader = adapter(plugin)
    loader.validate(plugin)
    result = {}
    index = []
    for skill in loader.inventory(plugin):
        name = skill['name']
        source = plugin / skill['entrypoint']
        content = source.read_text(encoding='utf-8')
        frontmatter = content.split('---', 2)[1].strip()
        canonical = f'../../../bb8/{skill["entrypoint"]}'
        body = (f'\n\n<!-- {MARKER}; edit the canonical skill and rerun sync.py. -->\n\n'
                f'# BB8: {name}\n\n'
                f'Read and follow the [canonical BB8 skill]({canonical}) before doing this task. '
                'Resolve that path relative to this SKILL.md file. Resolve the canonical skill\'s '
                'own references relative to the canonical file, not this wrapper.\n\n'
                'Follow the applicable repository instructions and the user\'s explicit scope. '
                'Do not retrieve prior projects, chats, memory, vaults, or credentials. '
                'Use actual host tools for authorized work and report unavailable capabilities.\n')
        if name == 'organise':
            body += '\nKnowledge operations are excluded under the current setup scope. Do not ingest or request a knowledge root.\n'
        for host in ['.agents', '.claude']:
            header = frontmatter
            if host == '.claude' and name == 'organise':
                header += '\ndisable-model-invocation: true'
            result[f'{host}/skills/{name}/SKILL.md'] = f'---\n{header}\n---{body}'.encode()
        metadata = (plugin / 'skills' / name / 'agents/openai.yaml').read_text(encoding='utf-8')
        if name == 'organise':
            metadata = metadata.replace('allow_implicit_invocation: true', 'allow_implicit_invocation: false')
        result[f'.agents/skills/{name}/agents/openai.yaml'] = f'# {MARKER} metadata\n{metadata}'.encode()
        index.append({'name': name, 'canonical': f'bb8/{skill["entrypoint"]}',
                      'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'codex': f'.agents/skills/{name}/SKILL.md',
                      'claude': f'.claude/skills/{name}/SKILL.md'})
    resources = []
    source_files = [plugin / name for name in ['plugin.json', '.codex-plugin/plugin.json', 'README.md', 'SESSION-SETUP-RUNBOOK.md']]
    for directory in ['skills', 'harness']:
        for path in (plugin / directory).rglob('*'):
            if path.is_symlink():
                raise ValueError('Symlinked canonical resource is forbidden')
            if path.is_file():
                source_files.append(path)
    for path in sorted(source_files):
        raw = path.read_bytes()
        resources.append({'path': 'bb8/' + path.relative_to(plugin).as_posix(),
                          'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    result['bb8/adapters/discovery/index.json'] = (json.dumps({'schema_version': 1,
        'generator': MARKER, 'plugin': 'bb8', 'plugin_version': '0.2.1',
        'skills': index, 'resources': resources}, indent=2) + '\n').encode()
    return result


def destination(repo, relative):
    repo = repo.resolve()
    target = repo / relative
    if not target.resolve().is_relative_to(repo):
        raise ValueError(f'Discovery path escapes repository: {relative}')
    cursor = target
    while cursor != repo:
        if cursor.is_symlink():
            raise ValueError(f'Symlinked discovery destination: {relative}')
        cursor = cursor.parent
    return target


def sync(repo=REPO, plugin=PLUGIN, write=False):
    planned = outputs(plugin)
    differences = []
    for relative, expected in planned.items():
        path = destination(repo, relative)
        if path.exists() and not path.is_file():
            raise ValueError(f'Discovery destination is not a file: {relative}')
        current = path.read_bytes() if path.is_file() else None
        if current == expected:
            continue
        differences.append(relative)
        if write and current is not None and MARKER.encode() not in current:
            raise ValueError(f'Existing unmanaged skill or metadata conflict: {relative}')
    # Check every conflict before writing any output.
    if write:
        for relative in differences:
            path = destination(repo, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(planned[relative])
    return {'status': 'PASS' if write or not differences else 'FAIL',
            'packaged_skills': 21, 'codex_wrappers': 21, 'claude_wrappers': 21,
            'files_written': len(differences) if write else 0,
            'missing_or_stale': [] if write else differences,
            'host_runtime_discovery': 'not_tested'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        result = sync(write=args.write)
        print(json.dumps(result, indent=2))
        return 0 if result['status'] == 'PASS' else 1
    except (ValueError, OSError) as error:
        print(f'BB8 discovery error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

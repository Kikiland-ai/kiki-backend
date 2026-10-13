#!/usr/bin/env python3
"""BB8 repo bootstrap: package locally, or provision explicitly configured GitHub repos."""

import argparse
import base64
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from zipfile import ZipFile, ZIP_DEFLATED

sys.dont_write_bytecode = True
PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parent
BEGIN = '<!-- BB8:BEGIN -->'
END = '<!-- BB8:END -->'
MARKER = '.bb8-bootstrap.json'
BRANCH = 'automation/bb8-bootstrap'


class ApiError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


class GitHub:
    def __init__(self, token):
        if not token:
            raise ValueError('Configured organization runtime identity is unavailable; no network work performed')
        self.token = token

    def request(self, method, path, payload=None):
        if not path.startswith('/') or path.startswith('//'):
            raise ValueError('Invalid GitHub API path')
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request('https://api.github.com' + path, data=data, method=method,
            headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'bb8-provisioner/0.1.0',
                     'Content-Type': 'application/json'})
        # Do not follow redirects while carrying the runtime authorization header.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=45) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            # Do not log response bodies or authorization material.
            raise ApiError(error.code, f'GitHub {method} failed with HTTP {error.code}') from None


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def merge_instructions(existing, fragment):
    if (BEGIN in existing) != (END in existing) or existing.count(BEGIN) > 1 or existing.count(END) > 1:
        raise ValueError('Malformed or duplicate BB8 instruction markers')
    managed = BEGIN + '\n' + fragment.strip() + '\n' + END
    if BEGIN in existing:
        start, finish = existing.index(BEGIN), existing.index(END) + len(END)
        if finish <= start:
            raise ValueError('Invalid BB8 instruction marker order')
        return existing[:start] + managed + existing[finish:]
    return existing + ('\n\n' if existing and not existing.endswith('\n\n') else '') + managed + '\n'


def bundle(root=ROOT):
    plugin = root / 'bb8'
    discovery = load_module(plugin / 'adapters/discovery/sync.py', 'bb8_discovery')
    discovery.adapter(plugin).validate(plugin)
    files = {}
    for path in sorted(plugin.rglob('*')):
        relative = path.relative_to(plugin)
        excluded_names = {'.git', '__pycache__', 'credentials', 'vault', 'knowledge', 'chats', 'chat-history', 'logs', 'cache'}
        if any(part.lower() in excluded_names for part in relative.parts) or path.name == '.env' or path.name.startswith('.env.') or path.suffix.lower() in {'.pyc', '.pem', '.key', '.p12', '.pfx'}:
            raise ValueError(f'Excluded artifact must not enter the starter bundle: {relative}')
        if path.is_symlink():
            raise ValueError(f'Symlink in bundle: {path.relative_to(root)}')
        if not path.is_file():
            continue
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    files.update(discovery.outputs(plugin))
    fragment = (plugin / 'provisioning/AGENTS.fragment.md').read_text(encoding='utf-8')
    files['AGENTS.md'] = merge_instructions('', fragment).encode()
    files['CLAUDE.md'] = merge_instructions('', '@AGENTS.md\n\nUse `/bb8` for coordinated work. BB8 project skills are under `.claude/skills/`.').encode()
    files['BB8.md'] = (root / 'BB8.md').read_bytes()
    files['.agents/plugins/marketplace.json'] = (root / '.agents/plugins/marketplace.json').read_bytes()
    files['.github/workflows/bb8-check.yml'] = (root / '.github/workflows/bb8-check.yml').read_bytes()
    return files


def bundle_digest(files):
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode() + b'\0' + files[name] + b'\0')
    return digest.hexdigest()


def validate_repo_name(repository, organization):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Repository must be owner/name')
    if repository.split('/')[0].casefold() != organization.casefold():
        raise ValueError('Repository lies outside the configured organization')


def read_blob(api, repository, entry):
    if entry['mode'] != '100644' or entry['type'] != 'blob':
        raise ValueError('Existing instruction or bootstrap marker is not a regular file')
    data = api.request('GET', f'/repos/{repository}/git/blobs/{entry["sha"]}')
    if data.get('encoding') != 'base64' or data.get('size', 0) > 128 * 1024:
        raise ValueError('Unsupported or oversized instruction file')
    return base64.b64decode(data['content'], validate=False).decode('utf-8')


def plan_files(files, current, existing_text, revision):
    if MARKER in current:
        marker = json.loads(existing_text[MARKER])
        if marker.get('schema_version') != 1 or marker.get('plugin') != 'bb8':
            raise ValueError('Existing bootstrap marker is not a managed BB8 record')
        if marker.get('status') == 'complete':
            return {}, 'already_bootstrapped'
        if marker.get('status') != 'initializing':
            raise ValueError('Unrecognized existing bootstrap marker')
    if any(name == 'bb8' or name.startswith('bb8/') for name in current):
        raise ValueError('Existing unmanaged BB8 directory; preserving it for explicit review')
    planned = {}
    for name, content in files.items():
        parent = Path(name).parent
        while parent.as_posix() != '.':
            ancestor = current.get(parent.as_posix())
            if ancestor and ancestor.get('type') != 'tree':
                raise ValueError(f'Existing target parent is not a directory: {parent.as_posix()}')
            parent = parent.parent
        if name in ('AGENTS.md', 'CLAUDE.md'):
            existing = existing_text.get(name, '')
            text = content.decode()
            fragment = text.split(BEGIN, 1)[1].split(END, 1)[0]
            if name == 'CLAUDE.md' and re.search(r'(?m)^\s*@AGENTS\.md\s*$', existing):
                fragment = fragment.replace('@AGENTS.md', '', 1)
            planned[name] = merge_instructions(existing, fragment).encode()
        elif name in current:
            raise ValueError(f'Existing target path conflict: {name}')
        else:
            planned[name] = content
    marker = {'schema_version': 1, 'status': 'complete', 'plugin': 'bb8',
              'plugin_version': '0.2.2', 'source_revision': revision,
              'bundle_sha256': bundle_digest(files)}
    planned[MARKER] = (json.dumps(marker, indent=2) + '\n').encode()
    return planned, 'ready'


def bootstrap(api, repository, files, revision, config, dry_run=False):
    validate_repo_name(repository, config['organization'])
    mode = config['write_mode']
    if mode not in ('direct-with-pr-fallback', 'pull-request'):
        raise ValueError('Unsupported write mode')
    if repository in config['excluded_repositories']:
        return {'repository': repository, 'status': 'excluded'}
    metadata = api.request('GET', f'/repos/{repository}')
    if metadata['full_name'].casefold() != repository.casefold():
        raise ValueError('GitHub repository identity mismatch')
    if metadata.get('archived') or metadata.get('disabled'):
        return {'repository': repository, 'status': 'blocked_read_only_repository'}
    branch = metadata.get('default_branch') or 'main'
    escaped = urllib.parse.quote(branch, safe='')
    try:
        head = api.request('GET', f'/repos/{repository}/git/ref/heads/{escaped}')['object']['sha']
    except ApiError as error:
        if error.status not in (404, 409) or metadata.get('size', 0) != 0:
            raise
        if dry_run:
            return {'repository': repository, 'status': 'would_initialize_and_bootstrap', 'files': len(files) + 1}
        initial = json.dumps({'schema_version': 1, 'status': 'initializing', 'plugin': 'bb8'}) + '\n'
        api.request('PUT', f'/repos/{repository}/contents/{MARKER}',
                    {'message': 'Initialize BB8 repository bootstrap',
                     'content': base64.b64encode(initial.encode()).decode(), 'branch': branch})
        head = api.request('GET', f'/repos/{repository}/git/ref/heads/{escaped}')['object']['sha']
    commit = api.request('GET', f'/repos/{repository}/git/commits/{head}')
    tree = api.request('GET', f'/repos/{repository}/git/trees/{commit["tree"]["sha"]}?recursive=1')
    if tree.get('truncated'):
        raise ValueError('Truncated repository tree; refusing an incomplete conflict check')
    current = {entry['path']: entry for entry in tree['tree']}
    texts = {name: read_blob(api, repository, current[name]) for name in ('AGENTS.md', 'CLAUDE.md', MARKER) if name in current}
    planned, status = plan_files(files, current, texts, revision)
    if not planned:
        return {'repository': repository, 'status': status}
    if dry_run:
        return {'repository': repository, 'status': 'would_bootstrap', 'files': len(planned)}
    pulls = api.request('GET', f'/repos/{repository}/pulls?state=open&head={urllib.parse.quote(config["organization"] + ":" + BRANCH, safe="")}')
    if pulls:
        return {'repository': repository, 'status': 'pull_request_pending', 'pull_request': pulls[0]['html_url']}
    elements = [{'path': name, 'mode': '100644', 'type': 'blob', 'content': data.decode('utf-8')}
                for name, data in sorted(planned.items())]
    new_tree = api.request('POST', f'/repos/{repository}/git/trees', {'base_tree': commit['tree']['sha'], 'tree': elements})['sha']
    new_commit = api.request('POST', f'/repos/{repository}/git/commits',
                             {'message': 'Add BB8 agent setup and Claude Code/Codex discovery',
                              'tree': new_tree, 'parents': [head]})['sha']
    if mode == 'direct-with-pr-fallback':
        latest = api.request('GET', f'/repos/{repository}/git/ref/heads/{escaped}')['object']['sha']
        if latest != head:
            return {'repository': repository, 'status': 'retry_head_changed'}
        try:
            api.request('PATCH', f'/repos/{repository}/git/refs/heads/{escaped}', {'sha': new_commit, 'force': False})
            observed = api.request('GET', f'/repos/{repository}/git/ref/heads/{escaped}')['object']['sha']
            return {'repository': repository, 'status': 'bootstrapped' if observed == new_commit else 'retry_verification', 'commit': new_commit}
        except ApiError as error:
            if error.status not in (403, 422):
                raise
    try:
        api.request('POST', f'/repos/{repository}/git/refs', {'ref': 'refs/heads/' + BRANCH, 'sha': new_commit})
    except ApiError as error:
        if error.status == 422:
            return {'repository': repository, 'status': 'blocked_existing_bootstrap_branch'}
        raise
    pr = api.request('POST', f'/repos/{repository}/pulls', {'title': 'Add BB8 repo agent setup', 'head': BRANCH, 'base': branch,
                     'body': 'Adds the reviewed BB8 suite, root instructions, and Claude Code/Codex skill discovery wrappers. Existing repository content is preserved. Merge this PR to activate repository-level guidance; native hosted plugins still require host registration.'})
    return {'repository': repository, 'status': 'pull_request_created', 'pull_request': pr['html_url']}


def parse_time(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Creation cutoff must include a timezone')
    return parsed


def scan(api, files, revision, config, dry_run=False):
    if not config.get('created_after'):
        raise ValueError('New-repository cutoff is unset; scheduled provisioning remains disabled')
    cutoff = parse_time(config['created_after'])
    outcomes = []
    page = 1
    while True:
        response = api.request('GET', f'/installation/repositories?per_page=100&page={page}')
        repositories = response['repositories']
        for repo in repositories:
            if repo['owner']['login'].casefold() != config['organization'].casefold():
                continue
            if parse_time(repo['created_at']) < cutoff:
                continue
            name = repo['full_name']
            try:
                outcomes.append(bootstrap(api, name, files, revision, config, dry_run))
            except (ApiError, ValueError) as error:
                outcomes.append({'repository': name, 'status': 'failed', 'error': str(error)})
        if len(repositories) < 100:
            break
        page += 1
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    package = sub.add_parser('package', help='Build a template starter archive without network access')
    package.add_argument('--output', required=True)
    package.add_argument('--source-revision', required=True)
    for name in ('scan', 'bootstrap'):
        command = sub.add_parser(name)
        command.add_argument('--source-revision', required=True)
        command.add_argument('--dry-run', action='store_true')
        if name == 'bootstrap':
            command.add_argument('--repository', required=True)
    args = parser.parse_args()
    try:
        files = bundle()
        if not re.fullmatch(r'[0-9a-f]{40}', args.source_revision):
            raise ValueError('Source revision must be a pinned 40-character commit SHA')
        if args.command == 'package':
            files[MARKER] = (json.dumps({'schema_version': 1, 'status': 'complete',
                'plugin': 'bb8', 'plugin_version': '0.2.2', 'source_revision': args.source_revision,
                'bundle_sha256': bundle_digest(files)}, indent=2) + '\n').encode()
            output = Path(args.output)
            if output.exists():
                raise ValueError('Output already exists; refusing to overwrite it')
            output.parent.mkdir(parents=True, exist_ok=True)
            with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
                for name, data in sorted(files.items()):
                    archive.writestr(name, data)
            print(json.dumps({'status': 'packaged', 'files': len(files), 'bundle_sha256': bundle_digest(files)}))
            return 0
        config = json.loads((PLUGIN / 'provisioning/config.json').read_text())
        api = GitHub(os.environ.get('BB8_GITHUB_TOKEN'))
        outcomes = scan(api, files, args.source_revision, config, args.dry_run) if args.command == 'scan' else [bootstrap(api, args.repository, files, args.source_revision, config, args.dry_run)]
        print(json.dumps(outcomes, indent=2))
        # PR fallbacks and retries remain visible as incomplete activation.
        incomplete = {'failed', 'retry_head_changed', 'retry_verification', 'blocked_existing_bootstrap_branch', 'blocked_read_only_repository', 'pull_request_created', 'pull_request_pending'}
        return 1 if any(item['status'] in incomplete for item in outcomes) else 0
    except (ValueError, OSError, ApiError) as error:
        print(f'BB8 provisioning error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

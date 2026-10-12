import base64
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bb8_bootstrap_tests', PLUGIN / 'provisioning/bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
REVISION = 'a' * 40
CONFIG = {'organization': 'Kikiland-ai', 'excluded_repositories': ['Kikiland-ai/Design-Thinking'],
          'write_mode': 'direct-with-pr-fallback', 'created_after': '2026-10-12T00:00:00Z'}
FILES = {'AGENTS.md': bootstrap.merge_instructions('', 'BB8 instructions').encode(),
         'CLAUDE.md': bootstrap.merge_instructions('', '@AGENTS.md\n\nBB8 discovery').encode(),
         'bb8/plugin.json': b'{"name":"bb8"}'}


class FakeAPI:
    def __init__(self, empty=False, protected=False, changed=False, pending=False):
        self.empty, self.protected, self.changed, self.pending = empty, protected, changed, pending
        self.calls = []
        self.head = 'old-head'
        self.ref_reads = 0
        self.initialized = not empty
        self.elements = []

    def request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == 'GET' and path == '/repos/Kikiland-ai/demo':
            return {'full_name': 'Kikiland-ai/demo', 'default_branch': 'main', 'size': 0 if self.empty else 1}
        if method == 'GET' and '/git/ref/heads/' in path:
            self.ref_reads += 1
            if not self.initialized:
                raise bootstrap.ApiError(409, 'Empty fixture')
            if self.changed and self.ref_reads == 2:
                return {'object': {'sha': 'concurrent-head'}}
            return {'object': {'sha': self.head}}
        if method == 'PUT' and '/contents/.bb8-bootstrap.json' in path:
            self.initialized = True
            return {'commit': {'sha': 'initialized'}}
        if method == 'GET' and '/git/commits/' in path:
            return {'tree': {'sha': 'old-tree'}}
        if method == 'GET' and '/git/trees/' in path:
            entries = [{'path': 'existing.py', 'mode': '100644', 'type': 'blob', 'sha': 'keep-this'}]
            if self.empty:
                entries.append({'path': bootstrap.MARKER, 'mode': '100644', 'type': 'blob', 'sha': 'marker'})
            return {'truncated': False, 'tree': entries}
        if method == 'GET' and '/git/blobs/marker' in path:
            text = json.dumps({'schema_version': 1, 'status': 'initializing', 'plugin': 'bb8'}).encode()
            return {'encoding': 'base64', 'size': len(text), 'content': base64.b64encode(text).decode()}
        if method == 'GET' and '/pulls?' in path:
            return [{'html_url': 'https://github.com/Kikiland-ai/demo/pull/1'}] if self.pending else []
        if method == 'POST' and path.endswith('/git/trees'):
            self.elements = payload['tree']
            self.assert_base = payload['base_tree']
            return {'sha': 'new-tree'}
        if method == 'POST' and path.endswith('/git/commits'):
            return {'sha': 'new-commit'}
        if method == 'PATCH' and '/git/refs/' in path:
            if self.protected:
                raise bootstrap.ApiError(422, 'Protected fixture')
            self.head = payload['sha']
            return {}
        if method == 'POST' and path.endswith('/git/refs'):
            return {'ref': payload['ref']}
        if method == 'POST' and path.endswith('/pulls'):
            return {'html_url': 'https://github.com/Kikiland-ai/demo/pull/1'}
        raise AssertionError((method, path, payload))


class ProvisioningTests(unittest.TestCase):
    def test_preserves_existing_instructions_and_is_idempotent(self):
        initial = '# Existing rules\nDo not remove.\n'
        merged = bootstrap.merge_instructions(initial, 'BB8 instructions')
        self.assertTrue(merged.startswith(initial))
        self.assertEqual(bootstrap.merge_instructions(merged, 'BB8 instructions'), merged)
        updated = bootstrap.merge_instructions(merged, 'New BB8 instructions')
        self.assertIn('Do not remove.', updated)
        self.assertNotIn('\nBB8 instructions\n', updated)

    def test_malformed_markers_fail(self):
        for text in [bootstrap.BEGIN, bootstrap.END, bootstrap.END + bootstrap.BEGIN,
                     bootstrap.BEGIN + bootstrap.END + bootstrap.BEGIN + bootstrap.END]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                bootstrap.merge_instructions(text, 'BB8')

    def test_only_configured_organization_is_allowed(self):
        with self.assertRaises(ValueError):
            bootstrap.validate_repo_name('other/demo', 'Kikiland-ai')
        with self.assertRaises(ValueError):
            bootstrap.validate_repo_name('Kikiland-ai/../outside', 'Kikiland-ai')

    def test_conflicts_are_preserved(self):
        for current in [{'bb8/plugin.json': {'type': 'blob'}},
                        {'.agents': {'type': 'blob'}}]:
            files = {**FILES, '.agents/skills/bb8/SKILL.md': b'wrapper'}
            with self.assertRaises(ValueError):
                bootstrap.plan_files(files, current, {}, REVISION)

    def test_complete_marker_prevents_repeated_writes(self):
        marker = json.dumps({'schema_version': 1, 'status': 'complete', 'plugin': 'bb8'})
        planned, status = bootstrap.plan_files(FILES, {bootstrap.MARKER: {}}, {bootstrap.MARKER: marker}, REVISION)
        self.assertEqual(planned, {})
        self.assertEqual(status, 'already_bootstrapped')

    def test_foreign_marker_is_not_adopted(self):
        with self.assertRaises(ValueError):
            bootstrap.plan_files(FILES, {bootstrap.MARKER: {}}, {bootstrap.MARKER: '{"status":"complete"}'}, REVISION)

    def test_existing_claude_import_is_not_duplicated(self):
        planned, _ = bootstrap.plan_files(FILES, {'CLAUDE.md': {}}, {'CLAUDE.md': '@AGENTS.md\nExisting rules'}, REVISION)
        self.assertEqual(planned['CLAUDE.md'].count(b'@AGENTS.md'), 1)

    def test_direct_write_keeps_base_tree_and_never_forces(self):
        api = FakeAPI()
        result = bootstrap.bootstrap(api, 'Kikiland-ai/demo', FILES, REVISION, CONFIG)
        self.assertEqual(result['status'], 'bootstrapped')
        self.assertEqual(api.assert_base, 'old-tree')
        self.assertNotIn('existing.py', {entry['path'] for entry in api.elements})
        writes = [payload for method, _, payload in api.calls if method == 'PATCH']
        self.assertEqual(writes, [{'sha': 'new-commit', 'force': False}])

    def test_protected_branch_gets_pr(self):
        api = FakeAPI(protected=True)
        result = bootstrap.bootstrap(api, 'Kikiland-ai/demo', FILES, REVISION, CONFIG)
        self.assertEqual(result['status'], 'pull_request_created')
        self.assertEqual(api.head, 'old-head')

    def test_pending_pr_does_not_create_duplicate_commits(self):
        api = FakeAPI(pending=True)
        result = bootstrap.bootstrap(api, 'Kikiland-ai/demo', FILES, REVISION, CONFIG)
        self.assertEqual(result['status'], 'pull_request_pending')
        self.assertFalse(any(method != 'GET' for method, _, _ in api.calls))

    def test_concurrent_head_is_not_overwritten(self):
        api = FakeAPI(changed=True)
        result = bootstrap.bootstrap(api, 'Kikiland-ai/demo', FILES, REVISION, CONFIG)
        self.assertEqual(result['status'], 'retry_head_changed')
        self.assertFalse(any(method == 'PATCH' for method, _, _ in api.calls))

    def test_empty_repository_is_initialized_then_bootstrapped(self):
        api = FakeAPI(empty=True)
        result = bootstrap.bootstrap(api, 'Kikiland-ai/demo', FILES, REVISION, CONFIG)
        self.assertEqual(result['status'], 'bootstrapped')
        self.assertTrue(any(method == 'PUT' for method, _, _ in api.calls))

    def test_dry_run_never_writes_or_initializes(self):
        for empty in [False, True]:
            api = FakeAPI(empty=empty)
            result = bootstrap.bootstrap(api, 'Kikiland-ai/demo', FILES, REVISION, CONFIG, True)
            self.assertTrue(result['status'].startswith('would_'))
            self.assertFalse(any(method != 'GET' for method, _, _ in api.calls))

    def test_scan_filters_creation_date_and_organization(self):
        class ListingAPI(FakeAPI):
            def request(self, method, path, payload=None):
                if path.startswith('/installation/repositories'):
                    return {'repositories': [
                        {'owner': {'login': 'Kikiland-ai'}, 'created_at': '2026-10-11T00:00:00Z', 'full_name': 'Kikiland-ai/old'},
                        {'owner': {'login': 'Other'}, 'created_at': '2026-10-13T00:00:00Z', 'full_name': 'Other/demo'},
                        {'owner': {'login': 'Kikiland-ai'}, 'created_at': '2026-10-13T00:00:00Z', 'full_name': 'Kikiland-ai/demo'}]}
                return super().request(method, path, payload)
        results = bootstrap.scan(ListingAPI(), FILES, REVISION, CONFIG, True)
        self.assertEqual([item['repository'] for item in results], ['Kikiland-ai/demo'])

    def test_unset_cutoff_prevents_scan(self):
        with self.assertRaises(ValueError):
            bootstrap.scan(FakeAPI(), FILES, REVISION, {**CONFIG, 'created_after': None})

    def test_invalid_write_mode_prevents_all_api_access(self):
        api = FakeAPI(empty=True)
        with self.assertRaises(ValueError):
            bootstrap.bootstrap(api, 'Kikiland-ai/demo', FILES, REVISION, {**CONFIG, 'write_mode': 'unknown'})
        self.assertEqual(api.calls, [])

    def test_template_bundle_contains_discovery_but_no_controller_workflow(self):
        files = bootstrap.bundle(PLUGIN.parent)
        self.assertIn('.github/workflows/bb8-check.yml', files)
        self.assertNotIn('.github/workflows/bb8-org-bootstrap.yml', files)
        self.assertIn('CLAUDE.md', files)
        self.assertIn('.agents/plugins/marketplace.json', files)
        marketplace = json.loads(files['.agents/plugins/marketplace.json'])
        self.assertEqual([plugin['name'] for plugin in marketplace['plugins']], ['bb8'])
        self.assertEqual(marketplace['plugins'][0]['source']['path'], './bb8')
        self.assertEqual(len([path for path in files if path.startswith('.claude/') and path.endswith('SKILL.md')]), 21)
        self.assertEqual(len([path for path in files if path.startswith('.agents/') and path.endswith('SKILL.md')]), 21)

    def test_excluded_runtime_files_are_not_bundled(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            shutil.copytree(PLUGIN, repo / 'bb8')
            (repo / 'bb8/.env').write_text('Non-secret test fixture')
            with self.assertRaises(ValueError):
                bootstrap.bundle(repo)


if __name__ == '__main__':
    unittest.main(verbosity=2)

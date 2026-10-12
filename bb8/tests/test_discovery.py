import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bb8_discovery_tests', PLUGIN / 'adapters/discovery/sync.py')
discovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discovery)


class DiscoveryTests(unittest.TestCase):
    def test_both_hosts_expose_exact_canonical_skill_ids(self):
        outputs = discovery.outputs(PLUGIN)
        loader = discovery.adapter(PLUGIN)
        for host in ['.agents', '.claude']:
            paths = [name for name in outputs if name.startswith(host + '/') and name.endswith('/SKILL.md')]
            self.assertEqual(len(paths), 21)
            names = {loader.frontmatter(outputs[path].decode())['name'] for path in paths}
            self.assertEqual(names, loader.EXPECTED)
            for path in paths:
                for link in loader.markdown_targets(outputs[path].decode()):
                    self.assertTrue((PLUGIN.parent / Path(path).parent / link).resolve().is_file())

    def test_write_check_and_detect_stale_wrapper(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            self.assertEqual(discovery.sync(repo, PLUGIN, True)['files_written'], 64)
            self.assertEqual(discovery.sync(repo, PLUGIN)['status'], 'PASS')
            path = repo / '.claude/skills/bb8/SKILL.md'
            path.write_text(path.read_text() + '\nStale change\n')
            self.assertEqual(discovery.sync(repo, PLUGIN)['status'], 'FAIL')
            self.assertEqual(discovery.sync(repo, PLUGIN, True)['files_written'], 1)

    def test_conflict_preflight_prevents_partial_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            path = repo / '.claude/skills/bb8/SKILL.md'
            path.parent.mkdir(parents=True)
            path.write_text('Existing user skill')
            with self.assertRaises(ValueError):
                discovery.sync(repo, PLUGIN, True)
            self.assertFalse((repo / '.agents').exists())
            self.assertEqual(path.read_text(), 'Existing user skill')

    def test_symlinked_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / 'repo'
            outside = Path(temporary) / 'outside'
            repo.mkdir()
            outside.mkdir()
            (repo / '.agents').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                discovery.sync(repo, PLUGIN, True)
            self.assertEqual(list(outside.iterdir()), [])

    def test_knowledge_skill_is_not_implicitly_enabled(self):
        outputs = discovery.outputs(PLUGIN)
        self.assertIn(b'disable-model-invocation: true', outputs['.claude/skills/organise/SKILL.md'])
        self.assertIn(b'allow_implicit_invocation: false', outputs['.agents/skills/organise/agents/openai.yaml'])

    def test_resource_catalogue_hashes_all_original_package_files(self):
        index = json.loads(discovery.outputs(PLUGIN)['bb8/adapters/discovery/index.json'])
        self.assertEqual(len(index['resources']), 71)
        for resource in index['resources']:
            raw = (PLUGIN.parent / resource['path']).read_bytes()
            self.assertEqual(resource['bytes'], len(raw))
            self.assertEqual(resource['sha256'], hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    unittest.main(verbosity=2)

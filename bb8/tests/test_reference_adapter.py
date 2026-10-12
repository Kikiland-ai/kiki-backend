"""Meaningful isolation and adapter checks against copied BB8 resources only."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bb8_reference', ROOT / 'adapters/reference/bb8.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def request(**overrides):
    values = {'task': 'Review an explicitly scoped generic file', 'skill': 'engineering-review', 'scope': ['example.py'], 'mode': 'read-only', 'tool': ['read'], 'reference': ['harness/references/engineering-principles.md']}
    values.update(overrides)
    return argparse.Namespace(**values)


class AdapterChecks(unittest.TestCase):
    def test_exact_inventory_and_links(self):
        result = adapter.validate(ROOT)
        self.assertEqual(result['packaged_skills'], 21)
        self.assertEqual(result['resolved_skill_links'], 33)
        self.assertEqual(result['native_registration'], 'not_checked')

    def test_scoped_reference_packet_without_repository_access(self):
        packet = adapter.prepare(request(scope=['nonexistent-demo/file.py']), ROOT)
        self.assertIn('nonexistent-demo/file.py', packet)
        self.assertIn('"native_plugin_active": false', packet)
        self.assertIn('instructions_prepared_not_executed', packet)
        self.assertIn('Packaged reference: skills/engineering-review/SKILL.md', packet)
        self.assertNotIn('Packaged reference: skills/organise/SKILL.md', packet)
        self.assertNotIn('Packaged reference: skills/product-discovery/SKILL.md', packet)

    def test_scope_traversal_and_absolute_paths_rejected(self):
        for value in ['../outside', '/absolute', 'C:/outside', 'a\\..\\outside', '']:
            with self.subTest(scope=value), self.assertRaises(ValueError):
                adapter.prepare(request(scope=[value]), ROOT)

    def test_unknown_or_excluded_skills_rejected(self):
        for value in ['host-skill', 'organise', '../../outside']:
            with self.subTest(skill=value), self.assertRaises(ValueError):
                adapter.prepare(request(skill=value), ROOT)

    def test_read_only_edit_conflict_rejected(self):
        with self.assertRaises(ValueError):
            adapter.prepare(request(tool=['read', 'edit']), ROOT)

    def test_reference_traversal_rejected(self):
        for value in ['harness/../skills/organise/SKILL.md', '../outside.md', 'skills/product-discovery/SKILL.md']:
            with self.subTest(reference=value), self.assertRaises(ValueError):
                adapter.prepare(request(reference=[value]), ROOT)

    def test_empty_frontmatter_rejected(self):
        with self.assertRaises(ValueError):
            adapter.frontmatter('---\nname: bb8\ndescription: ""\n---\n')

    def test_escaped_or_symlinked_resource_rejected(self):
        with self.assertRaises(ValueError):
            adapter.resource('../outside.md', ROOT)
        with tempfile.TemporaryDirectory() as temp:
            test_root = Path(temp)
            (test_root / 'real.md').write_text('safe fixture')
            (test_root / 'link.md').symlink_to('real.md')
            with self.assertRaises(ValueError):
                adapter.resource('link.md', test_root)

    def test_inactive_registry_blocks_reference_route(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / 'bb8'
            shutil.copytree(ROOT, copied)
            path = copied / 'harness/capability-registry.yaml'
            path.write_text(path.read_text().replace('status: "active"', 'status: "planned"', 1))
            with self.assertRaises(ValueError):
                adapter.prepare(request(), copied)

    def test_missing_link_and_extra_skill_fail_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / 'bb8'
            shutil.copytree(ROOT, copied)
            path = copied / 'skills/engineering-review/SKILL.md'
            path.write_text(path.read_text() + '\n[missing](references/missing.md)\n')
            with self.assertRaises(ValueError):
                adapter.validate(copied)
            path.write_bytes((ROOT / 'skills/engineering-review/SKILL.md').read_bytes())
            (copied / 'skills/extra').mkdir()
            with self.assertRaises(ValueError):
                adapter.validate(copied)

    def test_identity_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / 'bb8'
            shutil.copytree(ROOT, copied)
            path = copied / 'plugin.json'
            manifest = json.loads(path.read_text())
            manifest['name'] = 'other'
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                adapter.validate(copied)


if __name__ == '__main__':
    unittest.main(verbosity=2)

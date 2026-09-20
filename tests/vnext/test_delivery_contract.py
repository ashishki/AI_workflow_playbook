"""Packaging/source contract tests; not model, installation or field trials."""
import configparser
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DeliveryContractTests(unittest.TestCase):
    def test_companion_available_in_documented_author_environment(self):
        text = (ROOT / 'requirements-dev.txt').read_text(encoding='utf-8')
        self.assertIn('-e ./companion/ai_workflow_harness_lab', text)
        parser = configparser.ConfigParser()
        parser.read(ROOT / 'pytest.ini')
        self.assertIn('companion/ai_workflow_harness_lab/src', parser['pytest']['pythonpath'])

    def test_new_helpers_have_one_canonical_implementation(self):
        for name in ('solution_record.py', 'playbook_environment.py'):
            self.assertEqual((ROOT / 'tools' / name).read_bytes(),
                             (ROOT / 'plugins/playbook-native/skills/playbook/scripts' / name).read_bytes())

    def test_delivered_payload_contains_environment_and_ownership_routes(self):
        spec = importlib.util.spec_from_file_location('delivery_build', ROOT / 'distribution/native/build.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        _, payload = build.collect()
        for source in ('plugins/playbook-native/skills/playbook/', 'Мой проект/.agents/skills/playbook/'):
            self.assertIn(source + 'scripts/playbook_environment.py', payload)
            self.assertIn(source + 'references/environment.md', payload)
            self.assertIn(source + 'references/working-session.md', payload)
        self.assertIn('ПОМОЩЬ.md', payload)
        self.assertFalse(any('docs/delivery/' in name for name in payload))


if __name__ == '__main__':
    unittest.main()

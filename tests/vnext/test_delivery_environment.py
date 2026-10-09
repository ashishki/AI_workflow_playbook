"""Read-only inventory tests. These do not prove live Codex/browser usability."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'tools/playbook_environment.py'
SPEC = importlib.util.spec_from_file_location('delivery_environment', SCRIPT)
environment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(environment)


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_presence_never_claims_authentication_or_live_readiness(self):
        with patch.object(environment.shutil, 'which', return_value='/fake/tool'):
            report = environment.inspect_environment(self.root, 'product', {'review', 'browser'})
        self.assertEqual(report['status'], 'live_checks_pending')
        self.assertEqual(report['authorization'], 'not_checked')
        self.assertIn('review_execution', report['pending_live'])
        self.assertIn('browser_execution', report['pending_live'])

    def test_missing_cli_is_visible_not_self_review(self):
        with patch.object(environment.shutil, 'which', return_value=None):
            report = environment.inspect_environment(self.root, 'product', {'review'})
        self.assertEqual(report['status'], 'missing_prerequisites')
        self.assertIn('codex', report['missing_required'])

    def test_inspection_does_not_run_commands_read_content_or_write(self):
        (self.root / '.env').write_bytes(b'private-sentinel')
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        with patch('subprocess.run', side_effect=AssertionError('No commands')):
            with patch.object(Path, 'read_text', side_effect=AssertionError('No content reads')):
                environment.inspect_environment(self.root, 'product', set())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_engineering_checks_missing_companion_but_product_does_not_require_it(self):
        with patch.object(environment, 'module_present', return_value=False):
            report = environment.inspect_environment(self.root, 'engineering', {'tests'}, playbook_source=True)
        self.assertIn('ai_workflow_harness_lab', report['missing_required'])
        report = environment.inspect_environment(self.root, 'product', set())
        self.assertNotIn('ai_workflow_harness_lab', [c['id'] for c in report['checks']])
        downstream = environment.inspect_environment(self.root, 'engineering', {'tests'})
        self.assertNotIn('ai_workflow_harness_lab', [c['id'] for c in downstream['checks']])
        self.assertIn('project_checks', downstream['pending_live'])

    def test_symlink_instruction_is_not_loaded(self):
        try:
            (self.root / 'AGENTS.md').symlink_to(self.root / 'missing-file')
        except (OSError, NotImplementedError):
            self.skipTest('Host does not permit creating a symlink')
        report = environment.inspect_environment(self.root, 'product', set())
        self.assertIn({'path': 'AGENTS.md', 'status': 'symlink_not_followed'}, report['project_entrypoints'])

    def test_json_cli_returns_pending_for_requested_live_probe(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
                                 '--need', 'browser', '--json'], capture_output=True,
                                text=True, encoding='utf-8', timeout=15)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('browser_execution', json.loads(result.stdout)['pending_live'])

    def test_preview_need_requires_cloudflared_and_live_execution(self):
        def which(name):
            return '/fake/cloudflared' if name == 'cloudflared' else None
        with patch.object(environment.shutil, 'which', side_effect=which):
            report = environment.inspect_environment(self.root, 'product', {'preview'})
        self.assertNotIn('preview_adapter', report['missing_required'])
        self.assertIn('preview_execution', report['pending_live'])

    def test_claim_need_requires_wrangler_and_never_claims_terms_or_auth(self):
        def which(name):
            return '/fake/wrangler' if name == 'wrangler' else None
        with patch.object(environment.shutil, 'which', side_effect=which):
            report = environment.inspect_environment(self.root, 'product', {'claim'})
        self.assertNotIn('claim_adapter', report['missing_required'])
        self.assertIn('claim_execution', report['pending_live'])
        self.assertEqual(report['authorization'], 'not_checked')

    def test_missing_preview_and_claim_adapters_are_visible(self):
        with patch.object(environment.shutil, 'which', return_value=None):
            report = environment.inspect_environment(self.root, 'product', {'preview', 'claim'})
        self.assertIn('preview_adapter', report['missing_required'])
        self.assertIn('claim_adapter', report['missing_required'])

    def test_invalid_root_fails_without_creating_it(self):
        missing = self.root / 'not-created'
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(missing), '--json'],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()

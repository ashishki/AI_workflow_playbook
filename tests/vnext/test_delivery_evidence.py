"""Reference resolution is deliberately weaker than semantic/live verification."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'tools/solution_record.py'
SPEC = importlib.util.spec_from_file_location('delivery_record', SCRIPT)
record = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(record)


def fixture():
    return json.loads((ROOT / 'plugins/playbook-native/skills/playbook/assets/solution-record.example.json').read_text(encoding='utf-8'))


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = fixture()
        self.data['checks'] = [{'claim': 'Scenario', 'status': 'passed', 'evidence': ['check.txt']}]
        self.data['observations'] = []
        (self.root / 'solution.json').write_text(json.dumps(self.data), encoding='utf-8')
        (self.root / 'check.txt').write_text('A statement is not proof of its truth.', encoding='utf-8')

    def test_present_reference_is_not_truth(self):
        result = record.inspect_evidence(self.root, self.data)
        self.assertEqual(result['status'], 'local_references_present')
        self.assertEqual(result['quality'], 'not_assessed')
        self.assertEqual(result['authorization'], 'not_assessed')

    def test_missing_unsafe_and_external_are_explicit(self):
        for ref, status in [('missing.txt', 'missing_or_unsafe'), ('../outside', 'missing_or_unsafe'),
                            ('.env', 'missing_or_unsafe'), ('https://example.org/proof', 'external_unchecked')]:
            with self.subTest(reference=ref):
                self.data['checks'][0]['evidence'] = [ref]
                result = record.inspect_evidence(self.root, self.data)
                self.assertEqual(result['status'], 'unresolved_references')
                self.assertEqual(result['references'][0]['status'], status)

    def test_snapshot_detects_changed_and_uncovered_evidence(self):
        proof = record.snapshot(self.root, 'solution.json', ['check.txt'])
        (self.root / 'check.txt').write_text('Changed', encoding='utf-8')
        result = record.inspect_evidence(self.root, self.data, proof)
        self.assertEqual(result['status'], 'stale_snapshot')
        self.assertEqual(result['references'][0]['status'], 'changed')
        (self.root / 'other.txt').write_text('Other', encoding='utf-8')
        proof = record.snapshot(self.root, 'solution.json', ['other.txt'])
        self.assertEqual(record.inspect_evidence(self.root, self.data, proof)['references'][0]['status'], 'not_in_snapshot')

    def test_empty_evidence_is_not_a_passing_evidence_claim(self):
        self.data['checks'] = []
        self.assertEqual(record.inspect_evidence(self.root, self.data)['status'], 'no_evidence')

    def test_nonstring_observation_reference_rejected(self):
        self.data['observations'] = [{'metric': 'time', 'evidence': [42]}]
        with self.assertRaises(record.RecordError):
            record.inspect_evidence(self.root, self.data)

    def test_strict_cli_fails_missing_reference_without_modifying_record(self):
        (self.root / 'check.txt').unlink()
        before = (self.root / 'solution.json').read_bytes()
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root),
                                 'evidence', '--record', 'solution.json', '--strict'],
                                capture_output=True, text=True, encoding='utf-8', timeout=15)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(before, (self.root / 'solution.json').read_bytes())

    def test_summary_uses_human_status_without_altering_schema(self):
        text = record.render(self.data)
        self.assertIn('не независимое подтверждение', text)
        self.assertNotIn('not_checked /', text)
        self.assertEqual(record.validate(self.data), [])


if __name__ == '__main__':
    unittest.main()

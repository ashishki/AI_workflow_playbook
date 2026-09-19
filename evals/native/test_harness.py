"""Real Harness Lab integration, explicitly FAKE Codex. No model inference."""
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'companion/ai_workflow_harness_lab/src'))
from ai_workflow_harness_lab.adapters.command import CommandAdapter
from ai_workflow_harness_lab.comparison import compare
from ai_workflow_harness_lab.evidence import verify_bundle
from ai_workflow_harness_lab.runner import run_suite, RunError
from ai_workflow_harness_lab.suite_loader import load_suite


class NativeHarnessTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='native-harness-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        cli = bin_dir / 'codex'
        cli.write_text('''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
mode = os.environ['NATIVE_LAB_FAKE_MODE']
prompt = sys.argv[-1]
if mode == 'timeout':
 print(json.dumps({'type': 'thread.started'}), flush=True)
 time.sleep(30)
elif mode == 'corrupt':
 print('corrupt-event')
elif mode == 'incomplete':
 print(json.dumps({'type': 'turn.failed'}))
elif mode == 'mutate-plan' or (mode == 'success' and 'Исправь slugify' in prompt):
 Path('slugs.py').write_text("import re\\ndef slugify(value):\\n return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')\\n")
if mode != 'incomplete':
 Path(sys.argv[sys.argv.index('-o') + 1]).write_text('FAKE CLI: mechanism test only.')
 print(json.dumps({'type': 'turn.completed', 'usage': {}}))
''')
        cli.chmod(0o755)
        self.env = {'PATH': str(bin_dir) + os.pathsep + os.environ['PATH']}
        self.suite = load_suite(ROOT / 'evals/native/harness')
        command = (f'{shlex.quote(sys.executable)} {shlex.quote(str(ROOT / "evals/native/harness_adapter.py"))}'
                   ' --workspace "{workspace}" --prompt-file "{prompt_file}"'
                   ' --output-dir "{output_dir}" --condition {condition} --task-id {task_id}'
                   ' --timeout 1')
        self.adapter = CommandAdapter(command, timeout=10)

    def trial(self, mode='success', condition='playbook', task_ids=None, output=None):
        with patch.dict(os.environ, {**self.env, 'NATIVE_LAB_FAKE_MODE': mode}):
            return run_suite(self.suite, condition, self.adapter, 1,
                             output or self.root / (mode + condition), task_ids=task_ids)

    def test_both_arms_have_verified_bundles_and_comparable_results(self):
        for condition in ('baseline', 'playbook'):
            results = self.trial(condition=condition)
            self.assertEqual(len(results), 2)
            for result in results:
                self.assertTrue(result.valid, result.failure_records)
                self.assertEqual(result.score, 1.0, result.failure_records)
                self.assertEqual(verify_bundle(result.bundle_path), [])
                summary = json.loads((result.output_dir / 'adapter/adapter_summary.json').read_text())
                self.assertEqual(bool(summary['package_hashes']), condition == 'playbook')
                self.assertIn('FAKE CLI', (result.output_dir / 'adapter/final_message.txt').read_text())
        report = compare(self.root / 'successbaseline', self.root / 'successplaybook',
                         self.root / 'comparison', minimum_trials_per_task=1)
        # The lab must not promote scripted execution into empirical evidence.
        self.assertIn('mechanism', report['status'])
        self.assertEqual(report['compatibility_errors'], [])
        self.assertEqual(report['baseline']['mean'], 1.0)
        self.assertEqual(report['candidate']['mean'], 1.0)

    def test_previous_native_version_can_be_the_baseline(self):
        self.adapter.command_template += ' --baseline-package ' + shlex.quote(
            str(ROOT / 'plugins/playbook-native'))
        result, = self.trial(condition='baseline', task_ids=['plan'])
        self.assertTrue(result.valid, result.failure_records)
        self.assertEqual(result.score, 1.0)
        summary = json.loads((result.output_dir / 'adapter/adapter_summary.json').read_text())
        self.assertTrue(summary['package_hashes'])

    def test_unfixed_bug_fails_despite_successful_model_turn(self):
        result, = self.trial('no-fix', task_ids=['backend'])
        self.assertTrue(result.valid)
        self.assertEqual(result.score, 0.0)
        self.assertEqual(verify_bundle(result.bundle_path), [])

    def test_plan_mutation_fails_acceptance(self):
        result, = self.trial('mutate-plan', task_ids=['plan'])
        self.assertTrue(result.valid)
        self.assertEqual(result.score, 0.0)

    def test_bad_and_missing_traces_are_invalid_not_task_passes(self):
        for mode in ('corrupt', 'incomplete', 'timeout'):
            with self.subTest(mode=mode):
                result, = self.trial(mode, task_ids=['plan'])
                self.assertFalse(result.valid)
                self.assertEqual(result.score, 0.0)
                self.assertEqual(verify_bundle(result.bundle_path), [])
                self.assertTrue((result.output_dir / 'adapter/codex_events.jsonl').read_text())

    def test_rerun_preserves_existing_evidence(self):
        result, = self.trial(task_ids=['plan'])
        original = result.bundle_path.read_bytes()
        with self.assertRaises(RunError):
            self.trial(task_ids=['plan'])
        self.assertEqual(result.bundle_path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()

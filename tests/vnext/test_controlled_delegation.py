"""Source/mechanism checks; these do not run a model or prove delegation value."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "engineering" / "experiments" / "controlled-delegation"
SPEC = importlib.util.spec_from_file_location("controlled_delegation_eval", EXPERIMENT / "evaluate.py")
evaluator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluator)


class ControlledDelegationTests(unittest.TestCase):
    def test_unavailable_native_preflight_is_blocked_not_a_worker_failure(self):
        manifest=evaluator.load_manifest()
        runs=[evaluator.empty_run(s['id'],c['id']) for s in manifest['scenarios'] for c in manifest['conditions']]
        for run in runs:
            if run['condition']=='C': run.update(status='BLOCKED',notes='Native subagents unavailable; task not run.')
        value={'schema':evaluator.RESULTS_SCHEMA,'experiment_id':manifest['experiment_id'],'environment':{},'runs':runs}
        self.assertEqual(evaluator.decision(value,manifest)[0],'KEEP_EXPERIMENTAL')

    def observed_shape(self):
        """Synthetic records for source regression tests, never live evidence."""
        manifest=evaluator.load_manifest()
        runs=[]
        for scenario in manifest['scenarios']:
            for condition in manifest['conditions']:
                run=evaluator.empty_run(scenario['id'],condition['id'])
                run.update(status='PASS',outcome_score=90,human_minutes=1,cost_usd=1,
                           input_tokens=1,output_tokens=1,evidence=['source-test-only.txt'],
                           failed_or_conflicting_worker_detected=True,fresh_session_success=True,
                           usage_complete=True,task_status='PASS',mechanical={'status':'PASS'})
                if condition['id']=='C': run['subagents_started']=scenario.get('min_subagents_c',0)
                runs.append(run)
        return manifest,{'schema':evaluator.RESULTS_SCHEMA,'experiment_id':manifest['experiment_id'],'environment':{},'runs':runs}

    def test_review_confirmed_missing_comparison_or_usage_blocks_enablement(self):
        for probe in ('missing_a','missing_quality','partial_usage','missing_usage_confirmation'):
            with self.subTest(probe=probe):
                manifest,value=self.observed_shape()
                for run in value['runs']:
                    if probe=='missing_a' and run['condition']=='A': run['status']='NOT_RUN'
                    if probe=='missing_quality': run['outcome_score']=None
                    if probe=='partial_usage': run['usage_complete']=False
                    if probe=='missing_usage_confirmation': run.pop('usage_complete')
                self.assertEqual(evaluator.decision(value,manifest)[0],'KEEP_EXPERIMENTAL')

    def test_review_confirmed_failure_overrides_pass_claim(self):
        for field in ('task_status','mechanical'):
            with self.subTest(field=field):
                manifest,value=self.observed_shape()
                run=next(r for r in value['runs'] if r['condition']=='C' and r['scenario']=='medium_implementation')
                run[field]='FAIL' if field=='task_status' else {'status':'FAIL'}
                self.assertEqual(evaluator.decision(value,manifest)[0],'REVISE_OR_REJECT')

    def test_review_confirmations_require_booleans(self):
        for field in ('fresh_session_success','failed_or_conflicting_worker_detected','usage_complete'):
            with self.subTest(field=field):
                _,value=self.observed_shape();value['runs'][0][field]='false'
                with self.assertRaises(evaluator.ExperimentError): evaluator.validate_results(value)

    def test_nonfinite_metrics_and_json_are_rejected(self):
        for metric in ('cost_usd','human_minutes','wall_seconds','input_tokens','output_tokens'):
            for invalid in (float('nan'),float('inf')):
                with self.subTest(metric=metric,invalid=invalid):
                    _,value=self.observed_shape();value['runs'][0][metric]=invalid
                    with self.assertRaises(evaluator.ExperimentError): evaluator.validate_results(value)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'invalid.json';path.write_text('{"cost_usd": NaN}')
            with self.assertRaises(evaluator.ExperimentError): evaluator.strict_json(path)

    def test_empty_or_replaced_tests_cannot_pass(self):
        with tempfile.TemporaryDirectory(prefix='delegation-protected-') as tmp:
            root=Path(tmp)/'runs'
            evaluator.prepare(root,seed=1,head='a'*40,model='m',host='h')
            workspace=root/'workspaces/small_fix/A'
            test=workspace/'test_budget.py'
            test.unlink()
            self.assertEqual(evaluator.check_workspace('small_fix',workspace)['status'],'FAIL')
            test.write_text('import unittest\nclass Empty(unittest.TestCase):\n    def test_true(self): self.assertTrue(True)\n')
            result=evaluator.check_workspace('small_fix',workspace)
            self.assertEqual(result['status'],'FAIL')
            self.assertIn('Changed protected fixture: test_budget.py',result['fixture_errors'])

    def test_known_failure_is_not_hidden_by_other_blocked_run(self):
        manifest,value=self.observed_shape()
        next(r for r in value['runs'] if r['condition']=='C' and r['scenario']=='parallel_research')['status']='FAIL'
        next(r for r in value['runs'] if r['condition']=='C' and r['scenario']=='medium_implementation')['status']='BLOCKED'
        self.assertEqual(evaluator.decision(value,manifest)[0],'REVISE_OR_REJECT')

    def test_missing_cost_cannot_enable_delegation(self):
        manifest,value=self.observed_shape()
        for run in value['runs']: run['cost_usd']=None
        self.assertEqual(evaluator.decision(value,manifest)[0],'KEEP_EXPERIMENTAL')

    def test_reviewer_is_separate_from_small_task_workers(self):
        manifest,value=self.observed_shape()
        small=next(r for r in value['runs'] if r['condition']=='C' and r['scenario']=='small_fix')
        small.update(subagents_started=1,review_subagents_started=1,implementation_subagents_started=0,max_parallel=1,max_depth=1)
        evaluator.validate_results(value)
        self.assertEqual(evaluator.decision(value,manifest)[0],'ENABLE_CONDITIONALLY')

    def test_c_worker_minimum_is_enforced_and_exposed_in_prepare(self):
        manifest,value=self.observed_shape()
        conflict=next(r for r in value['runs'] if r['condition']=='C' and r['scenario']=='conflict_detection')
        conflict['subagents_started']=1
        self.assertEqual(evaluator.decision(value,manifest)[0],'REVISE_OR_REJECT')
        with tempfile.TemporaryDirectory(prefix='delegation-bound-') as tmp:
            root=Path(tmp)/'runs';evaluator.prepare(root,seed=1,head='a'*40,model='m',host='h')
            self.assertIn('2–3',(root/'workspaces/conflict_detection/C/AGENTS.md').read_text())

    def test_reference_is_packaged_and_linked(self):
        reference = ROOT / "plugins/playbook-native/skills/playbook/references/delegation.md"
        self.assertTrue(reference.is_file())
        self.assertGreater(len(reference.read_text(encoding="utf-8")), 1000)
        skill = (ROOT / "plugins/playbook-native/skills/playbook/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/delegation.md", skill)

        spec = importlib.util.spec_from_file_location("delegation_native_build", ROOT / "distribution/native/build.py")
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        _, payload = build.collect()
        for prefix in ("plugins/playbook-native/skills/playbook/", "Мой проект/.agents/skills/playbook/"):
            self.assertIn(prefix + "references/delegation.md", payload)

    def test_version_marker_matches_plugin(self):
        plugin = json.loads((ROOT / "plugins/playbook-native/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
        marker = (ROOT / "plugins/playbook-native/skills/playbook/assets/project-block.md").read_text(encoding="utf-8")
        self.assertEqual(plugin["version"], "0.2.0-preview.4")
        self.assertIn("v" + plugin["version"], marker)
        self.assertIn(plugin["version"], (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_prepare_creates_isolated_comparison(self):
        with tempfile.TemporaryDirectory(prefix="delegation-prepare-") as tmp:
            output = Path(tmp) / "runs"
            result = evaluator.prepare(output, seed=7, head="a" * 40, model="test-model", host="test-host")
            self.assertEqual(result["workspaces"], 15)
            plan = evaluator.strict_json(output / "run-plan.json")
            results = evaluator.strict_json(output / "results.json")
            self.assertEqual(len(plan["order"]), 15)
            self.assertEqual(len(results["runs"]), 15)
            self.assertTrue(all(run["status"] == "NOT_RUN" for run in results["runs"]))
            self.assertFalse((output / "workspaces/small_fix/A/.agents").exists())
            self.assertTrue((output / "workspaces/small_fix/B/.agents/skills/playbook/SKILL.md").is_file())
            self.assertTrue((output / "workspaces/small_fix/C/.agents/skills/playbook/references/delegation.md").is_file())

    def test_pass_without_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="delegation-result-") as tmp:
            output = Path(tmp) / "runs"
            evaluator.prepare(output, seed=1, head="b" * 40, model="m", host="h")
            value = evaluator.strict_json(output / "results.json")
            value["runs"][0]["status"] = "PASS"
            with self.assertRaises(evaluator.ExperimentError):
                evaluator.validate_results(value)

    def test_not_run_report_stays_experimental(self):
        with tempfile.TemporaryDirectory(prefix="delegation-report-") as tmp:
            output = Path(tmp) / "runs"
            report_dir = Path(tmp) / "report"
            evaluator.prepare(output, seed=1, head="c" * 40, model="m", host="h")
            result = evaluator.make_report(evaluator.strict_json(output / "results.json"), report_dir)
            self.assertEqual(result["decision"], "KEEP_EXPERIMENTAL")
            text = (report_dir / "REPORT_RU.md").read_text(encoding="utf-8")
            self.assertIn("Не все реальные C-прогоны выполнены", text)
            self.assertNotIn("ENABLE_CONDITIONALLY**", text)

    def test_unfixed_code_fixtures_fail_mechanical_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="delegation-fixtures-") as tmp:
            output = Path(tmp) / "runs"
            evaluator.prepare(output, seed=2, head="d" * 40, model="m", host="h")
            for scenario in ("small_fix", "medium_implementation", "fresh_session"):
                with self.subTest(scenario=scenario):
                    result = evaluator.check_workspace(scenario, output / "workspaces" / scenario / "A")
                    self.assertEqual(result["status"], "FAIL")

    def test_controlled_route_violation_is_not_accepted(self):
        manifest = evaluator.load_manifest()
        runs = []
        for scenario in manifest["scenarios"]:
            for condition in manifest["conditions"]:
                run = evaluator.empty_run(scenario["id"], condition["id"])
                run.update({"status": "PASS", "outcome_score": 90, "human_minutes": 1,
                            "wall_seconds": 1, "cost_usd": 1, "evidence": ["evidence.txt"],
                            "failed_or_conflicting_worker_detected": True,
                            "fresh_session_success": True})
                runs.append(run)
        small_c = next(run for run in runs if run["scenario"] == "small_fix" and run["condition"] == "C")
        small_c["subagents_started"] = 1
        value = {"schema": evaluator.RESULTS_SCHEMA, "experiment_id": manifest["experiment_id"],
                 "environment": {}, "runs": runs}
        outcome, reasons = evaluator.decision(value, manifest)
        self.assertEqual(outcome, "REVISE_OR_REJECT")
        self.assertTrue(any("Маленькая задача" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()

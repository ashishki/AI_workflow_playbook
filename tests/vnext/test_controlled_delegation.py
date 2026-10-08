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

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
        for prefix in ("plugins/playbook-native/skills/playbook/", "ĞœĞ¾Ğ¹ Ğ¿Ñ€Ğ¾ĞµĞºÑ‚/.agents/skills/playbook/"):
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
            result = evaluator.make_report(evaluator.strict_json(output / "results.json"), report_diŠBˆÙ[‹˜\ÜÙ\\]X[
™\İ[È™XÚ\Ú[Ûˆ—K’ÑQTÑVT’SQS•SŠBˆ^H
™\ÜÙ\ˆÈ”‘TÔ•Ô•K›YŠKœ™XYİ^
[˜ÛÙ[™ÏH]‹NŠBˆÙ[‹˜\ÜÙ\[Š´'t-H4,´`t-H4`4-t,4.ôc4/tbô-HËt/ô`4/´,ô/´/tbÈ4,´bô/ô/´.ô/t-t/tbÈ‹^
BˆÙ[‹˜\ÜÙ\›İ[Š‘SP“WĞÓÓ‘USÓSJŠˆ‹^
B‚ˆYˆ\İİ[™š^YØÛÙWÙš^\™\×Ù˜Z[ÛYXÚ[šXØ[ØXØÙ\[˜ÙJÙ[ŠN‚ˆÚ][\š[K•[\Ü˜\Q\™XİÜJ™Yš^H™[YØ][Û‹Yš^\™\ËHŠH\È\‚ˆİ]]H]
\
HÈœ[œÈ‚ˆ]˜[X]Ü‹œ™\\™Jİ]]ÙYYL‹XYH™ˆ
ˆ[Ù[H›H‹ÜİHšŠBˆ›ÜˆØÙ[˜\š[È[ˆ
œÛX[Ùš^‹›YY][WÚ[\[Y[][Ûˆ‹™œ™\ÚÜÙ\ÜÚ[ÛˆŠN‚ˆÚ]Ù[‹œİX•\İ
ØÙ[˜\š[Ï\ØÙ[˜\š[ÊN‚ˆ™\İ[H]˜[X]Ü‹˜ÚXÚ×İÛÜšÜÜXÙJØÙ[˜\š[Ëİ]]ÈÛÜšÜÜXÙ\ÈˆÈØÙ[˜\š[ÈÈHŠBˆÙ[‹˜\ÜÙ\\]X[
™\İ[Èœİ]\È—K‘RSŠB‚ˆYˆ\İØÛÛ›ÛYÜ›İ]Wİš[Û][Û—Ú\×Û›İØXØÙ\Y
Ù[ŠN‚ˆX[šY™\İH]˜[X]Ü‹›ØYÛX[šY™\İ

Bˆ[œÈH×Bˆ›ÜˆØÙ[˜\š[È[ˆX[šY™\İÈœØÙ[˜\š[ÜÈ—N‚ˆ›ÜˆÛÛ™][Ûˆ[ˆX[šY™\İÈ˜ÛÛ™][ÛœÈ—N‚ˆ[ˆH]˜[X]Ü‹™[\WÜ[ŠØÙ[˜\š[ÖÈšY—KÛÛ™][Û–ÈšY—JBˆ[‹\]JÈœİ]\Èˆ”TÔÈ‹›İ]ÛÛYWÜØÛÜ™HˆLš[X[—ÛZ[]\ÈˆKˆØ[ÜÙXÛÛ™ÈˆK˜ÛÜİİ\ÙˆK™]šY[˜ÙHˆÈ™]šY[˜ÙK—Kˆ™˜Z[YÛÜ—ØÛÛ™›Xİ[™×İÛÜšÙ\—Ù]XİYˆYKˆ™œ™\ÚÜÙ\ÜÚ[Û—ÜİXØÙ\ÜÈˆY_JBˆ[œË˜\[™
[ŠBˆÛX[ØÈH™^
[ˆ›Üˆ[ˆ[ˆ[œÈYˆ[–ÈœØÙ[˜\š[È—HOHœÛX[Ùš^ˆ[™[–È˜ÛÛ™][Ûˆ—HOHÈŠBˆÛX[ØÖÈœİX˜YÙ[×Üİ\Y—HHBˆ˜[YHHÈœØÚ[XHˆ]˜[X]Ü‹”‘TÕS×ÔĞÒSPK™^\š[Y[ÚYˆX[šY™\İÈ™^\š[Y[ÚY—Kˆ™[š\›Û›Y[ˆßKœ[œÈˆ[œßBˆİ]ÛÛYK™X\ÛÛœÈH]˜[X]Ü‹™XÚ\Ú[ÛŠ˜[YKX[šY™\İ
BˆÙ[‹˜\ÜÙ\\]X[
İ]ÛÛYK”‘U’TÑWÓÔ—Ô‘R‘PÕŠBˆÙ[‹˜\ÜÙ\YJ[J´'4,4.ô-t/tc4.´,4cÈ4-ô,4-4,4aô,ˆ[ˆ™X\ÛÛˆ›Üˆ™X\ÛÛˆ[ˆ™X\ÛÛœÊJB‚‚šYˆ×Û˜[YW×ÈOH—×ÛXZ[—×È‚ˆ[š]\İ›XZ[Š
B
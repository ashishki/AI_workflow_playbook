"""Offline contracts only; no inference, browser or real heavy executions."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('engineering_addon_bundle', HERE / 'bundle.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / 'Проект with spaces'
        self.root.mkdir()

    def test_four_portable_sources(self):
        self.assertEqual(set(b.check()['source_sha256']), set(b.SKILLS))
        self.assertEqual(b.check()['live_hosts'], 'NOT_RUN')

    def test_host_bodies_match_and_both_are_explicit_only(self):
        for name in b.SKILLS:
            codex = b.payload('codex', [name])
            claude = b.payload('claude', [name])
            c = codex[f'.agents/skills/{name}/SKILL.md']
            a = claude[f'.claude/skills/{name}/SKILL.md']
            self.assertEqual(c, a.replace(b'disable-model-invocation: true\n', b''))
            self.assertEqual(c, b.source_bytes(name))
            self.assertIn(b'allow_implicit_invocation: false', codex[f'.agents/skills/{name}/agents/openai.yaml'])
            self.assertNotIn(f'.claude/skills/{name}/agents/openai.yaml', claude)

    def test_plan_has_no_side_effects(self):
        result = b.install(self.root, 'codex')
        self.assertEqual(result['status'], 'planned')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_install_verify_both_hosts_and_unicode_path(self):
        for host in b.HOSTS:
            self.assertEqual(b.install(self.root, host, apply=True)['status'], 'installed_files_verified')
            self.assertEqual(b.verify(self.root, host)['status'], 'files_match')

    def test_selective_install_does_not_add_other_skills(self):
        name = b.SKILLS[0]
        b.install(self.root, 'codex', [name], apply=True)
        self.assertEqual([p.name for p in (self.root / '.agents/skills').iterdir()], [name])
        self.assertEqual(b.verify(self.root, 'codex', [name])['skills'], [name])

    def test_existing_owner_files_and_instructions_unchanged(self):
        originals = {'AGENTS.md': b'owner rules\r\n', 'CLAUDE.md': b'claude rules\n',
                     '.gitignore': b'.private/\n', 'app.txt': b'working app'}
        for name, value in originals.items():
            (self.root / name).write_bytes(value)
        other = self.root / '.agents/skills/other/SKILL.md'
        other.parent.mkdir(parents=True)
        other.write_text('custom skill', encoding='utf-8')
        b.install(self.root, 'codex', apply=True)
        for name, value in originals.items():
            self.assertEqual((self.root / name).read_bytes(), value)
        self.assertEqual(other.read_text(encoding='utf-8'), 'custom skill')

    def test_preflight_rejects_all_collisions_before_writing(self):
        target = self.root / '.agents/skills' / b.SKILLS[-1]
        target.mkdir(parents=True)
        (target / 'owner.txt').write_text('keep', encoding='utf-8')
        with self.assertRaises(b.BundleError):
            b.install(self.root, 'codex', apply=True)
        self.assertFalse((self.root / '.agents/skills' / b.SKILLS[0]).exists())
        self.assertEqual((target / 'owner.txt').read_text(encoding='utf-8'), 'keep')

    def test_reinstall_stops_without_overwrite(self):
        b.install(self.root, 'claude', apply=True)
        with self.assertRaises(b.BundleError):
            b.install(self.root, 'claude', apply=True)

    def test_verify_rejects_edit_missing_and_extra_files(self):
        for mode in ('edit', 'missing', 'extra'):
            with self.subTest(mode=mode):
                root = self.root / mode
                root.mkdir()
                name = b.SKILLS[0]
                b.install(root, 'codex', [name], apply=True)
                file = root / '.agents/skills' / name / 'SKILL.md'
                if mode == 'edit':
                    file.write_bytes(file.read_bytes() + b'\nedit\n')
                elif mode == 'missing':
                    file.unlink()
                else:
                    (file.parent / 'unknown.txt').write_text('unknown', encoding='utf-8')
                with self.assertRaises(b.BundleError):
                    b.verify(root, 'codex', [name])

    def test_build_manifest_matches_exact_payload(self):
        for host in b.HOSTS:
            output = self.root / host
            b.build(output, host)
            manifest = json.loads((output / 'BUNDLE.json').read_text(encoding='utf-8'))
            expected = b.payload(host)
            self.assertEqual(set(manifest['files']), set(expected))
            for path, digest in manifest['files'].items():
                self.assertEqual(hashlib.sha256((output / path).read_bytes()).hexdigest(), digest)
            self.assertEqual(manifest['live_compatibility'], 'NOT_RUN')
            self.assertEqual(b.verify(output, host)['status'], 'files_match')

    def test_build_is_deterministic(self):
        b.build(self.root / 'one', 'codex')
        b.build(self.root / 'two', 'codex')
        self.assertEqual((self.root / 'one/BUNDLE.json').read_bytes(),
                         (self.root / 'two/BUNDLE.json').read_bytes())

    def test_build_refuses_existing_output(self):
        with self.assertRaises(b.BundleError):
            b.build(self.root, 'codex')

    def test_unknown_host_or_selection_cannot_write(self):
        for host, names in [('x', None), ('codex', ['../outside']), ('claude', [b.SKILLS[0]] * 2)]:
            with self.assertRaises(b.BundleError):
                b.install(self.root, host, names, apply=True)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_file_in_parent_path_is_rejected(self):
        (self.root / '.agents').write_text('keep', encoding='utf-8')
        with self.assertRaises(b.BundleError):
            b.install(self.root, 'codex', apply=True)
        self.assertEqual((self.root / '.agents').read_text(encoding='utf-8'), 'keep')

    def test_linked_destination_is_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        try:
            (self.root / '.agents').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Creating symlinks not permitted on this runner')
        with self.assertRaises(b.BundleError):
            b.install(self.root, 'codex', apply=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_linked_source_is_rejected(self):
        source = self.root / 'sources'
        name = b.SKILLS[0]
        (source / name).mkdir(parents=True)
        file = self.root / 'outside.md'
        file.write_bytes(b.source_bytes(name))
        try:
            (source / name / 'SKILL.md').symlink_to(file)
        except OSError:
            self.skipTest('Creating symlinks not permitted on this runner')
        with self.assertRaises(b.BundleError):
            b.payload('codex', [name], source)

    def test_canonical_host_macros_and_bad_header_are_rejected(self):
        source = self.root / 'sources'
        name = b.SKILLS[0]
        (source / name).mkdir(parents=True)
        file = source / name / 'SKILL.md'
        valid = b.source_bytes(name)
        for value in (valid + b'\n${CLAUDE_SKILL_DIR}\n', valid.replace(b'name: ', b'context: fork\nname: '), b'invalid'):
            file.write_bytes(value)
            with self.assertRaises(b.BundleError):
                b.payload('claude', [name], source)

    def test_no_silent_host_or_tool_execution_in_doctor(self):
        output = io.StringIO()
        with patch.object(b.shutil, 'which', return_value=None), contextlib.redirect_stdout(output):
            self.assertEqual(b.main(['doctor']), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result['execution'], 'NOT_RUN')
        self.assertEqual(result['auth'], 'NOT_CHECKED')
        self.assertFalse(any(result['tools'].values()))

    def test_partial_install_not_reported_as_ready(self):
        name = b.SKILLS[0]
        folder = self.root / '.agents/skills' / name
        folder.mkdir(parents=True)
        (folder / 'SKILL.md').write_bytes(b.source_bytes(name))
        with self.assertRaises(b.BundleError):
            b.verify(self.root, 'codex', [name])
        with self.assertRaises(b.BundleError):
            b.install(self.root, 'codex', [name], apply=True)

    def test_cli_failure_has_nonzero_status(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(b.main(['verify', '--host', 'codex', '--project', str(self.root)]), 2)

    def test_source_contract_keeps_scope_and_failure_guards(self):
        change = b.source_bytes(b.SKILLS[0]).decode('utf-8')
        clarify = b.source_bytes(b.SKILLS[1]).decode('utf-8')
        browser = b.source_bytes(b.SKILLS[2]).decode('utf-8')
        heavy = b.source_bytes(b.SKILLS[3]).decode('utf-8')
        self.assertIn('Tests read are not tests run', change)
        self.assertIn('next bounded step', clarify)
        self.assertIn('untrusted', browser)
        self.assertIn('--no-skip-ci', heavy)
        self.assertIn('--on-timeout fail', heavy)
        self.assertIn('not the execution timeout', heavy)


if __name__ == '__main__':
    unittest.main()

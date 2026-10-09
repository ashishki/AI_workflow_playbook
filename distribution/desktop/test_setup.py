"""Offline setup mechanism tests; not a model, browser, clean-machine or user trial."""
from __future__ import annotations
import importlib.util
import contextlib
import io
import json
import shlex
import shutil
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'distribution' / 'desktop'))
sys.path.insert(0, str(ROOT / 'distribution' / 'native'))

import setup_core
import desktop_runtime
import desktop_setup

spec = importlib.util.spec_from_file_location('desktop_native_build', ROOT / 'distribution/native/build.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class SetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='playbook-desktop-tests-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.base = Path(cls.temp.name)
        result = native.build(cls.base / 'kit')
        cls.kit_path = Path(result['archive'])
        cls.kit = setup_core.Kit.load(cls.kit_path, result['sha256'])

    def new_project(self):
        path = Path(tempfile.mkdtemp(prefix='Проект с пробелами-', dir=self.base))
        (path / 'notes.txt').write_text('owner data', encoding='utf-8')
        (path / 'AGENTS.md').write_bytes(b'# Owner rules\r\nDo not publish.\r\n')
        (path / '.gitignore').write_bytes(b'owner-cache/\r\n')
        return path

    def test_documented_managed_review_command_reaches_runner_parser(self):
        root = self.new_project()
        text = (ROOT / 'plugins/playbook-native/skills/playbook/references/review.md').read_text(encoding='utf-8')
        example = next(line.strip() for line in text.splitlines() if line.strip().startswith('<local-helper> '))
        command = [str(root) if token == '<project>' else token for token in shlex.split(example)]
        self.assertEqual(command[:3], ['<local-helper>', 'helper', 'review'])
        with patch.object(desktop_runtime, 'verified_binary', return_value=None), contextlib.redirect_stdout(io.StringIO()):
            # --help exercises the actual bundled runner's parser without
            # authentication, subprocess inference or fabricated role evidence.
            self.assertEqual(desktop_setup.helper(self.kit, 'review', command[3:] + ['--help']), 0)

    def test_install_remove_and_rollback_preserve_owner_files(self):
        root = self.new_project()
        before_agents = (root / 'AGENTS.md').read_bytes()
        before_ignore = (root / '.gitignore').read_bytes()
        installed = setup_core.apply(
            setup_core.plan(root, self.kit, 'install', ['playbook-helper']),
            consent=True)
        self.assertEqual(installed['status'], 'complete')
        self.assertEqual(setup_core.installation_status(root)['installation'], 'files_verified')
        self.assertIn(setup_core.BEGIN.encode(), (root / 'AGENTS.md').read_bytes())
        self.assertEqual((root / 'notes.txt').read_text(encoding='utf-8'), 'owner data')
        setup_core.apply(setup_core.plan(root, self.kit, 'remove'), consent=True)
        self.assertEqual((root / 'AGENTS.md').read_bytes(), before_agents)
        self.assertEqual((root / '.gitignore').read_bytes(), before_ignore)
        self.assertEqual((root / 'notes.txt').read_text(encoding='utf-8'), 'owner data')
        setup_core.rollback(root, consent=True)
        self.assertEqual(setup_core.installation_status(root)['installation'], 'files_verified')

    def test_modified_managed_file_blocks_update_and_remove(self):
        root = self.new_project()
        setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
        skill = root / '.agents/skills/playbook/SKILL.md'
        skill.write_text(skill.read_text(encoding='utf-8') + '\nowner edit\n', encoding='utf-8')
        with self.assertRaises(setup_core.SetupError):
            setup_core.plan(root, self.kit, 'update')
        with self.assertRaises(setup_core.SetupError):
            setup_core.plan(root, self.kit, 'remove')

    def test_diagnostics_verify_owned_blocks_and_namespace_without_rejecting_owner_rules(self):
        root = self.new_project()
        setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
        agents = root / 'AGENTS.md'
        agents.write_bytes(agents.read_bytes() + b'\n# More owner rules\n')
        self.assertEqual(setup_core.installation_status(root)['installation'], 'files_verified')
        for name in ('AGENTS.md', '.gitignore'):
            path = root / name
            original = path.read_bytes()
            path.write_bytes(b'Owner replaced instructions\n')
            self.assertEqual(setup_core.installation_status(root)['installation'], 'modified')
            with self.assertRaises(setup_core.SetupError):
                setup_core.plan(root, self.kit, 'update')
            path.write_bytes(original)
        (root / '.agents/skills/playbook/custom.md').write_text('owner addition')
        self.assertEqual(setup_core.installation_status(root)['installation'], 'modified')

    def test_interrupted_write_can_be_rolled_back_without_losing_owner_data(self):
        root = self.new_project()
        original = {name: (root / name).read_bytes() for name in ('notes.txt', 'AGENTS.md', '.gitignore')}
        atomic = setup_core.atomic
        writes = 0
        def interrupt(project, name, data):
            nonlocal writes
            if name.startswith(setup_core.PREFIXES):
                writes += 1
                if writes == 2:
                    raise OSError('simulated interrupted write')
            return atomic(project, name, data)
        with patch.object(setup_core, 'atomic', side_effect=interrupt):
            with self.assertRaisesRegex(OSError, 'simulated interrupted write'):
                setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
        with self.assertRaises(setup_core.SetupError):
            setup_core.plan(root, self.kit, 'install')
        self.assertEqual(setup_core.installation_status(root)['installation'], 'interrupted')
        setup_core.rollback(root, consent=True)
        for name, data in original.items():
            self.assertEqual((root / name).read_bytes(), data)
        self.assertEqual(setup_core.installation_status(root)['installation'], 'not_managed')
        setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
        self.assertEqual(setup_core.installation_status(root)['installation'], 'files_verified')

    def test_final_journal_write_failure_is_interrupted_until_explicit_rollback(self):
        root = self.new_project()
        original = {name: (root / name).read_bytes() for name in ('notes.txt', 'AGENTS.md', '.gitignore')}
        atomic = setup_core.atomic
        def interrupt(project, name, data):
            if name == setup_core.JOURNAL and data and json.loads(data)['status'] == 'complete':
                raise OSError('interrupted final journal write')
            return atomic(project, name, data)
        with patch.object(setup_core, 'atomic', side_effect=interrupt):
            with self.assertRaisesRegex(OSError, 'interrupted final journal write'):
                setup_core.apply(setup_core.plan(root, self.kit, 'install', ['playbook-helper']), consent=True)
        state = setup_core.installation_status(root)
        self.assertEqual(state['modified_count'], 0)  # All owned writes finished.
        self.assertEqual(state['installation'], 'interrupted')
        self.assertEqual(state['setup_transaction'], 'pending')
        self.assertEqual(state['setup_readiness'], 'not_ready')
        text = desktop_setup.diagnostic_text(desktop_setup.report(self.kit, root))
        self.assertIn('«Вернуть установку»', text)
        self.assertNotIn('Состояние файлов: файлы проверены', text)
        with self.assertRaises(setup_core.SetupError):
            setup_core.plan(root, self.kit, 'update')
        setup_core.rollback(root, consent=True)
        for name, data in original.items():
            self.assertEqual((root / name).read_bytes(), data)
        self.assertEqual(setup_core.installation_status(root)['installation'], 'not_managed')

    def test_missing_or_tampered_helper_pointer_blocks_readiness_and_destructive_retry(self):
        for mutation in ('missing', 'different_command', 'invalid_json'):
            with self.subTest(mutation=mutation):
                root = self.new_project()
                setup_core.apply(setup_core.plan(root, self.kit, 'install', ['playbook-helper']), consent=True)
                pointer = root / setup_core.RUNTIME
                original = pointer.read_bytes()
                if mutation == 'missing':
                    pointer.unlink()
                elif mutation == 'different_command':
                    value = json.loads(original)
                    value['command'] = ['unrelated-helper']
                    pointer.write_bytes(setup_core.json_bytes(value))
                else:
                    pointer.write_bytes(b'{broken')
                changed = pointer.read_bytes() if pointer.exists() else None
                state = setup_core.installation_status(root)
                self.assertEqual(state['installation'], 'modified')
                self.assertEqual(state['modified_count'], 1)
                self.assertEqual(state['helper_pointer'], 'missing' if mutation == 'missing' else 'modified')
                self.assertEqual(state['setup_readiness'], 'not_ready')
                self.assertIn('нужна проверка', desktop_setup.diagnostic_text(desktop_setup.report(self.kit, root)))
                for action in ('update', 'remove'):
                    with self.assertRaisesRegex(setup_core.SetupError, 'helper pointer'):
                        setup_core.plan(root, self.kit, action, ['replacement-helper'])
                self.assertEqual(pointer.read_bytes() if pointer.exists() else None, changed)
                self.assertEqual((root / 'notes.txt').read_text(encoding='utf-8'), 'owner data')
                pointer.write_bytes(original)
                self.assertEqual(setup_core.installation_status(root)['setup_readiness'], 'installation_verified')

    def test_helper_pointer_mismatch_is_reported_and_explicit_update_refreshes_it(self):
        root = self.new_project()
        before = {name: (root / name).read_bytes() for name in ('notes.txt', 'AGENTS.md', '.gitignore')}
        setup_core.apply(setup_core.plan(root, self.kit, 'install', ['previous-helper']), consent=True)
        saved = (root / setup_core.RUNTIME).read_bytes()
        value = desktop_setup.report(self.kit, root, helper_command=['current-helper'])
        self.assertEqual(value['installation']['helper_pointer'], 'mismatch')
        self.assertEqual(value['installation']['installation'], 'modified')
        self.assertEqual(value['installation']['setup_readiness'], 'not_ready')
        self.assertIn('расположение отличается от этого комплекта', desktop_setup.diagnostic_text(value))
        self.assertEqual((root / setup_core.RUNTIME).read_bytes(), saved)  # Diagnostic is read-only.
        setup_core.apply(setup_core.plan(root, self.kit, 'update', ['current-helper']), consent=True)
        self.assertEqual(desktop_setup.report(self.kit, root, helper_command=['current-helper'])['installation']['setup_readiness'],
                         'installation_verified')
        setup_core.apply(setup_core.plan(root, self.kit, 'remove'), consent=True)
        for name, data in before.items():
            self.assertEqual((root / name).read_bytes(), data)
        setup_core.rollback(root, consent=True)
        self.assertEqual(setup_core.installation_status(root, expected_command=['current-helper'])['setup_readiness'],
                         'installation_verified')

    def test_helper_payload_mismatch_is_not_verified_even_at_the_same_location(self):
        root = self.new_project()
        setup_core.apply(setup_core.plan(root, self.kit, 'install', ['playbook-helper']), consent=True)
        original_pointer = (root / setup_core.RUNTIME).read_bytes()
        contents = dict(self.kit.files)
        manifest = json.loads(contents['PACKAGE.json'])
        manifest['version'] = '0.2.0-preview.5'
        contents['PACKAGE.json'] = setup_core.json_bytes(manifest)
        archive = root.parent / (root.name + '-synthetic-next.zip')
        with zipfile.ZipFile(archive, 'w') as zipped:
            for name, data in contents.items():
                zipped.writestr('Playbook/' + name, data)
        next_kit = setup_core.Kit.load(archive, setup_core.digest(archive.read_bytes()))
        value = desktop_setup.report(next_kit, root, helper_command=['playbook-helper'])
        self.assertEqual(value['installation']['helper_pointer'], 'mismatch')
        self.assertEqual(value['installation']['setup_readiness'], 'not_ready')
        self.assertEqual((root / setup_core.RUNTIME).read_bytes(), original_pointer)
        setup_core.apply(setup_core.plan(root, next_kit, 'update', ['playbook-helper']), consent=True)
        self.assertEqual(desktop_setup.report(next_kit, root, helper_command=['playbook-helper'])['installation']['setup_readiness'],
                         'installation_verified')

    def test_legacy_pointer_requires_exact_transaction_bytes_and_migrates_on_update(self):
        root = self.new_project()
        setup_core.apply(setup_core.plan(root, self.kit, 'install', ['playbook-helper']), consent=True)
        record = root / setup_core.RECORD
        value = json.loads(record.read_bytes())
        del value['runtime_sha256']
        record.write_bytes(setup_core.json_bytes(value))
        self.assertEqual(setup_core.installation_status(root)['helper_pointer'], 'verified')
        setup_core.apply(setup_core.plan(root, self.kit, 'update', ['playbook-helper']), consent=True)
        self.assertIn('runtime_sha256', json.loads(record.read_bytes()))
        # Loss of both identities cannot attest the old pointer or allow overwrite.
        value = json.loads(record.read_bytes())
        del value['runtime_sha256']
        record.write_bytes(setup_core.json_bytes(value))
        journal = root / setup_core.JOURNAL
        transaction = json.loads(journal.read_bytes())
        transaction['changes'].pop(setup_core.RUNTIME, None)
        journal.write_bytes(setup_core.json_bytes(transaction))
        self.assertEqual(setup_core.installation_status(root)['installation'], 'unverified')
        self.assertEqual(setup_core.installation_status(root)['setup_readiness'], 'not_ready')
        with self.assertRaisesRegex(setup_core.SetupError, 'helper pointer'):
            setup_core.plan(root, self.kit, 'update')

    def test_install_without_helper_pointer_does_not_claim_setup_readiness(self):
        root = self.new_project()
        setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
        state = setup_core.installation_status(root)
        self.assertEqual(state['helper_pointer'], 'not_configured')
        self.assertEqual(state['setup_readiness'], 'not_ready')

    def test_unmanaged_skill_namespace_is_not_overwritten(self):
        root = self.new_project()
        foreign = root / '.agents/skills/playbook'
        foreign.mkdir(parents=True)
        (foreign / 'custom.md').write_text('keep', encoding='utf-8')
        with self.assertRaises(setup_core.SetupError):
            setup_core.plan(root, self.kit, 'install')
        self.assertEqual((foreign / 'custom.md').read_text(encoding='utf-8'), 'keep')

    def test_interrupted_transaction_blocks_retry(self):
        root = self.new_project()
        setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
        journal = root / setup_core.JOURNAL
        value = json.loads(journal.read_text(encoding='utf-8'))
        value['status'] = 'pending'
        journal.write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaises(setup_core.SetupError):
            setup_core.plan(root, self.kit, 'update')

    def test_missing_foreign_or_invalid_journal_blocks_mutations_at_plan_and_apply(self):
        for variant in ('missing', 'foreign_root', 'wrong_schema', 'wrong_phase', 'moved'):
            with self.subTest(variant=variant):
                root = self.new_project()
                setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
                update = setup_core.plan(root, self.kit, 'update')
                removal = setup_core.plan(root, self.kit, 'remove')
                journal = root / setup_core.JOURNAL
                value = json.loads(journal.read_bytes())
                if variant == 'missing':
                    journal.unlink()
                elif variant == 'moved':
                    moved = root.with_name(root.name + '-copied')
                    shutil.copytree(root, moved)
                    root = moved
                    update.root = root
                    removal.root = root
                else:
                    value[{'foreign_root': 'root', 'wrong_schema': 'schema', 'wrong_phase': 'status'}[variant]] = 'invalid'
                    journal.write_bytes(setup_core.json_bytes(value))
                before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                self.assertEqual(setup_core.installation_status(root)['installation'], 'interrupted')
                for action, proposal in (('update', update), ('remove', removal)):
                    with self.assertRaisesRegex(setup_core.SetupError, 'transaction'):
                        setup_core.plan(root, self.kit, action)
                    with self.assertRaisesRegex(setup_core.SetupError, 'transaction'):
                        setup_core.apply(proposal, consent=True)
                after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                self.assertEqual(before, after)

    def test_support_report_does_not_include_project_path_or_claim_live_checks(self):
        root = self.new_project()
        setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
        value = desktop_setup.report(self.kit, root)
        serialized = json.dumps(value, ensure_ascii=False)
        self.assertNotIn(str(root), serialized)
        self.assertEqual(value['model_trial'], 'not_run')
        self.assertEqual(value['browser_trial'], 'not_run')
        self.assertEqual(value['user_trial'], 'not_run')

    def test_login_probe_does_not_attest_review_or_browser(self):
        root = self.new_project()
        probe = {'codex': 'launched', 'auth': 'cli_reports_login', 'review': 'not_run', 'browser': 'not_run'}
        with patch.object(desktop_runtime, 'probe', return_value=probe):
            value = desktop_setup.report(self.kit, root, probe_codex=True)
        self.assertEqual(value['runtime']['auth'], 'cli_reports_login')
        self.assertEqual(value['model_trial'], 'not_run')
        self.assertEqual(value['browser_trial'], 'not_run')

    def test_packaged_inventory_helper_runs_without_system_cli(self):
        root = self.new_project()
        setup_core.apply(setup_core.plan(root, self.kit, 'install'), consent=True)
        self.assertIn(desktop_setup.helper(
            self.kit, 'inventory', ['--root', str(root), '--json']), {0, 1})

    def test_runtime_plan_is_pinned_and_offline(self):
        with patch.object(desktop_runtime.urllib.request.OpenerDirector, 'open',
                          side_effect=AssertionError('no network')):
            value = desktop_runtime.asset_plan()
        self.assertEqual(value['version'], desktop_runtime.VERSION)
        self.assertRegex(value['sha256'], r'^[0-9a-f]{64}$')
        self.assertGreater(value['bytes'], 1_000_000)
        self.assertEqual(value['inference'], 'not_started')

    def test_self_test_exercises_actual_kit(self):
        result = desktop_setup.self_test(self.kit)
        self.assertEqual(result['status'], 'passed')
        self.assertIn('no model', result['scope'])

    def test_self_test_cannot_pass_with_broken_gui_runtime(self):
        def missing_tcl():
            raise ImportError('missing Tcl library')
        broken = SimpleNamespace(Tcl=missing_tcl, ttk=SimpleNamespace())
        with patch.dict(sys.modules, {'tkinter': broken, 'tkinter.ttk': broken.ttk}):
            with self.assertRaisesRegex(ImportError, 'missing Tcl library'):
                desktop_setup.self_test(self.kit)


if __name__ == '__main__':
    unittest.main()

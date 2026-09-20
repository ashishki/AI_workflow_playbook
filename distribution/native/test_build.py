"""Verify the delivered archive itself, not generated marketing copy."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec=importlib.util.spec_from_file_location('native_build',Path(__file__).with_name('build.py'))
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='playbook-package-test-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_archive_is_reproducible_and_manifest_matches_every_file(self):
        a=build.build(self.root/'one');b=build.build(self.root/'two')
        self.assertEqual(a['sha256'],b['sha256'])
        with zipfile.ZipFile(a['archive']) as z:
            payload={n:z.read(n) for n in z.namelist()}
        self.assertEqual(Path(a['archive']).with_suffix('.zip.sha256').read_bytes(),
                         f"{a['sha256']}  {Path(a['archive']).name}\n".encode('ascii'))
        m=json.loads(payload['Playbook/PACKAGE.json'])
        self.assertEqual(set(payload),{'Playbook/'+n for n in m['files']}|{'Playbook/PACKAGE.json'})
        for n,sha in m['files'].items():
            self.assertEqual(hashlib.sha256(payload['Playbook/'+n]).hexdigest(),sha)
        self.assertIn(b'data-kit="archive"',payload['Playbook/START.html'])
        self.assertNotIn(b'data-kit="source"',payload['Playbook/START.html'])
        self.assertFalse(any('/evals/' in n or '/reports/' in n or '/.git/' in n or n.endswith('auth.json') for n in payload))

    def test_starter_skills_are_exact_package_copies_and_extract_with_spaces(self):
        a=build.build(self.root/'out')
        with zipfile.ZipFile(a['archive']) as z:z.extractall(self.root/'Пример с пробелами')
        kit=self.root/'Пример с пробелами/Playbook'
        skills=list((kit/'Мой проект/.agents/skills').rglob('*'))
        files=[p for p in skills if p.is_file()]
        self.assertTrue(files)
        for p in files:
            relative=p.relative_to(kit/'Мой проект/.agents/skills')
            self.assertEqual(p.read_bytes(),(build.PACKAGE/'skills'/relative).read_bytes())
        self.assertEqual((kit/'Мой проект/AGENTS.md').read_bytes(),(build.PACKAGE/'skills/playbook/assets/project-block.md').read_bytes())
        self.assertFalse((kit/'Мой проект/index.html').exists(),'The kit must not pretend the user task is already implemented')

    def test_existing_archive_is_not_overwritten(self):
        a=build.build(self.root)
        original=Path(a['archive']).read_bytes()
        with self.assertRaises(FileExistsError):build.build(self.root)
        self.assertEqual(Path(a['archive']).read_bytes(),original)

    def test_existing_checksum_is_not_overwritten(self):
        version,_=build.collect()
        sentinel=self.root/f'Playbook-{version}.zip.sha256';sentinel.write_bytes(b'user file')
        with self.assertRaises(FileExistsError):build.build(self.root)
        self.assertEqual(sentinel.read_bytes(),b'user file')
        self.assertFalse(sentinel.with_suffix('').exists())

    def test_checksum_created_during_build_is_not_overwritten(self):
        version,_=build.collect()
        archive=self.root/f'Playbook-{version}.zip'
        sentinel=archive.with_suffix('.zip.sha256')
        original=build.open_checksum
        def create_racing_sidecar(path):
            # This path is private staging, so failure cannot expose it as a
            # final checksum or overwrite anything in the output directory.
            path.write_bytes(b'racing staging file')
            return original(path)
        with patch.object(build,'open_checksum',side_effect=create_racing_sidecar),self.assertRaises(FileExistsError):
            build.build(self.root)
        self.assertFalse(archive.exists())
        self.assertFalse(sentinel.exists())

    def test_replaced_path_fails_identity_check(self):
        original=self.root/'original';replacement=self.root/'replacement'
        original.write_bytes(b'original');replacement.write_bytes(b'replacement')
        with self.assertRaises(RuntimeError):build.verify_archive_identity(replacement,original.stat())

    def test_mutation_after_initial_hash_fails_before_success(self):
        version,_=build.collect()
        archive=self.root/f'Playbook-{version}.zip'
        original=build.hash_open_file
        calls=0
        def mutate_after_first_hash(handle):
            nonlocal calls
            result=original(handle)
            calls+=1
            if calls == 1:
                handle.seek(0);handle.write(b'racing mutation');handle.flush()
            return result
        with patch.object(build,'hash_open_file',side_effect=mutate_after_first_hash),self.assertRaises(RuntimeError):
            build.build(self.root)
        self.assertFalse(archive.exists())
        self.assertFalse(archive.with_suffix('.zip.sha256').exists())

    def test_sidecar_mutation_fails_before_final_names_are_published(self):
        version,_=build.collect()
        archive=self.root/f'Playbook-{version}.zip'
        original=build.write_checksum
        def mutate_sidecar(handle, contents):
            original(handle, contents)
            handle.seek(0);handle.write(b'0' * len(contents));handle.flush()
        with patch.object(build,'write_checksum',side_effect=mutate_sidecar),self.assertRaises(RuntimeError):
            build.build(self.root)
        self.assertFalse(archive.exists())
        self.assertFalse(archive.with_suffix('.zip.sha256').exists())

    def test_archive_mutation_after_final_links_fails_before_success(self):
        original=build.hash_open_file
        calls=0
        def mutate_after_links(handle):
            nonlocal calls
            calls+=1
            if calls == 3:
                with self.assertRaises(OSError):handle.write(b'late racing mutation')
                raise RuntimeError('read-only archive rejects post-link mutation')
            return original(handle)
        with patch.object(build,'hash_open_file',side_effect=mutate_after_links),self.assertRaises(RuntimeError):
            build.build(self.root)

    def test_sidecar_mutation_after_final_links_fails_before_success(self):
        original=build.read_open_file
        calls=0
        def mutate_after_links(handle):
            nonlocal calls
            calls+=1
            if calls == 2:
                with self.assertRaises(OSError):handle.write(b'0')
                raise RuntimeError('read-only checksum rejects post-link mutation')
            return original(handle)
        with patch.object(build,'read_open_file',side_effect=mutate_after_links),self.assertRaises(RuntimeError):
            build.build(self.root)

    def test_published_artifacts_are_read_only(self):
        result=build.build(self.root)
        archive=Path(result['archive'])
        self.assertEqual(archive.stat().st_mode & stat.S_IWUSR,0)
        self.assertEqual(archive.with_suffix('.zip.sha256').stat().st_mode & stat.S_IWUSR,0)

    @unittest.skipIf(hasattr(os,'geteuid') and os.geteuid() == 0,
                         'root bypasses Unix read-only file permissions')
    def test_published_artifacts_cannot_be_reopened_writable(self):
        result=build.build(self.root)
        archive=Path(result['archive'])
        with self.assertRaises(OSError):archive.open('r+b')
        with self.assertRaises(OSError):archive.with_suffix('.zip.sha256').open('r+b')

    def test_symlink_cannot_copy_unrelated_data_into_archive(self):
        package=self.root/'package';shutil.copytree(build.PACKAGE,package)
        secret=self.root/'outside.txt';secret.write_text('not part of the package')
        (package/'unexpected.txt').symlink_to(secret)
        with patch.object(build,'PACKAGE',package),self.assertRaises(ValueError):build.build(self.root/'out')
        self.assertFalse((self.root/'out').exists())

    def test_nonportable_member_names_are_rejected_on_every_platform(self):
        # These source-tree names cannot be created literally on every host;
        # validation must still be identical in the Windows CI job.
        for name in (
                'plugins/playbook-native/skills/..\\..\\outside.txt',
                'plugins/playbook-native/skills/.. /.. /.. /outside.txt',
                'plugins/playbook-native/skills/.. ./.. ./.. ./outside.txt',
                'plugins/playbook-native/skills/a*.md',
                'plugins/playbook-native/skills/ leading-space.md',
                'plugins/playbook-native/skills/NUL.txt',
                'plugins/playbook-native/skills/NUL .txt',
                'plugins/playbook-native/skills/CONIN$.txt',
                'plugins/playbook-native/skills/unsafe\x01name.md',
        ):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):build.validate_payload_names({name: b'malicious'})

    def test_nonportable_version_tokens_are_rejected(self):
        for version in ('../0.2.0', '0.2.0/../../outside', 'C:\\0.2.0', '\\\\host\\share', '0.2',
                        '01.2.3', '1.2.3-01', '1.2.3-.x', '1.2.3-x..y'):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):build.validate_version(version)

    def test_staged_substitution_is_detected_after_linking(self):
        version,_=build.collect()
        archive=self.root/f'Playbook-{version}.zip'
        substitute=self.root/'substitute';substitute.write_bytes(b'unvalidated bytes')
        def link_substitute(source, target):
            os.link(substitute, target)
        with patch.object(build,'publish_staged_file',side_effect=link_substitute),self.assertRaises(RuntimeError):
            build.build(self.root)
        self.assertEqual(archive.read_bytes(),b'unvalidated bytes')

    def test_failed_second_link_preserves_external_checksum(self):
        version,_=build.collect()
        archive=self.root/f'Playbook-{version}.zip'
        checksum=archive.with_suffix('.zip.sha256')
        original=build.publish_staged_file
        calls=0
        def fail_second_link(source, target):
            nonlocal calls
            calls+=1
            if calls == 2:
                target.write_bytes(b'external checksum')
            return original(source, target)
        with patch.object(build,'publish_staged_file',side_effect=fail_second_link),self.assertRaises(RuntimeError):
            build.build(self.root)
        self.assertTrue(archive.is_file())
        self.assertEqual(checksum.read_bytes(),b'external checksum')

    def test_case_and_unicode_colliding_members_are_rejected(self):
        for names in (
                ('plugins/playbook-native/skills/Case.md',
                 'plugins/playbook-native/skills/case.md'),
                ('plugins/playbook-native/skills/caf\u00e9.md',
                 'plugins/playbook-native/skills/cafe\u0301.md'),
                ('plugins/playbook-native/skills/Foo',
                 'plugins/playbook-native/skills/foo/bar.md'),
                ('plugins/playbook-native/skills/caf\u00e9',
                 'plugins/playbook-native/skills/cafe\u0301/bar.md'),
        ):
            with self.subTest(names=names):
                with self.assertRaises(ValueError):build.validate_payload_names({name: b'member' for name in names})

if __name__=='__main__':unittest.main()

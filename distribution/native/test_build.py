"""Verify the delivered archive itself, not generated marketing copy."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
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

    def test_symlink_cannot_copy_unrelated_data_into_archive(self):
        package=self.root/'package';shutil.copytree(build.PACKAGE,package)
        secret=self.root/'outside.txt';secret.write_text('not part of the package')
        (package/'unexpected.txt').symlink_to(secret)
        with patch.object(build,'PACKAGE',package),self.assertRaises(ValueError):build.build(self.root/'out')
        self.assertFalse((self.root/'out').exists())

if __name__=='__main__':unittest.main()

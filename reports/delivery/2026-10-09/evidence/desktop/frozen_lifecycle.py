from pathlib import Path
import hashlib
import json
import subprocess
import shutil
import zipfile

base = Path.cwd() / '.playbook-artifacts/delivery-acceptance-20261009/desktop-final'
helper = base / 'accepted-extracted/playbook-helper'
original_zip = next((base / 'accepted-extracted').glob('Playbook-*.zip'))
root = base / 'Ready CLI проект с пробелами'
root.mkdir()
owner = {'notes.txt': b'Owner data remains\r\n', 'AGENTS.md': b'# Owner rules\r\nDo not publish.\r\n',
         '.gitignore': b'owner-cache/\r\n'}
for name, data in owner.items():
    (root / name).write_bytes(data)
with zipfile.ZipFile(original_zip) as archive:
    contents = {name: archive.read(name) for name in archive.namelist()}
manifest = json.loads(contents['Playbook/PACKAGE.json'])
manifest['version'] = '0.2.0-preview.5'
changed_name = 'Playbook/Мой проект/.agents/skills/playbook/references/setup.md'
contents[changed_name] += b'\nSynthetic next-version acceptance marker.\n'
manifest['files'][changed_name[len('Playbook/'):]] = hashlib.sha256(contents[changed_name]).hexdigest()
contents['Playbook/PACKAGE.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
next_zip = base / 'accepted-synthetic-preview.5.zip'
with zipfile.ZipFile(next_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name, data in contents.items():
        archive.writestr(name, data)
next_sha = hashlib.sha256(next_zip.read_bytes()).hexdigest()

def run(action, next_kit=False, confirm=True, expected=0, project=None):
    project = project or root
    argv = [str(helper), '--root', str(project)]
    if next_kit:
        argv += ['--kit', str(next_zip), '--sha256', next_sha]
    if confirm:
        argv += ['--confirm']
    result = subprocess.run([*argv, action], capture_output=True, text=True, timeout=120)
    print(json.dumps({'action': action, 'synthetic_next_kit': next_kit, 'returncode': result.returncode,
                      'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()}, ensure_ascii=False), flush=True)
    assert result.returncode == expected
    return result

run('install')
assert json.loads(run('doctor', confirm=False).stdout)['installation']['setup_readiness'] == 'installation_verified'
run('update', next_kit=True)
assert (root / '.agents/skills/playbook/references/setup.md').read_bytes().endswith(b'Synthetic next-version acceptance marker.\n')
pointer = root / '.playbook-setup/runtime.json'
saved_pointer = pointer.read_bytes()
command = json.loads(saved_pointer)['command']
assert '--kit' in command and str(next_zip) in command
inventory = subprocess.run([*command, 'helper', 'inventory', '--root', str(root), '--json'],
                           capture_output=True, text=True, timeout=120)
assert inventory.returncode in {0, 1}, inventory.stderr
assert json.loads(inventory.stdout)['schema_version'] == 'playbook.environment.v1'
print('STORED_UPDATED_HELPER_POINTER_EXECUTES_ACTUAL_MATCHING_KIT', flush=True)
assert json.loads(run('doctor', next_kit=True, confirm=False).stdout)['installation']['setup_readiness'] == 'installation_verified'
assert json.loads(run('doctor', confirm=False).stdout)['installation']['helper_pointer'] == 'mismatch'
run('update', expected=2)
skill = root / '.agents/skills/playbook/SKILL.md'
original_skill = skill.read_bytes()
skill.write_bytes(original_skill + b'\nOwner edit\n')
run('remove', next_kit=True, expected=2)
skill.write_bytes(original_skill)
pointer.unlink()
assert json.loads(run('doctor', next_kit=True, confirm=False).stdout)['installation']['helper_pointer'] == 'missing'
run('update', next_kit=True, expected=2)
assert not pointer.exists()
pointer.write_bytes(saved_pointer)
run('remove', next_kit=True)
for name, data in owner.items():
    assert (root / name).read_bytes() == data
run('rollback', next_kit=True)
assert json.loads(run('doctor', next_kit=True, confirm=False).stdout)['installation']['setup_readiness'] == 'installation_verified'
assert (root / 'notes.txt').read_bytes() == owner['notes.txt']
def snapshot(project):
    return {path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in project.rglob('*') if path.is_file()}

copied = base / 'Copied CLI project'
shutil.copytree(root, copied)
for project in (copied, base / 'Moved CLI project'):
    if project != copied:
        shutil.move(str(copied), str(project))
    before = snapshot(project)
    diagnosis = json.loads(run('doctor', next_kit=True, confirm=False, project=project).stdout)
    assert diagnosis['installation']['installation'] == 'interrupted'
    assert diagnosis['installation']['setup_readiness'] == 'not_ready'
    for action in ('update', 'remove'):
        run(action, next_kit=True, project=project, expected=2)
    assert snapshot(project) == before, 'Copied/moved root operation changed file bytes'
    print('COPIED_OR_MOVED_ROOT_REFUSAL_WITHOUT_FILE_CHANGES: ' + project.name, flush=True)

journal = root / '.playbook-setup/journal.json'
original_journal = journal.read_bytes()
journal.unlink()
before = snapshot(root)
diagnosis = json.loads(run('doctor', next_kit=True, confirm=False).stdout)
assert diagnosis['installation']['installation'] == 'interrupted'
assert diagnosis['installation']['setup_readiness'] == 'not_ready'
for action in ('update', 'remove'):
    run(action, next_kit=True, expected=2)
assert snapshot(root) == before, 'Missing-journal operation changed file bytes'
assert not journal.exists(), 'Missing journal was silently recreated'
journal.write_bytes(original_journal)
print('MISSING_JOURNAL_REFUSAL_WITHOUT_FILE_CHANGES', flush=True)
print('FROZEN_READY_LIFECYCLE_PASS: actual install/update/stored pointer invocation/mismatch/missing pointer refusal/downgrade refusal/owner edit refusal/remove/rollback/copied and moved root refusal/missing journal refusal; owner files byte-preserved. Synthetic next release only, no model/account/deployment/human/clean-machine acceptance.', flush=True)

from pathlib import Path
import hashlib
import json
import os
import signal
import stat
import subprocess
import sys
import time
import tkinter as tk
import zipfile

repo = Path.cwd()
base = repo / '.playbook-artifacts/delivery-acceptance-20261009/desktop-final'
run_name = sys.argv[1]
evidence = base / ('gui-' + run_name)
evidence.mkdir()
artifact = next((base / (run_name + '-bundle')).glob('*.zip'))
destination = base / (run_name + '-extracted')
destination.mkdir()
with zipfile.ZipFile(artifact) as archive:
    archive.extractall(destination)
    for member in archive.infolist():
        if stat.S_ISREG(member.external_attr >> 16):
            os.chmod(destination / member.filename, stat.S_IMODE(member.external_attr >> 16))
manifest = json.loads((destination / 'DESKTOP.json').read_bytes())
for name, expected in manifest['files'].items():
    assert hashlib.sha256((destination / name).read_bytes()).hexdigest() == expected

sys.path.insert(0, str(repo / 'distribution/desktop'))
import desktop_runtime
assert desktop_runtime.verified_binary() is None, 'Do not automate login/status against a managed account runtime.'

project = base / ('GUI ' + run_name + ' проект с пробелами')
project.mkdir()
original = {'notes.txt': b'Owner notes\r\n', 'AGENTS.md': b'# Owner instructions\r\nDo not publish.\r\n',
            '.gitignore': b'owner-cache/\r\n'}
for name, data in original.items():
    (project / name).write_bytes(data)
controller = tk.Tk()
controller.withdraw()
own_name = controller.tk.call('tk', 'appname')
log = (evidence / 'gui-process.log').open('wb')
process = subprocess.Popen([str(destination / 'Playbook-Setup')], stdout=log, stderr=subprocess.STDOUT,
                           start_new_session=True)
observations = []

def wait_until(fn, timeout=40):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        controller.update()
        if process.poll() is not None:
            raise RuntimeError(f'GUI exited: {process.returncode}')
        value = fn()
        if value:
            return value
        time.sleep(.1)
    raise TimeoutError('GUI observation timed out')

try:
    target = wait_until(lambda: next((name for name in controller.tk.call('winfo', 'interps')
                                     if name != own_name), None))
    def send(script):
        return controller.tk.call('send', target, script)
    def remote(*args):
        return send(controller.tk.call('list', *args))
    send('''
        proc audit_find {root kind label} {
            foreach item [winfo children $root] {
                if {[winfo class $item] eq $kind && ($label eq "" || [$item cget -text] eq $label)} { return $item }
                set result [audit_find $item $kind $label]
                if {$result ne ""} { return $result }
            }
            return ""
        }
        proc audit_accept {remaining} {
            if {[winfo exists .__tk__messagebox.yes]} { .__tk__messagebox.yes invoke; return }
            if {$remaining > 0} { after 100 [list audit_accept [expr {$remaining - 1}]] }
        }
    ''')
    entry = remote('audit_find', '.', 'TEntry', '')
    output = remote('audit_find', '.', 'Text', '')
    remote(entry, 'insert', 0, str(project))
    def text():
        return remote(output, 'get', '1.0', 'end')
    def click(label, expected, confirm=False):
        button = remote('audit_find', '.', 'TButton', label)
        assert button, label
        if confirm:
            remote('after', 100, 'audit_accept 100')
        remote('after', 0, controller.tk.call('list', button, 'invoke'))
        value = wait_until(lambda: text() if expected in text() else None)
        observations.append({'button': label, 'observed_text': value.strip()})
        print(json.dumps(observations[-1], ensure_ascii=False), flush=True)
        return value
    def screenshot(name):
        path = evidence / name
        subprocess.run(['ffmpeg', '-y', '-f', 'x11grab', '-video_size', '1280x1024',
                        '-i', os.environ['DISPLAY'], '-frames:v', '1', str(path)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=15)

    click('3. Подготовить / обновить Playbook', 'Файлы Playbook подготовлены', True)
    healthy = click('Проверить подготовку', 'Состояние файлов: файлы проверены')
    assert 'Расположение помощника: записанное расположение сверено' in healthy
    screenshot('gui-healthy.png')
    journal = project / '.playbook-setup/journal.json'
    transaction = json.loads(journal.read_bytes())
    transaction['status'] = 'pending'
    journal.write_text(json.dumps(transaction), encoding='utf-8')
    interrupted = click('Проверить подготовку', 'установка прервана')
    assert 'Состояние файлов: файлы проверены' not in interrupted
    assert '«Вернуть установку»' in interrupted
    screenshot('gui-interrupted.png')
    click('Вернуть установку', 'Предыдущее состояние установки восстановлено', True)
    for name, data in original.items():
        assert (project / name).read_bytes() == data
    click('3. Подготовить / обновить Playbook', 'Файлы Playbook подготовлены', True)
    pointer = project / '.playbook-setup/runtime.json'
    saved_pointer = pointer.read_bytes()
    pointer.unlink()
    missing = click('Проверить подготовку', 'Расположение помощника: файл расположения отсутствует')
    assert 'Состояние файлов: есть изменения, нужна проверка' in missing
    screenshot('gui-pointer-missing.png')
    assert not pointer.exists()
    pointer.write_bytes(saved_pointer)
    changed = json.loads(saved_pointer)
    changed['command'] = ['/unrelated/helper']
    pointer.write_text(json.dumps(changed), encoding='utf-8')
    modified = click('Проверить подготовку', 'Расположение помощника: файл расположения изменён')
    assert 'Состояние файлов: есть изменения, нужна проверка' in modified
    screenshot('gui-pointer-modified.png')
    click('Отключить в папке', 'The local helper pointer is missing, modified or unverified')
    assert json.loads(pointer.read_bytes()) == changed
    pointer.write_bytes(saved_pointer)
    click('Отключить в папке', 'Playbook отключён в папке', True)
    for name, data in original.items():
        assert (project / name).read_bytes() == data
    click('Вернуть установку', 'Предыдущее состояние установки восстановлено', True)
    click('Проверить подготовку', 'Состояние файлов: файлы проверены')
    assert (project / 'notes.txt').read_bytes() == original['notes.txt']
    screenshot('gui-restored.png')
    summary = {'status': 'passed', 'scope': 'Actual frozen Linux GUI buttons, confirmation dialogs and diagnostics under Xvfb; no human, clean-machine, account, inference or deployment trial',
               'source_identity': json.loads((base / 'source-final-before.json').read_bytes()),
               'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(), 'observations': observations}
    (evidence / 'gui-automation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': summary['status'], 'scope': summary['scope']}, ensure_ascii=False))
finally:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=15)
    controller.destroy()
    log.close()

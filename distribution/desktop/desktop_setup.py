"""One local setup window, not a new chat, server or agent runtime."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import queue
import runpy
import sys
import tempfile
import threading
import webbrowser

from setup_core import Kit, SetupError, apply, installation_status, json_bytes, plan, rollback, strict_json, project, installed
import desktop_runtime as runtime

HELPERS = {'review': 'run_codex_role.py', 'state': 'solution_record.py',
           'inventory': 'playbook_environment.py'}
HELPER_PREFIX = 'plugins/playbook-native/skills/playbook/scripts/'
HOST_GUIDE = 'https://learn.chatgpt.com/docs/quickstart'


def bundle(args) -> Kit:
    if args.kit:
        if not args.sha256:
            raise SetupError('A separately verified archive checksum is required')
        return Kit.load(args.kit, args.sha256)
    home = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'data'
    metadata = strict_json((home / 'bundle.json').read_bytes())
    if metadata.get('schema') != 'playbook.desktop-bundle.v1':
        raise SetupError('Invalid bundled metadata')
    return Kit.load(home / 'Playbook.zip', metadata['sha256'])


def self_command(args) -> list[str]:
    if getattr(sys, 'frozen', False):
        exe = Path(sys.executable)
        base = exe.parents[3] if '.app' in exe.as_posix() and len(exe.parents) > 3 else exe.parent
        helper = base / ('playbook-helper.exe' if os.name == 'nt' else 'playbook-helper')
        if not helper.is_file():
            raise SetupError('The helper executable is missing; restore the complete distribution')
        return [str(helper)]
    command = [sys.executable, str(Path(__file__).resolve())]
    if args.kit:
        command += ['--kit', str(args.kit.resolve()), '--sha256', args.sha256]
    return command


def helper(kit: Kit, name: str, arguments: list[str]) -> int:
    root_arg = next((a.split('=', 1)[1] for a in arguments if a.startswith('--root=')), None)
    if '--root' in arguments:
        index = arguments.index('--root')
        if index + 1 >= len(arguments):
            raise SetupError('Missing helper project path')
        root_arg = arguments[index + 1]
    if root_arg is not None:
        record = installed(project(Path(root_arg)))
        if record and record.get('kit_sha256') != kit.sha256:
            raise SetupError('Helper and installed kit differ; update through the matching setup first')
    with tempfile.TemporaryDirectory(prefix='playbook-helper-') as tmp:
        directory = Path(tmp)
        for filename in (*HELPERS.values(), 'codex_role_run_lib.py'):
            data = kit.files.get(HELPER_PREFIX + filename)
            if data is None:
                raise SetupError('Canonical helper missing from this kit')
            (directory / filename).write_bytes(data)
        binary = runtime.verified_binary()
        old_path, old_argv, old_env = sys.path[:], sys.argv[:], os.environ.get('PATH')
        try:
            sys.path.insert(0, str(directory))
            if binary is not None:
                os.environ['PATH'] = runtime.process_environment(binary)['PATH']
            sys.argv = [str(directory / HELPERS[name]), *arguments]
            try:
                runpy.run_path(sys.argv[0], run_name='__main__')
            except SystemExit as exc:
                return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        finally:
            sys.path[:], sys.argv[:] = old_path, old_argv
            if old_env is None:
                os.environ.pop('PATH', None)
            else:
                os.environ['PATH'] = old_env
    return 0


def self_test(kit: Kit) -> dict:
    # Import and initialize Tcl without a display. Loading reviewer --help alone
    # does not detect missing shared libraries or Tcl scripts in a frozen GUI.
    import tkinter
    from tkinter import ttk
    tcl_version = tkinter.Tcl().eval('info patchlevel')
    with tempfile.TemporaryDirectory(prefix='playbook-smoke-') as tmp:
        root = Path(tmp) / 'Мой проект with spaces'
        root.mkdir()
        (root / 'notes.txt').write_text('Owner data stays unchanged', encoding='utf-8')
        original = b'# Existing instructions\r\nDo not publish.\r\n'
        (root / 'AGENTS.md').write_bytes(original)
        apply(plan(root, kit, 'install'), consent=True)
        assert installation_status(root)['installation'] == 'files_verified'
        assert helper(kit, 'inventory', ['--root', str(root), '--json']) in {0, 1}
        # Load the real reviewer entrypoint without inference so the frozen build
        # proves its dynamic stdlib imports are present.
        assert helper(kit, 'review', ['--help']) == 0
        apply(plan(root, kit, 'remove'), consent=True)
        assert (root / 'AGENTS.md').read_bytes() == original
        assert (root / 'notes.txt').read_text(encoding='utf-8') == 'Owner data stays unchanged'
        rollback(root, consent=True)
        assert installation_status(root)['installation'] == 'files_verified'
    return {'status': 'passed',
            'scope': 'Tcl runtime, actual packaged install/remove/rollback and inventory; no model, browser or user trial',
            'tcl_version': tcl_version,
            'version': kit.version, 'kit_sha256': kit.sha256}


def report(kit: Kit, root: Path | None, *, probe_codex: bool = False) -> dict:
    value = {'schema': 'playbook.support.v1', 'package_version': kit.version,
             'kit_sha256': kit.sha256, 'os': runtime.platform_key(),
             'installation': installation_status(root) if root else {'installation': 'not_selected'},
             'model_trial': 'not_run', 'browser_trial': 'not_run', 'user_trial': 'not_run'}
    value['runtime'] = runtime.probe() if probe_codex else {'probe': 'not_run'}
    return value


def gui(kit: Kit, args) -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    window = tk.Tk()
    window.title('Playbook — подготовка рабочего места')
    window.geometry('780x660')
    window.minsize(720, 560)
    frame = ttk.Frame(window, padding=20)
    frame.pack(fill='both', expand=True)
    selected = tk.StringVar()
    events: queue.Queue = queue.Queue()
    busy = False
    buttons = []
    ttk.Label(frame, text='Одна рабочая проблема. Один понятный путь.',
              font=('Arial', 17, 'bold'), wraplength=690).pack(anchor='w')
    ttk.Label(frame, text='Это мастер подготовки, не отдельный AI-чат. После подготовки вы работаете в Codex.\n'
              'Аккаунт и решения о данных остаются у вас. Версия ' + kit.version,
              wraplength=690).pack(anchor='w', pady=(8, 16))
    ttk.Button(frame, text='1. Как установить AI-приложение и войти',
               command=lambda: webbrowser.open(HOST_GUIDE)).pack(anchor='w')
    ttk.Label(frame, text='2. Выберите отдельную рабочую папку').pack(anchor='w', pady=(14, 5))
    entry = ttk.Entry(frame, textvariable=selected)
    entry.pack(fill='x')
    buttons.append(entry)
    row = ttk.Frame(frame)
    row.pack(fill='x', pady=6)

    def choose():
        directory = filedialog.askdirectory(title='Выберите рабочую папку', mustexist=True)
        if directory:
            selected.set(directory)

    def create():
        parent = filedialog.askdirectory(title='Где создать новую рабочую папку?', mustexist=True)
        if not parent:
            return
        dest = Path(parent) / 'Мой проект Playbook'
        try:
            dest.mkdir(mode=0o700)
            selected.set(str(dest))
        except FileExistsError:
            messagebox.showinfo('Папка уже существует', 'Выберите её кнопкой «Выбрать» или используйте другое место.')

    choose_button = ttk.Button(row, text='Выбрать папку', command=choose)
    choose_button.pack(side='left')
    create_button = ttk.Button(row, text='Создать новую папку', command=create)
    create_button.pack(side='left', padx=8)
    buttons.extend([choose_button, create_button])
    output = tk.Text(frame, height=10, wrap='word', state='disabled', font=('Arial', 11))

    def show(value):
        output.configure(state='normal')
        output.delete('1.0', 'end')
        output.insert('1.0', value)
        output.configure(state='disabled')

    def root():
        if not selected.get().strip():
            raise SetupError('Сначала выберите отдельную рабочую папку.')
        return Path(selected.get())

    def work(fn, done):
        nonlocal busy
        if busy:
            return
        busy = True
        progress.start(12)
        for button in buttons:
            button.configure(state='disabled')
        show('Выполняю выбранный шаг. Закрытие окна не отменяет уже выполненные действия.')
        def run():
            try:
                events.put((done, fn(), None))
            except Exception as exc:
                events.put((done, None, exc))
        threading.Thread(target=run, daemon=False).start()

    def poll():
        nonlocal busy
        try:
            done, result, error = events.get_nowait()
        except queue.Empty:
            pass
        else:
            busy = False
            progress.stop()
            for button in buttons:
                button.configure(state='normal')
            if error:
                show('Этот шаг не завершён. Не удаляйте рабочие данные и не отключайте защиту.\n\n'
                     + str(error) + '\n\nПри прерванной установке используйте «Вернуть установку». '
                     'Конфликт изменённых файлов нужно сначала разобрать с помощником.')
            else:
                done(result)
        window.after(100, poll)

    def guarded(fn):
        def call():
            try:
                fn()
            except Exception as exc:
                show('Ничего не меняю. ' + str(exc))
        return call

    def install():
        path = root()
        existing = installation_status(path)['installation'] != 'not_managed'
        proposal = plan(path, kit, 'update' if existing else 'install', self_command(args))
        count = proposal.summary()['files_changed']
        if not messagebox.askyesno('Подготовить папку?', f'Папка: {path}\n\n'
                f'Будут подготовлены инструкции и инструменты Playbook: {count} файлов.\n'
                'Ваши рабочие данные, глобальные настройки и аккаунты не меняются.\n'
                'Уже изменённые файлы Playbook не перезаписываются.\n\nПродолжить?'):
            return
        work(lambda: apply(proposal, consent=True), lambda result: show(
            'Файлы Playbook подготовлены и проверены.\n\n'
            'Теперь откройте выбранную папку в Codex и нажмите ниже «Скопировать первый запрос».\n'
            'Само открытие папки в приложении этим мастером не проверено.\n\n'
            'Для независимого ревью подготовьте инструмент проверки и войдите в аккаунт. '
            'Реальное ревью и браузер проверяет помощник в вашей сессии.'))

    def provision():
        details = runtime.asset_plan()
        if not messagebox.askyesno('Подготовить независимую проверку?',
            f'С официального GitHub OpenAI будет загружен Codex {details["version"]}, '
            f'около {details["bytes"] // 1000000} МБ.\n\n'
            f'Он будет установлен только для вас: {details["destination"]}\n'
            'Системные Python, Node и права администратора для этого комплекта не требуются. '
            'Глобальные настройки и модель не меняются. Вход в аккаунт — отдельный шаг.\n\n'
            'Продолжить загрузку и установку?'):
            return
        work(lambda: runtime.provision(consent=True), lambda _: show(
            'Инструмент установлен, целостность файлов проверена. Теперь нажмите «Войти».\n'
            'Это ещё не подтверждение доступности модели или успешного ревью.'))

    def login():
        if messagebox.askyesno('Вход в аккаунт', 'Откроется стандартный вход Codex в браузере. '
                              'Вводите данные только на странице провайдера. Playbook не читает пароль или токены. Продолжить?'):
            work(lambda: runtime.login(consent=True), lambda value: show(
                'Процедура входа завершена. Нажмите «Проверить подготовку». Реальное ревью ещё не запускалось.'
                if value.get('login') == 'cli_completed' else
                'Вход не подтверждён. Проверьте браузер, права аккаунта и доступность сети. '
                'Не отключайте ограничения. Разбор рабочей проблемы можно продолжать в Codex.'))

    def diagnose():
        path = root()
        def done(value):
            runtime_state = value['runtime']
            labels = {'not_managed': 'ещё не подготовлено мастером', 'files_verified': 'файлы проверены',
                      'modified': 'есть изменения, нужна проверка', 'launched': 'запуск проверен',
                      'launch_failed': 'запуск не получился', 'probe_failed': 'проверка не завершена',
                      'cli_reports_login': 'инструмент подтвердил вход', 'not_confirmed': 'не подтверждён',
                      'unknown': 'не проверен'}
            show('Состояние файлов: ' + labels.get(value['installation']['installation'], 'не проверено') + '\n'
                 'Запуск инструмента: ' + labels.get(runtime_state.get('codex'), 'не проверен') + '\n'
                 'Вход: ' + labels.get(runtime_state.get('auth'), 'не проверен') + '\n\n'
                 'Проверка моделью и проверка интерфейса не выполнялись мастером. '
                 'Попросите помощника проверить их в рабочей сессии.\n\n'
                 'Диагностика не читала содержимое вашего решения, токены и историю чата.')
        work(lambda: report(kit, path, probe_codex=True), done)

    def remove():
        proposal = plan(root(), kit, 'remove')
        if messagebox.askyesno('Отключить Playbook в этой папке?',
             'Будут удалены только неизменённые управляемые инструкции Playbook. '
             'Программа, данные и заметки останутся. Хостинг, подписки и внешние подключения НЕ отключаются. Продолжить?'):
            work(lambda: apply(proposal, consent=True), lambda _: show(
                'Playbook отключён в папке. Данные не удалены. Остался локальный журнал возврата установки. '
                'Облачные ресурсы и общие инструменты не менялись.'))

    def restore():
        path = root()
        if messagebox.askyesno('Вернуть предыдущую установку?',
             'Будет возвращено состояние до последней операции мастера. '
             'Это НЕ восстановление данных приложения. При последующих изменениях файлов операция остановится. Продолжить?'):
            work(lambda: rollback(path, consent=True), lambda _: show(
                'Предыдущее состояние установки восстановлено. Данные решения не менялись.'))

    def copy_prompt():
        path = root()
        window.clipboard_clear()
        window.clipboard_append('Прочитай AGENTS.md и подключённый Playbook в выбранной рабочей папке. '
          'Проверь доступные возможности и помоги с подготовкой по references/setup.md, без скрытых установок, '
          'расходов и публикации. Затем помоги разобраться с одной повторяющейся проблемой в моей работе. '
          'Не начинай создавать приложение до понимания проблемы.')
        show('Запрос скопирован. В Codex выберите папку:\n' + str(path)
             + '\n\nВставьте запрос и опишите свою рабочую ситуацию.')

    def export_report():
        value = report(kit, root())
        dest = filedialog.asksaveasfilename(title='Сохранить отчёт без частных данных',
                                           defaultextension='.json', initialfile='playbook-support.json')
        if not dest:
            return
        with open(dest, 'xb') as stream:
            stream.write(json_bytes(value))
        show('Отчёт сохранён локально. Проверьте его перед отправкой. Ничего никуда не отправлено.')

    actions = ttk.Frame(frame)
    actions.pack(fill='x', pady=6)
    actions.columnconfigure(0, weight=1)
    actions.columnconfigure(1, weight=1)
    for index, (label, fn) in enumerate([
        ('3. Подготовить / обновить Playbook', install),
        ('Подготовить инструмент проверки', provision),
        ('Войти', login),
        ('Проверить подготовку', diagnose),
        ('Скопировать первый запрос', copy_prompt),
    ]):
        button = ttk.Button(actions, text=label, command=guarded(fn))
        button.grid(row=index // 2, column=index % 2, sticky='ew', padx=3, pady=4)
        buttons.append(button)
    progress = ttk.Progressbar(frame, mode='indeterminate')
    progress.pack(fill='x', pady=(4, 0))
    output.pack(fill='both', expand=True, pady=12)
    foot = ttk.Frame(frame)
    foot.pack(fill='x')
    for label, fn in [('Вернуть установку', restore), ('Отключить в папке', remove), ('Отчёт для помощи', export_report)]:
        button = ttk.Button(foot, text=label, command=guarded(fn))
        button.pack(side='left', padx=3)
        buttons.append(button)
    show('Начните с установки AI-приложения, затем выберите папку.\n\n'
         'GitHub, VPS и API-ключ не нужны для первого разговора. '
         'Дополнительные подключения появляются только по задаче.\n\n'
         'Комплект предварительный: успешная установка не равна проверенной пользе в вашей работе.')
    def close():
        if busy:
            messagebox.showinfo('Шаг ещё выполняется', 'Дождитесь завершения, чтобы не прервать подготовку.')
            return
        window.destroy()
    window.protocol('WM_DELETE_WINDOW', close)
    window.after(100, poll)
    window.mainloop()
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--root', type=Path)
    parser.add_argument('--confirm', action='store_true')
    parser.add_argument('--probe-codex', action='store_true')
    parser.add_argument('action', nargs='?', default='gui',
                        choices=['gui', 'about', 'plan', 'install', 'update', 'remove', 'rollback', 'doctor',
                                 'runtime-plan', 'runtime-install', 'login', 'helper', 'self-test'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        kit = bundle(args)
        if args.action == 'gui':
            return gui(kit, args)
        if args.action == 'helper':
            if not args.arguments or args.arguments[0] not in HELPERS:
                raise SetupError('Choose review, state or inventory')
            return helper(kit, args.arguments[0], args.arguments[1:])
        if args.action == 'about':
            result = {'version': kit.version, 'kit_sha256': kit.sha256, 'helpers': sorted(HELPERS),
                      'python': 'bundled' if getattr(sys, 'frozen', False) else 'build_environment'}
        elif args.action == 'self-test':
            result = self_test(kit)
        elif args.action == 'runtime-plan':
            result = runtime.asset_plan()
        elif args.action == 'runtime-install':
            result = runtime.provision(consent=args.confirm)
        elif args.action == 'login':
            result = runtime.login(consent=args.confirm)
        else:
            if args.root is None:
                raise SetupError('Select a project folder')
            if args.action == 'doctor':
                result = report(kit, args.root, probe_codex=args.probe_codex)
            elif args.action == 'rollback':
                result = rollback(args.root, consent=args.confirm)
            else:
                operation = ('update' if installation_status(args.root)['installation'] != 'not_managed' else 'install') if args.action == 'plan' else args.action
                proposal = plan(args.root, kit, operation, self_command(args))
                result = proposal.summary() if args.action == 'plan' else apply(proposal, consent=args.confirm)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        if args.action == 'gui':
            import tkinter.messagebox
            tkinter.messagebox.showerror('Playbook: подготовка не завершена', str(exc))
        else:
            print(json.dumps({'status': 'blocked', 'reason': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

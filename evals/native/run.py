#!/usr/bin/env python3
"""Run one bounded real-Codex Native trial in an isolated fixture; never a release gate."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / 'fixtures'
PROMPTS = {
    'frontend': 'Исправь форму подписки: на узком экране кнопка выходит за границы. Сохрани оформление сайта. Проверь успешную подписку, ошибку невалидного email и внешний вид в работающем приложении. Исправь обнаруженные проблемы и покажи результат.',
    'no-browser': 'Исправь форму подписки: на узком экране кнопка выходит за границы. Сохрани оформление и проверь успешную подписку и невалидный email доступными средствами. В этом испытании browser и просмотр изображений недоступны: не используй их и не устанавливай инструменты. Явно сообщи, что фактически проверено и что осталось.',
    'backend': 'Исправь slugify: пробелы и дефисы в начале и конце результата должны удаляться, внутренние слова остаются разделены одним дефисом. Проверь обычную строку и строку из одних пробелов. Работай только над этим Python helper.',
    'quick': '$playbook Существующий проект. Исправить. Быстрый режим: поправь форму подписки, на телефоне кнопка выходит за границы. Сохрани оформление. Минимум бюрократии; проверь отправку, ошибку email и реальный результат. Исправь найденные проблемы и покажи итог.',
    'plan': '$playbook Сначала план. Хочу добавить второй вариант подписки: еженедельные письма и только важные новости. Изучи текущий проект, предложи подход и проверки. Код и файлы пока не меняй.',
    'review': '$playbook Существующий проект. Проверить результат. Расширенный контроль. Проверь текущую форму подписки: поведение, мобильный вид и доступность с клавиатуры. Дай конкретные замечания с проверками. Исходники не исправляй; временные файлы проверки разрешены. Независимого reviewer в этом испытании нет, не запускай другие агенты.',
    'new-plan': '$playbook Новый проект. Создать. Сначала план. Хочу небольшой сервис записи на занятия для одного преподавателя. Предложи первый полезный результат, важные вопросы и способ проверки. Не создавай файлы и не начинай реализацию.',
}

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts}

def install_payload(package, workspace):
    shutil.copytree(package / 'skills', workspace / '.agents/skills')
    blocks = list((package / 'skills').glob('*/assets/project-block.md'))
    if len(blocks) != 1:
        raise ValueError('Expected one project block')
    (workspace / 'AGENTS.md').write_text(blocks[0].read_text())

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', choices=[*PROMPTS, 'setup', 'remove'], required=True)
    ap.add_argument('--condition', choices=['baseline', 'native'], required=True)
    ap.add_argument('--output', type=Path, required=True, help='New, non-existing trial directory')
    ap.add_argument('--timeout', type=int, default=360)
    ap.add_argument('--package', type=Path, default=ROOT / 'plugins/playbook-native')
    ap.add_argument('--browser-mcp-cli', type=Path)
    ap.add_argument('--browser-executable', type=Path)
    args = ap.parse_args()
    if args.timeout < 1 or args.output.exists():
        ap.error('Require positive timeout and a fresh output directory')
    if args.case in {'setup', 'remove', 'plan', 'review', 'new-plan', 'quick'} and args.condition != 'native':
        ap.error('This case exercises the Native package only')
    if bool(args.browser_mcp_cli) != bool(args.browser_executable):
        ap.error('Browser MCP requires both CLI and executable paths')
    out = args.output.resolve(); out.mkdir(parents=True)
    workspace = out / 'workspace'
    fixture = 'backend' if args.case in {'backend', 'setup', 'remove'} else 'subscription'
    shutil.copytree(FIXTURES / fixture, workspace)
    if args.case == 'new-plan':
        shutil.rmtree(workspace); workspace.mkdir()
    package = out / 'package'; shutil.copytree(args.package, package)
    source_hashes = hashes(package)
    if args.condition == 'native' and args.case != 'setup':
        install_payload(package, workspace)
    if args.case == 'setup':
        (workspace / 'AGENTS.md').write_text('# User instructions\n\nPreserve the AUTHORS.txt file.\n')
        (workspace / 'AGENTS.override.md').write_text('# Local override\n\nUse Python standard library only.\n')
        (workspace / 'AUTHORS.txt').write_text('User-owned content: do not replace.\n')
    if args.case == 'remove':
        (workspace / 'AGENTS.md').write_text('# User instructions\n\nPreserve AUTHORS.txt.\n\n' + (workspace / 'AGENTS.md').read_text())
        (workspace / 'AUTHORS.txt').write_text('User-owned content: do not replace.\n')
        skill = workspace / '.agents/skills/playbook-frontend/SKILL.md'
        skill.write_text(skill.read_text() + '\nUser addition: keep this locally customized skill.\n')
    subprocess.run(['git', 'init', '-q', str(workspace)], check=True)
    subprocess.run(['git', '-C', str(workspace), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(workspace), '-c', 'user.name=Native Eval', '-c', 'user.email=eval@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    if args.case == 'setup':
        with (workspace / 'slugs.py').open('a') as f:
            f.write('\n# User uncommitted note: preserve exactly.\n')
    before = hashes(workspace)
    if args.case in {'setup', 'remove'}:
        entries = list((package / 'skills').glob('playbook*/SKILL.md'))
        setup = next(p for p in entries if p.parent.name != 'playbook-frontend')
        action = ('подключи Playbook к текущему репозиторию, затем повтори подключение и проверь, что нет дубликатов. Сохрани существующие инструкции и незакоммиченные изменения.'
                  if args.case == 'setup' else
                  'удали Playbook из текущего репозитория. Сохрани пользовательские инструкции, код и мои изменения внутри skill. Не заменяй удаление отключением проверки.')
        prompt = f'Прочитай skill {setup} и {action}'
    else:
        prompt = PROMPTS[args.case]
    prompt += '\nРаботай только в текущем изолированном репозитории. Не меняй глобальные настройки, не устанавливай зависимости, не обращайся к внешним сервисам, не публикуй и не коммить изменения. Для проверки используй только локальное приложение и доступные локальные инструменты.'
    (out / 'prompt.txt').write_text(prompt + '\n')
    cmd = ['codex', 'exec', '--ephemeral', '--sandbox', 'workspace-write', '-c', 'approval_policy="never"', '--json', '-C', str(workspace), '-o', str(out / 'final.txt'), '-']
    server = None
    if args.browser_mcp_cli:
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, *values): pass
        server = ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(workspace)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}/'
        browser_args=[str(args.browser_mcp_cli.resolve()),'--headless','--isolated','--executable-path',str(args.browser_executable.resolve()),'--output-dir',str(workspace/'browser-artifacts'),'--allowed-origins',url.rstrip('/'),'--block-service-workers','--no-webmcp']
        # Chromium cannot initialize its own OS sandbox as root. This concerns
        # the synthetic isolated browser only, not Codex workspace permissions.
        if hasattr(os, 'geteuid') and os.geteuid() == 0:
            browser_args.append('--no-sandbox')
        overrides=['mcp_servers.eval_browser.command="node"',f'mcp_servers.eval_browser.args={json.dumps(browser_args)}',f'mcp_servers.eval_browser.cwd={json.dumps(str(workspace))}','mcp_servers.eval_browser.required=true']
        cmd[-1:-1]=[value for config in overrides for value in ['-c',config]]
        prompt += f'\nДля обеих сравниваемых условий evaluator уже запустил именно текущий checkout на {url}. Подключён локальный eval_browser MCP для проверки этого приложения. Используй его; запуск Chromium из shell в этой среде заблокирован. Не открывай другие сайты. Не запускай или останавливай чужие серверы.'
        (out/'prompt.txt').write_text(prompt+'\n')
    env = dict(os.environ)
    if args.case == 'no-browser': env.pop('PLAYBOOK_EVAL_PLAYWRIGHT_MODULE', None)
    meta = {'case':args.case, 'condition':args.condition, 'source_hashes':source_hashes,
            'fixture_before':before, 'argv':cmd, 'timeout_seconds':args.timeout,
            'codex_version':subprocess.check_output(['codex','--version'],text=True).strip(),
            'model_configuration':'inherited unchanged from host; see protocol/report',
            'playwright_module':env.get('PLAYBOOK_EVAL_PLAYWRIGHT_MODULE'),
            'limitations':['not a clean host profile', 'single diagnostic trial', 'no automated semantic grading of final claims']}
    write_json(out/'metadata.json',meta)
    start=time.monotonic(); timed_out=False
    try:
        with (out/'events.jsonl').open('w') as stdout, (out/'stderr.txt').open('w') as stderr:
            proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,text=True,env=env,start_new_session=True)
            try: proc.communicate(prompt,timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out=True; os.killpg(proc.pid,signal.SIGTERM)
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL); proc.wait()
    finally:
        if server:
            server.shutdown(); server.server_close()
    events=[]; parse_errors=0
    for line in (out/'events.jsonl').read_text().splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: parse_errors+=1
    items=[e['item'] for e in events if e.get('type')=='item.completed' and isinstance(e.get('item'),dict)]
    summary={'case':args.case,'condition':args.condition,'exit_code':proc.returncode,'timed_out':timed_out,
             'elapsed_seconds':round(time.monotonic()-start,2),'event_parse_errors':parse_errors,
             'turn_completed':any(e.get('type')=='turn.completed' for e in events),
             'usage':[e['usage'] for e in events if 'usage' in e],
             'item_types':{t:sum(i.get('type')==t for i in items) for t in sorted({i.get('type','unknown') for i in items})},
             'fixture_after':hashes(workspace)}
    write_json(out/'summary.json',summary)
    (out/'changes.patch').write_text(subprocess.check_output(['git','-C',str(workspace),'diff','--no-ext-diff','HEAD'],text=True))
    print(json.dumps({'output':str(out),**{k:v for k,v in summary.items() if not k.startswith('fixture_')}},ensure_ascii=False))
    return 0 if proc.returncode == 0 and not timed_out and not parse_errors and summary['turn_completed'] else 1

if __name__ == '__main__': raise SystemExit(main())

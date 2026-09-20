#!/usr/bin/env python3
"""Read-only prerequisite inventory, not a health check or authorization probe.

No subprocesses, network calls, installs, credentials/config reads or project writes.
Finding an executable/module does not prove that it can run in this host sandbox.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any


def module_present(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def inspect_environment(root: Path, audience: str, needs: set[str], *,
                        playbook_source: bool = False) -> dict[str, Any]:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Project root is not a directory')
    if audience not in {'engineering', 'product'} or not needs <= {'review', 'browser', 'tests', 'preview', 'claim'}:
        raise ValueError('Unsupported audience or capability')
    if playbook_source and audience != 'engineering':
        raise ValueError('Playbook source checks are for the maintainer environment')
    checks: list[dict[str, Any]] = []

    def add(key: str, status: str, required: bool, message: str, next_step: str = '') -> None:
        checks.append({'id': key, 'status': status, 'required': required,
                       'message_ru': message, 'next_ru': next_step})

    floor = (3, 11) if playbook_source else (3, 10)
    add('python', 'found' if sys.version_info[:2] >= floor else 'missing', True,
        f'Python {sys.version_info.major}.{sys.version_info.minor}; нужно {floor[0]}.{floor[1]}+.',
        'При необходимости создайте согласованное локальное окружение; не меняйте глобальный Python.')
    for binary, required, message in (
        ('git', audience == 'engineering', 'Git найден в PATH; checkout ещё не проверен.'),
        ('codex', 'review' in needs, 'Codex CLI найден в PATH; вход и запуск ещё не проверены.'),
        ('node', False, 'Node найден в PATH; это не работающий браузер.'),
        ('cloudflared', False, 'cloudflared найден в PATH; публичный preview ещё не запускался.'),
        ('wrangler', False, 'Wrangler найден в PATH; temporary deployment и claim ещё не проверены.'),
    ):
        found = shutil.which(binary) is not None
        add(binary, 'found' if found else 'missing', required,
            message if found else f'{binary}: команда не найдена в PATH.',
            'Проверьте доступный инструмент в этой среде; установка требует отдельного разрешения.')
    if playbook_source:
        for module in ('pytest', 'jsonschema', 'ai_workflow_harness_lab'):
            found = module_present(module)
            add(module, 'found' if found else 'missing', 'tests' in needs,
                f'{module}: ' + ('модуль обнаружен, suite не запускался.' if found else 'модуль не найден.'),
                'Из корня checkout: .venv/bin/python -m pip install -r requirements-dev.txt.')

    add('review_execution', 'unknown', 'review' in needs,
        'Авторизация, разрешение дочернего процесса и реальный reviewer не проверялись.',
        'В разрешённой сессии выполните один существующий Role Runner и проверьте результат; не копируйте credentials.')
    add('browser_execution', 'unknown', 'browser' in needs,
        'Доступный браузер, нужная версия приложения и просмотр изображения не проверялись.',
        'Используйте доступный браузер/проектный runner; откройте текущую версию и проверьте реальное действие.')
    if 'preview' in needs:
        if shutil.which('cloudflared') is None:
            add('preview_adapter', 'missing', True,
                'cloudflared не найден: Quick Tunnel preview пока недоступен.',
                'Выберите поддерживаемую установку cloudflared или продолжите локальную проверку; не устанавливайте скрытно.')
        else:
            add('preview_adapter', 'found', True,
                'cloudflared найден; внешний tunnel, публичность и фактический URL ещё не проверены.')
        add('preview_execution', 'unknown', True,
            'Временный публичный preview не запускался и разрешение на внешний URL не проверялось.',
            'После явного разрешения запустите tunnel к проверенному localhost и проверьте внешний URL.')
    if 'claim' in needs:
        if shutil.which('wrangler') is None:
            add('claim_adapter', 'missing', True,
                'Wrangler не найден: claimable temporary deployment пока недоступен.',
                'Установка/обновление Wrangler требует отдельного разрешения; наличие npx не считается готовым adapter.')
        else:
            add('claim_adapter', 'found', True,
                'Wrangler найден; версия, Terms acceptance, temporary deployment и claim ещё не проверены.')
        add('claim_execution', 'unknown', True,
            'Temporary account/live deployment/claim не выполнялись; авторизация и Terms acceptance не проверялись.',
            'В изолированном context и после явного согласия выполните поддерживаемый temporary deployment и claim workflow.')
    if 'tests' in needs:
        add('project_checks', 'unknown', True,
            'Команды и результаты проверок конкретного проекта ещё не подтверждены.',
            'Прочитайте инструкции проекта и выполните применимые проверки в разрешённой среде.')

    # Inspect only named project-local entrypoints. Never traverse home/config dirs.
    entries = []
    for name in ('AGENTS.override.md', 'AGENTS.md', '.agents/skills/playbook/SKILL.md',
                 'plugins/playbook-native/skills/playbook/SKILL.md'):
        path = root
        symbolic = False
        for part in Path(name).parts:
            path = path / part
            if path.is_symlink():
                symbolic = True
                break
        if symbolic:
            entries.append({'path': name, 'status': 'symlink_not_followed'})
        elif path.is_file():
            entries.append({'path': name, 'status': 'present_not_loaded'})
    unavailable = [c['id'] for c in checks if c['required'] and c['status'] == 'missing']
    pending = [c['id'] for c in checks if c['required'] and c['status'] == 'unknown']
    status = 'missing_prerequisites' if unavailable else 'live_checks_pending' if pending else 'inventory_only'
    return {'schema_version': 'playbook.environment.v1', 'status': status,
            'audience': audience, 'playbook_source': playbook_source, 'checks': checks, 'project_entrypoints': entries,
            'missing_required': unavailable, 'pending_live': pending,
            'model': 'host_configuration_not_read', 'authorization': 'not_checked',
            'meaning': 'Presence only. Not readiness, authentication, execution, quality or permission.'}


def render(report: dict[str, Any]) -> str:
    lines = ['Проверка доступных инструментов — без запусков и изменений.', '']
    for check in report['checks']:
        if check['required'] or check['status'] == 'found':
            lines.append(check['message_ru'])
            if check['status'] != 'found' and check['next_ru']:
                lines.append('Следующий шаг: ' + check['next_ru'])
    lines += ['', 'Наличие инструмента не подтверждает его запуск, вход в аккаунт или право доступа.',
              'Модели, глобальные настройки и файлы проекта не изменялись.']
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--audience', choices=('engineering', 'product'), default='product')
    parser.add_argument('--need', action='append', choices=('review', 'browser', 'tests', 'preview', 'claim'), default=[])
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--playbook-source', action='store_true',
                        help='Inspect author test dependencies of this Playbook checkout, not a downstream project')
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    try:
        report = inspect_environment(args.root, args.audience, set(args.need),
                                     playbook_source=args.playbook_source)
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report))
        return 1 if report['missing_required'] or report['pending_live'] else 0
    except (OSError, ValueError) as exc:
        print(f'playbook_environment: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

"""Publish a plain-language round-2 report from actual receipts, without raw chats."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import statistics
from round2_checks import read,sha,write


def publish(root,output):
    root=Path(root).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    plan=read(root/'run-plan.json');runs=[];receipts=[]
    for item in plan['order']:
        path=root/'results'/f'{item["id"]}.json'
        if not path.is_file():
            runs.append({**item,'status':'NOT_RUN','task_status':'NOT_RUN','protocol_status':'NOT_RUN','score':None,'cost_usd':None,'human_minutes':None})
            continue
        value=read(path)
        # Child output snippets go into diagnostic evidence only; primary chats stay local.
        for entry in value.get('host_sessions',[]):entry.pop('messages',None)
        runs.append(value)
        name=f'evidence/{item["case"]}-{item["condition"]}-{item["repeat"]}.json'
        write(output/name,value);receipts.append({'path':name,'sha256':sha(output/name)})
    diagnostics=[]
    for path in sorted((root/'diagnostics').glob('*/result.json')):
        value=read(path);diagnostics.append(value)
        write(output/'evidence'/f'diagnostic-{value["kind"]}.json',value)
    decision='REVISE_OR_REJECT' if any(r['condition']=='C' and (r['task_status']=='FAIL' or r['protocol_status']=='FAIL') for r in runs) else 'KEEP_EXPERIMENTAL'
    value={'schema':'playbook.delegation.round2.results.v1','experiment_id':plan['experiment_id'],
           'environment':{k:plan[k] for k in ('head','model','reasoning','seed','repeats')},
           'runs':runs,'diagnostics':diagnostics,'decision':decision,
           'measurement_status':{'cost_usd':'NOT_RUN','active_human_minutes':'NOT_RUN'},
           'qualification_note':'Task success and useful measured performance do not fill unknown USD or human minutes.'}
    write(output/'results.json',value);write(output/'run-plan.json',plan)
    write(output/'evidence-index.json',{'raw_root':str(root),'receipts':receipts})
    lines=['# Что получилось во втором раунде','',
           'Проверены два вида работы: импорт продаж в SQLite и решение о выпуске релиза по нескольким источникам. '
           'Для каждого вида — два повтора A/B/C. A работает обычно, B использует Playbook без делегирования реализации, '
           'C подключает 2–3 независимых помощника. Все модельные запуски реальные; непроведённые не заменены симуляцией.','',
           '## Что исправлено','',
           '- Деньги теперь представлены целыми копейками. Старые примеры потери точности/overflow и все числа долей из неудачной попытки проверяются без float. '
           'Новый контракт объявлен заранее; старые failed outputs остаются заморожены.','- У ожидания есть предел: implementation 300 секунд, весь прогон с проверками/одной repair — 540 секунд. '
           'Помощник получает 60 секунд; завершённого помощника не используют повторно. Проверка кода запускается свежим общим read-only Role Runner.','',
           '## Результаты задач','',
           '| Задача | A: обычный | B: Playbook, один | C: с помощниками |','|---|---|---|---|']
    for name in ('sales_import','release_gate'):
        cells=[]
        for condition in 'ABC':
            values=[r for r in runs if r['case']==name and r['condition']==condition]
            counts=Counter(r['task_status'] for r in values)
            cells.append(', '.join(f'{n} {status}' for status,n in sorted(counts.items())))
        lines.append(f'| {name} | '+ ' | '.join(cells)+' |')
    lines += ['','## Время и расход','',
              '| Задача | Median A, с | Median B, с | Median C, с | C/B wall | C/B uncached input | C/B output |',
              '|---|---:|---:|---:|---:|---:|---:|']
    comparisons=[]
    for name in ('sales_import','release_gate'):
        buckets={c:[r for r in runs if r['case']==name and r['condition']==c and r.get('wall_seconds') is not None] for c in 'ABC'}
        median={c:statistics.median(r['wall_seconds'] for r in values) if values else None for c,values in buckets.items()}
        def ratio(key):
            b=sum(r.get(key,0) for r in buckets['B']);c=sum(r.get(key,0) for r in buckets['C'])
            return c/b if b else None
        for values in buckets.values():
            for r in values:r['uncached_input_tokens']=r['input_tokens']-r['cached_input_tokens']
        wall=median['C']/median['B'] if median['B'] and median['C'] is not None else None
        row=[*(f'{median[c]:.2f}' if median[c] is not None else 'NOT RUN' for c in 'ABC'),
             *(f'{x:.2f}×' if x is not None else '—' for x in (wall,ratio('uncached_input_tokens'),ratio('output_tokens')))]
        lines.append('| '+name+' | '+' | '.join(row)+' |')
        comparisons.append({'case':name,'median_wall':median,'c_b_wall':wall,'c_b_uncached_input':ratio('uncached_input_tokens'),'c_b_output':ratio('output_tokens')})
    lines += ['','Меньше 1× означает меньший расход/время C, больше 1× — больший. Это отдельные наблюдаемые единицы; '
              'токены не называются денежной стоимостью. Фактических USD billing receipts у этого host нет. '
              'Активное время человека без его участия не измерено; ноль обращений не означает ноль человеко-минут.','',
              '## Проверки помощников','']
    for item in diagnostics:lines.append(f'- {item["kind"]}: **{item["status"]}**. [Receipt](evidence/diagnostic-{item["kind"]}.json).')
    if not diagnostics:lines.append('- Реальные диагностические прогоны ещё NOT RUN.')
    lines += ['','Stale-input probe даёт настоящему model worker старый GO-снимок и проверяет, что основной агент отвергает его '
              'реально полученный ответ по текущим данным. Это не выдуманный ответ и не доказательство обнаружения любой галлюцинации. '
              'Timeout probe проверяет настоящий interrupt работающего native worker; результат local process unit test его не заменяет.','',
              '## Решение','',f'**{decision}**. Без измеренных USD/активного времени человека и более широкого опыта делегирование '
              'не становится режимом по умолчанию. По таблице отдельно видно, на какой из этих задач оно было быстрее/медленнее '
              'и требовало больше/меньше токенов. Два повтора не доказывают пользу для любой работы.','',
              'Подробные оценки, first attempts, repairs, независимые code-review verdicts и actual thread/settings/usage receipts — '
              '[results.json](results.json). Raw chats остаются локально: `'+str(root)+'`. Исходный первый раунд не переписан.']
    value['comparisons']=comparisons
    write(output/'results.json',value)
    (output/'REPORT_RU.md').write_text('\n'.join(lines)+'\n')
    return {'decision':decision,'report':str(output/'REPORT_RU.md'),'runs':len(runs)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    print(json.dumps(publish(args.root,args.output),ensure_ascii=False,indent=2))

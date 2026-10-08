"""Aggregate and report Controlled Delegation observations without causal claims."""
from __future__ import annotations
import statistics
from collections import defaultdict
from pathlib import Path
from experiment_core import write_json
from experiment_checks import validate_results

def mean(vals): return '—' if not vals else f'{statistics.mean(vals):.2f}'
def summary(runs):
    done=[r for r in runs if r['status'] in {'PASS','FAIL'}]
    return {'pass':sum(r['status']=='PASS' for r in runs),'fail':sum(r['status']=='FAIL' for r in runs),'nr':sum(r['status'] in {'NOT_RUN','BLOCKED'} for r in runs),
      'score':mean([float(r['outcome_score']) for r in done if r.get('outcome_score') is not None]),'human':mean([float(r['human_minutes']) for r in done if r.get('human_minutes') is not None]),'cost':mean([float(r['cost_usd']) for r in done if r.get('cost_usd') is not None]),'agents':mean([float(r['subagents_started']) for r in done])}

def decision(v,m):
    runs=v['runs']; c=[r for r in runs if r['condition']=='C']; reasons=[]
    if any(r['status'] in {'NOT_RUN','BLOCKED'} for r in c): return 'KEEP_EXPERIMENTAL',['Не все реальные C-прогоны выполнены.']
    if any(r['status']=='FAIL' for r in c): reasons.append('Есть FAIL в Controlled Delegation.')
    if any(r['critical_errors'] or r['write_conflicts'] for r in c): reasons.append('Есть критические ошибки или конфликты записи.')
    lim=m['limits']
    if any(r['max_parallel']>lim['max_parallel_agents_c'] for r in c): reasons.append('Превышен parallel limit.')
    if any(r['max_depth']>lim['max_depth_c'] for r in c): reasons.append('Превышен depth limit.')
    if any(r['owner_checkpoints']>lim['max_owner_checkpoints_c'] for r in c): reasons.append('Слишком много owner checkpoints.')
    by={r['scenario']:r for r in c}
    if by['small_fix']['subagents_started']!=0: reasons.append('Маленькая задача зря запустила субагентов.')
    if not by['conflict_detection'].get('failed_or_conflicting_worker_detected'): reasons.append('Не подтверждено обнаружение противоречивого worker.')
    if not by['fresh_session'].get('fresh_session_success'): reasons.append('Fresh-session continuation не подтверждён.')
    if reasons: return 'REVISE_OR_REJECT',reasons
    comparable=True; attention=0
    for s in by:
        b=next(r for r in runs if r['scenario']==s and r['condition']=='B'); cc=by[s]
        if b['status'] not in {'PASS','FAIL'} or b.get('human_minutes') is None or cc.get('human_minutes') is None: comparable=False; continue
        attention += cc['human_minutes']<=b['human_minutes']
        if b.get('outcome_score') is not None and cc.get('outcome_score') is not None and cc['outcome_score']<b['outcome_score']-5: reasons.append(f'Качество C ниже B: {s}.')
        if b.get('cost_usd') not in {None,0} and cc.get('cost_usd') is not None and cc['cost_usd']/b['cost_usd']>lim['max_cost_multiplier_without_quality_gain'] and (cc.get('outcome_score') or 0)-(b.get('outcome_score') or 0)<10: reasons.append(f'C >2x без quality gain: {s}.')
    if reasons: return 'REVISE_OR_REJECT',reasons
    if not comparable or attention<3: return 'KEEP_EXPERIMENTAL',['Недостаточно сопоставимых данных о внимании человека.']
    return 'ENABLE_CONDITIONALLY',['C прошёл ограничения и не увеличил участие человека минимум в 3 сценариях.']

def make_report(v,output_dir:Path):
    m=validate_results(v); output_dir.mkdir(parents=True,exist_ok=True); write_json(output_dir/'results.json',v); outcome,reasons=decision(v,m); grouped=defaultdict(list)
    for r in v['runs']: grouped[r['condition']].append(r)
    env=v.get('environment',{}); names={x['id']:x['name'] for x in m['conditions']}
    lines=['# Controlled Delegation — отчёт эксперимента','',f"Experiment: `{m['experiment_id']}`",f"HEAD: `{env.get('head','unknown')}`",f"Model/host: `{env.get('model','unknown')}` / `{env.get('host','unknown')}`",'', '> Ограниченный эксперимент: не универсальное доказательство multi-agent и не бизнес-пилот.','', '## Сводка','', '| Условие | PASS | FAIL | BLOCKED/NOT RUN | Outcome | Human min | Cost USD | Subagents |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in 'ABC':
        x=summary(grouped[c]); lines.append(f"| {c}: {names[c]} | {x['pass']} | {x['fail']} | {x['nr']} | {x['score']} | {x['human']} | {x['cost']} | {x['agents']} |")
    lines += ['', '## По сценариям','', '| Сценарий | A | B | C | C agents/depth/checkpoints | Mechanical |','|---|---|---|---|---|---|']
    for s in [x['id'] for x in m['scenarios']]:
        row={r['condition']:r for r in v['runs'] if r['scenario']==s}; c=row['C']; mech=c.get('mechanical',{}).get('status','NOT_RECORDED')
        lines.append(f"| {s} | {row['A']['status']} | {row['B']['status']} | {c['status']} | {c['subagents_started']}/{c['max_depth']}/{c['owner_checkpoints']} | {mech} |")
    lines += ['', '## Решение','',f'**{outcome}**','',*(f'- {x}' for x in reasons),'','## Что ещё не доказано','', '- перенос на другие модели/hosts/задачи;','- стоимость и внимание на реальной длительной работе;','- удобство для нетехнического владельца процесса;','- depth > 1;','- полезность ежедневных автоматизаций как отдельного runtime.','', 'Raw traces остаются локально в experiment workspaces.']
    report=output_dir/'REPORT_RU.md'; report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return {'status':'reported','decision':outcome,'report':str(report),'results':str(output_dir/'results.json')}

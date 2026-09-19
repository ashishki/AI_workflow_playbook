"""Public Codex execution counters. Missing data remains unknown, never zero."""
import json
import math
import re
from pathlib import Path

TOKEN_FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens')


def known_sum(values):
    if not values or any(isinstance(v, bool) or not isinstance(v, (int, float))
                         or not math.isfinite(v) or v < 0 for v in values):
        return 'unknown'
    return sum(values)


def trace_metrics(path: Path) -> dict:
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    usage = [e.get('usage', {}) for e in events if isinstance(e, dict) and e.get('type') == 'turn.completed']
    tools = {e['item']['id'] for e in events if isinstance(e, dict)
             and isinstance(e.get('item'), dict) and 'id' in e['item']
             and e['item'].get('type') in {'command_execution', 'mcp_tool_call', 'web_search'}}
    review_attempts = {e['item'].get('id', str(index)) for index, e in enumerate(events)
        if isinstance(e, dict) and e.get('type') == 'item.completed'
        and isinstance(e.get('item'), dict) and e['item'].get('type') == 'command_execution'
        and re.search(r'run_codex_role\.py[\s\"\']+run\b', e['item'].get('command', ''))}
    return {**{field: known_sum([u.get(field, 'unknown') for u in usage]) for field in TOKEN_FIELDS},
            'tool_call_count': len(tools), 'review_attempts': len(review_attempts)}


def execution_metrics(trace: Path, receipt: Path, review_traces: list[Path]) -> dict:
    primary = trace_metrics(trace)
    reviews = [trace_metrics(path) for path in review_traces]
    env = json.loads(receipt.read_text())['environment_summary']
    duration = (env['end_monotonic_ns'] - env['start_monotonic_ns']) / 1e9
    totals = {field: known_sum([primary[field]] + [r[field] for r in reviews])
              for field in (*TOKEN_FIELDS, 'tool_call_count')}
    missing = max(0, primary['review_attempts'] - len(reviews))
    if missing:
        totals = {field: 'unknown' for field in totals}
    return {'version': 'codex-execution.v1', 'primary': primary, 'reviews': reviews,
            'total': totals, 'review_count': max(primary['review_attempts'], len(reviews)),
            'missing_review_traces': missing, 'latency_seconds': duration,
            'cost': 'unknown', 'scope': 'main execution plus captured Role Runner reviews'}

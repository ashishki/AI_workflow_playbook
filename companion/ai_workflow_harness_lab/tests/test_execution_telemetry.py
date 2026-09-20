import json

from ai_workflow_harness_lab.telemetry import trace_metrics, execution_metrics
from ai_workflow_harness_lab.comparison import summarize


def trace(path, input_tokens, output_tokens):
    path.write_text('\n'.join(json.dumps(e) for e in [
        {'type': 'item.started', 'item': {'id': 'one', 'type': 'command_execution'}},
        {'type': 'item.completed', 'item': {'id': 'one', 'type': 'command_execution'}},
        {'type': 'turn.completed', 'usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens}},
    ]))


def test_nested_review_tokens_are_counted_once_and_latency_is_not_added_twice(tmp_path):
    main, review, receipt = [tmp_path / p for p in ('main.jsonl', 'review.jsonl', 'receipt.json')]
    trace(main, 100, 20)
    trace(review, 50, 10)
    receipt.write_text(json.dumps({'environment_summary': {'start_monotonic_ns': 0, 'end_monotonic_ns': 5_000_000_000}}))
    measured = execution_metrics(main, receipt, [review])
    assert measured['total']['input_tokens'] == 150
    assert measured['total']['output_tokens'] == 30
    assert measured['total']['tool_call_count'] == 2
    assert measured['latency_seconds'] == 5
    assert measured['review_count'] == 1
    assert measured['total']['cached_input_tokens'] == 'unknown'


def test_missing_usage_is_unknown_instead_of_a_zero_cost_success(tmp_path):
    path = tmp_path / 'events.jsonl'
    path.write_text('{"type":"turn.completed","usage":{}}\n')
    assert trace_metrics(path)['input_tokens'] == 'unknown'


def test_moved_or_deleted_review_trace_does_not_make_review_free(tmp_path):
    main, receipt = tmp_path / 'main.jsonl', tmp_path / 'receipt.json'
    main.write_text(json.dumps({'type': 'item.completed', 'item': {'id': 'review-call',
        'type': 'command_execution', 'command': 'python scripts/run_codex_role.py run --profile native'}})
        + '\n' + json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 100, 'output_tokens': 20}}))
    receipt.write_text(json.dumps({'environment_summary': {'start_monotonic_ns': 0, 'end_monotonic_ns': 5}}))
    result = execution_metrics(main, receipt, [])
    assert result['review_count'] == 1
    assert result['missing_review_traces'] == 1
    assert result['total']['input_tokens'] == 'unknown'


def test_comparison_does_not_hide_missing_measurements_from_one_attempt():
    template = {'valid': True, 'failures': [], 'score': 1.0, 'evidence_valid': True,
                'task_id': 'backend', 'scorer_outputs': [], 'receipt_count': 1}
    measured = {'total': {'input_tokens': 100, 'output_tokens': 10}, 'latency_seconds': 5, 'review_count': 1}
    report = summarize([{**template, 'execution_telemetry': measured}, template])
    assert report['input_tokens'] == 'unknown'
    assert report['wall_clock_latency'] == 'unknown'

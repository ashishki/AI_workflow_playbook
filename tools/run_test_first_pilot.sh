#!/usr/bin/bash -p
set -euo pipefail

# `bash -p` ignores BASH_ENV, exported functions, SHELLOPTS, and CDPATH before
# this allowlist removes the inherited process environment.
sanitize_environment() {
  local saved_home=${HOME:?HOME must identify the Codex subscription account}
  local saved_thread_id=${CODEX_THREAD_ID-}
  local saved_approval_record=${TFA_PILOT_APPROVAL_RECORD-}
  local saved_approval_id=${TFA_PILOT_APPROVAL_ID-}
  local saved_pilot_id=${TFA_PILOT_ID-}
  local variable

  while IFS= read -r variable; do
    unset "$variable" 2>/dev/null || true
  done < <(compgen -e)

  HOME=$saved_home
  CODEX_THREAD_ID=$saved_thread_id
  TFA_PILOT_APPROVAL_RECORD=$saved_approval_record
  TFA_PILOT_APPROVAL_ID=$saved_approval_id
  TFA_PILOT_ID=$saved_pilot_id
  export HOME
  export LANG=C.UTF-8
  export LC_ALL=C.UTF-8
  export PATH="/home/ashishki/.nvm/versions/node/v22.22.1/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin:/usr/bin:/bin"
  export PIP_CONFIG_FILE=/dev/null
  export PIP_DISABLE_PIP_VERSION_CHECK=1
  export PYTHONDONTWRITEBYTECODE=1
  export PYTHONNOUSERSITE=1
  export PYTHONPYCACHEPREFIX=/dev/null/test-first-pilot-pycache
  export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
}

sanitize_environment

SCRIPT_DIR=${BASH_SOURCE[0]%/*}
if [[ $SCRIPT_DIR == "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIR=.
fi
ROOT=$(cd "$SCRIPT_DIR/.." && pwd -P)
SUITE="$ROOT/companion/ai_workflow_harness_lab/suites/shishki_bot_ci_v1"
ADAPTER="$ROOT/tools/test_first_pilot_codex_adapter.py"
REGISTRY="$ROOT/reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md"
ASSET_MANIFEST="$ROOT/reports/test_first_pilot/shishki_bot_v1/ASSET_MANIFEST.sha256"
CRITIC_RECORD="$ROOT/reports/test_first_pilot/shishki_bot_v1/CRITIC_REVIEW.md"
PILOT_REPORT_ROOT="$ROOT/reports/test_first_pilot/shishki_bot_v1"
RUNS_ROOT="$PILOT_REPORT_ROOT/runs"
APPROVAL_USAGE_ROOT="$PILOT_REPORT_ROOT/approval_usage"
PYTHON="$ROOT/.venv/bin/python"
TOOLCHAIN_VERIFIER="$ROOT/tools/verify_test_first_pilot_toolchain.py"
MANIFEST_BUILDER="$ROOT/tools/build_test_first_pilot_manifest.py"
PERMISSION_VERIFIER="$ROOT/tools/verify_test_first_pilot_permissions.py"
RUN_SEAL="$ROOT/tools/test_first_pilot_run_seal.py"
CODEX="/home/ashishki/.nvm/versions/node/v22.22.1/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex"
BASH_BIN="/usr/bin/bash"
BWRAP="/usr/bin/bwrap"
CP="/usr/bin/cp"
MKDIR="/usr/bin/mkdir"
SHA256SUM="/usr/bin/sha256sum"
SYSTEM_PYTHON="/usr/bin/python3.12"
PYTHON_FLAGS=(-I -B -X "pycache_prefix=/dev/null/test-first-pilot-pycache")
TOOLCHAIN_PYTHON_FLAGS=(-I -S -B -X "pycache_prefix=/dev/null/test-first-pilot-pycache")

sha256_file() {
  local output
  output=$("$SHA256SUM" -- "$1")
  printf '%s\n' "${output%% *}"
}

verify_bootstrap() {
  # sha256sum is the minimal external trust anchor; the isolated verifier then
  # checks it again with Python's hashlib and checks every later executable.
  [[ /proc/$$/exe -ef $BASH_BIN ]] || {
    printf 'runner is not executing with the pinned Bash binary\n' >&2
    exit 2
  }
  [[ $PYTHON -ef $SYSTEM_PYTHON ]] || {
    printf 'pilot virtualenv Python no longer resolves to the pinned interpreter\n' >&2
    exit 2
  }
  [[ $(sha256_file "$SHA256SUM") == 9992e1f1feb6f0f396bc8d6691ebc1adbfc269fd628bce84eda1d4ba5c3995c7 ]] || {
    printf 'bootstrap sha256sum binary drifted\n' >&2
    exit 2
  }
  [[ $(sha256_file "$BASH_BIN") == bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1 ]] || {
    printf 'bootstrap Bash binary drifted\n' >&2
    exit 2
  }
  [[ $(sha256_file "$SYSTEM_PYTHON") == 1643dacd9feaedc58f3cc581e4d22577dfe25c09b10282936186ccf0f2e61118 ]] || {
    printf 'bootstrap Python binary drifted\n' >&2
    exit 2
  }
}

verify_frozen_assets() {
  [[ -f $ASSET_MANIFEST && ! -L $ASSET_MANIFEST ]] || {
    printf 'frozen asset manifest is missing: %s\n' "$ASSET_MANIFEST" >&2
    exit 2
  }
  verify_bootstrap
  (
    cd "$ROOT"
    "$SHA256SUM" -c -- "$ASSET_MANIFEST"
  )
  "$PYTHON" "${TOOLCHAIN_PYTHON_FLAGS[@]}" "$TOOLCHAIN_VERIFIER"
  "$PYTHON" "${PYTHON_FLAGS[@]}" "$MANIFEST_BUILDER" --check
}

file_has_exact_line() {
  local path=$1
  local expected=$2
  local line
  while IFS= read -r line || [[ -n $line ]]; do
    if [[ $line == "$expected" ]]; then
      return 0
    fi
  done < "$path"
  return 1
}

require_approval_line() {
  local line=$1
  file_has_exact_line "$TFA_PILOT_APPROVAL_RECORD" "$line" || {
    printf 'approval record is missing exact line: %s\n' "$line" >&2
    exit 2
  }
}

require_terminal_critic_allow() {
  local decision_count=0
  local last_nonempty=
  local line
  while IFS= read -r line || [[ -n $line ]]; do
    if [[ -n $line ]]; then
      last_nonempty=$line
    fi
    if [[ $line == Decision:* ]]; then
      decision_count=$((decision_count + 1))
    fi
  done < "$CRITIC_RECORD"
  if [[ $decision_count -ne 1 || $last_nonempty != 'Decision: ALLOW' ]]; then
    printf 'critic record must end with exactly one Decision: ALLOW line\n' >&2
    exit 2
  fi
}

require_terminal_approval() {
  local decision_count=0
  local last_nonempty=
  local line
  while IFS= read -r line || [[ -n $line ]]; do
    if [[ -n $line ]]; then
      last_nonempty=$line
    fi
    if [[ $line == Decision:* ]]; then
      decision_count=$((decision_count + 1))
    fi
  done < "$TFA_PILOT_APPROVAL_RECORD"
  if [[ $decision_count -ne 1 || $last_nonempty != 'Decision: approved' ]]; then
    printf 'approval record must end with exactly one Decision: approved line\n' >&2
    exit 2
  fi
}

harness() {
  "$PYTHON" "${PYTHON_FLAGS[@]}" -m ai_workflow_harness_lab.cli "$@"
}

verify_governance_unchanged() {
  [[ $(sha256_file "$ASSET_MANIFEST") == "$MANIFEST_DIGEST" ]] || {
    printf 'approved asset manifest changed during execution\n' >&2
    exit 2
  }
  [[ $(sha256_file "$TFA_PILOT_APPROVAL_RECORD") == "$APPROVAL_DIGEST" ]] || {
    printf 'approval record changed during execution\n' >&2
    exit 2
  }
  [[ $(sha256_file "$CRITIC_RECORD") == "$CRITIC_DIGEST" ]] || {
    printf 'critic record changed during execution\n' >&2
    exit 2
  }
}

authorize_full_run() {
  if [[ -n ${CODEX_THREAD_ID:-} ]]; then
    printf 'refusing nested pilot execution; launch from a separate human shell or CI\n' >&2
    exit 2
  fi

  : "${TFA_PILOT_APPROVAL_RECORD:?set TFA_PILOT_APPROVAL_RECORD to the durable approval path}"
  : "${TFA_PILOT_APPROVAL_ID:?set TFA_PILOT_APPROVAL_ID to the approval record ID}"
  : "${TFA_PILOT_ID:?set TFA_PILOT_ID to a new immutable run ID}"

  if [[ ! $TFA_PILOT_ID =~ ^[a-z0-9][a-z0-9._-]{2,63}$ ]]; then
    printf 'TFA_PILOT_ID must be a 3-64 character lowercase path-safe ID\n' >&2
    exit 2
  fi
  if [[ ! $TFA_PILOT_APPROVAL_ID =~ ^[a-z0-9][a-z0-9._-]{2,63}$ ]]; then
    printf 'TFA_PILOT_APPROVAL_ID must be a 3-64 character lowercase path-safe ID\n' >&2
    exit 2
  fi
  if [[ ! -f $REGISTRY || -L $REGISTRY \
    || ! -f $ASSET_MANIFEST || -L $ASSET_MANIFEST \
    || ! -f $CRITIC_RECORD || -L $CRITIC_RECORD \
    || ! -f $TFA_PILOT_APPROVAL_RECORD || -L $TFA_PILOT_APPROVAL_RECORD ]]; then
    printf 'registry, manifest, critic record, or approval record is missing or linked\n' >&2
    exit 2
  fi

  MANIFEST_DIGEST=$(sha256_file "$ASSET_MANIFEST")
  CRITIC_DIGEST=$(sha256_file "$CRITIC_RECORD")
  APPROVAL_DIGEST=$(sha256_file "$TFA_PILOT_APPROVAL_RECORD")
  require_terminal_critic_allow
  require_terminal_approval
  require_approval_line "Approval ID: $TFA_PILOT_APPROVAL_ID"
  require_approval_line "Pilot ID: $TFA_PILOT_ID"
  require_approval_line "Manifest SHA-256: $MANIFEST_DIGEST"
  require_approval_line "Critic report SHA-256: $CRITIC_DIGEST"
  require_approval_line 'Approver: Artem Shishkin'
  require_approval_line 'TFA-7.1: approved'
  require_approval_line 'TFA-7.2A: approved'
  require_approval_line 'TFA-7.2B: approved'
  require_approval_line 'TFA-7.2C: approved'
  require_approval_line 'Local evidence boundary: trusted single-writer host; no concurrent mutation; no independent attestation'
  require_approval_line 'Codex executions: 12'
  require_approval_line 'Paid API budget: USD 0'
  require_approval_line 'Retries: 0'
  require_approval_line 'Retention: raw 90 days; sanitized 365 days'
  require_approval_line 'Decision: approved'
}

preflight_only=false
if [[ ${1:-} == "--preflight-only" ]]; then
  preflight_only=true
elif [[ $# -ne 0 ]]; then
  printf 'usage: %s [--preflight-only]\n' "$0" >&2
  exit 2
fi

verify_bootstrap
if [[ $preflight_only != true ]]; then
  authorize_full_run
fi
verify_frozen_assets
harness validate-suite "$SUITE"
"$PYTHON" "${PYTHON_FLAGS[@]}" -m pytest -p no:cacheprovider --noconftest \
  "$ROOT/tests/unit/test_prepare_test_first_pilot_review.py" \
  "$ROOT/tests/unit/test_test_first_pilot_adapter.py" \
  "$ROOT/tests/unit/test_test_first_pilot_assets.py" \
  "$ROOT/tests/unit/test_test_first_pilot_permissions.py" \
  "$ROOT/tests/unit/test_test_first_pilot_run_seal.py" \
  "$ROOT/tests/unit/test_test_first_pilot_sandbox.py" \
  "$ROOT/tests/unit/test_test_first_pilot_toolchain.py" \
  "$ROOT/companion/ai_workflow_harness_lab/tests/test_cli.py" \
  "$ROOT/companion/ai_workflow_harness_lab/tests/test_comparison.py" \
  "$ROOT/companion/ai_workflow_harness_lab/tests/test_diff_scope.py" \
  "$ROOT/companion/ai_workflow_harness_lab/tests/test_shell_scorer.py" -q
"$PYTHON" "${PYTHON_FLAGS[@]}" "$PERMISSION_VERIFIER"

if [[ $preflight_only == true ]]; then
  printf 'pilot static preflight: ok; no model invocation attempted\n'
  exit 0
fi

verify_governance_unchanged
[[ $("$CODEX" --version) == 'codex-cli 0.144.4' ]] || {
  printf 'Codex CLI version drifted from codex-cli 0.144.4\n' >&2
  exit 2
}
LOGIN_STATUS=$("$CODEX" login status 2>&1) || {
  printf 'Codex login status command failed\n' >&2
  exit 2
}
[[ $LOGIN_STATUS == 'Logged in using ChatGPT' ]] || {
  printf 'Codex is not authenticated through ChatGPT subscription login\n' >&2
  exit 2
}

"$MKDIR" -p -- "$RUNS_ROOT" "$APPROVAL_USAGE_ROOT"
for directory in \
  "$ROOT/reports" \
  "$ROOT/reports/test_first_pilot" \
  "$PILOT_REPORT_ROOT" \
  "$RUNS_ROOT" \
  "$APPROVAL_USAGE_ROOT"; do
  if [[ ! -d $directory || -L $directory ]]; then
    printf 'pilot output directory is missing or linked: %s\n' "$directory" >&2
    exit 2
  fi
done

RUN_ROOT="$RUNS_ROOT/$TFA_PILOT_ID"
if [[ -e $RUN_ROOT ]]; then
  printf 'run root already exists; refusing overwrite: %s\n' "$RUN_ROOT" >&2
  exit 2
fi
APPROVAL_LOCK="$APPROVAL_USAGE_ROOT/$TFA_PILOT_APPROVAL_ID"
if ! "$MKDIR" "$APPROVAL_LOCK" 2>/dev/null; then
  printf 'approval ID was already consumed: %s\n' "$TFA_PILOT_APPROVAL_ID" >&2
  exit 2
fi
"$MKDIR" -p -- "$RUN_ROOT"
"$CP" -- "$TFA_PILOT_APPROVAL_RECORD" "$RUN_ROOT/approval_record.md"
"$CP" -- "$ASSET_MANIFEST" "$RUN_ROOT/asset_manifest.sha256"
"$CP" -- "$CRITIC_RECORD" "$RUN_ROOT/critic_record.md"
printf '%s\n' "$RUN_ROOT" > "$APPROVAL_LOCK/run_path.txt"
printf '%s  approval_record.md\n%s  asset_manifest.sha256\n%s  critic_record.md\n' \
  "$APPROVAL_DIGEST" "$MANIFEST_DIGEST" "$CRITIC_DIGEST" \
  > "$RUN_ROOT/governance_manifest.sha256"

MODEL_COMMAND="\"$BWRAP\" --die-with-parent --new-session --unshare-pid --bind / / --proc /proc --dev-bind /dev /dev -- \"$PYTHON\" -I -B -X \"pycache_prefix=/dev/null/test-first-pilot-pycache\" \"$ADAPTER\" --workspace \"{workspace}\" --prompt \"{prompt_file}\" --output \"{output_dir}\" --pilot-id \"$TFA_PILOT_ID\" --attempt-id \"{task_id}-{condition}-{trial}\" --task \"{task_id}\" --condition \"{condition}\" --trial \"{trial}\" --manifest-digest \"$MANIFEST_DIGEST\" --approval-id \"$TFA_PILOT_APPROVAL_ID\" --codex-bin \"$CODEX\" --timeout 1200"

run_one() {
  local task_id=$1
  local trial=$2
  local condition=$3
  local output="$RUN_ROOT/$condition"
  local append_args=()
  verify_governance_unchanged
  verify_frozen_assets
  if [[ -f $output/run_index.json ]]; then
    append_args=(--append)
  fi
  harness run \
    --suite "$SUITE" \
    --condition "$condition" \
    --adapter command \
    --command-template "$MODEL_COMMAND" \
    --adapter-timeout 1260 \
    --task-id "$task_id" \
    --trial-start "$trial" \
    --trials 1 \
    --output "$output" \
    --fail-on-invalid-run \
    "${append_args[@]}"
}

# Counterbalanced arm order across six preregistered pairs.
run_one pin_ci_actions 0 baseline
run_one pin_ci_actions 0 playbook
run_one reject_unapproved_ci_actions 0 playbook
run_one reject_unapproved_ci_actions 0 baseline

run_one pin_ci_actions 1 playbook
run_one pin_ci_actions 1 baseline
run_one reject_unapproved_ci_actions 1 baseline
run_one reject_unapproved_ci_actions 1 playbook

run_one pin_ci_actions 2 baseline
run_one pin_ci_actions 2 playbook
run_one reject_unapproved_ci_actions 2 playbook
run_one reject_unapproved_ci_actions 2 baseline

shopt -s globstar nullglob
BUNDLES=("$RUN_ROOT"/**/bundle.json)
shopt -u globstar nullglob
if [[ ${#BUNDLES[@]} -ne 12 ]]; then
  printf 'expected 12 bundles, found %s\n' "${#BUNDLES[@]}" >&2
  exit 1
fi
for bundle in "${BUNDLES[@]}"; do
  harness verify-bundle "$bundle"
  "$PYTHON" "${PYTHON_FLAGS[@]}" "$ROOT/tools/validate_harness_evidence.py" "$bundle"
done
verify_frozen_assets

for bundle in "${BUNDLES[@]}"; do
  printf '%s  %s\n' "$(sha256_file "$bundle")" "${bundle#"$RUN_ROOT/"}"
done > "$RUN_ROOT/bundle_manifest.sha256"

verify_governance_unchanged
verify_frozen_assets
"$PYTHON" "${PYTHON_FLAGS[@]}" "$RUN_SEAL" write "$RUN_ROOT" >/dev/null

printf 'pilot execution finished; evidence awaits independent pair adjudication: %s\n' "$RUN_ROOT"

# Native product checks

Maintainer tools, not part of a subscriber installation.
New comparisons use the existing **[Harness Lab Native suite](harness/README.md)**
and the [current development protocol](../../docs/native/DEVELOPMENT_RU.md).
The suite covers backend repair, plan-only, review-only, frontend, persistent
bookings and consent-aware contact export. The [plain/current/lean plan](VALUE_CHECK_RU.md)
tests incremental value over the plain agent; packaging checks cannot establish it.
The older runner below
is retained for reproducing diagnostics and browser-specific probes; it is not
the new comparison framework. Ground Truth Lab is deferred.

Read the [historical diagnostic protocol](PROTOCOL.md) to reproduce its trials and
[actual results](../../reports/native/2026-09-19/REPORT_RU.md) before making claims.
Synthetic repos only. No downstream app, global configuration or model changes.

## Reproduce

Requirements: authenticated `codex`, Git, Python 3.10+, Node, and an existing
Playwright installation with Chromium for the external browser probes. The runner
inherits the host's model/effort and user instructions; it is not a clean profile.
CLI and tool versions must be recorded. There is no automatic dependency install.

```bash
# Use the absolute module path for your existing Playwright installation.
export PLAYBOOK_EVAL_PLAYWRIGHT_MODULE=/absolute/path/node_modules/playwright

python3 evals/native/run.py --case frontend --condition baseline \
  --output .playbook-artifacts/native-pilot/my-baseline
python3 evals/native/run.py --case frontend --condition native \
  --output .playbook-artifacts/native-pilot/my-native

node evals/native/check-ui.cjs \
  .playbook-artifacts/native-pilot/my-native/workspace \
  .playbook-artifacts/native-pilot/my-native/external-check
node evals/native/check-launcher.cjs .playbook-artifacts/native-pilot/my-launcher
python3 -m unittest discover -s evals/native -p test_runner.py -v
```

Run the external probe against both arms and the original fixture. The original
fixture must fail success/mobile/error checks despite passing `npm test`; this
confirms that the probe detects the actual defects. Inspect the screenshots.
An external probe passing does **not** prove that the task agent used a browser.

Other model cases: `backend`, `plan`, `new-plan`, `review`, `no-browser`, `setup`,
`remove`, `quick`. Only frontend/backend/no-browser accept a baseline arm. A case being
available does not mean it has been run. Each output directory must be fresh;
raw events, before/after hashes, exact prompt, CLI command and final message are
retained. Deadline/failure/incomplete or malformed traces return a nonzero exit.
A completed model turn still requires semantic assessment; exit 0 is not PASS.

Harness unit tests use an explicitly fake CLI to test timeout/corruption/evidence
preservation. They are never counted as agent trials. `check-launcher.cjs` checks
UI behavior, not whether an agent correctly understands all possible requests.

## Optional local MCP condition

Supply an already installed official Playwright MCP CLI and Chromium:

```bash
python3 evals/native/run.py --case frontend --condition native \
  --browser-mcp-cli /absolute/path/node_modules/@playwright/mcp/cli.js \
  --browser-executable /absolute/path/chrome \
  --output .playbook-artifacts/native-pilot/my-mcp
```

For comparisons, give **both** arms the same capability. The runner starts its
own loopback server for that checkout and supplies transient MCP configuration;
it stops the server afterwards. Preview links in the agent final then expire.
This synthetic browser uses an isolated profile, local origin filtering and no
WebMCP. Origin filtering is not a security boundary. When running as root it
uses Chromium's `--no-sandbox`; the Codex workspace sandbox and approval policy
remain unchanged. Do not use this root-only laboratory browser with real accounts
or untrusted pages. Prefer a properly sandboxed non-root host for later trials.

Our MCP trial was **blocked** by tool approval and browser initialization; a
successful standalone tool preflight did not grant the agent access. Do not
weaken approval or try alternate routes around a denial to complete an eval.
Use a host with legitimately available capabilities for the next full trial.

Primary references: [Codex noninteractive execution](https://developers.openai.com/codex/noninteractive),
[Playwright MCP](https://github.com/microsoft/playwright-mcp).

## Native install lifecycle in a disposable container

This probe writes a personal plugin catalog **inside a new container only**.
It refuses to run without the evaluation image marker or with an existing plugin
source/catalog. Do not mount a user's home/config, Docker socket, or credentials.
No inference, network or account is needed for this lifecycle check. Build the
image separately (that step downloads Python/system packages):

```bash
docker build -t playbook-native-eval:20260919 evals/native/container
export PLAYBOOK_REPO="$(pwd)"
export PLAYBOOK_CODEX_BIN=/absolute/path/to/native/codex
export PLAYBOOK_CREATOR_SCRIPTS=/absolute/path/to/plugin-creator/scripts
mkdir -p .playbook-artifacts/my-lifecycle

docker run --rm --network none \
  --mount "type=bind,src=$PLAYBOOK_CODEX_BIN,dst=/codex,readonly" \
  --mount "type=bind,src=$PLAYBOOK_REPO/plugins/playbook-native,dst=/input,readonly" \
  --mount "type=bind,src=$PLAYBOOK_CREATOR_SCRIPTS,dst=/creator,readonly" \
  --mount "type=bind,src=$PLAYBOOK_REPO/evals/native/plugin_lifecycle.py,dst=/probe.py,readonly" \
  --mount "type=bind,src=$PLAYBOOK_REPO/.playbook-artifacts/my-lifecycle,dst=/out" \
  playbook-native-eval:20260919 python3 /probe.py
```

Supply the Linux native binary matching the image architecture, not the Node
wrapper. The output directory must be fresh. The probe uses official Plugin
Creator helpers, checks native namespaced skills in fresh app-server sessions,
reinstalls, updates via cachebuster, removes, and compares project hashes.
`lifecycle/result.json` retains actual commands, output and discovery results.
This checks lifecycle/discovery, not whether the model can read or follow a skill.
A model trial additionally needs its complete tool runtime; missing tools are a
failed trial, even if `codex exec` returns 0. Do not change permissions to force PASS.

For the delivered ZIP, first run the [archive tests/build](../../distribution/native/README.md),
extract it, then check its actual page (optional second positional argument):

```bash
node evals/native/check-launcher.cjs .playbook-artifacts/my-kit-ui \
  '/absolute/path/to/extracted/Playbook/START.html'
```

The new [onboarding report](../../reports/native/2026-09-19-onboarding/REPORT_RU.md)
separates native lifecycle, archive discovery, independent agent work and parent
browser checks. Clipboard success uses a controlled API stub; fallback selection
is exercised, but real OS clipboard integrations require desktop testing.

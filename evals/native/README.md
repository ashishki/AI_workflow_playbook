# Native diagnostic evaluations

Maintainer tools for this source preview, not part of a subscriber installation.
Read [PROTOCOL.md](PROTOCOL.md) **before** a model trial and
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

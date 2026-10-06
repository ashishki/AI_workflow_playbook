# Native kit (maintainer instructions)

This remains the canonical portable Playbook payload and the manual fallback for
private evaluation. It contains the same skills used by the Desktop setup.

    python3 distribution/native/sync_runtime.py --check
    python3 -m unittest discover -s distribution/native -p 'test_*.py' -v
    python3 distribution/native/build.py --output .playbook-artifacts/my-new-kit

The recipient can still extract the ZIP, select `Мой проект` in Codex and
describe a task directly. This fallback requires no build tools to *start*.
Its included Role Runner still needs an available Python 3.10+ and authenticated
Codex CLI when used directly.

For the preferred beginner preview, build the OS-specific wrapper in
`distribution/desktop/`. It embeds this exact ZIP and its checksum, adds a
local setup/update/remove transaction, and packages Python inside the helper so
the recipient does not have to install it. The Desktop review runtime is optional
and owner-confirmed.

The Native builder itself uses only Python's standard library; it does not install,
download, connect accounts or publish. `PACKAGE.json` covers every payload file
and the sidecar records the ZIP hash. Symlinks and non-portable collisions are
refused. No generated app, credentials, model configuration, developer reports or
dependency tree is shipped.

Before handing off any changed artifact, test the exact package. Native tests and
browser launcher probes do not establish desktop login, real reviewer capability,
clean-machine usability or user benefit. Those remain separate observations.

This is not a public release. Rights and supported delivery must be settled before
subscriber distribution. Development and eval decisions follow
[DEVELOPMENT_RU.md](../../docs/native/DEVELOPMENT_RU.md).

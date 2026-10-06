# Desktop setup preview (maintainer)

This directory turns the existing Native product kit into an OS-specific private
evaluation setup bundle. It does **not** create a second agent platform. The
user still works in Codex; the setup program only connects the canonical
Playbook files to a selected folder and optionally prepares the independent
review runtime.

## What the preview removes from beginner setup

- no system Python is required for the packaged Role Runner;
- no Git, GitHub, VPS, Docker, Node or API key is required to start discovery;
- update/remove operate only on Playbook-owned files and marked instruction
  blocks, refusing to overwrite owner edits;
- a transaction journal can restore the previous **installation state** after an
  interrupted setup. It is not application/data backup;
- the optional Codex CLI used by independent review is downloaded only after
  explicit confirmation from pinned official OpenAI release assets and verified
  by size and SHA256. Login is a separate owner action;
- diagnostics distinguish installed files, CLI launch/login, actual review,
  browser verification and user/business outcomes.

The binaries are intentionally not claimed as public release artifacts. They
still need clean-machine trials, code signing/notarization decisions, real
desktop login/reviewer checks and field pilots.

## Build

Python 3.12 and PyInstaller are maintainer build dependencies, not recipient
requirements.

    python -m pip install pyinstaller==6.16.0
    python -m unittest discover -s distribution/desktop -p "test_*.py" -v
    python distribution/desktop/build.py --output .playbook-artifacts/desktop

The builder first creates the canonical Native ZIP, embeds its exact bytes and
hash in both frozen executables, builds `Playbook-Setup` plus
`playbook-helper`, runs the frozen helper's offline self-test, then packages an
OS-specific ZIP with the Native ZIP as a manual fallback.

Build on each target OS. Do not cross-compile and then claim compatibility.

## Security/authority boundary

The setup program never treats installation as permission to publish, connect
business accounts, spend money or change production. It never copies account
tokens. The managed reviewer runtime is per-user and does not alter global PATH,
model or authentication settings. The current preview is unsigned; do not tell
a tester to disable operating-system protections to run it.

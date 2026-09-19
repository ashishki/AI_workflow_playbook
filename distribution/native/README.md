# Offline beginner kit (maintainer instructions)

Builds a small private evaluation ZIP from the canonical native package and
start page. The recipient extracts it, opens `START.html`, selects `Мой проект`
in Codex, and describes a task. No build tools are required by the recipient.

```bash
python3 -m unittest discover -s distribution/native -p test_build.py -v
python3 distribution/native/build.py --output .playbook-artifacts/my-new-kit
```

The output directory must not already contain this version's ZIP or checksum.
The script uses only Python's standard library; it does not install, download,
connect accounts or publish. Identical inputs on the same compression toolchain
produce identical ZIP bytes. `PACKAGE.json` records every payload file's SHA256;
a sidecar records the ZIP's hash. Symlinks are refused. The archive contains:

- `START.html`, a short Russian opening note and the existing rights statement;
- `Мой проект/`: exact canonical skills, the project block and a beginner README;
- `plugins/playbook-native/`: manifest and the same skills for native installation;
- `PACKAGE.json`, for inspection by the maintainer, not a user workflow step.

No generated app, historical manuals, tests, reports, credentials, model
configuration, `.git`, developer README or dependency tree is shipped. The two
skill copies serve different routes; only the starter copy is discovered when
opening `Мой проект`. Do not install the plugin globally as well for that trial.

Before handing off a changed ZIP, extract it to a fresh path, verify its manifest
and discovery, and run the [launcher probe](../../evals/native/README.md) against
its actual `START.html`. The tested result and artifact hash belong in the
[version report](../../reports/native/README.md).
Do not rename a different payload to an already distributed version.

This is not a public release. Rights and a supported desktop walkthrough must
be settled before subscriber distribution. The [small pilot plan](../../docs/native/PILOT_RU.md)
is for the owner; it is not copied into users' projects.

Development and eval decisions follow the [maintainer protocol](../../docs/native/DEVELOPMENT_RU.md).

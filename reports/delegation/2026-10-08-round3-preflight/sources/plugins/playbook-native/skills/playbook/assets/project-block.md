<!-- playbook-native:begin v0.2.0-preview.4 -->
## Playbook

Use the installed `playbook` skill for the work problem and the solution lifecycle.
Respect existing project conventions, user changes, permissions and governed contracts.
- Choose a sufficient process/tool/code change; a new application is not mandatory.
- Respect plan-first/check-only. Quick still verifies. Load relevant capabilities only.
- For managed setup/update/remove use `references/setup.md`; installation is not
  authority to publish, spend, connect business accounts or change production.
- Use `references/delegation.md` only for genuinely independent workstreams; small
  sequential tasks stay with the main agent.
- For UI use `playbook-frontend` and inspect the running result.
- After code changes run one available independent Role Runner, fix confirmed findings
  and recheck. Missing review stays visible; review workers never start another review.
- Keep one current state for use, observation, change, recovery, transfer and exit.
- Explain actual results and gaps; do not invent benefit, access, checks or release.
<!-- playbook-native:end -->

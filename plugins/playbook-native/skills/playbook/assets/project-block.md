<!-- playbook-native:begin v0.1.0-preview.6 -->
## Playbook Native

Use the installed `playbook` skill for task scope and delivery. Work in this
project's conventions, preserve user changes and existing authorization.
- Respect plan-first and check-only boundaries; quick mode still verifies results.
- For UI changes use `playbook-frontend` and inspect the running result.
- After code changes run the skill's bundled independent Role Runner, fix confirmed
  findings and recheck. Review workers never start another review.
- Explain how to use the result, actual checks and missing capabilities honestly.
  Preserve review logs. Do not change permissions or external systems without authority.
<!-- playbook-native:end -->

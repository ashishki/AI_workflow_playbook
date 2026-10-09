# Verify the app you changed

Use existing run scripts and browser instructions. These checks apply to local
development; a project's CI/release evidence policy can require more.

## Reach the right app

- Start the app from the actual checkout/worktree being edited, on an available
  port. Use the server's real ready URL. Do not reuse or stop an unknown process
  just because it occupies the expected port. Give concurrent worktrees separate
  ports and browser sessions.
- Check a distinctive property of this change in the rendered app. Compare it
  with the source being edited and the process you started. A URL, PID, commit
  label, or HTTP 200 alone does not establish that the changed code is running.
  On mismatch, rebuild/restart your own server and recheck. Do not report a pass
  if the mismatch remains unresolved.
- With HMR, wait for the changed screen to settle. Recapture after subsequent
  code edits. For a remote preview, require a deployment/build identity tied to
  the revision under review; otherwise state that the preview is unverified.
- A cloud browser's localhost may be a different machine. Do not expose a local
  service publicly or add a tunnel without authorization. Prefer a browser
  colocated with the dev server when available.

## Observe useful evidence

- Use a fresh test session and non-sensitive data. Exercise the main interaction
  and a relevant edge/error state. Verify the visible result and relevant
  persistence/navigation; clicking a button alone is not a successful outcome.
- Capture current screenshots after fonts/data are ready and animations settle.
  Open the images to inspect them. A saved PNG that was never viewed proves
  capture, not visual review. If image inspection is unavailable, disclose it.
- Inspect console/network errors when the tool provides them; distinguish new
  defects from known background noise. If those diagnostics are unavailable,
  state that gap instead of inventing a clean console.
- Use the project's artifact location or the session's temporary output folder.
  Keep only useful screenshots/traces and link them. Do not commit recordings,
  cookies, credentials, or customer data by default. No receipt schema is needed
  for a normal local check. Formal provenance is required only by project policy.
- Screenshot comparisons help stable repeated UI surfaces. Preserve established
  baselines; inspect differences before proposing updates. Do not add pixel
  snapshots to every UI change or hide defects with masks/looser thresholds.

## Missing capability

Use an already installed native browser, project Playwright runner, browser CLI,
or appropriate connected MCP tool. Do not install all alternatives. If none is
available, complete independent code checks and report exactly what blocks the
browser check and the smallest next step. Human inspection may close that gap,
but never relabel it as agent verification. An installed skill is not a browser.

Close only servers and browser sessions you created, unless the user needs the
preview kept open. Tell the user if a linked preview has been stopped.

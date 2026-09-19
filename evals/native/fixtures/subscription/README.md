# Письма по делу

A small static subscription page. No installation or remote services needed.

- `npm test`: existing input validation checks.
- `npm run preview`: local HTTP preview on 127.0.0.1:8011.
- For this self-contained static app, a browser can also open `index.html` by file URL.
- The available Playwright module path is provided in `PLAYBOOK_EVAL_PLAYWRIGHT_MODULE`.
  Use Node `require(process.env.PLAYBOOK_EVAL_PLAYWRIGHT_MODULE)` to access it.
- Chromium is already installed. You may use the browser and inspect screenshots.
- This demo displays subscription confirmation locally; it must not call external services.

const { chromium } = require('/tmp/visual-review/node_modules/playwright');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const root = path.resolve(__dirname, '..');
const evidence = path.join(root, 'evidence');
const files = { '/': ['index.html', 'text/html; charset=utf-8'], '/styles.css': ['styles.css', 'text/css'], '/app.js': ['app.js', 'text/javascript'] };
const checks = [];
const server = http.createServer(async (request, response) => {
  const file = files[new URL(request.url, 'http://localhost').pathname];
  if (!file) { response.writeHead(404).end(); return; }
  response.writeHead(200, { 'Content-Type': file[1] });
  response.end(await fs.readFile(path.join(root, file[0])));
});

async function main() {
  await fs.mkdir(evidence, { recursive: true });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}`;
  console.log(`Local preview: ${url}`);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [];
  const requests = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('requestfailed', request => errors.push(`Failed: ${request.url()}`));
  page.on('response', response => { if (response.status() >= 400) errors.push(`HTTP ${response.status()}: ${response.url()}`); });
  page.on('request', request => requests.push(request.url()));
  try {
    await page.goto(url, { waitUntil: 'networkidle' });
    assert.match(await page.title(), /English with Alina/);
    assert.match(await page.locator('h1').textContent(), /настоящей жизни/);
    assert.equal(await page.locator('.service-card').count(), 3);
    assert.equal(await page.locator('.price').first().textContent(), '1 500 ₽ / 60 минут');
    checks.push('Correct app served from this project: title, hero, three services and price match source.');
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('.skip-link').evaluate(node => node === document.activeElement), true);
    assert.notEqual(await page.locator('.skip-link').evaluate(node => getComputedStyle(node).outlineStyle), 'none');
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => location.hash), '#main');
    checks.push('Keyboard skip link operates and has visible focus styling.');
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(evidence, 'desktop.png') });
    await page.locator('#lessons').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(evidence, 'desktop-lessons.png') });
    for (const course of ['start', 'talk', 'travel']) {
      await page.locator(`[data-course="${course}"]`).click();
      assert.equal(await page.locator('#course').inputValue(), course);
      assert.equal(await page.locator('#name').evaluate(node => node === document.activeElement), true);
    }
    checks.push('All three course buttons open the form, select the matching course and focus the name field.');
    assert.equal(await page.locator('input, select, textarea').evaluateAll(nodes => nodes.every(node => node.labels.length > 0)), true);
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('#email').evaluate(node => node === document.activeElement), true);
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('#course').evaluate(node => node === document.activeElement), true);
    await page.keyboard.press('ArrowUp');
    assert.equal(await page.locator('#course').inputValue(), 'talk');
    checks.push('Form controls have labels; keyboard Tab order and native select operate.');
    await page.getByRole('button', { name: 'Проверить учебную заявку' }).click();
    assert.equal(await page.locator('#name-error').isVisible(), true);
    assert.equal(await page.locator('#email-error').isVisible(), true);
    assert.equal(await page.locator('#name').evaluate(node => node === document.activeElement), true);
    await page.locator('#name').fill('  ');
    await page.locator('#email').fill('wrong-email');
    await page.getByRole('button', { name: 'Проверить учебную заявку' }).click();
    assert.equal(await page.locator('#name').getAttribute('aria-invalid'), 'true');
    assert.equal(await page.locator('#email').getAttribute('aria-invalid'), 'true');
    checks.push('Empty submission, whitespace-only name and malformed email are blocked with visible errors.');
    await page.locator('#request').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(evidence, 'desktop-form-errors.png') });
    await page.locator('#name').fill('Саша');
    await page.locator('#email').fill('sasha@example.com');
    await page.locator('#message').fill('Хочу общаться в поездках без переводчика.');
    const beforeSubmit = requests.length;
    await page.getByRole('button', { name: 'Проверить учебную заявку' }).click();
    assert.equal(await page.locator('#request-form').isVisible(), false);
    assert.match(await page.getByRole('status').textContent(), /Саша, учебная заявка заполнена/);
    assert.match(await page.getByRole('status').textContent(), /никуда не отправлены/);
    await page.waitForTimeout(150);
    assert.equal(requests.length, beforeSubmit);
    assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0]);
    checks.push('Successful submission shows an explicit demo result; no request or browser storage is created.');
    await page.getByRole('button', { name: 'Заполнить ещё раз' }).click();
    assert.equal(await page.locator('#name').inputValue(), '');
    assert.equal(await page.locator('#email').inputValue(), '');
    assert.equal(await page.locator('#course').inputValue(), 'unsure');
    await page.locator('#name').fill('Тест');
    await page.reload({ waitUntil: 'networkidle' });
    assert.equal(await page.locator('#name').inputValue(), '');
    checks.push('Reset and reload clear the form.');
    for (const width of [360, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `Overflow at ${width}px`);
    }
    checks.push('No horizontal page overflow at 360, 390, 768 or 1440px.');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(evidence, 'mobile.png') });
    await page.locator('#lessons').screenshot({ path: path.join(evidence, 'mobile-lessons.png') });
    await page.locator('#approach').screenshot({ path: path.join(evidence, 'mobile-approach.png') });
    assert.match(await page.locator('#approach-title').innerText(), /Без гонки\. С вниманием к вам\./);
    assert.match(await page.locator('#request-title').innerText(), /Давайте познакомимся\./);
    await page.locator('[data-course="talk"]').click();
    await page.locator('#name').fill('Маша');
    await page.locator('#email').fill('masha@example.com');
    await page.locator('#request-form').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(evidence, 'mobile-form.png') });
    await page.getByRole('button', { name: 'Проверить учебную заявку' }).click();
    assert.match(await page.getByRole('status').textContent(), /Маша, учебная заявка заполнена/);
    await page.screenshot({ path: path.join(evidence, 'mobile-success.png') });
    checks.push('Mobile (390 × 844) course selection and successful form interaction pass.');
    await page.goto(pathToFileURL(path.join(root, 'index.html')).href, { waitUntil: 'load' });
    assert.equal(await page.locator('.demo-banner').evaluate(node => getComputedStyle(node).backgroundColor), 'rgb(39, 65, 55)');
    await page.locator('#name').fill('Саша');
    await page.locator('#email').fill('sasha@example.com');
    await page.getByRole('button', { name: 'Проверить учебную заявку' }).click();
    assert.match(await page.getByRole('status').textContent(), /учебная заявка заполнена/);
    checks.push('Direct opening with file:// loads CSS and the working form, without a server.');
    assert.deepEqual(errors, []);
    assert.equal(requests.some(request => /^https?:/.test(request) && !request.startsWith(url)), false);
    checks.push('No observed browser console/page/network errors or external HTTP requests.');
    await fs.writeFile(path.join(evidence, 'checks.json'), JSON.stringify({ time: new Date().toISOString(), browser: 'Chromium', checks, screenshots: ['desktop.png', 'desktop-lessons.png', 'desktop-form-errors.png', 'mobile.png', 'mobile-lessons.png', 'mobile-approach.png', 'mobile-form.png', 'mobile-success.png'], note: 'Screenshots require separate visual inspection. No automated accessibility audit or other browsers tested.' }, null, 2) + '\n');
    console.log(checks.map(check => `PASS: ${check}`).join('\n'));
  } finally {
    await context.close();
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.close());

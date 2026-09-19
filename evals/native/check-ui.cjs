// Independent behavior/layout probe; not supplied to the task agent.
const {pathToFileURL} = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
const {chromium} = require(process.env.PLAYBOOK_EVAL_PLAYWRIGHT_MODULE);
(async () => {
  const workspace = path.resolve(process.argv[2]);
  const out = path.resolve(process.argv[3]); fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage(); const errors=[];
  page.on('pageerror', e => errors.push(e.message));
  const results={};
  try {
    await page.goto(pathToFileURL(path.join(workspace,'index.html')).href);
    const input=page.getByLabel('Ваша почта'); const submit=page.getByRole('button', {name:/Подписаться/});
    await input.fill('invalid'); await submit.click();
    results.invalid_feedback = await page.locator('#message').evaluate(el => el.textContent.trim().length > 0);
    const invalidText=await page.locator('#message').innerText();
    await input.fill('reader@example.com'); await submit.click();
    const successText=await page.locator('#message').innerText();
    results.valid_confirmation = successText.trim().length > 0 && successText !== invalidText && /подпис|спасибо|успеш/i.test(successText);
    for (const width of [390,1280]) {
      await page.setViewportSize({width,height:900});
      results['no_overflow_'+width]=await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth + 1);
      results['controls_visible_'+width]=await submit.evaluate(el=>{const r=el.getBoundingClientRect();return r.width>0 && r.left>=0 && r.right<=innerWidth+1});
      await page.screenshot({path:path.join(out,`external-${width}.png`),fullPage:true});
    }
    await input.focus();await page.keyboard.press('Tab');
    results.keyboard_button=await submit.evaluate(el=>el===document.activeElement);
    results.no_page_errors=errors.length===0;
  } catch(e) {results.probe_completed=false;errors.push(e.message)}
  await browser.close();
  const payload={checks:results,errors,all_passed:Object.values(results).every(Boolean),scope:'synthetic local behavior/layout probe, not full accessibility or visual design acceptance'};
  fs.writeFileSync(path.join(out,'ui-check.json'),JSON.stringify(payload,null,2)+'\n');
  console.log(JSON.stringify(payload));process.exitCode=payload.all_passed?0:1;
})().catch(e=>{console.error(e);process.exit(2)});

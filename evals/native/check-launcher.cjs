const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYBOOK_EVAL_PLAYWRIGHT_MODULE);
(async()=>{
 const out=path.resolve(process.argv[2]);fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage();const errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))external.push(r.url())});
 await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedPrompt=text}}}));
 await page.goto(pathToFileURL(path.resolve(process.argv[3] || 'docs/native/start.html')).href);
 assert.equal(await page.getByRole('button',{name:'Скопировать запрос'}).isDisabled(),true);
 await page.getByRole('button',{name:/Быстро исправить/}).click();
 assert.match(await page.locator('#prompt').inputValue(),/Минимум бюрократии; проверка результата обязательна/);
 await page.getByRole('button',{name:'Скопировать запрос'}).click();
 assert.equal(await page.evaluate(()=>window.copiedPrompt),await page.locator('#prompt').inputValue());
 await page.locator('#options > summary').click();
 let combinations=0;
 for(const context of ['','new','existing'])for(const action of ['','create','fix','check'])for(const control of ['','auto','plan','extended']){
  await page.locator('#context').selectOption(context);await page.locator('#action').selectOption(action);await page.locator('#control').selectOption(control);
  const text=await page.locator('#prompt').inputValue();assert.ok(text.startsWith('Playbook, помоги с задачей.\n'));
  if(action==='check')assert.match(text,/Не исправляй исходники/);
  if(control==='plan')assert.match(text,/Не меняй файлы/);
  if(control==='auto')assert.match(text,/проверка результата обязательна/);
  combinations++;
 }
 await page.locator('#task').fill('<img src=x onerror="window.injected=true">');
 assert.equal(await page.locator('img').count(),0);assert.equal(await page.evaluate(()=>window.injected),undefined);
 await page.getByRole('button',{name:/Проверить готовое/}).click();
 await page.locator('#control').selectOption('extended');
 for(const width of [390,1280]){
  await page.setViewportSize({width,height:950});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
  await page.screenshot({path:path.join(out,`launcher-${width}.png`),fullPage:true});
 }
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:undefined}));
 await page.getByRole('button',{name:'Скопировать запрос'}).click();
 assert.match(await page.locator('#copy-feedback').innerText(),/Текст выделен/);
 assert.equal(await page.locator('#prompt').evaluate(e=>e.selectionEnd-e.selectionStart), (await page.locator('#prompt').inputValue()).length);
 await page.getByRole('button',{name:'возьмите учебный пример'}).click();
 assert.match(await page.locator('#task').inputValue(),/Я не программист/);
 assert.equal(await page.locator('#context').inputValue(),'new');
 await page.getByText('У меня уже есть свой проект',{exact:true}).click();
 await page.getByRole('button',{name:'Скопировать запрос подключения'}).click();
 assert.match(await page.locator('#install-prompt-feedback').innerText(),/Текст выделен/);
 await page.getByText('Не получается начать или открыть результат',{exact:true}).click();
 await page.getByRole('button',{name:'Скопировать запрос помощи'}).click();
 assert.match(await page.locator('#help-prompt-feedback').innerText(),/Текст выделен/);
 for(const width of [390,1280]){await page.setViewportSize({width,height:950});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);}
 const archiveEdition=await page.locator('body').getAttribute('data-kit')==='archive';
 assert.equal(await page.locator('#source-note').isHidden(),archiveEdition);
 await page.locator('#task').fill('   ');assert.equal(await page.locator('#copy').isDisabled(),true);
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={combinations,empty_input:'pass',scenario_prefills:'pass',clipboard:'pass',clipboard_fallback:'pass',first_run_example:'pass',install_and_help_prompts:'pass',archive_edition:archiveEdition,input_as_text:'pass',responsive:[390,1280],page_errors:errors,external_requests:external};
 fs.writeFileSync(path.join(out,'launcher-check.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

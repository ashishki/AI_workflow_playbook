const {chromium}=require('/tmp/visual-review/node_modules/playwright');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
(async()=>{const browser=await chromium.launch({headless:true});try{
 const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
 await page.goto(pathToFileURL(path.resolve('.playbook-artifacts/native-onboarding/first-run/Мой проект/index.html')).href);
 await page.locator('[data-course="talk"]').click();assert.equal(await page.locator('#course').inputValue(),'talk');
 await page.getByRole('button',{name:'Проверить учебную заявку'}).click();assert.equal(await page.locator('#name').getAttribute('aria-invalid'),'true');
 await page.locator('#name').fill('Тестовый ученик');await page.locator('#email').fill('wrong');
 await page.getByRole('button',{name:'Проверить учебную заявку'}).click();assert.equal(await page.locator('#email').getAttribute('aria-invalid'),'true');
 await page.locator('#email').fill('student@example.com');await page.getByRole('button',{name:'Проверить учебную заявку'}).click();assert.match(await page.getByRole('status').innerText(),/никуда не отправлены/);
 await page.getByRole('button',{name:'Заполнить ещё раз'}).click();assert.equal(await page.locator('#name').inputValue(),'');
 for(const width of [360,390,768,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
 assert.deepEqual(errors,[]);assert.equal(requests.some(u=>/^https?:/.test(u)),false);
 const result={passed:true,reviewer:'parent agent; independently written probe',browser:await browser.version(),direct_file_open:true,course_selection:true,empty_and_invalid_email:true,demo_success:true,reset:true,widths:[360,390,768,1440],page_errors:errors,external_requests:requests.filter(u=>/^https?:/.test(u))};
 fs.writeFileSync('.playbook-artifacts/native-onboarding/independent-ui.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});

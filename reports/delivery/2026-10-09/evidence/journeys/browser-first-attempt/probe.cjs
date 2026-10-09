const {chromium}=require('/tmp/visual-review/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const out=path.join(__dirname,'external-browser');fs.mkdirSync(out,{recursive:true});
const checks=[];
(async()=>{
const browser=await chromium.launch({headless:true});
try {
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 await page.goto(process.argv[2],{waitUntil:'networkidle'});
 await page.locator('#list-status').filter({hasText:''}).waitFor();
 assert((await page.locator('h1').textContent()).includes('Записи'));
 await page.screenshot({path:path.join(out,'desktop-empty.png'),fullPage:true});
 const fill=async(student,date,slot)=>{await page.fill('#student',student);await page.fill('#date',date);await page.fill('#slot',slot);};
 await fill('Синтетическая Анна','2027-03-02','09:30');await page.click('#submit');
 await page.waitForFunction(()=>document.querySelector('#form-status').textContent.includes('Запись создана'));
 assert((await page.locator('#bookings').textContent()).includes('Синтетическая Анна'));
 checks.push({id:'real_ui_create_and_read',status:'PASS'});
 await fill('Конфликт','2027-03-02','09:30');await page.click('#submit');
 await page.waitForFunction(()=>document.querySelector('#form-status').classList.contains('error'));
 assert((await page.locator('#form-status').textContent()).length>0);
 checks.push({id:'visible_conflict_error',status:'PASS'});
 await page.selectOption('#teacher','boris');await page.waitForFunction(()=>document.querySelector('#bookings').textContent.includes('Пока нет записей'));
 assert(!(await page.locator('#bookings').textContent()).includes('Синтетическая Анна'));
 checks.push({id:'identity_switch_clears_other_list',status:'PASS'});
 await page.setViewportSize({width:390,height:844});await fill('<img src=x onerror=alert(1)>','2027-03-02','09:30');await page.click('#submit');
 await page.waitForFunction(()=>document.querySelector('#form-status').textContent.includes('Запись создана'));
 assert((await page.locator('#bookings').textContent()).includes('<img src=x onerror=alert(1)>'));
 assert.strictEqual(await page.locator('#bookings img').count(),0);
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
 await page.screenshot({path:path.join(out,'mobile-created.png'),fullPage:true});
 checks.push({id:'mobile_no_horizontal_overflow_and_text_rendering',status:'PASS'});
 let committed=false;
 await page.route('**/api/bookings',async route=>{
   if(route.request().method()==='POST'&&!committed){committed=true;await route.fetch();await route.abort('failed');}
   else await route.continue();
 });
 await fill('Неизвестный исход','2027-03-02','10:00');await page.click('#submit');
 await page.waitForFunction(()=>document.querySelector('#form-status').classList.contains('error'));
 await page.click('#submit');
 await page.waitForFunction(()=>document.querySelector('#form-status').textContent.includes('повтор не создал дубликат'));
 assert.strictEqual((await page.locator('#bookings').textContent()).split('Неизвестный исход').length-1,1);
 checks.push({id:'committed_post_lost_response_retry_has_one_record',status:'PASS'});
 await page.reload({waitUntil:'networkidle'});await page.selectOption('#teacher','boris');
 await page.waitForFunction(()=>document.querySelector('#bookings').textContent.includes('Неизвестный исход'));
 checks.push({id:'page_reload_reads_persisted_bookings',status:'PASS'});
 await page.setViewportSize({width:1280,height:900});await page.screenshot({path:path.join(out,'desktop-created.png'),fullPage:true});
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({status:'PASS',checks,browser:await browser.version(),playwright:require('/tmp/visual-review/node_modules/playwright/package.json').version,url:process.argv[2],scope:'synthetic local app, no real participant/authentication/public preview'},null,2)+'\n');
 console.log(JSON.stringify({status:'PASS',checks}));
} catch(error){fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({status:'FAIL',checks,error:String(error)},null,2)+'\n');throw error;}
finally{await browser.close();}
})();

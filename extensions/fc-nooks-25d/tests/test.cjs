const { chromium } = require('playwright');
const fs = require('fs');
const assert = require('node:assert/strict');
const root = require('path').resolve(__dirname, '..');
const fixture = fs.readFileSync(__dirname+'/fixture.html','utf8');
(async()=>{
  const browser = await chromium.launch({
    executablePath:process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined),headless:true,
    args:['--no-sandbox']
  });
  const context=await browser.newContext({viewport:{width:1600,height:1050}});
  await context.route('https://app.playmfl.com/**',r=> {
    const url=r.request().url();
    if(url.endsWith('/viewer.css'))return r.fulfill({body:fs.readFileSync(root+'/viewer.css','utf8'),contentType:'text/css'});
    if(url.endsWith('/assets/harbour-park.jpg'))return r.fulfill({body:fs.readFileSync(root+'/assets/harbour-park.jpg'),contentType:'image/jpeg'});
    return r.fulfill({body:fixture,contentType:'text/html'});
  });
  const page = await context.newPage();
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  await page.goto('https://app.playmfl.com/matches/fixture-one');
  // Machine policy blocks unpacked extensions. Exercise packaged source in a
  // real browser, with only runtime.getURL mocked; do not claim MV3 load passed.
  await page.evaluate(()=>{globalThis.chrome=globalThis.chrome || {};chrome.runtime={getURL:name=>'https://app.playmfl.com/__fixture__/'+name};});
  for(const name of JSON.parse(fs.readFileSync(root+'/manifest.json','utf8')).content_scripts[0].js) await page.addScriptTag({content:fs.readFileSync(root+'/'+name,'utf8')});
  await page.locator('#fcn25d-toggle').waitFor({timeout:10000});
  console.log('PASS: packaged scripts create toggle (fixture injection; MV3 install blocked by administrator policy)');
  await page.locator('#fcn25d-toggle').click();
  await page.waitForTimeout(300);
  assert.equal(await page.locator('#fcn-score').textContent(),'2 – 1');
  assert.equal(await page.locator('#fcn-clock').textContent(),'29:42');
  assert.equal(await page.locator('[data-stadium-score]').count(),3);
  assert.deepEqual(await page.locator('[data-stadium-score]').allTextContents(),['2 – 1','2 – 1','2 – 1']);
  assert.deepEqual(await page.locator('[data-stadium-home]').allTextContents(),['RK','RK','RK']);
  assert.deepEqual(await page.locator('[data-stadium-away]').allTextContents(),['TCK','TCK','TCK']);
  assert.equal(await page.locator('[data-player]').count(),2);
  assert.equal(await page.locator('[data-ball]').getAttribute('visibility'),'visible');
  assert.equal(await page.locator('[data-goals] path').count(),8);
  console.log('PASS: scoreboard, clock, players, ball and two netted goals');
  // Capture rendered source and rendered overlay in a single browser evaluation.
  async function alignment(){return page.evaluate(()=>{
    const sh=document.querySelector('#fcn25d-host').shadowRoot;
    const source=document.querySelector('#mfl-pitch');
    const inv=source.getScreenCTM().inverse();
    const point=(el,x,y)=>new DOMPoint(x,y).matrixTransform(el.getScreenCTM()).matrixTransform(inv);
    const p=point(document.querySelector('#match-v2-p1'),1,2);
    const b=point(document.querySelector('#match-v2-puck'),0,0);
    const transform=el=>{const m=el.transform.baseVal.consolidate().matrix;return [m.e,m.f];};
    const project=p=>{
      const u=p.x/105,v=p.y/68,r=980/1588,d=1-v+r*v;
      return [(346*(1-v)+r*42*v+980*u)/d,(433*(1-v)+r*730*v)/d];
    };
    const actualP=transform(sh.querySelector('[data-player="match-v2-p1"]'));
    const actualB=transform(sh.querySelector('[data-ball]'));
    const error=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
    return {player:error(actualP,project(p)),ball:error(actualB,project(b)),sync:error(actualP,actualB),x:p.x};
  });}
  assert.ok((await alignment()).sync < .01);
  await page.evaluate(()=>{
    document.querySelector('#match-v2-p1').style.transform='translate(60px,40px)';
    document.querySelector('#match-v2-puck').style.transform='translate(61px,42px)';
  });
  const samples=[];
  for(let i=0;i<8;i++){await page.waitForTimeout(50);samples.push(await alignment());}
  assert.ok(samples.some(s=>s.x>24 && s.x<60),'Must sample rendered transition, not jump to target');
  assert.ok(samples.every(s=>s.sync<.05),'Player and ball must stay in sync');
  assert.ok(samples.every(s=>s.player<20 && s.ball<20),'Tracking must stay within roughly one rendered frame');
  console.log('PASS: rendered movement during native CSS transition, synchronized ball',JSON.stringify(samples));
  await page.waitForTimeout(300);
  assert.ok((await alignment()).player<.01);
  await page.evaluate(()=>{
    const parent=document.querySelector('#match-v2-p1').parentElement;
    const positions=[[4,31],[18,8],[18,23],[18,42],[18,56],[35,15],[35,33],[35,52],[49,8],[49,57]];
    for(let i=0;i<20;i++){
      const [px,py]=positions[i%10], el=document.createElementNS('http://www.w3.org/2000/svg','g');
      el.id='match-v2-p'+(i+3); el.setAttribute('transform',`translate(${i<10?px:101-px} ${py})`);
      el.innerHTML=`<circle r="1.5" fill="${i<10?'#ffbb30':'#3679ef'}"/><text>${i%10+1}</text>`;parent.append(el);
    }
  });
  await page.waitForTimeout(850);
  assert.equal(await page.locator('[data-player]').count(),22);
  console.log('PASS: full 22-player roster and node discovery');
  await page.waitForFunction(()=>document.querySelector('#fcn25d-host').shadowRoot.querySelector('svg').dataset.assetState==='ready');
  console.log('PASS: complete packaged stadium photograph loads');
  await page.screenshot({path:__dirname+'/harbour-park-desktop.png'});
  const width=await page.locator('#fcn-stage > svg').evaluate(el=>el.getBoundingClientRect().width);
  assert.ok(width>1000,'Packaged shadow stylesheet must load');
  await page.setViewportSize({width:600,height:900}); await page.waitForTimeout(100);
  assert.ok((await alignment()).sync<.01);
  await page.screenshot({path:__dirname+'/harbour-park-mobile.png'});
  console.log('PASS: responsive alignment and packaged stylesheet');
  await page.evaluate(()=>{
    const root=document.querySelector('#mfl-pitch');root.setAttribute('viewBox','-10 -5 125 78');
    const marker=document.createElementNS('http://www.w3.org/2000/svg','rect');
    for(const [k,v] of Object.entries({'data-testid':'pitch-bounds',x:0,y:0,width:105,height:68,fill:'none'}))marker.setAttribute(k,v);
    root.prepend(marker);
  });
  await page.waitForTimeout(100);
  assert.ok((await alignment()).player<.01);
  assert.ok((await alignment()).sync<.01);
  await page.evaluate(()=>{document.querySelector('[data-testid="pitch-bounds"]').remove();document.querySelector('#mfl-pitch').setAttribute('viewBox','0 0 105 68');});
  await page.waitForTimeout(100);
  console.log('PASS: padded viewBox with explicit pitch bounds');
  await page.locator('#fcn-select').click();
  await page.evaluate(()=>document.querySelector('#match-v2-puck circle').dispatchEvent(new MouseEvent('click',{bubbles:true})));
  await page.waitForTimeout(100);
  await page.evaluate(()=>{const old=document.querySelector('#mfl-pitch');old.replaceWith(old.cloneNode(true));});
  await page.waitForTimeout(900);
  assert.equal(await page.locator('[data-ball]').getAttribute('visibility'),'visible');
  console.log('PASS: manual ball selection and source SVG replacement recovery');
  await page.evaluate(()=>{document.querySelector('#match-v2-puck').remove();});
  await page.waitForTimeout(900);
  assert.equal(await page.locator('[data-ball]').getAttribute('visibility'),'hidden');
  console.log('PASS: missing ball is hidden, never fabricated');
  await page.evaluate(()=>{document.querySelector('header').innerHTML='<div><span class="clock">45:00</span> RK 3-1 TCK</div>';history.pushState({},'', '/matches/fixture-two');});
  await page.waitForTimeout(1000);
  assert.equal(await page.locator('#fcn-score').textContent(),'3 – 1');
  assert.equal(await page.locator('#fcn-clock').textContent(),'45:00');
  assert.deepEqual(await page.locator('[data-stadium-clock]').allTextContents(),['45:00','45:00','45:00']);
  await page.evaluate(()=>{document.querySelector('header').innerHTML='Unrecognised match data';});
  await page.waitForTimeout(350);
  assert.equal(await page.locator('#fcn-score').textContent(),'—');
  console.log('PASS: SPA match change and unavailable scoreboard reset');
  await page.evaluate(()=>{document.querySelector('#mfl-pitch').remove();history.pushState({},'', '/clubs');});
  await page.waitForTimeout(650);
  assert.ok(await page.locator('#fcn25d-toggle').isHidden());
  assert.ok(await page.locator('#fcn25d-view').isHidden());
  await page.evaluate(()=>{document.querySelector('#fcn25d-host').remove();history.pushState({},'', '/matches/fixture-three');});
  await page.waitForTimeout(650);
  assert.equal(await page.locator('#fcn25d-host').count(),1);
  assert.ok(await page.locator('#fcn25d-toggle').isVisible());
  await page.keyboard.press('Alt+Shift+M');
  assert.ok(await page.locator('#fcn25d-view').isVisible());
  await page.keyboard.press('Escape');
  assert.ok(await page.locator('#fcn25d-view').isHidden());
  console.log('PASS: navigation, host removal, keyboard toggle and Escape');
  assert.deepEqual(errors,[]);
  // Missing packaged art must not stop the live pitch or motion renderer.
  await context.route('**/assets/harbour-park.jpg',r=>r.fulfill({status:404,body:'Missing fixture asset'}));
  const fallbackPage=await context.newPage();
  fallbackPage.on('pageerror',e=>errors.push(e.message));
  await fallbackPage.goto('https://app.playmfl.com/matches/missing-asset');
  await fallbackPage.evaluate(()=>{globalThis.chrome=globalThis.chrome || {};chrome.runtime={getURL:name=>'https://app.playmfl.com/__fixture__/'+name};});
  for(const name of JSON.parse(fs.readFileSync(root+'/manifest.json','utf8')).content_scripts[0].js)await fallbackPage.addScriptTag({content:fs.readFileSync(root+'/'+name,'utf8')});
  await fallbackPage.locator('#fcn25d-toggle').click();
  await fallbackPage.waitForFunction(()=>document.querySelector('#fcn25d-host').shadowRoot.querySelector('svg').dataset.assetState==='failed');
  await fallbackPage.waitForTimeout(100);
  assert.equal(await fallbackPage.locator('[data-player]').count(),2);
  assert.equal(await fallbackPage.locator('[data-ball]').getAttribute('visibility'),'visible');
  assert.equal(await fallbackPage.locator('[data-asset-notice]').getAttribute('visibility'),'visible');
  assert.notEqual(await fallbackPage.locator('[data-fallback-grass]').getAttribute('fill'),'none');
  assert.equal(await fallbackPage.locator('#fcn-score').textContent(),'2 – 1');
  assert.deepEqual(errors,[]);
  console.log('PASS: missing stadium asset reports problem and preserves players, ball and scoreboard');
  await context.close();
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});

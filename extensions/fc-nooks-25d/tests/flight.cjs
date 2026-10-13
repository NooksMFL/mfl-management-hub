const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1400,height:950}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.setContent('<style>body{margin:0}#source{width:900px;height:600px}.motion{transition:transform 600ms linear}</style><svg id="source" viewBox="0 0 105 68"><g transform="translate(2 3) scale(1.2)"><g class="motion" id="ground" style="transform:translate(30px,30px)"><g id="match-v2-p1"><circle r="1.5" fill="red"/></g><g id="ball-shadow"><ellipse rx="1" ry=".4"/></g><g id="match-v2-puck" class="motion" style="transform:translate(0px,-6px)"><circle r=".6" fill="white"/></g></g></g></svg>');
  await page.evaluate(()=>{globalThis.chrome={runtime:{getURL:name=>'about:blank'}};});
  for(const file of ['tracking.js','stadiums.js','scene.js','camera.js','renderer.js'])await page.addScriptTag({content:fs.readFileSync(root+'/'+file,'utf8')});
  await page.evaluate(()=>{window.tracker=new FCN25D.Tracker();window.scene=FCN25D.buildScene();document.body.append(scene.svg);window.renderer=new FCN25D.Renderer(scene);window.camera=new FCN25D.ViewportCamera(scene);});
  async function capture(){return page.evaluate(()=>{
    const snapshot=tracker.sample();renderer.render(snapshot);camera.update(snapshot);
    const source=document.querySelector('#source'),inv=source.getScreenCTM().inverse();
    const centre=el=>{const b=el.getBBox();return new DOMPoint(b.x+b.width/2,b.y+b.height/2).matrixTransform(el.getScreenCTM()).matrixTransform(inv);};
    const ground=centre(document.querySelector('#ball-shadow')),air=centre(document.querySelector('#match-v2-puck'));
    const transform=el=>{const m=el.transform.baseVal.consolidate().matrix;return [m.e,m.f];};
    const expected=scene.project(ground.x/105,ground.y/68),actual=transform(scene.ball),p=transform(scene.actors.firstChild);
    return {ball:snapshot.ball,player:snapshot.players[0],ground,air,lift:-transform(scene.ball.querySelector('[data-ball-airborne]'))[1],error:Math.hypot(actual[0]-expected[0],actual[1]-expected[1]),sync:Math.hypot(actual[0]-p[0],actual[1]-p[1]),expectedLift:(ground.y-air.y)/105*scene.flightScale(ground.y/68)/scene.scale(ground.y/68)};
  });}
  let data=await capture();assert.equal(data.ball.flightMode,'rendered ball/shadow separation');assert.ok(Math.abs(data.ball.heightU-7.2/105)<.00001);assert.ok(data.sync<.0001);assert.ok(data.error<.0001);assert.ok(Math.abs(data.lift-data.expectedLift)<.0001);
  console.log('PASS: nested transforms: ground shadow anchors ball to player; sphere follows native lift');
  await page.evaluate(()=>{document.querySelector('#ground').style.transform='translate(60px,40px)';document.querySelector('#match-v2-puck').style.transform='translate(0px,-12px)';});
  const samples=[];
  for(let i=0;i<9;i++){await page.waitForTimeout(45);samples.push(await capture());}
  assert.ok(samples.some(s=>s.ball.heightU>7.4/105 && s.ball.heightU<14/105));
  assert.ok(samples.every(s=>s.sync<.0001 && s.error<.0001 && Math.abs(s.lift-s.expectedLift)<.0001));
  console.log('PASS: native flight and ground transitions sampled in one frame without interpolation lag');
  await page.waitForTimeout(250);
  await page.evaluate(()=>camera.setZoom(2.5));
  for(const id of await page.evaluate(()=>Object.keys(FCN25D.stadiums))){
    await page.evaluate(id=>scene.setStadium(id),id);data=await capture();assert.ok(data.sync<.0001 && data.error<.0001 && Math.abs(data.lift-data.expectedLift)<.0001);
  }
  assert.ok(await page.evaluate(()=>{
    const box=scene.svg.viewBox.baseVal,snapshot=tracker.sample(),ground=scene.project(snapshot.ball.u,snapshot.ball.v),airY=ground[1]-snapshot.ball.heightU*scene.flightScale(snapshot.ball.v);
    return ground[1]<=box.y+box.height && airY>=box.y && box.width<700;
  }),'Very close camera must keep sphere and ground shadow visible together');
  console.log('PASS: airborne ball and player alignment across all eleven calibrated stadiums; 2.5× camera retains sphere and shadow');
  await page.evaluate(()=>{document.querySelector('#match-v2-puck').style.transition='none';document.querySelector('#match-v2-puck').style.transform='translate(0px,0px)';});
  data=await capture();assert.ok(data.ball.heightU<.00001 && data.lift<.00001);
  console.log('PASS: landing returns sphere to its ground shadow immediately');
  await page.evaluate(()=>{
    document.querySelector('#ball-shadow').remove();const ball=document.querySelector('#match-v2-puck');
    ball.innerHTML='<ellipse id="ball-shadow" rx="1" ry=".4"/><circle cy="-8" r=".6" fill="white"/>';tracker.scan(performance.now());
  });
  // The group bbox includes its shadow; the visible sphere must be isolated.
  data=await page.evaluate(()=>tracker.sample());assert.ok(Math.abs(data.ball.heightU-9.6/105)<.00001);
  console.log('PASS: combined ball/shadow group uses sphere centre rather than combined bounding box');
  await page.evaluate(()=>{
    const shadow=document.querySelector('#ball-shadow');shadow.removeAttribute('id');tracker.scan(performance.now());tracker.selectShadow(shadow);
  });
  data=await page.evaluate(()=>tracker.sample());assert.equal(data.ball.flightMode,'rendered ball/shadow separation');
  console.log('PASS: explicitly selected unlabelled shadow supplies native flight cue');
  const picked=await page.evaluate(()=>{
    const shadow=document.querySelector('#match-v2-puck ellipse');shadow.style.pointerEvents='none';tracker.selectedShadow=null;
    const rect=shadow.getBoundingClientRect(),x=rect.left+rect.width/2,y=rect.top+rect.height/2;
    return tracker.selectShadow(document.elementFromPoint(x,y),x,y) && tracker.selectedShadow===shadow;
  });assert.ok(picked);
  console.log('PASS: explicit shadow hit test handles pointer-events:none without binding the pitch background');
  await page.evaluate(()=>{const old=document.querySelector('#source');old.replaceWith(old.cloneNode(true));});
  data=await page.evaluate(()=>tracker.sample());assert.equal(await page.evaluate(()=>tracker.selectedShadow),null);assert.ok(data.ball);
  await page.evaluate(()=>document.querySelector('#match-v2-puck').remove());
  data=await page.evaluate(()=>tracker.sample());assert.equal(data.ball,null);
  console.log('PASS: source replacement clears stale shadow binding; missing ball is never fabricated');
  assert.deepEqual(errors,[]);await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});

const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1600,height:1000}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.setContent('<style>body{margin:0}#source{width:900px;height:600px}.move{transition:transform 600ms linear}</style><div id="lineup"></div><svg id="source" viewBox="0 0 105 68"><rect width="105" height="68" fill="#438847"/><g id="match-v2-p1" data-last-name="Hansen" class="move" style="transform:translate(20px,30px)"><circle r="1.2" fill="#efb326"/><text>7</text></g><g id="match-v2-p2" aria-label="Player: Virgil van Dijk" transform="translate(80 30)"><circle r="1.2" fill="#267dc1"/><text>9</text></g><g id="match-v2-puck" class="move" style="transform:translate(20px,30px)"><circle r=".6" fill="white"/></g></svg>');
  await page.evaluate(()=>{globalThis.chrome={runtime:{getURL:name=>'about:blank'}};});
  for(const file of ['tracking.js','players.js','stadiums.js','scene.js','camera.js','sprites.js','renderer.js'])await page.addScriptTag({content:fs.readFileSync(root+'/'+file,'utf8')});
  await page.evaluate(()=>{
    window.tracker=new FCN25D.Tracker();window.info=new FCN25D.PlayerInfo();window.scene=FCN25D.buildScene();document.body.append(scene.svg);
    scene.svg.style.cssText='position:fixed;inset:0;width:1600px;height:900px';window.camera=new FCN25D.ViewportCamera(scene);window.renderer=new FCN25D.Renderer(scene);
    window.sample=()=>{const now=performance.now(),raw=tracker.sample(now),snapshot=info.enrich(raw,tracker,now);camera.update(snapshot);renderer.render(snapshot,now);return snapshot;};
  });
  let snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession.surname,'Hansen');assert.equal(snapshot.possession.source,'unambiguous ball proximity');
  assert.equal(await page.locator('[data-possession-label] text').textContent(),'Hansen');
  assert.equal(await page.locator('[data-possession-label][visibility="visible"]').count(),1);
  console.log('PASS: only ball carrier receives native surname; surname attributes and full accessible names supported');
  await page.evaluate(()=>{
    document.querySelector('#match-v2-p1').setAttribute('data-in-possession','false');document.querySelector('#match-v2-p2').setAttribute('data-in-possession','true');
    document.querySelector('#match-v2-puck').style.transition='none';document.querySelector('#match-v2-puck').style.transform='translate(80px,30px)';
  });
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession.surname,'van Dijk');assert.equal(snapshot.possession.source,'native possession marker');
  assert.equal(await page.locator('[data-possession-label] text').textContent(),'van Dijk');
  await page.evaluate(()=>{document.querySelector('#match-v2-p2').removeAttribute('data-in-possession');document.querySelector('#source').setAttribute('data-possession-player-id','match-v2-p2');});
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession.source,'native possession identity');
  console.log('PASS: label switches to receiving player and respects native possession markers/identity');
  await page.evaluate(()=>{document.querySelector('#source').removeAttribute('data-possession-player-id');document.querySelector('#match-v2-puck').style.transform='translate(50px,30px)';});
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession,null);assert.equal(await page.locator('[data-possession-label]').getAttribute('visibility'),'hidden');
  await page.evaluate(()=>{document.querySelector('#match-v2-puck').style.transform='translate(20px,30px)';document.querySelector('#match-v2-p2').setAttribute('transform','translate(20.3 30)');});
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession,null);
  await page.evaluate(()=>{
    document.querySelector('#match-v2-p2').setAttribute('transform','translate(80 30)');
    document.querySelector('#match-v2-puck').innerHTML='<circle cy="-2" r=".6" fill="white"/>';
    const shadow=document.createElementNS('http://www.w3.org/2000/svg','g');shadow.id='ball-shadow';shadow.setAttribute('transform','translate(20 30)');shadow.innerHTML='<ellipse rx="1" ry=".4"/>';document.querySelector('#source').append(shadow);tracker.scan(performance.now());
  });
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession,null);
  console.log('PASS: no proximity label on loose balls, contested possession or aerial passes');
  await page.evaluate(()=>{
    document.querySelector('#ball-shadow').remove();document.querySelector('#match-v2-puck circle').removeAttribute('cy');
    const p=document.querySelector('#match-v2-p1');p.removeAttribute('data-last-name');p.setAttribute('data-player-id','exact-identity');
    document.querySelector('#lineup').innerHTML='<div data-player-id="exact-identity"><a href="/players/exact-identity">Alex de la Cruz</a></div>';info.reset();tracker.scan(performance.now());
  });
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession.surname,'de la Cruz');assert.equal(snapshot.possession.nameSource,'matched native player identity');
  await page.evaluate(()=>{document.querySelector('#match-v2-p1').removeAttribute('data-player-id');info.reset();});
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession.surname,'');assert.equal(await page.locator('[data-possession-label]').getAttribute('visibility'),'hidden');
  console.log('PASS: lineup names require matching player identity; missing names and jersey initials are never invented');
  await page.evaluate(()=>{document.querySelector('#match-v2-p1').insertAdjacentHTML('beforeend','<text class="player-name">J. O’Neil</text>');info.reset();});
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession.surname,'O’Neil');
  for(const zoom of [1,1.75,2.5]) {
    await page.evaluate(zoom=>{camera.setZoom(zoom);sample();},zoom);
    assert.ok(Math.abs((await page.locator('[data-possession-label] rect').boundingBox()).height-21)<.1,'Surname badge maintains readable screen size across zoom levels');
  }
  await page.setViewportSize({width:600,height:900});
  await page.evaluate(()=>{scene.svg.style.width='600px';sample();});
  assert.ok(Math.abs((await page.locator('[data-possession-label] rect').boundingBox()).height-21)<.1);
  console.log('PASS: visible native surname labels and readable 21-pixel badge across camera views and resizing');
  await page.evaluate(()=>{
    document.querySelector('#match-v2-p1 .player-name').remove();
    const label=document.createElementNS('http://www.w3.org/2000/svg','text');label.id='floating-native-name';label.setAttribute('x','20');label.setAttribute('y','33');label.setAttribute('font-size','1');label.setAttribute('text-anchor','middle');label.textContent='Oscar Hansen';document.querySelector('#source').append(label);info.reset();
  });
  await page.evaluate(()=>document.querySelector('#match-v2-puck').style.transform='translate(50px,30px)');
  snapshot=await page.evaluate(()=>sample());assert.equal(snapshot.possession.surname,'Hansen');assert.equal(snapshot.possession.nameSource,'rendered native name label');assert.equal(snapshot.possession.source,'native possession name label');
  await page.evaluate(()=>document.querySelector('#match-v2-puck').style.transform='translate(20px,30px)');
  await page.evaluate(()=>{document.querySelector('#floating-native-name').remove();document.querySelector('#match-v2-p1').setAttribute('data-last-name','Hansen');info.reset();});
  console.log('PASS: native SVG name below the player identifies the carrier directly; overlay badge appears above');

  await page.evaluate(()=>{scene.svg.style.width='1600px';});await page.setViewportSize({width:1600,height:1000});
  await page.evaluate(()=>{
    document.querySelector('#match-v2-p1').style.transform='translate(60px,40px)';document.querySelector('#match-v2-puck').style.transition='transform 600ms linear';document.querySelector('#match-v2-puck').style.transform='translate(60px,40px)';
  });
  const phases=[];
  for(let i=0;i<7;i++){await page.waitForTimeout(50);phases.push(await page.evaluate(()=>{const snapshot=sample(),node=renderer.players.get('match-v2-p1'),a=node.transform.baseVal.consolidate().matrix,b=scene.ball.transform.baseVal.consolidate().matrix;return {pose:node.dataset.pose,leg:node.querySelector('[data-leg]').getAttribute('transform'),sync:Math.hypot(a.e-b.e,a.f-b.f)};}));}
  assert.ok(phases.some(p=>p.pose==='running'));assert.ok(new Set(phases.map(p=>p.leg)).size>2);
  // The two native transitions were started from identical coordinates.
  assert.ok(phases.every(p=>p.sync<.1),'Sprite gait must not displace player ground anchors from the ball');
  await page.waitForTimeout(350);await page.evaluate(()=>sample());await page.waitForTimeout(180);
  await page.evaluate(()=>sample());assert.equal(await page.locator('[data-player="match-v2-p1"]').getAttribute('data-pose'),'standing');
  await page.screenshot({path:__dirname+'/players-desktop.png'});
  console.log('PASS: gait follows actual rendered travel, ground anchors remain synchronized and stopped players stand still');
  await page.evaluate(()=>{const old=document.querySelector('#source');old.replaceWith(old.cloneNode(true));document.querySelector('#match-v2-p1').removeAttribute('data-last-name');info.reset();sample();});
  assert.equal(await page.locator('[data-possession-label]').getAttribute('visibility'),'hidden');
  await page.evaluate(()=>{renderer.clear();});assert.equal(await page.locator('[data-possession-label]').getAttribute('visibility'),'hidden');
  assert.deepEqual(errors,[]);await browser.close();
  console.log('PASS: source replacement/reset clears stale names and possession labels');
})().catch(error=>{console.error(error);process.exit(1);});

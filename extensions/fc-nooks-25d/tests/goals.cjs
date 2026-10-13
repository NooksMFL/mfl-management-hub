const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),headless:true,args:['--no-sandbox']});
  const page=await browser.newPage({viewport:{width:1500,height:1000}});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.setContent('<style>body{margin:0}#native{width:900px;height:600px}.puck{transition:transform 600ms linear}</style><header>29:42 IP 0-0 AVL</header><svg id="native" viewBox="-2 -2 109 72"><rect x="-2" y="-2" width="109" height="72" fill="#253b31"/><g id="field"><rect id="playing-field" width="105" height="68" fill="#378347"/><path d="M0 0H105V68H0Z" fill="none" stroke="white"/><g id="match-v2-p1" transform="translate(0 34)"><circle r="1.2"/></g><g id="match-v2-puck" class="puck" style="transform:translate(0px,34px)"><circle r=".6" fill="white"/></g></g></svg>');
  await page.evaluate(()=>{globalThis.chrome={runtime:{getURL:name=>'about:blank'}};});
  for(const file of ['tracking.js','scoreboard.js','stadiums.js','scene.js','camera.js','sprites.js','renderer.js'])await page.addScriptTag({content:fs.readFileSync(root+'/'+file,'utf8')});
  await page.evaluate(()=>{window.tracker=new FCN25D.Tracker();window.scene=FCN25D.buildScene();window.renderer=new FCN25D.Renderer(scene);window.camera=new FCN25D.ViewportCamera(scene);document.body.append(scene.svg);});
  async function sample(x){return page.evaluate(x=>{
    const ball=document.querySelector('#match-v2-puck');ball.style.transition='none';ball.style.transform=`translate(${x}px,34px)`;
    const snapshot=tracker.sample();renderer.render(snapshot);camera.update(snapshot);
    return snapshot;
  },x);}
  let snapshot=await sample(0);
  assert.ok(Math.abs(snapshot.ball.u)<.00001,'Native x=0 must land on the left goal line, not two metres inside the pitch');
  assert.ok(Math.abs(snapshot.players[0].u)<.00001);
  assert.equal(snapshot.bounds.w,105);assert.equal(snapshot.bounds.h,68);
  for(const x of [105,-1,106,5,100]) {
    snapshot=await sample(x);assert.ok(snapshot.ball && Math.abs(snapshot.ball.u-x/105)<.00001,`Native x=${x} must preserve its position relative to the goal line`);
  }
  console.log('PASS: unmarked pitch geometry overrides SVG padding; both goal lines, behind-goal and in-field positions map correctly');
  await page.evaluate(()=>{document.querySelector('#native').setAttribute('viewBox','10 10 130 90');document.querySelector('#field').setAttribute('transform','translate(12 14)');tracker.scan(performance.now());});
  snapshot=await sample(0);assert.ok(Math.abs(snapshot.ball.u)<.00001);assert.equal(snapshot.bounds.x,12);assert.equal(snapshot.bounds.y,14);
  snapshot=await sample(105);assert.ok(Math.abs(snapshot.ball.u-1)<.00001);
  console.log('PASS: translated source pitch and offset viewBox retain real goal-line coordinates');
  // Dynamic ball movement still reads rendered transforms, not inline targets.
  await sample(0);
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  await page.evaluate(()=>{const ball=document.querySelector('#match-v2-puck');ball.style.transition='transform 600ms linear';ball.style.transform='translate(105px,34px)';});
  const points=[];
  for(let i=0;i<6;i++){await page.waitForTimeout(55);points.push(await page.evaluate(()=>tracker.sample().ball.u));}
  assert.ok(points.every(u=>u>0 && u<1));assert.ok(points[5]>points[0]);
  console.log('PASS: corrected pitch calibration preserves intermediate rendered motion');
  await page.waitForTimeout(350);
  for(const id of await page.evaluate(()=>Object.keys(FCN25D.stadiums)))for(const zoom of [1,1.75,2.5])for(const side of [0,1]) {
    const result=await page.evaluate(({id,zoom,side})=>{
      scene.setStadium(id);camera.setZoom(zoom);
      const ball=document.querySelector('#match-v2-puck');ball.style.transition='none';ball.style.transform=`translate(${side*105}px,34px)`;
      const snapshot=tracker.sample();renderer.render(snapshot);camera.update(snapshot);
      const expected=scene.project(side,.5),actual=scene.ball.transform.baseVal.consolidate().matrix;
      const front=scene.svg.querySelectorAll('[data-goals] path')[side*4+3],numbers=front.getAttribute('d').match(/-?\d+(?:\.\d+)?/g).map(Number);
      const [ax,ay,,,,,bx,by]=numbers;
      const distance=Math.abs((by-ay)*actual.e-(bx-ax)*actual.f+bx*ay-by*ax)/Math.hypot(by-ay,bx-ax);
      return {point:Math.hypot(expected[0]-actual.e,expected[1]-actual.f),distance};
    },{id,zoom,side});
    assert.ok(result.point<.001 && result.distance<.002,`${id}, ${zoom}×, goal ${side}: ball must coincide with actual goal mouth`);
  }
  console.log('PASS: native goal-line ball coincides with netted goal mouth in all eleven stadiums and three camera views');
  await sample(5);
  await page.evaluate(()=>document.querySelector('header').textContent='30:00 IP 1-0 AVL');
  snapshot=await page.evaluate(()=>tracker.sample());assert.ok(Math.abs(snapshot.ball.u-5/105)<.00001);assert.equal(await page.evaluate(()=>FCN25D.readScoreboard().score),'1 – 0');
  console.log('PASS: changing score never fabricates a ball position or snaps a reset ball into the net');
  await page.evaluate(()=>{
    const ball=document.querySelector('#match-v2-puck'),shadow=document.createElementNS('http://www.w3.org/2000/svg','g');
    shadow.id='ball-shadow';shadow.innerHTML='<ellipse rx="1" ry=".4"/>';ball.parentElement.append(shadow);ball.querySelector('circle').setAttribute('cy','-1');tracker.scan(performance.now());
  });
  for(const side of [0,1]) {
    const result=await page.evaluate(side=>{
      const x=side?106:-1;
      document.querySelector('#match-v2-puck').style.transform=`translate(${x}px,34px)`;
      document.querySelector('#ball-shadow').setAttribute('transform',`translate(${x} 34)`);
      const snapshot=tracker.sample();renderer.render(snapshot);camera.update(snapshot);
      return snapshot;
    },side);
    assert.equal(result.ball.flightMode,'rendered ball/shadow separation');
    assert.ok(Math.abs(result.ball.u-(side?106:-1)/105)<.00001);
    assert.ok(Math.abs(result.ball.heightU-1/105)<.00001);
    assert.ok(result.ball.source.ball.includes('puck') && result.ball.source.shadow.includes('ball-shadow'));
  }
  console.log('PASS: airborne ball behind either goal retains correct ground position, flight height and diagnostic source anchors');
  // Decorative and hidden copies must not define the playing surface.
  await page.evaluate(()=>{
    document.querySelector('#playing-field').remove();
    document.querySelector('#native').insertAdjacentHTML('afterbegin','<defs><rect width="105" height="68" x="500" y="500"/></defs><g style="display:none"><rect width="105" height="68" x="300" y="300"/></g>');
    tracker.scan(performance.now());
  });
  let bounds=await page.evaluate(()=>tracker.sample().bounds);assert.equal(bounds.x,12);assert.equal(bounds.y,14);assert.equal(bounds.w,105);
  await page.evaluate(()=>{const line=tracker.boundary.element;line.replaceWith(line.cloneNode(true));});
  bounds=await page.evaluate(()=>tracker.sample().bounds);assert.equal(bounds.x,12);assert.equal(bounds.w,105);
  console.log('PASS: unmarked outline detection ignores hidden/defs copies and reconnects after boundary replacement');

  assert.deepEqual(errors,[]);await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});

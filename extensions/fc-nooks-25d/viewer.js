(() => {
  'use strict';
  const api = globalThis.FCN25D;
  if (api.started) return;
  api.started = true;
  const tracker = new api.Tracker(), scene = api.buildScene(), renderer = new api.Renderer(scene);
  const scoreboard=api.scoreboard, camera=new api.ViewportCamera(scene);
  const host = document.createElement('div'); host.dataset.fcn25d=''; host.id='fcn25d-host';
  // Shadow DOM shields the extension from MFL styles and vice versa.
  const shadow=host.attachShadow({mode:'open'});
  const styles=document.createElement('link'); styles.rel='stylesheet'; styles.href=chrome.runtime.getURL('viewer.css');
  const toggle=document.createElement('button'); toggle.id='fcn25d-toggle'; toggle.type='button'; toggle.textContent='FC Nooks · 2.5D'; toggle.setAttribute('aria-expanded','false');
  const view=document.createElement('section'); view.id='fcn25d-view'; view.hidden=true; view.setAttribute('role','dialog'); view.setAttribute('aria-label','FC Nooks stadium match view');
  view.innerHTML='<header><div><span class="eyebrow">FC NOOKS</span><h1>Under the lights</h1></div><div class="tools"><label class="stadium-control">Stadium <select id="fcn-stadium" aria-label="Stadium"></select></label><label class="stadium-control">Camera <select id="fcn-camera" aria-label="Camera distance"></select></label><span id="fcn-minty-controls" hidden><button id="fcn-minty-photo" type="button">Choose Minty face</button><input id="fcn-minty-file" type="file" accept="image/png,image/jpeg,image/webp" hidden><span id="fcn-minty-message">Choose the original photo once</span></span><button id="fcn-select" type="button">Select ball</button><button id="fcn-select-scoreboard" type="button">Select scoreboard</button><button id="fcn-diagnostics" type="button">Diagnostics</button><button id="fcn-close" type="button" aria-label="Close stadium view">Close ✕</button></div></header><div class="broadcast" aria-live="polite"><span id="fcn-home">HOME</span><strong id="fcn-score">—</strong><span id="fcn-away">AWAY</span><small id="fcn-clock">AWAITING MFL</small></div><div id="fcn-stage"></div><footer><div class="footer-status"><span id="fcn-status">Waiting for MFL pitch</span><button id="fcn-select-shadow" type="button" title="Choose the ball’s ground shadow for flight tracking">Set ball shadow</button></div><span>VIEW ONLY · Alt+Shift+M</span></footer><pre id="fcn-diagnostic-output" hidden></pre>';
  const pickNotice=document.createElement('div');pickNotice.id='fcn-pick-notice';pickNotice.hidden=true;pickNotice.setAttribute('role','status');
  pickNotice.innerHTML='<span></span><button type="button">Cancel</button>';
  view.querySelector('#fcn-stage').append(scene.svg); shadow.append(styles,toggle,view,pickNotice);
  const status=view.querySelector('#fcn-status'), output=view.querySelector('pre');
  const board={ home:view.querySelector('#fcn-home'), away:view.querySelector('#fcn-away'), score:view.querySelector('#fcn-score'), clock:view.querySelector('#fcn-clock') };
  let open=false, raf=0, lastStatus=-Infinity, lastPath=location.href, picking=false, pickTimer=0, lastSnapshot=null, lastFocus=null, failures=0;
  let scoreData=api.emptyScoreboard(),scoreError='',nativeTop=-1;
  const stadiumSelect=view.querySelector('#fcn-stadium');
  for(const [id,stadium] of Object.entries(api.stadiums)) {
    const option=document.createElement('option');option.value=id;option.textContent=stadium.name;stadiumSelect.append(option);
  }
  let stadiumRevision=0,portraitRevision=0,cameraRevision=0,preferenceError='';
  const cameraSelect=view.querySelector('#fcn-camera');
  for(const option of api.cameraViews) {
    const el=document.createElement('option');el.value=String(option.zoom);el.textContent=option.name;cameraSelect.append(el);
  }
  function chooseCamera(zoom,persist=true) {
    if(!camera.setZoom(zoom))return;
    cameraRevision++;cameraSelect.value=String(zoom);camera.update(lastSnapshot);
    if(persist) {
      try {chrome.storage.local.set({cameraZoom:zoom},()=>{if(chrome.runtime.lastError)preferenceError='Camera choice could not be saved';});}
      catch(_){preferenceError='Camera choice could not be saved';}
    }
  }
  chooseCamera(1.75,false);
  cameraSelect.addEventListener('change',()=>chooseCamera(Number(cameraSelect.value)));
  const initialCameraRevision=cameraRevision;
  const mintyControls=view.querySelector('#fcn-minty-controls'),mintyMessage=view.querySelector('#fcn-minty-message');
  function chooseStadium(id,persist=true) {
    if(!api.isStadium(id))return;
    stadiumRevision++;scene.setStadium(id);camera.update(lastSnapshot);mintyControls.hidden=id!=='minty-stadium';stadiumSelect.value=id;view.dataset.stadium=id;
    view.querySelector('.eyebrow').textContent='FC NOOKS / '+api.stadiums[id].label;
    if(persist) {
      try {
        chrome.storage.local.set({stadiumId:id},()=>{if(chrome.runtime.lastError)preferenceError='Stadium choice could not be saved';});
      } catch(_) { preferenceError='Stadium choice could not be saved'; }
    }
  }
  chooseStadium(api.defaultStadium,false);
  stadiumSelect.addEventListener('change',()=>chooseStadium(stadiumSelect.value));
  const preferenceRevision=stadiumRevision;
  try {
    chrome.storage.local.get(['stadiumId','mintyFace','cameraZoom'],saved=>{
      if(chrome.runtime.lastError){preferenceError='Saved stadium choice could not be read';return;}
      if(!portraitRevision && api.isPortrait(saved?.mintyFace)){scene.setPortrait(saved.mintyFace);mintyMessage.textContent='Face saved on this browser';}
      if(cameraRevision===initialCameraRevision && api.isCameraZoom(saved?.cameraZoom))chooseCamera(saved.cameraZoom,false);
      // A late storage response must not undo a choice made by the user.
      if(stadiumRevision===preferenceRevision && api.isStadium(saved?.stadiumId))chooseStadium(saved.stadiumId,false);
    });
  } catch(_) { preferenceError='Saved stadium choice could not be read'; }
  const photoInput=view.querySelector('#fcn-minty-file');
  view.querySelector('#fcn-minty-photo').addEventListener('click',()=>photoInput.click());
  photoInput.addEventListener('change',async()=>{
    const file=photoInput.files[0];photoInput.value='';if(!file)return;
    if(!['image/png','image/jpeg','image/webp'].includes(file.type) || file.size>1048576){mintyMessage.textContent='Use a PNG/JPG/WebP under 1 MB';return;}
    const revision=++portraitRevision;
    try {
      const url=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(new Error('Photo could not be read'));reader.readAsDataURL(file);});
      if(revision!==portraitRevision || !api.isPortrait(url))return;
      // Decode before replacing a working face. The file never leaves the browser.
      const check=new Image();check.src=url;await check.decode();
      if(revision!==portraitRevision)return;
      scene.setPortrait(url);mintyMessage.textContent='Face applied to players, crowd and banner';
      try {chrome.storage.local.set({mintyFace:url},()=>{if(chrome.runtime.lastError)mintyMessage.textContent='Face applied; could not save it';});}
      catch(_){mintyMessage.textContent='Face applied for this tab';}
    } catch(error){mintyMessage.textContent=error.message || 'Photo could not be loaded';}
  });
  function attach() { if (document.body && !host.isConnected) document.body.append(host); }
  function updateBoard(data) { Object.keys(board).forEach(key=>{if(board[key].textContent!==data[key])board[key].textContent=data[key];}); scene.updateScore(data); }
  function syncScoreboard() {
    if(!open)return;
    try {
      scoreData=scoreboard.read();updateBoard(scoreData);scoreError='';
      const inset=scoreboard.nativeInset();
      if(inset!==nativeTop){nativeTop=inset;view.style.setProperty('--fcn-native-top',inset+'px');}
    } catch(error) {
      scoreError=String(error.message || error).slice(0,160);
      scoreData=api.emptyScoreboard();updateBoard(scoreData);
      // Score parsing errors must never clear player tracks or stop motion.
    }
  }
  function reset() { tracker.reset(); scoreboard.reset(); renderer.clear(); camera.reset(); lastSnapshot=null; lastStatus=-Infinity; scoreData=api.emptyScoreboard();updateBoard(scoreData); }
  function available() { return /\/matches\/[^/]+/.test(location.pathname) || !!document.querySelector('svg [id^="match-v2-p"]'); }
  function stopPicking() { picking=false; clearTimeout(pickTimer);pickNotice.hidden=true;document.removeEventListener('click',pick,true); }
  function setOpen(value) {
    if (value && !available()) return;
    stopPicking(); open=value;
    view.hidden=!open; toggle.hidden=!available(); toggle.textContent=open?'Close 2.5D':'FC Nooks · 2.5D'; toggle.setAttribute('aria-expanded',String(open));
    cancelAnimationFrame(raf); raf=0;
    if (open) { lastFocus=document.activeElement; attach();lastStatus=-Infinity;syncScoreboard();frame();view.querySelector('#fcn-close').focus(); }
    else if (lastFocus?.isConnected) lastFocus.focus();
  }
  function frame() {
    if (!open) return;
    try {
      const now=performance.now();
      // Read both ball and players BEFORE any overlay writes.
      const snapshot=tracker.sample(now); lastSnapshot=snapshot;
      renderer.render(snapshot);camera.update(snapshot);
      if (now-lastStatus>600) { status.textContent=`${snapshot.players.length} players · ${snapshot.diagnostic}${scoreData.found?'':' · Select scoreboard if scores are missing'}${scene.svg.dataset.assetState==='failed'?' · stadium image missing':''}`; lastStatus=now; }
      failures=0;
    } catch (error) {
      status.textContent='Reconnecting to MFL pitch…';
      if (!failures++) console.warn('[FC Nooks]',error);
      tracker.reset(); renderer.clear();
    }
    raf=requestAnimationFrame(frame);
  }
  function reconcile() {
    attach();
    if (lastPath!==location.href) { lastPath=location.href; stopPicking(); reset(); }
    const match=available(); toggle.hidden=!match || picking;
    if (!match && open) setOpen(false);
  }
  function pick(event) {
    if (event.composedPath().includes(host)) return;
    event.preventDefault(); event.stopImmediatePropagation();
    const kind=picking;
    if(kind!=='scoreboard')tracker.sample(performance.now());
    const valid=kind==='scoreboard'?scoreboard.select(event.target):kind==='shadow'?tracker.selectShadow(event.target,event.clientX,event.clientY):tracker.select(event.target);
    stopPicking(); setOpen(true);
    status.textContent=valid?(kind==='scoreboard'?'Following the selected MFL scoreboard':kind==='shadow'?'Following the selected ball shadow for flight height':'Selected graphic; checking ball coordinates'):(kind==='scoreboard'?'Could not read that scoreboard; click the score/clock bar':'Select the ball graphic inside the MFL pitch.');
  }
  function startPicking(kind) {
    setOpen(false); picking=kind; toggle.hidden=true;pickNotice.hidden=false;
    pickNotice.querySelector('span').textContent=kind==='scoreboard'?'Click the score/clock bar on the original MFL view. Escape cancels.':kind==='shadow'?'Click the ball’s ground shadow on the original pitch. Escape cancels.':'Click the ball on the original MFL pitch. Escape cancels.';
    document.addEventListener('click',pick,true);
    pickTimer=setTimeout(()=>{stopPicking();setOpen(true);},15000);
  }
  view.querySelector('#fcn-select').addEventListener('click',()=>startPicking('ball'));
  view.querySelector('#fcn-select-scoreboard').addEventListener('click',()=>startPicking('scoreboard'));
  view.querySelector('#fcn-select-shadow').addEventListener('click',()=>startPicking('shadow'));
  pickNotice.querySelector('button').addEventListener('click',()=>{stopPicking();setOpen(true);});
  view.querySelector('#fcn-diagnostics').addEventListener('click',()=>{
    output.hidden=!output.hidden;
    output.textContent=JSON.stringify({version:'1.12.0',camera:camera.diagnostics(),stadium:scene.stadiumId,stadiumImage:scene.svg.dataset.assetState,preferenceError,source:tracker.root?.getAttribute('viewBox'),players:lastSnapshot?.players.length,ball:lastSnapshot?.ball,candidates:tracker.balls.map(el=>({tag:el.tagName,id:el.id})),shadows:tracker.shadows.map(el=>({tag:el.tagName,id:el.id})),bounds:lastSnapshot?.bounds,scoreboard:scoreboard.diagnostics(),scoreError},null,2);
  });
  toggle.addEventListener('click',()=>setOpen(!open));
  view.querySelector('#fcn-close').addEventListener('click',()=>setOpen(false));
  document.addEventListener('keydown',event=>{
    if (event.altKey && event.shiftKey && event.code==='KeyM') { event.preventDefault(); setOpen(!open); }
    if (event.key==='Escape' && (open || picking)) { stopPicking(); setOpen(false); reconcile(); }
  });
  // Observe document AND body replacement/removal; do not observe our own frames.
  const observer=new MutationObserver(()=>{ if (!host.isConnected) attach(); });
  observer.observe(document.documentElement,{childList:true,subtree:true});
  window.addEventListener('popstate',reconcile);
  window.addEventListener('hashchange',reconcile);
  document.addEventListener('visibilitychange',()=>{cancelAnimationFrame(raf);if(open && !document.hidden) frame();});
  // This refreshes extracted DOM values only; it never invents match time and
  // is not a player/ball animation clock.
  setInterval(syncScoreboard,100);
  setInterval(reconcile,500); reconcile();
})();

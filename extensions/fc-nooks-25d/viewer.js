(() => {
  'use strict';
  const api = globalThis.FCN25D;
  if (api.started) return;
  api.started = true;
  const tracker = new api.Tracker(), scene = api.buildScene(), renderer = new api.Renderer(scene);
  const host = document.createElement('div'); host.dataset.fcn25d=''; host.id='fcn25d-host';
  // Shadow DOM shields the extension from MFL styles and vice versa.
  const shadow=host.attachShadow({mode:'open'});
  const styles=document.createElement('link'); styles.rel='stylesheet'; styles.href=chrome.runtime.getURL('viewer.css');
  const toggle=document.createElement('button'); toggle.id='fcn25d-toggle'; toggle.type='button'; toggle.textContent='FC Nooks · 2.5D'; toggle.setAttribute('aria-expanded','false');
  const view=document.createElement('section'); view.id='fcn25d-view'; view.hidden=true; view.setAttribute('role','dialog'); view.setAttribute('aria-label','FC Nooks stadium match view');
  view.innerHTML='<header><div><span class="eyebrow">FC NOOKS / IRONWOOD LANE</span><h1>Under the lights</h1></div><div class="tools"><button id="fcn-select" type="button">Select ball</button><button id="fcn-diagnostics" type="button">Diagnostics</button><button id="fcn-close" type="button" aria-label="Close stadium view">Close ✕</button></div></header><div class="broadcast" aria-live="polite"><span id="fcn-home">HOME</span><strong id="fcn-score">—</strong><span id="fcn-away">AWAY</span><small id="fcn-clock">AWAITING MFL</small></div><div id="fcn-stage"></div><footer><span id="fcn-status">Waiting for MFL pitch</span><span>VIEW ONLY · Alt+Shift+M</span></footer><pre id="fcn-diagnostic-output" hidden></pre>';
  view.querySelector('#fcn-stage').append(scene.svg); shadow.append(styles,toggle,view);
  const status=view.querySelector('#fcn-status'), output=view.querySelector('pre');
  const board={ home:view.querySelector('#fcn-home'), away:view.querySelector('#fcn-away'), score:view.querySelector('#fcn-score'), clock:view.querySelector('#fcn-clock') };
  let open=false, raf=0, lastBoard=-Infinity, lastStatus=-Infinity, lastPath=location.href, picking=false, pickTimer=0, lastSnapshot=null, lastFocus=null, failures=0;
  function attach() { if (document.body && !host.isConnected) document.body.append(host); }
  function updateBoard(data) { Object.keys(board).forEach(key=>{if(board[key].textContent!==data[key])board[key].textContent=data[key];}); scene.updateScore(data); }
  function reset() { tracker.reset(); renderer.clear(); lastSnapshot=null; lastBoard=-Infinity; lastStatus=-Infinity; updateBoard(api.emptyScoreboard()); }
  function available() { return /\/matches\/[^/]+/.test(location.pathname) || !!document.querySelector('svg [id^="match-v2-p"]'); }
  function stopPicking() { picking=false; clearTimeout(pickTimer); document.removeEventListener('click',pick,true); }
  function setOpen(value) {
    if (value && !available()) return;
    stopPicking(); open=value;
    view.hidden=!open; toggle.hidden=!available(); toggle.textContent=open?'Close 2.5D':'FC Nooks · 2.5D'; toggle.setAttribute('aria-expanded',String(open));
    cancelAnimationFrame(raf); raf=0;
    if (open) { lastFocus=document.activeElement; attach(); lastBoard=-Infinity; lastStatus=-Infinity; frame(); view.querySelector('#fcn-close').focus(); }
    else if (lastFocus?.isConnected) lastFocus.focus();
  }
  function frame() {
    if (!open) return;
    try {
      const now=performance.now();
      // Read both ball and players BEFORE any overlay writes.
      const snapshot=tracker.sample(now); lastSnapshot=snapshot;
      renderer.render(snapshot);
      if (now-lastBoard>250) { updateBoard(api.readScoreboard()); lastBoard=now; }
      if (now-lastStatus>600) { status.textContent=`${snapshot.players.length} players · ${snapshot.diagnostic} · ${snapshot.bounds.source}${scene.svg.dataset.assetState==='failed'?' · stadium image missing':''}`; lastStatus=now; }
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
    const valid=tracker.select(event.target);
    stopPicking(); setOpen(true);
    status.textContent=valid?'Selected graphic; checking ball coordinates':'Select the ball graphic inside the MFL pitch.';
  }
  view.querySelector('#fcn-select').addEventListener('click',()=>{
    setOpen(false); picking=true; toggle.hidden=true;
    document.addEventListener('click',pick,true);
    pickTimer=setTimeout(()=>{stopPicking();setOpen(true);},15000);
  });
  view.querySelector('#fcn-diagnostics').addEventListener('click',()=>{
    output.hidden=!output.hidden;
    output.textContent=JSON.stringify({version:'1.8.0',source:tracker.root?.getAttribute('viewBox'),players:lastSnapshot?.players.length,ballTracked:!!lastSnapshot?.ball,candidates:tracker.balls.map(el=>({tag:el.tagName,id:el.id})),bounds:lastSnapshot?.bounds,scoreboard:api.readScoreboard()},null,2);
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
  setInterval(reconcile,500); reconcile();
})();

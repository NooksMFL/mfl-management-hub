(() => {
  'use strict';
  const api=globalThis.FCN25D;
  const empty=()=>({home:'HOME',away:'AWAY',score:'—',clock:'AWAITING MFL',found:false});
  const named='header,nav,[role="banner"],[class*="score" i],[class*="header" i],[class*="clock" i],[class*="timer" i],[id*="score" i],[data-testid*="score" i],[data-testid*="clock" i],[data-testid*="timer" i]';
  const clockPattern=/(?:\b\d{1,3}\s*:\s*[0-5]\d(?:\s*\+\s*\d{1,2}(?::[0-5]\d)?)?|\b\d{1,3}(?:\s*\+\s*\d{1,2})?\s*['′]|\b(?:HALF\s*TIME|FULL\s*TIME|HT|FT)\b)/i;
  const normalize=value=>String(value || '').replace(/[\u200b-\u200d\ufeff]/g,'').replace(/[–—−]/g,'-').replace(/\s*:\s*/g,':').replace(/\s+/g,' ').trim();
  const name=value=>/^[\p{L}][\p{L}\p{N} .&'’-]{0,44}$/u.test(value) && !/^(?:play|pause|score|clock|home|away|highlights|extended highlights|half time|full time|HT|FT)$/i.test(value);
  const external=el=>el && !el.closest('[data-fcn25d],script,style,noscript,template');
  function visible(el) {
    if(!external(el) || el.closest('[hidden],[aria-hidden="true"]'))return false;
    const s=getComputedStyle(el);
    return s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity)!==0 && el.getClientRects().length>0;
  }
  function textParts(root) {
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),parts=[];
    let node,count=0;
    while((node=walker.nextNode()) && count++<180) {
      const text=normalize(node.nodeValue),parent=node.parentElement;
      if(text && visible(parent) && !parent.closest('svg title,svg desc,.sr-only,[class*="sr-only"]'))parts.push(text);
    }
    return parts;
  }
  function parse(parts) {
    const joined=normalize(parts.join(' '));
    if(!joined || joined.length>650)return empty();
    const clockMatch=joined.match(clockPattern);
    const clock=clockMatch?normalize(clockMatch[0]):'';
    // Text-node boundaries matter: React can render "IP", "0-0", "AVL"
    // without literal spaces, or put the two digits in separate elements.
    for(let i=0;i<parts.length;i++) {
      const pair=parts[i].match(/^(\d{1,2})\s*[-:]\s*(\d{1,2})$/);
      if(pair && !clockPattern.test(parts[i]) && name(parts[i-1] || '') && name(parts[i+1] || ''))
        return {home:parts[i-1],away:parts[i+1],score:`${pair[1]} – ${pair[2]}`,clock:clock || 'CLOCK UNAVAILABLE',found:true};
      if(name(parts[i] || '') && /^\d{1,2}$/.test(parts[i+1] || '')) {
        const separated=parts[i+2]==='-' && /^\d{1,2}$/.test(parts[i+3] || '');
        const awayIndex=separated?i+4:i+3,awayScore=parts[separated?i+3:i+2];
        if(/^\d{1,2}$/.test(awayScore || '') && name(parts[awayIndex] || '') && (separated || clock))
          return {home:parts[i],away:parts[awayIndex],score:`${parts[i+1]} – ${awayScore}`,clock:clock || 'CLOCK UNAVAILABLE',found:true};
      }
    }
    const withoutClock=normalize(joined.replace(new RegExp(clockPattern.source,'gi'),' '));
    // Unanchored, because the playback row also includes speed/menu controls.
    const spaced=withoutClock.match(/(?:^|\s)([A-Z][A-Z0-9]{0,7})\s+(\d{1,2})\s*[-:]\s*(\d{1,2})\s+([A-Z][A-Z0-9]{0,7})(?=\s|$)/);
    const compact=withoutClock.match(/(?:^|[^A-Z])([A-Z]{1,8})\s*(\d{1,2})\s*[-:]\s*(\d{1,2})\s*([A-Z]{1,8})(?=[^A-Z]|$)/);
    const m=spaced || compact;
    if(m)return {home:m[1],away:m[4],score:`${m[2]} – ${m[3]}`,clock:clock || 'CLOCK UNAVAILABLE',found:true};
    // Retain support for a plain full-name header, without swallowing controls.
    const full=withoutClock.match(/^([\p{L}][\p{L}\p{N} .&'’-]{0,44}?)\s+(\d{1,2})\s*-\s*(\d{1,2})\s+([\p{L}][\p{L}\p{N} .&'’-]{0,44})$/u);
    if(full)return {home:full[1],away:full[4],score:`${full[2]} – ${full[3]}`,clock:clock || 'CLOCK UNAVAILABLE',found:true};
    return empty();
  }
  function sample(root) {
    if(!root?.isConnected || !visible(root))return empty();
    if(normalize(root.textContent).length>1200)return empty();
    const parts=textParts(root),data=parse(parts);
    // Some layouts place clock and score in neighbouring wrappers. Read a
    // nearby small ancestor, never an unrelated clock elsewhere on the page.
    if(data.found && data.clock==='CLOCK UNAVAILABLE') {
      let parent=root.parentElement;
      for(let i=0;parent && parent!==document.body && i<3;i++,parent=parent.parentElement) {
        const p=textParts(parent),text=normalize(p.join(' '));
        if(text.length>650)break;
        const clock=text.match(clockPattern);
        if(clock){data.clock=normalize(clock[0]);break;}
      }
    }
    return data;
  }
  class ScoreboardReader {
    constructor(){this.reset();}
    reset(){this.root=null;this.manual=false;this.nextScan=0;this.changes=new WeakMap();this.scanLimited=false;this.lastData=empty();}
    candidates() {
      const roots=new Set();
      const add=el=>{
        for(let i=0;el && el!==document.body && el!==document.documentElement && i<5;i++,el=el.parentElement)
          if(external(el))roots.add(el);
      };
      [...document.querySelectorAll(named)].slice(0,200).forEach(add);
      // CSS-module/Tailwind headers often have no score/header selector at all.
      // Find short clock/score leaves once during discovery, not on every frame.
      const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
      let node,count=0;
      while((node=walker.nextNode()) && count++<6000) {
        const text=normalize(node.nodeValue);
        const numeric=/^\d{1,3}$/.test(text) && visible(node.parentElement) && node.parentElement.getBoundingClientRect().bottom<=180;
        if(text.length<100 && (clockPattern.test(text) || /^\d{1,2}\s*[-:]\s*\d{1,2}$/.test(text) || numeric))add(node.parentElement);
      }
      this.scanLimited=count>=6000;
      return [...roots].filter(visible);
    }
    rank(root,data,now,pitch) {
      const rect=root.getBoundingClientRect(),text=normalize(textParts(root).join(' '));
      let rank=data.clock!=='CLOCK UNAVAILABLE'?75:0;
      if(root.matches(named))rank+=12;
      if(rect.top>=-5 && rect.bottom<=180)rank+=40;
      if(pitch && rect.bottom<=pitch.top+70)rank+=20;
      if(rect.height>180)rank-=55;
      rank-=text.length/30;
      const previous=this.changes.get(root),signature=data.score+'|'+data.clock;
      const changed=previous && previous.signature!==signature;
      const lastChanged=changed?now:previous?.lastChanged || 0;
      this.changes.set(root,{signature,lastChanged});
      if(lastChanged && now-lastChanged<5000)rank+=25;
      return rank;
    }
    select(el) {
      let best=null,rank=-Infinity,parent=el;
      for(let i=0;parent && parent!==document.body && i<6;i++,parent=parent.parentElement) {
        const data=sample(parent);if(!data.found)continue;
        const value=this.rank(parent,data,performance.now(),null);
        if(value>rank){best=parent;rank=value;}
      }
      if(!best)return false;
      this.root=best;this.manual=true;this.nextScan=Infinity;return true;
    }
    read(now=performance.now()) {
      if(this.manual && !this.root?.isConnected){this.root=null;this.manual=false;this.nextScan=0;}
      let data=sample(this.root);
      // Responsive layouts can keep an old, hidden score row mounted.
      if(this.manual && !data.found){this.root=null;this.manual=false;this.nextScan=0;}
      if(!this.manual && (now>=this.nextScan || (this.root && !data.found))) {
        const pitch=document.querySelector('svg [id^="match-v2-p"]')?.closest('svg')?.getBoundingClientRect();
        let best=null,bestData=empty(),rank=-Infinity;
        for(const root of this.candidates()) {
          const candidate=sample(root);if(!candidate.found)continue;
          const value=this.rank(root,candidate,now,pitch);
          if(value>rank){best=root;bestData=candidate;rank=value;}
        }
        this.root=best;data=bestData;this.nextScan=now+1500;
      }
      this.lastData=data;return data;
    }
    nativeInset() {
      if(!this.root?.isConnected)return 0;
      const r=this.root.getBoundingClientRect();
      return r.top>=-5 && r.bottom<=180 && r.height<160?Math.max(0,Math.ceil(r.bottom+6)):0;
    }
    diagnostics() {
      return {mode:this.manual?'selected':'automatic',source:this.root?`${this.root.tagName.toLowerCase()}${this.root.id?'#'+this.root.id:''}`:'none',text:this.root?normalize(textParts(this.root).join(' ')).slice(0,200):'',scanLimited:this.scanLimited,values:this.lastData};
    }
  }
  api.ScoreboardReader=ScoreboardReader;
  api.scoreboard=new ScoreboardReader();
  api.readScoreboard=()=>api.scoreboard.read();
  api.emptyScoreboard=empty;
})();

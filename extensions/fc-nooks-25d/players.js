(() => {
  'use strict';
  const api=globalThis.FCN25D;
  const surnameAttributes=['data-surname','data-last-name','data-lastname','data-family-name'];
  const nameAttributes=['data-player-name','data-full-name','data-name'];
  const possessingAttributes=['data-in-possession','data-has-ball','data-possession','data-ball-carrier'];
  const visible=el=>{const s=getComputedStyle(el);return s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity)!==0 && el.getClientRects().length>0;};
  function clean(value) {
    const text=String(value || '').normalize('NFC').replace(/\s+/g,' ').trim()
      .replace(/^(?:player|footballer)\s*:?\s+/i,'').replace(/^#?\d{1,2}[.\s]+/,'')
      .split(/[|•]/)[0].replace(/\s*(?:#\d+|,?\s*(?:number|shirt|jersey)\s*\d+).*$/i,'').trim();
    return text.length<=80 && /^[\p{L}\p{M} .,’'’-]+$/u.test(text) && !/\b(?:player|home|away|goalkeeper|forward|midfielder|defender|captain|team|unknown|mfl|playmfl|null|undefined)\b/i.test(text)?text:'';
  }
  function surname(value,explicit=false) {
    const name=clean(value);if(!name)return '';
    if(explicit)return name;
    if(name.includes(','))return name.split(',')[0].trim();
    const words=name.split(' ').filter(Boolean);
    if(words.length===1)return words[0].length>=2 && !/^[A-Z]\.$/.test(words[0])?words[0]:'';
    let start=words.length-1;
    while(start>0 && /^(?:da|das|de|del|della|der|di|dos|du|la|le|van|von|ten|ter)$/i.test(words[start-1]))start--;
    return words.slice(start).join(' ');
  }
  const attr=(el,names)=>{for(const name of names){const value=el.getAttribute(name);if(value)return value;}return '';};
  function entityId(el) {
    const direct=el.getAttribute('data-player-id') || el.querySelector('[data-player-id]')?.getAttribute('data-player-id');
    if(direct)return direct;
    return el.closest('a[href*="/players/"]')?.getAttribute('href')?.match(/\/players\/([^/?#]+)/)?.[1] || '';
  }
  function readName(el,external) {
    const explicit=attr(el,surnameAttributes) || attr(el.querySelector?.('[data-surname],[data-last-name],[data-lastname],[data-family-name]') || el,surnameAttributes);
    if(explicit)return {surname:surname(explicit,true),source:'surname attribute'};
    const full=attr(el,nameAttributes) || attr(el.querySelector('[data-player-name],[data-full-name],[data-name]') || el,nameAttributes);
    if(full)return {surname:surname(full),source:'name attribute'};
    for(const ref of ['aria-labelledby','aria-describedby'])for(const id of (el.getAttribute(ref) || '').split(/\s+/)) {
      const target=id && document.getElementById(id),name=target && surname(target.textContent);
      if(name)return {surname:name,source:'linked native label'};
    }
    const title=el.querySelector('title')?.textContent || el.getAttribute('aria-label') || el.getAttribute('title');
    if(title && surname(title))return {surname:surname(title),source:'native title/accessible name'};
    const entity=entityId(el);
    if(entity && external.has(entity))return external.get(entity);
    if(external.has(el.id))return external.get(el.id);
    return {surname:'',source:'name unavailable'};
  }
  function visibleName(el,root,bounds,player) {
    for(const text of el.querySelectorAll('text')) {
      if(text===el.querySelector('text') && text.textContent.trim().length<=3)continue;
      const name=surname(text.textContent);
      if(name && visible(text)) {
        let below=false;
        try {
          const box=text.getBBox(),position=api.svgPosition(text,root,box.x+box.width/2,box.y+box.height/2);
          const dy=position?((position[1]-bounds.y)/bounds.h-player.v)*68:0;
          below=dy>.25 && dy<6;
        } catch(_) { /* static name metadata still remains usable */ }
        return {surname:name,source:'visible native player label',below};
      }
    }
    return null;
  }
  class PlayerInfo {
    constructor(){this.reset();}
    reset(){this.root=null;this.names=new WeakMap();this.nextNames=0;}
    enrich(snapshot,tracker,now=performance.now()) {
      if(tracker.root!==this.root){this.reset();this.root=tracker.root;}
      if(!this.root)return {...snapshot,possession:null};
      const byId=new Map(tracker.objects.map(el=>[el.id,el]));
      if(now>=this.nextNames || tracker.objects.some(el=>!this.names.has(el))) {
        const external=new Map();
        for(const el of [...document.querySelectorAll('[data-player-id],[data-player-ref],a[href*="/players/"]')].slice(0,200)) {
          if(tracker.objects.includes(el) || el.closest('[data-fcn25d]'))continue;
          const value=attr(el,surnameAttributes),full=attr(el,nameAttributes);
          const label=el.querySelector('[data-testid*="player-name"],.player-name,a[href*="/players/"]')?.textContent || (['a','text'].includes(el.tagName.toLowerCase())?el.textContent:'');
          const name=value?surname(value,true):surname(full || label);
          const id=el.getAttribute('data-player-id') || el.getAttribute('data-player-ref') || el.getAttribute('href')?.match(/\/players\/([^/?#]+)/)?.[1];
          if(id && name)external.set(id,{surname:name,source:'matched native player identity'});
        }
        for(const el of tracker.objects)this.names.set(el,readName(el,external));
        this.nextNames=now+500;
      }
      const labelled=new Map(),explicit=[];
      for(const player of snapshot.players) {
        const el=byId.get(player.id);if(!el)continue;
        const active=possessingAttributes.some(name=>/^(?:true|1|yes|ball)$/i.test(el.getAttribute(name) || '')) || /(?:^|\s)(?:has-ball|in-possession|ball-carrier)(?:\s|$)/i.test(el.getAttribute('class') || '');
        if(active)explicit.push(player);
        // A native surname shown only on the carrier is useful direct evidence.
        const label=visibleName(el,this.root,snapshot.bounds,player);if(label)labelled.set(player.id,label);
      }
      // Some native viewers draw names as separate SVG text beside the dots.
      // Match those rendered labels only when their position identifies one
      // player clearly; use the existing rendered-CTM helper, not target styles.
      for(const text of [...this.root.querySelectorAll('text')].slice(0,100)) {
        if(tracker.objects.some(el=>el.contains(text)) || tracker.balls.some(el=>el.contains(text)))continue;
        const raw=text.textContent.trim(),name=surname(raw);
        if(!name || raw.length<4 || !visible(text))continue;
        try {
          const box=text.getBBox(),position=api.svgPosition(text,this.root,box.x+box.width/2,box.y+box.height/2);
          if(!position)continue;
          const u=(position[0]-snapshot.bounds.x)/snapshot.bounds.w,v=(position[1]-snapshot.bounds.y)/snapshot.bounds.h;
          const matches=snapshot.players.map(player=>({player,dx:Math.abs((player.u-u)*105),dy:(player.v-v)*68}))
            .filter(match=>match.dx<2.5 && Math.abs(match.dy)>.25 && Math.abs(match.dy)<6)
            .map(match=>({...match,distance:Math.hypot(match.dx,match.dy)})).sort((a,b)=>a.distance-b.distance);
          if(matches[0] && (!matches[1] || matches[1].distance-matches[0].distance>.75))
            labelled.set(matches[0].player.id,{surname:name,source:'rendered native name label',below:matches[0].dy<0});
        } catch(_) { /* disconnected/hidden text is not a player identity */ }
      }
      let carrier=null,source='';
      if(explicit.length===1){carrier=explicit[0];source='native possession marker';}
      if(!carrier) {
        const selector='[data-possession-player-id],[data-ball-carrier-id],[data-owner-player-id]';
        const owner=this.root.matches(selector)?this.root:this.root.querySelector(selector);
        const id=owner && (owner.getAttribute('data-possession-player-id') || owner.getAttribute('data-ball-carrier-id') || owner.getAttribute('data-owner-player-id'));
        if(id)carrier=snapshot.players.find(p=>p.id===id || entityId(byId.get(p.id))===id) || null;
        if(carrier)source='native possession identity';
      }
      if(!carrier) {
        const below=[...labelled.entries()].filter(([,name])=>name.below);
        if(below.length===1) {
          carrier=snapshot.players.find(player=>player.id===below[0][0]);
          source='native possession name label';
        }
      }
      const ball=snapshot.ball;
      if(!carrier && ball && (ball.heightU || 0)*105<.75) {
        const nearest=snapshot.players.map(player=>({player,distance:Math.hypot((player.u-ball.u)*105,(player.v-ball.v)*68)})).sort((a,b)=>a.distance-b.distance);
        if(nearest[0]?.distance<=1.8 && (!nearest[1] || nearest[1].distance-nearest[0].distance>=.55)) {
          carrier=nearest[0].player;source='unambiguous ball proximity';
        }
      }
      const players=snapshot.players.map(player=>{
        const el=byId.get(player.id),name=labelled.get(player.id) || this.names.get(el) || {surname:'',source:'name unavailable'};
        return {...player,surname:name.surname,nameSource:name.source};
      });
      const named=carrier && players.find(p=>p.id===carrier.id);
      return {...snapshot,players,possession:named?{playerId:named.id,surname:named.surname,source,nameSource:named.nameSource}:null};
    }
  }
  api.PlayerInfo=PlayerInfo;
  api.playerSurname=surname;
})();

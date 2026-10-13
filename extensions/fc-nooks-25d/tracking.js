(() => {
  'use strict';
  const api = globalThis.FCN25D = globalThis.FCN25D || {};
  // Preserved from the uploaded viewer.js: rendered screen CTM -> root SVG.
  // Inline transform styles are future transition targets, not current positions.
  function svgPosition(el, root, localX = 0, localY = 0) {
    try {
      const m = el.getScreenCTM();
      const inv = root.getScreenCTM()?.inverse();
      if (!m || !inv) return null;
      const p = new DOMPoint(localX, localY).matrixTransform(m).matrixTransform(inv);
      return Number.isFinite(p.x) && Number.isFinite(p.y) ? [p.x, p.y] : null;
    } catch (_) { return null; }
  }
  const playerSelector = '[id^="match-v2-p"]';
  const isPlayer = el => /^match-v2-p\d+$/.test(el.id) && el.querySelector('circle');
  // "puck" also starts with match-v2-p; never classify that prefix as a player.
  const inPlayer = el => { for (let p=el;p;p=p.parentElement) if (isPlayer(p)) return true; return false; };
  const excluded = el => !!el.closest('[data-fcn25d]');
  function signature(el) {
    return [el.id, el.getAttribute('class'), el.getAttribute('href'), el.getAttribute('aria-label'), el.getAttribute('data-testid')].join(' ');
  }
  const isBall = el => /puck|football|soccer.?ball|(?:^|[^a-z])ball(?:$|[^a-z])/i.test(signature(el)) && !/shade|shadow|label|trail/i.test(signature(el));
  const visible = el => {
    const style = getComputedStyle(el);
    return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) !== 0;
  };
  class Tracker {
    constructor() { this.reset(); }
    reset() { this.root = null; this.boundary=null;this.objects = []; this.balls = []; this.shadows=[];this.sizes=new WeakMap();this.selected = null;this.selectedShadow=null; this.nextScan = 0; }
    select(el) {
      if (!this.root || !this.root.contains(el) || inPlayer(el)) return false;
      // Select the clicked graphic rather than a parent containing the entire pitch.
      this.selected = el;
      return true;
    }
    selectShadow(el,clientX,clientY) {
      if(!this.root)return false;
      // Decorative SVG shadows often have pointer-events:none. Resolve the
      // explicitly clicked screen position rather than binding the pitch rect.
      if(Number.isFinite(clientX) && Number.isFinite(clientY)) {
        const bounds=this.bounds();
        const candidates=[...new Set([...this.shadows,...this.root.querySelectorAll('ellipse,[id*="shadow" i],[class*="shadow" i]'),el])];
        el=candidates.find(node=>{
          if(!this.root.contains(node) || inPlayer(node) || !visible(node) || typeof node.getBBox!=='function')return false;
          const b=node.getBBox(),r=node.getBoundingClientRect();
          return b.width>0 && b.height>0 && b.width<bounds.w*.12 && b.height<bounds.h*.08 &&
            clientX>=r.left-4 && clientX<=r.right+4 && clientY>=r.top-4 && clientY<=r.bottom+4;
        });
      }
      if(!el || !this.root.contains(el) || inPlayer(el) || typeof el.getBBox!=='function')return false;
      this.selectedShadow=el;return true;
    }
    scan(now) {
      const roots = [...document.querySelectorAll('svg')].filter(root => !excluded(root) && [...root.querySelectorAll(playerSelector)].some(isPlayer));
      const root = roots.find(root => visible(root) && root.getBoundingClientRect().width > 0) || null;
      if (root !== this.root) { this.selected = null;this.selectedShadow=null;this.sizes=new WeakMap(); this.root = root; }
      this.objects = root ? [...root.querySelectorAll(playerSelector)].filter(isPlayer) : [];
      this.balls = root ? [...root.querySelectorAll('[id],[class],[href],[aria-label],[data-testid]')]
        .filter(el => isBall(el) && !inPlayer(el) && ![...this.ancestors(el, root)].some(isBall)) : [];
      this.shadows=root?[...root.querySelectorAll('[id],[class],[data-testid]')].filter(el=>/puck|football|(?:^|[^a-z])ball(?:$|[^a-z])/i.test(signature(el)) && /shadow|shade/i.test(signature(el)) && !inPlayer(el)):[];
      this.boundary=this.findBoundary();
      this.nextScan = now + 750;
    }
    *ancestors(el, root) { for (let p = el.parentElement; p && p !== root; p = p.parentElement) yield p; }
    centre(el) {
      const b=el.getBBox();
      return b.width || b.height?svgPosition(el,this.root,b.x+b.width/2,b.y+b.height/2):null;
    }
    flight(el,visual,bounds) {
      const local=[...el.querySelectorAll('[id],[class]')].filter(n=>/shadow|shade/i.test(signature(n)));
      const candidates=[...local,...this.shadows,...(this.selectedShadow?[this.selectedShadow]:[])].filter(n=>n.isConnected && visible(n));
      if(this.selectedShadow && (!this.selectedShadow.isConnected || !this.root.contains(this.selectedShadow)))this.selectedShadow=null;
      const shadow=this.selectedShadow || candidates.find(n=>el.contains(n) || n.parentElement===el.parentElement) || (candidates.length===1?candidates[0]:null);
      if(shadow) {
        // A ball group may contain both the ball and its shadow; its combined
        // bbox centre is not the airborne ball's centre. Isolate the graphic.
        const graphic=[...el.querySelectorAll('circle,image,use,path')].find(n=>!candidates.some(s=>s===n || s.contains(n)));
        if(graphic && el.contains(shadow))visual=this.centre(graphic) || visual;
        const ground=this.centre(shadow);
        if(ground && Math.abs(visual[0]-ground[0])<bounds.w*.12 && visual[1]<=ground[1]+bounds.h*.03)
          return {position:ground,visualPosition:visual,shadowElement:shadow,heightU:Math.max(0,ground[1]-visual[1])/bounds.w,offsetU:(visual[0]-ground[0])/bounds.w,visualScale:1,flightMode:'rendered ball/shadow separation'};
      }
      // Follow native rendered scale, never the inline future transition target.
      // Divide out static SVG asset scaling and parent zoom before interpreting
      // the ball's growth as a flight cue. This is visual height, not metres.
      let motion=el;
      for(const parent of this.ancestors(el,this.root))if(isBall(parent)){motion=parent;break;}
      let scale=1;
      try {
        const relative=motion.parentElement.getScreenCTM().inverse().multiply(motion.getScreenCTM());
        const base=motion.transform?.baseVal?.consolidate()?.matrix;
        const baseScale=base?Math.sqrt(Math.abs(base.a*base.d-base.b*base.c)):1;
        scale=Math.sqrt(Math.abs(relative.a*relative.d-relative.b*relative.c))/Math.max(.001,baseScale);
      } catch(_) { /* use the observed glyph-size cue below */ }
      const box=el.getBBox(),width=box.width;
      const minimum=Math.min(width,this.sizes.get(el) || width);
      if(width>0){this.sizes.set(el,minimum);scale=Math.max(scale,width/Math.max(.001,minimum));}
      scale=Number.isFinite(scale)?Math.min(3,Math.max(1,scale)):1;
      return {position:visual,visualPosition:visual,heightU:(scale-1)*.018,offsetU:0,visualScale:scale,flightMode:scale>1.025?'rendered ball size/scale cue':'no visible elevation cue'};
    }
    findBoundary() {
      if(!this.root)return null;
      const explicit=this.root.querySelector('[data-testid="pitch-bounds"], rect[data-pitch-bounds]');
      if(explicit)return {element:explicit,source:'pitch marker'};
      let best=null,bestRank=-Infinity;
      // A viewBox can include goal/advertising margins. Discover the playing
      // surface itself, without guessing its limits from player positions.
      for(const el of [...this.root.querySelectorAll('rect,path,polygon')].slice(0,400)) {
        if(el.closest('defs,clipPath,mask,pattern,symbol') || inPlayer(el) || isBall(el) || [...this.ancestors(el,this.root)].some(isBall))continue;
        try {
          const b=el.getBBox();
          const canonical=Math.abs(b.width-105)<.2 && Math.abs(b.height-68)<.2;
          const named=/pitch|playing.field|field.bound|field.outline/i.test(signature(el));
          if(!canonical && !(named && b.width>30 && b.height>20 && Math.abs(b.width/b.height-105/68)<.08))continue;
          if(!visible(el) || !el.getClientRects().length)continue;
          let hidden=false;
          for(const parent of this.ancestors(el,this.root))if(!visible(parent)){hidden=true;break;}
          if(hidden)continue;
          const rank=(canonical?1000:100)+(named?20:0)+(el.tagName==='rect'?10:0);
          if(rank>bestRank){best={element:el,source:'rendered pitch geometry'};bestRank=rank;}
        } catch(_) { /* an unrendered or replaced shape is not a boundary */ }
      }
      return best;
    }
    bounds() {
      const explicit=this.root?.querySelector('[data-testid="pitch-bounds"], rect[data-pitch-bounds]');
      if(explicit && this.boundary?.element!==explicit)this.boundary={element:explicit,source:'pitch marker'};
      if(this.boundary && !this.root?.contains(this.boundary.element))this.boundary=this.findBoundary();
      const pitch=this.boundary?.element;
      if(pitch)try {
        const b=pitch.getBBox();
        const corners=[[b.x,b.y],[b.x+b.width,b.y],[b.x+b.width,b.y+b.height],[b.x,b.y+b.height]].map(([x,y])=>svgPosition(pitch,this.root,x,y));
        if(corners.every(Boolean)) {
          const xs=corners.map(p=>p[0]),ys=corners.map(p=>p[1]);
          const x=Math.min(...xs),y=Math.min(...ys),w=Math.max(...xs)-x,h=Math.max(...ys)-y;
          if(w>0 && h>0)return {x,y,w,h,source:this.boundary.source,element:`${pitch.tagName}${pitch.id?'#'+pitch.id:''}`};
        }
      } catch(_) { /* use original viewBox fallback until geometry reconnects */ }
      const b = this.root?.viewBox?.baseVal;
      return b?.width > 30 && b.height > 20 && b.width < 1000 && b.height < 1000
        ? { x: b.x, y: b.y, w: b.width, h: b.height, source: 'SVG viewBox' }
        : { x: 0, y: 0, w: 105, h: 68, source: '105 × 68 fallback' };
    }
    sample(now = performance.now()) {
      if ((this.root && !this.root.isConnected) || now >= this.nextScan || this.objects.some(el => !el.isConnected)) this.scan(now);
      const root = this.root, bounds = this.bounds();
      if (!root) return { players: [], ball: null, bounds, diagnostic: 'Waiting for MFL pitch SVG' };
      const normalize = p => p && ({ u: (p[0]-bounds.x)/bounds.w, v: (p[1]-bounds.y)/bounds.h });
      const players = this.objects.filter(el => root.contains(el) && visible(el)).map(el => {
        const c = el.querySelector('circle');
        const p = normalize(svgPosition(el, root, Number(c.getAttribute('cx') || 0), Number(c.getAttribute('cy') || 0)));
        return p && { ...p, id: el.id, color: getComputedStyle(c).fill || c.getAttribute('fill') || '#28a7e0', number: el.querySelector('text')?.textContent.trim().slice(0,3) || '' };
      }).filter(p => p && p.u >= 0 && p.u <= 1 && p.v >= 0 && p.v <= 1);
      if (this.selected && (!this.selected.isConnected || !root.contains(this.selected))) this.selected = null;
      let ball = null;
      for (const el of this.selected ? [this.selected] : this.balls) {
        try {
          if (!el.isConnected || !root.contains(el) || !visible(el)) continue;
          const b = el.getBBox();
          if (!b.width && !b.height) continue;
          const visual=svgPosition(el, root, b.x+b.width/2, b.y+b.height/2);
          if(!visual)continue;
          const flight=this.flight(el,visual,bounds),p=normalize(flight.position);
          if (p && p.u >= -0.03 && p.u <= 1.03 && p.v >= -0.05 && p.v <= 1.05) {
            const shadow=flight.shadowElement;
            ball={...p,heightU:flight.heightU,offsetU:flight.offsetU,visualScale:flight.visualScale,flightMode:flight.flightMode,
              source:{ball:`${el.tagName}${el.id?'#'+el.id:''}`,shadow:shadow?`${shadow.tagName}${shadow.id?'#'+shadow.id:''}`:null,visualPosition:flight.visualPosition,groundPosition:flight.position}};
            break;
          }
        } catch (_) { /* a replaced SVG node is retried on the next scan */ }
      }
      return { players, ball, bounds, diagnostic: ball ? 'Ball tracked' : `Ball unavailable (${this.balls.length} candidates); use Select ball` };
    }
  }
  api.Tracker = Tracker;
  api.svgPosition = svgPosition;
})();

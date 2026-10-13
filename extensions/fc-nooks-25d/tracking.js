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
    reset() { this.root = null; this.objects = []; this.balls = []; this.selected = null; this.nextScan = 0; }
    select(el) {
      if (!this.root || !this.root.contains(el) || inPlayer(el)) return false;
      // Select the clicked graphic rather than a parent containing the entire pitch.
      this.selected = el;
      return true;
    }
    scan(now) {
      const roots = [...document.querySelectorAll('svg')].filter(root => !excluded(root) && [...root.querySelectorAll(playerSelector)].some(isPlayer));
      const root = roots.find(root => visible(root) && root.getBoundingClientRect().width > 0) || null;
      if (root !== this.root) { this.selected = null; this.root = root; }
      this.objects = root ? [...root.querySelectorAll(playerSelector)].filter(isPlayer) : [];
      this.balls = root ? [...root.querySelectorAll('[id],[class],[href],[aria-label],[data-testid]')]
        .filter(el => isBall(el) && !inPlayer(el) && ![...this.ancestors(el, root)].some(isBall)) : [];
      this.nextScan = now + 750;
    }
    *ancestors(el, root) { for (let p = el.parentElement; p && p !== root; p = p.parentElement) yield p; }
    bounds() {
      // Explicit pitch markers, if supplied by MFL, take precedence over a padded viewBox.
      const pitch = this.root?.querySelector('[data-testid="pitch-bounds"], rect[data-pitch-bounds]');
      if (pitch) {
        try {
          const b = pitch.getBBox(), a = svgPosition(pitch, this.root, b.x, b.y), z = svgPosition(pitch, this.root, b.x + b.width, b.y + b.height);
          if (a && z && z[0] > a[0] && z[1] > a[1]) return { x: a[0], y: a[1], w: z[0]-a[0], h: z[1]-a[1], source: 'pitch marker' };
        } catch (_) { /* use original viewBox fallback */ }
      }
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
          const p = normalize(svgPosition(el, root, b.x+b.width/2, b.y+b.height/2));
          if (p && p.u >= -0.03 && p.u <= 1.03 && p.v >= -0.05 && p.v <= 1.05) { ball = p; break; }
        } catch (_) { /* a replaced SVG node is retried on the next scan */ }
      }
      return { players, ball, bounds, diagnostic: ball ? 'Ball tracked' : `Ball unavailable (${this.balls.length} candidates); use Select ball` };
    }
  }
  api.Tracker = Tracker;
  api.svgPosition = svgPosition;
})();

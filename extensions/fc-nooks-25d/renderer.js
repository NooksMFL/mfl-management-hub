(() => {
  'use strict';
  const api = globalThis.FCN25D;
  class Renderer {
    constructor(scene) { this.scene = scene; this.players = new Map(); this.ball = scene.ball; }
    clear() { for (const node of this.players.values()) node.remove(); this.players.clear(); this.ball.setAttribute('visibility','hidden'); }
    render(snapshot) {
      const seen = new Set();
      // One snapshot, one projection, no interpolation or second animation clock.
      for (const p of snapshot.players) {
        seen.add(p.id);
        let node = this.players.get(p.id);
        if (!node) {
          node = api.svg('g', {'class':'fcn-player','data-player':p.id});
          node.innerHTML = '<ellipse cy="1" rx="5" ry="1.5" fill="#153622" opacity=".38"/><path d="M-1.6 -5l-.8 4M1.4 -5l1 4" stroke="#cca37e" stroke-width="1.8"/><path d="M-2.4 -1h-2M2.3 -1h2" stroke="#19262a" stroke-width="1.4"/><path d="M-3.2 -8h6.4l-.5 3.5h-2.3L0 -7l-.4 2.5h-2.3z" fill="#172e42"/><path d="M-3 -15l-1.5 4M3 -15l1.5 4" stroke="#cda989" stroke-width="1.6"/><path class="shirt" d="M-2.3 -16q2.3 1.5 4.6 0l1.5 2.5-1.2 1-.5 4.6q-2.1 .7-4.2 0l-.5-4.6-1.2-1z"/><path d="M1.8 -15.5l.4 6.6h-1.5l-.5-7" fill="#000" opacity=".13"/><circle cy="-19" r="2.2" fill="#c6a583"/><path d="M-2 -19q0-3 3-2.2l1 1.5" fill="#2a261f"/><text class="jersey" y="-10" text-anchor="middle" fill="#ffffef" font-size="4" font-weight="700" font-family="Arial"/>';
          this.scene.actors.append(node); this.players.set(p.id,node);
        }
        const [x,y] = api.project(p.u,p.v), scale = this.scene.scale(p.v);
        node.setAttribute('transform',`translate(${x} ${y}) scale(${scale})`);
        const shirt=node.querySelector('.shirt'), number=node.querySelector('text');
        if (shirt.getAttribute('fill')!==p.color) shirt.setAttribute('fill',p.color);
        if (number.textContent!==p.number) number.textContent = p.number;
      }
      for (const [id,node] of this.players) if (!seen.has(id)) { node.remove(); this.players.delete(id); }
      // Depth order changes only where needed; football is above feet, below heads.
      const ordered = [...snapshot.players].sort((a,b)=>a.v-b.v).map(p=>this.players.get(p.id));
      ordered.forEach((node,i)=>{ if (this.scene.actors.children[i] !== node) this.scene.actors.insertBefore(node,this.scene.actors.children[i] || null); });
      this.ball.setAttribute('visibility',snapshot.ball ? 'visible' : 'hidden');
      if (snapshot.ball) {
        const [x,y] = api.project(snapshot.ball.u,snapshot.ball.v);
        this.ball.setAttribute('transform',`translate(${x} ${y}) scale(${this.scene.scale(snapshot.ball.v)})`);
      }
    }
  }
  api.Renderer = Renderer;
})();

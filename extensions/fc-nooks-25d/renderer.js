(() => {
  'use strict';
  const api = globalThis.FCN25D;
  class Renderer {
    constructor(scene) {
      this.scene=scene;this.players=new Map();this.sprites=new Map();this.ball=scene.ball;
      this.airborne=this.ball.querySelector('[data-ball-airborne]');this.shadow=this.ball.querySelector('[data-ball-shadow]');
      this.label=api.svg('g',{'data-possession-label':'true',visibility:'hidden','pointer-events':'none','aria-hidden':'true'});
      this.label.innerHTML='<rect rx="3" fill="#0a1727" fill-opacity=".94" stroke-width="1"/><text text-anchor="middle" fill="#f6f8f4" font-size="12" font-family="Arial" font-weight="600"/>';
      scene.svg.append(this.label);this.labelRect=this.label.querySelector('rect');this.labelText=this.label.querySelector('text');
    }
    clear() { for (const node of this.players.values()) node.remove(); this.players.clear();this.sprites.clear();this.label.setAttribute('visibility','hidden');this.label.setAttribute('aria-hidden','true');this.ball.setAttribute('visibility','hidden'); }
    render(snapshot,now=performance.now()) {
      const seen = new Set();
      // One snapshot, one projection, no interpolation or second animation clock.
      for (const p of snapshot.players) {
        seen.add(p.id);
        let node = this.players.get(p.id);
        if (!node) {
          const sprite=new api.PlayerSprite(p.id,this.scene);node=sprite.node;this.sprites.set(p.id,sprite);
          this.scene.actors.append(node);this.players.set(p.id,node);
        }
        this.sprites.get(p.id).update(p,now);
        const [x,y] = this.scene.project(p.u,p.v), scale = this.scene.scale(p.v);
        node.setAttribute('transform',`translate(${x} ${y}) scale(${scale})`);
      }
      for (const [id,node] of this.players) if (!seen.has(id)) { node.remove(); this.players.delete(id);this.sprites.delete(id); }
      // Depth order changes only where needed; football is above feet, below heads.
      const ordered = [...snapshot.players].sort((a,b)=>a.v-b.v).map(p=>this.players.get(p.id));
      ordered.forEach((node,i)=>{ if (this.scene.actors.children[i] !== node) this.scene.actors.insertBefore(node,this.scene.actors.children[i] || null); });
      this.updateLabel(snapshot);
      this.ball.setAttribute('visibility',snapshot.ball ? 'visible' : 'hidden');
      if (snapshot.ball) {
        const [x,y] = this.scene.project(snapshot.ball.u,snapshot.ball.v);
        const scale=this.scene.scale(snapshot.ball.v),flightScale=this.scene.flightScale(snapshot.ball.v);
        const lift=(snapshot.ball.heightU || 0)*flightScale/scale,offset=(snapshot.ball.offsetU || 0)*flightScale/scale;
        this.ball.setAttribute('transform',`translate(${x} ${y}) scale(${scale})`);
        this.airborne.setAttribute('transform',`translate(${offset} ${-lift}) scale(${Math.min(1.8,snapshot.ball.visualScale || 1)})`);
        const height=snapshot.ball.heightU || 0;
        this.shadow.setAttribute('opacity',Math.max(.18,.5-height*4));
        this.shadow.setAttribute('rx',3.5+Math.min(5,height*100));
        this.ball.dataset.flight=snapshot.ball.flightMode || 'unknown';
      }
    }
    updateLabel(snapshot) {
      const possession=snapshot.possession;
      const player=possession?.surname && snapshot.players.find(p=>p.id===possession.playerId);
      if(!player){this.label.setAttribute('visibility','hidden');this.label.setAttribute('aria-hidden','true');return;}
      const raw=possession.surname,letters=Array.from(raw),text=letters.length>25?letters.slice(0,24).join('')+'…':raw;
      const m=this.scene.svg.getScreenCTM(),pixelScale=m?Math.hypot(m.a,m.b):1;
      const unit=1/Math.max(.001,pixelScale);
      if(this.labelText.textContent!==text || this.labelScale!==pixelScale) {
        this.labelText.textContent=text;this.labelText.setAttribute('font-size',12*unit);
        this.labelWidth=this.labelText.getComputedTextLength()+12*unit;this.labelScale=pixelScale;
      }
      const width=this.labelWidth,height=20*unit;
      const [px,py]=this.scene.project(player.u,player.v),box=this.scene.svg.viewBox.baseVal;
      const x=Math.max(box.x+width/2+2*unit,Math.min(box.x+box.width-width/2-2*unit,px));
      const y=Math.max(box.y+height+2*unit,Math.min(box.y+box.height-2*unit,py-28*this.scene.scale(player.v)-5*unit));
      this.label.setAttribute('transform',`translate(${x} ${y})`);
      this.labelRect.setAttribute('x',-width/2);this.labelRect.setAttribute('y',-height);this.labelRect.setAttribute('width',width);this.labelRect.setAttribute('height',height);
      this.labelRect.setAttribute('rx',3*unit);this.labelRect.setAttribute('stroke-width',unit);this.labelRect.setAttribute('stroke',CSS.supports('color',player.color)?player.color:'#28a7e0');
      this.labelText.setAttribute('y',-6*unit);
      this.label.setAttribute('visibility','visible');this.label.setAttribute('aria-hidden','false');this.label.setAttribute('aria-label',raw);
      this.label.dataset.playerId=player.id;this.label.dataset.source=possession.source;
    }

  }
  api.Renderer = Renderer;
})();

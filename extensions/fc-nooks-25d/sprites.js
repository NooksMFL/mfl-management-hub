(() => {
  'use strict';
  const api=globalThis.FCN25D;
  const set=(el,key,value)=>{if(el.getAttribute(key)!==value)el.setAttribute(key,value);};
  class PlayerSprite {
    constructor(id,scene) {
      this.node=api.svg('g',{'class':'fcn-player','data-player':id});
      // Athletic proportions, shaped joints, boot soles and simple lighting.
      // Every moving part is inside a glyph; its ground anchor never changes.
      this.node.innerHTML=`<ellipse cy=".5" rx="4.2" ry="1.25" fill="#102d20" opacity=".34"/>
      <g data-body>
        <g data-leg="back" transform="translate(-1.7 -7)"><path d="M0 0L-.1 3.4L.1 6.2" fill="none" stroke="#bb8864" stroke-width="1.9" stroke-linecap="round"/><path d="M.05 3.2L.1 6.4" stroke="#f0f1e9" stroke-width="1.7"/><path d="M-.75 6.1h1.6l1.2 .65q.3 .6-.35 .75H-.85z" fill="#16232b"/><path d="M-.7 7.35h2.5" stroke="#eceddb" stroke-width=".28"/></g>
        <g data-leg="front" transform="translate(1.7 -7)"><path d="M0 0L.4 3.4L.2 6.2" fill="none" stroke="#d0a17c" stroke-width="2" stroke-linecap="round"/><path d="M.38 3.25L.2 6.4" stroke="#f0f1e9" stroke-width="1.75"/><path d="M-.65 6.1h1.6l1.25 .65q.3 .6-.4 .75H-.75z" fill="#1b2830"/><path d="M-.6 7.35h2.5" stroke="#eeeece" stroke-width=".28"/></g>
        <g data-arm="back" transform="translate(-3 -17)"><path data-sleeve d="M0 0L-.8 2.5" stroke-width="2.3" stroke-linecap="round"/><path d="M-.8 2.5L-1.1 4.4L.25 6" fill="none" stroke="#bb8864" stroke-width="1.35" stroke-linecap="round"/><ellipse cx=".4" cy="6.2" rx=".6" ry=".8" fill="#c08d67"/></g>
        <path d="M-3.15 -10h6.3l-.45 4.3H.6L0 -8l-.6 2.3h-2.1z" fill="#173047"/><path d="M-2.3 -9.3h1.5l-.5 3.3h-1.3z" fill="#ffffff" opacity=".1"/>
        <path class="shirt" d="M-2.7 -18.5q2.7 1 5.4 0l.9 2.2-.6 5.8q-3.05 1.1-6.1 0l-.55-5.8z"/>
        <path d="M-2.7 -18.3q1.2 .45 2.1 .5l-.5 7.5-2-.2z" fill="#fff" opacity=".13"/><path d="M2.05 -18.2l1.15 1.7-.65 6-1.15 .25z" fill="#071d27" opacity=".22"/>
        <path d="M-1.3 -18.9q1.3 1.9 2.6 0" fill="none" stroke="#e7e8df" stroke-width=".55"/>
        <path d="M-.8 -21v2q.8 .8 1.6 0v-2" fill="#c99771"/>
        <ellipse cx=".15" cy="-22.4" rx="1.65" ry="2.05" fill="#d0a17c"/><path d="M.9 -24l.7 .6-.25 2.6-.7 .4" fill="#996a4b" opacity=".4"/>
        <path d="M-1.5 -22.7q-.25-2.3 1.6-2.2t1.8 2.05l-.7-.3-.4-1.1q-1.4 .55-2.3 1.55" fill="#312a26"/><path d="M.6 -22.3h.4" stroke="#302d29" stroke-width=".25"/>
        <g data-arm="front" transform="translate(3 -17)"><path data-sleeve d="M0 0L.8 2.5" stroke-width="2.4" stroke-linecap="round"/><path d="M.8 2.5L1 4.4L-.25 6" fill="none" stroke="#d0a17c" stroke-width="1.45" stroke-linecap="round"/><ellipse cx="-.4" cy="6.2" rx=".65" ry=".8" fill="#d8ad88"/></g>
      </g><text class="jersey" y="-12.7" text-anchor="middle" fill="#ffffef" stroke="#10252b" stroke-width=".1" font-size="3.7" font-weight="700" font-family="Arial"/>`;
      this.body=this.node.querySelector('[data-body]');
      this.legs=[...this.node.querySelectorAll('[data-leg]')];this.arms=[...this.node.querySelectorAll('[data-arm]')];
      this.shirt=this.node.querySelector('.shirt');this.sleeves=[...this.node.querySelectorAll('[data-sleeve]')];this.number=this.node.querySelector('.jersey');
      const face=api.svg('image',{x:-4.5,y:-27,width:9,height:9,preserveAspectRatio:'xMidYMid slice','data-player-portrait':'true',visibility:scene.stadiumId==='minty-stadium' && scene.portrait?'visible':'hidden'});
      if(scene.portrait)face.setAttribute('href',scene.portrait);this.node.append(face);
      this.phase=0;this.last=null;this.lastMove=-Infinity;this.facing=1;
    }
    update(player,now) {
      const color=CSS.supports('color',player.color)?player.color:'#28a7e0';
      set(this.shirt,'fill',color);this.sleeves.forEach(el=>set(el,'stroke',color));
      if(this.number.textContent!==player.number)this.number.textContent=player.number;
      if(this.last) {
        const dx=(player.u-this.last.u)*105,dy=(player.v-this.last.v)*68,distance=Math.hypot(dx,dy);
        if(distance>.003 && distance<6) {
          this.phase=(this.phase+distance*Math.PI*2/3.4)%(Math.PI*2);this.lastMove=now;
          if(Math.abs(dx)>.015)this.facing=dx<0?-1:1;
        } else if(distance>=6) {this.phase=0;this.lastMove=-Infinity;}
      }
      const running=now-this.lastMove<140,swing=running?Math.sin(this.phase)*18:0;
      set(this.body,'transform',`scale(${this.facing} 1)`);
      this.legs.forEach((el,i)=>set(el,'transform',`translate(${i?1.7:-1.7} -7) rotate(${(i?swing:-swing).toFixed(1)})`));
      this.arms.forEach((el,i)=>set(el,'transform',`translate(${i?3:-3} -17) rotate(${(i?-swing:swing).toFixed(1)})`));
      this.node.dataset.pose=running?'running':'standing';this.last={u:player.u,v:player.v};
    }
  }
  api.PlayerSprite=PlayerSprite;
})();

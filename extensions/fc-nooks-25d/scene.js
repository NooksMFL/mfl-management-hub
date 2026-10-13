(() => {
  'use strict';
  const api = globalThis.FCN25D;
  const NS = 'http://www.w3.org/2000/svg';
  api.svg = (tag, attrs = {}) => {
    const el = document.createElementNS(NS,tag);
    for (const [key,value] of Object.entries(attrs)) el.setAttribute(key,value);
    return el;
  };
  // Architectural plate calibration. All lines, actors and nets share this
  // projective mapping; never compensate for alignment with independent CSS.
  const theme = Object.freeze({
    width:1672, height:941, farLeft:346, farRight:1326, farY:433,
    nearLeft:42, nearRight:1630, nearY:730,
    screens:[{x:748,y:176,w:179,h:45},{x:147,y:212,w:119,h:49},{x:1407,y:212,w:116,h:49}]
  });
  api.camera = calibration => {
    const t={...theme,...calibration},ratio=(t.farRight-t.farLeft)/(t.nearRight-t.nearLeft);
    const denominator=v=>1-v+ratio*v;
    return {
      project(u,v) {
        const d=denominator(v);
        return [(t.farLeft*(1-v)+ratio*t.nearLeft*v+(t.farRight-t.farLeft)*u)/d,
          (t.farY*(1-v)+ratio*t.nearY*v)/d];
      },
      scale:v=>.62/denominator(v),
      flightScale:v=>(t.farRight-t.farLeft)/denominator(v)
    };
  };
  api.project = api.camera(theme).project;
  api.theme = theme;
  const path = points => points.map(([x,y],i)=>`${i?'L':'M'}${x.toFixed(3)},${y.toFixed(3)}`).join(' ');
  function buildScene() {
    let camera=api.camera(theme),portrait='';
    const project=(u,v)=>camera.project(u,v);
    const fieldPath=points=>path(points.map(([u,v])=>project(u,v)));
    const scene=api.svg('svg',{viewBox:`0 0 ${theme.width} ${theme.height}`,role:'img','aria-label':'Ironwood Lane: a traditional red-brick football ground under floodlights',preserveAspectRatio:'xMidYMid meet','data-asset-state':'loading'});
    // A complete local bitmap supplies photographic crowd/architecture detail.
    // A small inline bowl and turf remain if an installation omits the asset.
    scene.innerHTML=`<defs>
      <linearGradient id="fcn-fallback-sky" x2="0" y2="1"><stop stop-color="#162a3a"/><stop offset="1" stop-color="#314358"/></linearGradient>
      <radialGradient id="fcn-fallback-grass"><stop stop-color="#578845"/><stop offset="1" stop-color="#356735"/></radialGradient>
      <pattern id="fcn-fallback-crowd" width="13" height="11" patternUnits="userSpaceOnUse"><rect width="13" height="11" fill="#37242c"/><circle cx="3" cy="3" r="1.6" fill="#c2a88a"/><path d="M0 9q0-5 3-5t3 5" fill="#8b4857"/><circle cx="10" cy="6" r="1.5" fill="#d0c5ac"/></pattern>
      <pattern id="fcn-net" width="5" height="5" patternUnits="userSpaceOnUse"><path d="M0 0H5V5" fill="none" stroke="#e6eee6" stroke-width=".6" opacity=".65"/></pattern>
    </defs>
    <rect width="1672" height="941" fill="url(#fcn-fallback-sky)"/>
    <path d="M20 166H1652L1672 941H0Z M330 420L1342 420L1640 740H32Z" fill="url(#fcn-fallback-crowd)" fill-rule="evenodd" stroke="#375261" stroke-width="3"/>
    <path d="M25 153L1647 153L1600 213H72Z" fill="#482936" stroke="#8298a3"/>
    <path d="M50 315H1622" stroke="#90ad9e" stroke-width="9"/>`;
    const backdrop=api.svg('g',{'data-backdrop-layer':'true'});
    scene.append(backdrop);
    const grass=api.svg('path',{d:fieldPath([[0,0],[1,0],[1,1],[0,1]])+' Z',fill:'url(#fcn-fallback-grass)','data-fallback-grass':'true'});
    scene.append(grass);
    const notice=api.svg('text',{x:836,y:105,'text-anchor':'middle',fill:'#ffd58e','font-size':18,'font-family':'Arial',visibility:'hidden','data-asset-notice':'true'});
    notice.textContent='Stadium image missing — reinstall the complete extension folder';

    function buildPitch() {
    const markings=api.svg('g',{fill:'none',stroke:'#f1f2df','stroke-width':1.6,opacity:.86,'data-pitch-markings':'true'});
    const line=points=>markings.append(api.svg('path',{d:fieldPath(points)}));
    line([[0,0],[1,0],[1,1],[0,1],[0,0]]);line([[.5,0],[.5,1]]);
    for (const side of [0,1]) {
      const s=side?-1:1;
      line([[side,(34-20.16)/68],[side+s*16.5/105,(34-20.16)/68],[side+s*16.5/105,(34+20.16)/68],[side,(34+20.16)/68]]);
      line([[side,(34-9.16)/68],[side+s*5.5/105,(34-9.16)/68],[side+s*5.5/105,(34+9.16)/68],[side,(34+9.16)/68]]);
      line(Array.from({length:37},(_,i)=>{const a=-.925+i*1.85/36;return [side+s*(11+9.15*Math.cos(a))/105,.5+9.15*Math.sin(a)/68];}));
      const [x,y]=project(side+s*11/105,.5);markings.append(api.svg('circle',{cx:x,cy:y,r:1.6,fill:'#f1f2df',stroke:'none'}));
    }
    line(Array.from({length:81},(_,i)=>[.5+9.15/105*Math.cos(i*Math.PI/40),.5+9.15/68*Math.sin(i*Math.PI/40)]));
    const [cx,cy]=project(.5,.5);markings.append(api.svg('circle',{cx,cy,r:1.8,fill:'#f1f2df',stroke:'none'}));
    // Corner arcs and slender corner flags complete the real pitch silhouette.
    for (const u of [0,1]) for (const v of [0,1]) {
      const points=Array.from({length:13},(_,i)=>{const a=i*Math.PI/24;return [u+(u?-1:1)*Math.cos(a)/105,v+(v?-1:1)*Math.sin(a)/68];});
      line(points);
      const [x,y]=project(u,v);markings.append(api.svg('path',{d:`M${x} ${y}v-12m0 0l6 2-6 2`,stroke:'#d8e9ce','stroke-width':1.1}));
    }
    const goals=api.svg('g',{'data-goals':'true'});
    for (const side of [0,1]) {
      const a=project(side,.5-3.66/68),b=project(side,.5+3.66/68),direction=side?1:-1;
      const depth=22*direction,height=22;
      const backA=[a[0]+depth,a[1]-5],backB=[b[0]+depth,b[1]-5];
      const topA=[a[0],a[1]-height],topB=[b[0],b[1]-height],rearA=[backA[0],backA[1]-height],rearB=[backB[0],backB[1]-height];
      for (const points of [[a,b,backB,backA],[topA,topB,rearB,rearA],[backA,backB,rearB,rearA]]) goals.append(api.svg('path',{d:path(points)+' Z',fill:'url(#fcn-net)',stroke:'#dce6dc','stroke-width':.8}));
      goals.append(api.svg('path',{d:path([a,topA,topB,b]),fill:'none',stroke:'#f1f4e8','stroke-width':2.2,'stroke-linejoin':'round'}));
    }
    return [markings,goals];
    }
    let pitchLayers=buildPitch();scene.append(...pitchLayers);
    // Cover only displays physically present in each plate, including tiny grounds.
    const displays=api.svg('g',{'data-stadium-displays':'true','font-family':'Arial','text-anchor':'middle'});
    for (const [index,screen] of theme.screens.entries()) {
      const {x,y,w,h}=screen;
      const g=api.svg('g',{'data-stadium-screen':index});
      g.append(api.svg('rect',{x,y,width:w,height:h,fill:'#050d13'}));
      const label=api.svg('text',{x:x+w/2,y:y+9,fill:'#d7b093','font-size':5.4,'letter-spacing':1.7,'data-stadium-label':'true'});g.append(label);
      g.append(api.svg('text',{x:x+w/2,y:y+29,fill:'#f1f4e7','font-size':18,'font-weight':700,'data-stadium-score':'true'}));
      g.append(api.svg('text',{x:x+7,y:y+27,fill:'#c0d4d1','font-size':5.6,'text-anchor':'start','data-stadium-home':'true'}));
      g.append(api.svg('text',{x:x+w-7,y:y+27,fill:'#c0d4d1','font-size':5.6,'text-anchor':'end','data-stadium-away':'true'}));
      g.append(api.svg('text',{x:x+w/2,y:y+h-5,fill:'#c6d8cf','font-size':6,'data-stadium-clock':'true'}));
      displays.append(g);
    }
    scene.append(displays);
    const actors=api.svg('g',{'data-actors':'true'}),ball=api.svg('g',{'data-ball':'true',visibility:'hidden'});
    ball.innerHTML='<ellipse data-ball-shadow cy="1" rx="3.5" ry="1.3" fill="#14351b" opacity=".5"/><g data-ball-airborne><circle cy="-2" r="2.8" fill="#fffee9" stroke="#30423d" stroke-width=".6"/><path d="M-.7 -3.5L1 -3.5L1.7 -2L0 -.9L-1.3 -2Z" fill="#2a333b"/></g>';
    scene.append(actors,ball,notice);
    const minty=api.svg('g',{'data-minty-decor':'true',visibility:'hidden'});
    const defs=scene.querySelector('defs');
    const pattern=api.svg('pattern',{id:'fcn-minty-faces',width:30,height:26,patternUnits:'userSpaceOnUse'});
    const face=api.svg('image',{x:4,y:0,width:18,height:18,preserveAspectRatio:'xMidYMid slice','data-minty-portrait':'true'});
    pattern.append(face);defs.append(pattern);
    const crowd=api.svg('path',{d:'M0 267L310 260L310 410L0 505Z M1362 260L1672 267L1672 505L1362 410Z M325 250H1347V407H325Z M0 814H1672V941H0Z',fill:'url(#fcn-minty-faces)',opacity:.85,'data-minty-crowd':'true'});
    minty.append(crowd,api.svg('rect',{x:584,y:288,width:502,height:72,rx:3,fill:'#123a31',stroke:'#b8f0d4','stroke-width':2}));
    for(const x of [596,682,930,1016])minty.append(api.svg('image',{x,y:292,width:64,height:64,preserveAspectRatio:'xMidYMid slice','data-minty-portrait':'true'}));
    const banner=api.svg('text',{x:836,y:331,'text-anchor':'middle',fill:'#effff7','font-size':19,'font-family':'Arial','font-weight':700});banner.textContent='MINTY STADIUM';minty.append(banner);
    scene.insertBefore(minty,pitchLayers[0]);
    let stadiumId=null,revision=0,currentPhoto=null,pendingPhoto=null;
    function syncPortrait() {
      const visible=stadiumId==='minty-stadium' && !!portrait;
      minty.setAttribute('visibility',visible?'visible':'hidden');
      scene.dataset.portrait=portrait?'ready':'missing';
      scene.querySelectorAll('[data-minty-portrait],[data-player-portrait]').forEach(el=>{
        if(portrait)el.setAttribute('href',portrait);else el.removeAttribute('href');
        if(el.hasAttribute('data-player-portrait'))el.setAttribute('visibility',visible?'visible':'hidden');
      });
    }
    function setStadium(id) {
      if (!api.isStadium(id)) return false;
      if (id===stadiumId) return true;
      const stadium=api.stadiums[id],request=++revision;
      stadiumId=id;scene.dataset.stadium=id;
      camera=api.camera(stadium.pitch);
      grass.setAttribute('d',fieldPath([[0,0],[1,0],[1,1],[0,1]])+' Z');
      const replacement=buildPitch();
      pitchLayers.forEach((old,index)=>old.replaceWith(replacement[index]));pitchLayers=replacement;
      syncPortrait();scene.dataset.assetState='loading';
      scene.setAttribute('aria-label',stadium.description);
      scene.querySelectorAll('[data-stadium-label]').forEach(el=>{el.textContent=stadium.label;});
      scene.querySelectorAll('[data-stadium-screen]').forEach((el,index)=>{
        const base=theme.screens[index],target=stadium.screens?stadium.screens[index]:base;
        if(!target){el.setAttribute('visibility','hidden');return;}
        el.setAttribute('visibility','visible');
        const sx=target.w/base.w,sy=target.h/base.h;
        el.setAttribute('transform',`matrix(${sx} 0 0 ${sy} ${target.x-base.x*sx} ${target.y-base.y*sy})`);
      });
      notice.setAttribute('visibility','hidden');
      // Keep the prior plate visible until the new one is decoded. No player,
      // ball, source node, scoreboard or animation frame is reset by a switch.
      pendingPhoto?.remove();
      const photo=api.svg('image',{x:0,y:0,width:theme.width,height:theme.height,preserveAspectRatio:'none','data-backdrop':'true'});
      pendingPhoto=photo;
      photo.addEventListener('load',()=>{
        if(request!==revision)return;
        currentPhoto?.remove();currentPhoto=photo;pendingPhoto=null;
        scene.dataset.assetState='ready';grass.setAttribute('fill','none');notice.setAttribute('visibility','hidden');
      });
      photo.addEventListener('error',()=>{
        if(request!==revision)return;
        photo.remove();currentPhoto?.remove();currentPhoto=null;pendingPhoto=null;
        scene.dataset.assetState='failed';grass.setAttribute('fill','url(#fcn-fallback-grass)');notice.setAttribute('visibility','visible');
      });
      backdrop.append(photo);
      photo.setAttribute('href',chrome.runtime.getURL(stadium.asset));
      return true;
    }
    setStadium(api.defaultStadium);
    return {
      svg:scene,actors,ball,
      setStadium,
      get stadiumId(){return stadiumId;},
      project,scale:v=>camera.scale(v),flightScale:v=>camera.flightScale(v),
      setPortrait(url) {portrait=url;syncPortrait();},
      get portrait(){return portrait;},
      updateScore(data) {
        scene.querySelectorAll('[data-stadium-score]').forEach(el=>{if(el.textContent!==data.score)el.textContent=data.score;});
        scene.querySelectorAll('[data-stadium-clock]').forEach(el=>{if(el.textContent!==data.clock)el.textContent=data.clock;});
        for(const side of ['home','away']) {
          const name=data[side].length>8?data[side].slice(0,7)+'…':data[side];
          scene.querySelectorAll(`[data-stadium-${side}]`).forEach(el=>{if(el.textContent!==name)el.textContent=name;});
        }
      }
    };
  }
  api.buildScene=buildScene;
})();

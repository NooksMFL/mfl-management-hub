(() => {
  'use strict';
  const api = globalThis.FCN25D;
  api.cameraViews = Object.freeze([
    {zoom:1, name:'Full stadium'},
    {zoom:1.75, name:'Close · 1.75×'},
    {zoom:2.5, name:'Very close · 2.5×'}
  ]);
  api.isCameraZoom = value => typeof value === 'number' && api.cameraViews.some(view => view.zoom === value);

  class ViewportCamera {
    constructor(scene) {
      this.scene = scene;
      this.zoom = 1.75;
      this.reset();
    }
    reset() {
      this.centre = this.scene.project(.5,.5);
      this.hasBall = false;
      this.write();
    }
    setZoom(zoom) {
      if (!api.isCameraZoom(zoom)) return false;
      this.zoom = zoom;
      this.write();
      return true;
    }
    update(snapshot) {
      const ball = snapshot?.ball;
      if (this.zoom === 1 || !ball) return;
      const ground = this.scene.project(ball.u,ball.v);
      const flightScale = this.scene.flightScale(ball.v);
      const airborne = [ground[0]+(ball.offsetU || 0)*flightScale, ground[1]-(ball.heightU || 0)*flightScale];
      const focus = [(ground[0]+airborne[0])/2, (ground[1]+airborne[1])/2];
      const size = [api.theme.width/this.zoom, api.theme.height/this.zoom];
      if (!this.hasBall) {
        this.centre = focus;
        this.hasBall = true;
      } else {
        // Hold the shot while play stays in its central region; pan only when
        // it crosses that region. This never interpolates actor coordinates.
        for (const axis of [0,1]) {
          const margin = size[axis]*.16;
          const distance = focus[axis]-this.centre[axis];
          if (Math.abs(distance)>margin) this.centre[axis] = focus[axis]-Math.sign(distance)*margin;
          // Keep both the airborne sphere and its ground shadow in the frame
          // when their separation fits, including high passes near a touchline.
          const low = Math.min(ground[axis],airborne[axis])-16;
          const high = Math.max(ground[axis],airborne[axis])+16;
          if (high-low<size[axis]) {
            this.centre[axis] = Math.max(high-size[axis]/2, Math.min(low+size[axis]/2,this.centre[axis]));
          }
        }
      }
      this.write();
    }
    write() {
      const width = api.theme.width/this.zoom, height = api.theme.height/this.zoom;
      const clamp = (value,half,extent) => Math.max(half,Math.min(extent-half,value));
      this.centre[0] = clamp(this.centre[0],width/2,api.theme.width);
      this.centre[1] = clamp(this.centre[1],height/2,api.theme.height);
      const box = this.zoom===1 ? [0,0,api.theme.width,api.theme.height] : [this.centre[0]-width/2,this.centre[1]-height/2,width,height];
      const value = box.map(number=>number.toFixed(3)).join(' ');
      if (value!==this.lastBox) {
        // One SVG viewport crops the complete scene: backdrop, lines, goals,
        // players, sphere and shadow always receive exactly the same zoom/pan.
        this.scene.svg.setAttribute('viewBox',value);
        this.lastBox = value;
      }
      if(this.scene.svg.dataset.cameraZoom!==String(this.zoom))this.scene.svg.dataset.cameraZoom = String(this.zoom);
    }
    diagnostics() { return {zoom:this.zoom, viewBox:this.lastBox, followingBall:this.zoom!==1 && this.hasBall}; }
  }
  api.ViewportCamera = ViewportCamera;
})();

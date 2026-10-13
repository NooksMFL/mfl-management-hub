(() => {
  'use strict';
  const api=globalThis.FCN25D;
  // All packaged plates share the same calibrated camera and screen positions.
  // Add a theme here without touching MFL extraction or the animation loop.
  api.stadiums=Object.freeze({
    'selhurst-park':Object.freeze({name:'Selhurst Park',label:'SELHURST PARK',asset:'assets/selhurst-park.jpg',description:'Selhurst Park-inspired Crystal Palace stadium, with red and blue stands under floodlights',screens:[{x:759,y:181,w:153,h:46},{x:145,y:213,w:125,h:53},{x:1405,y:213,w:122,h:53}]}),
    'ironwood-lane':Object.freeze({name:'Ironwood Lane',label:'IRONWOOD LANE',asset:'assets/ironwood-lane.jpg',description:'Ironwood Lane: a traditional red-brick football ground under floodlights'}),
    'harbour-park':Object.freeze({name:'Harbour Park',label:'HARBOUR PARK',asset:'assets/harbour-park.jpg',description:'Harbour Park: a coastal football stadium under floodlights'})
  });
  api.defaultStadium='selhurst-park';
  api.isStadium=id=>typeof id==='string' && Object.prototype.hasOwnProperty.call(api.stadiums,id);
})();

(() => {
  'use strict';
  const api=globalThis.FCN25D;
  // Each local plate declares its pitch calibration and actual display positions.
  // Add a theme here without touching MFL extraction or the animation loop.
  api.stadiums=Object.freeze({
    'selhurst-park':Object.freeze({name:'Selhurst Park',label:'SELHURST PARK',asset:'assets/selhurst-park.jpg',description:'Selhurst Park-inspired Crystal Palace stadium, with red and blue stands under floodlights',screens:[{x:759,y:181,w:153,h:46},{x:145,y:213,w:125,h:53},{x:1405,y:213,w:122,h:53}]}),
    'ironwood-lane':Object.freeze({name:'Ironwood Lane',label:'IRONWOOD LANE',asset:'assets/ironwood-lane.jpg',description:'Ironwood Lane: a traditional red-brick football ground under floodlights'}),
    'harbour-park':Object.freeze({name:'Harbour Park',label:'HARBOUR PARK',asset:'assets/harbour-park.jpg',description:'Harbour Park: a coastal football stadium under floodlights'}),
    "wembley":Object.freeze({"name":"Wembley","label":"WEMBLEY","asset":"assets/wembley.jpg","description":"Wembley-inspired floodlit arena with a signature illuminated arch","pitch":{"farY":466}}),
    "san-siro":Object.freeze({"name":"San Siro","label":"SAN SIRO","asset":"assets/san-siro.jpg","description":"San Siro-inspired three-tier bowl, spiral towers and red roof trusses"}),
    "camp-nou":Object.freeze({"name":"Camp Nou","label":"CAMP NOU","asset":"assets/camp-nou.jpg","description":"Camp Nou-inspired sweeping open bowl above Barcelona at dusk"}),
    "craven-cottage":Object.freeze({"name":"Craven Cottage","label":"CRAVEN COTTAGE","asset":"assets/craven-cottage.jpg","description":"Craven Cottage-inspired riverside ground with a traditional brick pavilion"}),
    "dripping-pan":Object.freeze({"name":"The Dripping Pan","label":"THE DRIPPING PAN","asset":"assets/dripping-pan.jpg","description":"The Dripping Pan-inspired small Lewes ground with grassy banks and a low red stand","pitch":{"farY":420},"screens":[{"x":789,"y":250,"w":62,"h":23}]}),
    "bracken-moor":Object.freeze({"name":"Bracken Moor","label":"BRACKEN MOOR","asset":"assets/bracken-moor.jpg","description":"Bracken Moor-inspired small hillside ground with blue and yellow terraces","pitch":{"farY":434},"screens":[{"x":815,"y":294,"w":39,"h":18}]}),
    "sandygate":Object.freeze({"name":"Sandygate","label":"SANDYGATE","asset":"assets/sandygate.jpg","description":"Sandygate-inspired tiny Sheffield ground with a low stand and stone boundary walls","pitch":{"farY":416},"screens":[{"x":819,"y":287,"w":45,"h":19}]}),
    "minty-stadium":Object.freeze({"name":"Minty Stadium","label":"MINTY STADIUM","asset":"assets/minty-stadium.jpg","description":"Minty Stadium: a mint and white floodlit ground with a personal face banner"})
  });
  api.isPortrait=url=>typeof url==='string' && url.length<1500000 && /^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(url);
  api.defaultStadium='selhurst-park';
  api.isStadium=id=>typeof id==='string' && Object.prototype.hasOwnProperty.call(api.stadiums,id);
})();

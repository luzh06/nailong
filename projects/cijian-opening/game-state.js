export const ROLE_IDS=['JP','CN','FR','AU'];
export function resolveRole(search,saved){const id=new URLSearchParams(search).get('role');return ROLE_IDS.includes(id)?id:ROLE_IDS.includes(saved)?saved:'JP'}
export function navIndex(nav,x,z){const i=Math.round((x-nav.minX)/nav.step),j=Math.round((z-nav.minZ)/nav.step);return i>=0&&i<nav.w&&j>=0&&j<nav.h?j*nav.w+i:-1}
export function canWalk(nav,x,z){const k=navIndex(nav,x,z);return k>=0&&nav.walkable[k]===1}
export function floorHeight(nav,x,z){const k=navIndex(nav,x,z);return k>=0&&nav.walkable[k]?nav.heights[k]:-1.52}
export function nearestWalkable(nav,x,z){let best=Infinity,result;nav.walkable.forEach((v,k)=>{if(!v)return;const px=nav.minX+(k%nav.w)*nav.step,pz=nav.minZ+Math.floor(k/nav.w)*nav.step,d=(px-x)**2+(pz-z)**2;if(d<best){best=d;result={x:px,z:pz}}});return result}
export class OpeningState{
 constructor(){this.phase='loading';this.inRange=false;this.transitions=0}
 ready(){if(this.phase==='loading')this.phase='exploring'}
 updateRange(distance){this.inRange=this.phase==='exploring'&&distance<=1.25;return this.inRange}
 interact(){if(!this.inRange||this.phase!=='exploring')return false;this.phase='reading';this.inRange=false;this.transitions++;return true}
 finish(){if(this.phase==='reading')this.phase='complete'}
 replay(){if(this.phase==='complete'){this.phase='exploring';this.inRange=false}}
}

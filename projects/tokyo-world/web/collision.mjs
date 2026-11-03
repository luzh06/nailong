import {Vector3,Triangle} from './vendor/three.module.js';
import {Octree} from './vendor/Octree.js';
import {Capsule} from './vendor/Capsule.js';

// A horizontal grid stores triangle indices once per intersected 2 m cell.
// Unlike recursive octree subdivision, coplanar faces have bounded storage.
// Narrow phase remains the official r170 capsule/triangle implementation.
class SolidGrid {
 constructor(data){
  this.data=data;this.cells=new Map();this.size=2;
  this.seen=new Uint32Array(data.length/9);this.stamp=0;
  this.minY=new Float32Array(data.length/9);this.maxY=new Float32Array(data.length/9);
  this.triangle=new Triangle();this.reverse=new Triangle();this.solver=new Octree();
  this.work=new Capsule(new Vector3(),new Vector3(),.28);this.center=new Vector3();
  for(let i=0,id=0;i<data.length;i+=9,id++){
   this.minY[id]=Math.min(data[i+1],data[i+4],data[i+7]);
   this.maxY[id]=Math.max(data[i+1],data[i+4],data[i+7]);
   const x0=Math.floor(Math.min(data[i],data[i+3],data[i+6])/this.size),x1=Math.floor(Math.max(data[i],data[i+3],data[i+6])/this.size);
   const z0=Math.floor(Math.min(data[i+2],data[i+5],data[i+8])/this.size),z1=Math.floor(Math.max(data[i+2],data[i+5],data[i+8])/this.size);
   for(let x=x0;x<=x1;x++)for(let z=z0;z<=z1;z++){
    const key=x+','+z;let cell=this.cells.get(key);if(!cell)this.cells.set(key,cell=[]);cell.push(id);
   }
  }
 }
 capsuleIntersect(body){
  this.work.copy(body);const c=this.work,r=c.radius,ids=[];
  const x0=Math.floor((Math.min(c.start.x,c.end.x)-r)/this.size),x1=Math.floor((Math.max(c.start.x,c.end.x)+r)/this.size);
  const z0=Math.floor((Math.min(c.start.z,c.end.z)-r)/this.size),z1=Math.floor((Math.max(c.start.z,c.end.z)+r)/this.size);
  const y0=Math.min(c.start.y,c.end.y)-r,y1=Math.max(c.start.y,c.end.y)+r;
  if(++this.stamp===4294967295){this.seen.fill(0);this.stamp=1;}
  for(let x=x0;x<=x1;x++)for(let z=z0;z<=z1;z++)for(const id of this.cells.get(x+','+z)||[]){
   if(this.seen[id]===this.stamp)continue;this.seen[id]=this.stamp;
   if(this.minY[id]<=y1&&this.maxY[id]>=y0)ids.push(id);
  }
  let deepest=false;
  for(const id of ids){
   const i=id*9,t=this.triangle;t.a.fromArray(this.data,i);t.b.fromArray(this.data,i+3);t.c.fromArray(this.data,i+6);
   const b=this.reverse;b.a.copy(t.c);b.b.copy(t.b);b.c.copy(t.a);
   const hit=this.solver.triangleCapsuleIntersect(c,t)||this.solver.triangleCapsuleIntersect(c,b);
   if(hit&&(!deepest||hit.depth>deepest.depth))deepest=hit;
  }
  // Return a real contact, not a sum whose opposing corrections can cancel.
  // WalkWorld resolves contacts iteratively then checks the final clearance.
  return deepest;
 }
}

export class WalkWorld {
 constructor(nav,triangles){
  this.nav=nav;this.radius=.28;this.stepHeight=.32;this.tree=new SolidGrid(triangles);
  this.capsule=new Capsule(new Vector3(),new Vector3(),this.radius);
  this.hasSolids=triangles.length>0;
 }
 ground(x,y){
  const n=this.nav,i=Math.round((x-n.x0)/n.step),j=Math.round((y-n.y0)/n.step);
  return i<0||j<0||i>=n.nx||j>=n.ny?null:n.heights[j*n.nx+i];
 }
 body(x,y,height){
  this.capsule.start.set(x,height+.32,-y);this.capsule.end.set(x,height+1.38,-y);return this.capsule;
 }
 contact(x,y,height){return this.hasSolids?this.tree.capsuleIntersect(this.body(x,y,height)):false;}
 standHeight(x,y){
  const h=this.ground(x,y);if(h===null)return null;let top=h,bottom=h;
  // A finite foot spans more than one tread. Use its highest support rather
  // than snapping the entire capsule down to the next cell too early.
  for(let i=0;i<8;i++){
   const a=i*Math.PI/4,k=this.ground(x+Math.cos(a)*this.radius,y+Math.sin(a)*this.radius);
   if(k===null)return null;top=Math.max(top,k);bottom=Math.min(bottom,k);
   if(top-bottom>this.stepHeight)return null;
  }
  const limit=top+this.stepHeight;
  // The heightfield samples tread bevels at 25 cm spacing. Resolve the few
  // millimetres of under-sampling against real low edges, with full headroom
  // checks on every retry. Tall walls and downward ceiling normals cannot lift.
  for(let i=0;i<6;i++){
   const hit=this.contact(x,y,top);
   if(!hit||hit.depth<.001||hit.normal.y<.5||!hit.point||hit.point.y>top+this.stepHeight)break;
   const raised=top+hit.depth/hit.normal.y+.001;
   if(raised>limit)break;top=raised;
  }
  return top;
 }
 canStand(x,y){const h=this.standHeight(x,y);if(h===null)return false;const hit=this.contact(x,y,h);return !hit||hit.depth<.002;}
 move(position,dx,dy){
  let p={...position};const count=Math.max(1,Math.ceil(Math.hypot(dx,dy)/.07));
  for(let i=0;i<count;i++){
   let x=p.x+dx/count,y=p.y+dy/count,h=this.standHeight(x,y);
   if(h===null||Math.abs(h-p.height)>this.stepHeight)continue;
   let blocked=false;
   for(let k=0;k<5;k++){
    const hit=this.contact(x,y,h);if(!hit||hit.depth<.001)break;
    if(Math.abs(hit.normal.y)>.7){blocked=true;break;}
    x+=hit.normal.x*(hit.depth+.0005);y-=hit.normal.z*(hit.depth+.0005);
    h=this.standHeight(x,y);if(h===null||Math.abs(h-p.height)>this.stepHeight){blocked=true;break;}
   }
   if(!blocked&&this.canStand(x,y))p={x,y,height:h};
  }
  return p;
 }
 findSpawn(x,y,maxDistance=3){
  if(this.canStand(x,y))return {x,y,height:this.standHeight(x,y)};
  for(let r=.25;r<=maxDistance;r+=.25){for(let i=0;i<24;i++){
   const angle=i*Math.PI/12,a=x+Math.cos(angle)*r,b=y+Math.sin(angle)*r;
   if(this.canStand(a,b))return {x:a,y:b,height:this.standHeight(a,b)};
  }}
  return null;
 }
}

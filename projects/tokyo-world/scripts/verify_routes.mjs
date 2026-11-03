// Offline route verification uses the same delivered WalkWorld as the browser.
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {WalkWorld} from '../web/collision.mjs';

class Queue {
 constructor(){this.items=[];}
 push(item){const a=this.items;let i=a.length;a.push(item);while(i){const p=(i-1)>>1;if(a[p].score<=item.score)break;a[i]=a[p];i=p;}a[i]=item;}
 pop(){const a=this.items,first=a[0],last=a.pop();if(a.length){let i=0;while(i*2+1<a.length){let c=i*2+1;if(c+1<a.length&&a[c+1].score<a[c].score)c++;if(a[c].score>=last.score)break;a[i]=a[c];i=c;}a[i]=last;}return first;}
}

export function findRoute(w,start,end){
 const n=w.nav,N=n.nx*n.ny,valid=new Int8Array(N),cost=new Float32Array(N).fill(Infinity),parent=new Int32Array(N).fill(-1),q=new Queue();
 const idx=p=>Math.round((p.y-n.y0)/n.step)*n.nx+Math.round((p.x-n.x0)/n.step);
 const pos=id=>({x:n.x0+(id%n.nx)*n.step,y:n.y0+Math.floor(id/n.nx)*n.step,height:n.heights[id]});
 const s=idx(start),goal=idx(end),ep=pos(goal);
 const heuristic=id=>{const p=pos(id);return Math.hypot(p.x-ep.x,p.y-ep.y)/n.step;};
 const stand=id=>{if(id<0||id>=N)return false;if(!valid[id]){const p=pos(id);valid[id]=p.height!==null&&w.canStand(p.x,p.y)?1:-1;}return valid[id]>0;};
 if(!stand(s)||!stand(goal))throw new Error('route endpoint has no capsule clearance');
 cost[s]=0;q.push({id:s,score:heuristic(s),cost:0});let expanded=0;
 while(q.items.length){
  const entry=q.pop(),id=entry.id;if(entry.cost!==cost[id])continue;
  if(id===goal){const path=[];for(let k=id;k!==-1;k=parent[k])path.push(pos(k));return {path:path.reverse(),expanded};}
  expanded++;
  const p=pos(id),col=id%n.nx;
  for(const next of [col>0?id-1:-1,col<n.nx-1?id+1:-1,id-n.nx,id+n.nx]){
   if(!stand(next)||Math.abs(n.heights[next]-p.height)>w.stepHeight)continue;
   const c=cost[id]+1;if(c>=cost[next])continue;
   // Validate the whole edge, including support and substep collision.
   const target=pos(next),m=w.move(p,target.x-p.x,target.y-p.y);
   if(Math.hypot(m.x-target.x,m.y-target.y)>.025)continue;
   parent[next]=id;cost[next]=c;q.push({id:next,score:c+heuristic(next),cost:c});
  }
 }
 throw new Error('No capsule route after '+expanded+' cells');
}

export const routePoints={stairs:[1,15],west_street:[-2.25,-88.5],junction:[1.75,-25.5],north_lane:[-25.5,-19.5],parking:[29.25,-8],gate_front:[41.5,-9.5],gate_back:[51.5,-9.5],court:[67,-9.5],hozomon_back:[83,-9.5]};
export const routePairs=[['stairs','junction'],['junction','west_street'],['junction','north_lane'],['junction','parking'],['parking','gate_front'],['gate_front','gate_back'],['gate_back','court'],['court','hozomon_back']];

export function verifyRoutes(w){
 const report=[];
 for(const [a,b] of routePairs){
  const t=performance.now();
  try{
   const spawn=key=>{const [x,y]=routePoints[key];return w.findSpawn(x,y,1);};
   const start=spawn(a),end=spawn(b);if(!start||!end)throw new Error('no nearby spawn');
   const {path,expanded}=findRoute(w,start,end);
   for(const way of [path,[...path].reverse()]){
    let p={...way[0]};for(const target of way.slice(1)){p=w.move(p,target.x-p.x,target.y-p.y);if(Math.hypot(p.x-target.x,p.y-target.y)>.03)throw new Error('return blocked at '+JSON.stringify(p));}
   }
   report.push({from:a,to:b,ok:true,metres:(path.length-1)*w.nav.step,expanded,ms:performance.now()-t,path});
  }catch(e){report.push({from:a,to:b,ok:false,error:e.message,ms:performance.now()-t});}
  console.log(JSON.stringify({...report.at(-1),path:undefined}));
 }
 return report;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const root=new URL('../web/',import.meta.url),n=JSON.parse(fs.readFileSync(new URL('navigation.json',root))),b=fs.readFileSync(new URL('collision.bin',root));
 const w=new WalkWorld(n,new Float32Array(b.buffer,b.byteOffset,b.byteLength/4));
 const report=verifyRoutes(w);fs.writeFileSync(new URL('../../../../output/tokyo-verification/routes.json',import.meta.url),JSON.stringify(report,null,2));
 if(report.some(r=>!r.ok))process.exitCode=1;
}

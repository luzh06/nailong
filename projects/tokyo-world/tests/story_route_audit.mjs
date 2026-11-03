// 剧情路线可达性审计：用浏览器同一套 WalkWorld（胶囊碰撞）检查游戏层用到的每个点能否站立、能否互相走到，
// 并从出生点泛洪，列出“看起来能走、实际进不去”的区域。输出 output/tokyo-verification/story-route-audit.json。
// 用法：node projects/tokyo-world/tests/story_route_audit.mjs
import fs from 'node:fs';
import {WalkWorld} from '../web/collision.mjs';
import {findRoute} from '../scripts/verify_routes.mjs';

const root=new URL('../web/',import.meta.url);
const nav=JSON.parse(fs.readFileSync(new URL('navigation.json',root)));
const bin=fs.readFileSync(new URL('collision.bin',root));
const w=new WalkWorld(nav,new Float32Array(bin.buffer,bin.byteOffset,bin.byteLength/4));

// 与 web/game/story-data.mjs 保持一致
const P={spawn:[1.2,15.6],tokyo01_view:[1.2,12.5],junction:[1.75,-25.5],sakura_npc:[31.6,-16.2],sakura_view:[30.5,-15],gate_front:[41.5,-9.5],court_trigger:[56,-9.5],fireworks_npc:[56,-6.6],door:[66.5,-9.5]};
const legs=[['spawn','tokyo01_view'],['tokyo01_view','junction'],['junction','sakura_view'],['sakura_view','sakura_npc'],['sakura_view','gate_front'],['gate_front','court_trigger'],['court_trigger','fireworks_npc'],['court_trigger','door']];

const out={points:{},legs:[],islands:[]};
for(const [k,[x,y]] of Object.entries(P)){const s=w.findSpawn(x,y,1.5);out.points[k]={x,y,canStand:w.canStand(x,y),nearest:s&&{x:+s.x.toFixed(2),y:+s.y.toFixed(2),offset:+Math.hypot(s.x-x,s.y-y).toFixed(2)}};}
for(const [a,b] of legs){const t=performance.now();
 try{const s=w.findSpawn(...P[a],1.5),e=w.findSpawn(...P[b],1.5);if(!s||!e)throw new Error('端点附近无可站立位置');
  const {path}=findRoute(w,s,e),len=(path.length-1)*nav.step,direct=Math.hypot(e.x-s.x,e.y-s.y);
  out.legs.push({from:a,to:b,ok:true,metres:+len.toFixed(1),direct:+direct.toFixed(1),detour:+(len/Math.max(direct,.1)).toFixed(2),ms:Math.round(performance.now()-t)});}
 catch(err){out.legs.push({from:a,to:b,ok:false,error:err.message});}
 console.log(JSON.stringify(out.legs.at(-1)));}

// 泛洪：只用“能站 + 台阶高差”判断（不逐边做胶囊扫掠，偏乐观），找出与出生点不连通的可站立区域
const {nx,ny,step,x0,y0,heights}=nav,N=nx*ny,stand=new Int8Array(N),seen=new Uint8Array(N);
const pos=id=>[x0+(id%nx)*step,y0+Math.floor(id/nx)*step];
for(let id=0;id<N;id+=1){if(heights[id]===null)continue;const [x,y]=pos(id);stand[id]=w.canStand(x,y)?1:0;}
const comp=new Int32Array(N).fill(-1),sizes=[];
for(let id=0;id<N;id++){if(!stand[id]||comp[id]>=0)continue;const c=sizes.length;let size=0,minx=1e9,maxx=-1e9,miny=1e9,maxy=-1e9,hs=0,hmin=1e9;const q=[id];comp[id]=c;
 while(q.length){const k=q.pop();size++;hs+=heights[k];hmin=Math.min(hmin,heights[k]);const [x,y]=pos(k);minx=Math.min(minx,x);maxx=Math.max(maxx,x);miny=Math.min(miny,y);maxy=Math.max(maxy,y);const col=k%nx;
  for(const n of [col>0?k-1:-1,col<nx-1?k+1:-1,k-nx,k+nx]){if(n<0||n>=N||!stand[n]||comp[n]>=0)continue;if(Math.abs(heights[n]-heights[k])>w.stepHeight)continue;comp[n]=c;q.push(n);}}
 sizes.push({c,cells:size,area:+(size*step*step).toFixed(1),bbox:{x:[+minx.toFixed(1),+maxx.toFixed(1)],y:[+miny.toFixed(1),+maxy.toFixed(1)]},avgH:+(hs/size).toFixed(2),minH:+hmin.toFixed(2)});}
const sp=w.findSpawn(...P.spawn,1.5),spId=Math.round((sp.y-y0)/step)*nx+Math.round((sp.x-x0)/step),main=comp[spId];
out.mainArea=sizes[main]?.area;
// 与主区域相邻地面的高差：低于 1.2 米视为“地面级孤岛”（可能被隐形墙/栏杆/道具围住），高的多半是屋顶
const groundNear=s=>{let best=null;for(let id=0;id<N;id++){if(comp[id]!==main)continue;const [x,y]=pos(id);if(x<s.bbox.x[0]-3||x>s.bbox.x[1]+3||y<s.bbox.y[0]-3||y>s.bbox.y[1]+3)continue;best=best===null?heights[id]:Math.min(best,heights[id]);}return best;};
out.islands=sizes.filter(s=>s.c!==main&&s.area>=4).map(s=>{const g=groundNear(s);return{...s,groundNearby:g,kind:g!==null&&s.minH-g<1.2?'地面级（可疑）':'屋顶/高台'};}).sort((a,b)=>b.area-a.area).slice(0,40);
fs.mkdirSync(new URL('../../../../output/tokyo-verification/',import.meta.url),{recursive:true});
const file=new URL('../../../../output/tokyo-verification/story-route-audit.json',import.meta.url);
fs.writeFileSync(file,JSON.stringify(out,null,1));
console.log('main area m2',out.mainArea,'islands>=4m2',out.islands.length);
for(const i of out.islands.filter(i=>i.kind.startsWith('地面')))console.log('island',JSON.stringify(i));
console.log(JSON.stringify(out.points));

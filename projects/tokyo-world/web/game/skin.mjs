// 程序化绑骨与步态：给没有骨骼的静态人物网格在载入时建骨架、算蒙皮权重，并每帧驱动走路/站立/说话动作。
// 四个模型都是约 1.7 米的 A 字站姿（手臂在 0.75–1.05 米处与躯干分开，手在 x≈±0.28 米）；
// 关节位置从网格横截面自动量取，量不到时用人体比例兜底。人物正面朝 +Z。
import * as THREE from 'three';

const H=1.7;// 模型统一身高（导出时已归一）

// ---------- 量取关节 ----------
function measure(pos){
 const n=pos.count,v=new THREE.Vector3();
 const slice=(y0,y1,f)=>{for(let i=0;i<n;i++){v.fromBufferAttribute(pos,i);if(v.y>=y0&&v.y<y1)f(v);}};
 // 肩：1.30 米处躯干半宽向内收一点
 let half=0;slice(1.28,1.32,p=>{half=Math.max(half,Math.abs(p.x));});
 const shoulderX=THREE.MathUtils.clamp(half-.055,.13,.24);
 // 手腕：0.80–0.90 米处最外侧的一簇（手臂与腿分开的那一段）
 const outer=side=>{const xs=[];slice(.8,.9,p=>{if(p.x*side>0)xs.push(Math.abs(p.x));});xs.sort((a,b)=>b-a);
  if(!xs.length)return shoulderX+.09;const c=[xs[0]];for(let i=1;i<xs.length;i++){if(xs[i-1]-xs[i]>.02)break;c.push(xs[i]);}
  const m=c.reduce((a,b)=>a+b,0)/c.length;return m>shoulderX-.01?m:shoulderX+.09;};
 // 腿：0.25–0.35 米处一侧顶点的平均 x
 const leg=side=>{let s=0,k=0;slice(.25,.35,p=>{if(p.x*side>.01){s+=Math.abs(p.x);k++;}});return k?THREE.MathUtils.clamp(s/k,.06,.12):.085;};
 return{shoulderX,wristL:outer(1),wristR:outer(-1),legL:leg(1),legR:leg(-1)};
}

// ---------- 骨架定义 ----------
// 每根骨头：关节位置（模型空间）、父骨、权重用的线段终点与半径、可影响的身体区域
function skeletonDef(m){
 const d={};
 const add=(name,parent,joint,end,radius,zone)=>{d[name]={name,parent,joint:new THREE.Vector3(...joint),end:new THREE.Vector3(...end),radius,zone};};
 add('hips',null,[0,.95,0],[0,1.05,0],.17,'core');
 add('spine','hips',[0,1.05,0],[0,1.22,0],.16,'core');
 add('chest','spine',[0,1.22,0],[0,1.42,0],.17,'core');
 add('neck','chest',[0,1.42,0],[0,1.5,0],.065,'core');
 add('head','neck',[0,1.5,0],[0,1.72,0],.12,'core');
 for(const [s,side] of [['L',1],['R',-1]]){
  const sx=m.shoulderX*side,wx=(side>0?m.wristL:m.wristR)*side,ex=(sx+wx)/2+.015*side,lx=(side>0?m.legL:m.legR)*side;
  add('upper'+s,'chest',[sx,1.36,0],[ex,1.06,-.01],.06,'arm'+s);
  add('fore'+s,'upper'+s,[ex,1.06,-.01],[wx,.83,.01],.05,'arm'+s);
  add('hand'+s,'fore'+s,[wx,.83,.01],[wx+.01*side,.68,.02],.055,'arm'+s);
  add('thigh'+s,'hips',[lx,.9,0],[lx,.48,.01],.095,'leg'+s);
  add('shin'+s,'thigh'+s,[lx,.48,.01],[lx,.08,-.01],.07,'leg'+s);
  add('foot'+s,'shin'+s,[lx,.08,-.01],[lx,.02,.13],.06,'leg'+s);
 }
 return d;
}

const seg=new THREE.Line3(),cp=new THREE.Vector3();
function segDist(p,a,b){seg.set(a,b);seg.closestPointToPoint(p,true,cp);return p.distanceTo(cp);}

// ---------- 蒙皮权重 ----------
function computeWeights(pos,def,names){
 const n=pos.count,idx=new Uint16Array(n*4),wts=new Float32Array(n*4),p=new THREE.Vector3(),lowSide=new Int8Array(n);
 const bones=names.map(k=>def[k]);
 const hipY=.9,cand=new Array(bones.length),legs={shinL:def.shinL,footL:def.footL,shinR:def.shinR,footR:def.footR};
 for(let i=0;i<n;i++){
  // 中线附近两腿共享权重只用于膝盖以上（裙摆、裆部）；小腿和鞋严格按侧，否则并拢的双脚会被互相拉扯
  p.fromBufferAttribute(pos,i);const center=Math.abs(p.x)<.035&&p.y>.58;
  let side=p.x>=0?'L':'R';
  // 膝盖以下：按离哪条小腿/脚更近来分左右（内八字的鞋尖可能越过中线）
  if(p.y<=.58){const dl=Math.min(segDist(p,legs.shinL.joint,legs.shinL.end),segDist(p,legs.footL.joint,legs.footL.end)),dr=Math.min(segDist(p,legs.shinR.joint,legs.shinR.end),segDist(p,legs.footR.joint,legs.footR.end));side=dl<=dr?'L':'R';lowSide[i]=side==='L'?1:-1;}
  let m=0;
  for(let b=0;b<bones.length;b++){const B=bones[b],z=B.zone;
   // 区域限制：腿骨只管髋部以下同侧（中线附近两侧都可，裙摆不撕开）；手臂只管同侧
   if(z.startsWith('leg')&&(p.y>hipY+.1||(z!=='leg'+side&&!center)))continue;
   if(z.startsWith('arm')&&(z!=='arm'+side||p.y<.6))continue;
   const dn=segDist(p,B.joint,B.end)/B.radius;
   cand[m++]=[b,Math.exp(-dn*dn*1.6)+1e-6*(z==='core'?1:0)];}
  cand.length=m;cand.sort((a,b)=>b[1]-a[1]);
  let sum=0;for(let k=0;k<4&&k<m;k++)sum+=cand[k][1];
  for(let k=0;k<4;k++){if(k<m&&sum>0){idx[i*4+k]=cand[k][0];wts[i*4+k]=cand[k][1]/sum;}}
  if(sum<=0){idx[i*4]=0;wts[i*4]=1;}
 }
 return{idx,wts,lowSide};
}

// ---------- 建骨与替换网格 ----------
export function rigStaticCharacter(model){
 model.updateMatrixWorld(true);
 let mesh=null;model.traverse(o=>{if(o.isMesh&&!mesh)mesh=o;});
 if(!mesh)return null;
 const inv=new THREE.Matrix4().copy(model.matrixWorld).invert();
 const geo=mesh.geometry.clone();geo.applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv,mesh.matrixWorld));
 const pos=geo.attributes.position;
 const m=measure(pos),def=skeletonDef(m),names=Object.keys(def);
 const bones={};
 for(const k of names){const b=new THREE.Bone();b.name=k;bones[k]=b;}
 for(const k of names){const D=def[k],b=bones[k];
  if(D.parent){b.position.copy(D.joint).sub(def[D.parent].joint);bones[D.parent].add(b);}else b.position.copy(D.joint);}
 const {idx,wts,lowSide}=computeWeights(pos,def,names);
 // 减面时两只鞋之间可能连出“桥”三角形：膝下两角分属左右腿的三角形会被拉成细条，直接去掉
 if(geo.index){const a=geo.index.array,keep=[];for(let t=0;t<a.length;t+=3){const s0=lowSide[a[t]],s1=lowSide[a[t+1]],s2=lowSide[a[t+2]];
  if(s0&&s1&&s2&&(s0!==s1||s1!==s2))continue;keep.push(a[t],a[t+1],a[t+2]);}
  if(keep.length<a.length)geo.setIndex(keep);}
 geo.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(idx,4));
 geo.setAttribute('skinWeight',new THREE.Float32BufferAttribute(wts,4));
 const skinned=new THREE.SkinnedMesh(geo,mesh.material);
 skinned.name=mesh.name+'_skinned';skinned.castShadow=mesh.castShadow;skinned.receiveShadow=mesh.receiveShadow;skinned.frustumCulled=false;
 skinned.add(bones.hips);skinned.updateMatrixWorld(true);
 skinned.bind(new THREE.Skeleton(names.map(k=>bones[k])));
 mesh.parent.remove(mesh);model.add(skinned);
 return{bones,measure:m,mesh:skinned};
}

// ---------- 步态 ----------
// 角度单位弧度；绕骨骼局部 X 轴为前后摆（负值向前，人物朝 +Z）。
export class Gait{
 constructor(rig){this.b=rig.bones;this.phase=0;this.t=Math.random()*10;this.walk=0;this.talk=0;this.base={};
  for(const [k,b] of Object.entries(this.b))this.base[k]={p:b.position.clone()};}
 // speed：米/秒；talking：是否在说话
 update(dt,speed,talking){
  const b=this.b,t=(this.t+=dt);
  const target=THREE.MathUtils.clamp(speed/1.6,0,1.35);
  this.walk+=(target-this.walk)*(1-Math.exp(-dt*7));
  this.talk+=((talking?1:0)-this.talk)*(1-Math.exp(-dt*4));
  const w=Math.min(1,this.walk),run=Math.max(0,this.walk-1)/.35;
  // 步频：慢走约 1.3 米一个完整周期，越快步子越大（快走约 1.85 米），避免小碎步
  const stride=1.3+.35*Math.max(0,speed-1.8);
  this.phase+=dt*Math.max(speed,0)/stride*Math.PI*2;
  const ph=this.phase,s=Math.sin(ph),c=Math.cos(ph);
  const A=(.42+.1*run)*w,K=(.95+.2*run)*w;
  // 腿：大腿摆、膝盖在向前摆时弯、脚掌保持贴地
  const legs=[['L',1],['R',-1]];
  for(const [S,dir] of legs){const sw=s*dir,vel=c*dir;
   const thigh=-A*sw-.03*w;
   const knee=.06*w+K*Math.pow(Math.max(0,vel),1.6)*.85+.12*w*Math.max(0,-sw);
   b['thigh'+S].rotation.set(thigh,0,.03*dir*w);
   b['shin'+S].rotation.set(knee,0,0);
   // 脚掌：抵消大腿与小腿的角度、保持大致水平，限制幅度以免鞋子被拉伸
   b['foot'+S].rotation.set(THREE.MathUtils.clamp(-(thigh+knee)*.4+.1*w*Math.max(0,sw),-.35,.3),0,0);}
  // 骨盆：经过位时最高，左右转、侧倾；躯干反向扭转，略前倾
  const idleSway=Math.sin(t*.7)*(1-w);
  b.hips.position.y=this.base.hips.p.y+(.022*Math.cos(2*ph)-.012)*w+Math.sin(t*1.6)*.002*(1-w);
  b.hips.position.x=this.base.hips.p.x+.012*s*w+idleSway*.008;
  b.hips.rotation.set(0,.11*s*w,.035*s*w+idleSway*.015);
  const breathe=Math.sin(t*1.7);
  b.spine.rotation.set(.05*w+.08*run,-.06*s*w,-.02*s*w);
  b.chest.rotation.set(.012*breathe*(1-w),-.08*s*w,0);
  b.neck.rotation.set(-.03*w+this.talk*.04*Math.sin(t*2.6),.06*s*w,0);
  b.head.rotation.set(-.02*w+this.talk*.05*Math.sin(t*2.6+.6),.04*s*w+this.talk*.08*Math.sin(t*.9),this.talk*.03*Math.sin(t*1.3));
  // 手臂：与对侧腿同步前后摆，前摆时肘部多弯；站立时自然下垂、轻微晃动
  for(const [S,dir] of legs){const sw=s*dir;
   const B=(.36+.1*run)*w;
   const gesture=S==='R'?this.talk:0;
   b['upper'+S].rotation.set(B*sw-.02-gesture*(.25+.08*Math.sin(t*2.2)),0,dir*(.05*w-.02*(1-w)+idleSway*.01)+dir*gesture*.12);
   b['fore'+S].rotation.set(-(.1+.28*w*Math.max(0,-sw)+.15*run)-gesture*(.55+.12*Math.sin(t*2.2+.8)),0,0);
   b['hand'+S].rotation.set(-.08,0,0);}
 }
}

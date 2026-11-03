// 程序生成的樱花树：分枝树干 + 花簇卡片（实例化）+ 飘落花瓣 + 树下落花。
// Codex 交付 web/models/sakura.glb 后由 main 自动改用模型，本文件保留飘落花瓣与落花。
import * as THREE from 'three';

let seed=7;const rnd=()=>{seed=(seed*16807)%2147483647;return(seed-1)/2147483646;};
const R=(a,b)=>a+(b-a)*rnd();

function canvasTex(w,h,draw,srgb=true){const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);const t=new THREE.CanvasTexture(c);if(srgb)t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=4;return t;}
function flower(g,x,y,r,col,rot){g.save();g.translate(x,y);g.rotate(rot);for(let i=0;i<5;i++){g.rotate(Math.PI*2/5);g.beginPath();g.ellipse(0,-r*.55,r*.36,r*.55,0,0,Math.PI*2);g.fillStyle=col;g.fill();}
 g.beginPath();g.arc(0,0,r*.18,0,Math.PI*2);g.fillStyle='#c4506a';g.fill();g.restore();}
// 一张花簇：几十朵五瓣花叠成的不规则团块，带透明边
function blossomTexture(){return canvasTex(256,256,(g,w,h)=>{const cols=['#fbe3ea','#f7cfdc','#f4c0d1','#fff1f4','#efb3c6','#f9d9e3'];
 for(let i=0;i<130;i++){const a=rnd()*Math.PI*2,d=Math.pow(rnd(),.8)*78;const x=128+Math.cos(a)*d,y=128+Math.sin(a)*d*.85;flower(g,x,y,R(9,17),cols[i%cols.length],rnd()*6);}
 for(let i=0;i<26;i++){const x=R(30,226),y=R(30,226);g.fillStyle='rgba(120,150,80,.55)';g.beginPath();g.ellipse(x,y,R(3,6),R(1.5,3),rnd()*3,0,7);g.fill();}});}
function petalTexture(){return canvasTex(32,32,(g)=>{g.beginPath();g.ellipse(16,16,7,13,0,0,Math.PI*2);g.fillStyle='#f8d3de';g.fill();g.beginPath();g.moveTo(16,2);g.lineTo(13,6);g.lineTo(19,6);g.fillStyle='rgba(0,0,0,0)';g.globalCompositeOperation='destination-out';g.fill();});}
function barkTexture(){return canvasTex(128,256,(g,w,h)=>{g.fillStyle='#4a362c';g.fillRect(0,0,w,h);for(let i=0;i<260;i++){g.fillStyle=`rgba(${rnd()<.5?20:95},${rnd()<.5?14:70},${rnd()<.5?10:58},${R(.15,.45)})`;g.fillRect(R(0,w),R(0,h),R(1,3),R(10,60));}
 for(let i=0;i<18;i++){g.fillStyle='rgba(30,22,18,.6)';g.fillRect(0,R(0,h),w,R(1,2.5));}});}
function groundPetals(){return canvasTex(512,512,(g,w,h)=>{const cols=['#f6cfda','#fbe2e9','#efb7c8'];for(let i=0;i<1600;i++){const a=rnd()*Math.PI*2,d=Math.pow(rnd(),.8)*240,x=256+Math.cos(a)*d,y=256+Math.sin(a)*d;
 g.globalAlpha=Math.max(0,1-d/250)*R(.5,1);g.beginPath();g.ellipse(x,y,R(2,4),R(4,7),rnd()*6,0,7);g.fillStyle=cols[i%3];g.fill();}});}

function mergeGeometries(list){let vc=0,ic=0;for(const g of list){vc+=g.attributes.position.count;ic+=g.index.count;}
 const pos=new Float32Array(vc*3),nor=new Float32Array(vc*3),uv=new Float32Array(vc*2),idx=new Uint32Array(ic);let vo=0,io=0;
 for(const g of list){pos.set(g.attributes.position.array,vo*3);nor.set(g.attributes.normal.array,vo*3);uv.set(g.attributes.uv.array,vo*2);
  const ia=g.index.array;for(let i=0;i<ia.length;i++)idx[io+i]=ia[i]+vo;vo+=g.attributes.position.count;io+=ia.length;g.dispose();}
 const out=new THREE.BufferGeometry();out.setAttribute('position',new THREE.BufferAttribute(pos,3));out.setAttribute('normal',new THREE.BufferAttribute(nor,3));out.setAttribute('uv',new THREE.BufferAttribute(uv,2));out.setIndex(new THREE.BufferAttribute(idx,1));return out;}

export function createSakura({withTree=true}={}){
 seed=7;const group=new THREE.Group();group.name='sakura';
 const tips=[];
 if(withTree){
  const tubes=[];
  // 递归分枝：粗干先斜出，再分成 2–3 支向外上方展开，形成伞状树冠
  function branch(start,dir,len,rad,depth){
   const pts=[start.clone()];let p=start.clone(),d=dir.clone();
   for(let i=1;i<=3;i++){d.add(new THREE.Vector3(R(-.25,.25),R(-.12,.08),R(-.25,.25))).normalize();p=p.clone().addScaledVector(d,len/3);pts.push(p);}
   const curve=new THREE.CatmullRomCurve3(pts);const g=new THREE.TubeGeometry(curve,6,rad,depth<2?9:6,false);
   // 渐细：沿管长缩小半径
   const pa=g.attributes.position,center=new THREE.Vector3(),v=new THREE.Vector3();
   for(let i=0;i<pa.count;i++){const seg=Math.floor(i/((depth<2?9:6)+1))/6;center.copy(curve.getPointAt(Math.min(1,seg)));v.fromBufferAttribute(pa,i).sub(center).multiplyScalar(1-seg*.45);v.add(center);pa.setXYZ(i,v.x,v.y,v.z);}
   tubes.push(g);
   if(depth>=4||len<.7){tips.push({p,d});return;}
   const n=depth===0?3:rnd()<.5?2:3;
   for(let k=0;k<n;k++){const a=(k/n)*Math.PI*2+R(-.5,.5)+depth;const nd=new THREE.Vector3(Math.cos(a),R(.35,.9)-depth*.08,Math.sin(a)).normalize().lerp(d,.35).normalize();
    branch(p,nd,len*R(.62,.78),rad*.62,depth+1);if(depth>=2)tips.push({p:p.clone().addScaledVector(nd,len*.3),d:nd});}
  }
  branch(new THREE.Vector3(0,0,0),new THREE.Vector3(.12,1,.05).normalize(),3.1,.42,0);
  const bark=new THREE.MeshStandardMaterial({map:barkTexture(),color:0xb8a698,roughness:.95,metalness:0});
  const trunk=new THREE.Mesh(mergeGeometries(tubes),bark);trunk.receiveShadow=true;group.add(trunk);
  // 花簇：在枝梢附近撒卡片，朝向随机但偏向上方，靠外的更大
  const tex=blossomTexture();
  const mat=new THREE.MeshStandardMaterial({map:tex,alphaTest:.42,side:THREE.DoubleSide,roughness:.85,metalness:0,emissive:new THREE.Color(.95,.62,.7),emissiveIntensity:.22,emissiveMap:tex});
  const m=new THREE.Matrix4(),q=new THREE.Quaternion(),e=new THREE.Euler(),s=new THREE.Vector3(),pos=new THREE.Vector3(),col=new THREE.Color();
  // 体积：一团团起伏的花云（低细分球体，顶点扰动），先撑出树冠轮廓
  const puffGeo=new THREE.SphereGeometry(1,16,12);{const p=puffGeo.attributes.position,v=new THREE.Vector3();for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i);v.multiplyScalar(1+Math.sin(v.x*5.1)*.08+Math.sin(v.y*6.3+v.z*4.7)*.08);p.setXYZ(i,v.x,v.y*.8,v.z);}puffGeo.computeVertexNormals();}
  const PUFF=640,puffs=new THREE.InstancedMesh(puffGeo,new THREE.MeshStandardMaterial({color:0xffffff,roughness:.92,metalness:0,emissive:new THREE.Color(.85,.5,.6),emissiveIntensity:.12}),PUFF);
  for(let i=0;i<PUFF;i++){const t=tips[i%tips.length];pos.copy(t.p).add(new THREE.Vector3(R(-1,1),R(-.3,.6),R(-1,1)).multiplyScalar(R(.1,.85)));
   q.setFromEuler(e.set(R(0,3),R(0,6),R(0,3)));const sz=R(.26,.5);s.set(sz,sz,sz);m.compose(pos,q,s);puffs.setMatrixAt(i,m);
   col.setHSL(.94+R(-.015,.015),R(.55,.75),R(.74,.84));puffs.setColorAt(i,col);}
  puffs.receiveShadow=true;group.add(puffs);
  // 细节：贴在花云表面的小花簇卡片，给出一朵朵花的质感
  const COUNT=2200,card=new THREE.PlaneGeometry(1,1),inst=new THREE.InstancedMesh(card,mat,COUNT);
  for(let i=0;i<COUNT;i++){const t=tips[i%tips.length];pos.copy(t.p).add(new THREE.Vector3(R(-1,1),R(-.45,.7),R(-1,1)).normalize().multiplyScalar(R(.45,1.05)));
   e.set(R(-1.3,-.3),R(0,6.3),R(-.4,.4));q.setFromEuler(e);const sz=R(.32,.62);s.set(sz,sz,sz);m.compose(pos,q,s);inst.setMatrixAt(i,m);
   col.setHSL(.95+R(-.02,.02),R(.45,.7),R(.86,.97));inst.setColorAt(i,col);}
  inst.receiveShadow=true;group.add(inst);group.userData.canopy=inst;
 }
 // 树下落花
 const fall=new THREE.Mesh(new THREE.CircleGeometry(4.6,48),new THREE.MeshStandardMaterial({map:groundPetals(),transparent:true,depthWrite:false,roughness:.9,polygonOffset:true,polygonOffsetFactor:-3}));
 fall.rotation.x=-Math.PI/2;fall.position.y=.025;fall.renderOrder=1;group.add(fall);
 // 飘落花瓣
 const P=260,petals=new THREE.InstancedMesh(new THREE.PlaneGeometry(.045,.07),new THREE.MeshStandardMaterial({map:petalTexture(),alphaTest:.3,side:THREE.DoubleSide,roughness:.8,emissive:new THREE.Color(.9,.6,.68),emissiveIntensity:.25}),P);
 const state=Array.from({length:P},()=>({p:new THREE.Vector3(R(-3.5,3.5),R(.2,6),R(-3.5,3.5)),v:new THREE.Vector3(R(.1,.35),-R(.25,.55),R(-.1,.15)),r:new THREE.Vector3(rnd()*6,rnd()*6,rnd()*6),w:R(1,3)}));
 petals.frustumCulled=false;group.add(petals);
 const mm=new THREE.Matrix4(),qq=new THREE.Quaternion(),ee=new THREE.Euler(),one=new THREE.Vector3(1,1,1);let time=0;
 group.userData.update=(dt)=>{time+=dt;const gust=.6+.4*Math.sin(time*.35);
  for(let i=0;i<P;i++){const s=state[i];s.p.x+=(s.v.x*gust+Math.sin(time*s.w+i)*.12)*dt;s.p.y+=s.v.y*dt;s.p.z+=(s.v.z+Math.cos(time*s.w*.8+i)*.12)*dt;
   s.r.x+=dt*s.w*1.7;s.r.y+=dt*s.w;if(s.p.y<.03){s.p.set(R(-3.2,3.2),R(4.2,6.2),R(-3.2,3.2));}
   ee.set(s.r.x,s.r.y,s.r.z);qq.setFromEuler(ee);mm.compose(s.p,qq,one);petals.setMatrixAt(i,mm);}
  petals.instanceMatrix.needsUpdate=true;};
 return group;
}

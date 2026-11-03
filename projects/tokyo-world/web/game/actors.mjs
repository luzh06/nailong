// 角色：加载 GLB、按身高缩放、软阴影、动画。
// GLB 带 idle/walk/talk 动画时用 AnimationMixer；没有骨骼时用程序化动作（呼吸、步行起伏、侧摆、转身）。
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/GLTFLoader.js';
import {clone as cloneSkinned} from 'three/addons/SkeletonUtils.js';
import {ROLES} from './story-data.mjs';

const loader=new GLTFLoader();
const cache=new Map();
function loadGltf(id){if(!cache.has(id))cache.set(id,loader.loadAsync(new URL(`../models/characters/${id}.glb`,import.meta.url).href));return cache.get(id);}
export function preloadActor(id){return loadGltf(id);}

let blobTex=null;
function blobTexture(){if(blobTex)return blobTex;const c=document.createElement('canvas');c.width=c.height=128;const g=c.getContext('2d');
 const r=g.createRadialGradient(64,64,4,64,64,62);r.addColorStop(0,'rgba(0,0,0,.62)');r.addColorStop(.5,'rgba(0,0,0,.32)');r.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=r;g.fillRect(0,0,128,128);
 blobTex=new THREE.CanvasTexture(c);return blobTex;}

const damp=(a,b,k,dt)=>a+(b-a)*(1-Math.exp(-k*dt));
function angleDamp(a,b,k,dt){let d=b-a;while(d>Math.PI)d-=2*Math.PI;while(d<-Math.PI)d+=2*Math.PI;return a+d*(1-Math.exp(-k*dt));}

export class Actor{
 constructor(id,gltf){
  this.id=id;this.role=ROLES[id];
  this.root=new THREE.Group();this.root.name='actor_'+id;
  this.body=new THREE.Group();this.root.add(this.body);
  const model=gltf.scene;const s=this.role.height/1.7;model.scale.setScalar(s);
  model.traverse(o=>{if(!o.isMesh)return;o.castShadow=false;o.receiveShadow=true;o.frustumCulled=true;
   const m=o.material;if(m){m.envMapIntensity=.55;if(m.metalnessMap)m.metalness=.6;m.roughness=Math.max(m.roughness??1,.55);}});
  this.body.add(model);this.model=model;
  const blob=new THREE.Mesh(new THREE.PlaneGeometry(1.1,1.1),new THREE.MeshBasicMaterial({map:blobTexture(),transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2}));
  blob.rotation.x=-Math.PI/2;blob.position.y=.02;blob.renderOrder=2;this.root.add(blob);this.blob=blob;
  this.clips=new Map(gltf.animations.map(a=>[a.name,a]));
  this.rigged=this.clips.has('idle')&&this.clips.has('walk');
  if(this.rigged){this.mixer=new THREE.AnimationMixer(model);this.actions={};for(const [k,c] of this.clips)this.actions[k]=this.mixer.clipAction(c);this.current=null;this.play('idle');}
  this.facing=0;this.targetFacing=0;this.speed=0;this.phase=Math.random()*10;this.mode='idle';this.time=0;this.talking=false;this.opacity=1;
 }
 play(name,fade=.25){if(!this.rigged)return;const a=this.actions[name]||this.actions.idle;if(this.current===a)return;a.reset().fadeIn(fade).play();this.current?.fadeOut(fade);this.current=a;}
 // 世界位置：three 坐标
 place(x,h,z){this.root.position.set(x,h,z);}
 face(angle,instant=false){this.targetFacing=angle;if(instant)this.facing=angle;}
 faceToward(x,z,instant=false){this.face(Math.atan2(x-this.root.position.x,z-this.root.position.z),instant);}
 setOpacity(v){this.opacity=v;this.model.traverse(o=>{if(!o.isMesh)return;o.material.transparent=v<1;o.material.opacity=v;o.material.depthWrite=v>=.99;});this.blob.material.opacity=v;this.root.visible=v>.01;}
 // speed：米/秒
 update(dt,speed=0){
  this.time+=dt;this.speed=damp(this.speed,speed,8,dt);
  this.facing=angleDamp(this.facing,this.targetFacing,speed>.1?10:6,dt);this.root.rotation.y=this.facing;
  if(this.rigged){
   this.play(this.speed>.25?'walk':this.talking&&this.actions.talk?'talk':'idle');
   if(this.current===this.actions.walk)this.current.timeScale=THREE.MathUtils.clamp(this.speed/1.8,.6,1.9);
   this.mixer.update(dt);return;
  }
  // 程序化：步频随速度；步行时上下起伏、左右侧摆、略前倾；站立时呼吸；说话时轻微点头
  const walkK=THREE.MathUtils.clamp(this.speed/1.8,0,1.6);
  this.phase+=dt*(walkK>.05?6.2*Math.min(1.3,.75+walkK*.35):0);
  const b=this.body;
  const bob=Math.abs(Math.sin(this.phase))*.035*Math.min(1,walkK);
  const breathe=Math.sin(this.time*1.6)*.004*(1-Math.min(1,walkK));
  b.position.y=bob;
  b.rotation.z=Math.sin(this.phase)*.035*Math.min(1,walkK);
  b.rotation.x=.06*Math.min(1,walkK)+(this.talking?Math.sin(this.time*2.4)*.018:0);
  b.rotation.y=Math.sin(this.phase)*.05*Math.min(1,walkK);
  b.scale.set(1-breathe*.5,1+breathe,1-breathe*.5);
  this.blob.scale.setScalar(1-bob*2);
 }
}

// 克隆场景保证同一模型可重复使用（带骨骼时需 SkeletonUtils 才能正确复制绑定）
export async function createActor(id){const g=await loadGltf(id);
 const scene=g.animations.length?cloneSkinned(g.scene):g.scene.clone(true);
 return new Actor(id,{scene,animations:g.animations});}

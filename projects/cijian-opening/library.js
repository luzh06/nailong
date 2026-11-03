import * as T from 'three';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {roles} from './roles.js';
import {resolveRole,canWalk,floorHeight,nearestWalkable,OpeningState} from './game-state.js';
import {disposeGraphs} from './lifecycle.js';
export function mountLibrary({root,roleId,onSelect}){
const events=new AbortController(),listen=(el,type,fn,opt={})=>el.addEventListener(type,fn,{...opt,signal:events.signal});
let disposed=false,frame;
const $=s=>root.querySelector(s),canvas=$('#library'),reduced=matchMedia('(prefers-reduced-motion:reduce)').matches;
let saved;try{saved=localStorage.getItem('cijian.selectedRole')}catch{}
const role=roles.find(r=>r.id===resolveRole('?role='+encodeURIComponent(roleId),saved));
try{localStorage.setItem('cijian.selectedRole',role.id)}catch{}
const currentURL=new URL(location);currentURL.searchParams.set('role',role.id);history.replaceState(null,'',currentURL);
const state=new OpeningState(),keys=new Set(),scene=new T.Scene();scene.background=new T.Color(0x241a11);
const renderer=new T.WebGLRenderer({canvas,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
const camera=new T.PerspectiveCamera(68,1,.04,80);
scene.add(new T.HemisphereLight(0xffedcf,0x514333,2.2));
const light=new T.DirectionalLight(0xffe1b5,2);light.position.set(-3,4,2);scene.add(light);
const player=new T.Vector3(),bookAnchor=new T.Vector3(2.18,-.48,2.28),spawn={x:-3.9,z:3.15};
const eyeHeight={JP:1.53,CN:1.70,FR:1.60,AU:1.79}[role.id];
const glow=new T.Group();glow.position.copy(bookAnchor);scene.add(glow);
const lightCanvas=document.createElement('canvas');lightCanvas.width=lightCanvas.height=128;const g=lightCanvas.getContext('2d'),grad=g.createRadialGradient(64,64,0,64,64,64);grad.addColorStop(0,'#ffe9abbb');grad.addColorStop(.35,'#f4c26244');grad.addColorStop(1,'#f4c26200');g.fillStyle=grad;g.fillRect(0,0,128,128);
const halo=new T.Sprite(new T.SpriteMaterial({map:new T.CanvasTexture(lightCanvas),depthWrite:false,blending:T.AdditiveBlending}));halo.scale.set(.8,.8,1);glow.add(halo);
const bookLight=new T.PointLight(0xffd89b,.65,1.8);glow.add(bookLight);
let nav,ready=false,yaw=0,pitch=0,drag=false,elapsed=0,lastHint=0;
const clock=new T.Clock(),forward=new T.Vector3(),right=new T.Vector3(),motion=new T.Vector3();
function resize(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight)}resize();listen(window,'resize',resize);
function clearKeys(){keys.clear();drag=false}listen(window,'blur',clearKeys);listen(document,'visibilitychange',clearKeys);
function releaseMouse(){if(document.pointerLockElement===canvas)document.exitPointerLock();clearKeys()}
function hint(text){$('#hint').textContent=text;lastHint=elapsed}
function updateCamera(){camera.position.copy(player);camera.position.y+=eyeHeight;camera.rotation.set(pitch,yaw,0,'YXZ')}
function reset(){
 if(!ready||state.phase!=='exploring')return;
 releaseMouse();const p=nearestWalkable(nav,spawn.x,spawn.z);player.set(p.x,floorHeight(nav,p.x,p.z),p.z);
 yaw=Math.atan2(-(bookAnchor.x-p.x),-(bookAnchor.z-p.z));pitch=-.06;updateCamera();
 canvas.focus();
}

async function load(){try{
 const loader=new GLTFLoader();$('#load-status').textContent='正在读取图书馆…';
 nav=await fetch('./navigation.json').then(r=>{if(!r.ok)throw Error('导航读取失败');return r.json()});
 const lib=await loader.loadAsync('./assets/library.glb');if(disposed){disposeGraphs(lib.scene);return;}scene.add(lib.scene);
 $('#load-status').textContent='正在放置古书…';
 const bookGLB=await loader.loadAsync('./assets/antique-book.glb');
 if(disposed){disposeGraphs(bookGLB.scene);return;}const book=bookGLB.scene;if(bookGLB.animations.length){const mixer=new T.AnimationMixer(book);mixer.clipAction(bookGLB.animations[0]).play();mixer.setTime(0)}
 const wrapper=new T.Group();wrapper.add(book);wrapper.scale.setScalar(1.3);wrapper.rotation.y=-2.18;wrapper.position.copy(bookAnchor);scene.add(wrapper);
 const center=new T.Box3().setFromObject(wrapper).getCenter(new T.Vector3());wrapper.position.add(bookAnchor.clone().sub(center));
 ready=true;state.ready();$('#loading').hidden=true;$('#book-marker').hidden=false;reset();
}catch(e){if(disposed)return;console.error(e);$('#load-status').textContent='图书馆素材未能读取';$('#loading small').textContent='请双击“启动开头.bat”重试，并保留 assets 资源目录。';$('#retry').hidden=false}}
$('#retry').onclick=()=>location.reload();
function interact(){
 if(!state.interact()){if(ready&&state.phase==='exploring')hint('请先走近发光的古书。');return}
 releaseMouse();$('#interact').hidden=true;$('#book-marker').hidden=true;$('#crosshair').hidden=true;$('#hint').textContent='';
 window.dispatchEvent(new CustomEvent('cijian:book-interacted',{detail:{role:role.id}}));
 if(reduced){finish();return}
 $('#cinematic').hidden=false;$('#skip').focus();const video=$('#book-video');video.currentTime=0;video.play().catch(()=>{$('#video-fallback').hidden=false});
}
function finish(){
 if(state.phase!=='reading')return;
 $('#book-video').pause();$('#cinematic').hidden=true;$('#video-fallback').hidden=true;state.finish();$('#complete').hidden=false;$('#replay').focus();
 try{sessionStorage.setItem('cijian.libraryCompleted',JSON.stringify({role:role.id,completed:true}))}catch{}
 window.dispatchEvent(new CustomEvent('cijian:library-complete',{detail:{role:role.id,nextScene:'tokyo',integrated:false}}));
}
$('#book-video').src='./assets/antique-sequence.mp4';
$('#interact').onclick=interact;$('#book-video').onended=finish;$('#book-video').onerror=()=>{if(state.phase==='reading')$('#video-fallback').hidden=false};$('#skip').onclick=finish;$('#continue').onclick=finish;
$('#replay').onclick=()=>{state.replay();$('#complete').hidden=true;$('#book-marker').hidden=false;$('#crosshair').hidden=false;reset()};
listen(window,'keydown',e=>{
 if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyF','Space'].includes(e.code)&&!['BUTTON','A'].includes(e.target.tagName))e.preventDefault();
 if(e.code==='KeyF'&&!e.repeat)interact();if(e.code==='Escape')releaseMouse();if(e.code==='KeyR'&&!e.repeat)reset();
 if(state.phase==='exploring')keys.add(e.code);
});listen(window,'keyup',e=>keys.delete(e.code));
listen(canvas,'pointerdown',()=>{
 if(state.phase!=='exploring')return;canvas.focus();drag=true;
 if(!document.pointerLockElement){try{const result=canvas.requestPointerLock();if(result?.catch)result.catch(()=>hint('按住鼠标拖动也可以转向。'))}catch{hint('按住鼠标拖动也可以转向。')}}
});
listen(document,'pointermove',e=>{
 if(state.phase!=='exploring'||!(document.pointerLockElement===canvas||drag))return;
 yaw-=e.movementX*.0025;pitch=T.MathUtils.clamp(pitch-e.movementY*.0025,-1.35,1.35);
});listen(document,'pointerup',()=>drag=false);listen(canvas,'pointercancel',()=>drag=false);
listen(document,'pointerlockchange',()=>{if(document.pointerLockElement!==canvas)clearKeys()});
root.querySelectorAll('[data-move]').forEach(b=>{listen(b,'pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(b.dataset.move)});for(const ev of ['pointerup','pointercancel','lostpointercapture'])listen(b,ev,()=>keys.delete(b.dataset.move))});
function tick(){
 if(disposed)return;frame=requestAnimationFrame(tick);const dt=Math.min(clock.getDelta(),.05);elapsed+=dt;if(!ready||state.phase!=='exploring')return;
 const v=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown')),h=Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft'));
 forward.set(-Math.sin(yaw),0,-Math.cos(yaw));right.set(Math.cos(yaw),0,-Math.sin(yaw));motion.copy(forward).multiplyScalar(v).addScaledVector(right,h);
 if(motion.lengthSq()){
  motion.normalize().multiplyScalar(1.7*dt);
  // Short substeps keep collision stable even after a slow frame.
  const n=Math.max(1,Math.ceil(motion.length()/.04));motion.divideScalar(n);
  for(let i=0;i<n;i++){if(canWalk(nav,player.x+motion.x,player.z))player.x+=motion.x;if(canWalk(nav,player.x,player.z+motion.z))player.z+=motion.z}
  player.y=floorHeight(nav,player.x,player.z);
 }
 const distance=Math.hypot(player.x-bookAnchor.x,player.z-bookAnchor.z),near=state.updateRange(distance);$('#interact').hidden=!near;
 glow.scale.setScalar(reduced?1:1+Math.sin(elapsed*2.2)*.06);halo.material.opacity=reduced?.7:.6+Math.sin(elapsed*2.2)*.15;
 updateCamera();renderer.render(scene,camera);
 const mark=bookAnchor.clone();mark.y+=.4;mark.project(camera);const marker=$('#book-marker');marker.hidden=near||mark.z>1||mark.z< -1;if(near)$('#hint').textContent='';
 marker.style.left=`${T.MathUtils.clamp((mark.x*.5+.5)*innerWidth,50,innerWidth-50)}px`;marker.style.top=`${T.MathUtils.clamp((-mark.y*.5+.5)*innerHeight,165,innerHeight-180)}px`;$('#distance').textContent=near?'按 F 交互':`${distance.toFixed(1)} m`;
 if(elapsed-lastHint>7)$('#hint').textContent='';
}
window.CijianLibrary={get ready(){return ready},get role(){return role.id},get phase(){return state.phase},get firstPerson(){return true},snapshot(){return{position:player.toArray(),camera:camera.position.toArray(),eyeHeight,yaw,pitch,inRange:state.inRange,transitions:state.transitions,phase:state.phase,book:bookAnchor.toArray()}}};
$('#choose-role').onclick=()=>onSelect();
$('#loading').hidden=false;$('#complete').hidden=true;$('#cinematic').hidden=true;$('#video-fallback').hidden=true;$('#retry').hidden=true;$('#crosshair').hidden=false;$('#interact').hidden=true;$('#book-marker').hidden=true;$('#hint').textContent='';
load();tick();
return {destroy(){
 if(disposed)return;disposed=true;releaseMouse();events.abort();cancelAnimationFrame(frame);
 const video=$('#book-video');video.pause();video.onended=null;video.onerror=null;
 root.querySelectorAll('button').forEach(b=>b.onclick=null);
 disposeGraphs(scene);renderer.dispose();renderer.forceContextLoss();delete window.CijianLibrary;
}};
}

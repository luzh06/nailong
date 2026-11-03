import * as T from 'three';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {roles as roleDefinitions} from './roles.js';
import {disposeGraphs} from './lifecycle.js';
import {makePortalMaterial,makeComposite} from './portal.js';
export function mountSelection({root,onConfirm}){
const events=new AbortController(),listen=(el,type,fn)=>el.addEventListener(type,fn,{signal:events.signal});
let disposed=false,frame;
const roles=roleDefinitions.map(r=>({...r}));
root.querySelector('#labels').replaceChildren();root.querySelector('#roster').replaceChildren();
root.querySelector('#detail').hidden=true;root.querySelector('#back').hidden=true;root.querySelector('#confirmed').hidden=true;
const $=s=>root.querySelector(s),canvas=$('#stage');
const renderer=new T.WebGLRenderer({canvas,antialias:true,alpha:true,premultipliedAlpha:false});
const portrait=new T.WebGLRenderer({canvas:$('#portrait'),antialias:true,alpha:true});
for(const r of [renderer,portrait]){r.setPixelRatio(Math.min(devicePixelRatio,2));r.outputColorSpace=T.SRGBColorSpace;r.toneMapping=T.ACESFilmicToneMapping;r.toneMappingExposure=1.15;}
portrait.setClearColor(0,0);
renderer.setClearColor(0,0);
const scene=new T.Scene();
const actorScene=new T.Scene(),camera=new T.PerspectiveCamera(36,1,.05,80),size=new T.Vector2();
function light(s){s.add(new T.HemisphereLight(0xffffff,0x9ca6a2,2.4));const a=new T.DirectionalLight(0xfff5e7,3.1);a.position.set(3,8,6);s.add(a);const b=new T.DirectionalLight(0xc6dbff,1);b.position.set(-6,3,2);s.add(b)}
light(scene);light(actorScene);
const floor=new T.Mesh(new T.PlaneGeometry(200,200),new T.MeshStandardMaterial({color:0xeae7df,roughness:.85}));floor.rotation.x=-Math.PI/2;floor.position.y=-.1;floor.visible=false;scene.add(floor);
const worldTarget=new T.WebGLRenderTarget(1,1,{type:T.HalfFloatType});
const composite=makeComposite(worldTarget.texture,size);
const frames=[],labels=[],buttons=[];let selected=-1,confirmed=false,blend=0,progress=0;
let navigationTimer;
const reduced=matchMedia('(prefers-reduced-motion:reduce)').matches;
const targetPos=new T.Vector3(),targetLook=new T.Vector3(),look=new T.Vector3(),overview=new T.Vector3();
function shape(w,h,r){const s=new T.Shape();s.moveTo(-w/2+r,0);s.lineTo(w/2-r,0);s.quadraticCurveTo(w/2,0,w/2,r);s.lineTo(w/2,h-r);s.quadraticCurveTo(w/2,h,w/2-r,h);s.lineTo(-w/2+r,h);s.quadraticCurveTo(-w/2,h,-w/2,h-r);s.lineTo(-w/2,r);s.quadraticCurveTo(-w/2,0,-w/2+r,0);return s}
roles.forEach((r,i)=>{
 r.x=(i-1.5)*3.05;r.angle=0;r.target=new T.WebGLRenderTarget(1,1,{type:T.HalfFloatType});r.room=new T.Scene();light(r.room);r.room.background=new T.Color('#6a5337');
 r.root=new T.Group();r.root.position.x=r.x;r.root.rotation.y=r.angle;r.room.add(r.root);
 const ground=new T.Mesh(new T.PlaneGeometry(200,200),new T.MeshStandardMaterial({color:0x59452e,roughness:.95}));ground.rotation.x=-Math.PI/2;ground.position.y=-.07;r.room.add(ground);
 const panel=new T.Mesh(new T.ShapeGeometry(shape(2.45,3.45,.17)),makePortalMaterial(r.target.texture,size));panel.position.set(r.x,0,.22);panel.rotation.y=r.angle;panel.userData.role=i;scene.add(panel);frames.push(panel);
 const border=new T.LineLoop(new T.BufferGeometry().setFromPoints(shape(2.49,3.49,.18).getPoints(24)),new T.LineBasicMaterial({color:0xd5d2c9}));border.position.copy(panel.position);border.rotation.copy(panel.rotation);scene.add(border);
 const label=document.createElement('div');label.className='label';label.innerHTML=`<b ${i>1?'lang="en"':''}>${r.name}</b><small lang="en">${r.en.split(' / ')[1].toLowerCase().replace(/\b\w/g,c=>c.toUpperCase())}</small>`;$('#labels').append(label);labels.push(label);
 const btn=document.createElement('button');btn.textContent=r.name;btn.setAttribute('aria-label',`查看${r.name}`);btn.setAttribute('aria-pressed','false');if(i>1)btn.lang='en';btn.onclick=()=>select(i);$('#roster').append(btn);buttons.push(btn);
});
function status(text,error=false){$('#status').textContent=text;$('#status').classList.toggle('sr-only',!error)}
function resize(){const w=innerWidth,h=innerHeight;camera.aspect=w/h;camera.updateProjectionMatrix();for(const r of [renderer,portrait])r.setSize(w,h);renderer.getDrawingBufferSize(size);worldTarget.setSize(size.x,size.y);roles.forEach(r=>r.target.setSize(size.x,size.y));const z=Math.max(12,12.6/camera.aspect);overview.set(0,2.9,z);if(selected<0){targetPos.copy(overview);targetLook.set(0,1.5,0)}else focus()}
function focus(){const r=roles[selected],mobile=innerWidth<700;targetPos.set(r.x+(mobile?.7:.9),1.6,mobile?7.2:6.0);targetLook.set(r.x+(mobile?.7:.9),1.4,0)}
// RenderTexture uses the actual target buffer size for gl_FragCoord alignment.

resize();camera.position.copy(targetPos);look.copy(targetLook);
function syncActors(){roles.forEach((r,i)=>{if(r.model)r.model.visible=false;if(r.actor)r.actor.visible=selected<0||i===selected})}
function select(i){if(confirmed||selected===i)return;selected=i;document.body.classList.add('focused');$('#back').hidden=false;$('#detail').hidden=false;$('#detail').dataset.role=roles[i].id;$('#origin').textContent=roles[i].en.toLowerCase().replace(/\b\w/g,c=>c.toUpperCase()).replace(' / ',' · ');$('#name').textContent=roles[i].name;$('#bio').textContent=roles[i].bio;$('#enter').disabled=!roles[i].ready;buttons.forEach((b,j)=>b.setAttribute('aria-pressed',String(i===j)));syncActors();focus();status(roles[i].ready?'':roles[i].failed?'人物载入失败，请刷新重试':'正在载入人物…',!roles[i].ready)}
function back(){clearTimeout(navigationTimer);selected=-1;confirmed=false;document.body.classList.remove('focused');$('#detail').hidden=true;$('#confirmed').hidden=true;$('#back').hidden=true;buttons.forEach(b=>b.setAttribute('aria-pressed','false'));syncActors();resize();status('')}
function enter(){if(selected<0||!roles[selected].ready||confirmed)return;confirmed=true;const r=roles[selected];try{localStorage.setItem('cijian.selectedRole',r.id)}catch{}window.dispatchEvent(new CustomEvent('cijian:role-confirmed',{detail:{id:r.id,name:r.name}}));$('#confirmed h2').textContent=r.name;$('#confirmed h2').lang=selected>1?'en':'zh';$('#confirmed').hidden=false;$('#reset').focus();navigationTimer=setTimeout(()=>{onConfirm(r.id)},reduced?50:650)}
$('#back').onclick=back;$('#enter').onclick=enter;$('#reset').onclick=()=>{const url=new URL(location);url.searchParams.delete('role');history.replaceState(null,'',url);back()};listen(window,'keydown',e=>{if(e.key==='Escape')back();else if(e.key==='Enter'&&selected>=0&&e.target.id!=='back'&&e.target.id!=='reset'){e.preventDefault();enter()}else if(!confirmed&&/^[1-4]$/.test(e.key))select(Number(e.key)-1)});
const ray=new T.Raycaster(),pointer=new T.Vector2();let down=null;
function hit(e){pointer.set(e.clientX/innerWidth*2-1,-e.clientY/innerHeight*2+1);ray.setFromCamera(pointer,camera);return ray.intersectObjects(frames,false)[0]}
listen(canvas,'pointerdown',e=>down=[e.clientX,e.clientY]);listen(canvas,'pointerup',e=>{if(selected>=0||!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>8)return;const h=hit(e);if(h)select(h.object.userData.role)});listen(canvas,'pointermove',e=>canvas.style.cursor=selected<0&&hit(e)?'pointer':'default');
async function load(){const loader=new GLTFLoader();for(let i=0;i<roles.length&&!disposed;i++){const r=roles[i];try{const {scene:model}=await loader.loadAsync(r.path);if(disposed){disposeGraphs(model);return;}const box=new T.Box3().setFromObject(model),dim=box.getSize(new T.Vector3()),center=box.getCenter(new T.Vector3()),fit=2.72/dim.y;model.scale.multiplyScalar(fit);model.position.set(-center.x*fit,.08-box.min.y*fit,.3-center.z*fit);r.model=model;r.root.add(model);const wrapper=new T.Group();wrapper.position.x=r.x;wrapper.rotation.y=r.angle;r.actor=wrapper;wrapper.add(model.clone(true));actorScene.add(wrapper);r.ready=true;progress++;syncActors()}catch(e){r.failed=true;console.error(r.name,e)}if(selected===i){$('#enter').disabled=!r.ready;status(r.ready?'':'人物载入失败，请刷新重试',!r.ready)}else if(selected<0)status(progress===4?'':'正在载入人物…',progress!==4)}}
load();listen(window,'resize',resize);const clock=new T.Clock();let lastSelected=0;
function animate(){if(disposed)return;frame=requestAnimationFrame(animate);const dt=Math.min(clock.getDelta(),.05),a=reduced?1:1-Math.exp(-dt*5);camera.position.lerp(targetPos,a);look.lerp(targetLook,a);camera.lookAt(look);blend=T.MathUtils.lerp(blend,selected>=0?1:0,a);if(selected>=0)lastSelected=selected;composite.material.uniforms.blend.value=blend;composite.material.uniforms.inner.value=roles[lastSelected].target.texture;
 roles.forEach((r,i)=>{if(blend>.999&&i!==selected)return;renderer.setRenderTarget(r.target);renderer.render(r.room,camera)});
 renderer.setRenderTarget(worldTarget);renderer.render(scene,camera);renderer.setRenderTarget(null);renderer.render(composite.scene,composite.camera);portrait.toneMappingExposure=T.MathUtils.lerp(1.15,.82,blend);portrait.render(actorScene,camera);
 labels.forEach((l,i)=>{const v=new T.Vector3(roles[i].x,-.24,.2).project(camera);l.style.left=`${(v.x*.5+.5)*innerWidth}px`;l.style.top=`${(-v.y*.5+.5)*innerHeight}px`});document.body.dataset.portalBlend=blend.toFixed(2);
}animate();

window.CijianSelection={get roles(){return roles.map(r=>({id:r.id,name:r.name,ready:!!r.ready,failed:!!r.failed,visible:!!r.actor?.visible}))},get selected(){return selected},get confirmed(){return confirmed}};

return {destroy(){
 if(disposed)return;disposed=true;clearTimeout(navigationTimer);cancelAnimationFrame(frame);events.abort();
 document.body.classList.remove('focused');
 root.querySelectorAll('button').forEach(b=>b.onclick=null);
 disposeGraphs(scene,actorScene,composite.scene,...roles.map(r=>r.room));
 for(const r of roles)r.target.dispose();worldTarget.dispose();
 for(const r of [renderer,portrait]){r.dispose();r.forceContextLoss();}
 delete window.CijianSelection;
}};
}

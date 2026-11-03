// 开场：古书标题 → 四张借阅卡（选角色与随身相机）→ 翻书镜头与旁白 → 书页发光入城。
// 古书模型与动画来自 5060 的 cijian_antique_book.glb（CIJIAN_AntiqueBook，8 秒：取出→开封面→翻页）。
// 东京街区在开场期间于后台加载；书页发光后若仍未就绪，停在“书页正在显影”并显示真实进度。
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/GLTFLoader.js';
import {ROLES,ROLE_ORDER,OPENING_LINES} from './story-data.mjs';
import {sfx,wait,preloadSfx} from './fx.mjs';

const url=p=>new URL(p,import.meta.url).href;
const CAMERAS={instant:'即时成像 · 方画幅',rangefinder:'胶片旁轴 · 3:2'};

export function createOpening({getProgress}){
 const root=document.createElement('section');root.className='cj-layer cj-opening';root.setAttribute('aria-label','此间 开场');
 root.innerHTML=`<div class="bgimg" style="position:absolute;inset:-3%;background:url(${url('./art/library-warm.webp')}) center/cover;filter:blur(9px) brightness(.32) saturate(.8);transform:scale(1.05)"></div>
 <canvas></canvas><div class="cj-vignette"></div><div class="cj-grain"></div>
 <div class="cj-title"><div class="eyebrow">CIJIAN · A JOURNEY IN THREE SUNSETS</div><h1><span>此</span><span>间</span></h1><i class="seal">三日<br>归途</i>
  <p class="sub">东京出发 · 悉尼归返</p><p class="line">四个人，一本书，三次日落之前的旅行页。</p>
  <div class="actions"><button class="cj-btn primary" data-start>翻开这本书</button></div></div>
 <div class="cj-cards" aria-live="polite"><header><small>BORROWING CARDS</small><h2>借阅卡</h2><p>选择一位旅人。另外三人也在这本书里。</p></header>
  <div class="cj-deck"></div>
  <div class="cj-gear"><span>随身相机</span><button data-cam="instant" aria-pressed="false">${CAMERAS.instant}</button><button data-cam="rangefinder" aria-pressed="false">${CAMERAS.rangefinder}</button></div>
  <button class="cj-btn primary" data-go disabled>盖章借阅，出发</button></div>
 <div class="cj-narration"></div><button class="cj-skip" hidden>跳过 ›</button>
 <div class="cj-white"><div class="dev">书页正在显影<i><b></b></i></div></div>
 <div class="cj-load"><span>东京街区载入中</span><i><b></b></i></div>
 <div class="cj-foot"><span>互动作品 · 三人团队制作</span><span>建议使用 Chrome / Edge · 键鼠操作</span></div>`;
 document.body.append(root);document.body.classList.add('cj-game');
 const $=s=>root.querySelector(s);
 preloadSfx();

 // ---------- 3D 古书 ----------
 const canvas=$('canvas');
 const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:'high-performance'});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 const scene=new THREE.Scene();scene.fog=new THREE.FogExp2(0x120e0a,.16);
 const camera=new THREE.PerspectiveCamera(30,1,.01,100);
 const key=new THREE.SpotLight(0xffd6a0,120,0,.55,.7,1.6);key.position.set(-1.6,3.2,1.8);key.castShadow=true;key.shadow.mapSize.set(1024,1024);key.shadow.bias=-.0015;key.shadow.normalBias=.012;scene.add(key,key.target);
 scene.add(new THREE.HemisphereLight(0x8a7a66,0x1a140e,.55));
 const rim=new THREE.DirectionalLight(0x9db4ff,.9);rim.position.set(2,1.5,-2.5);scene.add(rim);
 const table=new THREE.Mesh(new THREE.CircleGeometry(40,96),new THREE.MeshStandardMaterial({color:0x22170f,roughness:.82,metalness:0}));table.rotation.x=-Math.PI/2;table.receiveShadow=true;scene.add(table);
 // 书页发出的光（入书时增强）
 const pageGlow=new THREE.PointLight(0xfff0cf,0,3,1.5);scene.add(pageGlow);
 // 尘埃
 const dustN=420,dustPos=new Float32Array(dustN*3);for(let i=0;i<dustN;i++){dustPos[i*3]=(Math.random()-.5)*3;dustPos[i*3+1]=Math.random()*2.2;dustPos[i*3+2]=(Math.random()-.5)*2.4;}
 const dustGeo=new THREE.BufferGeometry();dustGeo.setAttribute('position',new THREE.BufferAttribute(dustPos,3));
 const dust=new THREE.Points(dustGeo,new THREE.PointsMaterial({color:0xffe2b0,size:.008,transparent:true,opacity:.55,depthWrite:false,blending:THREE.AdditiveBlending}));scene.add(dust);

 let mixer=null,action=null,book=null,clipDur=8,box=new THREE.Box3(),center=new THREE.Vector3(),radius=.4;
 const endCenter=new THREE.Vector3();let endRadius=.4;
 const camFrom=new THREE.Vector3(),camTo=new THREE.Vector3(),lookFrom=new THREE.Vector3(),lookTo=new THREE.Vector3(),look=new THREE.Vector3();
 let shot={t:0,dur:1,from:camFrom,to:camTo,la:lookFrom,lb:lookTo};
 // 标题和借阅卡阶段把书挪到画面右侧，给左侧标题留白；翻书时回到正中
 let shift=.2,shiftTarget=.2;
 function setShot(pos,target,dur){shot={t:0,dur,from:camera.position.clone(),to:pos.clone(),la:look.clone(),lb:target.clone()};}
 const ready=new GLTFLoader().loadAsync(url('./models/cijian_antique_book.glb')).then(g=>{
  book=g.scene;book.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});scene.add(book);
  mixer=new THREE.AnimationMixer(book);const clip=g.animations[0];clipDur=clip.duration;action=mixer.clipAction(clip);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.play();
  // 标题画面：停在“读书姿态、封面未开”的那一帧
  // 先取最后一帧（摊开在地图页）的包围盒，供翻书镜头取景
  mixer.setTime(clipDur-.01);book.updateMatrixWorld(true);const be=new THREE.Box3().setFromObject(book);be.getCenter(endCenter);endRadius=be.getSize(new THREE.Vector3()).length()/2;
  mixer.setTime(1.62);action.paused=true;book.updateMatrixWorld(true);box.setFromObject(book);box.getCenter(center);radius=box.getSize(new THREE.Vector3()).length()/2;
  table.position.y=box.min.y-.002;
  key.target.position.copy(center);pageGlow.position.copy(center).add(new THREE.Vector3(0,radius*.6,0));
  const p=center.clone().add(new THREE.Vector3(radius*1.9,radius*1.7,radius*3.1));camera.position.copy(p);look.copy(center);
  setShot(center.clone().add(new THREE.Vector3(radius*1.5,radius*1.45,radius*2.7)),center,9);
 }).catch(e=>{console.error('[opening] book',e);});

 let running=true,last=performance.now();
 function size(){const w=innerWidth,h=innerHeight;renderer.setSize(w,h,false);camera.aspect=w/h;applyShift();}
 function applyShift(){const w=innerWidth,h=innerHeight;if(w<820){camera.clearViewOffset();camera.updateProjectionMatrix();return;}camera.setViewOffset(w,h,-w*shift,0,w,h);camera.updateProjectionMatrix();}
 size();addEventListener('resize',size);
 function loop(n){if(!running)return;const dt=Math.min(.05,(n-last)/1000);last=n;
  if(mixer&&!action.paused)mixer.update(dt);
  if(Math.abs(shift-shiftTarget)>1e-4){shift+=(shiftTarget-shift)*(1-Math.exp(-2.2*dt));applyShift();}
  shot.t=Math.min(shot.dur,shot.t+dt);const k=THREE.MathUtils.smootherstep(shot.t/shot.dur,0,1);camera.position.lerpVectors(shot.from,shot.to,k);look.lerpVectors(shot.la,shot.lb,k);camera.lookAt(look);
  const pa=dustGeo.attributes.position;for(let i=0;i<dustN;i++){let y=pa.getY(i)+dt*.02*(1+(i%5)*.3);if(y>2.2)y=0;pa.setY(i,y);pa.setX(i,pa.getX(i)+Math.sin(n*.0003+i)*.0002);}pa.needsUpdate=true;
  renderer.render(scene,camera);
  const p=getProgress();$('.cj-load b').style.width=Math.round(p*100)+'%';$('.cj-load span').textContent=p>=1?'东京街区已就绪':'东京街区载入中 '+Math.round(p*100)+'%';
  requestAnimationFrame(loop);}
 requestAnimationFrame(loop);

 // ---------- 借阅卡 ----------
 let role=null,cam=null;
 const deck=$('.cj-deck');
 deck.innerHTML=ROLE_ORDER.map((id,i)=>{const r=ROLES[id];return `<button class="cj-card" data-role="${id}" aria-label="${r.name}，${r.from}。${r.line}">
  <div class="rule"><span>NO. 0${i+1}</span><span>${r.mark}</span></div><div class="pic"><img src="${url('./img/card-'+id+'.webp')}" alt=""></div>
  <div class="meta"><b>${r.name}</b><span>${r.from}</span><em>${r.line}</em></div><i class="stamp">此间<br>借阅</i></button>`;}).join('');
 function choose(id){role=id;deck.querySelectorAll('.cj-card').forEach(c=>c.classList.toggle('chosen',c.dataset.role===id));setCam(ROLES[id].camera);$('[data-go]').disabled=false;sfx('entry-reveal',{volume:.25,rate:1.3});}
 function setCam(c){cam=c;root.querySelectorAll('[data-cam]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.cam===c)));}
 deck.addEventListener('click',e=>{const c=e.target.closest('.cj-card');if(c)choose(c.dataset.role);});
 root.querySelectorAll('[data-cam]').forEach(b=>b.onclick=()=>setCam(b.dataset.cam));
 deck.addEventListener('mouseover',e=>{const c=e.target.closest('.cj-card');if(c&&c.dataset.h!=='1'){c.dataset.h='1';sfx('page-left',{volume:.08,rate:1.6});setTimeout(()=>c.dataset.h='',400);}});

 let skip=false;
 async function narrate(lines,each=2600){const box=$('.cj-narration');for(const l of lines){if(skip)break;const p=document.createElement('p');p.textContent=l;box.append(p);
  void document.body.offsetWidth;await wait(34);p.classList.add('on');await waitSkippable(each);p.classList.remove('on');await waitSkippable(700);p.remove();}}
 function waitSkippable(ms){return new Promise(r=>{const t=setTimeout(r,ms);const iv=setInterval(()=>{if(skip){clearTimeout(t);clearInterval(iv);r();}},60);setTimeout(()=>clearInterval(iv),ms+10);});}

 return{
  // 标题 → 借阅卡；resolve {role, camera}
  async choose(){await new Promise(r=>$('[data-start]').onclick=r);sfx('book-open',{volume:.35,rate:.9});
   $('.cj-title').classList.add('out');$('.cj-foot').style.opacity=0;await wait(500);$('.cj-cards').classList.add('on');
   shiftTarget=0;if(book)setShot(center.clone().add(new THREE.Vector3(-radius*.4,radius*3.6,radius*2.8)),center,4);
   await new Promise(r=>$('[data-go]').onclick=r);
   sfx('camera-shutter',{volume:.25,rate:.7});deck.classList.add('done');await wait(1100);$('.cj-cards').classList.remove('on');await wait(700);
   return{role,camera:cam};},
  // 翻书镜头 + 旁白，最后书页发光、白幕覆盖
  async playBook(){await ready;const s=$('.cj-skip');s.hidden=false;s.onclick=()=>{skip=true;};
   shiftTarget=0;
   if(book){action.paused=false;mixer.setTime(1.62);
    setShot(endCenter.clone().add(new THREE.Vector3(endRadius*.15,endRadius*2.1,endRadius*1.35)),endCenter,2.6);sfx('book-open',{volume:.5});
    setTimeout(()=>{if(!skip)sfx('page-right',{volume:.35});},1500);setTimeout(()=>{if(!skip)sfx('page-left',{volume:.3});},2800);setTimeout(()=>{if(!skip)sfx('page-right',{volume:.3});},3900);}
   const lines=narrate(OPENING_LINES,2500);
   await waitSkippable(7000);
   // 翻到最后一页（地图页）后推近，书页慢慢发亮
   if(book){const c2=endCenter.clone();setShot(c2.clone().add(new THREE.Vector3(0,endRadius*.62,endRadius*.12)),c2,skip?.8:5);}
   await lines;
   const t0=performance.now(),dur=skip?600:2600;
   await new Promise(res=>{const glow=()=>{const k=Math.min(1,(performance.now()-t0)/dur);pageGlow.intensity=k*k*14;renderer.toneMappingExposure=1.3+k*k*2.2;if(k<1&&running)setTimeout(glow,16);else res();};glow();});
   s.hidden=true;$('.cj-white').classList.add('on');sfx('entry-reveal',{volume:.4});await wait(1500);},
  // 白幕停留直到城市就绪
  async waitWorld(isReady){const dev=$('.cj-white .dev');if(!isReady()){dev.classList.add('on');while(!isReady()){dev.querySelector('b').style.width=Math.round(getProgress()*100)+'%';await wait(120);}dev.querySelector('b').style.width='100%';await wait(400);dev.classList.remove('on');}},
  // 白幕淡出，露出城市；之后销毁开场
  async reveal(){running=false;$('canvas').style.opacity=0;root.querySelector('.bgimg').style.opacity=0;root.querySelector('.cj-vignette').style.opacity=0;root.querySelector('.cj-grain').style.opacity=0;$('.cj-load').style.opacity=0;
   root.style.background='transparent';const w=$('.cj-white');w.style.transition='opacity 2.4s cubic-bezier(.16,1,.3,1)';w.classList.remove('on');await wait(2400);
   removeEventListener('resize',size);renderer.dispose();renderer.forceContextLoss?.();root.remove();},
 };
}

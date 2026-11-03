// 《此间》游戏层总控：开场 → 东京第一天（三个图鉴点 + 配对事件 + 夜晚烟花）→ 书页门 → 悉尼终章与回忆卡。
// 东京场景、碰撞与输入由 world.js 提供，本文件只通过 window.__cijian.hooks 接入，不改动其渲染与碰撞实现。
import * as THREE from 'three';
import {ROLES,SPOTS,SPOT_ORDER,PLACES,PAIR_EVENTS} from './story-data.mjs';
import {createOpening} from './opening.mjs';
import {createActor,preloadActor} from './actors.mjs';
import {createRig} from './rig.mjs';
import {createDialogue} from './dialogue.mjs';
import {createJournal} from './journal.mjs';
import {createHud} from './hud.mjs';
import {createSakura} from './sakura.mjs';
import {createFireworks} from './fireworks.mjs';
import {shutter,curtain,toast,sfx,wait,startAmbience,setAmbience} from './fx.mjs';
import {playFinale} from './finale.mjs';
import {PhotoSystem,HdrPipeline} from './photo/index.js';

const link=document.createElement('link');link.rel='stylesheet';link.href=new URL('./game.css',import.meta.url).href;document.head.append(link);
const Q=new URLSearchParams(location.search);

const worldProgress=()=>{if(window.__cijian?.ready)return 1;const w=parseFloat(document.querySelector('#bar i')?.style.width||'0');return Math.min(.99,(w||0)/100);};
const worldReady=new Promise(res=>{if(window.__cijian?.ready)res(window.__cijian);else document.addEventListener('cijian:ready',e=>res(e.detail),{once:true});});

// ---------- 开场 ----------
let choice;
const opening=createOpening({getProgress:worldProgress});
if(Q.has('role')&&ROLES[Q.get('role')]){choice={role:Q.get('role'),camera:ROLES[Q.get('role')].camera};}
else choice=await opening.choose();
const role=ROLES[choice.role],partnerId=role.partner,partnerRole=ROLES[partnerId];
const actorsP=Promise.all([preloadActor(choice.role),preloadActor(partnerId)]).then(()=>Promise.all([createActor(choice.role),createActor(partnerId)]));
let world=null,actors=null;worldReady.then(w=>{world=w;w.hooks.suspend=true;});actorsP.then(a=>actors=a);
if(!Q.has('skipintro'))await opening.playBook();
await opening.waitWorld(()=>world&&actors);
const game=setup(world,actors);
world.hooks.suspend=false;
await opening.reveal();
await game.begin();

function setup(W,[avatar,partner]){
 const {scene,camera,renderer,walkWorld,me,hooks,toneU,skyU}=W;
 const v3=(x,y,h)=>new THREE.Vector3(x,h??(walkWorld.ground(x,y)??0),-y);
 document.body.classList.add('cj-game','cj-playing');

 // ---------- 角色 ----------
 scene.add(avatar.root,partner.root);
 const rig=createRig({world:W,avatar});
 const isCnJp=role.pairSpot==='TOKYO-02';
 const npcSpot=isCnJp?PLACES.sakuraNpc:PLACES.fireworksNpc;
 partner.place(...v3(npcSpot.x,npcSpot.y).toArray());
 partner.face(isCnJp?Math.atan2(PLACES.sakura.x-npcSpot.x,-(PLACES.sakura.y-npcSpot.y))+Math.PI*.6:Math.PI*.5,true);
 partner.root.visible=isCnJp;
 const pair={met:false,agreed:false,exchanged:false,leaving:0};

 // ---------- 布景：樱花与烟花 ----------
 const sakura=createSakura();sakura.position.copy(v3(PLACES.sakura.x,PLACES.sakura.y));scene.add(sakura);
 const fwC=PLACES.fireworksCenter;
 const nightExp={base:toneU.uExp.value,cur:toneU.uExp.value,target:toneU.uExp.value,bloom:toneU.uBloom.value};
 const fireworks=createFireworks({center:new THREE.Vector3(fwC.x,fwC.z,-fwC.y),onFlash:f=>{toneU.uExp.value=nightExp.cur*(1+f*.45);}});
 scene.add(fireworks.points);
 hooks.obstacles=[{x:PLACES.sakura.x,y:PLACES.sakura.y,r:.45},{get x(){return pair.leaving?1e4:npcSpot.x;},get y(){return npcSpot.y;},r:.32}];

 // ---------- 拍照 ----------
 const pipeline=new HdrPipeline(renderer);pipeline.setLuts(toneU.lutA.value,toneU.lutB.value);
 const occ=new THREE.BufferGeometry();occ.setAttribute('position',new THREE.BufferAttribute(walkWorld.tree.data,3));
 const occluder=new THREE.Mesh(occ,new THREE.MeshBasicMaterial({side:THREE.DoubleSide}));occluder.updateMatrixWorld(true);
 let phase='afternoon';
 const spotTargets={'TOKYO-01':()=>{const t=SPOTS['TOKYO-01'].target;return new THREE.Vector3(t.x,t.z,-t.y);},'TOKYO-02':()=>sakura,'TOKYO-03':()=>fireworks.target};
 const photo=new PhotoSystem({renderer,scene,camera,pipeline,styleId:choice.camera,focalLengths:[24,35,50,85],occluders:[occluder],avatar:avatar.root,
  spots:SPOT_ORDER.map(id=>({id,label:SPOTS[id].title,target:spotTargets[id](),radius:id==='TOKYO-03'?13:SPOTS[id].radius,minCoverage:SPOTS[id].minCoverage,phases:id==='TOKYO-03'?['night']:null,
   waitTip:id==='TOKYO-03'?'烟花要等到夜里':undefined})),
  subjects:[{id:partnerId,label:partnerRole.name,object:partner.root,needsConsent:true}],
  getContext:()=>({sceneId:'tokyo',phase,weather:'clear'})});
 photo.album.cardInfo=()=>({title:'此间 · 东京',subtitle:`${role.name}的第一天`,caption:'三次日落之前，让你的旅行页显影。',sealText:'此间'});
 hooks.render=()=>{pipeline.grade=toneU.uGrade.value;pipeline.exposure=toneU.uExp.value;pipeline.bloom=W.quality.bloom?toneU.uBloom.value:0;pipeline.lutMix=toneU.uT.value;pipeline.time=toneU.uTime.value;return photo.render();};
 hooks.lookScale=()=>photo.lookScale;
 photo.addEventListener('enter',()=>{rig.setFirstPerson(true);document.body.classList.add('cj-photo');});
 photo.addEventListener('exit',()=>{rig.setFirstPerson(false);document.body.classList.remove('cj-photo');});
 photo.addEventListener('error',e=>toast(e.detail.message,4000));

 // ---------- 界面 ----------
 const dlg=createDialogue();dlg.setPlayer(choice.role);
 let busy=false;// 对话、过场、显影卡片时为 true
 let canTalk=false;
 const journal=createJournal({onDoor:()=>toFinale(),onOpenChange:open=>{W.setUiBlocked(open);if(!open&&!busy)resume();}});
 const hud=createHud({onJournal:()=>journal.toggle(),onCamera:()=>{if(!busy&&W.walking)photo.toggle();},onAlbum:()=>photo.album.toggle(),onResume:()=>resume(),onInteract:()=>{if(canTalk&&!busy&&!photo.active)talk();}});
 function resume(){if(busy||journal.isOpen||W.mapUI.expanded)return;hud.paused(false);W.resumeWalk();}
 hooks.zoom=d=>photo.active?true:rig.zoom(d);
 hooks.blockMove=()=>photo.active||busy;
 hooks.exit=()=>{if(!busy&&!journal.isOpen&&!photo.album.isOpen&&!W.mapUI.expanded)hud.paused(true);};
 document.addEventListener('cijian:mapchange',e=>{if(!e.detail.expanded&&!busy)setTimeout(resume,0);});

 // ---------- 收集显影 ----------
 const reveal=document.createElement('div');reveal.className='cj-reveal';reveal.innerHTML='<figure><img alt=""><figcaption><small></small><b></b><span></span></figcaption></figure><p class="tip">点击继续 · 已写入旅行图鉴</p>';document.body.append(reveal);
 async function showReveal(id){const s=SPOTS[id];reveal.querySelector('img').src=new URL(`./art/${id}.webp`,import.meta.url).href;
  reveal.querySelector('small').textContent=`${id} · 东京 ${journal.count}/3`;reveal.querySelector('b').textContent=s.title;reveal.querySelector('span').textContent=s.caption;
  W.setUiBlocked(true);document.body.classList.add('cj-cinematic');reveal.classList.add('on');sfx('entry-reveal',{volume:.5});
  await new Promise(r=>{const done=()=>{removeEventListener('keydown',k,true);r();};const k=e=>{if(['Space','Enter','KeyF','Escape'].includes(e.code)){e.preventDefault();e.stopPropagation();done();}};
   addEventListener('keydown',k,true);reveal.onclick=done;});
  reveal.classList.remove('on');document.body.classList.remove('cj-cinematic');W.setUiBlocked(false);}
 const near=(p,r)=>Math.hypot(me.x-p.x,me.y-p.y)<=r;
 photo.addEventListener('photo',async e=>{const {record}=e.detail,m=record.meta;
  const url=URL.createObjectURL(record.blob);
  // 配对互拍：对方在画面里、已征得同意
  if(pair.agreed&&!pair.exchanged&&m.subjects.includes(partnerId)&&m.storyOk){await exchange();}
  for(const id of m.spotHits){if(journal.has(id))continue;const s=SPOTS[id];
   if(!near(s.view,s.viewRadius)){toast(`再走近一些：${s.hint}`);continue;}
   if(id==='TOKYO-03'&&phase!=='night')continue;
   journal.collect(id,url);hud.setProgress(journal.count);
   busy=true;photo.exit();await wait(900);await showReveal(id);busy=false;
   if(id==='TOKYO-02'&&!isCnJp)toast('天色在变——宝蔵门那边，好像要放烟花了');
   resume();break;}
  refresh();});

 // ---------- 配对事件 ----------
 const ev=PAIR_EVENTS[choice.role];
 function twoShot(){const a=avatar.root.position,b=partner.root.position;const mid=a.clone().lerp(b,.5);const side=new THREE.Vector3(b.z-a.z,0,a.x-b.x).normalize();
  const camPos=mid.clone().addScaledVector(side,2.6).add(new THREE.Vector3(0,1.55,0)).addScaledVector(a.clone().sub(b).normalize(),.9);rig.shot(camPos,mid.clone().add(new THREE.Vector3(0,1.25,0)),1.4);}
 function faceEachOther(){avatar.faceToward(partner.root.position.x,partner.root.position.z);partner.faceToward(avatar.root.position.x,avatar.root.position.z);}
 async function talk(){if(busy)return;busy=true;W.setUiBlocked(true);hud.prompt('');document.body.classList.add('cj-cinematic');
  faceEachOther();partner.talking=true;twoShot();await wait(600);
  if(!pair.met){await dlg.lines(ev.intro,partnerId);pair.met=true;}
  const r=await dlg.hub(ev.hub,ev.options,partnerId);
  dlg.hide();partner.talking=false;rig.release();document.body.classList.remove('cj-cinematic');
  if(r==='advance'){pair.agreed=true;photo.setConsent(partnerId);toast(ev.exchangeHint,4200);}
  busy=false;W.setUiBlocked(false);resume();refresh();}
 async function exchange(){busy=true;W.setUiBlocked(true);await wait(700);photo.exit();document.body.classList.add('cj-cinematic');
  // 对方举起相机为玩家取景：镜头切到对方的视角
  faceEachOther();const a=avatar.root.position.clone(),b=partner.root.position.clone();
  const eye=b.clone().add(new THREE.Vector3(0,partnerRole.height-.1,0)).addScaledVector(a.clone().sub(b).normalize(),.25);
  rig.shot(eye,a.clone().add(new THREE.Vector3(0,role.height*.62,0)),1.2);
  await dlg.lines([{who:'narr',text:ev.gift}],partnerId);dlg.hide();
  await wait(400);const giftAvatar=photo.avatar;photo.avatar=null;photo.enter();photo.ui.spot.textContent=`${partnerRole.name}正在为你取景`;
  await wait(1400);const gift=await photo.shoot({force:true});photo.exit();photo.avatar=giftAvatar;
  if(gift)toast(`收到一张${partnerRole.name}拍的照片 · 已放进相册`,3200);
  twoShot();await wait(900);partner.talking=true;
  await dlg.lines(ev.farewell,partnerId);dlg.hide();partner.talking=false;
  pair.exchanged=true;journal.setPair(partnerRole.name,true);
  rig.release();document.body.classList.remove('cj-cinematic');
  // 对方沿另一条路离开，渐隐
  pair.leaving=1;const dir=new THREE.Vector3(Math.random()-.5,0,Math.random()-.5).normalize();partner.face(Math.atan2(dir.x,dir.z));
  busy=false;W.setUiBlocked(false);resume();refresh();
  const t0=performance.now();await new Promise(res=>{const step=()=>{const k=(performance.now()-t0)/3200;partner.root.position.addScaledVector(dir,.022);
   partner.root.position.y=walkWorld.ground(partner.root.position.x,-partner.root.position.z)??partner.root.position.y;partner.setOpacity(Math.max(0,1-k));partner.speed=1.3;if(k<1)requestAnimationFrame(step);else res();};step();});}

 // ---------- 夜晚 ----------
 async function nightfall(){if(phase==='night')return;busy=true;W.setUiBlocked(true);
  await shutter(async()=>{phase='night';toneU.uGrade.value.set(.62,.7,1.08);nightExp.target=nightExp.base*.16;nightExp.cur=nightExp.target;toneU.uExp.value=nightExp.cur;toneU.uBloom.value=Math.max(.5,nightExp.bloom*2.4);
   skyU.uFogC.value.multiplyScalar(.4);W.sun.intensity*=.1;scene.environmentIntensity=.35;hud.setPhase('夜 · 烟花');setAmbience(.05);
   if(!isCnJp){partner.root.visible=true;partner.setOpacity(1);}fireworks.start();},{hold:700});
  // 过场：镜头从角色身后抬起，看向第一束烟花，再把视角交还玩家（朝向烟花）
  document.body.classList.add('cj-cinematic');
  const head=rig.headPosition(),fw=fireworks.target.clone(),dirXZ=new THREE.Vector3(fw.x-head.x,0,fw.z-head.z).normalize();
  rig.shot(head.clone().addScaledVector(dirXZ,-3.2).add(new THREE.Vector3(0,-.6,0)),fw,3.2);
  toast('夜色降临。宝蔵门的上空，第一束烟花升起。',3600);await wait(4200);
  me.yaw=Math.atan2(-dirXZ.z,dirXZ.x);me.pitch=.75;rig.release();document.body.classList.remove('cj-cinematic');
  busy=false;W.setUiBlocked(false);resume();refresh();}

 // ---------- 目标与提示 ----------
 const head=o=>o.position.clone().add(new THREE.Vector3(0,2.05,0));
 function objective(){
  const has=id=>journal.has(id);
  if(!has('TOKYO-01')){const s1=SPOTS['TOKYO-01'],t=s1.target;
   // 已站在取景点附近：标记移到要拍的街道上
   return near(s1.view,s1.viewRadius)?[s1.hint+'（按 C 举起相机，空格按下快门）',new THREE.Vector3(t.x,t.z,-t.y),'对准街道']:[s1.hint,v3(s1.view.x,s1.view.y).add(new THREE.Vector3(0,1.2,0)),'台阶'];}
  if(isCnJp&&!pair.exchanged){
   if(!pair.agreed)return[pair.met?`${partnerRole.name}还在樱花树下`:'樱花树下好像站着一个人。走近，按 F 打招呼',head(partner.root),'樱花树下'];
   return[ev.exchangeHint,head(partner.root),partnerRole.name];}
  if(!has('TOKYO-02'))return[SPOTS['TOKYO-02'].hint,v3(PLACES.sakura.x,PLACES.sakura.y).add(new THREE.Vector3(0,3.6,0)),'樱花'];
  if(phase!=='night')return['天色渐暗——穿过雷门，去宝蔵门前等烟花',v3(PLACES.courtTrigger.x,PLACES.courtTrigger.y).add(new THREE.Vector3(0,1.6,0)),'宝蔵门'];
  if(!isCnJp&&!pair.exchanged){
   if(!pair.agreed)return[pair.met?`${partnerRole.name}还在人群边缘`:'人群边缘有个人也举着相机。走近，按 F 打招呼',head(partner.root),'人群边缘'];
   return[ev.exchangeHint,head(partner.root),partnerRole.name];}
  if(!has('TOKYO-03'))return[SPOTS['TOKYO-03'].hint,fireworks.target.clone(),'烟花'];
  return['东京的三页都显影了。按 J 翻开图鉴——书页门已经显出悉尼',null,''];
 }
 function refresh(){const [t,pos,l]=objective();hud.setObjective(t,pos,l);const done=journal.count===3&&pair.exchanged;journal.setDoor(done);hud.pulseJournal(done);
  journal.setPair(partnerRole.name,pair.exchanged);}

 // ---------- 按键 ----------
 addEventListener('keydown',e=>{if(e.repeat)return;
  if(e.code==='KeyF'&&canTalk&&!busy&&!photo.active&&!journal.isOpen){e.preventDefault();talk();}
  else if(e.code==='KeyJ'&&!busy&&!photo.active&&!journal.isOpen&&!W.mapUI.expanded){e.preventDefault();journal.open();}});
 // 取景只在行走时可用（避免暂停层下误开）
 const origToggle=photo.toggle.bind(photo);photo.toggle=()=>{if(busy||journal.isOpen||(!W.walking&&!photo.active))return;origToggle();};

 // ---------- 每帧 ----------
 const pl=new THREE.Vector3();let refreshTimer=0;
 hooks.camera=(m,dt,move)=>rig.update(dt,move);
 hooks.update=(dt,n,walking)=>{
  if(!walking)rig.update(dt,null);
  if(pair.leaving){partner.update(dt,1.3);}else{
   const d=Math.hypot(avatar.root.position.x-partner.root.position.x,avatar.root.position.z-partner.root.position.z);
   if(partner.root.visible&&d<6&&!busy)partner.faceToward(avatar.root.position.x,avatar.root.position.z);
   partner.update(dt,0);
   canTalk=partner.root.visible&&!pair.agreed&&d<2.8&&!busy;
   hud.prompt(canTalk&&!photo.active?`与 ${pair.met?partnerRole.name:'陌生人'} 交谈`:'');}
  sakura.userData.update(dt);fireworks.update(dt);
  pl.set(me.x,0,-me.y);hud.update(camera,pl);
  if((refreshTimer-=dt)<=0){refreshTimer=.5;if(!busy)refresh();}
  // 第一次进入宝蔵门广场且樱花已显影：入夜
  if(phase!=='night'&&!busy&&journal.has('TOKYO-02')&&(!isCnJp||pair.exchanged)&&near(PLACES.courtTrigger,PLACES.courtTrigger.r))nightfall();
 };

 async function toFinale(){busy=true;photo.exit();W.setUiBlocked(true);document.body.classList.add('cj-cinematic');
  const c=await curtain({color:'#efe4cc',eyebrow:'THE BOOK DOOR',caption:'翻向下一页',duration:1600});sfx('book-close',{volume:.5});
  fireworks.stop();
  const photos=[...SPOT_ORDER.map(id=>journal.photo(id)).filter(Boolean)];
  await playFinale({roleId:choice.role,photos,onAlbum:()=>{photo.album.open();},onReplay:()=>{location.href=location.pathname;}});
  await c.out(600);}

 return{async begin(){
  // 第一画面：站在台阶顶，镜头先看街道，再落到角色身后
  W.setUiBlocked(false);
  const sp=PLACES.spawn;W.me.yaw=sp.yaw;me.x=sp.x;me.y=sp.y;me.height=walkWorld.ground(sp.x,sp.y)??me.height;me.pitch=-.12;
  avatar.place(...v3(sp.x,sp.y).toArray());avatar.face(Math.atan2(Math.cos(sp.yaw),-Math.sin(sp.yaw)),true);
  const title=await curtain({color:'rgba(11,12,10,.0)',eyebrow:'DAY 1 · TOKYO · AFTERNOON',caption:'第一天 · 东京',duration:10});
  title.el.style.background='linear-gradient(180deg,rgba(10,10,8,.0),rgba(10,10,8,.35))';title.el.style.cursor='pointer';
  const tip=document.createElement('p');tip.style.cssText='position:absolute;left:0;right:0;bottom:12vh;text-align:center;font:13px "Songti SC","SimSun",serif;letter-spacing:.3em;color:#e9dcc0;text-shadow:0 2px 10px #000';tip.textContent='点击画面，开始旅行';title.el.append(tip);
  startAmbience();refresh();
  await new Promise(r=>title.el.addEventListener('click',r,{once:true}));
  W.enterWalkAt({x:sp.x,y:sp.y,yaw:sp.yaw,pitch:-.12});
  title.out(900);toast(`${role.name}：${role.line}`,3600);
  window.__cijianGame={photo,journal,pair,get phase(){return phase;},rig,avatar,partner,nightfall,talk,toFinale,refresh};
 }};
}

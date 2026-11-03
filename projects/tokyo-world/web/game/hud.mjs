// 游玩界面：章节标题、图鉴进度、当前目标与距离、屏幕标记、F 交互提示、暂停层、底部按钮。
import * as THREE from 'three';

export function createHud({onJournal,onCamera,onAlbum,onResume,onInteract}){
 const hud=document.createElement('div');hud.className='cj-hud';hud.dataset.hud='';
 hud.innerHTML=`<div class="cj-chapter"><small>DAY 1 · TOKYO</small><b>第一天 · 东京</b><span data-phase>午后</span></div>
  <div class="cj-progress" aria-label="东京图鉴进度"><i>1</i><i>2</i><i>3</i></div>
  <div class="cj-objective" role="status" aria-live="polite"><small>书页上的下一行</small><span data-text></span><span class="dist" data-dist></span></div>
  <div class="cj-tray"><button data-j><span class="cj-kbd">J</span>图鉴</button><button data-c><span class="cj-kbd">C</span>取景</button><button data-b><span class="cj-kbd">B</span>相册</button></div>`;
 const prompt=document.createElement('div');prompt.className='cj-prompt';prompt.innerHTML='<span class="cj-kbd">F</span><span data-t></span>';
 const marker=document.createElement('div');marker.className='cj-marker';marker.dataset.hud='';marker.innerHTML='<i></i><span></span>';
 const pause=document.createElement('div');pause.className='cj-pause';pause.innerHTML=`<div><b>旅途暂停</b><p>点击画面，继续旅行</p>
  <div class="cj-keys"><span>WASD / 方向键</span><span>行走（Shift 快走）</span><span>鼠标</span><span>环视 · 滚轮拉近拉远</span><span>F</span><span>交谈 / 互动</span><span>C · 空格</span><span>举起相机 · 按下快门</span><span>J / B / M</span><span>图鉴 / 相册 / 地图</span></div></div>`;
 document.body.append(hud,prompt,marker,pause);
 hud.querySelector('[data-j]').onclick=onJournal;hud.querySelector('[data-c]').onclick=onCamera;hud.querySelector('[data-b]').onclick=onAlbum;
 pause.onclick=()=>onResume?.();
 // 触屏：交互提示本身可以点
 prompt.onclick=()=>onInteract?.();
 const text=hud.querySelector('[data-text]'),dist=hud.querySelector('[data-dist]'),obj=hud.querySelector('.cj-objective');
 const v=new THREE.Vector3();let target=null,label='';
 return{
  setObjective(t,pos=null,markLabel=''){if(text.textContent!==t){text.textContent=t;obj.classList.remove('flash');void obj.offsetWidth;obj.classList.add('flash');}target=pos;label=markLabel;marker.querySelector('span').textContent=markLabel;},
  setPhase(p){hud.querySelector('[data-phase]').textContent=p;},
  setProgress(n){hud.querySelectorAll('.cj-progress i').forEach((e,i)=>e.classList.toggle('got',i<n));},
  pulseJournal(on){hud.querySelector('[data-j]').classList.toggle('pulse',on);},
  prompt(t){if(t){prompt.querySelector('[data-t]').textContent=t;prompt.classList.add('on');}else prompt.classList.remove('on');},
  paused(on){pause.classList.toggle('on',on);},
  get isPaused(){return pause.classList.contains('on');},
  // 每帧：把目标投到屏幕；在身后或屏幕外时贴边显示
  update(camera,player){if(!target){marker.style.opacity=0;dist.textContent='';return;}
   const d=Math.hypot(target.x-player.x,target.z-player.z);dist.textContent=d>4?`· 约 ${Math.round(d)} 米`:'';
   v.copy(target).project(camera);const behind=v.z>1;let x=v.x,y=v.y;
   if(behind){x=-x;y=-1;}
   const edge=behind||Math.abs(x)>.92||Math.abs(y)>.88;x=THREE.MathUtils.clamp(x,-.92,.92);y=THREE.MathUtils.clamp(y,-.85,.88);
   marker.style.opacity=d<2.2?0:1;marker.classList.toggle('edge',edge);
   marker.style.transform=`translate(${(x*.5+.5)*innerWidth}px,${(-y*.5+.5)*innerHeight}px) translate(-50%,-100%)`;},
  element:hud,
 };
}

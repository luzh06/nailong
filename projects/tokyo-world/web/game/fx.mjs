// 转场与声音：快门叶片、纸色/墨色幕布、提示条；书页音效与合成的烟花声。
const base=new URL('./',import.meta.url).href;
const wait=ms=>new Promise(r=>setTimeout(r,ms));
export {wait};
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- 声音 ----------
// 浏览器只允许在用户点击/按键之后创建声音；之前的调用直接跳过，不报警告
let actx=null,master=null,activated=false;
for(const ev of ['pointerdown','keydown'])addEventListener(ev,e=>{if(e.isTrusted)activated=true;},{capture:true,passive:true});
function audio(){if(!actx){if(!activated)return null;try{actx=new AudioContext();master=actx.createGain();master.gain.value=.8;master.connect(actx.destination);}catch{return null;}}if(actx.state==='suspended')actx.resume().catch(()=>{});return actx;}
const raw=new Map(),buffers=new Map();
const fetchRaw=name=>{if(!raw.has(name))raw.set(name,fetch(base+'audio/'+name+'.wav').then(r=>r.arrayBuffer()).catch(()=>null));return raw.get(name);};
async function load(name,ctx){if(!buffers.has(name))buffers.set(name,fetchRaw(name).then(b=>b?ctx.decodeAudioData(b.slice(0)):null).catch(()=>null));return buffers.get(name);}
export async function sfx(name,{volume=.5,rate=1}={}){const ctx=audio();if(!ctx)return;const b=await load(name,ctx);if(!b)return;
 const s=ctx.createBufferSource();s.buffer=b;s.playbackRate.value=rate;const g=ctx.createGain();g.gain.value=volume;s.connect(g).connect(master);s.start();}
// 预先下载音效文件（不创建 AudioContext）
export function preloadSfx(){['book-open','book-close','page-left','page-right','entry-reveal','camera-shutter'].forEach(fetchRaw);}
// 远处烟花：低频闷响 + 细碎噼啪
export function boom(distance=1){const ctx=audio();if(!ctx)return;const t=ctx.currentTime+Math.min(.9,distance*.25);
 const len=1.6,buf=ctx.createBuffer(1,ctx.sampleRate*len,ctx.sampleRate),d=buf.getChannelData(0);
 for(let i=0;i<d.length;i++){const k=i/d.length;d[i]=(Math.random()*2-1)*Math.pow(1-k,3);}
 const n=ctx.createBufferSource();n.buffer=buf;const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=180;
 const g=ctx.createGain();g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.55/distance,t+.02);g.gain.exponentialRampToValueAtTime(.0001,t+1.5);
 n.connect(lp).connect(g).connect(master);n.start(t);
 const c=ctx.createBufferSource();c.buffer=buf;const hp=ctx.createBiquadFilter();hp.type='highpass';hp.frequency.value=2400;const g2=ctx.createGain();
 g2.gain.setValueAtTime(.0001,t+.25);g2.gain.exponentialRampToValueAtTime(.07/distance,t+.35);g2.gain.exponentialRampToValueAtTime(.0001,t+1.4);
 c.connect(hp).connect(g2).connect(master);c.start(t+.2);}
// 环境底噪：很轻的风声，给街巷一点空气感
let ambience=null;
export function startAmbience(){const ctx=audio();if(!ctx||ambience)return;const len=4,buf=ctx.createBuffer(2,ctx.sampleRate*len,ctx.sampleRate);
 for(let ch=0;ch<2;ch++){const d=buf.getChannelData(ch);let b=0;for(let i=0;i<d.length;i++){b=.985*b+.015*(Math.random()*2-1);d[i]=b*3;}}
 const s=ctx.createBufferSource();s.buffer=buf;s.loop=true;const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=700;const g=ctx.createGain();g.gain.value=0;
 s.connect(lp).connect(g).connect(master);s.start();g.gain.linearRampToValueAtTime(.12,ctx.currentTime+4);ambience={s,g};}
export function setAmbience(v){if(ambience&&actx)ambience.g.gain.linearRampToValueAtTime(v,actx.currentTime+2);}

// ---------- 画面转场 ----------
function el(cls,html=''){const e=document.createElement('div');e.className=cls;e.innerHTML=html;document.body.append(e);return e;}

// 快门：六片叶片向中心合拢 → 回调（切时段/换场景，被遮住）→ 张开
export async function shutter(mid,{hold=260}={}){
 const s=el('cj-shutter',Array.from({length:6},()=>'<i></i>').join(''));const blades=[...s.children];
 const close=reduced?0:520,open=reduced?0:620;
 blades.forEach((b,i)=>{b.style.opacity=1;b.animate([{transform:`rotate(${i*60}deg) translateY(-118vmax) skewX(-28deg)`},{transform:`rotate(${i*60+38}deg) translateY(-73vmax) skewX(-28deg)`}],{duration:close,easing:'cubic-bezier(.7,0,.84,0)',fill:'forwards'});});
 sfx('camera-shutter',{volume:.35,rate:.82});
 await wait(close);
 const fill=el('cj-curtain');fill.style.background='#0b0c0a';fill.style.transition='none';fill.classList.add('on');
 try{await mid?.();}finally{await wait(hold);}
 fill.style.transition='opacity .25s';fill.classList.remove('on');
 blades.forEach((b,i)=>b.animate([{transform:`rotate(${i*60+38}deg) translateY(-73vmax) skewX(-28deg)`},{transform:`rotate(${i*60+76}deg) translateY(-118vmax) skewX(-28deg)`}],{duration:open,easing:'cubic-bezier(.16,1,.3,1)',fill:'forwards'}));
 await wait(open);s.remove();setTimeout(()=>fill.remove(),300);
}

// 幕布：纸色或墨色淡入，可带一行标题；返回 { out() }
export async function curtain({color='#0b0c0a',caption='',eyebrow='',duration=900}={}){
 const c=el('cj-curtain',caption?`<div class="cap"><small>${eyebrow}</small>${caption}</div>`:'');c.style.background=color;c.style.setProperty('--d',duration+'ms');
 if(color.startsWith('#e')||color.startsWith('#f'))c.querySelector('.cap')?.style.setProperty('color','#4a3d2a');
 void c.offsetWidth;await wait(34);c.classList.add('on');await wait(duration);
 return{el:c,async out(d=duration){c.style.setProperty('--d',d+'ms');c.classList.remove('on');await wait(d);c.remove();}};
}

let toastTimer=0,toastEl=null;
export function toast(text,ms=2600){if(!toastEl)toastEl=el('cj-toast');toastEl.textContent=text;toastEl.classList.add('on');clearTimeout(toastTimer);toastTimer=setTimeout(()=>toastEl.classList.remove('on'),ms);}

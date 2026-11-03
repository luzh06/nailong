// 旅行图鉴（古书）：杭州/巴黎为此前旅程（预设已集齐），东京为本局实拍，悉尼为下一页。
// 已显影的条目显示插画，并在角上贴一张玩家真实拍下的照片。
import {SPOTS,SPOT_ORDER,PRESET_REGIONS,SYDNEY_ENTRIES} from './story-data.mjs';
import {sfx} from './fx.mjs';

const art=id=>new URL(`./art/${id}.webp`,import.meta.url).href;
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

export function createJournal({onDoor,onOpenChange}){
 const root=document.createElement('section');root.className='cj-journal';root.setAttribute('role','dialog');root.setAttribute('aria-label','旅行图鉴');
 root.innerHTML='<div class="cj-book"><button class="close" aria-label="合上图鉴">×</button><div class="cj-page l"></div><div class="cj-page r"></div><nav><button data-prev>A 上一页</button><span data-info></span><button data-next>D 下一页</button></nav></div>';
 document.body.append(root);
 const L=root.querySelector('.cj-page.l'),Rp=root.querySelector('.cj-page.r'),info=root.querySelector('[data-info]');
 const state={spread:1,collected:new Map(),fresh:new Set(),doorOpen:false,open:false,pairName:'',pairDone:false};
 const entryHtml=(id,title,caption,{locked=false,own=null,sealText='',fresh=false}={})=>
  `<div class="cj-entry${locked?' locked':''}${fresh?' fresh':''}"><div class="ph"><img src="${art(id)}" alt="">${own?`<img class="own" src="${own}" alt="你拍下的照片">`:''}</div>
   <div><b>${esc(title)}</b><span>${esc(caption)}</span><em>${id}</em></div>${sealText?`<i class="sealmark">${sealText}</i>`:''}</div>`;
 function regionPage(title,latin,entries,note){return `<h3>${title}<small>${latin}</small></h3><div class="rule"></div><div class="cj-entries">${entries}</div><p class="cj-pagenote">${note}</p>`;}
 function render(){
  if(state.spread===0){
   const [a,b]=PRESET_REGIONS;
   L.innerHTML=regionPage(a.region,a.latin,a.entries.map(e=>entryHtml(...e,{sealText:'已集'})).join(''),a.note);
   Rp.innerHTML=regionPage(b.region,b.latin,b.entries.map(e=>entryHtml(...e,{sealText:'已集'})).join(''),b.note);
  }else{
   const got=SPOT_ORDER.filter(id=>state.collected.has(id)).length;
   L.innerHTML=regionPage('东京','TOKYO',SPOT_ORDER.map(id=>{const s=SPOTS[id],c=state.collected.get(id);return entryHtml(id,s.title,c?s.caption:s.hint,{locked:!c,own:c?.url,sealText:c?'显影':'',fresh:state.fresh.has(id)});}).join(''),
    `本段留影 ${got}/3${state.pairName?(state.pairDone?` · 已与${esc(state.pairName)}交换照片`:` · ${esc(state.pairName)}还在这座城市的某处`):''}`);
   Rp.innerHTML=regionPage('悉尼','SYDNEY',SYDNEY_ENTRIES.map(e=>entryHtml(e[0],e[1],'这一页还没有显影。',{locked:true})).join(''),'')+
    `<div class="cj-door"${state.doorOpen?'':' hidden'} role="button" tabindex="0">书页门已经显出悉尼<br><small>点击，翻向下一页</small></div>`;
   const door=Rp.querySelector('.cj-door');door.onclick=()=>{close();onDoor?.();};door.onkeydown=e=>{if(e.key==='Enter')door.click();};
  }
  state.fresh.clear();
  info.textContent=state.spread===0?'此前的旅程':'当前旅程';
  root.querySelector('[data-prev]').disabled=state.spread===0;root.querySelector('[data-next]').disabled=state.spread===1;
 }
 function turn(d){const n=Math.max(0,Math.min(1,state.spread+d));if(n===state.spread)return;state.spread=n;sfx(d>0?'page-right':'page-left',{volume:.4});render();}
 function open(spread=1){if(state.open)return;state.spread=spread;render();state.open=true;root.classList.add('on');sfx('book-open',{volume:.45});onOpenChange?.(true);}
 function close(){if(!state.open)return;state.open=false;root.classList.remove('on');sfx('book-close',{volume:.35});onOpenChange?.(false);}
 root.querySelector('.close').onclick=close;root.querySelector('[data-prev]').onclick=()=>turn(-1);root.querySelector('[data-next]').onclick=()=>turn(1);
 root.addEventListener('click',e=>{if(e.target===root)close();});
 addEventListener('keydown',e=>{if(!state.open)return;if(e.code==='Escape'||e.code==='KeyJ'){e.preventDefault();e.stopPropagation();close();}else if(e.code==='KeyA'||e.code==='ArrowLeft')turn(-1);else if(e.code==='KeyD'||e.code==='ArrowRight')turn(1);},true);
 return{open,close,toggle(){state.open?close():open();},
  collect(id,url){state.collected.set(id,{url});state.fresh.add(id);},
  setPair(name,done){state.pairName=name;state.pairDone=done;},
  setDoor(v){state.doorOpen=v;},
  get open_(){return state.open;},get isOpen(){return state.open;},
  get count(){return state.collected.size;},has:id=>state.collected.has(id),photo:id=>state.collected.get(id)?.url};
}

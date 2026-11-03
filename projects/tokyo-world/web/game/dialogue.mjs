// 对话面板：逐字显示、立绘、选项（数字键 / 点击），空格或 F / 回车翻页。
import {ROLES} from './story-data.mjs';
import {sfx} from './fx.mjs';

const img=id=>new URL(`./img/bust-${id}.webp`,import.meta.url).href;

export function createDialogue({container=document.body}={}){
 const root=document.createElement('section');root.className='cj-dialogue';root.setAttribute('role','dialog');root.setAttribute('aria-live','polite');
 root.innerHTML='<div class="sheet"><div class="bust"><img alt=""></div><div class="body"><div class="who"><b></b><small></small></div><div class="text"></div><div class="opts"></div><div class="next" hidden>空格 继续</div></div></div>';
 container.append(root);
 const $=s=>root.querySelector(s),bust=$('.bust img'),name=$('.who b'),latin=$('.who small'),text=$('.text'),opts=$('.opts'),next=$('.next');
 let me='rin',typing=null,advance=null,open=false;

 function speaker(line,npc){
  if(line.who==='narr'){bust.style.opacity=0;name.textContent='';latin.textContent='';text.classList.add('narr');return;}
  const id=line.who==='me'?me:(line.id||npc);const r=ROLES[id];
  text.classList.remove('narr');if(bust.dataset.id!==id){bust.src=img(id);bust.dataset.id=id;}bust.style.opacity=1;name.textContent=r.name;latin.textContent=r.latin;
 }
 // 逐字：再按一次直接显示全句
 function type(str){return new Promise(res=>{let i=0,t=0;text.textContent='';
  const finish=()=>{clearTimeout(t);text.textContent=str;typing=null;res();};typing={finish};
  const step=()=>{i+=2;text.textContent=str.slice(0,i);if(i>=str.length)finish();else t=setTimeout(step,28);};t=setTimeout(step,28);});}
 async function line(l,npc){speaker(l,npc);opts.innerHTML='';next.hidden=true;
  const done=type(l.text);await done;next.hidden=false;await new Promise(r=>{advance=r;});next.hidden=true;sfx('page-right',{volume:.12,rate:1.4});}
 function onKey(e){if(!open)return;
  if(['Space','Enter','KeyF'].includes(e.code)){e.preventDefault();e.stopPropagation();if(typing){typing.finish?.();return;}if(advance){const a=advance;advance=null;a();}return;}
  const n=Number(e.key);if(n>=1&&n<=opts.children.length){e.preventDefault();opts.children[n-1].click();}
 }
 addEventListener('keydown',onKey,true);
 root.addEventListener('click',e=>{if(e.target.closest('button'))return;if(typing){typing.finish?.();return;}if(advance){const a=advance;advance=null;a();}});

 function show(){open=true;root.classList.add('on');}
 function hide(){open=false;root.classList.remove('on');advance=null;}
 async function lines(list,npc){show();for(const l of list)await line(l,npc);}
 // 三组选项：非 key 的回应后回到选项；key 的回应后返回 'advance'；leave 返回 'leave'
 async function hub(prompt,options,npc,{leave='先告辞'}={}){show();const seen=new Set();
  for(;;){speaker({who:'narr'},npc);text.classList.add('narr');next.hidden=true;await type(prompt);
   const pick=await new Promise(res=>{opts.innerHTML='';
    [...options.map((o,i)=>({...o,i})),{label:leave,leave:true}].forEach((o,k)=>{const b=document.createElement('button');b.innerHTML=`<span>${k+1}</span>`;b.append(o.label);
     if(seen.has(o.i))b.classList.add('seen');if(o.key)b.classList.add('key');b.onclick=()=>res(o);opts.append(b);});
    opts.firstChild?.focus({preventScroll:true});});
   opts.innerHTML='';
   if(pick.leave)return 'leave';
   seen.add(pick.i);await lines([{who:'me',text:pick.label.replace(/^“|”$/g,'')},...pick.reply],npc);
   if(pick.key)return 'advance';
  }
 }
 return{lines,hub,show,hide,setPlayer(id){me=id;},get open(){return open;},dispose(){removeEventListener('keydown',onKey,true);root.remove();}};
}

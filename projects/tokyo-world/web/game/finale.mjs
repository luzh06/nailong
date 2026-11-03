// 终章（书页章节）：悉尼三页插画 → 海滩重逢 → 首次认识另外两人 → 四块文化头像拼图合成回忆卡 → 下载 / 再来一次。
// 悉尼尚无可行走场景，本章以图鉴插画与对白呈现，不冒充实景地图。
// 拼图卡面、裁切路径与合成节奏移植自团队交付的《此间 · 回忆卡》页面。
import {ROLES,finaleScript} from './story-data.mjs';
import {createDialogue} from './dialogue.mjs';
import {sfx,wait} from './fx.mjs';

const art=id=>new URL(`./art/${id}.webp`,import.meta.url).href;
const W=1600,H=1200;
const NAMES=['林川','凛','Camille','Noah'],CULTURES=['中国 · CHINA','日本 · JAPAN','法国 · FRANCE','澳大利亚 · AUSTRALIA'];
const SHAPES=['M32 0H800V220C800 220 870 220 870 300C870 380 800 380 800 380V600H480C480 600 480 670 400 670C320 670 320 600 320 600H0V32Q0 0 32 0Z',
 'M800 0H1568Q1600 0 1600 32V600H1280C1280 600 1280 530 1200 530C1120 530 1120 600 1120 600H800V380C800 380 870 380 870 300C870 220 800 220 800 220V0Z',
 'M0 600H320C320 600 320 670 400 670C480 670 480 600 480 600H800V820C800 820 730 820 730 900C730 980 800 980 800 980V1200H32Q0 1200 0 1168Z',
 'M800 600H1120C1120 600 1120 530 1200 530C1280 530 1280 600 1280 600H1600V1168Q1600 1200 1568 1200H800V980C800 980 730 980 730 900C730 820 800 820 800 820V600Z'];
const PIECE_OF={linchuan:0,rin:1,camille:2,noah:3};
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)),ease=x=>1-Math.pow(1-clamp(x),3);

function spaced(c,text,x,y,sp){const L=[...text];const w=L.reduce((s,l)=>s+c.measureText(l).width,0)+sp*(L.length-1);let p=x-w/2;for(const l of L){c.fillText(l,p,y);p+=c.measureText(l).width+sp;}}
function buildCard(img){const card=document.createElement('canvas');card.width=W;card.height=H;const cc=card.getContext('2d');
 cc.fillStyle='#f1e4c7';cc.fillRect(0,0,W,H);let seed=231;for(let i=0;i<22000;i++){seed=(seed*1664525+1013904223)>>>0;const x=seed%W;seed=(seed*1664525+1013904223)>>>0;const y=seed%H;cc.fillStyle=i%2?'#6e572308':'#ffffff18';cc.fillRect(x,y,1.7,1.7);}
 cc.drawImage(img,40,100,1520,1000);cc.strokeStyle='#9a783b';cc.lineWidth=2;cc.strokeRect(22,22,W-44,H-44);cc.strokeRect(31,31,W-62,H-62);
 cc.textAlign='center';cc.fillStyle='#614d2f';cc.font='34px "KaiTi",serif';spaced(cc,'此间 · 回忆卡',800,67,8);cc.font='16px Georgia,serif';spaced(cc,'CIJIAN  /  FOUR MEMORIES, ONE JOURNEY',800,1154,4);
 for(let i=0;i<4;i++){const x=i%2?800:40,y=i<2?100:600,cx=i%2?1190:410;const g=cc.createLinearGradient(0,y+338,0,y+500);g.addColorStop(0,'#1b221b00');g.addColorStop(1,'#131c19dd');cc.fillStyle=g;cc.fillRect(x,y+338,760,162);
  cc.fillStyle='#f9efd9';cc.font=i<2?'42px "KaiTi",serif':'italic 39px Georgia,serif';cc.fillText(NAMES[i],cx,y+438);cc.fillStyle='#ddc69c';cc.font='17px "Microsoft YaHei",sans-serif';spaced(cc,CULTURES[i],cx,y+472,4);}
 const paths=SHAPES.map(p=>new Path2D(p));cc.strokeStyle='#e4c58d';cc.lineWidth=2;for(const p of paths)cc.stroke(p);
 const pieces=paths.map(p=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');g.save();g.clip(p);g.drawImage(card,0,0);g.restore();g.strokeStyle='#e4c58d';g.lineWidth=2;g.stroke(p);return c;});
 return{card,pieces,paths};}

// 四块按顺序飞入：玩家的那一块最先（玩家按下放入），NPC 依次自动放入
function animatePuzzle(canvas,{card,pieces,paths},order,onPlace){const ctx=canvas.getContext('2d');const centers=[[400,300],[1200,300],[400,900],[1200,900]],offsets=[[-300,-180],[300,-180],[-300,180],[300,180]];
 const DUR=10;let time=0,last=performance.now(),placed=0;
 return new Promise(res=>{function size(){const r=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(r.width*d);canvas.height=Math.round(r.height*d);}
  size();
  function frame(n){time+=Math.min(.05,(n-last)/1000);last=n;const cw=canvas.width,ch=canvas.height;ctx.clearRect(0,0,cw,ch);
   let scale=Math.min(cw/(W+700),ch/(H+360));const settle=ease((time-7.4)/2.2);scale*=1+settle*.24;
   ctx.save();ctx.translate(cw/2,ch/2);ctx.scale(scale,scale);
   ctx.save();ctx.translate(-W/2,-H/2);ctx.globalAlpha=.1;ctx.fillStyle='#d4bb87';for(const p of paths)ctx.fill(p);ctx.restore();
   let done=0;
   order.forEach((i,k)=>{const start=.5+k*1.5,p=ease((time-start)/2);if(p>=1)done++;const appear=ease((time-start+.5)/.6);
    ctx.save();ctx.globalAlpha=appear;ctx.translate(-W/2+offsets[i][0]*(1-p),-H/2+offsets[i][1]*(1-p));ctx.translate(...centers[i]);ctx.rotate((i%2?1:-1)*.07*(1-p));ctx.translate(-centers[i][0],-centers[i][1]);
    ctx.shadowColor='rgba(0,0,0,.5)';ctx.shadowBlur=28*(1-p)+5;ctx.shadowOffsetY=12*(1-p);ctx.drawImage(pieces[i],0,0);ctx.restore();});
   if(done>placed){placed=done;onPlace?.(placed);}
   const gl=ease((time-7)/.9)*(1-ease((time-8.4)/1));
   if(gl>0){ctx.save();ctx.translate(-W/2,-H/2);ctx.globalCompositeOperation='lighter';ctx.globalAlpha=gl*.35;ctx.fillStyle='#ffe2a8';ctx.fillRect(0,0,W,H);ctx.restore();}
   if(time>=8.4){ctx.save();ctx.translate(-W/2,-H/2);ctx.globalAlpha=ease((time-8.4)/1.2);ctx.drawImage(card,0,0);ctx.restore();}
   ctx.restore();
   if(time<DUR)requestAnimationFrame(frame);else{removeEventListener('resize',size);res();}}
  addEventListener('resize',size);requestAnimationFrame(frame);});}

export async function playFinale({roleId,photos,onReplay,onAlbum}){
 const r=ROLES[roleId],script=finaleScript(roleId);
 const root=document.createElement('section');root.className='cj-finale';root.setAttribute('aria-label','终章 · 悉尼');
 root.innerHTML='<button class="cj-skip">跳过旁白 ›</button>';document.body.append(root);
 const dlg=createDialogue({container:root});dlg.setPlayer(roleId);
 let skip=false;root.querySelector('.cj-skip').onclick=()=>{skip=true;};
 const pause=ms=>new Promise(res=>{const t0=performance.now();const iv=setInterval(()=>{if(skip||performance.now()-t0>ms){clearInterval(iv);res();}},50);});
 void document.body.offsetWidth;await wait(34);root.classList.add('on');await wait(1200);
 let scene=null;
 for(const page of script.pages){const s=document.createElement('div');s.className='cj-scene';
  s.innerHTML=`<div class="bg" style="background-image:url(${art(page.art)})"></div><div class="shade"></div><div class="cap"><small>${page.eyebrow}</small><h2>${page.title}</h2><p>${page.text}</p></div>`;
  root.insertBefore(s,root.firstChild);void document.body.offsetWidth;await wait(34);s.classList.add('on');sfx('page-right',{volume:.4});
  if(scene){const old=scene;setTimeout(()=>old.remove(),1700);}scene=s;await pause(page===script.pages[2]?4200:6200);}
 skip=false;root.querySelector('.cj-skip').hidden=true;
 scene.querySelector('.cap').style.opacity=0;
 await dlg.lines(script.reunion,r.partner);
 await dlg.lines(script.intro,r.partner);
 dlg.hide();
 // 拼图
 const img=new Image();img.src=art('memory-card-art');await img.decode().catch(()=>{});
 const built=buildCard(img);
 const wrap=document.createElement('div');wrap.className='cj-pieces';wrap.innerHTML='<canvas aria-label="四块文化背景与人物头像拼图合成回忆卡"></canvas>';
 const title=document.createElement('div');title.className='cj-endtitle';title.innerHTML='<h2>回忆，在此相逢</h2><p>四个人 · 四段来处 · 一张回忆卡</p>';
 const bar=document.createElement('div');bar.className='cj-endbar';
 bar.innerHTML='<button class="cj-btn primary" data-save>保存回忆卡</button><button class="cj-btn" data-album>我的东京相册</button><button class="cj-btn" data-again>再读一次</button>';
 scene.style.transition='opacity 1.6s';scene.style.opacity=.18;root.append(wrap,title,bar);
 void document.body.offsetWidth;await wait(34);wrap.classList.add('on');title.classList.add('on');
 const mine=PIECE_OF[roleId],order=[mine,...[0,1,2,3].filter(i=>i!==mine)];
 await animatePuzzle(wrap.querySelector('canvas'),built,order,n=>sfx(n===4?'entry-reveal':'page-left',{volume:n===4?.5:.3,rate:1.1}));
 title.querySelector('p').textContent=`${r.name}的旅程，在南方的海边完成。回到入书的那一刻，照片还在书里。`;
 bar.classList.add('on');
 bar.querySelector('[data-save]').onclick=()=>built.card.toBlob(b=>{const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='此间_回忆卡.png';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),3000);},'image/png');
 bar.querySelector('[data-album]').onclick=()=>onAlbum?.();
 bar.querySelector('[data-again]').onclick=()=>onReplay?.();
 return root;
}

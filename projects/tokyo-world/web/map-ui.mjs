const DEFAULT_BOUNDS={eastMin:-137,eastMax:22,northMin:-88,northMax:71};

export function worldToMap(position,bounds=DEFAULT_BOUNDS){
 const east=-position.z-32.5,north=1.8-position.x;
 return {x:(east-bounds.eastMin)/(bounds.eastMax-bounds.eastMin),y:(bounds.northMax-north)/(bounds.northMax-bounds.northMin),east,north};
}
export function headingToMap(direction){return Math.atan2(direction.x,-direction.z)*180/Math.PI+90;}

function region(e,n){
 if(e>=-54&&e<=-16&&n< -38)return '寺院参道';
 if(e> -32&&Math.abs(n)<12)return '夕焼けだんだん';
 if(e> -64&&e< -50&&n> -12&&n<15)return '谷中十字路口';
 if(n>13)return '北侧背巷';
 if(n< -13)return '南侧街区';
 return '谷中银座';
}

export function createMapUI({container=document.body,mapBounds=DEFAULT_BOUNDS,onClose=()=>{}}={}){
 const cssURL=new URL('./map-ui.css',import.meta.url).href;
 let stylesheet=document.querySelector('link[data-cijian-map-style]');
 if(!stylesheet){stylesheet=document.createElement('link');stylesheet.rel='stylesheet';stylesheet.href=cssURL;stylesheet.dataset.cijianMapStyle='';document.head.append(stylesheet);}
 const root=document.createElement('section');root.className='cijian-map';root.setAttribute('aria-label','谷中位置地图');
 root.innerHTML=`<div class="cijian-map-shade"></div><div class="cijian-map-card" role="group" aria-label="谷中地图">
  <header class="cijian-map-head"><div><span class="cijian-map-eyebrow">FIELD NOTES / 01</span><h2>谷中散策図</h2></div><div class="cijian-map-actions"><button type="button" data-map-expand aria-label="展开地图" title="展开地图 · M"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7 3H3v4m10-4h4v4M3 13v4h4m6 0h4v-4"/></svg></button><button type="button" data-map-hide aria-label="收起小地图" title="收起小地图"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m5 5 10 10M15 5 5 15"/></svg></button></div></header>
  <div class="cijian-map-stage"><img class="cijian-map-art" alt="从实际三维模型正投影绘制的建筑、道路与台阶" draggable="false"><svg class="cijian-map-overlay" viewBox="0 0 1000 1000" aria-hidden="true"><g class="cijian-map-position"><circle class="cijian-map-halo" r="29"/><circle class="cijian-map-dot" r="11"/><g class="cijian-map-bearing"><path d="M0-45 12-17 0-23-12-17Z"/></g></g></svg><div class="cijian-map-compass" aria-label="地图上方是北方"><span>N</span><i></i></div><div class="cijian-map-scale"><i></i><span>20 m</span></div><span class="cijian-map-artnote">模型实测投影</span></div>
  <footer class="cijian-map-foot"><div class="cijian-map-location"><span class="cijian-map-mode">当前视角</span><strong class="cijian-map-region">谷中街区</strong></div><span class="cijian-map-coordinates"></span></footer>
  <p class="cijian-map-caption">以实际场景模型为准 · 浅草寺为创作拼接位置<br><span>纸纹来自生成美术；建筑、道路与标记均使用实际坐标。</span></p>
 </div><button class="cijian-map-reopen" type="button" aria-label="打开地图"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m2 5 5-2 6 2 5-2v12l-5 2-6-2-5 2Zm5-2v12m6-10v12"/></svg><span>散策図</span><kbd>M</kbd></button>`;
 root.querySelector('.cijian-map-art').src=new URL('./map/actual-map.png',import.meta.url).href;
 root.style.setProperty('--map-paper-image',`url("${new URL('./map/yanaka-atlas.png',import.meta.url).href}")`);
 root.querySelector('.cijian-map-scale i').style.width=`${20/(mapBounds.eastMax-mapBounds.eastMin)*100}%`;
 container.append(root);
 const card=root.querySelector('.cijian-map-card'),expand=root.querySelector('[data-map-expand]'),hide=root.querySelector('[data-map-hide]');
 const position=root.querySelector('.cijian-map-position'),bearing=root.querySelector('.cijian-map-bearing');
 const mode=root.querySelector('.cijian-map-mode'),location=root.querySelector('.cijian-map-region'),coordinates=root.querySelector('.cijian-map-coordinates');
 let expanded=false,hidden=false,previousFocus=null,lastText='';
 function setExpanded(next){
  if(next){hidden=false;previousFocus=document.activeElement;document.exitPointerLock?.();}
  expanded=next;root.classList.toggle('is-expanded',expanded);root.classList.remove('is-hidden');
  card.setAttribute('role',expanded?'dialog':'group');if(expanded)card.setAttribute('aria-modal','true');else card.removeAttribute('aria-modal');
  expand.setAttribute('aria-label',expanded?'缩小地图':'展开地图');expand.title=expanded?'缩小地图 · M':'展开地图 · M';
  if(expanded)hide.focus();else{previousFocus?.focus?.();onClose();}
  document.dispatchEvent(new CustomEvent('cijian:mapchange',{detail:{expanded}}));
 }
 function toggle(){if(hidden){hidden=false;root.classList.remove('is-hidden');return;}setExpanded(!expanded);}
 const close=()=>{if(expanded){setExpanded(false);return;}hidden=true;root.classList.add('is-hidden');onClose();};
 expand.addEventListener('click',toggle);hide.addEventListener('click',close);
 root.querySelector('.cijian-map-shade').addEventListener('click',()=>setExpanded(false));
 root.querySelector('.cijian-map-reopen').addEventListener('click',()=>{hidden=false;root.classList.remove('is-hidden');setExpanded(true);});
 const key=e=>{
  if(e.code==='KeyM'&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)){e.preventDefault();toggle();}
  if(expanded&&e.code==='Escape'){e.preventDefault();e.stopPropagation();setExpanded(false);}
  if(expanded&&e.code==='Tab'){e.preventDefault();(document.activeElement===hide?expand:hide).focus();}
 };
 document.addEventListener('keydown',key,true);
 const error=()=>{root.classList.add('map-unavailable');root.querySelector('.cijian-map-artnote').textContent='地图底图未能载入';};
 root.querySelector('.cijian-map-art').addEventListener('error',error);
 function update(cameraPosition,cameraDirection,walking=false){
  const p=worldToMap(cameraPosition,mapBounds),outside=p.x<0||p.x>1||p.y<0||p.y>1;
  position.setAttribute('transform',`translate(${Math.max(.018,Math.min(.982,p.x))*1000} ${Math.max(.018,Math.min(.982,p.y))*1000})`);
  bearing.setAttribute('transform',`rotate(${headingToMap(cameraDirection)})`);
  root.classList.toggle('is-walking',walking);root.classList.toggle('is-outside',outside);
  const text=`${walking}|${outside}|${region(p.east,p.north)}|${Math.round(cameraPosition.y*10)/10}`;
  if(text!==lastText){lastText=text;mode.textContent=walking?'你在这里':'当前视角';location.textContent=outside?'视角位于地图范围外':region(p.east,p.north);coordinates.textContent=`${cameraPosition.y.toFixed(1)} m`;
   coordinates.title=walking?'当前镜头高度（模型坐标）':'观察镜头高度（模型坐标）';}
 }
 return {update,toggle,dispose(){document.removeEventListener('keydown',key,true);root.remove();},get expanded(){return expanded;},element:root};
}

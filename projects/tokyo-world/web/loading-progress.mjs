// Same-origin Resource Timing reports bytes actually read, including image
// requests made by TextureLoader. Never infer completion from file counts.
export function createLoadingProgress(manifest){
 performance.setResourceTimingBufferSize(2048);
 const expected=new Map(manifest.assets.map(a=>[new URL(a.url,import.meta.url).href,a.bytes]));
 const completed=new Set();let bytes=0,phase='读取街区数据';
 const msg=document.getElementById('msg'),bar=document.querySelector('#bar i');
 const draw=()=>{if(!msg?.isConnected)return;msg.textContent=phase+' · 已读取 '+(bytes/1048576).toFixed(1)+' MB';if(bar)bar.style.width=Math.min(100,bytes/manifest.totalBytes*100)+'%';};
 const consume=entries=>{for(const e of entries){if(!expected.has(e.name)||completed.has(e.name))continue;completed.add(e.name);bytes+=e.decodedBodySize||e.encodedBodySize||0;}draw();};
 const observer=typeof PerformanceObserver==='function'?new PerformanceObserver(list=>consume(list.getEntries())):null;
 observer?.observe({type:'resource',buffered:true});draw();
 return {setPhase(text){phase=text;draw();},finish(){consume(performance.getEntriesByType('resource'));observer?.disconnect();},get bytes(){return bytes;}};
}

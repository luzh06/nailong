import {mountSelection} from './selection.js';
const selection=document.querySelector('#selection-scene'),library=document.querySelector('#library-scene');
let controller,scene='selection',switching=false;
const error=e=>{console.error(e);document.querySelector('#boot-error').hidden=false;document.querySelector('#boot-message').textContent='场景加载失败，请双击“启动开头.bat”重新打开。';};
function showScene(name){
 document.body.classList.remove('focused');document.body.dataset.scene=name;
 selection.hidden=name!=='selection';library.hidden=name!=='library';
 selection.inert=selection.hidden;library.inert=library.hidden;
 document.querySelector('#selection-css').disabled=name!=='selection';
 document.querySelector('#library-css').disabled=name!=='library';scene=name;
}
function freshCanvases(root){root.querySelectorAll('canvas').forEach(canvas=>canvas.replaceWith(canvas.cloneNode()));}
async function enterLibrary(roleId){
 if(switching||scene!=='selection')return;switching=true;
 try{
  const {mountLibrary}=await import('./library.js');
  controller.destroy();freshCanvases(library);showScene('library');
  const url=new URL(location);url.searchParams.set('role',roleId);url.hash='library';history.replaceState(null,'',url);
  controller=mountLibrary({root:library,roleId,onSelect:returnToSelection});
  dispatchEvent(new CustomEvent('cijian:opening-scene',{detail:{scene:'library',role:roleId}}));
 }catch(e){error(e)}finally{switching=false}
}
function returnToSelection(){
 if(switching||scene!=='library')return;switching=true;
 try{
  controller.destroy();freshCanvases(selection);showScene('selection');
  const url=new URL(location);url.searchParams.delete('role');url.hash='';history.replaceState(null,'',url);
  controller=mountSelection({root:selection,onConfirm:enterLibrary});
  dispatchEvent(new CustomEvent('cijian:opening-scene',{detail:{scene:'selection'}}));
 }catch(e){error(e)}finally{switching=false}
}
showScene('selection');controller=mountSelection({root:selection,onConfirm:enterLibrary});
window.CijianOpening={get scene(){return scene},get singlePage(){return true}};

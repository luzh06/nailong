// 第三人称相机：越肩跟随、滚轮拉近拉远、与真实碰撞三角面做相机避障；取景时切第一人称，过场时由镜头接管。
import * as THREE from 'three';
import {Capsule} from 'three/addons/Capsule.js';

const DIST_MIN=1.4,DIST_MAX=6,SHOULDER=.48,HEAD=1.58;
const damp=(a,b,k,dt)=>a+(b-a)*(1-Math.exp(-k*dt));

export function createRig({world,avatar}){
 const {camera,walkWorld,me}=world;
 const probe=new Capsule(new THREE.Vector3(),new THREE.Vector3(),.2);
 const target=new THREE.Vector3(),want=new THREE.Vector3(),dir=new THREE.Vector3(),right=new THREE.Vector3(),look=new THREE.Vector3();
 const state={dist:4,want:4,cur:4,mode:'third',cine:null,lastYaw:me.yaw,firstPersonBlend:0};

 // 从角色头部向相机方向逐段检测，遇到墙/屋檐就把相机拉近
 function clearDistance(from,dirN,max){
  const step=.2;
  const blocked=d=>{const p=from.clone().addScaledVector(dirN,d);probe.start.copy(p);probe.end.copy(p);return !!walkWorld.tree.capsuleIntersect(probe);};
  // 街区立面的碰撞是单层薄面，不能“穿过薄物体”，否则镜头会进到楼里；一碰到就拉近
  for(let d=.35;d<=max;d+=step)if(blocked(d))return Math.max(.6,d-.3);
  return max;
 }
 function headPos(out){return out.set(me.x,me.height+HEAD,-me.y);}
 function forward(out,pitch=me.pitch){const cp=Math.cos(pitch);return out.set(Math.cos(me.yaw)*cp,Math.sin(pitch),-Math.sin(me.yaw)*cp);}

 function update(dt,move){
  // 角色位置与朝向：朝移动方向转身
  avatar.place(me.x,me.height,-me.y);
  const sp=move?Math.hypot(move.x,move.y)/Math.max(dt,1e-4):0;
  if(move&&sp>.2)avatar.face(Math.atan2(move.x,-move.y));
  avatar.update(dt,sp);
  if(state.cine){cinematic(dt);return;}
  if(state.mode==='first'){ // 取景：眼睛位置
   camera.position.set(me.x,me.eye,-me.y);camera.up.set(0,1,0);camera.lookAt(look.copy(camera.position).add(forward(dir)));return;}
  headPos(target);
  const pitch=THREE.MathUtils.clamp(me.pitch,-1.05,1.0);
  forward(dir,pitch);right.set(Math.sin(me.yaw),0,Math.cos(me.yaw));// 角色右侧
  // 越肩点：头部右侧，低头时相机抬高
  const pivot=target.clone().addScaledVector(right,SHOULDER*Math.min(1,state.cur/2.4));
  const back=dir.clone().negate();
  const free=clearDistance(pivot,back,state.want);
  const goal=Math.min(state.want,free);
  state.cur=goal<state.cur?damp(state.cur,goal,22,dt):damp(state.cur,goal,3.5,dt);
  want.copy(pivot).addScaledVector(back,state.cur);
  const g=walkWorld.ground(want.x,-want.z);if(g!==null&&want.y<g+.35)want.y=g+.35;
  camera.position.copy(want);camera.up.set(0,1,0);camera.lookAt(look.copy(pivot).addScaledVector(dir,2));
  // 相机太近时把人物淡掉，避免穿模
  avatar.model.visible=state.cur>.75;
 }
 // 过场镜头：{from:Vector3,to:Vector3,lookA,lookB,t,dur}
 function cinematic(dt){const c=state.cine;c.t=Math.min(c.dur,c.t+dt);const k=c.dur?THREE.MathUtils.smootherstep(c.t/c.dur,0,1):1;
  camera.position.lerpVectors(c.from,c.to,k);look.lerpVectors(c.lookA,c.lookB,k);camera.up.set(0,1,0);camera.lookAt(look);avatar.model.visible=true;}
 return{
  update,
  zoom(deltaY){if(state.mode!=='third'||state.cine)return false;state.want=THREE.MathUtils.clamp(state.want+deltaY*.004,DIST_MIN,DIST_MAX);return true;},
  setFirstPerson(on){state.mode=on?'first':'third';},
  // 过场：从当前相机平滑移动到 to，看向 lookAt
  shot(to,lookAt,dur=1.6){const l=new THREE.Vector3();camera.getWorldDirection(l).multiplyScalar(4).add(camera.position);
   state.cine={from:camera.position.clone(),to:to.clone(),lookA:state.cine?state.cine.lookB.clone():l,lookB:lookAt.clone(),t:0,dur};},
  release(){state.cine=null;},
  get cinematic(){return !!state.cine;},
  headPosition:()=>headPos(new THREE.Vector3()),
 };
}

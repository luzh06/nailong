// 烟花：CPU 模拟的点粒子，HDR 颜色进入既有泛光链；三种花型（牡丹、垂柳金、千轮）。
import * as THREE from 'three';
import {boom} from './fx.mjs';

const MAX=9000;
// 饱和的花色：经过 AgX 和夜色调后仍能看出颜色
const PALETTES=[[[1,.32,.08],[1,.62,.18]],[[1,.16,.42],[1,.5,.72]],[[.25,.5,1],[.62,.82,1]],[[1,.72,.2],[1,.4,.1]],[[.4,1,.35],[.9,1,.5]],[[.75,.3,1],[1,.55,.9]]];

export function createFireworks({center,onFlash}){
 const pos=new Float32Array(MAX*3),col=new Float32Array(MAX*3),size=new Float32Array(MAX),alpha=new Float32Array(MAX);
 const vel=new Float32Array(MAX*3),life=new Float32Array(MAX),maxLife=new Float32Array(MAX),drag=new Float32Array(MAX),grav=new Float32Array(MAX),trail=new Uint8Array(MAX),base=new Float32Array(MAX*3);
 const geo=new THREE.BufferGeometry();
 geo.setAttribute('position',new THREE.BufferAttribute(pos,3).setUsage(THREE.DynamicDrawUsage));
 geo.setAttribute('color',new THREE.BufferAttribute(col,3).setUsage(THREE.DynamicDrawUsage));
 geo.setAttribute('size',new THREE.BufferAttribute(size,1).setUsage(THREE.DynamicDrawUsage));
 geo.setAttribute('alpha',new THREE.BufferAttribute(alpha,1).setUsage(THREE.DynamicDrawUsage));
 const mat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,uniforms:{uScale:{value:innerHeight}},
  vertexShader:'attribute float size;attribute float alpha;attribute vec3 color;varying vec3 vC;varying float vA;uniform float uScale;void main(){vC=color;vA=alpha;vec4 mv=modelViewMatrix*vec4(position,1.);gl_PointSize=max(1.5,size*uScale/-mv.z);gl_Position=projectionMatrix*mv;}',
  fragmentShader:'varying vec3 vC;varying float vA;void main(){vec2 d=gl_PointCoord-.5;float r=length(d);float a=smoothstep(.5,.0,r);a*=a;gl_FragColor=vec4(vC*a*vA,1.);}'});
 const points=new THREE.Points(geo,mat);points.frustumCulled=false;points.renderOrder=5;
 let head=0,timer=1.2,running=false,flash=0;const shells=[];
 function spawn(x,y,z,vx,vy,vz,c,l,s,d,g,t){const i=head;head=(head+1)%MAX;pos[i*3]=x;pos[i*3+1]=y;pos[i*3+2]=z;vel[i*3]=vx;vel[i*3+1]=vy;vel[i*3+2]=vz;
  base[i*3]=c[0];base[i*3+1]=c[1];base[i*3+2]=c[2];life[i]=l;maxLife[i]=l;size[i]=s;drag[i]=d;grav[i]=g;trail[i]=t;}
 function launch(){const x=center.x+(Math.random()-.5)*26,z=center.z+(Math.random()-.5)*12;const h=center.y+(Math.random()-.3)*10;
  shells.push({x,y:center.y-34,z,vy:24+Math.random()*4,top:h,type:Math.random(),pal:PALETTES[Math.floor(Math.random()*PALETTES.length)]});}
 function burst(s){const n=s.type<.4?220:s.type<.7?170:260,sp=s.type<.4?17:s.type<.7?12:19;const [a,b]=s.pal;
  for(let i=0;i<n;i++){const u=Math.random()*2-1,th=Math.random()*Math.PI*2,r=Math.sqrt(1-u*u),k=sp*(.85+Math.random()*.25);
   const c=Math.random()<.5?a:b,hdr=[c[0]*c[0]*4,c[1]*c[1]*4,c[2]*c[2]*4];
   if(s.type<.4)spawn(s.x,s.y,s.z,r*Math.cos(th)*k,u*k,r*Math.sin(th)*k,hdr,1.8+Math.random()*.6,1.15,1.5,4,0);
   else if(s.type<.7)spawn(s.x,s.y,s.z,r*Math.cos(th)*k,u*k,r*Math.sin(th)*k,[4.2,2.2,.5],3.4+Math.random(),.8,2.4,2.2,1);
   else spawn(s.x,s.y,s.z,r*Math.cos(th)*k,u*k,r*Math.sin(th)*k,hdr,1.5+Math.random()*.4,.85,1.2,5,1);}
  spawn(s.x,s.y,s.z,0,0,0,[30,26,20],.22,7,0,0,0);
  flash=Math.min(1,flash+.7);boom(1.6);}
 function update(dt){
  if(running){timer-=dt;if(timer<=0){launch();if(Math.random()<.35)launch();timer=1.1+Math.random()*1.6;}}
  for(let k=shells.length-1;k>=0;k--){const s=shells[k];s.y+=s.vy*dt;s.vy-=9.8*dt*.6;spawn(s.x+(Math.random()-.5)*.1,s.y,s.z,0,-1,0,[4,2.6,1.2],.45,.22,3,0,0);
   if(s.y>=s.top||s.vy<4){burst(s);shells.splice(k,1);}}
  for(let i=0;i<MAX;i++){if(life[i]<=0){alpha[i]=0;continue;}life[i]-=dt;const t=life[i]/maxLife[i],d=Math.exp(-drag[i]*dt);
   vel[i*3]*=d;vel[i*3+1]=vel[i*3+1]*d-grav[i]*dt;vel[i*3+2]*=d;pos[i*3]+=vel[i*3]*dt;pos[i*3+1]+=vel[i*3+1]*dt;pos[i*3+2]+=vel[i*3+2]*dt;
   const tw=trail[i]&&Math.random()<.5?.35:1;alpha[i]=Math.max(0,Math.min(1,t*1.6))*tw;col[i*3]=base[i*3];col[i*3+1]=base[i*3+1]*(.6+.4*t);col[i*3+2]=base[i*3+2]*(.4+.6*t);
   if(trail[i]&&Math.random()<dt*20&&t>.25)spawn(pos[i*3],pos[i*3+1],pos[i*3+2],0,-.4,0,[base[i*3]*.5,base[i*3+1]*.4,base[i*3+2]*.25],.6,size[i]*.6,2,1,0);}
  for(const a of ['position','color','alpha','size'])geo.attributes[a].needsUpdate=true;
  flash=Math.max(0,flash-dt*2.4);onFlash?.(flash);
  mat.uniforms.uScale.value=innerHeight;
 }
 return{points,update,start(){running=true;timer=.4;},stop(){running=false;},get running(){return running;},
  // 给拍照判定用：天空里一片烟花区域
  target:new THREE.Vector3(center.x,center.y,center.z)};
}

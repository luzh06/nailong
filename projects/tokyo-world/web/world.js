// 《此间》烘焙实时版。Blender 坐标 (x,y,z) -> three (x,z,-y)；+y 东（上台阶），+x 南。
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/GLTFLoader.js';
import {RGBELoader} from 'three/addons/RGBELoader.js';
import {EXRLoader} from 'three/addons/EXRLoader.js';
import {createMapUI} from './map-ui.mjs';
import {WalkWorld} from './collision.mjs';
import {createExperienceControls} from './experience-controls.mjs';
import {createLoadingProgress} from './loading-progress.mjs';

const q=new URLSearchParams(location.search);
const W=0,H=0;
const log=m=>console.info('[Cijian]',m);
const fatal=e=>{console.error(e);const target=$('msg')||$('hint');if(target)target.textContent='出现错误：'+(e?.message||e)+'。请刷新重试。';};
addEventListener('unhandledrejection',e=>fatal(e.reason));
addEventListener('error',e=>{if(e.message)fatal(new Error(e.message));});
const A='../'; // 开发和打包目录结构相同，都相对 web/ 取
const DATA='./data/';
const $=id=>document.getElementById(id);
const progress=createLoadingProgress(await (await fetch('./asset-manifest.json')).json());
const MAN=await (await fetch(DATA+'bk.json')).json();
const WORLD=await (await fetch('./world.json')).json();
const NAV=await (await fetch('./navigation.json')).json();
const collisionResponse=await fetch('./collision.bin');
if(!collisionResponse.ok)throw new Error('无法载入街区碰撞数据');
const collisionStart=performance.now();
const walkWorld=new WalkWorld(NAV,new Float32Array(await collisionResponse.arrayBuffer()));
log('collision ready '+Math.round(performance.now()-collisionStart)+' ms');
THREE.Cache.enabled=true;
const B=A+'bake/'+MAN.dir+'/',EXT=MAN.ext||'png';

// ---------- 光 ----------
const LIGHT={
 sunset:{hdr:'qwantani_sunset_puresky_4k.hdr',az:268,el:6.1,sun:7.5,col:[1,.58,.3],strength:.85,cap:9,exposure:.3,fog:.0010,fogc:[1,.8,.58],ground:[.2,.17,.16],bloom:.2,hgamb:.3}};
const ORDER=MAN.lights.filter(k=>LIGHT[k]);
const start=q.get('light')||ORDER[0];
function bl2three(x,y,z){return new THREE.Vector3(x,z,-y);}
function sunDir(L){const a=L.az*Math.PI/180,e=L.el*Math.PI/180;return bl2three(-Math.cos(a)*Math.cos(e),Math.sin(a)*Math.cos(e),Math.sin(e));}

const canvas=document.createElement('canvas');document.body.prepend(canvas);
const renderer=new THREE.WebGLRenderer({canvas,antialias:false,powerPreference:'high-performance'});
renderer.setPixelRatio(1);renderer.toneMapping=THREE.NoToneMapping;renderer.outputColorSpace=THREE.LinearSRGBColorSpace;
const gl=renderer.getContext();
const aniso=renderer.capabilities.getMaxAnisotropy();
const fsGeo=new THREE.BufferGeometry();fsGeo.setAttribute('position',new THREE.BufferAttribute(new Float32Array([-1,-1,0,3,-1,0,-1,3,0]),3));
const fsCam=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
function fsPass(frag,uniforms,defines={}){const m=new THREE.ShaderMaterial({uniforms,defines,depthTest:false,depthWrite:false,glslVersion:THREE.GLSL3,
 vertexShader:'out vec2 vUv;void main(){vUv=position.xy*.5+.5;gl_Position=vec4(position.xy,0,1);}',
 fragmentShader:'precision highp float;in vec2 vUv;out vec4 oc;'+frag});
 const s=new THREE.Scene(),o=new THREE.Mesh(fsGeo,m);o.frustumCulled=false;s.add(o);return{m,s,u:uniforms};}
function drawTo(p,rt){renderer.setRenderTarget(rt);renderer.render(p.s,fsCam);}

// ---------- 天空：按 Cycles 的方式旋转、封顶、加强度 ----------
const EQ=`vec2 eq(vec3 d){return vec2(-atan(d.y,d.x)/6.2831853+.5,asin(clamp(d.z,-1.,1.))/3.1415927+.5);}
vec3 rotz(vec3 d,float r){float c=cos(r),s=sin(r);return vec3(c*d.x-s*d.y,s*d.x+c*d.y,d.z);}`;
const FOGF=`vec3 fogLight(vec3 dir,vec3 sunD,vec3 sunE,vec3 amb,float g,vec3 c){float t=dot(dir,sunD);float h=(1.-g*g)/(12.566*pow(1.+g*g-2.*g*t,1.5));return c*(sunE*h*.22+amb);}`;
const skyLayer={};
async function loadSky(k){const L=LIGHT[k];const hdr=await new RGBELoader().loadAsync(A+'assets/hdri/'+L.hdr);hdr.minFilter=hdr.magFilter=THREE.LinearFilter;hdr.wrapS=THREE.RepeatWrapping;hdr.generateMipmaps=false;
 // 太阳在 HDRI 里的位置：取上半球最亮点
 const {data,width:w,height:h}=hdr.image;let best=0,bi=0;const half=data instanceof Uint16Array;const ds=half?THREE.DataUtils.fromHalfFloat:(x=>x);
 for(let r=0;r<h>>1;r++)for(let c=0;c<w;c++){const i=(r*w+c)*4,l=ds(data[i])+ds(data[i+1])+ds(data[i+2]);if(l>best){best=l;bi=r*w+c;}}
 const col=bi%w; // RGBE 数据从上往下，上半张是天
 const phi=(.5-(col+.5)/w)*2*Math.PI,a=L.az*Math.PI/180,target=Math.atan2(Math.sin(a),-Math.cos(a));
 skyLayer[k]={tex:hdr,rot:phi-target};return skyLayer[k];}
const skyU={tA:{value:null},tB:{value:null},rA:{value:0},rB:{value:0},cA:{value:new THREE.Vector2()},cB:{value:new THREE.Vector2()},uT:{value:0},
 uFog:{value:0},uSunD:{value:new THREE.Vector3()},uSunE:{value:new THREE.Vector3()},uAmb:{value:new THREE.Vector3()},uFogC:{value:new THREE.Vector3()},uG:{value:.55},uMaxD:{value:480}};
const SKYF=`uniform sampler2D tA,tB;uniform float rA,rB,uT,uFog,uG;uniform vec2 cA,cB;uniform vec3 uSunD,uSunE,uAmb,uFogC;${EQ}${FOGF}
vec3 sk(sampler2D t,vec3 d,float r,vec2 c){vec2 p=eq(rotz(d,r));return min(textureLod(t,p,0.).rgb,vec3(c.x))*c.y;}
vec3 sky(vec3 d){vec3 c=sk(tA,d,rA,cA);if(uT>0.)c=mix(c,sk(tB,d,rB,cB),uT);return c;}`;
const skyMat=new THREE.ShaderMaterial({uniforms:skyU,side:THREE.BackSide,depthWrite:false,depthTest:true,glslVersion:THREE.GLSL3,
 vertexShader:'out vec3 vD;void main(){vD=position;vec4 p=projectionMatrix*mat4(mat3(viewMatrix))*vec4(position,1.);gl_Position=p.xyww;}',
 fragmentShader:'precision highp float;in vec3 vD;layout(location=0) out vec4 oc;'+SKYF+`
 void main(){vec3 d=normalize(vec3(vD.x,-vD.z,vD.y));vec3 c=sky(d);
  vec3 dw=normalize(vD);float hz=length(dw.xz);float dist=min(480./max(hz,.001),max(0.,89.)/max(dw.y,.001));
  float T=exp(-uFog*dist);c=c*T+(1.-T)*fogLight(dw,uSunD,uSunE,uAmb,uG,uFogC);oc=vec4(c,1.);}`});
const sky=new THREE.Mesh(new THREE.SphereGeometry(10,32,16),skyMat);sky.frustumCulled=false;sky.renderOrder=-1;

// 反射环境：把旋转封顶后的天空转成 PMREM，下半球压成地面色
const pm=new THREE.PMREMGenerator(renderer);
const envRT=new THREE.WebGLRenderTarget(1024,512,{type:THREE.HalfFloatType,depthBuffer:false});envRT.texture.mapping=THREE.EquirectangularReflectionMapping;
const envU=Object.assign({uGround:{value:new THREE.Vector3()}},skyU);
const envP=fsPass(SKYF+`uniform vec3 uGround;void main(){vec2 uv=vec2(vUv.x,vUv.y);float ph=(uv.x-.5)*6.2831853,th=(uv.y-.5)*3.1415927;
 vec3 tdir=vec3(cos(th)*sin(ph),sin(th),-cos(th)*cos(ph));vec3 d=vec3(tdir.x,-tdir.z,tdir.y);
 vec3 c=sky(d);c=mix(uGround,c,smoothstep(-.04,.02,d.z));oc=vec4(c,1.);}`,envU);
let curEnv=null;
let probe=null;
function rebuildEnv(){let src=envRT.texture;if(probe){src=probe;}else{drawTo(envP,envRT);renderer.setRenderTarget(null);}const r=pm.fromEquirectangular(src);if(curEnv)curEnv.dispose();curEnv=r;scene.environment=r.texture;}

// ---------- 场景 ----------
const scene=new THREE.Scene();scene.add(sky);
const sun=new THREE.DirectionalLight(0xffffff,1);scene.add(sun,sun.target);
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
Object.assign(sun.shadow.camera,{left:-85,right:85,top:85,bottom:-85,near:1,far:400});
sun.shadow.normalBias=.04;sun.shadow.bias=-.0002;
const shared={uT:{value:0},uFog:{value:.001},uSunD:skyU.uSunD,uSunE:skyU.uSunE,uAmb:skyU.uAmb,uFogC:skyU.uFogC,uG:skyU.uG,uSunI:{value:new THREE.Vector3()}};
const gtx=new GLTFLoader();
const tl=new THREE.TextureLoader(),exr=new EXRLoader();exr.setDataType(THREE.HalfFloatType);
const tick=()=>{};
function loadTex(p,srgb){return tl.loadAsync(p).then(t=>{t.flipY=false;t.wrapS=t.wrapT=THREE.ClampToEdgeWrapping;t.anisotropy=Math.min(aniso,4);if(srgb)t.colorSpace=THREE.SRGBColorSpace;t.generateMipmaps=true;t.minFilter=THREE.LinearMipmapLinearFilter;tick();return t;});}
function loadExr(p){return exr.loadAsync(p).then(t=>{t.wrapS=t.wrapT=THREE.ClampToEdgeWrapping;t.minFilter=THREE.LinearFilter;t.magFilter=THREE.LinearFilter;t.generateMipmaps=false;tick();return t;});}

const PHYS=THREE.ShaderChunk.lights_physical_pars_fragment
 .replace('reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );','')
 .replace('reflectedLight.directSpecular += irradiance * BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );','PhysicalMaterial mS=material;mS.roughness=max(material.roughness,.3);reflectedLight.directSpecular += min(irradiance * BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, mS ),vec3(6.)) * uVisNow;');
function patch(mat,tex,plant){
 mat.onBeforeCompile=s=>{
  Object.assign(s.uniforms,shared,tex);
  s.vertexShader=s.vertexShader.replace('#include <common>',`#include <common>
   varying vec2 vLm;varying vec3 vWp;${plant?'attribute vec3 _lm_a;attribute vec3 _lm_b;varying vec3 vLa;varying vec3 vLb;':''}`)
   .replace('#include <begin_vertex>',`#include <begin_vertex>
   vLm=uv;vWp=(modelMatrix*vec4(position,1.)).xyz;${plant?'vLa=_lm_a;vLb=_lm_b;':''}`);
  s.fragmentShader=s.fragmentShader.replace('#include <common>',`#include <common>
   varying vec2 vLm;varying vec3 vWp;float uVisNow=1.;
   uniform float uT,uFog,uG;uniform vec3 uSunD,uSunE,uAmb,uFogC,uSunI;
   ${plant?'varying vec3 vLa;varying vec3 vLb;':'uniform sampler2D tLA,tLB,tVA,tVB;'}
   ${FOGF}`)
   .replace('#include <lights_physical_pars_fragment>',PHYS)
   .replace('#include <lights_fragment_begin>',`
   vec3 bakedLm;
   ${plant?`bakedLm=mix(vLa,vLb,uT);uVisNow=0.;`:`
    vec2 lmuv=vec2(vLm.x,1.-vLm.y);
    bakedLm=texture2D(tLA,lmuv).rgb;if(uT>0.)bakedLm=mix(bakedLm,texture2D(tLB,lmuv).rgb,uT);
    // 太阳可见度：烘的是 太阳直射/π，除回去
    vec3 vd=texture2D(tVA,lmuv).rgb;if(uT>0.)vd=mix(vd,texture2D(tVB,lmuv).rgb,uT);
    float ndl=max(dot(normalize(cross(dFdx(vWp),dFdy(vWp))),uSunD),.0);
    uVisNow=clamp(vd.r/max(uSunI.r*max(ndl,.02),1e-4),0.,1.);`}
   #include <lights_fragment_begin>`)
   .replace('#include <lights_fragment_maps>',`#include <lights_fragment_maps>
   #if defined( RE_IndirectDiffuse )
    irradiance=bakedLm*PI;
   #endif
   #if defined( USE_ENVMAP )
    iblIrradiance=vec3(0.);
    // 暗处的天空反射要压掉，没有反射探针时靠烘焙亮度近似
    radiance*=clamp(dot(bakedLm,vec3(.3,.5,.2))*6.,.25,1.);
   #endif`)
   .replace('#include <fog_fragment>',`{vec3 fv=vWp-cameraPosition;float fd=length(fv);float T=exp(-uFog*fd);
    gl_FragColor.rgb=gl_FragColor.rgb*T+(1.-T)*fogLight(fv/fd,uSunD,uSunE,uAmb,uG,uFogC);}`);
 };
 mat.customProgramCacheKey=()=>plant?'p':('s-'+(['ground','road_a','road_b','stone','apron','soil','pavers'].includes(mat.name)?'floor':'clip'));
}

async function build(){
 const t0=performance.now();
 const gltf=await gtx.loadAsync(DATA+'bk.glb');
 progress.setPhase('读取光照与贴图');
 const jobs=[];let meshes=0;
 const L0=ORDER[0],L1=ORDER[1]||ORDER[0];
 gltf.scene.traverse(o=>{ if(!o.isMesh)return;meshes++;
  const mn=o.material.name,g=o.name.startsWith('bk_')?o.name.slice(3):mn,f=MAN.groups[g];if(!f&&!MAN.plants.some(p=>mn.startsWith(p)))log('NOGROUP '+o.name+' '+mn);
  if(g==='far'){o.visible=false;return;}
  o.castShadow=o.name.startsWith('bk_')&&!['ground','road_a','road_b','stone','apron','soil','pavers'].includes(g);
  o.frustumCulled=true;
  if(f){
   const m=new THREE.MeshStandardMaterial({name:g,roughness:1,metalness:1});
   const tex={tLA:{value:null},tLB:{value:null},tVA:{value:null},tVB:{value:null}};
   patch(m,tex,false);o.material=m;
   const has=s=>f.includes(s.slice(1));
   if(has('_albedo.'+EXT))jobs.push(loadTex(B+g+'_albedo.'+EXT,true).then(t=>{m.map=t;}));
   if(has('_orm.'+EXT))jobs.push(loadTex(B+g+'_orm.'+EXT,false).then(t=>{m.roughnessMap=m.metalnessMap=t;}));
   if(has('_normal.'+EXT))jobs.push(loadTex(B+g+'_normal.'+EXT,false).then(t=>{m.normalMap=t;}));
   if(has('_emit.'+EXT)){m.emissive=new THREE.Color(1,1,1);jobs.push(loadTex(B+g+'_emit.'+EXT,true).then(t=>{m.emissiveMap=t;}));}
   jobs.push(loadExr(B+g+'_'+L0+'.exr').then(t=>{tex.tLA.value=t;if(L1===L0)tex.tLB.value=t;}));
   jobs.push(loadExr(B+g+'_'+L0+'_vis.exr').then(t=>{tex.tVA.value=t;if(L1===L0)tex.tVB.value=t;}));
   if(L1!==L0){jobs.push(loadExr(B+g+'_'+L1+'.exr').then(t=>{tex.tLB.value=t;}));jobs.push(loadExr(B+g+'_'+L1+'_vis.exr').then(t=>{tex.tVB.value=t;}));}
  }else{ // 植物
   const k=MAN.plants.find(p=>mn.startsWith(p))||mn;
   const m=new THREE.MeshStandardMaterial({name:k,side:THREE.DoubleSide,roughness:1,metalness:0});
   const a=o.geometry.attributes;a._lm_a=a['_lm_'+L0];a._lm_b=a['_lm_'+L1];
   if(a._lm_a){o.geometry.setAttribute('_lm_a',a._lm_a);o.geometry.setAttribute('_lm_b',a._lm_b);}
   patch(m,{},true);o.material=m;
   const P=A+'assets/models/'+k+'/textures/'+k;
   const wrap=t=>{t.wrapS=t.wrapT=THREE.RepeatWrapping;return t;};
   jobs.push(loadTex(P+'_diff_2k.jpg',true).then(t=>{m.map=wrap(t);}));
   jobs.push(loadTex(P+'_nor_gl_2k.jpg',false).then(t=>{m.normalMap=wrap(t);}));
   jobs.push(loadTex(P+'_arm_2k.jpg',false).then(t=>{m.roughnessMap=wrap(t);}));
  }
 });
 await Promise.all(jobs);
 scene.add(gltf.scene);
 await buildWorld();
 return{meshes,ms:performance.now()-t0};
}

// ---------- 后期：多级泛光 + AgX 查找表 ----------
let SW=W||innerWidth,SH=H||innerHeight;
const rtOpt={type:THREE.HalfFloatType,format:THREE.RGBAFormat,minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter,depthBuffer:false};
const hdrRT=new THREE.WebGLRenderTarget(SW,SH,{...rtOpt,depthBuffer:true,samples:4});
const QUALITY={low:{label:'流畅',dpr:.75,samples:0,shadow:1024,bloom:false},standard:{label:'标准',dpr:1,samples:2,shadow:2048,bloom:true},high:{label:'精细',dpr:Math.min(devicePixelRatio,1.5),samples:4,shadow:4096,bloom:true}};
let quality='standard';
const blackBloom=new THREE.DataTexture(new Uint8Array([0,0,0,255]),1,1);blackBloom.needsUpdate=true;
function applyQuality(key){
 quality=key;const p=QUALITY[key];renderer.setPixelRatio(p.dpr);hdrRT.dispose();hdrRT.samples=p.samples;hdrRT.setSize(Math.round(SW*p.dpr),Math.round(SH*p.dpr));
 sun.shadow.map?.dispose();sun.shadow.map=null;sun.shadow.mapSize.set(p.shadow,p.shadow);renderer.shadowMap.needsUpdate=true;
 $('quality').textContent='画质：'+p.label;$('quality').setAttribute('aria-label','当前画质'+p.label+'，点击切换');
}
const LV=6;const down=[],up=[];
function sizeChain(){let w=SW,h=SH;for(let i=0;i<LV;i++){w=Math.max(2,w>>1);h=Math.max(2,h>>1);if(!down[i]){down[i]=new THREE.WebGLRenderTarget(w,h,rtOpt);up[i]=new THREE.WebGLRenderTarget(w,h,rtOpt);}else{down[i].setSize(w,h);up[i].setSize(w,h);}}}
sizeChain();
const bright=fsPass(`uniform sampler2D t;uniform float th;void main(){vec3 c=texture(t,vUv).rgb;float l=max(c.r,max(c.g,c.b));oc=vec4(c*smoothstep(th*.75,th*1.25,l),1.);}`,{t:{value:null},th:{value:1.6}});
const dn=fsPass(`uniform sampler2D t;uniform vec2 px;void main(){vec3 c=texture(t,vUv).rgb*.25;for(int i=0;i<4;i++){vec2 s=vec2((i&1)*2-1,(i&2)-1)*px;c+=texture(t,vUv+s).rgb*.1875;}oc=vec4(c,1.);}`,{t:{value:null},px:{value:new THREE.Vector2()}});
const us=fsPass(`uniform sampler2D t,tb;uniform vec2 px;void main(){vec3 c=vec3(0.);for(int i=0;i<4;i++){vec2 s=vec2((i&1)*2-1,(i&2)-1)*px;c+=texture(tb,vUv+s).rgb*.25;}oc=vec4(texture(t,vUv).rgb+c,1.);}`,{t:{value:null},tb:{value:null},px:{value:new THREE.Vector2()}});
const LN=48;
const toneU={t:{value:hdrRT.texture},tBloom:{value:null},lutA:{value:null},lutB:{value:null},uT:shared.uT,uExp:{value:1},uBloom:{value:.35},uTime:{value:0},uGrade:{value:new THREE.Vector3(1,1,1)}};
const tone=fsPass(`precision highp sampler3D;uniform sampler2D t,tBloom;uniform sampler3D lutA,lutB;uniform float uT,uExp,uBloom,uTime;uniform vec3 uGrade;
 vec3 enc(vec3 c){return clamp((log2(max(c,vec3(1e-5)))+9.)/16.,0.,1.);}
 vec3 lut(sampler3D l,vec3 c){vec3 e=enc(c);e=e*(${(LN-1).toFixed(1)}/${LN.toFixed(1)})+.5/${LN.toFixed(1)};return texture(l,e).rgb;}
 float rnd(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
 void main(){vec3 c=texture(t,vUv).rgb;c+=texture(tBloom,vUv).rgb*uBloom;c*=uExp;
  vec3 o=lut(lutA,c);if(uT>0.)o=mix(o,lut(lutB,c),uT);o*=uGrade; // 游戏层的时段色调（夜晚偏蓝），默认 1
  o+=(rnd(gl_FragCoord.xy+uTime)-.5)/255.;oc=vec4(o,1.);}`,toneU);
async function loadLut(k){const b=new Float32Array(await (await fetch(DATA+'lut_'+k+'.bin')).arrayBuffer());const a=new Uint16Array(LN*LN*LN*4);
 for(let i=0;i<LN*LN*LN;i++){for(let c=0;c<3;c++)a[i*4+c]=THREE.DataUtils.toHalfFloat(b[i*3+c]);a[i*4+3]=THREE.DataUtils.toHalfFloat(1);}
 const t=new THREE.Data3DTexture(a,LN,LN,LN);t.format=THREE.RGBAFormat;t.type=THREE.HalfFloatType;t.minFilter=t.magFilter=THREE.LinearFilter;t.wrapS=t.wrapT=t.wrapR=THREE.ClampToEdgeWrapping;t.needsUpdate=true;return t;}

function postChain(){
 if(!QUALITY[quality].bloom){toneU.tBloom.value=blackBloom;drawTo(tone,null);return;}
 bright.u.t.value=hdrRT.texture;drawTo(bright,down[0]);
 for(let i=1;i<LV;i++){dn.u.t.value=down[i-1].texture;dn.u.px.value.set(1/down[i-1].width,1/down[i-1].height);drawTo(dn,down[i]);}
 let prev=down[LV-1];
 for(let i=LV-2;i>=0;i--){us.u.t.value=down[i].texture;us.u.tb.value=prev.texture;us.u.px.value.set(.5/prev.width,.5/prev.height);drawTo(us,up[i]);prev=up[i];}
 toneU.tBloom.value=prev.texture;drawTo(tone,null);
}

// ---------- 光切换 ----------
let T=0,Ttarget=0;
function applyLight(t){const A=LIGHT[ORDER[0]],Bb=LIGHT[ORDER[1]||ORDER[0]];
 T=t;shared.uT.value=skyU.uT.value=t;
 const lerp=(a,b)=>a+(b-a)*t,v3=(a,b)=>[0,1,2].map(i=>lerp(a[i],b[i]));
 const sd=sunDir(A).lerp(sunDir(Bb),t).normalize();const col=v3(A.col,Bb.col),s=lerp(A.sun,Bb.sun);
 sun.target.position.set(0,0,40);sun.position.copy(sd).multiplyScalar(160).add(sun.target.position);sun.color.setRGB(col[0],col[1],col[2]);sun.intensity=s;
 skyU.uSunD.value.copy(sd);skyU.uSunE.value.set(col[0]*s,col[1]*s,col[2]*s);shared.uSunI.value.set(col[0]*s/Math.PI,col[1]*s/Math.PI,col[2]*s/Math.PI);
 const fc=v3(A.fogc,Bb.fogc);skyU.uFogC.value.set(...fc);const am=lerp(A.hgamb,Bb.hgamb);skyU.uAmb.value.set(am,am,am);
 skyU.uG.value=.55;const f=lerp(A.fog,Bb.fog);skyU.uFog.value=shared.uFog.value=f;
 toneU.uExp.value=Math.pow(2,lerp(A.exposure,Bb.exposure));toneU.uBloom.value=lerp(A.bloom,Bb.bloom);
 envU.uGround.value.set(...v3(A.ground,Bb.ground));}

// ---------- 相机和走动 ----------
const camera=new THREE.PerspectiveCamera(42,SW/SH,.08,1600);
function setFov(lens){camera.fov=2*Math.atan(18/lens/(SW/SH))*180/Math.PI;camera.updateProjectionMatrix();}
function resize(){if(W)return;SW=innerWidth;SH=innerHeight;const ratio=renderer.getPixelRatio();renderer.setSize(SW,SH,false);hdrRT.setSize(Math.round(SW*ratio),Math.round(SH*ratio));sizeChain();camera.aspect=SW/SH;camera.updateProjectionMatrix();}
const CAMS={west:[[1.2,15.2,4.412+1.6],[-.2,-40,3.4],27],street:[[-.5,-34,1.6],[.3,14,3.4],27],mid:[[-1.4,9,.02+7.6/.4*.122+1.6],[.4,-30,3.5],30],main:[[-1.1,-4.7,1.6],[1,6,2],24],
 steps:[[-1.1,.3,1.6],[-1.1,2.3,.32],32],road:[[.2,-3.45,1.6],[1.1,-1.9,-.02],32],sky:[[.2,-3,1.6],[2.95,1.2,9],30],pole:[[1.3,-.75,1.6],[2.95,.55,1.15],32]};
function toCam(c){const[p,t,l]=c;camera.position.copy(bl2three(...p));camera.up.set(0,1,0);camera.lookAt(bl2three(...t));setFov(l);}
Object.assign(CAMS,{
 street_east:[[-2.2,-88.5,1.8],[-.2,-30,3.2],26],
 junction:[[2.1,-25.7,1.65],[-18.2,-23.9,3.4],24],
 clane:[[-25.4,-19.5,2.1],[-25,-1.5,3.2],26],
 temple_gate:[[29.3,-8,2.6],[47.8,-8.5,8.5],24],
 temple_court:[[50.2,-10.1,2.6],[74.8,-9.5,9],24],
 aerial:[[110,-120,100],[20,-30,0],28]
});
let walking=false;
const propLODs=[],layerGroups=new Map(),loadErrors=[];
const sharedTextures=new Map();
function shareTextures(gltf){
 gltf.scene.traverse(o=>{if(!o.isMesh)return;for(const m of (Array.isArray(o.material)?o.material:[o.material])){
  for(const [slot,t] of Object.entries(m)){if(!t?.isTexture)continue;const association=gltf.parser.associations.get(t),index=association?.textures;
   if(index===undefined)continue;const info=gltf.parser.json.textures[index],image=gltf.parser.json.images[info.source];
   const key=JSON.stringify([image.uri,t.colorSpace,t.channel,t.wrapS,t.wrapT,t.offset.toArray(),t.repeat.toArray(),t.rotation]);
   if(sharedTextures.has(key)){const cached=sharedTextures.get(key);m[slot]=cached;if(t!==cached)t.dispose();}else sharedTextures.set(key,t);
  }
 }});
}
const groundAt=(x,y)=>walkWorld.ground(x,y);
function realtimeMaterial(mat){
 const mats=Array.isArray(mat)?mat:[mat];
 for(const m of mats){if(!m)continue;m.envMapIntensity=.6;if(m.emissiveIntensity>2)m.emissiveIntensity=2;
  for(const v of Object.values(m))if(v?.isTexture)v.anisotropy=Math.min(aniso,4);
  // Match the baked core's atmospheric scattering before the shared AgX output.
  m.onBeforeCompile=s=>{Object.assign(s.uniforms,shared);s.vertexShader=s.vertexShader.replace('#include <common>','#include <common>\nvarying vec3 vWorldFog;').replace('#include <begin_vertex>','#include <begin_vertex>\nvWorldFog=(modelMatrix*vec4(position,1.)).xyz;');
   s.fragmentShader=s.fragmentShader.replace('#include <common>',`#include <common>\nvarying vec3 vWorldFog;uniform float uFog,uG;uniform vec3 uSunD,uSunE,uAmb,uFogC;${FOGF}`).replace('#include <fog_fragment>',`vec3 fdv=vWorldFog-cameraPosition;float fdist=length(fdv);float trans=exp(-uFog*fdist);gl_FragColor.rgb=gl_FragColor.rgb*trans+(1.-trans)*fogLight(fdv/max(fdist,.0001),uSunD,uSunE,uAmb,uG,uFogC);`);};
  m.customProgramCacheKey=()=> 'world-fog-v1';
 }
}
async function loadLayer(layer){
 progress.setPhase('组装街区 '+layer.id);
  const gltf=await gtx.loadAsync('./'+layer.url);shareTextures(gltf);let triangles=0;
  let accessStone=null;
  if(layer.id==='L')layerGroups.get('S')?.traverse(o=>{if(o.isMesh)for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m.name==='stonepave'&&!accessStone){accessStone=m.clone();accessStone.metalness=0;accessStone.roughness=.95;accessStone.color.setRGB(.7,.69,.66);accessStone.normalScale.multiplyScalar(.5);accessStone.vertexColors=false;}});
  const repairs=new Map();
  for(const [name,binding] of Object.entries(layer.materialBindings||{})){
   let source=null;layerGroups.get(binding.layer)?.traverse(o=>{if(o.isMesh)for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(m.name===binding.material)source=m;});
   if(!source)throw new Error('修复材质来源缺失：'+name);
   repairs.set(name,source);
  }
  const repairClones=new Map();
  gltf.scene.traverse(o=>{if(!o.isMesh)return;if(accessStone)o.material=accessStone;
   if(repairs.has(o.material.name)){
    const own=o.material;if(!repairClones.has(own.name)){const material=repairs.get(own.name).clone();material.name=own.name;material.color.copy(own.color);material.metalness=own.name==='repair_metal'?.55:0;material.roughness=.92;material.vertexColors=!!o.geometry.attributes.color;repairClones.set(own.name,material);}
    o.material=repairClones.get(own.name);
   }
   realtimeMaterial(o.material);o.castShadow=!layer.background;o.receiveShadow=true;o.frustumCulled=true;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;});
  scene.add(gltf.scene);layerGroups.set(layer.id,gltf.scene);log('layer '+layer.id+' '+triangles+' tris');
}
async function buildWorld(){
 for(const layer of WORLD.layers){if(!layer.background)await loadLayer(layer);}
 const needed=[...new Set(WORLD.placements.map(p=>p.asset))],templates=new Map();
 for(const asset of needed){progress.setPhase('组装店铺与道具 '+(templates.size+1)+'/'+needed.length);
  const g=await gtx.loadAsync('./'+WORLD.props[asset].url);shareTextures(g);const levels=[new THREE.Group(),new THREE.Group(),new THREE.Group()];
  g.scene.updateMatrixWorld(true);
  g.scene.traverse(o=>{if(!o.isMesh||/_COL(?:\b|_)/i.test(o.name)||o.name.toUpperCase().endsWith('COL'))return;
   const level=/LOD2/i.test(o.name)?2:/LOD1/i.test(o.name)?1:0;const mesh=new THREE.Mesh(o.geometry,o.material);mesh.matrixAutoUpdate=false;mesh.matrix.copy(o.matrixWorld);mesh.castShadow=mesh.receiveShadow=true;realtimeMaterial(mesh.material);levels[level].add(mesh);
  });templates.set(asset,levels);
 }
 for(const p of WORLD.placements){const e=p.center_enu,n=p.outward_enu;
  const c=p.center_qs_h1||[1.8-e[1],e[0]+32.5,e[2]],normal=p.outward_qs_h1||[-n[1],n[0]];
  const lod=new THREE.LOD();const levels=templates.get(p.asset);levels.forEach((g,i)=>{if(g.children.length)lod.addLevel(g.clone(true),[0,18,42][i]);});
  const d=p.offset||0;lod.position.copy(bl2three(c[0]+normal[0]*d,c[1]+normal[1]*d,c[2]));lod.rotation.y=Math.atan2(normal[1],normal[0])+Math.PI/2;lod.scale.setScalar(p.scale||1);scene.add(lod);propLODs.push(lod);
 }
 log('props '+WORLD.placements.length+' placements / '+templates.size+' shared assets');
 // Bridge the existing street between the baked sample (y=-34) and E (y=-62).
 let asphalt=null;layerGroups.get('E').traverse(o=>{if(!o.isMesh)return;for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(/^asphalt/.test(m.name))asphalt=m;});
 const roadMat=asphalt?asphalt.clone():new THREE.MeshStandardMaterial({color:0x484b4c,roughness:.98});realtimeMaterial(roadMat);
 const roadGeo=new THREE.PlaneGeometry(4.6,28.1);roadGeo.rotateX(-Math.PI/2);const uv=roadGeo.attributes.uv;
 for(let i=0;i<uv.count;i++)uv.setXY(i,uv.getX(i)*2.3,uv.getY(i)*14);
 const bridge=new THREE.Mesh(roadGeo,roadMat);bridge.position.set(0,-.008,48);bridge.receiveShadow=true;bridge.name='viewer_street_bridge';scene.add(bridge);
}
const me={x:.8,y:15.2,height:groundAt(.8,15.2),yaw:-Math.PI*.5,pitch:-.03,eye:groundAt(.8,15.2)+1.6,step:0};
let uiBlocked=false;
// 游戏层（web/game/）挂接点：第三人称相机、拍照取景渲染、角色/NPC 动画、额外圆柱障碍。未设置时保持原第一人称行为。
const hooks={camera:null,render:null,update:null,zoom:null,lookScale:null,blockMove:null,exit:null,obstacles:[],suspend:false};
const controls=createExperienceControls({canvas,container:document.body,
 onLook:({dx,dy,source})=>{if(walking){const scale=(source==='lock'?.0021:.003)*(hooks.lookScale?.()??1);me.yaw-=dx*scale;me.pitch=THREE.MathUtils.clamp(me.pitch-dy*scale,-1.3,1.3);}else{const eu=new THREE.Euler().setFromQuaternion(camera.quaternion,'YXZ');eu.y-=dx*.003;eu.x=THREE.MathUtils.clamp(eu.x-dy*.003,-1.4,1.4);camera.quaternion.setFromEuler(eu);}},
 onZoom:({deltaY})=>{if(hooks.zoom?.(deltaY))return;camera.fov=THREE.MathUtils.clamp(camera.fov+deltaY*.02,20,90);camera.updateProjectionMatrix();},
 onExit:e=>{walking=false;$('walk').textContent='进入行走';hooks.exit?.(e);},
 onHint:text=>{$('hint').textContent=text;$('hint').hidden=!text;}
});
controls.setMode('blocked');
function stopWalking(){walking=false;$('walk').textContent='进入行走';controls.setMode(uiBlocked?'blocked':'view');controls.reset();}
const stillIntent={forward:0,right:0,sprint:false};
// 圆柱障碍（NPC、樱花树干）：把目标点推到圆外，再交给真实碰撞重新解算。
function avoidObstacles(x,y){for(const o of hooks.obstacles){const ox=x-o.x,oy=y-o.y,d=Math.hypot(ox,oy),r=o.r+walkWorld.radius;if(d<r&&d>1e-4){x=o.x+ox/d*r;y=o.y+oy/d*r;}}return{x,y};}
function walk(dt){const {forward:fx,right:rx,sprint}=hooks.blockMove?.()?stillIntent:controls.getMoveIntent(),sp=(sprint?3.4:1.8)*dt;
 const dx=Math.cos(me.yaw),dy=Math.sin(me.yaw);
 let p=walkWorld.move(me,(fx*dx+rx*dy)*sp,(fx*dy-rx*dx)*sp);
 if(hooks.obstacles.length){const a=avoidObstacles(p.x,p.y);if(a.x!==p.x||a.y!==p.y)p=walkWorld.move(me,a.x-me.x,a.y-me.y);}
 const move={x:p.x-me.x,y:p.y-me.y,dt,sprint,intent:Math.hypot(fx,rx)};
 me.step+=Math.hypot(p.x-me.x,p.y-me.y)*5;me.x=p.x;me.y=p.y;me.height=p.height;
 if(hooks.camera){hooks.camera(me,dt,move);return;}
 const tg=me.height+1.6+Math.sin(me.step)*.012;me.eye+=(tg-me.eye)*Math.min(1,dt*9);
 const cp=Math.cos(me.pitch);camera.position.copy(bl2three(me.x,me.y,me.eye));camera.up.set(0,1,0);camera.lookAt(bl2three(me.x+dx*cp,me.y+dy*cp,me.eye+Math.sin(me.pitch)));}

// ---------- 主流程 ----------
renderer.setSize(SW,SH,false);
await Promise.all(ORDER.map(loadSky));
const a=skyLayer[ORDER[0]],b=skyLayer[ORDER[1]||ORDER[0]];
const cap=k=>{const L=LIGHT[k];return new THREE.Vector2(L.cap,L.strength);};
skyU.tA.value=a.tex;skyU.tB.value=b.tex;skyU.rA.value=a.rot;skyU.rB.value=b.rot;skyU.cA.value=cap(ORDER[0]);skyU.cB.value=cap(ORDER[1]||ORDER[0]);
toneU.lutA.value=await loadLut(ORDER[0]);toneU.lutB.value=ORDER[1]?await loadLut(ORDER[1]):toneU.lutA.value;
const info=await build();
// A local reflection probe from the old narrow sample would incorrectly light the full district.
Ttarget=start===ORDER[1]?1:0;applyLight(Ttarget);rebuildEnv();
renderer.compile(scene,camera);
log('ready '+JSON.stringify(info));
const go=()=>{$('load').style.opacity=0;setTimeout(()=>$('load').remove(),700);};
renderer.info.autoReset=false;
function frame(){renderer.info.reset();if(hooks.render?.()){renderer.shadowMap.autoUpdate=false;return;}renderer.setRenderTarget(hdrRT);renderer.clear();renderer.render(scene,camera);postChain();renderer.shadowMap.autoUpdate=false;}

{
 progress.finish();go();addEventListener('resize',resize);resize();toCam(CAMS.west);controls.setMode('view');
 const mapUI=createMapUI(),mapDirection=new THREE.Vector3();
 document.addEventListener('cijian:mapchange',()=>{uiBlocked=mapUI.expanded||!$('credits').hidden;stopWalking();});
 function selectView(k){if(!CAMS[k])return;stopWalking();$('view').value=k;toCam(CAMS[k]);}
 $('view').addEventListener('change',()=>selectView($('view').value));
 $('walk').addEventListener('click',()=>{if(uiBlocked)return;if(walking){stopWalking();return;}
  if($('view').value==='aerial'){$('hint').textContent='全景俯瞰用于观察，请先选择地面机位再进入行走。';return;}
  const spawn=walkWorld.findSpawn(camera.position.x,-camera.position.z,1);
  if(!spawn){$('hint').hidden=false;$('hint').textContent='附近没有可站立的通路，请选择其他地面机位。';return;}
  Object.assign(me,spawn);me.eye=spawn.height+1.6;me.step=0;
  const d=camera.getWorldDirection(new THREE.Vector3());me.yaw=Math.atan2(-d.z,d.x);me.pitch=Math.asin(d.y);walking=true;$('walk').textContent='退出行走';$('walk').blur();controls.setMode('walk');});
 $('credit').addEventListener('click',()=>{$('credits').hidden=!$('credits').hidden;uiBlocked=mapUI.expanded||!$('credits').hidden;stopWalking();});
 applyQuality(Object.hasOwn(QUALITY,q.get('quality'))?q.get('quality'):'standard');
 $('quality').addEventListener('click',()=>{const keys=Object.keys(QUALITY);applyQuality(keys[(keys.indexOf(quality)+1)%keys.length]);});
 $('shot').addEventListener('click',()=>{frame();canvas.toBlob(blob=>{if(!blob){fatal(new Error('截图失败'));return;}const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='此间-谷中-'+new Date().toISOString().replace(/[:.]/g,'-')+'.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);},'image/png');});
 // 游戏层用：按给定位置/朝向直接进入行走（跳过机位选择），以及读写色调参数。
 function enterWalkAt({x,y,yaw=me.yaw,pitch=-.08}={}){const spawn=walkWorld.findSpawn(x,y,1.5);if(!spawn)return false;
  Object.assign(me,spawn);me.eye=spawn.height+1.6;me.step=0;me.yaw=yaw;me.pitch=pitch;walking=true;$('walk').textContent='退出行走';controls.setMode('walk');return true;}
 function resumeWalk(){if(uiBlocked)return false;walking=true;$('walk').textContent='退出行走';controls.setMode('walk');return true;}
 window.__cijian={scene,camera,renderer,world:WORLD,navigation:NAV,groundAt,walkWorld,controls,layerGroups,propLODs,mapUI,ready:true,setView:selectView,render:frame,
  hooks,me,THREE,bl2three,toneU,shared,skyU,sun,LIGHT,lightOrder:ORDER,cams:CAMS,enterWalkAt,resumeWalk,stopWalking,setUiBlocked(v){uiBlocked=v;if(v)stopWalking();},
  get quality(){return {key:quality,...QUALITY[quality],hdrSize:[hdrRT.width,hdrRT.height],samples:hdrRT.samples};},get player(){return {...me};},get walking(){return walking;}};
 window.__cijian.backgroundReady=Promise.all(WORLD.layers.filter(l=>l.background).map(loadLayer)).catch(e=>{loadErrors.push(String(e));fatal(e);});
 document.dispatchEvent(new CustomEvent('cijian:ready',{detail:window.__cijian}));
 let last=performance.now(),env=0;
 let measureAt=last,measureFrames=0;const samples=[];
  const loop=n=>{const elapsed=n-last,dt=Math.min(.05,elapsed/1000);last=n;
  if(hooks.suspend){requestAnimationFrame(loop);return;} // 开场等全屏界面遮住城市时不渲染
  if(Math.abs(T-Ttarget)>1e-3){applyLight(T+Math.sign(Ttarget-T)*Math.min(Math.abs(Ttarget-T),dt/4));if(++env%8===0)rebuildEnv();}
  if(walking)walk(dt);hooks.update?.(dt,n,walking);mapUI.update(camera.position,camera.getWorldDirection(mapDirection),walking);toneU.uTime.value=n%1000;frame();measureFrames++;samples.push(elapsed);if(samples.length>600)samples.shift();
  if(n-measureAt>1000){$('stats').textContent=Math.round(measureFrames*1000/(n-measureAt))+' FPS · '+Math.round(renderer.info.render.triangles/1000)+'k △';measureAt=n;measureFrames=0;window.__cijian.frameTimes=samples;}
  requestAnimationFrame(loop);};
 requestAnimationFrame(loop);
}

// 《此间》烘焙实时版。Blender 坐标 (x,y,z) -> three (x,z,-y)；+y 东（上台阶），+x 南。
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/GLTFLoader.js';
import {RGBELoader} from 'three/addons/RGBELoader.js';
import {EXRLoader} from 'three/addons/EXRLoader.js';

const q=new URLSearchParams(location.search);
const NAME=q.get('name')||'x',SHOTS=(q.get('shots')||'').split(',').filter(Boolean),BENCH=q.has('bench'),FRAMES=+q.get('frames')||900;
const W=+q.get('w')||0,H=+q.get('h')||0,AUTO=SHOTS.length>0||BENCH;
const post=(p,b)=>fetch(p,{method:'POST',body:b}).catch(()=>{}),log=m=>post('/result?'+NAME+'_log',m);
const A='../'; // 开发和打包目录结构相同，都相对 web/ 取
const DATA='./data/';
const $=id=>document.getElementById(id);
const MAN=await (await fetch(DATA+'bk.json')).json();
const B=A+'bake/'+MAN.dir+'/',EXT=MAN.ext||'png';

// ---------- 光 ----------
const LIGHT={
 morning:{hdr:'kloofendal_48d_partly_cloudy_puresky_4k.hdr',az:100,el:38,sun:4.0,col:[1,.92,.8],strength:1.9,cap:8,exposure:.5,fog:.0010,fogc:[1,1,1],ground:[.30,.31,.33],bloom:.0,hgamb:.9},
 sunset:{hdr:'qwantani_sunset_puresky_4k.hdr',az:268,el:6.1,sun:7.5,col:[1,.58,.3],strength:.85,cap:9,exposure:.3,fog:.0010,fogc:[1,.8,.58],ground:[.2,.17,.16],bloom:.2,hgamb:.3}};
const ORDER=MAN.lights.filter(k=>LIGHT[k]);
const start=q.get('light')||ORDER[0];
function bl2three(x,y,z){return new THREE.Vector3(x,z,-y);}
function sunDir(L){const a=L.az*Math.PI/180,e=L.el*Math.PI/180;return bl2three(-Math.cos(a)*Math.cos(e),Math.sin(a)*Math.cos(e),Math.sin(e));}

const canvas=document.createElement('canvas');document.body.prepend(canvas);
const renderer=new THREE.WebGLRenderer({canvas,antialias:false,powerPreference:'high-performance',preserveDrawingBuffer:AUTO});
renderer.setPixelRatio(1);renderer.toneMapping=THREE.NoToneMapping;renderer.outputColorSpace=THREE.LinearSRGBColorSpace;
const gl=renderer.getContext();
const aniso=renderer.capabilities.getMaxAnisotropy();
const fsGeo=new THREE.BufferGeometry();fsGeo.setAttribute('position',new THREE.BufferAttribute(new Float32Array([-1,-1,0,3,-1,0,-1,3,0]),3));
const fsCam=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
function fsPass(frag,uniforms,defines){const m=new THREE.ShaderMaterial({uniforms,defines,depthTest:false,depthWrite:false,glslVersion:THREE.GLSL3,
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
const shared={uT:{value:0},uFog:{value:.001},uSunD:skyU.uSunD,uSunE:skyU.uSunE,uAmb:skyU.uAmb,uFogC:skyU.uFogC,uG:skyU.uG,uSunI:{value:new THREE.Vector3()}};
const gtx=new GLTFLoader();
const tl=new THREE.TextureLoader(),exr=new EXRLoader();exr.setDataType(THREE.HalfFloatType);
let total=1,done=0;const tick=()=>{done++;const b=document.querySelector('#bar i');if(b)b.style.width=(done/total*100)+'%';};
function loadTex(p,srgb){return tl.loadAsync(p).catch(e=>{log('MISSING '+p);tick();return new THREE.Texture();}).then(t=>{t.flipY=false;t.wrapS=t.wrapT=THREE.ClampToEdgeWrapping;t.anisotropy=aniso;if(srgb)t.colorSpace=THREE.SRGBColorSpace;t.generateMipmaps=true;t.minFilter=THREE.LinearMipmapLinearFilter;tick();return t;});}
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
 mat.customProgramCacheKey=()=>plant?'p':'s';
}

// 远景卡片：Cycles 渲的范围外街道，预乘透明，只加雾
async function addCards(){const r=await fetch(B+'cards.json');if(!r.ok)return;const meta=await r.json();
 for(const k in meta){const c=meta[k],t=await exr.loadAsync(B+'card_'+k+'.exr');t.minFilter=t.magFilter=THREE.LinearFilter;t.generateMipmaps=false;
  const m=new THREE.ShaderMaterial({transparent:true,depthWrite:false,premultipliedAlpha:true,blending:THREE.CustomBlending,blendSrc:THREE.OneFactor,blendDst:THREE.OneMinusSrcAlphaFactor,
   uniforms:{t:{value:t},uFog:shared.uFog,uSunD:shared.uSunD,uSunE:shared.uSunE,uAmb:shared.uAmb,uFogC:shared.uFogC,uG:shared.uG},
   vertexShader:'varying vec2 vU;varying vec3 vW;void main(){vU=uv;vW=(modelMatrix*vec4(position,1.)).xyz;gl_Position=projectionMatrix*viewMatrix*vec4(vW,1.);}',
   fragmentShader:`uniform sampler2D t;uniform float uFog,uG;uniform vec3 uSunD,uSunE,uAmb,uFogC;varying vec2 vU;varying vec3 vW;${FOGF}
    void main(){vec4 c=texture2D(t,vU);vec3 fv=vW-cameraPosition;float fd=length(fv)+40.;float T=exp(-uFog*fd);gl_FragColor=vec4(c.rgb*T+c.a*(1.-T)*fogLight(fv/length(fv),uSunD,uSunE,uAmb,uG,uFogC),c.a);}`});
  const o=new THREE.Mesh(new THREE.PlaneGeometry(c.w,c.h),m);o.position.copy(bl2three(...c.center));o.lookAt(bl2three(...c.eye));o.renderOrder=1;scene.add(o);}
}
async function build(){
 const t0=performance.now();
 const gltf=await gtx.loadAsync(DATA+'bk.glb');
 $('msg').textContent='载入贴图';
 const jobs=[];let meshes=0;
 const L0=ORDER[0],L1=ORDER[1]||ORDER[0];
 gltf.scene.traverse(o=>{ if(!o.isMesh)return;meshes++;
  const mn=o.material.name,g=o.name.startsWith('bk_')?o.name.slice(3):mn,f=MAN.groups[g];if(!f&&!MAN.plants.some(p=>mn.startsWith(p)))log('NOGROUP '+o.name+' '+mn);
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
 total=jobs.length+1;
 await Promise.all(jobs);
 scene.add(gltf.scene);
 await addCards();
 return{meshes,ms:performance.now()-t0};
}

// ---------- 后期：多级泛光 + AgX 查找表 ----------
let SW=W||innerWidth,SH=H||innerHeight;
const rtOpt={type:THREE.HalfFloatType,format:THREE.RGBAFormat,minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter,depthBuffer:false};
const hdrRT=new THREE.WebGLRenderTarget(SW,SH,{...rtOpt,depthBuffer:true,samples:4});
const LV=6;const down=[],up=[];
function sizeChain(){let w=SW,h=SH;for(let i=0;i<LV;i++){w=Math.max(2,w>>1);h=Math.max(2,h>>1);if(!down[i]){down[i]=new THREE.WebGLRenderTarget(w,h,rtOpt);up[i]=new THREE.WebGLRenderTarget(w,h,rtOpt);}else{down[i].setSize(w,h);up[i].setSize(w,h);}}}
sizeChain();
const bright=fsPass(`uniform sampler2D t;uniform float th;void main(){vec3 c=texture(t,vUv).rgb;float l=max(c.r,max(c.g,c.b));oc=vec4(c*smoothstep(th*.75,th*1.25,l),1.);}`,{t:{value:null},th:{value:1.6}});
const dn=fsPass(`uniform sampler2D t;uniform vec2 px;void main(){vec3 c=texture(t,vUv).rgb*.25;for(int i=0;i<4;i++){vec2 s=vec2((i&1)*2-1,(i&2)-1)*px;c+=texture(t,vUv+s).rgb*.1875;}oc=vec4(c,1.);}`,{t:{value:null},px:{value:new THREE.Vector2()}});
const us=fsPass(`uniform sampler2D t,tb;uniform vec2 px;void main(){vec3 c=vec3(0.);for(int i=0;i<4;i++){vec2 s=vec2((i&1)*2-1,(i&2)-1)*px;c+=texture(tb,vUv+s).rgb*.25;}oc=vec4(texture(t,vUv).rgb+c,1.);}`,{t:{value:null},tb:{value:null},px:{value:new THREE.Vector2()}});
const LN=48;
const toneU={t:{value:hdrRT.texture},tBloom:{value:null},lutA:{value:null},lutB:{value:null},uT:shared.uT,uExp:{value:1},uBloom:{value:.35},uTime:{value:0}};
const tone=fsPass(`precision highp sampler3D;uniform sampler2D t,tBloom;uniform sampler3D lutA,lutB;uniform float uT,uExp,uBloom,uTime;
 vec3 enc(vec3 c){return clamp((log2(max(c,vec3(1e-5)))+9.)/16.,0.,1.);}
 vec3 lut(sampler3D l,vec3 c){vec3 e=enc(c);e=e*(${(LN-1).toFixed(1)}/${LN.toFixed(1)})+.5/${LN.toFixed(1)};return texture(l,e).rgb;}
 float rnd(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
 void main(){vec3 c=texture(t,vUv).rgb;c+=texture(tBloom,vUv).rgb*uBloom;c*=uExp;
  vec3 o=lut(lutA,c);if(uT>0.)o=mix(o,lut(lutB,c),uT);
  o+=(rnd(gl_FragCoord.xy+uTime)-.5)/255.;oc=vec4(o,1.);}`,toneU);
async function loadLut(k){const b=new Float32Array(await (await fetch(DATA+'lut_'+k+'.bin')).arrayBuffer());const a=new Uint16Array(LN*LN*LN*4);
 for(let i=0;i<LN*LN*LN;i++){for(let c=0;c<3;c++)a[i*4+c]=THREE.DataUtils.toHalfFloat(b[i*3+c]);a[i*4+3]=THREE.DataUtils.toHalfFloat(1);}
 const t=new THREE.Data3DTexture(a,LN,LN,LN);t.format=THREE.RGBAFormat;t.type=THREE.HalfFloatType;t.minFilter=t.magFilter=THREE.LinearFilter;t.wrapS=t.wrapT=t.wrapR=THREE.ClampToEdgeWrapping;t.needsUpdate=true;return t;}

function postChain(){
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
 sun.position.copy(sd).multiplyScalar(100);sun.color.setRGB(col[0],col[1],col[2]);sun.intensity=s;
 skyU.uSunD.value.copy(sd);skyU.uSunE.value.set(col[0]*s,col[1]*s,col[2]*s);shared.uSunI.value.set(col[0]*s/Math.PI,col[1]*s/Math.PI,col[2]*s/Math.PI);
 const fc=v3(A.fogc,Bb.fogc);skyU.uFogC.value.set(...fc);const am=lerp(A.hgamb,Bb.hgamb);skyU.uAmb.value.set(am,am,am);
 skyU.uG.value=.55;const f=lerp(A.fog,Bb.fog);skyU.uFog.value=shared.uFog.value=f;
 toneU.uExp.value=Math.pow(2,lerp(A.exposure,Bb.exposure));toneU.uBloom.value=lerp(A.bloom,Bb.bloom);
 envU.uGround.value.set(...v3(A.ground,Bb.ground));}

// ---------- 相机和走动 ----------
const camera=new THREE.PerspectiveCamera(42,SW/SH,.08,1600);
function setFov(lens){camera.fov=2*Math.atan(18/lens/(SW/SH))*180/Math.PI;camera.updateProjectionMatrix();}
function resize(){if(W)return;SW=innerWidth;SH=innerHeight;renderer.setSize(SW,SH,false);hdrRT.setSize(SW,SH);sizeChain();camera.aspect=SW/SH;setFov(26);}
const CAMS={west:[[1.2,15.2,4.412+1.6],[-.2,-40,3.4],27],street:[[-.5,-34,1.6],[.3,14,3.4],27],mid:[[-1.4,9,.02+7.6/.4*.122+1.6],[.4,-30,3.5],30],main:[[-1.1,-4.7,1.6],[1,6,2],24],
 steps:[[-1.1,.3,1.6],[-1.1,2.3,.32],32],road:[[.2,-3.45,1.6],[1.1,-1.9,-.02],32],sky:[[.2,-3,1.6],[2.95,1.2,9],30],pole:[[1.3,-.75,1.6],[2.95,.55,1.15],32]};
function toCam(c){const[p,t,l]=c;camera.position.copy(bl2three(...p));camera.up.set(0,1,0);camera.lookAt(bl2three(...t));setFov(l);}
const ST={Y0:1.4,TR:.4,RS:.122,N:36,Z0:.02};
function groundH(y){const s=(y-ST.Y0)/ST.TR;if(s<=0)return 0;if(s>=ST.N)return ST.Z0+ST.N*ST.RS;const f=Math.floor(s),k=Math.min(1,(s-f)*4);return ST.Z0+(f+k*k*(3-2*k))*ST.RS;}
const me={x:.8,y:15.2,yaw:-Math.PI*.5,pitch:-.03,eye:groundH(15.2)+1.6,step:0};const keys={};
addEventListener('keydown',e=>{keys[e.code]=1;if(e.code==='KeyT')Ttarget=Ttarget>.5?0:1;});addEventListener('keyup',e=>keys[e.code]=0);
canvas.addEventListener('click',()=>{if(!AUTO){canvas.requestPointerLock();$('hint').hidden=true;}});
addEventListener('mousemove',e=>{if(document.pointerLockElement!==canvas)return;me.yaw-=e.movementX*.0021;me.pitch=Math.max(-1.3,Math.min(1.3,me.pitch-e.movementY*.0021));});
function walk(dt){const sp=(keys.ShiftLeft?2.6:1.45)*dt;let fx=(keys.KeyW?1:0)-(keys.KeyS?1:0),rx=(keys.KeyD?1:0)-(keys.KeyA?1:0);const l=Math.hypot(fx,rx);if(l){fx/=l;rx/=l;}
 const dx=Math.cos(me.yaw),dy=Math.sin(me.yaw);// 平面方向：yaw=π/2 朝 +y
 const nx=me.x+(fx*dx+rx*dy)*sp,ny=me.y+(fx*dy-rx*dx)*sp;
 const lim=ny>ST.Y0&&ny<ST.Y0+ST.N*ST.TR?2.1:2.3;me.x=Math.max(-lim,Math.min(lim,nx));me.y=Math.max(-28,Math.min(27,ny));
 if(l)me.step+=sp*5;const tg=groundH(me.y)+1.6+Math.sin(me.step)*.012;me.eye+=(tg-me.eye)*Math.min(1,dt*9);
 const cp=Math.cos(me.pitch);camera.position.copy(bl2three(me.x,me.y,me.eye));camera.up.set(0,1,0);camera.lookAt(bl2three(me.x+dx*cp,me.y+dy*cp,me.eye+Math.sin(me.pitch)));}

// ---------- 主流程 ----------
renderer.setSize(SW,SH,false);
await Promise.all(ORDER.map(loadSky));
const a=skyLayer[ORDER[0]],b=skyLayer[ORDER[1]||ORDER[0]];
const cap=k=>{const L=LIGHT[k];return new THREE.Vector2(L.cap,L.strength);};
skyU.tA.value=a.tex;skyU.tB.value=b.tex;skyU.rA.value=a.rot;skyU.rB.value=b.rot;skyU.cA.value=cap(ORDER[0]);skyU.cB.value=cap(ORDER[1]||ORDER[0]);
toneU.lutA.value=await loadLut(ORDER[0]);toneU.lutB.value=ORDER[1]?await loadLut(ORDER[1]):toneU.lutA.value;
const info=await build();
try{const t=await exr.loadAsync(B+'probe_mid.exr');t.mapping=THREE.EquirectangularReflectionMapping;t.minFilter=t.magFilter=THREE.LinearFilter;t.generateMipmaps=false;probe=t;}catch(e){log('noprobe');}
Ttarget=start===ORDER[1]?1:0;applyLight(Ttarget);rebuildEnv();
renderer.compile(scene,camera);
log('ready '+JSON.stringify(info));
const go=()=>{$('load').style.opacity=0;setTimeout(()=>$('load').remove(),700);};
renderer.info.autoReset=false;
function frame(){renderer.info.reset();renderer.setRenderTarget(hdrRT);renderer.clear();renderer.render(scene,camera);postChain();}

if(SHOTS.length){for(const c of SHOTS){toCam(CAMS[c]);for(let i=0;i<3;i++){frame();await new Promise(r=>setTimeout(r,120));}
  await post('/shot?'+NAME+'_'+c,canvas.toDataURL('image/jpeg',.92));}
 await post('/result?done_'+NAME,'1');
}else if(BENCH){
 // 帧时间：readPixels 同步等 GPU 完成（不受 rAF 限速影响）；扩展可用时另记 GPU 计时。页面隐藏时的帧不计。
 const P=[[-1,-26,1.6],[0,-15,1.6],[-1,-4.7,1.6],[.2,-1,1.6],[.2,1.2,1.62],[0,6,2.9],[0,10,4.0],[0,15,5.9],[0,26,6.0]].map(p=>bl2three(...p));
 const path=new THREE.CatmullRomCurve3(P);const cpu=[],gpu=[],raf=[],pend=[],px=new Uint8Array(4);let calls=0,tri=0,f=0,hid=0,prev=0;
 const ext=gl.getExtension('EXT_disjoint_timer_query_webgl2');
 const pollQ=()=>{while(pend.length){const q0=pend[0];if(!gl.getQueryParameter(q0,gl.QUERY_RESULT_AVAILABLE))break;if(!gl.getParameter(ext.GPU_DISJOINT_EXT))gpu.push(gl.getQueryParameter(q0,gl.QUERY_RESULT)/1e6);gl.deleteQuery(q0);pend.shift();}};
 const stat=s0=>{if(!s0.length)return null;const s=[...s0].sort((x,y)=>x-y),n=s.length;return{n,avg:+(s.reduce((x,y)=>x+y,0)/n).toFixed(2),p50:+s[n>>1].toFixed(2),p95:+s[Math.floor(n*.95)].toFixed(2),p99:+s[Math.floor(n*.99)].toFixed(2),max:+s[n-1].toFixed(2)};};
 function place(i){const t=i/FRAMES,s=t<.5?t*2:(1-t)*2,p=path.getPointAt(Math.min(s,.999)),ah=path.getPointAt(Math.min(s+.02,1));const yaw=Math.sin(t*Math.PI*6)*.7,dir=ah.clone().sub(p).setY(0).normalize();if(t>=.5)dir.negate();dir.applyAxisAngle(new THREE.Vector3(0,1,0),yaw);camera.position.copy(p);camera.lookAt(p.clone().add(dir));setFov(26);}
 const out=document.createElement('pre');out.style.cssText='position:fixed;left:12px;top:12px;margin:0;padding:10px;background:#000a;color:#fff;font:13px/1.4 monospace;white-space:pre-wrap;max-width:60ch;z-index:9';document.body.append(out);go();
 const loop=n=>{if(document.hidden){hid++;requestAnimationFrame(loop);return;}
  if(prev&&f>20)raf.push(n-prev);prev=n;place(f);const c0=performance.now();let qq;if(ext){qq=gl.createQuery();gl.beginQuery(ext.TIME_ELAPSED_EXT,qq);}
  frame();if(ext){gl.endQuery(ext.TIME_ELAPSED_EXT);pend.push(qq);}gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px);if(f>20)cpu.push(performance.now()-c0);if(ext)pollQ();
  calls=Math.max(calls,renderer.info.render.calls);tri=Math.max(tri,renderer.info.render.triangles);f++;if(f%30===0)out.textContent='测试中 '+f+'/'+FRAMES+'（别切走或遮挡窗口）';
  if(f<FRAMES)requestAnimationFrame(loop);else{const i=gl.getExtension('WEBGL_debug_renderer_info');
   setTimeout(()=>{if(ext)pollQ();const r={name:NAME,res:SW+'x'+SH,dpr:devicePixelRatio,gpu:i&&gl.getParameter(i.UNMASKED_RENDERER_WEBGL),...info,calls,tris:tri,geos:renderer.info.memory.geometries,tex:renderer.info.memory.textures,hiddenFrames:hid,syncMs:stat(cpu),gpuMs:stat(gpu.slice(20)),rafMs:stat(raf)};
    out.textContent=JSON.stringify(r,null,1);out.style.userSelect='text';post('/result?'+NAME,JSON.stringify(r)).then(()=>post('/result?done_'+NAME,'1'));},800);}};
 requestAnimationFrame(loop);
}else{
 go();$('hint').hidden=false;addEventListener('resize',resize);resize();
 let last=performance.now(),env=0;
 const loop=n=>{const dt=Math.min(.05,(n-last)/1000);last=n;
  if(Math.abs(T-Ttarget)>1e-3){applyLight(T+Math.sign(Ttarget-T)*Math.min(Math.abs(Ttarget-T),dt/4));if(++env%8===0)rebuildEnv();}
  walk(dt);toneU.uTime.value=n%1000;frame();requestAnimationFrame(loop);};
 requestAnimationFrame(loop);
}

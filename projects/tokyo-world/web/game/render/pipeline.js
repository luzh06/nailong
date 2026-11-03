// 画面管线：把场景画成最终显示的图。游戏每帧用它画到屏幕，拍照用它画到离屏大图，两边颜色一致。
//
// HdrPipeline 照搬烘焙小样 projects/cijian-5070/web/game.js 的后期（东京、图书馆）：
//   场景 → HDR 目标（MSAA）→ 多级泛光 → 曝光 → AgX 查找表（log2 编码，48³）→ 抖动
// ComposerPipeline 包一层 Three.js 的 EffectComposer（悉尼 sydney-harbour/web/src/post.js 就是这种：
//   RenderPass → UnrealBloomPass → OutputPass）。
// StandardPipeline 给没有自定义后期的场景用：Three.js 自带的色调映射 + sRGB。
//
// 三者接口相同：render(scene, camera, target, { width, height })，输出是显示空间（sRGB）的颜色；
// exposureScale 是拍照时的曝光补偿倍数（1 = 不补偿），只影响这条管线画出的画面。
// 宿主有自己的后期也可以：只要提供同样签名的 render，能画到任意大小的 target 即可。
import * as THREE from 'three';

const FS_VERT = 'out vec2 vUv;void main(){vUv=position.xy*.5+.5;gl_Position=vec4(position.xy,0,1);}';
const fsGeo = new THREE.BufferGeometry();
fsGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
const fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

export function fullscreenPass(frag, uniforms) {
  const material = new THREE.ShaderMaterial({
    uniforms,
    depthTest: false,
    depthWrite: false,
    glslVersion: THREE.GLSL3,
    vertexShader: FS_VERT,
    fragmentShader: 'precision highp float;precision highp sampler3D;in vec2 vUv;out vec4 oc;' + frag,
  });
  const scene = new THREE.Scene();
  const mesh = new THREE.Mesh(fsGeo, material);
  mesh.frustumCulled = false;
  scene.add(mesh);
  return {
    u: uniforms,
    material,
    draw(renderer, target) {
      renderer.setRenderTarget(target);
      renderer.render(scene, fsCam);
    },
    dispose() {
      material.dispose();
    },
  };
}

const HDR_OPT = { type: THREE.HalfFloatType, format: THREE.RGBAFormat, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: false };

// 一套按尺寸分配的渲染目标：主 HDR 目标 + 泛光的下采样/上采样链。
// bloomHeight 是泛光链第一级的高度：离屏大图也用和屏幕一样的泛光分辨率，
// 这样泛光的相对大小和强度与屏幕一致（实测不这样做，日落时照片和屏幕差约 5/255）。
class Chain {
  constructor(width, height, levels, bloomHeight) {
    this.hdr = new THREE.WebGLRenderTarget(width, height, { ...HDR_OPT, depthBuffer: true, samples: 4 });
    this.down = [];
    this.up = [];
    this.levels = levels;
    this.setSize(width, height, bloomHeight);
  }
  setSize(width, height, bloomHeight = height >> 1) {
    this.width = width;
    this.height = height;
    this.bloomHeight = bloomHeight;
    this.hdr.setSize(width, height);
    let h = Math.max(2, bloomHeight) * 2;
    let w = Math.round((h * width) / height);
    for (let i = 0; i < this.levels; i++) {
      w = Math.max(2, w >> 1);
      h = Math.max(2, h >> 1);
      if (!this.down[i]) {
        this.down[i] = new THREE.WebGLRenderTarget(w, h, HDR_OPT);
        this.up[i] = new THREE.WebGLRenderTarget(w, h, HDR_OPT);
      } else {
        this.down[i].setSize(w, h);
        this.up[i].setSize(w, h);
      }
    }
  }
  dispose() {
    this.hdr.dispose();
    this.down.forEach((t) => t.dispose());
    this.up.forEach((t) => t.dispose());
  }
}

export class HdrPipeline {
  /**
   * @param {THREE.WebGLRenderer} renderer 要求 toneMapping = NoToneMapping、outputColorSpace = LinearSRGBColorSpace（查找表已经输出显示色）
   * @param {object} [o]
   * @param {number} [o.lutSize=48]
   * @param {number} [o.bloomLevels=6]   泛光级数
   */
  constructor(renderer, { lutSize = 48, bloomLevels = 6 } = {}) {
    this.renderer = renderer;
    this.lutSize = lutSize;
    this.bloomLevels = bloomLevels;
    this.exposure = 1;    // 线性倍数（game.js 里是 2^exposure）
    this.exposureScale = 1;
    this.bloom = 0.35;
    this.bloomThreshold = 1.6;
    this.lutMix = 0;      // 0 用 lutA，1 用 lutB，中间混合（时段过渡）
    this.dither = true;
    this.time = 0;
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.outputColorSpace = THREE.LinearSRGBColorSpace;

    const LN = lutSize.toFixed(1);
    const LN1 = (lutSize - 1).toFixed(1);
    this.bright = fullscreenPass(
      'uniform sampler2D t;uniform float th;void main(){vec3 c=texture(t,vUv).rgb;float l=max(c.r,max(c.g,c.b));oc=vec4(c*smoothstep(th*.75,th*1.25,l),1.);}',
      { t: { value: null }, th: { value: 1.6 } },
    );
    this.dn = fullscreenPass(
      'uniform sampler2D t;uniform vec2 px;void main(){vec3 c=texture(t,vUv).rgb*.25;for(int i=0;i<4;i++){vec2 s=vec2((i&1)*2-1,(i&2)-1)*px;c+=texture(t,vUv+s).rgb*.1875;}oc=vec4(c,1.);}',
      { t: { value: null }, px: { value: new THREE.Vector2() } },
    );
    this.us = fullscreenPass(
      'uniform sampler2D t,tb;uniform vec2 px;void main(){vec3 c=vec3(0.);for(int i=0;i<4;i++){vec2 s=vec2((i&1)*2-1,(i&2)-1)*px;c+=texture(tb,vUv+s).rgb*.25;}oc=vec4(texture(t,vUv).rgb+c,1.);}',
      { t: { value: null }, tb: { value: null }, px: { value: new THREE.Vector2() } },
    );
    this.tone = fullscreenPass(
      `uniform sampler2D t,tBloom;uniform sampler3D lutA,lutB;uniform float uT,uExp,uBloom,uTime,uDither;uniform vec3 uGrade;
      vec3 enc(vec3 c){return clamp((log2(max(c,vec3(1e-5)))+9.)/16.,0.,1.);}
      vec3 lut(sampler3D l,vec3 c){vec3 e=enc(c);e=e*(${LN1}/${LN})+.5/${LN};return texture(l,e).rgb;}
      float rnd(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
      void main(){vec3 c=texture(t,vUv).rgb;c+=texture(tBloom,vUv).rgb*uBloom;c*=uExp;
        vec3 o=lut(lutA,c);if(uT>0.)o=mix(o,lut(lutB,c),uT);o*=uGrade;
        o+=(rnd(gl_FragCoord.xy+uTime)-.5)/255.*uDither;oc=vec4(o,1.);}`,
      {
        t: { value: null },
        tBloom: { value: null },
        lutA: { value: null },
        lutB: { value: null },
        uT: { value: 0 },
        uExp: { value: 1 },
        uBloom: { value: 0.35 },
        uTime: { value: 0 },
        uDither: { value: 1 },
        uGrade: { value: new THREE.Vector3(1, 1, 1) },
      },
    );
    this.chains = new Map();
  }

  /** 读 game.js 用的 .bin 查找表（float32 RGB，lutSize³） */
  async loadLut(url) {
    const n = this.lutSize;
    const b = new Float32Array(await (await fetch(url)).arrayBuffer());
    if (b.length !== n * n * n * 3) throw new Error(`查找表尺寸不对：${url}`);
    const a = new Uint16Array(n * n * n * 4);
    for (let i = 0; i < n * n * n; i++) {
      for (let c = 0; c < 3; c++) a[i * 4 + c] = THREE.DataUtils.toHalfFloat(b[i * 3 + c]);
      a[i * 4 + 3] = THREE.DataUtils.toHalfFloat(1);
    }
    const t = new THREE.Data3DTexture(a, n, n, n);
    t.format = THREE.RGBAFormat;
    t.type = THREE.HalfFloatType;
    t.minFilter = t.magFilter = THREE.LinearFilter;
    t.wrapS = t.wrapT = t.wrapR = THREE.ClampToEdgeWrapping;
    t.needsUpdate = true;
    return t;
  }

  setLuts(lutA, lutB = lutA) {
    this.tone.u.lutA.value = lutA;
    this.tone.u.lutB.value = lutB;
  }

  _chain(width, height, screen, screenHeight) {
    const key = screen ? 'screen' : `${width}x${height}`;
    let c = this.chains.get(key);
    // 泛光链按“这张图在屏幕上有多高”的一半起步：照片对应的是取景框那一块，所以用取景框的像素高度
    const ref = screenHeight ?? this.renderer.getDrawingBufferSize(new THREE.Vector2()).y;
    const bloomHeight = Math.min(height, ref) >> 1;
    if (!c) {
      c = new Chain(width, height, this.bloomLevels, bloomHeight);
      this.chains.set(key, c);
    } else if (c.width !== width || c.height !== height || c.bloomHeight !== bloomHeight) c.setSize(width, height, bloomHeight);
    return c;
  }

  /** 释放离屏大图用的渲染目标（拍完照调用，屏幕那套保留） */
  releaseOffscreen() {
    for (const [k, c] of this.chains) {
      if (k !== 'screen') {
        c.dispose();
        this.chains.delete(k);
      }
    }
  }

  /**
   * @param target null 表示画到屏幕
   * @param size  画到离屏目标时的像素尺寸（默认取 target 的尺寸）；
   *              size.screenHeight 是这张图在屏幕上对应的像素高度（拍照时 = 取景框高度），泛光按它算
   */
  render(scene, camera, target = null, size = null) {
    const r = this.renderer;
    let w;
    let h;
    if (target) {
      w = size?.width ?? target.width;
      h = size?.height ?? target.height;
    } else {
      const s = r.getDrawingBufferSize(new THREE.Vector2());
      w = s.x;
      h = s.y;
    }
    const c = this._chain(w, h, !target, size?.screenHeight);
    r.setRenderTarget(c.hdr);
    r.clear();
    r.render(scene, camera);

    this.bright.u.t.value = c.hdr.texture;
    this.bright.u.th.value = this.bloomThreshold;
    this.bright.draw(r, c.down[0]);
    for (let i = 1; i < c.levels; i++) {
      this.dn.u.t.value = c.down[i - 1].texture;
      this.dn.u.px.value.set(1 / c.down[i - 1].width, 1 / c.down[i - 1].height);
      this.dn.draw(r, c.down[i]);
    }
    let prev = c.down[c.levels - 1];
    for (let i = c.levels - 2; i >= 0; i--) {
      this.us.u.t.value = c.down[i].texture;
      this.us.u.tb.value = prev.texture;
      this.us.u.px.value.set(0.5 / prev.width, 0.5 / prev.height);
      this.us.draw(r, c.up[i]);
      prev = c.up[i];
    }
    const u = this.tone.u;
    u.t.value = c.hdr.texture;
    u.tBloom.value = prev.texture;
    u.uT.value = this.lutMix;
    u.uExp.value = this.exposure * this.exposureScale;
    u.uBloom.value = this.bloom;
    u.uTime.value = this.time;
    u.uDither.value = this.dither ? 1 : 0;
    if (this.grade) u.uGrade.value.copy(this.grade);
    this.tone.draw(r, target);
  }

  dispose() {
    this.chains.forEach((c) => c.dispose());
    this.chains.clear();
    [this.bright, this.dn, this.us, this.tone].forEach((p) => p.dispose());
  }
}

// 没有自定义后期的场景：Three.js 自带色调映射 + sRGB，效果等同于直接 renderer.render 到屏幕
export class StandardPipeline {
  constructor(renderer) {
    this.renderer = renderer;
    this.pass = fullscreenPass(
      `uniform sampler2D t;uniform int toneMode;uniform float exposure;
      vec3 cjRRTFit(vec3 v){vec3 a=v*(v+0.0245786)-0.000090537;vec3 b=v*(0.983729*v+0.4329510)+0.238081;return a/b;}
      vec3 cjAces(vec3 color){
        const mat3 inM=mat3(vec3(0.59719,0.07600,0.02840),vec3(0.35458,0.90834,0.13383),vec3(0.04823,0.01566,0.83777));
        const mat3 outM=mat3(vec3(1.60475,-0.10208,-0.00327),vec3(-0.53108,1.10813,-0.07276),vec3(-0.07367,-0.00605,1.07602));
        color*=exposure/0.6;color=inM*color;color=cjRRTFit(color);color=outM*color;return clamp(color,0.,1.);}
      vec3 cjNeutral(vec3 color){
        const float sc=0.8-0.04;const float ds=0.15;color*=exposure;
        float x=min(color.r,min(color.g,color.b));float off=x<0.08?x-6.25*x*x:0.04;color-=off;
        float peak=max(color.r,max(color.g,color.b));if(peak<sc)return color;
        float d=1.-sc;float np=1.-d*d/(peak+d-sc);color*=np/peak;float g=1.-1./(ds*(peak-np)+1.);return mix(color,vec3(np),g);}
      vec3 cjToSRGB(vec3 c){c=clamp(c,0.,1.);return mix(c*12.92,pow(c,vec3(1./2.4))*1.055-0.055,step(0.0031308,c));}
      void main(){vec3 c=texture(t,vUv).rgb;
        if(toneMode==1)c=cjAces(c);else if(toneMode==2)c=cjNeutral(c);else c*=exposure;
        oc=vec4(cjToSRGB(c),1.);}`,
      { t: { value: null }, toneMode: { value: 1 }, exposure: { value: 1 } },
    );
    this.rt = null;
    this.exposureScale = 1;
  }

  render(scene, camera, target = null, size = null) {
    const r = this.renderer;
    if (!target) {
      const e = r.toneMappingExposure;
      r.toneMappingExposure = e * this.exposureScale;
      r.setRenderTarget(null);
      r.render(scene, camera);
      r.toneMappingExposure = e;
      return;
    }
    const w = size?.width ?? target.width;
    const h = size?.height ?? target.height;
    if (!this.rt || this.rt.width !== w || this.rt.height !== h) {
      this.rt?.dispose();
      this.rt = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: 4 });
    }
    // 画到离屏目标时 Three.js 不做色调映射，这里补上
    r.setRenderTarget(this.rt);
    r.render(scene, camera);
    const u = this.pass.u;
    u.t.value = this.rt.texture;
    u.exposure.value = r.toneMappingExposure * this.exposureScale;
    u.toneMode.value = r.toneMapping === THREE.NoToneMapping ? 0 : r.toneMapping === THREE.NeutralToneMapping ? 2 : 1; // AgX 等暂按 ACES
    this.pass.draw(r, target);
  }

  releaseOffscreen() {
    this.rt?.dispose();
    this.rt = null;
  }

  dispose() {
    this.releaseOffscreen();
    this.pass.dispose();
  }
}

// 包一层 EffectComposer。照片尺寸和屏幕不同时，临时把 composer 改到照片尺寸，
// 但泛光（UnrealBloomPass）仍按屏幕分辨率算，这样泛光的相对大小和屏幕一致；画完恢复原尺寸。
export class ComposerPipeline {
  /**
   * @param {THREE.WebGLRenderer} renderer
   * @param {import('three/addons/postprocessing/EffectComposer.js').EffectComposer} composer 宿主已经搭好的 composer
   * @param {object} [o]
   * @param {object} [o.renderPass] 画场景的那个 pass；不给就取第一个带 scene 和 camera 的 pass
   */
  constructor(renderer, composer, { renderPass } = {}) {
    this.renderer = renderer;
    this.composer = composer;
    this.renderPass = renderPass ?? composer.passes.find((p) => p.scene && p.camera);
    if (!this.renderPass) throw new Error('ComposerPipeline：composer 里找不到画场景的 pass');
    this.exposureScale = 1;
    this.copy = fullscreenPass('uniform sampler2D t;void main(){oc=texture(t,vUv);}', { t: { value: null } });
  }

  render(scene, camera, target = null, size = null) {
    const r = this.renderer;
    const c = this.composer;
    const rp = this.renderPass;
    const prev = { camera: rp.camera, scene: rp.scene, exposure: r.toneMappingExposure };
    rp.camera = camera;
    rp.scene = scene;
    r.toneMappingExposure = prev.exposure * this.exposureScale;
    try {
      if (!target) {
        c.renderToScreen = true;
        c.render();
        return;
      }
      const db = r.getDrawingBufferSize(new THREE.Vector2());
      const w = size?.width ?? target.width;
      const h = size?.height ?? target.height;
      const resize = w !== db.x || h !== db.y;
      let saved;
      if (resize) {
        saved = { w: c._width, h: c._height, pr: c._pixelRatio };
        c.setPixelRatio(1);
        c.setSize(w, h);
        // 泛光按屏幕上的像素密度算：照片对应取景框那一块，所以用取景框的像素高度、照片的宽高比
        const bh = size?.screenHeight ?? db.y;
        for (const p of c.passes) if (p.renderTargetsHorizontal) p.setSize(Math.round((bh * w) / h), bh);
      }
      c.renderToScreen = false;
      c.render();
      this.copy.u.t.value = c.readBuffer.texture;
      this.copy.draw(r, target);
      c.renderToScreen = true;
      if (resize) {
        c.setPixelRatio(saved.pr);
        c.setSize(saved.w, saved.h);
      }
    } finally {
      rp.camera = prev.camera;
      rp.scene = prev.scene;
      r.toneMappingExposure = prev.exposure;
    }
  }

  dispose() {
    this.copy.dispose();
  }
}

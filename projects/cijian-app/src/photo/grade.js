// 调色通道：把线性 HDR 画面做色调映射、转 sRGB，再按相机风格调色。
// 预览（画到屏幕）和拍照（画到离屏目标）共用同一个材质，保证取景所见即所得。
import * as THREE from 'three';

const vertexShader = /* glsl */ `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}`;

const fragmentShader = /* glsl */ `
precision highp float;
precision highp sampler3D;
uniform sampler2D tScene;
uniform sampler3D tLut;
uniform float useLut;
uniform float lutSize;
uniform int toneMode;          // 0 无, 1 ACES, 2 Neutral
uniform float exposure;
uniform float contrast;
uniform float saturation;
uniform vec3 tint;
uniform float fade;
uniform vec3 fadeColor;
uniform vec3 highlight;
uniform float grain;
uniform float vignette;
uniform float seed;
uniform vec2 resolution;
uniform vec4 uvRect;           // 取样区域：x, y, w, h（预览时为整屏）
varying vec2 vUv;

vec3 cjRRTFit(vec3 v) {
  vec3 a = v * (v + 0.0245786) - 0.000090537;
  vec3 b = v * (0.983729 * v + 0.4329510) + 0.238081;
  return a / b;
}
vec3 cjAces(vec3 color) {
  const mat3 inM = mat3(vec3(0.59719, 0.07600, 0.02840), vec3(0.35458, 0.90834, 0.13383), vec3(0.04823, 0.01566, 0.83777));
  const mat3 outM = mat3(vec3(1.60475, -0.10208, -0.00327), vec3(-0.53108, 1.10813, -0.07276), vec3(-0.07367, -0.00605, 1.07602));
  color *= exposure / 0.6;
  color = inM * color;
  color = cjRRTFit(color);
  color = outM * color;
  return clamp(color, 0.0, 1.0);
}
vec3 cjNeutral(vec3 color) {
  const float startCompression = 0.8 - 0.04;
  const float desaturation = 0.15;
  color *= exposure;
  float x = min(color.r, min(color.g, color.b));
  float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
  color -= offset;
  float peak = max(color.r, max(color.g, color.b));
  if (peak < startCompression) return color;
  float d = 1.0 - startCompression;
  float newPeak = 1.0 - d * d / (peak + d - startCompression);
  color *= newPeak / peak;
  float g = 1.0 - 1.0 / (desaturation * (peak - newPeak) + 1.0);
  return mix(color, vec3(newPeak), g);
}
vec3 cjToSRGB(vec3 c) {
  c = clamp(c, 0.0, 1.0);
  return mix(c * 12.92, pow(c, vec3(1.0 / 2.4)) * 1.055 - 0.055, step(0.0031308, c));
}
float cjHash(vec2 p) {
  p = fract(p * vec2(443.897, 441.423));
  p += dot(p, p.yx + 19.19);
  return fract((p.x + p.y) * p.x);
}

void main() {
  vec2 uv = uvRect.xy + vUv * uvRect.zw;
  vec3 c = texture2D(tScene, uv).rgb;
  if (toneMode == 1) c = cjAces(c);
  else if (toneMode == 2) c = cjNeutral(c);
  else c *= exposure;
  c = cjToSRGB(c);

  // 风格调色（显示空间）
  float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(luma), c, saturation);
  c = (c - 0.5) * contrast + 0.5;
  c *= tint;
  c = mix(c, c * highlight, smoothstep(0.55, 1.0, luma));
  c = fadeColor * fade + c * (1.0 - fade);
  c = clamp(c, 0.0, 1.0);

  if (useLut > 0.5) {
    vec3 lc = c * ((lutSize - 1.0) / lutSize) + 0.5 / lutSize;
    c = texture(tLut, lc).rgb;
  }

  // 暗角按照片自身的画面算，不按整屏
  vec2 q = vUv - 0.5;
  q.x *= resolution.x / resolution.y;
  float v = smoothstep(0.85, 0.2, length(q) * 1.05);
  c *= mix(1.0, v, vignette);

  // 颗粒：中间调最明显
  float n = cjHash(vUv * resolution + seed) - 0.5;
  c += n * grain * (1.0 - abs(luma - 0.5) * 1.2);

  gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}`;

const dummyLut = (() => {
  const t = new THREE.Data3DTexture(new Uint8Array([255, 255, 255, 255]), 1, 1, 1);
  t.needsUpdate = true;
  return t;
})();

export class GradePass {
  constructor() {
    this.material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        tScene: { value: null },
        tLut: { value: dummyLut },
        useLut: { value: 0 },
        lutSize: { value: 1 },
        toneMode: { value: 1 },
        exposure: { value: 1 },
        contrast: { value: 1 },
        saturation: { value: 1 },
        tint: { value: new THREE.Vector3(1, 1, 1) },
        fade: { value: 0 },
        fadeColor: { value: new THREE.Vector3() },
        highlight: { value: new THREE.Vector3(1, 1, 1) },
        grain: { value: 0 },
        vignette: { value: 0 },
        seed: { value: 0 },
        resolution: { value: new THREE.Vector2(1, 1) },
        uvRect: { value: new THREE.Vector4(0, 0, 1, 1) },
      },
      depthTest: false,
      depthWrite: false,
    });
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.material);
    this.quad.frustumCulled = false;
    this.scene = new THREE.Scene();
    this.scene.add(this.quad);
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.luts = new Map();
  }

  // 跟随宿主渲染器的色调映射，避免拍出来的颜色和平时看到的不一样
  syncToneMapping(renderer) {
    const u = this.material.uniforms;
    u.exposure.value = renderer.toneMappingExposure;
    if (renderer.toneMapping === THREE.NoToneMapping) u.toneMode.value = 0;
    else if (renderer.toneMapping === THREE.NeutralToneMapping) u.toneMode.value = 2;
    else u.toneMode.value = 1; // ACES；AgX 等其他映射暂时按 ACES 处理
  }

  async setStyle(style) {
    const u = this.material.uniforms;
    const g = style.grade;
    u.contrast.value = g.contrast;
    u.saturation.value = g.saturation;
    u.tint.value.fromArray(g.tint);
    u.fade.value = g.fade;
    u.fadeColor.value.fromArray(g.fadeColor);
    u.highlight.value.fromArray(g.highlight);
    u.grain.value = g.grain;
    u.vignette.value = g.vignette;
    u.useLut.value = 0;
    if (style.lut) {
      let lut = this.luts.get(style.lut);
      if (!lut) {
        const { LUTCubeLoader } = await import('three/addons/loaders/LUTCubeLoader.js');
        lut = await new LUTCubeLoader().loadAsync(style.lut);
        this.luts.set(style.lut, lut);
      }
      u.tLut.value = lut.texture3D;
      u.lutSize.value = lut.size;
      u.useLut.value = 1;
    }
  }

  render(renderer, input, target, { width, height, seed = 0, uvRect = null }) {
    const u = this.material.uniforms;
    u.tScene.value = input.texture;
    u.resolution.value.set(width, height);
    u.seed.value = seed;
    if (uvRect) u.uvRect.value.set(...uvRect);
    else u.uvRect.value.set(0, 0, 1, 1);
    renderer.setRenderTarget(target);
    renderer.render(this.scene, this.camera);
  }

  dispose() {
    this.material.dispose();
    this.quad.geometry.dispose();
  }
}

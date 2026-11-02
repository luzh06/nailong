// 相机风格调色：输入是画面管线输出的最终显示色（sRGB），只在这之上做“相机的味道”。
// 场景本身的曝光、泛光、AgX 查找表都由管线负责，所以照片和玩家看到的画面是同一套颜色。
// 预览（画到屏幕）和拍照（画到离屏目标）共用这个通道，取景所见即所得。
import * as THREE from 'three';
import { fullscreenPass } from '../render/pipeline.js';

const FRAG = /* glsl */ `
uniform sampler2D tSrc;
uniform sampler3D tLut;
uniform float useLut, lutSize;
uniform float strength;        // 0 = 原样（用于对比），1 = 完整风格
uniform float contrast, saturation, fade, grain, vignette, seed;
uniform vec3 tint, fadeColor, highlight, shadowTint;
uniform vec2 resolution;
uniform vec4 uvRect;           // 取样区域 x, y, w, h

float cjHash(vec2 p) {
  p = fract(p * vec2(443.897, 441.423));
  p += dot(p, p.yx + 19.19);
  return fract((p.x + p.y) * p.x);
}

void main() {
  vec2 uv = uvRect.xy + vUv * uvRect.zw;
  vec3 src = texture(tSrc, uv).rgb;
  vec3 c = src;
  float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(luma), c, saturation);
  c = (c - 0.5) * contrast + 0.5;
  c *= tint;
  // 分离色调：暗部和亮部各偏一点色（胶片的冷暗部、暖高光）
  c = mix(c * shadowTint, c, smoothstep(0.0, 0.45, luma));
  c = mix(c, c * highlight, smoothstep(0.55, 1.0, luma));
  c = fadeColor * fade + c * (1.0 - fade);
  c = clamp(c, 0.0, 1.0);
  if (useLut > 0.5) {
    vec3 lc = c * ((lutSize - 1.0) / lutSize) + 0.5 / lutSize;
    c = texture(tLut, lc).rgb;
  }
  // 暗角按照片自身的画面算
  vec2 q = vUv - 0.5;
  q.x *= resolution.x / resolution.y;
  c *= mix(1.0, smoothstep(0.85, 0.2, length(q) * 1.05), vignette);
  // 颗粒：中间调最明显
  c += (cjHash(vUv * resolution + seed) - 0.5) * grain * (1.0 - abs(luma - 0.5) * 1.2);
  oc = vec4(clamp(mix(src, c, strength), 0.0, 1.0), 1.0);
}`;

const dummyLut = (() => {
  const t = new THREE.Data3DTexture(new Uint8Array([255, 255, 255, 255]), 1, 1, 1);
  t.needsUpdate = true;
  return t;
})();

export class GradePass {
  constructor() {
    this.pass = fullscreenPass(FRAG, {
      tSrc: { value: null },
      tLut: { value: dummyLut },
      useLut: { value: 0 },
      lutSize: { value: 1 },
      strength: { value: 1 },
      contrast: { value: 1 },
      saturation: { value: 1 },
      tint: { value: new THREE.Vector3(1, 1, 1) },
      fade: { value: 0 },
      fadeColor: { value: new THREE.Vector3() },
      highlight: { value: new THREE.Vector3(1, 1, 1) },
      shadowTint: { value: new THREE.Vector3(1, 1, 1) },
      grain: { value: 0 },
      vignette: { value: 0 },
      seed: { value: 0 },
      resolution: { value: new THREE.Vector2(1, 1) },
      uvRect: { value: new THREE.Vector4(0, 0, 1, 1) },
    });
    this.luts = new Map();
  }

  get strength() {
    return this.pass.u.strength.value;
  }
  set strength(v) {
    this.pass.u.strength.value = v;
  }

  async setStyle(style) {
    const u = this.pass.u;
    const g = style.grade;
    u.contrast.value = g.contrast;
    u.saturation.value = g.saturation;
    u.tint.value.fromArray(g.tint);
    u.fade.value = g.fade;
    u.fadeColor.value.fromArray(g.fadeColor);
    u.highlight.value.fromArray(g.highlight);
    u.shadowTint.value.fromArray(g.shadow ?? [1, 1, 1]);
    u.grain.value = g.grain;
    u.vignette.value = g.vignette;
    u.useLut.value = 0;
    u.tLut.value = dummyLut;
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
    const u = this.pass.u;
    u.tSrc.value = input.texture;
    u.resolution.value.set(width, height);
    u.seed.value = seed;
    if (uvRect) u.uvRect.value.set(...uvRect);
    else u.uvRect.value.set(0, 0, 1, 1);
    this.pass.draw(renderer, target);
  }

  dispose() {
    this.pass.dispose();
  }
}

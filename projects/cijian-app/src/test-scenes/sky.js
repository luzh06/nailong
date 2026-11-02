// 测试场景用的渐变天空（天顶、地平线、太阳光晕），顺便做成环境贴图给水面和金属反光。
// 只是占位，正式场景用各自的 HDRI。
import * as THREE from 'three';

export function makeSky(renderer, scene, radius) {
  const u = {
    top: { value: new THREE.Color() },
    horizon: { value: new THREE.Color() },
    bottom: { value: new THREE.Color() },
    sunDir: { value: new THREE.Vector3(0, 1, 0) },
    sunColor: { value: new THREE.Color() },
    sunSize: { value: 0.02 },
    glow: { value: 1 },
  };
  const mat = new THREE.ShaderMaterial({
    uniforms: u,
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    vertexShader: `varying vec3 vDir;
      void main(){ vDir = normalize(position); vec4 p = modelViewMatrix * vec4(position,1.); gl_Position = projectionMatrix * p; gl_Position.z = gl_Position.w; }`,
    fragmentShader: `uniform vec3 top, horizon, bottom, sunDir, sunColor; uniform float sunSize, glow; varying vec3 vDir;
      void main(){
        vec3 d = normalize(vDir);
        float y = d.y;
        vec3 c = y > 0. ? mix(horizon, top, pow(y, .45)) : mix(horizon, bottom, pow(min(-y * 6., 1.), .6));
        float s = max(dot(d, normalize(sunDir)), 0.);
        c += sunColor * (pow(s, 8.) * .25 + pow(s, 64.) * .6) * glow;
        c += sunColor * smoothstep(cos(sunSize), cos(sunSize * .7), s) * 20.;
        gl_FragColor = vec4(c, 1.);
      }`,
  });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(radius, 48, 24), mat);
  dome.frustumCulled = false;
  dome.renderOrder = -1;
  dome.onBeforeRender = (r, s, cam) => dome.position.copy(cam.position);
  scene.add(dome);

  // 环境贴图：单独拿天空画一张
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envScene = new THREE.Scene();
  const envDome = new THREE.Mesh(new THREE.SphereGeometry(10, 32, 16), mat);
  envScene.add(envDome);
  let envRT = null;

  return {
    dome,
    set({ top, horizon, bottom, sunDir, sunColor, sunSize = 0.02, glow = 1 }) {
      u.top.value.set(top);
      u.horizon.value.set(horizon);
      u.bottom.value.set(bottom ?? horizon);
      u.sunDir.value.set(...sunDir).normalize();
      u.sunColor.value.set(sunColor);
      u.sunSize.value = sunSize;
      u.glow.value = glow;
      envRT?.dispose();
      envRT = pmrem.fromScene(envScene, 0.02);
      scene.environment = envRT.texture;
    },
  };
}

// 写字的招牌贴图（招牌全是虚构店名）
export function signTexture(text, { w = 512, h = 160, bg = '#efe4cc', fg = '#1d1a17', font = '"Songti SC","Hiragino Mincho ProN",serif', weight = 700, vertical = false } = {}) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const g = c.getContext('2d');
  g.fillStyle = bg;
  g.fillRect(0, 0, w, h);
  g.strokeStyle = fg;
  g.lineWidth = Math.min(w, h) * 0.03;
  g.strokeRect(g.lineWidth, g.lineWidth, w - g.lineWidth * 2, h - g.lineWidth * 2);
  g.fillStyle = fg;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  if (vertical) {
    const chars = [...text];
    const px = Math.min(w * 0.7, (h * 0.85) / chars.length);
    g.font = `${weight} ${px}px ${font}`;
    chars.forEach((ch, i) => g.fillText(ch, w / 2, h * 0.075 + px * (i + 0.5)));
  } else {
    let px = h * 0.55;
    g.font = `${weight} ${px}px ${font}`;
    const tw = g.measureText(text).width;
    if (tw > w * 0.86) px *= (w * 0.86) / tw;
    g.font = `${weight} ${px}px ${font}`;
    g.fillText(text, w / 2, h * 0.53);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

export function stripeTexture(a, b, n = 8) {
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 16;
  const g = c.getContext('2d');
  for (let i = 0; i < n; i++) {
    g.fillStyle = i % 2 ? b : a;
    g.fillRect((i * 256) / n, 0, 256 / n + 1, 16);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function mulberry32(a) {
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

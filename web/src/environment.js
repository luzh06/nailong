import * as THREE from 'three';
import { CSM } from 'three/addons/csm/CSM.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { Water } from 'three/addons/objects/Water.js';
import { loadShoreTexture, upgradeWater } from './water.js';

const SKY = './assets/sky';

// hdrSun: where the sun (or brightest glow) sits in each HDRI, measured by scanning the 1k HDR
// (u = horizontal position 0..1, elevation in degrees). azimuth: where we want it, clockwise from
// north. The sky is rotated so the two agree, and the shadow-casting light follows the same line.
// fog: average colour of the sky backdrop 1-5 degrees above the horizon (x background intensity),
// so distant water fades into the sky rather than into a band of a different colour.
// water: light reaching the water body (x2 in the shader; 0x808080 = neutral daylight).
export const TIME_PRESETS = {
  day: {
    label: '白天', sky: 'kloofendal_48d_partly_cloudy_puresky', hdrSun: { u: 0.5952, elevation: 47.99 },
    azimuth: 20, sunColor: 0xfff1de, sunIntensity: 3.2, envIntensity: 1.0, backgroundIntensity: 1.0,
    exposure: 0.8, fog: 0x9ca0af, fogDensity: 0.00010, night: 0, bloom: 0.1, water: 0x808080, tileTint: 0xffffff, interior: 0.22,
  },
  golden: {
    label: '黄金时段', sky: 'belfast_sunset_puresky', hdrSun: { u: 0.605, elevation: 1.93 },
    azimuth: 285, lightElevation: 7, sunColor: 0xffb46e, sunIntensity: 2.6, envIntensity: 0.9,
    backgroundIntensity: 1.0, exposure: 0.8, fog: 0x978b84, fogDensity: 0.00013, night: 0.12, bloom: 0.3,
    water: 0x6e6256, tileTint: 0xf2d2b0, interior: 0.15,
  },
  blue: {
    label: '蓝调', sky: 'qwantani_dusk_2_puresky', hdrSun: { u: 0.5903, elevation: 12.13 },
    azimuth: 280, lightElevation: 8, sunColor: 0x9db4ff, sunIntensity: 0.15, envIntensity: 0.32,
    backgroundIntensity: 0.55, exposure: 1.1, fog: 0x524850, fogDensity: 0.00015, night: 1, bloom: 0.75,
    water: 0x1a2030, tileTint: 0x39405a, interior: 0.05,
  },
};

function directionFromAzimuth(azimuthDeg, elevationDeg) {
  const az = THREE.MathUtils.degToRad(azimuthDeg);
  const el = THREE.MathUtils.degToRad(elevationDeg);
  return new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
}

/** Rotation about Y that carries the HDRI's sun (at horizontal position u) to the wanted azimuth. */
function skyRotation(u, azimuthDeg) {
  const hdrAngle = (u - 0.5) * Math.PI * 2;              // equirect: angle in the X/Z plane, from +X
  const wanted = directionFromAzimuth(azimuthDeg, 0);
  return Math.atan2(wanted.z, wanted.x) - hdrAngle;
}

export class Environment {
  constructor(renderer, scene, camera, quality, extent) {
    this.renderer = renderer;
    this.scene = scene;
    this.pmrem = new THREE.PMREMGenerator(renderer);
    this.hdrLoader = new RGBELoader();
    this.texLoader = new THREE.TextureLoader();
    this.cache = new Map();

    this.csm = new CSM({
      maxFar: quality === 'low' ? 1200 : 3500,
      cascades: quality === 'low' ? 2 : 3,
      mode: 'practical',
      parent: scene,
      shadowMapSize: quality === 'low' ? 1024 : 2048,
      lightDirection: new THREE.Vector3(-1, -1, 0).normalize(),
      lightIntensity: 3,
      lightFar: 6000,
      lightMargin: 600,
      camera,
    });
    for (const light of this.csm.lights) {
      light.shadow.normalBias = 0.6;
      light.shadow.bias = -0.0002;
    }

    const normals = this.texLoader.load('./assets/water/waternormals.jpg');
    normals.wrapS = normals.wrapT = THREE.RepeatWrapping;
    this.water = new Water(new THREE.PlaneGeometry(40000, 40000), {
      textureWidth: quality === 'low' ? 512 : 1024,
      textureHeight: quality === 'low' ? 512 : 1024,
      waterNormals: normals,
      sunDirection: new THREE.Vector3(0, 1, 0),
      sunColor: 0xffffff,
      waterColor: 0x0e3a49,
      // Moderate chop: reflections stay readable, broken up but not smeared
      distortionScale: 3.5,
      fog: true,
    });
    upgradeWater(this.water, { shoreTexture: loadShoreTexture(), extent });
    this.water.rotation.x = -Math.PI / 2;
    this.water.material.uniforms.size.value = 2.0;
    this.water.receiveShadow = false;
    scene.add(this.water);
  }

  async loadSky(name) {
    if (!this.cache.has(name)) {
      const [hdr, backdrop] = await Promise.all([
        this.hdrLoader.loadAsync(`${SKY}/${name}_1k.hdr`),
        this.texLoader.loadAsync(`${SKY}/${name}_backdrop.jpg`),
      ]);
      hdr.mapping = THREE.EquirectangularReflectionMapping;
      const env = this.pmrem.fromEquirectangular(hdr).texture;
      hdr.dispose();
      backdrop.mapping = THREE.EquirectangularReflectionMapping;
      backdrop.colorSpace = THREE.SRGBColorSpace;
      this.cache.set(name, { env, backdrop });
    }
    return this.cache.get(name);
  }

  async apply(presetName) {
    const p = TIME_PRESETS[presetName];
    const { env, backdrop } = await this.loadSky(p.sky);
    const rotation = skyRotation(p.hdrSun.u, p.azimuth);
    const s = this.scene;
    s.environment = env;
    s.background = backdrop;
    // three.js rotates the lookup direction, so the visible sky turns the opposite way
    s.environmentRotation.set(0, -rotation, 0);
    s.backgroundRotation.set(0, -rotation, 0);
    s.environmentIntensity = p.envIntensity;
    s.backgroundIntensity = p.backgroundIntensity;
    s.fog = new THREE.FogExp2(p.fog, p.fogDensity);

    const sunDir = directionFromAzimuth(p.azimuth, p.lightElevation ?? p.hdrSun.elevation);
    this.csm.lightDirection.copy(sunDir).negate();
    for (const light of this.csm.lights) {
      light.color.set(p.sunColor);
      light.intensity = p.sunIntensity;
    }
    const u = this.water.material.uniforms;
    u.sunDirection.value.copy(sunDir);
    u.sunColor.value.set(p.sunColor).multiplyScalar(Math.min(1, p.sunIntensity / 2));
    u.waterColor.value.set(p.water);
    this.renderer.toneMappingExposure = p.exposure;
    return p;
  }

  update(dt) {
    this.csm.update();
    this.water.material.uniforms.time.value += dt * this.waterSpeed;
  }

  waterSpeed = 0.5;
}

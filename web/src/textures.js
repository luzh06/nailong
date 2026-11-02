import * as THREE from 'three';

// Texture sets built by scripts/fetch_assets.py: assets/textures/<id>/{diff,nor,arm}.jpg
// arm = ambient occlusion (R), roughness (G), metalness (B) — three.js reads the same channels.
const BASE = './assets/textures';

export class TextureLibrary {
  constructor(renderer, manager) {
    this.loader = new THREE.TextureLoader(manager);
    this.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    this.images = new Map();
  }

  /** Raw texture, loaded once and shared; clone() it before giving it its own repeat. */
  load(url, srgb) {
    const key = `${url}|${srgb}`;
    if (!this.images.has(key)) {
      const tex = this.loader.load(url);
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = this.anisotropy;
      tex.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      this.images.set(key, tex);
    }
    return this.images.get(key);
  }

  /**
   * PBR maps for a texture set, tiled so one texture repeat covers `metres` of a surface whose
   * UVs are in metres. Returns material properties ready to spread into a MeshStandardMaterial.
   */
  pbr(id, metres, { normal = true, arm = true } = {}) {
    const tile = (tex) => {
      const t = tex.clone();
      t.repeat.set(1 / metres, 1 / metres);
      t.needsUpdate = true;
      return t;
    };
    const props = { map: tile(this.load(`${BASE}/${id}/diff.jpg`, true)) };
    if (normal) props.normalMap = tile(this.load(`${BASE}/${id}/nor.jpg`, false));
    if (arm) {
      const armTex = tile(this.load(`${BASE}/${id}/arm.jpg`, false));
      Object.assign(props, { roughnessMap: armTex, aoMap: armTex, roughness: 1, metalness: 0 });
    }
    return props;
  }

  /** Untiled sampler for shader-driven use (the shader applies its own scale). */
  raw(id, map = 'diff') {
    return this.load(`${BASE}/${id}/${map}.jpg`, map === 'diff');
  }
}

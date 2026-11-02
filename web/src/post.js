import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// Scene -> bloom (in linear HDR, so only genuinely bright things glow: sun glints on the water,
// lamps, lit windows) -> tone mapping and sRGB output. 4x MSAA on the half-float target.
export function createPost(renderer, scene, camera, quality) {
  const size = renderer.getSize(new THREE.Vector2());
  const target = new THREE.WebGLRenderTarget(size.x, size.y, {
    type: THREE.HalfFloatType,
    samples: quality === 'low' ? 0 : 4,
  });
  const composer = new EffectComposer(renderer, target);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(size.clone().multiplyScalar(0.5), 0.2, 0.55, 1.0);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  return {
    composer,
    setBloom(strength) {
      bloom.strength = strength;
      bloom.enabled = strength > 0.01;
    },
    setSize(w, h) {
      composer.setSize(w, h);
      bloom.resolution.set(w / 2, h / 2);
    },
  };
}

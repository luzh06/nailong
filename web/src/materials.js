import * as THREE from 'three';
import { facadeFragmentMain, facadeFragmentPars, facadeVertex } from './shaders/facade.js';
import { groundFragmentMain, groundFragmentPars, groundVertex } from './shaders/ground.js';
import { tileFragmentMain, tileFragmentPars, tileVertex } from './shaders/opera.js';

/**
 * Patch a built-in material's shader. CSM (cascaded shadows) installs its own onBeforeCompile,
 * so ours runs after it instead of replacing it.
 */
function patchShader(material, spec, csm) {
  csm.setupMaterial(material);
  const csmHook = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    csmHook.call(material, shader, renderer);
    Object.assign(shader.uniforms, spec.uniforms ?? {});
    if (spec.vertex) {
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', `#include <common>\n${spec.vertex.pars}`)
        .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>\n${spec.vertex.main}`);
    }
    let frag = shader.fragmentShader.replace('#include <common>', `#include <common>\n${spec.fragmentPars ?? ''}`);
    if (spec.fragmentMain) frag = frag.replace('#include <map_fragment>', spec.fragmentMain);
    if (spec.roughness) frag = frag.replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>\n${spec.roughness}`);
    if (spec.metalness) frag = frag.replace('#include <metalnessmap_fragment>', `#include <metalnessmap_fragment>\n${spec.metalness}`);
    if (spec.emissive) frag = frag.replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>\n${spec.emissive}`);
    shader.fragmentShader = frag;
  };
  material.customProgramCacheKey = () => spec.key;
  return material;
}

export function createMaterials(lib, csm, landcover) {
  const night = { value: 0 };
  const flood = { value: 0 };
  const [x0, y0, x1, y1] = landcover.extent;
  const mask = new THREE.TextureLoader().load('./assets/ground/landcover.webp');
  mask.colorSpace = THREE.NoColorSpace;

  const facade = patchShader(new THREE.MeshStandardMaterial({ map: lib.raw('concrete_wall_008') }), {
    key: 'facade',
    uniforms: {
      uNight: night,
      uRoofMap: { value: lib.raw('concrete_floor_worn_001') },
      uTerracottaMap: { value: lib.raw('ceramic_roof_01') },
    },
    vertex: facadeVertex,
    fragmentPars: facadeFragmentPars,
    fragmentMain: facadeFragmentMain,
    roughness: 'roughnessFactor = fRough;',
    metalness: 'metalnessFactor = fMetal;',
    emissive: 'totalEmissiveRadiance += fEmissive;',
  }, csm);

  const ground = patchShader(new THREE.MeshStandardMaterial({ roughness: 0.9 }), {
    key: 'ground',
    uniforms: {
      uLandcover: { value: mask },
      uExtent: { value: new THREE.Vector4(x0, y0, x1 - x0, y1 - y0) },
      uPave: { value: lib.raw('concrete_floor_worn_001') },
      uGrass: { value: lib.raw('lawn') },
      uRoad: { value: lib.raw('asphalt_02') },
      uSand: { value: lib.raw('coast_sand_01') },
      uRock: { value: lib.raw('rock_pitted_mossy') },
      uNight: night,
    },
    vertex: groundVertex,
    fragmentPars: groundFragmentPars,
    fragmentMain: groundFragmentMain,
    roughness: 'roughnessFactor = gRough;',
    emissive: 'totalEmissiveRadiance += gEmissive;',
  }, csm);

  const tile = patchShader(new THREE.MeshPhysicalMaterial({
    color: 0xffffff, roughness: 0.3, clearcoat: 0.35, clearcoatRoughness: 0.18, side: THREE.DoubleSide,
  }), {
    key: 'opera-tile',
    uniforms: { uFlood: flood },
    vertex: tileVertex,
    fragmentPars: tileFragmentPars,
    fragmentMain: tileFragmentMain,
    roughness: 'roughnessFactor = tRough;',
    emissive: 'totalEmissiveRadiance += vec3(1.0, 0.92, 0.8) * uFlood * 0.6;',
  }, csm);

  const operaGlass = new THREE.MeshPhysicalMaterial({
    // bronze-tinted glazing: dark, but reflective enough to pick up the sky and the harbour
    color: 0x4a3a2c, metalness: 0.55, roughness: 0.1, emissive: 0xffa860, emissiveIntensity: 0,
    side: THREE.DoubleSide,
  });
  csm.setupMaterial(operaGlass);

  const standard = (props, tint) => {
    const m = new THREE.MeshStandardMaterial(props);
    if (tint) m.color.set(tint);
    csm.setupMaterial(m);
    return m;
  };
  const byName = {
    building_facade: facade,
    ground_terrain: ground,
    // The walkable foreshore uses the same land-cover blend: grass where the parks are, paving on paths
    walk_promenade: ground,
    seawall_sandstone: standard(lib.pbr('sandstone_blocks_05', 3.0), 0xf2e2cc),
    // "Bridge grey" paint: the plate texture's rusty albedo is far too dark, so keep only its
    // relief (plate seams, rivets) and roughness and paint the colour on
    bridge_steel: standard({ ...lib.pbr('metal_plate', 2.0), map: null }, 0x7f8784),
    bridge_granite: standard(lib.pbr('sandstone_blocks_08', 4.0), 0xc8c6c0), // Moruya granite ashlar
    bridge_deck: standard(lib.pbr('asphalt_02', 6.0), 0x9a9a9a),
    opera_tile: tile,
    opera_glass: operaGlass,
    // pink Tarana granite aggregate panels; a fine scale so the aggregate does not read as brick
    opera_podium: standard(lib.pbr('gravel_embedded_concrete', 1.2), 0xdcb7a6),
  };

  return {
    byName,
    setNight(amount) {
      night.value = amount;
      flood.value = amount;
      operaGlass.emissiveIntensity = 0.9 * amount;
    },
  };
}

/** Swap the exported placeholder materials for the real ones and set up shadows. */
export function applyMaterials(root, materials) {
  const missing = new Set();
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const name = obj.material.name;
    const replacement = materials.byName[name];
    if (!replacement) {
      missing.add(name);
      return;
    }
    if (name === 'building_facade') {
      // The façade shader reads the per-building colour attribute as `bstyle`
      obj.geometry.setAttribute('bstyle', obj.geometry.getAttribute('color'));
      obj.geometry.deleteAttribute('color');
    }
    obj.material = replacement;
    obj.castShadow = name !== 'walk_promenade' && name !== 'ground_terrain';
    obj.receiveShadow = true;
  });
  return [...missing];
}

import * as THREE from 'three';

// Harbour water on top of three.js' Water (planar reflection + scrolling normal maps), with the
// parts that made it read as a distorted mirror replaced:
//  - Fresnel reflectance with F0 = 0.02 (water) instead of 0.3, and no flat grey added to the
//    reflection, so looking down shows the water body and grazing views reflect the skyline.
//  - Colour by distance to shore (web/assets/water/shore_distance.png, scripts/build_landcover.py):
//    green-teal shallows along seawalls and beaches fading to deep harbour blue-green.
//  - An animated wash of foam where water meets seawalls, wharves and rock.

const SHORE_MAX_METRES = 64.0;

const SHORE_PARS = /* glsl */ `
  uniform sampler2D shoreMap;
  uniform vec4 shoreExtent;     // x0, y0 (south-west corner, scene metres), width, height
  uniform vec3 shallowColor;
  uniform vec3 deepColor;
  uniform vec3 foamColor;
`;

const SHORE_MAIN = /* glsl */ `
  vec2 shoreXY = vec2(worldPosition.x, -worldPosition.z);
  float shoreDist = texture2D(shoreMap, (shoreXY - shoreExtent.xy) / shoreExtent.zw).r * ${SHORE_MAX_METRES.toFixed(1)};
  vec3 bodyColor = mix(shallowColor, deepColor, smoothstep(0.0, 28.0, shoreDist));
  float wash = 1.0 - smoothstep(0.0, 2.4, shoreDist);
  float churn = texture2D(normalSampler, shoreXY * 0.31 + vec2(time * 0.03, -time * 0.02)).r;
  float lap = 0.5 + 0.5 * sin(shoreDist * 4.0 - time * 1.6 + churn * 4.0);
  float foam = wash * smoothstep(0.35, 0.8, churn * 0.7 + lap * 0.5) * (0.6 + 0.4 * wash);
`;

export function upgradeWater(water, { shoreTexture, extent }) {
  const material = water.material;
  const [x0, y0, x1, y1] = extent;
  Object.assign(material.uniforms, {
    shoreMap: { value: shoreTexture },
    shoreExtent: { value: new THREE.Vector4(x0, y0, x1 - x0, y1 - y0) },
    shallowColor: { value: new THREE.Color(0x1d5a52) },
    deepColor: { value: new THREE.Color(0x0a2e3a) },
    foamColor: { value: new THREE.Color(0xe8ece8) },
  });
  let fs = material.fragmentShader;
  const replace = (from, to) => {
    if (!fs.includes(from)) throw new Error(`water shader patch failed: ${from.slice(0, 40)}`);
    fs = fs.replace(from, to);
  };
  replace('uniform vec3 waterColor;', `uniform vec3 waterColor;\n${SHORE_PARS}`);
  replace('vec3 diffuseLight = vec3(0.0);', `${SHORE_MAIN}\n\t\t\t\t\tvec3 diffuseLight = vec3(0.0);`);
  replace('float rf0 = 0.3;', 'float rf0 = 0.02;');
  replace('vec3 scatter = max( 0.0, dot( surfaceNormal, eyeDirection ) ) * waterColor;',
    'vec3 scatter = max( 0.0, dot( surfaceNormal, eyeDirection ) ) * bodyColor * waterColor * 2.0;');
  replace('( vec3( 0.1 ) + reflectionSample * 0.9 + reflectionSample * specularLight )',
    '( reflectionSample + reflectionSample * specularLight )');
  replace('vec3 outgoingLight = albedo;',
    'vec3 outgoingLight = mix(albedo, foamColor * (sunColor * 0.5 + 0.35), foam);');
  material.fragmentShader = fs;
  material.needsUpdate = true;
  return water;
}

export function loadShoreTexture() {
  const tex = new THREE.TextureLoader().load('./assets/water/shore_distance.png');
  tex.colorSpace = THREE.NoColorSpace;
  return tex;
}

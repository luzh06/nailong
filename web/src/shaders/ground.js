// Terrain surface: blends paving, asphalt, grass, sand and sandstone from the land-cover mask
// (scripts/build_landcover.py). Steep slopes turn to rock whatever the mask says. Every layer is
// sampled at two scales and mixed by a slow noise so the textures do not visibly repeat.

export const groundVertex = {
  pars: /* glsl */ `
    varying vec3 vGroundPos;
    varying float vGroundUp;
  `,
  main: /* glsl */ `
    vGroundPos = (modelMatrix * vec4(transformed, 1.0)).xyz;
    vGroundUp = normalize(mat3(modelMatrix) * objectNormal).y;
  `,
};

export const groundFragmentPars = /* glsl */ `
  varying vec3 vGroundPos;
  varying float vGroundUp;
  uniform sampler2D uLandcover;
  uniform vec4 uExtent;          // x0, y0 (south-west corner, scene metres), width, height
  uniform sampler2D uPave;
  uniform sampler2D uGrass;
  uniform sampler2D uRoad;
  uniform sampler2D uSand;
  uniform sampler2D uRock;
  uniform float uNight;
  float gRough;
  vec3 gEmissive;

  float gHash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float gNoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(gHash(i), gHash(i + vec2(1, 0)), u.x), mix(gHash(i + vec2(0, 1)), gHash(i + vec2(1, 1)), u.x), u.y);
  }
  // Two scales, the second rotated, blended by low-frequency noise: hides tiling
  vec3 layer(sampler2D tex, vec2 xy, float metres, float blend) {
    vec3 a = texture2D(tex, xy / metres).rgb;
    vec2 r = mat2(0.8, -0.6, 0.6, 0.8) * xy;
    vec3 b = texture2D(tex, r / (metres * 3.7)).rgb;
    return mix(a, b, blend);
  }
`;

export const groundFragmentMain = /* glsl */ `
  vec2 gxy = vec2(vGroundPos.x, -vGroundPos.z);          // scene metres: x east, y north
  vec4 cover = texture2D(uLandcover, (gxy - uExtent.xy) / uExtent.zw);
  float macro = gNoise(gxy / 90.0);
  float mixer = gNoise(gxy / 23.0 + 7.0);
  float steep = smoothstep(0.62, 0.82, 1.0 - vGroundUp);

  vec3 pave = layer(uPave, gxy, 4.0, mixer * 0.5) * vec3(0.8, 0.78, 0.74);
  // Asphalt clearly darker than footpaths, so streets read from across the harbour
  vec3 road = layer(uRoad, gxy, 5.0, mixer * 0.4) * 0.48;
  // Sydney lawns: green, with drier yellow-green patches across large parks
  vec3 grass = layer(uGrass, gxy, 2.5, mixer * 0.6) * mix(vec3(1.0, 1.02, 0.95), vec3(1.25, 1.12, 0.8), macro * macro);
  // Lawns are never one even green: thicker darker tufts and worn patches at a few metres' scale
  float tuft = gNoise(gxy / 5.0 + 3.1);
  float fine = gNoise(gxy / 1.1 + 11.0);
  grass *= (0.78 + 0.42 * tuft) * (0.9 + 0.2 * fine);
  grass = mix(grass, grass * vec3(1.12, 1.05, 0.82), smoothstep(0.62, 0.9, tuft) * 0.6);
  vec3 sand = layer(uSand, gxy, 4.0, mixer * 0.5) * vec3(1.05, 0.98, 0.88);
  vec3 rock = layer(uRock, gxy, 6.0, mixer * 0.5) * vec3(1.08, 0.92, 0.74);

  float wRoad = cover.g;
  float wGrass = cover.r * (1.0 - wRoad);
  float wSand = cover.b;
  float wRock = max(cover.a, steep * (1.0 - wRoad));

  vec3 groundCol = pave;
  groundCol = mix(groundCol, road, wRoad);
  groundCol = mix(groundCol, grass, wGrass);
  groundCol = mix(groundCol, sand, wSand);
  groundCol = mix(groundCol, rock, wRock);
  diffuseColor.rgb = groundCol * (0.88 + 0.24 * macro);

  gRough = mix(mix(mix(mix(0.82, 0.88, wRoad), 0.96, wGrass), 0.92, wSand), 0.86, wRock);
  // Sodium-warm street light on roads and a faint spill on paving after dark
  gEmissive = vec3(1.0, 0.62, 0.32) * uNight * (0.05 * wRoad + 0.012 * (1.0 - wGrass - wRock));
`;

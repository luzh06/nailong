// Procedural façades for the OSM buildings, patched into MeshStandardMaterial.
//
// Per-building data comes from the `bstyle` attribute written by scripts/ground.py:
//   x = random seed, y = (style + 0.5) / 8, z = height / 300.
// Wall UVs are metres (U along the footprint perimeter, V = height above sea level); roof UVs are
// world X/Y metres. Windows are drawn with filtered edges and fade to their average colour once a
// window cell shrinks below a few pixels, so distant towers do not shimmer.

export const facadeVertex = {
  pars: /* glsl */ `
    attribute vec4 bstyle;
    varying vec4 vStyle;
    varying vec2 vFacadeUv;
    varying float vUpness;
  `,
  main: /* glsl */ `
    vStyle = bstyle;
    vFacadeUv = uv;
    vUpness = normalize(mat3(modelMatrix) * objectNormal).y;
  `,
};

export const facadeFragmentPars = /* glsl */ `
  varying vec4 vStyle;
  varying vec2 vFacadeUv;
  varying float vUpness;
  uniform float uNight;
  uniform sampler2D uRoofMap;
  uniform sampler2D uTerracottaMap;
  float fRough;
  float fMetal;
  vec3 fEmissive;

  float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
  }

  vec3 pick3(float s, vec3 a, vec3 b, vec3 c) {
    return s < 0.34 ? a : (s < 0.67 ? b : c);
  }

  // floorH, bayW: window grid in metres; win: window size as a fraction of the cell;
  // litShare: fraction of windows lit at night
  void facadeStyle(int st, float seed, out float floorH, out float bayW, out vec2 win,
                   out vec3 wall, out vec3 glass, out float litShare) {
    float s2 = fract(seed * 7.13);
    floorH = 3.4; bayW = 3.0; win = vec2(0.45, 0.5); litShare = 0.35;
    glass = vec3(0.07, 0.08, 0.09);
    if (st == 0) {        // glass curtain-wall tower
      floorH = 3.9; bayW = 1.5; win = vec2(0.93, 0.84); litShare = 0.5;
      wall = pick3(seed, vec3(0.56, 0.58, 0.6), vec3(0.17, 0.19, 0.21), vec3(0.74, 0.73, 0.69));
      glass = pick3(s2, vec3(0.30, 0.43, 0.50), vec3(0.24, 0.29, 0.37), vec3(0.36, 0.34, 0.31));
    } else if (st == 1) { // post-war office: concrete frame, ribbon windows
      floorH = 3.7; bayW = 2.8; win = vec2(0.64, 0.5); litShare = 0.45;
      wall = pick3(seed, vec3(0.72, 0.71, 0.68), vec3(0.6, 0.58, 0.54), vec3(0.8, 0.76, 0.68));
      glass = pick3(s2, vec3(0.16, 0.21, 0.25), vec3(0.12, 0.13, 0.14), vec3(0.22, 0.24, 0.22));
    } else if (st == 2) { // Sydney sandstone
      floorH = 4.2; bayW = 2.6; win = vec2(0.42, 0.55);
      wall = pick3(seed, vec3(0.8, 0.66, 0.46), vec3(0.73, 0.59, 0.41), vec3(0.85, 0.73, 0.55));
    } else if (st == 3) { // face brick
      floorH = 3.4; bayW = 2.8; win = vec2(0.4, 0.5);
      wall = pick3(seed, vec3(0.5, 0.26, 0.18), vec3(0.62, 0.4, 0.28), vec3(0.78, 0.66, 0.52));
    } else if (st == 4) { // rendered apartments
      floorH = 3.0; bayW = 3.2; win = vec2(0.48, 0.48); litShare = 0.4;
      wall = pick3(seed, vec3(0.9, 0.88, 0.83), vec3(0.86, 0.8, 0.7), vec3(0.76, 0.8, 0.78));
    } else if (st == 5) { // houses and terraces
      floorH = 3.0; bayW = 3.6; win = vec2(0.36, 0.45); litShare = 0.3;
      wall = pick3(seed, vec3(0.6, 0.33, 0.24), vec3(0.88, 0.86, 0.8), vec3(0.7, 0.66, 0.58));
    } else if (st == 6) { // garages, sheds, canopies
      win = vec2(0.0); litShare = 0.0;
      wall = pick3(seed, vec3(0.66, 0.64, 0.6), vec3(0.52, 0.5, 0.47), vec3(0.75, 0.72, 0.66));
    } else {              // wharf sheds and warehouses
      floorH = 6.0; bayW = 5.0; win = vec2(0.22, 0.16); litShare = 0.2;
      wall = pick3(seed, vec3(0.62, 0.6, 0.55), vec3(0.55, 0.52, 0.46), vec3(0.7, 0.68, 0.62));
    }
  }

  vec3 shadeRoof(int st, float seed, vec2 xy) {
    fRough = 0.9; fMetal = 0.0; fEmissive = vec3(0.0);
    vec3 roof;
    if (st == 5) {
      // houses: terracotta tiles (70 %) or a Colorbond steel roof
      vec3 tile = texture2D(uTerracottaMap, xy / 3.0).rgb;
      bool steel = fract(seed * 3.7) >= 0.7;
      roof = steel ? vec3(0.28, 0.3, 0.31) * (0.8 + 0.4 * tile.g) : tile * vec3(1.05, 0.92, 0.85);
      fRough = steel ? 0.5 : 0.85;
      fMetal = steel ? 0.3 : 0.0;
    } else {
      vec3 concrete = texture2D(uRoofMap, xy / 6.0).rgb;
      // plant rooms and skylights break up large flat roofs
      float plant = step(0.86, hash12(floor(xy / 4.0) + seed * 31.0));
      vec3 tint = st == 0 ? vec3(0.45) : pick3(fract(seed * 5.1), vec3(0.62), vec3(0.72, 0.7, 0.66), vec3(0.5, 0.5, 0.52));
      roof = mix(concrete * tint * 1.4, vec3(0.32, 0.33, 0.34), plant * 0.8);
    }
    return roof;
  }

  vec3 shadeWall(int st, float seed, vec2 uv, vec3 detail) {
    float floorH, bayW, litShare;
    vec2 win;
    vec3 wall, glass;
    facadeStyle(st, seed, floorH, bayW, win, wall, glass, litShare);

    vec2 cell = vec2(uv.x / bayW, uv.y / floorH);
    vec2 id = floor(cell);
    vec2 f = fract(cell);
    vec2 fw = max(fwidth(cell), vec2(1e-4));
    float mx = smoothstep(win.x * 0.5 + fw.x, win.x * 0.5 - fw.x, abs(f.x - 0.5));
    float my = smoothstep(win.y * 0.5 + fw.y, win.y * 0.5 - fw.y, abs(f.y - 0.55));
    float windowMask = mx * my;
    // Below ~3 px per cell the pattern would alias: fade to the cell's average coverage
    float far = smoothstep(0.25, 0.7, max(fw.x, fw.y));
    windowMask = mix(windowMask, win.x * win.y, far);

    float h = hash12(id + seed * 113.0);
    vec3 glassCol = glass * (0.75 + 0.5 * h);
    glassCol = mix(glassCol, vec3(0.62, 0.6, 0.55), step(0.9, h) * (1.0 - far)); // drawn blinds
    float grime = 1.0 - 0.07 * hash12(vec2(floor(uv.x * 1.5), seed * 7.0));
    vec3 wallCol = wall * (0.62 + 0.46 * detail) * grime;  // real façades are darker than their paint chips

    fRough = mix(st == 0 ? 0.35 : 0.82, 0.06, windowMask);
    fMetal = mix(st == 0 ? 0.5 : 0.0, 0.9, windowMask);
    // Lit windows: mostly warm interiors, some cool office light; whole floors tend to be lit together
    float floorOn = step(0.35, hash12(vec2(id.y, seed * 51.0)));
    float lit = step(hash12(id * 1.37 + seed * 17.0), litShare) * floorOn;
    vec3 lamp = mix(vec3(1.0, 0.7, 0.4), vec3(0.8, 0.88, 1.0), step(0.8, hash12(id + 3.1)) * (st <= 1 ? 1.0 : 0.3));
    fEmissive = lamp * (0.9 + 1.2 * h) * lit * windowMask * uNight * (1.0 - 0.45 * far);
    return mix(wallCol, glassCol, windowMask);
  }
`;

export const facadeFragmentMain = /* glsl */ `
  int facadeType = int(vStyle.y * 8.0);
  float facadeSeed = vStyle.x;
  vec3 facadeDetail = texture2D(map, vFacadeUv / 3.0).rgb;
  float facadeLum = dot(facadeDetail, vec3(0.333));
  if (vUpness > 0.6) {
    diffuseColor.rgb = shadeRoof(facadeType, facadeSeed, vFacadeUv);
  } else {
    diffuseColor.rgb = shadeWall(facadeType, facadeSeed, vFacadeUv, vec3(facadeLum));
  }
`;

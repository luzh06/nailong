// Procedural façades for the OSM buildings and landmark towers, patched into MeshStandardMaterial.
//
// Per-building data comes from the `bstyle` attribute written by scripts/ground.py and landmarks.py:
//   x = random seed, y = (style + 0.5) / 16, z = height / 300.
// Wall UVs are metres (U along the footprint perimeter, V = height above sea level); roof UVs are
// world X/Y metres.
//
// Windows are layered like real curtain walls and punched openings:
//   frame (aluminium) -> glass (dielectric, ~15 % reflectance for coated glass, Fresnel)
//   -> blinds -> an interior-mapped room behind each window (Joost van Dongen, "Interior Mapping",
//      2008): ceiling with a lamp, floor, side walls and back wall with a desk-height band, found by
//      intersecting the view ray with a box per window cell. Rooms switch on by floor and by window.
// The pattern fades to its average colour once a window cell shrinks below a few pixels.

export const facadeVertex = {
  pars: /* glsl */ `
    attribute vec4 bstyle;
    varying vec4 vStyle;
    varying vec2 vFacadeUv;
    varying float vUpness;
    varying vec3 vFacadePos;
    varying vec3 vFacadeNormal;
  `,
  main: /* glsl */ `
    vStyle = bstyle;
    vFacadeUv = uv;
    vFacadeNormal = normalize(mat3(modelMatrix) * objectNormal);
    vUpness = vFacadeNormal.y;
    vFacadePos = (modelMatrix * vec4(transformed, 1.0)).xyz;
  `,
};

export const facadeFragmentPars = /* glsl */ `
  varying vec4 vStyle;
  varying vec2 vFacadeUv;
  varying float vUpness;
  varying vec3 vFacadePos;
  varying vec3 vFacadeNormal;
  uniform float uNight;
  uniform float uInteriorAmbient;
  uniform sampler2D uRoofMap;
  uniform sampler2D uTerracottaMap;
  float fRough;
  float fMetal;
  vec3 fEmissive;
  float fWindowMask;

  float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
  }

  vec3 pick3(float s, vec3 a, vec3 b, vec3 c) {
    return s < 0.34 ? a : (s < 0.67 ? b : c);
  }

  struct Facade {
    float floorH, bayW, roomDepth, litShare;
    vec2 win;          // window size as a fraction of the cell
    vec3 wall, frame, glass;
    float wallRough, wallMetal, glassMetal;
  };

  Facade facadeStyle(int st, float seed) {
    float s2 = fract(seed * 7.13);
    Facade f;
    f.floorH = 3.4; f.bayW = 3.0; f.roomDepth = 5.0; f.litShare = 0.35;
    f.win = vec2(0.45, 0.5);
    f.wall = vec3(0.7); f.frame = vec3(0.16, 0.17, 0.18); f.glass = vec3(0.05, 0.06, 0.07);
    f.wallRough = 0.82; f.wallMetal = 0.0; f.glassMetal = 0.08;
    if (st == 0) {        // glass curtain-wall tower: aluminium spandrels, coated glass
      f.floorH = 3.9; f.bayW = 1.5; f.roomDepth = 8.0; f.win = vec2(0.92, 0.8); f.litShare = 0.5;
      f.wall = pick3(seed, vec3(0.56, 0.58, 0.6), vec3(0.2, 0.22, 0.24), vec3(0.7, 0.69, 0.66));
      f.frame = f.wall * 0.8;
      f.glass = pick3(s2, vec3(0.26, 0.38, 0.44), vec3(0.22, 0.27, 0.34), vec3(0.32, 0.3, 0.27));
      f.wallRough = 0.38; f.wallMetal = 0.6; f.glassMetal = 0.35;
    } else if (st == 1) { // post-war office: concrete frame, ribbon windows
      f.floorH = 3.7; f.bayW = 2.8; f.roomDepth = 7.0; f.win = vec2(0.64, 0.5); f.litShare = 0.45;
      f.wall = pick3(seed, vec3(0.72, 0.71, 0.68), vec3(0.6, 0.58, 0.54), vec3(0.8, 0.76, 0.68));
      f.glass = pick3(s2, vec3(0.14, 0.19, 0.22), vec3(0.1, 0.11, 0.12), vec3(0.2, 0.22, 0.2));
      f.glassMetal = 0.2;
    } else if (st == 2) { // Sydney sandstone, timber-framed sash windows
      f.floorH = 4.2; f.bayW = 2.6; f.win = vec2(0.42, 0.55);
      f.wall = pick3(seed, vec3(0.8, 0.66, 0.46), vec3(0.73, 0.59, 0.41), vec3(0.85, 0.73, 0.55));
      f.frame = vec3(0.86, 0.84, 0.78); f.wallRough = 0.78;
    } else if (st == 3) { // face brick
      f.floorH = 3.4; f.bayW = 2.8; f.win = vec2(0.4, 0.5); f.roomDepth = 4.5;
      f.wall = pick3(seed, vec3(0.5, 0.26, 0.18), vec3(0.62, 0.4, 0.28), vec3(0.78, 0.66, 0.52));
      f.frame = vec3(0.9, 0.9, 0.86); f.wallRough = 0.86;
    } else if (st == 4) { // rendered apartments
      f.floorH = 3.0; f.bayW = 3.2; f.win = vec2(0.48, 0.48); f.litShare = 0.4; f.roomDepth = 4.0;
      f.wall = pick3(seed, vec3(0.9, 0.88, 0.83), vec3(0.86, 0.8, 0.7), vec3(0.76, 0.8, 0.78));
      f.frame = vec3(0.3, 0.3, 0.32);
    } else if (st == 5) { // houses and terraces
      f.floorH = 3.0; f.bayW = 3.6; f.win = vec2(0.36, 0.45); f.litShare = 0.3; f.roomDepth = 3.5;
      f.wall = pick3(seed, vec3(0.6, 0.33, 0.24), vec3(0.88, 0.86, 0.8), vec3(0.7, 0.66, 0.58));
      f.frame = vec3(0.92, 0.92, 0.9);
    } else if (st == 6) { // garages, sheds, canopies, steelwork
      f.win = vec2(0.0); f.litShare = 0.0;
      f.wall = pick3(seed, vec3(0.66, 0.64, 0.6), vec3(0.52, 0.5, 0.47), vec3(0.75, 0.72, 0.66));
      f.wallRough = 0.5; f.wallMetal = 0.5;
    } else if (st == 7) { // wharf sheds and warehouses
      f.floorH = 6.0; f.bayW = 5.0; f.win = vec2(0.22, 0.16); f.litShare = 0.2;
      f.wall = pick3(seed, vec3(0.62, 0.6, 0.55), vec3(0.55, 0.52, 0.46), vec3(0.7, 0.68, 0.62));
    } else if (st == 8) { // Sydney Tower turret: gold-anodised panels and gold-tinted glazing
      f.floorH = 3.4; f.bayW = 1.2; f.win = vec2(0.9, 0.55); f.litShare = 0.9;
      f.wall = vec3(0.86, 0.62, 0.26); f.frame = f.wall; f.glass = vec3(0.5, 0.36, 0.14);
      f.wallRough = 0.28; f.wallMetal = 0.95; f.glassMetal = 0.6;
    } else if (st == 9) { // off-white structural concrete with deep fins (Australia Square)
      f.floorH = 3.4; f.bayW = 2.6; f.win = vec2(0.7, 0.58); f.roomDepth = 8.0; f.litShare = 0.5;
      f.wall = vec3(0.8, 0.79, 0.75); f.glass = vec3(0.1, 0.11, 0.12); f.wallRough = 0.88;
    } else {              // glass behind vertical aluminium fins (Quay Quarter Tower)
      f.floorH = 3.9; f.bayW = 1.5; f.win = vec2(0.8, 0.86); f.roomDepth = 9.0; f.litShare = 0.55;
      f.wall = vec3(0.78, 0.79, 0.8); f.frame = vec3(0.7, 0.71, 0.72);
      f.glass = vec3(0.24, 0.32, 0.36); f.wallRough = 0.3; f.wallMetal = 0.8; f.glassMetal = 0.3;
    }
    return f;
  }

  vec3 shadeRoof(int st, float seed, vec2 xy) {
    fRough = 0.9; fMetal = 0.0; fEmissive = vec3(0.0); fWindowMask = 0.0;
    vec3 roof;
    if (st == 5) {
      // houses: terracotta tiles (70 %) or a Colorbond steel roof
      vec3 tile = texture2D(uTerracottaMap, xy / 3.0).rgb;
      bool steel = fract(seed * 3.7) >= 0.7;
      roof = steel ? vec3(0.28, 0.3, 0.31) * (0.8 + 0.4 * tile.g) : tile * vec3(1.05, 0.92, 0.85);
      fRough = steel ? 0.5 : 0.85;
      fMetal = steel ? 0.3 : 0.0;
    } else if (st == 8) {
      roof = vec3(0.86, 0.62, 0.26); fRough = 0.3; fMetal = 0.95;
    } else {
      vec3 concrete = texture2D(uRoofMap, xy / 6.0).rgb;
      // plant rooms and skylights break up large flat roofs
      float plant = step(0.86, hash12(floor(xy / 4.0) + seed * 31.0));
      vec3 tint = st == 0 ? vec3(0.45) : pick3(fract(seed * 5.1), vec3(0.62), vec3(0.72, 0.7, 0.66), vec3(0.5, 0.5, 0.52));
      roof = mix(concrete * tint * 1.4, vec3(0.32, 0.33, 0.34), plant * 0.8);
    }
    return roof;
  }

  // The room behind one window, seen along the view ray. Returns lit radiance (emissive) and,
  // through roomAlbedo, the surface colour for daytime ambient light.
  vec3 interiorRoom(Facade f, vec2 cellF, vec2 cellId, float seed, vec3 rayLocal, float lit, vec3 lamp,
                    out vec3 roomAlbedo) {
    vec3 size = vec3(f.bayW, f.floorH, f.roomDepth);
    vec3 p = vec3(cellF * size.xy, 0.0);
    vec3 d = rayLocal;
    vec3 tWall = vec3(
      (d.x > 0.0 ? size.x - p.x : -p.x) / (abs(d.x) < 1e-4 ? 1e-4 : d.x),
      (d.y > 0.0 ? size.y - p.y : -p.y) / (abs(d.y) < 1e-4 ? 1e-4 : d.y),
      size.z / max(d.z, 1e-4));
    float t = min(tWall.x, min(tWall.y, tWall.z));
    vec3 hit = p + d * t;

    float room = hash12(cellId + seed * 91.0);
    vec3 wallTone = mix(vec3(0.74, 0.71, 0.65), vec3(0.6, 0.64, 0.68), room);
    vec3 floorTone = fract(room * 7.0) < 0.5 ? vec3(0.2, 0.2, 0.22) : vec3(0.34, 0.24, 0.16);
    vec3 albedo;
    if (t == tWall.y) {
      albedo = d.y > 0.0 ? vec3(0.82) : floorTone;               // ceiling / floor
    } else if (t == tWall.z) {
      // back wall: desks, shelves and people at desk height read as a darker band
      float furniture = 1.0 - 0.55 * step(hit.y, 0.95) * step(0.2, fract(hit.x / 1.7 + room));
      albedo = wallTone * furniture;
    } else {
      albedo = wallTone * 0.85;                                   // side walls
    }
    roomAlbedo = albedo;
    // Ceiling lamp in the middle of the room
    vec3 toLamp = vec3(size.x * 0.5, size.y - 0.05, size.z * 0.45) - hit;
    float glow = 1.0 / (1.0 + dot(toLamp, toLamp) * 0.12);
    float panel = (t == tWall.y && d.y > 0.0) ? smoothstep(1.2, 0.4, length(hit.xz - vec2(size.x * 0.5, size.z * 0.45))) : 0.0;
    return lit * lamp * (albedo * glow * 2.4 + panel * 3.0);
  }

  vec3 shadeWall(int st, float seed, vec2 uv, float detail) {
    Facade f = facadeStyle(st, seed);
    vec2 cell = vec2(uv.x / f.bayW, uv.y / f.floorH);
    vec2 id = floor(cell);
    vec2 cf = fract(cell);
    vec2 fw = max(fwidth(cell), vec2(1e-4));
    vec2 winHalf = f.win * 0.5;
    vec2 offs = abs(cf - vec2(0.5, 0.55));
    float outer = smoothstep(winHalf.x + fw.x, winHalf.x - fw.x, offs.x) * smoothstep(winHalf.y + fw.y, winHalf.y - fw.y, offs.y);
    // aluminium / timber frame: a thin band just inside the opening
    vec2 frameW = vec2(0.05 / max(f.bayW, 0.5), 0.05 / max(f.floorH, 0.5)) * 1.6;
    vec2 ih = max(winHalf - frameW, vec2(0.0));
    float glassMask = smoothstep(ih.x + fw.x, ih.x - fw.x, offs.x) * smoothstep(ih.y + fw.y, ih.y - fw.y, offs.y);
    float frameMask = max(outer - glassMask, 0.0);
    float far = smoothstep(0.22, 0.6, max(fw.x, fw.y));

    // per-window and per-floor variation
    float h = hash12(id + seed * 113.0);
    float floorOn = step(0.3, hash12(vec2(id.y, seed * 51.0)));
    float lit = mix(step(0.62, h) * 0.4, 1.0, uNight) * step(hash12(id * 1.37 + seed * 17.0), f.litShare) * floorOn;
    vec3 lamp = mix(vec3(1.0, 0.72, 0.44), vec3(0.82, 0.9, 1.0), step(0.78, hash12(id + 3.1)) * (st <= 1 || st >= 9 ? 1.0 : 0.3));

    // view ray in the wall's frame: x along U, y up, z into the building
    vec3 N = normalize(vFacadeNormal);
    vec3 T = normalize(cross(vec3(0.0, 1.0, 0.0), N));
    vec3 V = normalize(vFacadePos - cameraPosition);
    vec3 rayLocal = vec3(dot(V, T), V.y, -dot(V, N));
    float cosView = clamp(-dot(V, N), 0.0, 1.0);
    float fresnel = pow(1.0 - cosView, 5.0);

    // window-local coordinates (0..1 inside the opening) for blinds and reveal shadow
    vec2 wl = clamp((cf - vec2(0.5, 0.55)) / max(ih, vec2(1e-3)) * 0.5 + 0.5, 0.0, 1.0);
    float blind = step(0.45, fract(h * 5.3)) * (0.15 + 0.7 * fract(h * 11.7));
    float blindMask = step(1.0 - blind, wl.y);
    // wall thickness: the reveal shades the top and one side of the opening
    float reveal = 1.0 - 0.45 * (smoothstep(0.82, 1.0, wl.y) + smoothstep(0.12, 0.0, wl.x)) * (1.0 - far);

    vec3 roomAlbedo;
    vec3 roomLight = interiorRoom(f, cf, id, seed, rayLocal, lit, lamp, roomAlbedo);
    vec3 interior = roomLight + roomAlbedo * uInteriorAmbient;
    vec3 blindCol = vec3(0.78, 0.74, 0.66);
    interior = mix(interior, blindCol * uInteriorAmbient * 1.6 + lit * lamp * 0.9, blindMask);
    // seen through tinted glass; at grazing angles the reflection takes over
    float transmit = (1.0 - fresnel) * 0.7;
    vec3 throughGlass = interior * transmit * reveal;

    // Far away: average the window cell instead of resolving rooms
    float coverage = f.win.x * f.win.y;
    // Averaged over many windows the light is much dimmer than one lit room: most of a cell is
    // frame, blinds and unlit floors. Too high and distant towers glow as uniform white blocks.
    vec3 farLight = lamp * f.litShare * 0.3 * mix(0.15, 1.0, uNight) * coverage + vec3(0.03) * uInteriorAmbient;
    throughGlass = mix(throughGlass * glassMask, farLight, far);

    vec3 wallCol = f.wall * (0.62 + 0.46 * detail) * (1.0 - 0.07 * hash12(vec2(floor(uv.x * 1.5), seed * 7.0)));
    float windowArea = mix(glassMask, coverage, far);
    fWindowMask = windowArea;
    fRough = mix(mix(f.wallRough, 0.4, frameMask), 0.04, windowArea);
    fMetal = mix(mix(f.wallMetal, 0.6, frameMask), f.glassMetal, windowArea);
    fEmissive = throughGlass;
    vec3 surface = mix(wallCol, f.frame, frameMask * (1.0 - far));
    return mix(surface, f.glass, windowArea);
  }
`;

export const facadeFragmentMain = /* glsl */ `
  int facadeType = int(vStyle.y * 16.0);
  float facadeSeed = vStyle.x;
  float facadeLum = dot(texture2D(map, vFacadeUv / 3.0).rgb, vec3(0.333));
  if (vUpness > 0.6) {
    diffuseColor.rgb = shadeRoof(facadeType, facadeSeed, vFacadeUv);
  } else if (vUpness < -0.6) {
    diffuseColor.rgb = vec3(0.3);   // undersides (canopies, turret base)
    fRough = 0.9; fMetal = 0.0; fEmissive = vec3(0.0); fWindowMask = 0.0;
  } else {
    // The style colours are authored as display (sRGB) values; lighting works in linear space.
    diffuseColor.rgb = pow(shadeWall(facadeType, facadeSeed, vFacadeUv, facadeLum), vec3(2.2));
  }
`;

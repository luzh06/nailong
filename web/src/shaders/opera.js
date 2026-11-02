// Opera House shell tiles: 1,056,006 Höganäs tiles in two finishes, glossy white and matte cream,
// laid in chevron "lids" (en.wikipedia.org/wiki/Sydney_Opera_House). UVs are metres in the plane
// of each shell half (scripts/opera.py). The pattern fades to its average where it gets too fine.

export const tileVertex = {
  pars: /* glsl */ `varying vec2 vTileUv;`,
  main: /* glsl */ `vTileUv = uv;`,
};

export const tileFragmentPars = /* glsl */ `
  varying vec2 vTileUv;
  uniform float uFlood;
  float tRough;
`;

export const tileFragmentMain = /* glsl */ `
  const float LID = 1.25;        // width of one precast lid across the shell
  const float STRIPE = 0.36;     // chevron band of glossy or matte tiles
  vec2 tuv = vTileUv;
  float across = fract(tuv.x / LID);
  float chevron = (tuv.y + abs(across - 0.5) * LID * 1.4) / STRIPE;
  float fw = max(fwidth(chevron), 1e-4);
  float band = smoothstep(0.5 - fw, 0.5 + fw, abs(fract(chevron) - 0.5) * 2.0);
  float joint = 1.0 - smoothstep(0.0, fwidth(tuv.x / LID) * 1.5 + 0.004, min(across, 1.0 - across));
  float fine = smoothstep(0.2, 0.6, fw);
  band = mix(band, 0.5, fine);
  joint *= 1.0 - fine;

  vec3 glossy = vec3(0.94, 0.94, 0.91);
  vec3 matte = vec3(0.87, 0.84, 0.76);
  diffuseColor.rgb = mix(glossy, matte, band) * (1.0 - 0.18 * joint);
  tRough = mix(0.12, 0.5, band);
`;

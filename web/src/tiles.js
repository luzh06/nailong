import * as THREE from 'three';
import { TilesRenderer } from '3d-tiles-renderer';
import {
  GLTFExtensionsPlugin,
  GoogleCloudAuthPlugin,
  ReorientationPlugin,
  TileCompressionPlugin,
  TileFlatteningPlugin,
  TilesFadePlugin,
  UnloadTilesPlugin,
} from '3d-tiles-renderer/plugins';

// Google Photorealistic 3D Tiles (Map Tiles API) streamed with 3DTilesRendererJS (Apache-2.0).
// Terms (developers.google.com/maps/documentation/tile/policies): stream only — no prefetching,
// caching or offline use — and show the Google Maps attribution plus the per-tile data credits.

// Our scene heights are above mean sea level (AHD); tile heights are above the WGS84 ellipsoid.
// The geoid sits about this far above the ellipsoid at Sydney; checked against the tiles' own
// harbour surface, which should land at our sea level (y = 0).
export const GEOID_SEPARATION = 22.3;
const SCREEN_SPACE_ERROR = 8;          // lower = sharper and heavier; the library default is 16
const WATER_FLATTEN_REACH = 4.0;       // only photogrammetry within 4 m of the water shape moves

/**
 * @param {{ apiKey: string, origin: { lat: number, lon: number }, renderer: THREE.WebGLRenderer,
 *           camera: THREE.Camera, draco: object }} options
 */
export function createGoogleTiles({ apiKey, origin, renderer, camera, draco }) {
  const tiles = new TilesRenderer();
  tiles.registerPlugin(new GoogleCloudAuthPlugin({ apiToken: apiKey, autoRefreshToken: true }));
  tiles.registerPlugin(new GLTFExtensionsPlugin({ dracoLoader: draco }));
  tiles.registerPlugin(new TileCompressionPlugin());
  tiles.registerPlugin(new UnloadTilesPlugin());
  tiles.registerPlugin(new TilesFadePlugin());
  // Put our scene origin (Opera House, at sea level) at three.js (0, 0, 0) with +Y up
  tiles.registerPlugin(new ReorientationPlugin({
    lat: THREE.MathUtils.degToRad(origin.lat),
    lon: THREE.MathUtils.degToRad(origin.lon),
    height: GEOID_SEPARATION,
    recenter: true,
  }));
  const flattening = new TileFlatteningPlugin();
  tiles.registerPlugin(flattening);

  tiles.errorTarget = SCREEN_SPACE_ERROR;
  tiles.setCamera(camera);
  tiles.setResolutionFromRenderer(camera, renderer);

  // Photogrammetry carries its own baked daylight, so time of day can only tint it. Scene fog
  // (aerial haze) still applies, so distant blocks sit in the same atmosphere as our water and sky.
  const tint = new THREE.Color(1, 1, 1);
  const materials = new Set();
  tiles.addEventListener('load-model', ({ scene }) => {
    scene.traverse((obj) => {
      if (!obj.isMesh) return;
      obj.material.fog = true;
      obj.material.color.copy(tint);
      obj.castShadow = false;
      obj.receiveShadow = false;
      materials.add(obj.material);
    });
  });
  tiles.addEventListener('dispose-model', ({ scene }) => {
    scene.traverse((obj) => { if (obj.isMesh) materials.delete(obj.material); });
  });

  return {
    tiles,
    group: tiles.group,
    /** Press the tiles' noisy water surface down onto `mesh` (our hidden harbour shape). */
    flattenWater(mesh) {
      flattening.addShape(mesh, new THREE.Vector3(0, -1, 0), WATER_FLATTEN_REACH);
    },
    update() {
      tiles.update();
    },
    /** Multiply the baked photogrammetry colour, e.g. warmer at golden hour, dim at dusk. */
    setTint(color) {
      tint.set(color);
      for (const m of materials) m.color.copy(tint);
    },
    setSize(cam, rend) {
      tiles.setResolutionFromRenderer(cam, rend);
    },
    /** "Google Maps" plus the data providers for the tiles currently on screen. */
    attribution() {
      const credits = tiles.getAttributions()
        .filter((a) => a.type === 'string')
        .map((a) => a.value);
      return ['Google Maps', ...new Set(credits)].join(' · ');
    },
  };
}

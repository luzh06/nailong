import * as THREE from 'three';

// Night lighting that is not part of a material: the lamps strung along the bridge's upper
// chords and pylon tops (positions from scene_meta.json). Bright enough for the bloom pass.
export function createBridgeLamps(positions) {
  const geometry = new THREE.SphereGeometry(0.7, 8, 6);
  const material = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.85, 0.6).multiplyScalar(6) });
  const mesh = new THREE.InstancedMesh(geometry, material, positions.length);
  const m = new THREE.Matrix4();
  positions.forEach(([x, y, z], i) => mesh.setMatrixAt(i, m.makeTranslation(x, y, z)));
  mesh.name = 'BridgeLamps';
  mesh.computeBoundingSphere();
  return {
    mesh,
    setNight(amount) {
      mesh.visible = amount > 0.2;
      material.color.setRGB(1.0, 0.85, 0.6).multiplyScalar(6 * amount);
    },
  };
}

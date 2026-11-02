// 测试页用的简单人形占位：胶囊身体 + 球形头 + 两条胳膊。正式版换成队友做好的 GLB 人物模型。
// 只模仿正式人物要有的三个动作：idle（站着）、walk（走）、pose_photo（拍照姿势：举手比划）。
import * as THREE from 'three';

export function makePerson({ name = '', color = 0x6a7a8a, skin = 0xd9b08c, hair = 0x2a211c, height = 1.7 } = {}) {
  const g = new THREE.Group();
  g.name = name;
  const k = height / 1.7;
  const mat = (c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.85 });
  const add = (m, parent = g) => {
    m.castShadow = true;
    m.receiveShadow = true;
    parent.add(m);
    return m;
  };
  const body = add(new THREE.Mesh(new THREE.CapsuleGeometry(0.2 * k, 0.78 * k, 4, 12), mat(color)));
  body.position.y = 0.98 * k;
  const legs = add(new THREE.Mesh(new THREE.CapsuleGeometry(0.15 * k, 0.5 * k, 4, 10), mat(0x2e2c30)));
  legs.position.y = 0.42 * k;
  const head = add(new THREE.Mesh(new THREE.SphereGeometry(0.13 * k, 16, 12), mat(skin)));
  head.position.y = 1.58 * k;
  const hairCap = add(new THREE.Mesh(new THREE.SphereGeometry(0.136 * k, 16, 10, 0, Math.PI * 2, 0, Math.PI * 0.55), mat(hair)), head);
  hairCap.rotation.x = -0.55; // 头发往后梳，露出朝 +z 的脸（人物的正面）
  for (const sx of [-1, 1]) {
    const eye = add(new THREE.Mesh(new THREE.SphereGeometry(0.014 * k, 8, 6), mat(0x1d1a17)), head);
    eye.position.set(sx * 0.045 * k, 0.01 * k, 0.122 * k);
  }
  // 胳膊挂在肩膀上，绕肩转就能摆姿势
  const arms = [-1, 1].map((sx) => {
    const sh = new THREE.Group();
    sh.position.set(sx * 0.25 * k, 1.36 * k, 0);
    g.add(sh);
    const arm = add(new THREE.Mesh(new THREE.CapsuleGeometry(0.055 * k, 0.5 * k, 3, 8), mat(color)), sh);
    arm.position.y = -0.3 * k;
    return sh;
  });
  let pose = 'idle';
  let t = 0;
  g.userData.person = {
    get pose() {
      return pose;
    },
    play(name) {
      pose = name;
    },
    update(dt) {
      t += dt;
      const [l, r] = arms;
      if (pose === 'walk') {
        const s = Math.sin(t * 7) * 0.5;
        l.rotation.set(s, 0, 0.05);
        r.rotation.set(-s, 0, -0.05);
        body.position.y = 0.98 * k + Math.abs(Math.sin(t * 7)) * 0.03;
      } else if (pose === 'pose_photo') {
        // 右手举起比个“耶”，左手叉腰
        r.rotation.set(0, 0, -2.6 + Math.sin(t * 5) * 0.12);
        l.rotation.set(0, 0, 0.7);
        body.position.y = 0.98 * k;
      } else {
        l.rotation.set(0, 0, 0.08);
        r.rotation.set(0, 0, -0.08);
        body.position.y = 0.98 * k + Math.sin(t * 1.6) * 0.006;
      }
    },
  };
  return g;
}

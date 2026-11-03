// Noah · 第一天《拍照的人也在照片里》：上午版任务线（见 此间_悉尼上午版执行方案.md、此间_第一天执行整合文档.md 5.2）。
// 落地 → 咖啡亭找 Maya → 补拍告别相册 3 张（合影、观景望远镜、Sam 的长椅）→ 交给 Maya
// → 快门转场到黄金时段 → 岸边拍黄昏的海 → 地图页“海岸”显影 → 回忆卡 → 未完待续。
// 歌剧院、海港大桥、蓝调时分随时拍到都会另外盖章。
//
// 前景道具和点位由 5060 交付到 data/props/anchors.json；没有这个文件时，用出生点附近的临时点位。
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const INTERACT_RADIUS = 3.2;

const STYLE = /* css */ `
  .q-panel { position: fixed; right: 12px; top: 64px; width: 250px; background: rgba(238,232,220,.94); color: #1d1a17;
    font: 14px/1.6 "Songti SC","Noto Serif SC",serif; padding: 12px 14px; border-radius: 4px; box-shadow: 0 6px 20px rgba(0,0,0,.25); }
  .q-panel h3 { margin: 0 0 6px; font-size: 13px; letter-spacing: .25em; color: #787066; font-weight: 400; }
  .q-panel ul { margin: 0; padding-left: 1.1em; }
  .q-panel li.done { color: #9a9288; text-decoration: line-through; }
  .q-prompt { position: fixed; left: 50%; bottom: 18%; transform: translateX(-50%); background: rgba(29,26,23,.72); color: #f4efe6;
    padding: 6px 14px; border-radius: 3px; font: 14px "Songti SC",serif; letter-spacing: .08em; display: none; }
  .q-dialog { position: fixed; left: 50%; bottom: 6%; transform: translateX(-50%); width: min(760px, 88vw); background: rgba(238,232,220,.97);
    color: #1d1a17; font: 17px/1.7 "Songti SC","Noto Serif SC",serif; padding: 18px 24px 14px; border-radius: 4px; box-shadow: 0 10px 30px rgba(0,0,0,.35); display: none; z-index: 15; }
  .q-dialog .who { font-size: 13px; letter-spacing: .3em; color: #b23428; margin-bottom: 4px; }
  .q-dialog .opts { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
  .q-dialog button { text-align: left; font: inherit; font-size: 15px; background: transparent; border: 1px solid #1d1a17; color: #1d1a17; padding: 6px 12px; border-radius: 3px; cursor: pointer; }
  .q-dialog button:hover { background: #1d1a17; color: #eee8dc; }
  .q-dialog .next { font-size: 12px; color: #787066; text-align: right; margin-top: 6px; }
  .q-toast { position: fixed; left: 50%; top: 12%; transform: translateX(-50%); display: flex; align-items: center; gap: 14px; background: rgba(238,232,220,.95);
    color: #1d1a17; font: 15px "Songti SC",serif; padding: 10px 18px; border-radius: 4px; box-shadow: 0 8px 24px rgba(0,0,0,.3); opacity: 0; transition: opacity .4s; pointer-events: none; z-index: 16; }
  .q-toast.show { opacity: 1; }
  .q-toast canvas { width: 64px; height: 64px; }
  .q-iris { position: fixed; inset: 0; background: #000; opacity: 0; pointer-events: none; transition: opacity .7s; z-index: 18; }
  .q-iris.on { opacity: 1; }
  .q-map { position: fixed; inset: 0; display: none; place-items: center; background: rgba(20,16,12,.6); z-index: 17; }
  .q-map.on { display: grid; }
  .q-map .page { width: min(720px, 90vw); background: #eee8dc; color: #1d1a17; font-family: "Songti SC","Noto Serif SC",serif; padding: 34px 40px 28px;
    border-radius: 4px; box-shadow: 0 20px 60px rgba(0,0,0,.45); text-align: center; }
  .q-map .page h2 { margin: 0; font-size: 28px; letter-spacing: .4em; animation: q-develop 3s ease-out both; }
  .q-map .page p { color: #787066; letter-spacing: .1em; }
  .q-map .stamps { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin: 18px 0; }
  .q-map .stamps canvas { width: 92px; height: 92px; animation: q-develop 2s ease-out both; }
  .q-map .tbc { margin-top: 18px; font-size: 15px; color: #1d1a17; letter-spacing: .2em; }
  .q-map button { font: inherit; font-size: 15px; margin: 8px 6px 0; padding: 7px 18px; border-radius: 3px; cursor: pointer; border: 1px solid #1d1a17; background: transparent; }
  .q-map button.primary { background: #b23428; border-color: #b23428; color: #fff; }
  @keyframes q-develop { from { opacity: 0; filter: blur(3px) sepia(1); } to { opacity: 1; filter: none; } }
`;

function el(tag, cls, html = '') {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  e.innerHTML = html;
  document.body.appendChild(e);
  return e;
}

/** 出生点附近的临时点位（5060 的 anchors.json 到了就不用这些） */
function defaultAnchors(meta, player) {
  const spawn = new THREE.Vector3(...meta.views.spawn.pos);
  const look = new THREE.Vector3(...meta.views.spawn.look);
  const d = new THREE.Vector3(look.x - spawn.x, 0, look.z - spawn.z).normalize();
  const side = new THREE.Vector3(-d.z, 0, d.x);
  const at = (fwd, right, lift = 0) => {
    // 往回找一个在步行区里的位置
    for (let k = 1; k >= 0.2; k -= 0.1) {
      const x = spawn.x + d.x * fwd * k + side.x * right * k;
      const z = spawn.z + d.z * fwd * k + side.z * right * k;
      if (player.insideWalkZone(x, z)) return [x, player.groundHeight(x, z) + lift, z];
    }
    return [spawn.x, player.groundHeight(spawn.x, spawn.z) + lift, spawn.z];
  };
  return {
    anchors: {
      ANCHOR_spawn: at(0, 0),
      ANCHOR_npc_maya: at(9, -6, 1.0),
      ANCHOR_photo_cafe: at(9, -6, 1.3),
      ANCHOR_photo_landmark: at(13, 1, 1.2),
      ANCHOR_photo_bench: at(11, 6, 0.5),
      // 海港中央、离水面 8 米：贴着水面的点会被岸边地形挡住
      ANCHOR_photo_shore: [spawn.x + d.x * 300, 8, spawn.z + d.z * 300],
    },
    props: [],
  };
}

const FAR_ANCHORS = {
  ANCHOR_photo_opera: [0, 30, 0],
  ANCHOR_photo_bridge: [-401, 70, -513],
  ANCHOR_photo_bluehour: [-401, 70, -513],
};

export async function loadNoahAnchors(meta, player, scene) {
  let data = null;
  try {
    const res = await fetch('./data/props/anchors.json');
    if (res.ok) data = await res.json();
  } catch { /* 没有交付文件就用临时点位 */ }
  const usingProps = !!data;
  if (!data) data = defaultAnchors(meta, player);
  data.anchors = { ...FAR_ANCHORS, ...data.anchors };

  // 5060 的前景道具：{ props: [{ file, pos: [x,y,z], rotY }] }，坐标已是网页坐标
  if (data.props?.length) {
    const loader = new GLTFLoader();
    await Promise.all(data.props.map(async (p) => {
      try {
        const g = await loader.loadAsync(`./data/props/${p.file}`);
        g.scene.position.set(...p.pos);
        g.scene.rotation.y = p.rotY ?? 0;
        if (p.scale) g.scene.scale.setScalar(p.scale);
        g.scene.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
        scene.add(g.scene);
      } catch (err) {
        console.warn('前景道具载入失败', p.file, err);
      }
    }));
  }
  return { data, usingProps };
}

export class NoahDay1 {
  constructor({ photo, player, scene, anchors, setTime, getTime }) {
    this.photo = photo;
    this.player = player;
    this.setTime = setTime;
    this.getTime = getTime;
    this.actions = new Set();
    this.stamps = new Map();     // spot id -> stamp canvas
    this.step = 'intro';
    this.choice = null;
    this.blocking = false;       // 对白和地图页打开时，人物不走

    const a = anchors.anchors;
    const v = (k) => new THREE.Vector3(...a[k]);
    this.points = [
      { id: 'maya', pos: v('ANCHOR_npc_maya'), label: '和 Maya 说话' },
      { id: 'landmark', pos: v('ANCHOR_photo_landmark'), label: '看看观景望远镜旁的指示牌' },
      { id: 'bench', pos: v('ANCHOR_photo_bench'), label: '读长椅上的小铜牌' },
    ];
    // 交互点的光圈：只在游戏里看得到，照片里不出现
    for (const p of this.points) {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.035, 8, 48), new THREE.MeshBasicMaterial({ color: 0xffe9b0, transparent: true, opacity: 0.85 }));
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(p.pos.x, player.groundHeight(p.pos.x, p.pos.z) + 0.06, p.pos.z);
      ring.userData.hideInPhoto = true;
      scene.add(ring);
      p.ring = ring;
    }

    const style = document.createElement('style');
    style.textContent = STYLE;
    document.head.appendChild(style);
    this.ui = {
      panel: el('aside', 'q-panel'),
      prompt: el('div', 'q-prompt'),
      dialog: el('div', 'q-dialog'),
      toast: el('div', 'q-toast'),
      iris: el('div', 'q-iris'),
      map: el('div', 'q-map'),
    };
    this.ui.panel.dataset.hud = '';
    this.ui.prompt.dataset.hud = '';

    window.addEventListener('keydown', (e) => {
      if (e.code === 'KeyE' && !this.photo.active && !this.blocking && this.near) this.interact(this.near.id);
    });
    photo.addEventListener('stamp', (e) => this.onStamp(e.detail));
    photo.addEventListener('stampwait', (e) => this.toast(this.waitText(e.detail.spot)));
    photo.addEventListener('consentwait', () => this.toast('先问一声 Maya：可以拍吗？'));
    photo.addEventListener('error', (e) => this.toast(e.detail.message));

    this.render();
    setTimeout(() => this.toast('三次日落之前，让你的旅行页显影。'), 800);
  }

  actionDone = (action) => this.actions.has(action);
  getChoice = () => this.choice;

  waitText(spot) {
    const map = { sy_cafe: '先和 Maya 说好，再拍合影', sy_landmark: '先看看望远镜旁的指示牌', sy_bench: '先读一读长椅上的铜牌', sy_shore: '等黄昏再来' };
    return map[spot?.id] ?? '这张先记下，剧情走到那一步再盖章';
  }

  // ---- 每帧：找最近的交互点 ----
  update(time) {
    let near = null;
    const p = this.player.pos;
    for (const pt of this.points) {
      pt.ring.rotation.z = time * 0.6;
      const dist = Math.hypot(pt.pos.x - p.x, pt.pos.z - p.z);
      if (dist < INTERACT_RADIUS && (!near || dist < near.dist)) near = { ...pt, dist };
    }
    this.near = near;
    const show = near && !this.blocking && !this.photo.active;
    this.ui.prompt.style.display = show ? 'block' : 'none';
    if (show) this.ui.prompt.textContent = `E  ${near.label}`;
  }

  interact(id) {
    if (id === 'maya') {
      if (this.step === 'intro') this.talkMayaFirst();
      else if (this.step === 'album' && this.albumDone()) this.talkMayaDeliver();
      else if (this.step === 'album') this.say([['Maya', '还差几张呢。合影、观景望远镜那边、Sam 的长椅，你慢慢拍。']]);
      else this.say([['Maya', '去岸边吧，今天的晚霞应该会很好看。']]);
    } else if (id === 'landmark') {
      this.actions.add('meet_tess');
      this.say([
        ['指示牌', '「从这里望过去，是对岸的歌剧院。」下面贴着一张手写卡片：“步道照片第 12 号，Tess 拍。”'],
        ['Noah', '把望远镜和远处的帆一起拍进去吧。'],
      ]);
    } else if (id === 'bench') {
      this.actions.add('bench_story');
      this.say([
        ['铜牌', '「给每个在这里等渡轮的人。」'],
        ['Noah', 'Sam 每天下班都坐在这儿。就拍这张椅子，空着的那种。'],
      ]);
    }
    this.render();
  }

  talkMayaFirst() {
    this.say([
      ['Noah', 'Maya！今天店里怎么这么安静……等等，你认识我吗？'],
      ['Maya', '当然认识，每次拍合照的都是你。正好，Sam 下周就搬走了，告别相册还缺三张。'],
      ['Noah', '交给我。合影、观景望远镜那边，还有他最常坐的那张长椅，对吧？'],
    ], [
      { text: '“大家看这边——可以拍吗？”', run: () => { this.actions.add('ask_group'); this.photo.setConsent?.('maya'); this.toast('Maya 点头：“拍吧，拍好看点。”'); } },
    ], () => { this.step = 'album'; this.render(); });
  }

  albumDone() {
    return ['sy_cafe', 'sy_landmark', 'sy_bench'].every((id) => this.stamps.has(id));
  }

  talkMayaDeliver() {
    this.say([
      ['Maya', '每一张都很好。……不过 Noah，你总在替别人留纪念。这次也留一张自己的吧。'],
    ], [
      { text: '“哈，我？我在镜头后面就好。”', run: () => { this.choice = '把自己留在了镜头后面'; } },
      { text: '“……那等黄昏，我也站进去一次。”', run: () => { this.choice = '答应站进照片里一次'; } },
    ], async () => {
      this.actions.add('deliver');
      this.step = 'shore';
      await this.shutterTo('golden');
      this.toast('黄昏了。去岸边，拍下海港。');
      this.render();
    });
  }

  async shutterTo(time) {
    this.blocking = true;
    this.ui.iris.classList.add('on');
    await new Promise((r) => setTimeout(r, 750));
    await this.setTime(time);
    await new Promise((r) => setTimeout(r, 250));
    this.ui.iris.classList.remove('on');
    this.blocking = false;
  }

  // 集章簿存在浏览器里、跨刷新保留，所以这里不看 first，只看这一趟旅程有没有盖过
  onStamp({ spot, canvas }) {
    if (this.stamps.has(spot.id)) return;
    this.stamps.set(spot.id, canvas);
    this.toast(`盖章：${spot.label}`, canvas);
    if (this.step === 'album' && this.albumDone()) this.toast('三张都拍好了。回咖啡亭交给 Maya。');
    if (spot.id === 'sy_shore' && this.step === 'shore') {
      this.step = 'done';
      setTimeout(() => this.showMapPage(), 1600);
    }
    this.render();
  }

  showMapPage() {
    this.blocking = true;
    const m = this.ui.map;
    m.innerHTML = `<div class="page">
      <p>第一次日落。你的旅行页，显影了一角。</p>
      <h2>海　岸</h2>
      <div class="stamps"></div>
      <p>${this.choice ? `今天，你${this.choice}。` : ''}</p>
      <div class="tbc">第二天，这一页还没有显影。未完待续</div>
      <div><button class="primary" data-a="card">做一张回忆卡</button><button data-a="stay">再逛逛（歌剧院、大桥、蓝调时分）</button></div>
    </div>`;
    const box = m.querySelector('.stamps');
    for (const c of this.stamps.values()) {
      const copy = document.createElement('canvas');
      copy.width = c.width;
      copy.height = c.height;
      copy.getContext('2d').drawImage(c, 0, 0);
      box.appendChild(copy);
    }
    m.classList.add('on');
    m.onclick = (e) => {
      const a = e.target.closest('[data-a]')?.dataset.a;
      if (!a) return;
      m.classList.remove('on');
      this.blocking = false;
      if (a === 'card') this.photo.album.open();
    };
  }

  // ---- 对白 ----
  say(lines, options = null, onEnd = null) {
    this.blocking = true;
    const d = this.ui.dialog;
    let i = 0;
    const show = () => {
      const [who, text] = lines[i];
      const last = i === lines.length - 1;
      d.innerHTML = `<div class="who">${who}</div><div>${text}</div>`;
      if (last && options) {
        const box = document.createElement('div');
        box.className = 'opts';
        for (const o of options) {
          const b = document.createElement('button');
          b.textContent = o.text;
          b.onclick = () => { o.run?.(); close(); };
          box.appendChild(b);
        }
        d.appendChild(box);
      } else {
        d.insertAdjacentHTML('beforeend', '<div class="next">点击继续</div>');
      }
    };
    const close = () => {
      d.style.display = 'none';
      d.onclick = null;
      this.blocking = false;
      onEnd?.();
      this.render();
    };
    d.onclick = (e) => {
      if (e.target.closest('button')) return;
      if (i === lines.length - 1) { if (!options) close(); return; }
      i += 1;
      show();
    };
    d.style.display = 'block';
    show();
  }

  toast(text, canvas = null) {
    const t = this.ui.toast;
    t.replaceChildren();
    if (canvas) {
      const c = document.createElement('canvas');
      c.width = canvas.width;
      c.height = canvas.height;
      c.getContext('2d').drawImage(canvas, 0, 0);
      t.appendChild(c);
    }
    t.appendChild(document.createTextNode(text));
    t.classList.add('show');
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => t.classList.remove('show'), 3200);
  }

  // ---- 书签上的任务清单 ----
  render() {
    const done = (id) => this.stamps.has(id);
    const li = (ok, text) => `<li class="${ok ? 'done' : ''}">${text}</li>`;
    let items = '';
    if (this.step === 'intro') items = li(false, '去步道边的咖啡亭找 Maya');
    else if (this.step === 'album') {
      items = li(done('sy_cafe'), '咖啡亭前的合影（C 拿相机）')
        + li(done('sy_landmark'), '观景望远镜，连远处的歌剧院一起')
        + li(done('sy_bench'), 'Sam 的长椅')
        + (this.albumDone() ? li(false, '回咖啡亭交给 Maya') : '');
    } else if (this.step === 'shore') items = li(false, '在岸边拍下黄昏的海');
    else items = li(true, '第一天的旅行页显影了');
    const extra = ['sy_opera', 'sy_bridge', 'sy_bluehour'].filter(done).length;
    this.ui.panel.innerHTML = `<h3>书签 · 第一天</h3><ul>${items}</ul>`
      + `<h3 style="margin-top:10px">远方的章 ${extra}/3</h3><ul>${li(done('sy_opera'), '歌剧院（135mm）')}${li(done('sy_bridge'), '海港大桥')}${li(done('sy_bluehour'), '蓝调时分')}</ul>`;
  }
}

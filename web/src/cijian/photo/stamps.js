// 纪念章：用 Canvas 程序画，全部是虚构图案，不用任何真章或品牌。
//   station：东京，日本车站纪念章的样子（圆形双圈、上沿弧形小字、中间线描、下面一条站名带）
//   trail  ：悉尼，海岸步道标记牌的样子（圆角长方形、编号牌、线描、波浪线和箭头、地点名）
// 印泥斑驳：先用实色画好，再用两层随机噪声擦掉一部分，像真的盖在纸上。
// 同一个打卡点每次画出来都一样（随机数用 id 做种子）。

const RED = [178, 52, 40];
const SERIF = '"Source Han Serif SC","Noto Serif SC","Songti SC","STSong",serif';

/**
 * @param {object} spec
 * @param {'station'|'trail'} spec.style
 * @param {string} spec.label   主名字（站名带 / 牌子下方）
 * @param {string} [spec.sub]   上沿小字（station）或牌子顶部小字（trail）
 * @param {string} [spec.code]  编号，比如 T1、S2
 * @param {string} spec.icon    线描图案名，见 ICONS
 * @param {string} [spec.id]    随机种子
 * @param {object} [o]
 * @param {number} [o.size]     画布边长（像素）
 * @param {number[]} [o.ink]    印泥颜色
 * @param {number} [o.wear]     斑驳程度 0—1
 * @returns {HTMLCanvasElement}
 */
export function drawStamp(spec, { size = 360, ink = RED, wear = 0.55 } = {}) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const g = c.getContext('2d');
  const rand = mulberry32(hash(spec.id ?? spec.label));
  const col = `rgb(${ink.join(',')})`;
  g.fillStyle = g.strokeStyle = col;
  g.lineCap = g.lineJoin = 'round';
  (spec.style === 'trail' ? trail : station)(g, size, spec);
  mottle(g, size, rand, wear);
  return c;
}

// ---- 东京：车站纪念章 ----
function station(g, S, spec) {
  const cx = S / 2;
  const cy = S / 2;
  const R = S * 0.47;
  g.lineWidth = S * 0.03;
  circle(g, cx, cy, R);
  g.lineWidth = S * 0.008;
  circle(g, cx, cy, R * 0.9);
  // 站名带：一条横贯下部的实心带，字是镂空的
  const bandY = cy + R * 0.34;
  const bandH = R * 0.36;
  const half = Math.sqrt(Math.max(0, (R * 0.9) ** 2 - (bandY + bandH - cy) ** 2));
  g.save();
  g.beginPath();
  g.arc(cx, cy, R * 0.9, 0, Math.PI * 2);
  g.clip();
  g.fillRect(cx - R, bandY, R * 2, bandH);
  g.globalCompositeOperation = 'destination-out';
  fitText(g, spec.label, cx, bandY + bandH * 0.52, half * 2 * 0.8, bandH * 0.62, 900);
  g.restore();
  // 编号放在站名带下面
  if (spec.code) {
    g.font = `700 ${S * 0.05}px ${SERIF}`;
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText(spec.code, cx, bandY + bandH + R * 0.12);
  }
  // 上沿弧形小字
  if (spec.sub) arcText(g, spec.sub, cx, cy, R * 0.76, S * 0.055, -Math.PI / 2, 0.11);
  // 中间线描
  g.lineWidth = S * 0.016;
  ICONS[spec.icon]?.(g, cx, cy - R * 0.1, R * 0.5);
}

// ---- 悉尼：海岸步道标记牌 ----
function trail(g, S, spec) {
  const w = S * 0.8;
  const h = S * 0.9;
  const x = (S - w) / 2;
  const y = (S - h) / 2;
  g.lineWidth = S * 0.028;
  g.beginPath();
  g.roundRect(x, y, w, h, S * 0.09);
  g.stroke();
  g.lineWidth = S * 0.008;
  g.beginPath();
  g.roundRect(x + S * 0.035, y + S * 0.035, w - S * 0.07, h - S * 0.07, S * 0.065);
  g.stroke();
  // 顶部：编号牌（实心，字镂空）+ 一行小字
  const top = y + S * 0.075;
  if (spec.code) {
    const pw = S * 0.2;
    const ph = S * 0.1;
    g.beginPath();
    g.roundRect(x + S * 0.075, top, pw, ph, ph / 2);
    g.fill();
    g.save();
    g.globalCompositeOperation = 'destination-out';
    fitText(g, spec.code, x + S * 0.075 + pw / 2, top + ph * 0.54, pw * 0.8, ph * 0.72, 900);
    g.restore();
  }
  if (spec.sub) {
    g.textAlign = 'left';
    fitText(g, spec.sub, x + S * 0.32 + (w - S * 0.4) / 2, top + S * 0.054, w - S * 0.42, S * 0.05, 600);
  }
  // 中间线描
  g.lineWidth = S * 0.016;
  ICONS[spec.icon]?.(g, S / 2, y + h * 0.43, S * 0.23);
  // 波浪线 + 箭头
  const wy = y + h * 0.69;
  g.lineWidth = S * 0.012;
  wave(g, x + S * 0.08, wy, w * 0.62, S * 0.022, 3);
  const ax = x + w - S * 0.17;
  g.lineWidth = S * 0.016;
  g.beginPath();
  g.moveTo(ax, wy);
  g.lineTo(ax + S * 0.09, wy);
  g.moveTo(ax + S * 0.06, wy - S * 0.03);
  g.lineTo(ax + S * 0.09, wy);
  g.lineTo(ax + S * 0.06, wy + S * 0.03);
  g.stroke();
  // 地点名
  fitText(g, spec.label, S / 2, y + h * 0.85, w * 0.82, S * 0.1, 900);
}

// ---- 线描图案：都在 (cx, cy) 为中心、半宽约 r 的方框里 ----
const ICONS = {
  // 唱片和风铃（遥的店）
  record(g, cx, cy, r) {
    circle(g, cx - r * 0.25, cy + r * 0.1, r * 0.62);
    g.save();
    g.lineWidth *= 0.5;
    for (const k of [0.48, 0.36]) circle(g, cx - r * 0.25, cy + r * 0.1, r * k);
    g.restore();
    dot(g, cx - r * 0.25, cy + r * 0.1, r * 0.1);
    // 风铃：从上方挂下来，铃身是半球，下面一张短册
    const bx = cx + r * 0.62;
    line(g, bx, cy - r * 0.95, bx, cy - r * 0.62);
    g.beginPath();
    g.arc(bx, cy - r * 0.38, r * 0.24, Math.PI, 0);
    g.closePath();
    g.stroke();
    line(g, bx, cy - r * 0.38, bx, cy + r * 0.12);
    g.strokeRect(bx - r * 0.1, cy + r * 0.12, r * 0.2, r * 0.5);
  },
  // 咖啡杯（喫茶）
  cup(g, cx, cy, r) {
    g.beginPath();
    g.moveTo(cx - r * 0.55, cy - r * 0.1);
    g.lineTo(cx - r * 0.45, cy + r * 0.5);
    g.quadraticCurveTo(cx, cy + r * 0.62, cx + r * 0.45, cy + r * 0.5);
    g.lineTo(cx + r * 0.55, cy - r * 0.1);
    g.closePath();
    g.stroke();
    g.beginPath();
    g.ellipse(cx + r * 0.66, cy + r * 0.15, r * 0.18, r * 0.2, 0, -Math.PI / 2, Math.PI / 2);
    g.stroke();
    g.beginPath();
    g.ellipse(cx, cy + r * 0.62, r * 0.85, r * 0.12, 0, 0, Math.PI);
    g.stroke();
    for (const dx of [-0.22, 0.05, 0.3]) {
      g.beginPath();
      g.moveTo(cx + r * dx, cy - r * 0.25);
      g.bezierCurveTo(cx + r * (dx - 0.15), cy - r * 0.45, cx + r * (dx + 0.15), cy - r * 0.6, cx + r * dx, cy - r * 0.85);
      g.stroke();
    }
  },
  // 菜筐和萝卜（八百政）
  veg(g, cx, cy, r) {
    g.strokeRect(cx - r * 0.75, cy + r * 0.05, r * 1.5, r * 0.55);
    line(g, cx - r * 0.75, cy + r * 0.32, cx + r * 0.75, cy + r * 0.32);
    for (const dx of [-0.45, -0.05]) circle(g, cx + r * dx, cy - r * 0.12, r * 0.2);
    // 萝卜斜靠着
    g.beginPath();
    g.moveTo(cx + r * 0.25, cy + r * 0.02);
    g.quadraticCurveTo(cx + r * 0.42, cy - r * 0.5, cx + r * 0.78, cy - r * 0.62);
    g.quadraticCurveTo(cx + r * 0.62, cy - r * 0.25, cx + r * 0.42, cy + r * 0.04);
    g.stroke();
    for (const a of [-0.4, 0, 0.4]) {
      g.beginPath();
      g.moveTo(cx + r * 0.78, cy - r * 0.62);
      g.quadraticCurveTo(cx + r * (0.9 + a * 0.2), cy - r * (0.85 + a * 0.1), cx + r * (0.75 + a * 0.5), cy - r * 1.0);
      g.stroke();
    }
  },
  // 台阶和落日，台阶上一只猫
  stairs(g, cx, cy, r) {
    line(g, cx - r * 0.95, cy - r * 0.05, cx + r * 0.95, cy - r * 0.05);
    g.beginPath();
    g.arc(cx + r * 0.1, cy - r * 0.05, r * 0.38, Math.PI, 0);
    g.stroke();
    for (let i = 0; i < 5; i++) {
      const a = Math.PI + ((i + 1) / 6) * Math.PI;
      line(g, cx + r * 0.1 + Math.cos(a) * r * 0.5, cy - r * 0.05 + Math.sin(a) * r * 0.5,
        cx + r * 0.1 + Math.cos(a) * r * 0.68, cy - r * 0.05 + Math.sin(a) * r * 0.68);
    }
    g.beginPath();
    let x = cx - r * 0.95;
    let y = cy + r * 0.12;
    g.moveTo(x, y);
    for (let i = 0; i < 5; i++) {
      x += r * 0.38;
      g.lineTo(x, y);
      y += r * 0.15;
      g.lineTo(x, y);
    }
    g.stroke();
    // 猫：坐着的剪影
    const kx = cx - r * 0.6;
    const ky = cy + r * 0.12;
    g.beginPath();
    g.ellipse(kx, ky - r * 0.14, r * 0.1, r * 0.14, 0, 0, Math.PI * 2);
    g.fill();
    circle(g, kx, ky - r * 0.33, r * 0.07, true);
    g.beginPath();
    g.moveTo(kx - r * 0.06, ky - r * 0.37);
    g.lineTo(kx - r * 0.05, ky - r * 0.46);
    g.lineTo(kx - r * 0.01, ky - r * 0.39);
    g.moveTo(kx + r * 0.06, ky - r * 0.37);
    g.lineTo(kx + r * 0.05, ky - r * 0.46);
    g.lineTo(kx + r * 0.01, ky - r * 0.39);
    g.fill();
  },
  // 大提灯（虚构，灯面不写字）
  lantern(g, cx, cy, r) {
    line(g, cx - r * 0.9, cy - r * 0.92, cx + r * 0.9, cy - r * 0.92);
    g.fillRect(cx - r * 0.36, cy - r * 0.86, r * 0.72, r * 0.14);
    g.fillRect(cx - r * 0.36, cy + r * 0.72, r * 0.72, r * 0.14);
    g.beginPath();
    g.ellipse(cx, cy - r * 0.07, r * 0.62, r * 0.8, 0, 0, Math.PI * 2);
    g.stroke();
    g.save();
    g.lineWidth *= 0.5;
    for (let i = 1; i < 6; i++) {
      const yy = cy - r * 0.07 + (i / 6 - 0.5) * r * 1.5;
      const hw = r * 0.62 * Math.sqrt(1 - ((yy - (cy - r * 0.07)) / (r * 0.8)) ** 2);
      line(g, cx - hw, yy, cx + hw, yy);
    }
    g.restore();
  },
  // 五重塔
  pagoda(g, cx, cy, r) {
    line(g, cx, cy - r * 1.02, cx, cy - r * 0.72);
    for (let i = 0; i < 5; i++) {
      const y = cy - r * 0.68 + i * r * 0.32;
      const hw = r * (0.42 + i * 0.1);
      g.beginPath();
      g.moveTo(cx - hw, y + r * 0.04);
      g.quadraticCurveTo(cx - hw * 0.6, y + r * 0.1, cx, y - r * 0.04);
      g.quadraticCurveTo(cx + hw * 0.6, y + r * 0.1, cx + hw, y + r * 0.04);
      g.stroke();
      const bw = hw * 0.55;
      g.strokeRect(cx - bw, y + r * 0.08, bw * 2, r * 0.2);
    }
    line(g, cx - r * 0.9, cy + r * 0.98, cx + r * 0.9, cy + r * 0.98);
  },
  // 电线杆和电线，线上一只鸟
  poles(g, cx, cy, r) {
    for (const [px, k] of [[-0.55, 1], [0.6, 0.78]]) {
      const x = cx + r * px;
      line(g, x, cy - r * 0.95 * k, x, cy + r * 0.95);
      line(g, x - r * 0.24 * k, cy - r * 0.72 * k, x + r * 0.24 * k, cy - r * 0.72 * k);
    }
    g.save();
    g.lineWidth *= 0.55;
    for (const dy of [0, 0.14]) {
      g.beginPath();
      g.moveTo(cx - r * 0.79, cy - r * (0.72 - dy));
      g.quadraticCurveTo(cx, cy - r * (0.3 - dy), cx + r * 0.79, cy - r * (0.56 - dy));
      g.stroke();
    }
    g.restore();
    g.beginPath();
    g.ellipse(cx + r * 0.05, cy - r * 0.58, r * 0.08, r * 0.05, 0, 0, Math.PI * 2);
    g.fill();
    circle(g, cx + r * 0.14, cy - r * 0.64, r * 0.04, true);
  },
  // 悉尼：咖啡店雨棚和杯子
  cafe(g, cx, cy, r) {
    g.beginPath();
    g.moveTo(cx - r * 0.9, cy - r * 0.45);
    g.lineTo(cx - r * 0.75, cy - r * 0.85);
    g.lineTo(cx + r * 0.75, cy - r * 0.85);
    g.lineTo(cx + r * 0.9, cy - r * 0.45);
    g.closePath();
    g.stroke();
    for (let i = 0; i < 5; i++) {
      const x = cx - r * 0.9 + (i + 0.5) * r * 0.36;
      g.beginPath();
      g.arc(x, cy - r * 0.45, r * 0.18, 0, Math.PI);
      g.stroke();
    }
    ICONS.cup(g, cx, cy + r * 0.35, r * 0.6);
  },
  // 观景望远镜（步道地标）
  marker(g, cx, cy, r) {
    g.save();
    g.translate(cx, cy - r * 0.4);
    g.rotate(-0.25);
    g.strokeRect(-r * 0.5, -r * 0.2, r * 0.8, r * 0.4);
    g.strokeRect(r * 0.3, -r * 0.26, r * 0.22, r * 0.52);
    g.strokeRect(-r * 0.7, -r * 0.14, r * 0.2, r * 0.28);
    g.restore();
    line(g, cx, cy - r * 0.2, cx, cy + r * 0.7);
    line(g, cx - r * 0.4, cy + r * 0.7, cx + r * 0.4, cy + r * 0.7);
    line(g, cx - r * 0.2, cy + r * 0.25, cx + r * 0.2, cy + r * 0.25);
  },
  // 长椅：斜侧面看，靠背三根板条、座面两根、铸铁扶手
  bench(g, cx, cy, r) {
    const dx = r * 0.32;
    const dy = -r * 0.22;
    const L = cx - r * 0.85;
    const R = cx + r * 0.6;
    const seat = cy + r * 0.2;
    for (const k of [0, 0.5]) line(g, L + dx * k, seat + dy * k, R + dx * k, seat + dy * k);
    for (const k of [0, 1, 2]) line(g, L + dx, seat + dy - r * (0.28 + k * 0.2), R + dx, seat + dy - r * (0.28 + k * 0.2));
    for (const x of [L, R]) {
      line(g, x + dx, seat + dy - r * 0.8, x + dx, seat + dy + r * 0.45);
      line(g, x, seat, x, seat + r * 0.55);
      g.beginPath();
      g.moveTo(x, seat - r * 0.02);
      g.quadraticCurveTo(x + dx * 0.2, seat - r * 0.35, x + dx, seat + dy - r * 0.3);
      g.stroke();
    }
    g.save();
    g.lineWidth *= 0.6;
    line(g, cx - r * 1.0, seat + r * 0.6, cx + r * 1.0, seat + r * 0.6);
    g.restore();
  },
  // 海上落日
  shore(g, cx, cy, r) {
    g.beginPath();
    g.arc(cx, cy + r * 0.05, r * 0.5, Math.PI, 0);
    g.closePath();
    g.stroke();
    for (let i = 0; i < 7; i++) {
      const a = Math.PI + ((i + 1) / 8) * Math.PI;
      line(g, cx + Math.cos(a) * r * 0.62, cy + r * 0.05 + Math.sin(a) * r * 0.62,
        cx + Math.cos(a) * r * 0.82, cy + r * 0.05 + Math.sin(a) * r * 0.82);
    }
    for (let i = 0; i < 3; i++) wave(g, cx - r * (0.9 - i * 0.15), cy + r * (0.28 + i * 0.22), r * (1.8 - i * 0.3), r * 0.06, 4 - i);
  },
  // 帆形屋顶（远景剧院，线描示意）
  opera(g, cx, cy, r) {
    const base = cy + r * 0.45;
    line(g, cx - r * 0.95, base, cx + r * 0.95, base);
    g.strokeRect(cx - r * 0.8, base, r * 1.6, r * 0.18);
    const sails = [[-0.7, 0.55, 0.65], [-0.35, 0.6, 0.85], [0.05, 0.5, 0.7], [0.35, 0.45, 0.55]];
    for (const [x0, w, hgt] of sails) {
      g.beginPath();
      g.moveTo(cx + r * x0, base);
      g.quadraticCurveTo(cx + r * (x0 + w * 0.15), base - r * hgt * 1.1, cx + r * (x0 + w), base - r * hgt);
      g.quadraticCurveTo(cx + r * (x0 + w * 0.8), base - r * hgt * 0.35, cx + r * (x0 + w * 0.7), base);
      g.stroke();
    }
  },
  // 拱桥
  bridge(g, cx, cy, r) {
    const deck = cy + r * 0.2;
    line(g, cx - r * 1.0, deck, cx + r * 1.0, deck);
    g.beginPath();
    g.moveTo(cx - r * 0.72, deck + r * 0.1);
    g.quadraticCurveTo(cx, cy - r * 1.05, cx + r * 0.72, deck + r * 0.1);
    g.stroke();
    g.beginPath();
    g.moveTo(cx - r * 0.72, deck + r * 0.1);
    g.quadraticCurveTo(cx, cy - r * 0.7, cx + r * 0.72, deck + r * 0.1);
    g.stroke();
    g.save();
    g.lineWidth *= 0.5;
    for (let i = 1; i < 8; i++) {
      const t = i / 8;
      const x = cx - r * 0.72 + t * r * 1.44;
      const yTop = (1 - t) ** 2 * (deck + r * 0.1) + 2 * (1 - t) * t * (cy - r * 1.05) + t * t * (deck + r * 0.1);
      line(g, x, yTop, x, deck);
    }
    g.restore();
    for (const s of [-1, 1]) g.strokeRect(cx + s * r * 0.85 - r * 0.1, deck - r * 0.32, r * 0.2, r * 0.6);
  },
  // 月亮和亮灯的楼
  bluehour(g, cx, cy, r) {
    g.beginPath();
    g.arc(cx + r * 0.5, cy - r * 0.6, r * 0.25, 0, Math.PI * 2);
    g.arc(cx + r * 0.6, cy - r * 0.68, r * 0.22, 0, Math.PI * 2, true);
    g.fill('evenodd');
    const towers = [[-0.9, 0.5, 0.25], [-0.62, 0.95, 0.22], [-0.36, 0.7, 0.2], [-0.12, 1.15, 0.24], [0.16, 0.6, 0.22], [0.42, 0.85, 0.2], [0.66, 0.5, 0.24]];
    const base = cy + r * 0.6;
    for (const [x, h, w] of towers) {
      g.strokeRect(cx + r * x, base - r * h * 0.85, r * w, r * h * 0.85);
      for (let k = 0; k < Math.floor(h * 4); k++) dot(g, cx + r * (x + w / 2), base - r * (0.15 + k * 0.19), r * 0.035);
    }
    line(g, cx - r * 1.0, base, cx + r * 1.0, base);
  },
};

// ---- 印泥斑驳 ----
function mottle(g, S, rand, wear) {
  g.save();
  g.globalCompositeOperation = 'destination-out';
  // 大块：低频噪声放大，印泥有的地方淡
  const coarse = noiseCanvas(14, rand, (v) => Math.max(0, v - 0.35) * 0.9 * wear);
  g.imageSmoothingEnabled = true;
  g.drawImage(coarse, 0, 0, S, S);
  // 细点：纸纹吃不到印泥的小白点，大小不一的圆点（不用像素格，免得一看就是电脑做的）
  const n = Math.round(S * S * 0.006 * wear);
  for (let i = 0; i < n; i++) {
    g.globalAlpha = 0.35 + rand() * 0.65;
    g.beginPath();
    g.arc(rand() * S, rand() * S, S * (0.002 + rand() ** 3 * 0.009), 0, Math.PI * 2);
    g.fill();
  }
  g.globalAlpha = 1;
  // 再加一层很淡的细颗粒，平滑放大
  const fine = noiseCanvas(Math.round(S / 4), rand, (v) => v * 0.14 * wear);
  g.drawImage(fine, 0, 0, S, S);
  // 几道印面磨损的缺口
  g.lineCap = 'round';
  for (let i = 0; i < 5; i++) {
    g.globalAlpha = 0.5 + rand() * 0.4;
    g.lineWidth = S * (0.004 + rand() * 0.01);
    g.beginPath();
    const x = rand() * S;
    const y = rand() * S;
    g.moveTo(x, y);
    g.lineTo(x + (rand() - 0.5) * S * 0.15, y + (rand() - 0.5) * S * 0.08);
    g.stroke();
  }
  g.restore();
  // 一侧压得重、一侧轻：整体一道很淡的渐变擦除
  g.save();
  g.globalCompositeOperation = 'destination-out';
  const a = rand() * Math.PI * 2;
  const grad = g.createLinearGradient(S / 2 + Math.cos(a) * S / 2, S / 2 + Math.sin(a) * S / 2, S / 2 - Math.cos(a) * S / 2, S / 2 - Math.sin(a) * S / 2);
  grad.addColorStop(0, `rgba(0,0,0,${0.35 * wear})`);
  grad.addColorStop(0.6, 'rgba(0,0,0,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, S, S);
  g.restore();
}

function noiseCanvas(n, rand, map) {
  const c = document.createElement('canvas');
  c.width = c.height = n;
  const k = c.getContext('2d');
  const img = k.createImageData(n, n);
  for (let i = 0; i < n * n; i++) img.data[i * 4 + 3] = Math.round(Math.min(1, map(rand())) * 255);
  k.putImageData(img, 0, 0);
  return c;
}

// ---- 小工具 ----
function circle(g, x, y, r, fill = false) {
  g.beginPath();
  g.arc(x, y, r, 0, Math.PI * 2);
  fill ? g.fill() : g.stroke();
}
function dot(g, x, y, r) {
  circle(g, x, y, r, true);
}
function line(g, x0, y0, x1, y1) {
  g.beginPath();
  g.moveTo(x0, y0);
  g.lineTo(x1, y1);
  g.stroke();
}
function wave(g, x, y, w, amp, n) {
  g.beginPath();
  g.moveTo(x, y);
  const step = w / n;
  for (let i = 0; i < n; i++) {
    g.quadraticCurveTo(x + step * (i + 0.25), y - amp, x + step * (i + 0.5), y);
    g.quadraticCurveTo(x + step * (i + 0.75), y + amp, x + step * (i + 1), y);
  }
  g.stroke();
}
// 字号自动缩到放得下
function fitText(g, text, x, y, maxW, maxH, weight) {
  let px = maxH;
  g.font = `${weight} ${px}px ${SERIF}`;
  const w = g.measureText(text).width;
  if (w > maxW) px *= maxW / w;
  g.font = `${weight} ${px}px ${SERIF}`;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(text, x, y);
}
// 沿圆弧排字（车站章上沿那一圈）
function arcText(g, text, cx, cy, r, px, mid, step) {
  const chars = [...text];
  g.font = `700 ${px}px ${SERIF}`;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  const start = mid - (step * (chars.length - 1)) / 2;
  chars.forEach((ch, i) => {
    const a = start + i * step;
    g.save();
    g.translate(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
    g.rotate(a + Math.PI / 2);
    g.fillText(ch, 0, 0);
    g.restore();
  });
}
function hash(s) {
  let h = 2166136261;
  for (const ch of String(s)) h = Math.imul(h ^ ch.codePointAt(0), 16777619);
  return h >>> 0;
}
function mulberry32(a) {
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

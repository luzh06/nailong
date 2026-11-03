// 冲印（加相纸白边）和回忆卡合成。视觉沿用海报 poster/make_poster.py：
// 纸色 PAPER(238,232,220) 加颗粒，INK/GREY/RED 三色，顶部 CIJIAN 和细横线，右下角朱红印章。
import { CAMERA_STYLES } from './styles.js';

const PAPER = [238, 232, 220];
const INK = 'rgb(29,26,23)';
const GREY = 'rgb(120,112,102)';
const RED = [178, 52, 40];
const SERIF = '"Source Han Serif SC","Noto Serif SC","Songti SC","STSong",serif';

export async function blobToImage(blob) {
  return await createImageBitmap(blob);
}

export function canvasToBlob(canvas, type = 'image/png', quality) {
  return new Promise((resolve, reject) =>
    canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('图片编码失败'))), type, quality),
  );
}

// 按相机风格给照片加边，得到一张“冲印好的照片”
export function framePhoto(img, styleId) {
  const style = CAMERA_STYLES[styleId] || CAMERA_STYLES.rangefinder;
  const f = style.frame;
  const base = Math.min(img.width, img.height);
  const l = Math.round(base * f.side);
  const t = Math.round(base * f.top);
  const b = Math.round(base * f.bottom);
  const c = document.createElement('canvas');
  c.width = img.width + l * 2;
  c.height = img.height + t + b;
  const g = c.getContext('2d');
  g.fillStyle = f.color;
  g.fillRect(0, 0, c.width, c.height);
  g.drawImage(img, l, t);
  // 相纸边上一点点纸纹
  paperGrain(g, c.width, c.height, 5, 0.5);
  g.drawImage(img, l, t);
  return c;
}

function paperGrain(g, w, h, amount, alpha = 1) {
  const img = g.getImageData(0, 0, w, h);
  const d = img.data;
  for (let i = 0; i < d.length; i += 4) {
    const n = (Math.random() - 0.5) * amount * 2 * alpha;
    d[i] += n;
    d[i + 1] += n;
    d[i + 2] += n;
  }
  g.putImageData(img, 0, 0);
}

function spacedText(g, text, x, y, spacing) {
  const chars = [...text];
  const widths = chars.map((ch) => g.measureText(ch).width);
  const total = widths.reduce((a, b) => a + b, 0) + spacing * (chars.length - 1);
  let cx = x - total / 2;
  g.textAlign = 'left';
  chars.forEach((ch, i) => {
    g.fillText(ch, cx, y);
    cx += widths[i] + spacing;
  });
}

function drawWithShadow(g, src, x, y, w, h, angle = 0) {
  g.save();
  g.translate(x + w / 2, y + h / 2);
  g.rotate(angle);
  g.shadowColor = 'rgba(40,30,20,0.28)';
  g.shadowBlur = w * 0.04;
  g.shadowOffsetY = w * 0.012;
  g.drawImage(src, -w / 2, -h / 2, w, h);
  g.restore();
}

// 朱红印章：圆角方框加两个字，印泥斑驳用随机擦除做
function seal(g, cx, cy, size, text = '此间') {
  const s = document.createElement('canvas');
  s.width = s.height = size;
  const k = s.getContext('2d');
  const [r, gg, b] = RED;
  k.fillStyle = `rgb(${r},${gg},${b})`;
  const pad = size * 0.06;
  const rad = size * 0.12;
  k.beginPath();
  k.roundRect(pad, pad, size - pad * 2, size - pad * 2, rad);
  k.fill();
  k.globalCompositeOperation = 'destination-out';
  k.font = `900 ${size * 0.36}px ${SERIF}`;
  k.textAlign = 'center';
  k.textBaseline = 'middle';
  const chars = [...text];
  if (chars.length === 2) {
    k.fillText(chars[0], size / 2, size * 0.32);
    k.fillText(chars[1], size / 2, size * 0.7);
  } else {
    k.fillText(text, size / 2, size / 2);
  }
  // 斑驳：擦掉一些小点
  for (let i = 0; i < size * 1.2; i++) {
    k.globalAlpha = Math.random() * 0.8;
    k.beginPath();
    k.arc(Math.random() * size, Math.random() * size, Math.random() * size * 0.012 + 0.5, 0, Math.PI * 2);
    k.fill();
  }
  g.save();
  g.globalAlpha = 0.9;
  g.translate(cx, cy);
  g.rotate(-0.06);
  g.drawImage(s, -size / 2, -size / 2);
  g.restore();
}

/**
 * 合成回忆卡。
 * photos: [{ blob, meta }]，1—3 张
 * info: { title, subtitle, caption, sealText, stamps? }，stamps 是纪念章 canvas 数组（见 stamps.js）
 */
export async function composeMemoryCard(photos, info = {}) {
  if (!photos.length) throw new Error('还没有选照片');
  await document.fonts?.ready;
  const W = 1600;
  const H = 2200;
  const c = document.createElement('canvas');
  c.width = W;
  c.height = H;
  const g = c.getContext('2d');

  g.fillStyle = `rgb(${PAPER.join(',')})`;
  g.fillRect(0, 0, W, H);
  paperGrain(g, W, H, 9);

  // 页眉
  g.fillStyle = INK;
  g.font = `600 30px ${SERIF}`;
  g.textBaseline = 'alphabetic';
  spacedText(g, 'CIJIAN', W / 2, 120, 18);
  g.fillStyle = GREY;
  g.font = `400 24px ${SERIF}`;
  spacedText(g, info.subtitle || '三日归途 · 第一天', W / 2, 165, 6);
  g.strokeStyle = GREY;
  g.lineWidth = 1.5;
  g.beginPath();
  g.moveTo(W * 0.18, 200);
  g.lineTo(W * 0.82, 200);
  g.stroke();

  g.fillStyle = INK;
  g.font = `900 84px ${SERIF}`;
  spacedText(g, info.title || '旅行页', W / 2, 330, 14);

  // 照片
  const framed = [];
  for (const p of photos.slice(0, 3)) {
    const img = await blobToImage(p.blob);
    framed.push(framePhoto(img, p.meta.cameraStyle));
    img.close?.();
  }
  const top = 400;
  const areaH = 1450;
  const fit = (src, maxW, maxH) => {
    const s = Math.min(maxW / src.width, maxH / src.height);
    return [src.width * s, src.height * s];
  };
  if (framed.length === 1) {
    const [w, h] = fit(framed[0], W * 0.78, areaH);
    drawWithShadow(g, framed[0], (W - w) / 2, top + (areaH - h) / 2, w, h, -0.01);
  } else if (framed.length === 2) {
    const [w1, h1] = fit(framed[0], W * 0.62, areaH * 0.56);
    const [w2, h2] = fit(framed[1], W * 0.56, areaH * 0.5);
    drawWithShadow(g, framed[0], W * 0.12, top, w1, h1, -0.025);
    drawWithShadow(g, framed[1], W * 0.88 - w2, top + areaH - h2, w2, h2, 0.03);
  } else {
    // 一大两小：按实际高度排紧，整组在照片区里上下居中（横幅照片矮，不这样中间会空一大块）
    const [w1, h1] = fit(framed[0], W * 0.7, areaH * 0.6);
    const [w2, h2] = fit(framed[1], W * 0.4, areaH * 0.36);
    const [w3, h3] = fit(framed[2], W * 0.4, areaH * 0.36);
    const gap = 50;
    const y0 = top + Math.max(0, (areaH - (h1 + gap + Math.max(h2, h3))) / 2);
    drawWithShadow(g, framed[0], (W - w1) / 2, y0, w1, h1, -0.015);
    drawWithShadow(g, framed[1], W * 0.08, y0 + h1 + gap, w2, h2, 0.035);
    drawWithShadow(g, framed[2], W * 0.92 - w3, y0 + h1 + gap + (h2 - h3) / 2, w3, h3, -0.03);
  }

  // 一行说明：时间 · 天气 · 地点 · 当天的选择
  const stamps = info.stamps ?? [];
  g.fillStyle = GREY;
  g.font = `400 30px ${SERIF}`;
  spacedText(g, info.caption || '', W / 2, stamps.length > 4 ? 1888 : stamps.length ? 1900 : 1960, 4);

  // 这一城集到的纪念章：排在左下，像随手盖在纸上（正片叠底，略歪）
  // 1—4 枚排一行；5 枚以上排成错开的两行，免得挤成一串、压到纸边
  if (stamps.length) {
    const left = 120;
    const right = W - 330;
    const rows = stamps.length > 4 ? [stamps.slice(0, Math.ceil(stamps.length / 2)), stamps.slice(Math.ceil(stamps.length / 2))] : [stamps];
    const size = rows.length > 1 ? 138 : Math.min(210, (right - left) / (stamps.length * 0.8 + 0.2));
    const rowY = rows.length > 1 ? [1968, 2110] : [2058];
    let k = 0;
    rows.forEach((row, ri) => {
      const cols = rows[0].length;
      const step = Math.min(size * (rows.length > 1 ? 1.3 : 1.12), (right - left - size) / Math.max(1, cols - 1));
      const x0 = left + (right - left - (size + step * (cols - 1))) / 2 + size / 2 + (ri ? step / 2 : 0);
      row.forEach((st, i) => {
        const s = size * (0.94 + ((k * 29) % 5) * 0.015);
        g.save();
        g.globalCompositeOperation = 'multiply';
        g.globalAlpha = 0.9;
        g.translate(x0 + step * i, rowY[ri] + (((k * 37) % 5) - 2) * 6);
        g.rotate((((k * 53) % 9) - 4) * 0.035);
        g.drawImage(st, -s / 2, -s / 2, s, s);
        g.restore();
        k++;
      });
    });
  }

  seal(g, W - 210, H - 170, 170, info.sealText || '此间');
  return c;
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

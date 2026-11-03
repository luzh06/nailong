// 快门声：先用 WebAudio 合成占位，正式音效（CC0 或自录）到了再换成音频文件。
let ctx;

function noiseBurst(t, dur, gain, freq) {
  const len = Math.ceil(ctx.sampleRate * dur);
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 4);
  const src = ctx.createBufferSource();
  src.buffer = buf;
  const bp = ctx.createBiquadFilter();
  bp.type = 'bandpass';
  bp.frequency.value = freq;
  bp.Q.value = 1.2;
  const g = ctx.createGain();
  g.gain.value = gain;
  src.connect(bp).connect(g).connect(ctx.destination);
  src.start(t);
}

function motor(t, dur) {
  const o = ctx.createOscillator();
  o.type = 'sawtooth';
  o.frequency.setValueAtTime(95, t);
  o.frequency.linearRampToValueAtTime(120, t + dur);
  const lp = ctx.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.value = 700;
  const g = ctx.createGain();
  g.gain.setValueAtTime(0, t);
  g.gain.linearRampToValueAtTime(0.05, t + 0.05);
  g.gain.setValueAtTime(0.05, t + dur - 0.08);
  g.gain.linearRampToValueAtTime(0, t + dur);
  o.connect(lp).connect(g).connect(ctx.destination);
  o.start(t);
  o.stop(t + dur);
}

export function playShutter(kind) {
  try {
    ctx ??= new AudioContext();
    if (ctx.state === 'suspended') ctx.resume();
    const t = ctx.currentTime + 0.01;
    if (kind === 'instant') {
      noiseBurst(t, 0.05, 0.6, 2600);
      motor(t + 0.12, 0.7); // 吐出相纸
    } else {
      noiseBurst(t, 0.04, 0.7, 3200); // 咔
      noiseBurst(t + 0.07, 0.05, 0.45, 1800); // 嗒
      noiseBurst(t + 0.32, 0.12, 0.18, 900); // 过片
    }
  } catch {
    /* 没有声音也不影响拍照 */
  }
}

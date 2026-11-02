// 相机风格：只改变照片的样子，不改变能力（见 此间_剧情与整合方案_v0.2.md 模块 5）。
// grade 里的数值是临时调色，等东京 Cycles 渲染图到了再对照调；
// 正式版可以在 lut 里填 .cube 文件路径，填了就在调色之后再套 LUT。

export const CAMERA_STYLES = {
  instant: {
    id: 'instant',
    name: '即时成像相机',
    aspect: 1,                      // 照片画面宽高比
    frame: { side: 0.055, top: 0.055, bottom: 0.2, color: '#f3efe6' },  // 相纸白边，占画面边长的比例
    grade: {
      contrast: 0.88,
      saturation: 0.8,
      tint: [1.04, 1.0, 0.93],      // 乘在显示色上，偏暖
      fade: 0.09,                   // 黑位抬起，褪色感
      fadeColor: [0.16, 0.13, 0.12],
      highlight: [1.0, 0.98, 0.94], // 高光压一点、偏奶油色
      grain: 0.03,
      vignette: 0.28,
    },
    lut: null,
    develop: 'instant',             // 相纸慢慢显影
    shutter: 'instant',
    finder: 'square',
  },
  rangefinder: {
    id: 'rangefinder',
    name: '胶片旁轴相机',
    aspect: 3 / 2,
    frame: { side: 0.025, top: 0.025, bottom: 0.025, color: '#f6f3ec' },  // 冲印的细白边
    grade: {
      contrast: 1.08,
      saturation: 1.04,
      tint: [1.05, 1.0, 0.91],
      fade: 0.02,
      fadeColor: [0.1, 0.08, 0.07],
      highlight: [1.0, 0.97, 0.9],
      grain: 0.045,
      vignette: 0.36,
    },
    lut: null,
    develop: 'ink',                 // 书页上墨色浮现
    shutter: 'mech',
    finder: 'brightline',
  },
};

export const FOCAL_LENGTHS = [24, 35, 50, 85];

// 135 画幅的短边是 24mm；方画幅也按 24mm 算，保证同焦段视角一致
export function verticalFovForFocal(focalMm, aspect) {
  const shortSide = 24;
  const h = aspect >= 1 ? shortSide : shortSide / aspect;
  return (2 * Math.atan(h / 2 / focalMm) * 180) / Math.PI;
}

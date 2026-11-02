async (page) => {
  await page.bringToFront();
  const dir = 'C:/Users/LU/AppData/Local/Temp/claude/D--project-cijian/54b26533-9386-4e26-9508-580ec68cbc7d/scratchpad/diff';
  const prefix = globalThis.__shotPrefix || 'q1';
  const views = {
    spawn_golden: '&time=golden',
    spawn_day: '&time=day',
    spawn_blue: '&time=blue',
    cbd_day: '&time=day&cam=-260,60,-150&look=-300,60,450&fov=50',
    skyline_tele_day: '&time=day&cam=28,15,-767&look=-420,110,700&fov=22',
    night_facades: '&time=blue&cam=-250,40,-200&look=-420,60,640&fov=30',
    foreshore_day: '&time=day&cam=40,16,-760&look=-40,4,-735&fov=55',
    water_shore_golden: '&time=golden&cam=-150,8,-600&look=-330,0,-180&fov=55',
    bridge_golden: '&time=golden&cam=-200,30,-560&look=-450,60,-380&fov=55',
    aerial_golden: '&time=golden&cam=200,700,-1800&look=-200,0,0&fov=50',
  };
  const logs = [];
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type()) && !m.text().includes('favicon') && !m.text().includes('404')) logs.push(m.text().slice(0, 400)); });
  page.on('pageerror', (e) => logs.push('pageerror: ' + e.message));
  await page.setViewportSize({ width: 1280, height: 800 });
  const stats = {};
  for (const [name, q] of Object.entries(views)) {
    await page.goto(`http://127.0.0.1:8770/?still=1${q}&t=${Date.now()}`);
    await page.waitForFunction(() => !document.getElementById('loading'), null, { timeout: 90000 });
    await page.waitForTimeout(3500);
    stats[name] = await page.evaluate(() => document.getElementById('stats').textContent.split('\n')[0]);
    await page.evaluate(() => document.querySelectorAll('.hud, .hint, .stats').forEach((el) => { el.style.display = 'none'; }));
    await page.screenshot({ path: `${dir}/${prefix}_${name}.png` });
  }
  return { stats, logs: [...new Set(logs)].slice(0, 8) };
}

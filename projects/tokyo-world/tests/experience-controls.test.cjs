'use strict';

// experience-controls 独立测试：
// 1) 静态检查（固定导出、文件、harness 标记）
// 2) 用本机 Chrome/Edge 无头加载独立 harness，读取真实浏览器里的测试报告。
//
// 运行：
//   cd projects/tokyo-world
//   node tests/experience-controls.test.cjs
// 可选：
//   set XC_BROWSER=C:\path\to\chrome.exe
//
// 不修改主入口，不加载 Three.js，不依赖 npm 包。

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const os = require('node:os');
const { pathToFileURL } = require('node:url');
const { spawn, spawnSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const MODULE = path.join(ROOT, 'web', 'experience-controls.mjs');
const CSS = path.join(ROOT, 'web', 'experience-controls.css');
const HARNESS = path.join(ROOT, 'tests', 'experience-controls-harness.html');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg'
};

function startServer() {
  const server = http.createServer((req, res) => {
    let rel = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
    if (rel === '/') rel = '/tests/experience-controls-harness.html';
    const file = path.join(ROOT, rel.replace(/^\/+/, ''));
    const relative = path.relative(ROOT, file);
    if (relative.startsWith('..') || path.isAbsolute(relative)) {
      res.writeHead(403);
      res.end('forbidden');
      return;
    }
    fs.stat(file, (error, stat) => {
      if (error || !stat.isFile()) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('not found');
        return;
      }
      res.writeHead(200, {
        'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
        'Cache-Control': 'no-store'
      });
      fs.createReadStream(file).pipe(res);
    });
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

function findBrowsers() {
  const candidates = [
    process.env.XC_BROWSER,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
  ].filter(Boolean);
  const unique = [...new Set(candidates)];
  return unique.filter((candidate) => {
    try { return fs.statSync(candidate).isFile(); } catch { return false; }
  });
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function waitForDevTools(profile, child, stderr) {
  return new Promise((resolve, reject) => {
    const file = path.join(profile, 'DevToolsActivePort');
    const deadline = Date.now() + 20000;
    const poll = () => {
      if (fs.existsSync(file)) {
        const port = Number(String(fs.readFileSync(file, 'utf8')).trim().split(/\r?\n/)[0]);
        if (Number.isInteger(port) && port > 0) {
          resolve(port);
          return;
        }
      }
      if (child.exitCode !== null) {
        reject(new Error(`browser exited with ${child.exitCode}\n${stderr().slice(-3000)}`));
        return;
      }
      if (Date.now() > deadline) {
        reject(new Error(`DevToolsActivePort not written\n${stderr().slice(-3000)}`));
        return;
      }
      setTimeout(poll, 100);
    };
    poll();
  });
}

async function waitForTargets(port) {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      if (response.ok) {
        const targets = await response.json();
        if (targets.some((target) => target.type === 'page')) return targets;
      }
    } catch { /* booting */ }
    await sleep(100);
  }
  throw new Error('DevTools targets did not become available');
}

function connectCDP(url) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(url);
    const pending = new Map();
    let sequence = 0;
    let onEvent = null;
    const api = {
      send(method, params = {}) {
        return new Promise((res, rej) => {
          const id = ++sequence;
          pending.set(id, { res, rej });
          socket.send(JSON.stringify({ id, method, params }));
        });
      },
      onEvent(fn) { onEvent = fn; },
      close() { try { socket.close(); } catch { /* ignore */ } }
    };
    socket.addEventListener('open', () => resolve(api));
    socket.addEventListener('message', (event) => {
      let message;
      try { message = JSON.parse(typeof event.data === 'string' ? event.data : String(event.data)); } catch { return; }
      if (message.id) {
        const waiter = pending.get(message.id);
        if (!waiter) return;
        pending.delete(message.id);
        if (message.error) waiter.rej(new Error(`${message.error.message} (${message.error.code})`));
        else waiter.res(message.result);
        return;
      }
      if (onEvent) onEvent(message);
    });
    socket.addEventListener('error', () => reject(new Error('CDP WebSocket failed')));
    socket.addEventListener('close', () => {
      for (const waiter of pending.values()) waiter.rej(new Error('CDP socket closed'));
      pending.clear();
    });
  });
}

function stopBrowser(child) {
  if (!child || child.exitCode !== null) return;
  try { child.kill(); } catch { /* ignore */ }
  try {
    spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], {
      windowsHide: true,
      stdio: 'ignore',
      timeout: 15000
    });
  } catch { /* ignore */ }
}

async function runHarness(browser, url) {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'xc-controls-test-'));
  let child = null;
  let cdp = null;
  let stderr = '';
  const exceptions = [];
  try {
    child = spawn(browser, [
      '--headless=new',
      '--disable-gpu',
      '--no-sandbox',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-extensions',
      '--disable-background-networking',
      '--hide-scrollbars',
      '--mute-audio',
      '--window-size=1200,900',
      '--remote-debugging-port=0',
      `--user-data-dir=${profile}`,
      'about:blank'
    ], { stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true });
    child.stderr.on('data', (chunk) => {
      stderr += chunk;
      if (stderr.length > 24000) stderr = stderr.slice(-24000);
    });
    const port = await waitForDevTools(profile, child, () => stderr);
    const targets = await waitForTargets(port);
    const page = targets.find((target) => target.type === 'page');
    if (!page?.webSocketDebuggerUrl) throw new Error('no debuggable page target');
    cdp = await connectCDP(page.webSocketDebuggerUrl);
    cdp.onEvent((message) => {
      if (message.method === 'Runtime.exceptionThrown') {
        exceptions.push(message.params?.exceptionDetails?.text || 'exception');
      }
    });
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    const navigation = await cdp.send('Page.navigate', { url });
    if (navigation?.errorText) throw new Error(`navigation failed: ${navigation.errorText}`);

    let report = null;
    const deadline = Date.now() + 25000;
    while (Date.now() < deadline) {
      const evaluated = await cdp.send('Runtime.evaluate', {
        expression: 'window.__XC_TEST_RESULTS__ ? JSON.stringify(window.__XC_TEST_RESULTS__) : ""',
        returnByValue: true,
        awaitPromise: true
      });
      const value = evaluated?.result?.value;
      if (value) {
        try { report = JSON.parse(value); break; } catch { /* still writing */ }
      }
      await sleep(150);
    }
    if (!report) {
      let diagnostic = '';
      try {
        const evaluated = await cdp.send('Runtime.evaluate', {
          expression: '(document.getElementById("xc-results")?.textContent || "") + "\\n" + (document.body?.innerText || "").slice(-1800)',
          returnByValue: true
        });
        diagnostic = evaluated?.result?.value || '';
      } catch { /* ignore */ }
      throw new Error(
        `harness results timed out\nexceptions: ${exceptions.join(' | ') || 'none'}\n` +
        `page: ${diagnostic}\nstderr: ${stderr.slice(-3000)}`
      );
    }
    return { report, browser };
  } finally {
    if (cdp) cdp.close();
    stopBrowser(child);
    await sleep(350);
    try {
      fs.rmSync(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 120 });
    } catch { /* profile can remain locked briefly on Windows */ }
  }
}

test('fixed API, files and harness markers exist', async () => {
  for (const file of [MODULE, CSS, HARNESS]) {
    assert.ok(fs.existsSync(file), `missing ${file}`);
  }
  const moduleSource = await fsp.readFile(MODULE, 'utf8');
  assert.match(moduleSource, /export function createExperienceControls\s*\(/, 'fixed export missing');
  assert.match(moduleSource, /getMoveIntent\s*\(/, 'getMoveIntent missing');
  assert.match(moduleSource, /setMode\s*\(/, 'setMode missing');
  assert.match(moduleSource, /dispose\s*\(/, 'dispose missing');

  const mod = await import(pathToFileURL(MODULE).href);
  assert.equal(typeof mod.createExperienceControls, 'function', 'module export is not a function');

  const css = await fsp.readFile(CSS, 'utf8');
  assert.match(css, /\.xc-stick/, 'touch stick styling missing');
  assert.match(css, /\.xc-exit/, 'touch exit styling missing');
  assert.match(css, /prefers-reduced-motion/, 'reduced-motion support missing');
  assert.match(css, /min-height:44px/, 'touch buttons must be at least 44px');
  assert.match(css, /:focus-visible/, 'focus-visible styling missing');
  assert.match(css, /left:max\(16px, env\(safe-area-inset-left\)\)/, 'stick must sit bottom-left with safe area');
  assert.match(css, /bottom:calc\(92px \+ env\(safe-area-inset-bottom\)\)/, 'stick must reserve bottom-left for itself');

  const harness = await fsp.readFile(HARNESS, 'utf8');
  assert.match(harness, /createExperienceControls/, 'harness does not import controls');
  assert.match(harness, /xc-results/, 'harness result marker missing');
});

test('browser harness passes every required interaction scenario', async () => {
  const browsers = findBrowsers();
  assert.ok(browsers.length, 'No Chrome/Edge found. Set XC_BROWSER to a Chrome/Edge executable.');
  const server = await startServer();
  const url = `http://127.0.0.1:${server.address().port}/tests/experience-controls-harness.html?autorun=1`;
  try {
    let found = null;
    let lastError = null;
    for (const browser of browsers) {
      try {
        found = await runHarness(browser, url);
        break;
      } catch (error) {
        lastError = error;
      }
    }
    assert.ok(found, `No browser completed the harness.\n${lastError?.stack || lastError}`);
    const report = found.report;
    assert.equal(report.pending, false, 'harness did not finish');
    assert.equal(report.failed, 0,
      `browser harness failures:\n${report.results.filter((r) => !r.ok).map((r) => `${r.name}: ${r.error}`).join('\n')}`);
    assert.ok(report.total >= 12, `expected at least 12 tests, got ${report.total}`);
    assert.equal(report.unhandled || 0, 0, `unhandled rejections: ${report.unhandled}`);
    console.log(`\n[experience-controls] ${report.passed}/${report.total} tests passed in ${path.basename(found.browser)}`);
    for (const item of report.results) {
      console.log(`  ${item.ok ? 'PASS' : 'FAIL'}  ${item.name}`);
    }
    console.log(`  browser: ${report.browser || 'unknown'}`);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

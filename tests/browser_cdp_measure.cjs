// Drives Chrome through the DevTools Protocol for what --dump-dom cannot do: a real pointer hover and an emulated media feature
// (forced-colors). Usage: node browser_cdp_measure.cjs <chrome> <job.json>
// job: {url, width, height, features?: [{name, value}], waitFor: selector, hover?: selector, measure: JS expression}
// Prints the measure expression's JSON value on one line. Exits 1, with the reason on stderr, when Chrome cannot be driven or the
// selector never appears.
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const [chromePath, jobFile] = process.argv.slice(2);
const job = JSON.parse(fs.readFileSync(jobFile, 'utf8'));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'cdp-measure-'));
const chrome = spawn(chromePath, ['--headless=new', '--disable-gpu', '--remote-debugging-port=0', '--user-data-dir=' + profile, '--hide-scrollbars', '--allow-file-access-from-files', 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
let stderr = '';
const endpoint = new Promise((resolve, reject) => {
  chrome.stderr.on('data', d => {
    stderr += d;
    const m = stderr.match(/DevTools listening on (ws:\/\/\S+)/);
    if (m) resolve(m[1]);
  });
  setTimeout(() => reject(new Error('Chrome did not start: ' + stderr.slice(0, 400))), 20000);
});
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const ws = new WebSocket(await endpoint);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let id = 0;
  const pending = new Map();
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      const [resolve, reject] = pending.get(m.id);
      pending.delete(m.id);
      if (m.error) reject(new Error(JSON.stringify(m.error))); else resolve(m.result);
    }
  };
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const n = ++id;
    pending.set(n, [resolve, reject]);
    ws.send(JSON.stringify({ id: n, method, params, sessionId }));
  });
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  const S = (method, params) => send(method, params, sessionId);
  const run = async expression => {
    const r = await S('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text);
    return r.result.value;
  };
  await S('Page.enable');
  await S('Runtime.enable');
  await S('Emulation.setDeviceMetricsOverride', { width: job.width, height: job.height, deviceScaleFactor: 1, mobile: false });
  if (job.features) await S('Emulation.setEmulatedMedia', { media: '', features: job.features });
  await S('Page.navigate', { url: job.url });
  let found = false;
  for (let i = 0; i < 200 && !found; i++) {
    await sleep(50);
    found = await run(`!!document.querySelector(${JSON.stringify(job.waitFor)})`);
  }
  if (!found) throw new Error('never appeared: ' + job.waitFor);
  await run('document.fonts.ready.then(() => true)');
  if (job.hover) {
    const at = await run(`(() => { const e = document.querySelector(${JSON.stringify(job.hover)}); if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`);
    if (!at) throw new Error('nothing to hover: ' + job.hover);
    await S('Input.dispatchMouseEvent', { type: 'mouseMoved', x: at.x, y: at.y });
    await sleep(300);
  }
  console.log(JSON.stringify(await run(job.measure)));
  ws.close();
}

main().then(
  () => { chrome.kill(); setTimeout(() => { fs.rmSync(profile, { recursive: true, force: true }); process.exit(0); }, 300); },
  e => { console.error(String((e && e.stack) || e)); chrome.kill(); setTimeout(() => { fs.rmSync(profile, { recursive: true, force: true }); process.exit(1); }, 300); },
);

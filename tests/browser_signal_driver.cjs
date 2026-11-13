// Drives one Chrome tab through the DevTools Protocol for the Signal page tests: real key presses, real clicks, text
// insertion, screenshots, and a record of the console and of every request the page made.
// Usage: node browser_signal_driver.cjs <chrome> <job.json>
// job: {url, width, height, steps: [...]}. A step is one of
//   {eval: expr, as: name}              evaluate expr in the page, keep its value under `name`
//   {wait: expr, as?: name, ms?: 8000}  poll until expr is truthy (error on timeout), keep the value if named
//   {click: selector}                   a real mouse click at the element's centre
//   {key: "Tab", shift?: true}          a real key press (Tab, Enter, Escape, or one character)
//   {insert: text}                      insert text at the focus, as typing would
//   {shot: path}                        a PNG of the viewport
//   {reload: true}                      reload the page
//   {stop: true}                        print "@@STOP" and wait for a line on stdin (the test stops the service)
// Prints one line "@@RESULT <json>": {values, console, requests, documentHeaders}. console holds the page's console errors
// and warnings, exceptions, and browser log entries of level error or warning, each {source, level, text}.
// Exits 1, reason on stderr, when Chrome cannot be driven or a wait times out.
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const readline = require('readline');

const [chromePath, jobFile] = process.argv.slice(2);
const job = JSON.parse(fs.readFileSync(jobFile, 'utf8'));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'signal-driver-'));
const chrome = spawn(chromePath, ['--headless=new', '--disable-gpu', '--remote-debugging-port=0', '--user-data-dir=' + profile, '--hide-scrollbars', 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
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
const stdinLines = readline.createInterface({ input: process.stdin })[Symbol.asyncIterator]();

const KEYS = {
  Tab: { code: 'Tab', vk: 9 },
  Enter: { code: 'Enter', vk: 13, text: '\r' },
  Escape: { code: 'Escape', vk: 27 },
  '/': { code: 'Slash', vk: 191, text: '/' },
};

async function main() {
  const ws = new WebSocket(await endpoint);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let id = 0;
  const pending = new Map();
  const events = [];
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      const [resolve, reject] = pending.get(m.id);
      pending.delete(m.id);
      if (m.error) reject(new Error(JSON.stringify(m.error))); else resolve(m.result);
    } else if (m.method) events.push(m);
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
  for (const domain of ['Page', 'Runtime', 'Network', 'Log']) await S(domain + '.enable');
  await S('Emulation.setFocusEmulationEnabled', { enabled: true });
  await S('Emulation.setDeviceMetricsOverride', { width: job.width, height: job.height, deviceScaleFactor: 1, mobile: false });

  const key = async (name, shift) => {
    const k = KEYS[name];
    if (!k) throw new Error('unknown key ' + name);
    const base = { key: name, code: k.code, windowsVirtualKeyCode: k.vk, modifiers: shift ? 8 : 0 };
    await S('Input.dispatchKeyEvent', { type: k.text ? 'keyDown' : 'rawKeyDown', ...base, ...(k.text ? { text: k.text } : {}) });
    await S('Input.dispatchKeyEvent', { type: 'keyUp', ...base });
  };

  const values = {};
  await S('Page.navigate', { url: job.url });
  for (const [n, step] of job.steps.entries()) {
    const where = 'step ' + n + ' ' + JSON.stringify(step).slice(0, 160);
    if ('eval' in step) {
      values[step.as] = await run(step.eval);
    } else if ('wait' in step) {
      let value = false;
      let lastError = '';
      const deadline = Date.now() + (step.ms || 8000);
      while (!value && Date.now() < deadline) {
        try { value = await run(step.wait); } catch (e) { value = false; lastError = String(e.message || e); } // the page may be between documents; the last error is reported on timeout
        if (!value) await sleep(40);
      }
      if (!value) throw new Error('timed out: ' + where + (lastError ? ' (last error: ' + lastError.slice(0, 200) + ')' : ''));
      if (step.as) values[step.as] = value;
    } else if ('click' in step) {
      const at = await run(`(() => { const e = document.querySelector(${JSON.stringify(step.click)}); if (!e) return null; e.scrollIntoView({block: 'center'}); const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; })()`);
      if (!at) throw new Error('nothing to click: ' + where);
      for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased'])
        await S('Input.dispatchMouseEvent', { type, x: at.x, y: at.y, button: 'left', clickCount: 1, buttons: type === 'mousePressed' ? 1 : 0 });
    } else if ('key' in step) {
      await key(step.key, step.shift);
    } else if ('insert' in step) {
      await S('Input.insertText', { text: step.insert });
    } else if ('shot' in step) {
      const r = await S('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(step.shot, Buffer.from(r.data, 'base64'));
    } else if ('reload' in step) {
      await S('Page.reload');
    } else if ('stop' in step) {
      console.log('@@STOP');
      const line = await stdinLines.next();
      if (line.done) throw new Error('the test closed stdin before releasing: ' + where);
    } else {
      throw new Error('unknown step: ' + where);
    }
  }
  await sleep(200); // late console entries
  const consoleLines = [];
  for (const e of events) {
    const p = e.params;
    if (e.method === 'Runtime.consoleAPICalled' && ['error', 'warning', 'assert'].includes(p.type))
      consoleLines.push({ source: 'console', level: p.type, text: p.args.map(a => a.value === undefined ? (a.description || a.type) : String(a.value)).join(' ') });
    else if (e.method === 'Runtime.exceptionThrown')
      consoleLines.push({ source: 'exception', level: 'error', text: (p.exceptionDetails.exception && p.exceptionDetails.exception.description) || p.exceptionDetails.text });
    else if (e.method === 'Log.entryAdded' && ['error', 'warning'].includes(p.entry.level))
      consoleLines.push({ source: p.entry.source, level: p.entry.level, text: p.entry.text + (p.entry.url ? ' ' + p.entry.url : '') });
  }
  const requests = events.filter(e => e.method === 'Network.requestWillBeSent').map(e => e.params.request.url);
  const documentHeaders = events.filter(e => e.method === 'Network.responseReceived' && e.params.type === 'Document').map(e => ({ url: e.params.response.url, headers: e.params.response.headers }));
  console.log('@@RESULT ' + JSON.stringify({ values, console: consoleLines, requests, documentHeaders }));
  ws.close();
}

const finish = code => { chrome.kill(); setTimeout(() => { fs.rmSync(profile, { recursive: true, force: true }); process.exit(code); }, 300); };
main().then(() => finish(0), e => { console.error(String((e && e.stack) || e)); finish(1); });

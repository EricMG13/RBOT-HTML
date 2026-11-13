// Shared by the DevTools Protocol drivers (browser_cdp_measure.cjs, browser_signal_driver.cjs): start a headless Chrome with its
// own profile folder, find its DevTools endpoint, and open a WebSocket whose `send` returns each command's result.
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

// Returns {chrome, profile, endpoint}; endpoint is a promise of the ws:// URL, rejected after 20 s.
function startChrome(chromePath, prefix, extraArgs = []) {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), prefix));
  const chrome = spawn(chromePath, ['--headless=new', '--disable-gpu', '--remote-debugging-port=0', '--user-data-dir=' + profile, '--hide-scrollbars', ...extraArgs, 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = '';
  const endpoint = new Promise((resolve, reject) => {
    chrome.stderr.on('data', d => {
      stderr += d;
      const m = stderr.match(/DevTools listening on (ws:\/\/\S+)/);
      if (m) resolve(m[1]);
    });
    setTimeout(() => reject(new Error('Chrome did not start: ' + stderr.slice(0, 400))), 20000);
  });
  return { chrome, profile, endpoint };
}

// Opens the socket; onEvent, when given, receives every message that is not a command's answer.
async function connect(endpoint, onEvent) {
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
    } else if (m.method && onEvent) onEvent(m);
  };
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const n = ++id;
    pending.set(n, [resolve, reject]);
    ws.send(JSON.stringify({ id: n, method, params, sessionId }));
  });
  return { ws, send };
}

module.exports = { startChrome, connect };

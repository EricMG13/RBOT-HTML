(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('.run-card'); i++) await sleep(50);
  await sleep(300);
  const rect = sel => { const el = document.querySelector(sel); return el ? el.getBoundingClientRect() : null; };
  const run = rect('.activity-running'), wait = rect('.activity-waiting');
  const bar = document.querySelector('.run-card progress');
  const out = {
    runningRight: run && run.right, waitingLeft: wait && wait.left,
    scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth,
    bodyScrollWidth: document.body.scrollWidth, contentScroll: document.getElementById('content').scrollWidth,
    contentClient: document.getElementById('content').clientWidth,
    progressName: bar && bar.getAttribute('aria-label'), progressMax: bar && bar.max, progressValue: bar && bar.value,
    barHeight: bar && bar.getBoundingClientRect().height,
    badges: [...document.querySelectorAll('.run-mods .chip')].map(c => { const s = getComputedStyle(c); return [s.backgroundColor, s.color, s.height]; }),
  };
  const details = document.querySelector('details.run-files');
  details.open = true;
  const before = details.open;
  // A changed snapshot, as the 30 s reload brings: the open list stays open.
  window.RUN_ACTIVITY = { ...window.RUN_ACTIVITY, updated: 'later', runs: window.RUN_ACTIVITY.runs.map(r => (r.id === 'r1' ? { ...r, reason: 'changed' } : r)) };
  window.onRunActivity();
  await sleep(100);
  const after = document.querySelector('details.run-files');
  out.openBefore = before; out.openAfter = after.open; out.changedShown = document.body.textContent.includes('changed');
  const text = JSON.stringify(out);
  // Framed (the 375px test), the page posts its measures to the wrapper; otherwise it writes them here.
  if (parent !== window) { parent.postMessage(text, '*'); return; }
  const pre = document.createElement('pre'); pre.id = 'probe'; pre.textContent = text; document.body.appendChild(pre);
})();

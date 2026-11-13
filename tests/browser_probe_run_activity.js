(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('.run-card'); i++) await sleep(50);
  await sleep(300);
  const rect = sel => { const el = document.querySelector(sel); return el ? el.getBoundingClientRect() : null; };
  const run = rect('.activity-running'), wait = rect('.activity-waiting');
  const out = {
    runningRight: run && run.right, waitingLeft: wait && wait.left,
    scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth,
    bodyScrollWidth: document.body.scrollWidth, contentScroll: document.getElementById('content').scrollWidth,
    contentClient: document.getElementById('content').clientWidth,
    steps: document.querySelectorAll('.run-card .step').length,
    stepStates: [...document.querySelectorAll('.run-card .step')].map(s => s.className.replace('step ', '')),
    loaders: document.querySelectorAll('.lat').length,
    queued: document.querySelectorAll('.run-queue li').length,
  };
  // A changed snapshot, as the 30 s reload brings: the card is drawn again with the new reason.
  window.RUN_ACTIVITY = { ...window.RUN_ACTIVITY, updated: 'later', runs: window.RUN_ACTIVITY.runs.map(r => (r.id === 'r1' ? { ...r, reason: 'changed' } : r)) };
  window.onRunActivity();
  await sleep(100);
  out.changedShown = document.body.textContent.includes('changed');
  const text = JSON.stringify(out);
  // Framed (the 375px test), the page posts its measures to the wrapper; otherwise it writes them here.
  if (parent !== window) { parent.postMessage(text, '*'); return; }
  const pre = document.createElement('pre'); pre.id = 'probe'; pre.textContent = text; document.body.appendChild(pre);
})();

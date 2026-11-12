(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('#content *'); i++) await sleep(50);
  await sleep(300);
  const cs = getComputedStyle(document.getElementById('content'));
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify({left: cs.paddingLeft, right: cs.paddingRight}); document.body.appendChild(out);
})();

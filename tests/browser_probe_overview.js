(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.overview-part'); i++) await sleep(50);
  const content = document.getElementById('content'), de = document.documentElement;
  const shown = id => getComputedStyle(document.getElementById(id)).display !== 'none';
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    parts: [...document.querySelectorAll('.overview-part')].map(part => part.id),
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
    navigatorShown: shown('navigator'), moduleToggleShown: shown('module-toggle'),
    outline: document.querySelectorAll('#module-list .section-outline').length,
    timeline: document.querySelectorAll('.overview-page .tl').length,
    lead: document.querySelector('#overview-lead').textContent,
    // One tile per module: its name, then its declared state when the handoff has one.
    bottomLines: [...document.querySelectorAll('#overview-modules .mt')].map(tile => [tile.querySelector('.mt-name').textContent, tile.querySelector('.mt-state')?.textContent ?? ''].join(' ').trim()),
  });
  document.body.append(out);
})();

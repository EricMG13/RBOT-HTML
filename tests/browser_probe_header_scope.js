(async () => {
  // The run header's "As of" chip (the run's scope): one line, clear of the title and of the start link.
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('header.issuer h1'); i++) await sleep(50);
  await sleep(300);
  const de = document.documentElement, box = el => el.getBoundingClientRect();
  const header = document.querySelector('header.issuer'), h1 = header.querySelector('h1');
  const chips = [...header.querySelectorAll('.hchips .hchip')], scope = chips[0];
  const link = header.querySelector('a.start-run');
  const hit = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  const s = box(scope), t = box(h1);
  const seen = {
    headerHeight: box(header).height, scopeHeight: s.height, scopeText: scope.textContent,
    sideCount: header.querySelectorAll('.issuer-side').length,
    chipsText: chips.map(c => c.textContent), chipsOnOneRow: chips.every(c => Math.abs(box(c).top - s.top) < 1),
    scopeOverlapsTitle: hit(s, t), fits: de.scrollWidth <= innerWidth,
  };
  if (link) {
    const a = box(link);
    Object.assign(seen, {
      linkOverlapsTitle: hit(a, t), linkOverlapsChips: chips.some(c => hit(a, box(c))),
      linkMidMinusTitleMid: Math.abs((a.top + a.bottom) / 2 - (t.top + t.bottom) / 2),
      linkRight: a.right, headerRight: box(header.querySelector('.issuer-row')).right,
    });
  }
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();

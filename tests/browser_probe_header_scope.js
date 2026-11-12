(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('header.issuer h1'); i++) await sleep(50);
  await sleep(300);
  const de = document.documentElement, box = el => el.getBoundingClientRect();
  const header = document.querySelector('header.issuer'), h1 = header.querySelector('h1');
  const scope = header.querySelector('.scope'), icon = scope.querySelector('img,svg'), text = scope.querySelector('strong');
  const link = header.querySelector('a.start-run');
  const hit = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  const s = box(scope), t = box(h1);
  const seen = {
    headerHeight: box(header).height, scopeHeight: s.height, sideCount: header.querySelectorAll('.issuer-side').length,
    iconGap: box(text).left - box(icon).right, scopeOverlapsTitle: hit(s, t),
    fits: de.scrollWidth <= innerWidth,
  };
  if (link) {
    const a = box(link);
    Object.assign(seen, {
      sameRow: Math.abs((s.top + s.bottom) / 2 - (a.top + a.bottom) / 2), linkOverlapsTitle: hit(a, t),
    });
  }
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();

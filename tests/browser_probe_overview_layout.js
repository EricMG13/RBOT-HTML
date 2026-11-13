(async () => {
  // Measures the Overview as the redesign draws it: the lead, the why grid (key findings beside
  // what would change the view and what to watch), the module tiles and the limitations.
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('#overview-lead'); i++) await sleep(50);
  await sleep(300);
  const $ = selector => document.querySelector(selector);
  const box = element => element.getBoundingClientRect();
  const style = (element, name) => getComputedStyle(element)[name];
  const de = document.documentElement;
  const seen = {
    parts: [...document.querySelectorAll('#content .overview-part')].map(part => part.id),
    fits: de.scrollWidth <= window.innerWidth && $('#content').scrollWidth <= $('#content').clientWidth,
    viewport: window.innerWidth,
    navigatorShown: style($('#navigator'), 'display') !== 'none',
  };
  const lead = $('#overview-lead');
  if (lead) {
    const h2 = lead.querySelector('h2'), eyebrow = lead.querySelector('h3.eyebrow');
    const first = lead.querySelector('.verdict-lead, p.intro');
    seen.lead = {
      text: lead.textContent,
      h2: h2 && { text: h2.textContent, cls: h2.className, transform: style(h2, 'textTransform') },
      eyebrow: eyebrow && eyebrow.textContent,
      firstSize: first ? style(first, 'fontSize') : null,
      firstText: first ? first.textContent : null,
      left: box(lead).left,
    };
  }
  const why = $('#overview-why');
  if (why) {
    const key = why.querySelector(':scope > .c14'), side = why.querySelector(':scope > .c10');
    const w = box(why), k = box(key), s = box(side);
    seen.why = {
      width: w.width, gap: s.left - k.right,
      key: { left: k.left, width: k.width, top: k.top },
      side: { left: s.left, width: s.width, top: s.top },
      keyItems: [...key.querySelectorAll('.feed-item .feed-title')].map(t => t.textContent),
      callout: side.querySelector('.callout h2')?.textContent ?? null,
      pageH2Left: box($('#module-head h2')).left,
    };
  }
  const watch = $('#overview-watch');
  if (watch) {
    seen.watch = {
      from: watch.querySelector('.from a')?.textContent ?? null,
      inSide: Boolean($('#overview-why .c10 #overview-watch')),
      entries: [...watch.querySelectorAll('.tl-i')].map(item => [item.querySelector('.tl-d').textContent, item.querySelector('.tl-t').textContent]),
      lanes: document.querySelectorAll('#content .event-lane, #content .lane').length,
    };
  }
  seen.tiles = [...document.querySelectorAll('#overview-modules .mt')].map(tile => [
    tile.querySelector('.mt-name').textContent,
    tile.querySelector('.mt-state')?.textContent ?? '',
    tile.querySelector('.mt-lead').textContent,
  ]);
  seen.limits = [...document.querySelectorAll('#overview-limitations li')].map(li => li.textContent);
  seen.chartIndexLinks = [...document.querySelectorAll('#content a')].filter(a => a.textContent === 'Chart index').length;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();

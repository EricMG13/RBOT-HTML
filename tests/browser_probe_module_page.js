(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('#head'); i++) await sleep(50);
  const de = document.documentElement, style = el => getComputedStyle(el), box = el => el.getBoundingClientRect();
  const font = el => el ? { size: style(el).fontSize, line: style(el).lineHeight, color: style(el).color, weight: style(el).fontWeight, width: box(el).width } : null;
  const text = el => el ? el.textContent.replace(/\s+/g, ' ').trim() : null;
  const seen = { width: innerWidth };
  const head = document.getElementById('head'), h2 = head?.querySelector('h2');
  if (head) {
    const link = head.querySelector('a[download]');
    seen.head = { h2: text(h2), size: style(h2).fontSize, transform: style(h2).textTransform, text: text(head), cls: head.className, download: link ? { href: link.getAttribute('href'), icon: link.querySelectorAll('svg,img').length, border: style(link).borderTopWidth } : null,
      tools: text(head.querySelector('.head-tools')), toolsRight: box(head.querySelector('.head-tools')).right, headRight: box(head).right };
  }
  const bl = document.getElementById('bottom-line');
  if (bl) {
    const first = bl.querySelector('p, li');
    seen.bottom = { text: text(bl), bg: style(bl).backgroundColor, first: font(first), firstText: text(first), ps: [...bl.querySelectorAll('p, li')].map(p => ({ size: style(p).fontSize, text: text(p) })),
      headings: [...bl.querySelectorAll('h3, h4, h5, h6')].map(h => ({ cls: h.className, text: text(h), srOnly: box(h).bottom <= 0 || box(h).width <= 1 })), band: bl.classList.contains('band'),
      lines: [...bl.querySelectorAll('dl .row')].map(r => ({ text: text(r), size: style(r).fontSize, line: style(r).lineHeight, color: style(r).color, label: style(r.querySelector('dt')).fontWeight })),
      badge: text(bl.querySelector('.badge')), badgeClass: bl.querySelector('.badge')?.className, link: text(bl.querySelector('.band-link')), linkBorder: bl.querySelector('.band-link') ? style(bl.querySelector('.band-link')).borderTopWidth : null };
  }
  const prose = document.querySelector('#content .analysis-text, #contrary-evidence .passage-text');
  seen.prose = font(prose);
  const kf = document.querySelector('#key-findings li');
  if (kf) { const dot = getComputedStyle(kf, '::before'); seen.keyItem = { size: style(kf).fontSize, dotWidth: dot.width, dotBg: dot.backgroundColor, list: style(kf.parentElement).listStyleType }; }
  const lim = document.querySelector('#limitations li, #limitations .passage-text, #limits p');
  if (lim) { const dot = getComputedStyle(lim, '::before'); seen.limit = { size: style(lim).fontSize, line: style(lim).lineHeight, color: style(lim).color, dotWidth: dot.width, dotBg: dot.backgroundColor }; }
  seen.cards = [...document.querySelectorAll('#content .panel-card')].map(c => ({ closed: c.closest('details:not([open])') !== null, height: box(c).height }));
  seen.folds = [...document.querySelectorAll('details.fold > summary, details.audit > summary')].map(s => ({ id: s.parentElement.id, display: style(s).display, radius: style(s.parentElement).borderTopLeftRadius, children: [...s.children].filter(c => c.tagName !== 'svg' && c.tagName !== 'IMG').map(text), text: text(s), border: style(s.parentElement).borderTopWidth }));
  seen.findings = [...document.querySelectorAll('article.finding')].map(a => ({ text: text(a), pills: a.querySelectorAll('.pill').length, basis: [...a.querySelectorAll('.basis-link')].map(b => ({ ...b.dataset })), cls: a.className }));
  const f0 = document.querySelector('article.finding');
  if (f0) { const h = f0.querySelector('h4'); seen.finding0 = { size: style(h).fontSize, line: style(h).lineHeight, weight: style(h).fontWeight, impact: font(f0.querySelector('.impact')), dotWidth: getComputedStyle(f0, '::before').width, dotBg: getComputedStyle(f0, '::before').backgroundColor, border: style(f0).borderTopWidth, impactLabelWeight: style(f0.querySelector('.impact b')).fontWeight }; }
  seen.fits = de.scrollWidth <= innerWidth;
  const inspector = document.getElementById('inspector');
  const read = () => {
    const fig = inspector.querySelector('.inspector-figure strong'), ctx = inspector.querySelector('.evidence-context'), card = inspector.querySelector('.evidence-fields > div');
    return { text: text(inspector), figure: fig ? { size: style(fig).fontSize, text: text(fig), before: !!(ctx.compareDocumentPosition(fig) & Node.DOCUMENT_POSITION_PRECEDING) } : null, hasFigure: !!inspector.querySelector('.inspector-figure'),
      context: ctx ? { size: style(ctx).fontSize, color: style(ctx).color } : null, card: card ? style(card).borderTopLeftRadius : null,
      h2: { text: text(inspector.querySelector('h2')), srOnly: box(inspector.querySelector('h2')).bottom <= 0 || box(inspector.querySelector('h2')).width <= 1 }, links: [...inspector.querySelectorAll('a')].map(a => a.getAttribute('href')), fits: de.scrollWidth <= innerWidth,
      excerptQuote: inspector.querySelector('.excerpt') ? { style: style(inspector.querySelector('.excerpt')).fontStyle, left: style(inspector.querySelector('.excerpt')).borderLeftWidth } : null };
  };
  const figure = document.querySelector('#content [data-paragraph][data-figure]');
  if (figure) { figure.click(); await sleep(300); seen.fromFigure = read(); document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); await sleep(200); }
  const chip = document.querySelector('#content .basis-link:not([data-figure]), #content .chip');
  if (chip) { chip.click(); await sleep(300); seen.fromChip = read(); }
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();

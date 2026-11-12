(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('header.issuer h1'); i++) await sleep(50);
  await sleep(400);
  const firstText = root => { const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {acceptNode: n =>
      n.textContent.trim() && n.parentElement.getBoundingClientRect().width ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT});
    const node = w.nextNode(); if (!node) return null; const r = document.createRange(); r.selectNodeContents(node);
    return r.getBoundingClientRect().left; };
  const inner = (el, side) => { const cs = getComputedStyle(el), b = el.getBoundingClientRect();
    return side === 'left' ? b.left + parseFloat(cs.paddingLeft) : b.right - parseFloat(cs.paddingRight); };
  const header = document.querySelector('header.issuer'), h1 = header.querySelector('h1');
  const seen = {h1Left: h1.getBoundingClientRect().left, headerRight: inner(header, 'right'),
    content: {left: firstText(document.getElementById('content')), right: inner(document.getElementById('content'), 'right')}};
  const head = document.getElementById('module-head');
  if (head.textContent.trim()) seen.head = {left: firstText(head), right: inner(head, 'right')};
  const browse = document.querySelector('.mobile-modules');
  if (browse && browse.getBoundingClientRect().width) { const bs = getComputedStyle(browse);
    seen.browse = {left: inner(browse, 'left'), paddingLeft: bs.paddingLeft, paddingRight: bs.paddingRight}; }
  seen.fits = document.documentElement.scrollWidth <= innerWidth;
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();

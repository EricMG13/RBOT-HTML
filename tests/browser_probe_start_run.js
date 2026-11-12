(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('header.issuer h1'); i++) await sleep(50);
  await sleep(300);
  const de = document.documentElement, box = el => el.getBoundingClientRect();
  const header = document.querySelector('header.issuer'), h1 = header.querySelector('h1');
  const links = [...header.querySelectorAll('a.start-run')], link = links[0];
  const seen = {
    inHeader: links.length, inDocument: document.querySelectorAll('a.start-run').length,
    inContent: document.querySelectorAll('#content a.start-run').length,
    inAnyFormOfTheClass: document.documentElement.outerHTML.includes('start-run'),
    fits: de.scrollWidth <= innerWidth, scrollWidth: de.scrollWidth, innerWidth,
  };
  if (link) {
    const a = box(link), t = box(h1), row = box(header.querySelector('.issuer-row'));
    Object.assign(seen, {
      text: link.textContent.trim(), href: link.getAttribute('href'), cls: link.className,
      icons: link.querySelectorAll('img').length,
      overlapsTitle: a.left < t.right && t.left < a.right && a.top < t.bottom && t.top < a.bottom,
      belowTitle: a.top >= t.bottom - 1, linkWidth: a.width, rowWidth: row.width, linkRight: a.right, rowRight: row.right,
    });
  }
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();

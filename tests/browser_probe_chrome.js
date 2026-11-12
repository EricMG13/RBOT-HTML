(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('#findings .basis-link'); i++) await sleep(50);
  const de = document.documentElement, style = el => getComputedStyle(el), box = el => el.getBoundingClientRect();
  const header = document.querySelector('header.issuer'), bar = document.getElementById('context-bar');
  const back = header.querySelector('a'), h1 = header.querySelector('h1'), code = bar.querySelector('.code');
  const all = bar.querySelector('a[href^="#W-Report/history"]');
  const item = document.querySelector('.module-item[aria-current]'), heading = document.querySelector('.nav-heading');
  const seen = {
    width: innerWidth,
    back: back ? { text: back.textContent.trim(), href: back.getAttribute('href') } : null,
    headerText: header.textContent, headerCodes: header.querySelectorAll('.code').length,
    h1Size: style(h1).fontSize, meta: header.querySelector('.issuer-meta')?.textContent ?? null,
    tabs: [...document.querySelectorAll('.workspace-tabs a')].map(a => ({ text: a.textContent.trim(), art: a.querySelectorAll('img,svg').length })),
    navWidth: box(document.getElementById('navigator')).width,
    headingTransform: style(heading).textTransform, headingSize: style(heading).fontSize,
    itemBackground: style(item).backgroundColor, itemWeight: style(item).fontWeight,
    allGap: box(bar).right - box(all).right, allText: all.textContent,
    codeTransform: style(code).textTransform, codeText: code.textContent,
    fits: de.scrollWidth <= innerWidth,
  };
  const chip = document.querySelector('#findings .basis-link');
  chip.click();
  await sleep(400);
  seen.inspectorWidth = box(document.getElementById('inspector')).width;
  seen.fitsOpen = de.scrollWidth <= innerWidth;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();

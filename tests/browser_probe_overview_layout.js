(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('#overview-lead'); i++) await sleep(50);
  await sleep(300);
  const $ = selector => document.querySelector(selector);
  const box = element => element.getBoundingClientRect();
  const style = (element, name) => getComputedStyle(element)[name];
  const de = document.documentElement;
  const main = $('.overview-main'), aside = $('.overview-aside');
  const seen = {
    hasMain: main !== null, hasAside: aside !== null,
    ids: [...document.querySelectorAll('#content [id^="overview-"]')].map(part => part.id),
    fits: de.scrollWidth <= window.innerWidth,
    viewport: window.innerWidth,
  };
  if (main && aside) {
    const m = box(main), a = box(aside);
    const pageH2 = $('#module-head h2');
    seen.pageH2Left = pageH2 && box(pageH2).left;
    seen.mainBox = { left: m.left, right: m.right, top: m.top, bottom: m.bottom };
    seen.asideBox = { left: a.left, right: a.right, top: a.top, bottom: a.bottom, width: a.width };
    seen.inMain = [...main.querySelectorAll('[id^="overview-"]')].map(part => part.id);
    seen.inAside = [...aside.querySelectorAll('[id^="overview-"]')].map(part => part.id);
    seen.asideLabel = aside.getAttribute('aria-label');
  }
  const lead = $('#overview-lead');
  if (lead) {
    const h2 = lead.querySelector('h2'), h3 = [...lead.querySelectorAll('h3')].find(h => h.textContent === 'Bottom line');
    const first = lead.querySelector('.reading-headline p, .reading-headline li, p.intro');
    seen.lead = {
      text: lead.textContent,
      h2: h2 && { text: h2.textContent, size: style(h2, 'fontSize'), transform: style(h2, 'textTransform') },
      h3Class: h3 ? h3.className : null,
      firstSize: first ? style(first, 'fontSize') : null,
      firstText: first ? first.textContent : null,
    };
  }
  const entry = $('.bottom-entry');
  seen.entries = [...document.querySelectorAll('.bottom-entry')].map(row => row.textContent);
  if (entry) seen.entryColumns = style(entry, 'gridTemplateColumns');
  seen.limits = [...document.querySelectorAll('#overview-limitations li')].map(li => li.textContent);
  const table = $('#overview-dates table.dates-table');
  if (table) {
    const thead = table.querySelector('thead'), row = table.querySelector('tbody tr');
    seen.dates = {
      caption: table.querySelector('caption') !== null,
      cols: table.querySelectorAll('th[scope="col"]').length,
      theadHeight: box(thead).height, theadDisplay: style(thead, 'display'),
      rowDisplay: row && style(row, 'display'),
      rowColumns: row && style(row, 'gridTemplateColumns'),
      rows: [...table.querySelectorAll('tbody tr')].map(r => r.textContent.trim()),
    };
  }
  const charts = $('#overview-charts');
  if (charts) {
    const link = [...charts.querySelectorAll('a')].find(a => a.textContent === 'Chart index');
    seen.charts = {
      href: link ? link.getAttribute('href') : null,
      cards: [...charts.querySelectorAll('.panel-card')].map(card => box(card).width),
    };
  }
  seen.chartIndexLinks = [...document.querySelectorAll('#content a')].filter(a => a.textContent === 'Chart index').length;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();

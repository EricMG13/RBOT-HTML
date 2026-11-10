(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.index-table'); i++) await sleep(50);
  const all = selector => [...document.querySelectorAll(selector)];
  const bar = document.getElementById('context-bar'), de = document.documentElement, content = document.getElementById('content');
  const pops = all('#context-bar details.context-pop');
  pops.forEach(pop => { pop.open = true; });
  const summary = pops.at(-1)?.querySelector('summary');
  if (summary) summary.focus();
  const list = pops.at(-1)?.querySelector('.context-list')?.getBoundingClientRect();
  const scroll = document.querySelector('.chart-index .table-scroll');
  const seen = {
    shown: !bar.hidden && bar.getBoundingClientRect().height > 0, text: bar.querySelector('.context-run')?.textContent,
    others: all('#context-bar details.context-pop a').filter(a => /-other/.test(a.getAttribute('href'))).map(a => a.getAttribute('href')),
    roles: all('#context-bar .context-role').map(r => r.dataset.role),
    indexRows: all('.index-table tbody tr').map(r => `${r.cells[0].textContent}|${r.cells[2].textContent}`), indexScrollFocusable: scroll?.getAttribute('tabindex') === '0',
    summaryFocus: Boolean(summary) && document.activeElement === summary, listInView: Boolean(list) && list.right <= innerWidth && list.bottom <= innerHeight,
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  };
  const link = bar.querySelector('[data-role="analysis"] a');
  if (link) { link.click(); await sleep(400); }
  seen.after = location.hash;
  seen.barAfter = !bar.hidden && Boolean(bar.querySelector('.context-run'));
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();

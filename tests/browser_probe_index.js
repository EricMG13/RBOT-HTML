(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.index-table, .overview-part'); i++) await sleep(50);
  const all = selector => [...document.querySelectorAll(selector)];
  const bar = document.getElementById('context-bar'), de = document.documentElement, content = document.getElementById('content');
  const scroll = document.querySelector('.chart-index .table-scroll');
  const history = bar.querySelector('a[href^="#W-Report/history"]');
  const seen = {
    shown: !bar.hidden && bar.getBoundingClientRect().height > 0, text: bar.querySelector('.context-run')?.textContent,
    historyHref: history?.getAttribute('href'), historyText: history?.textContent, popovers: all('#context-bar details').length,
    tabs: all('.workspace-tabs a').map(a => a.textContent.trim()), current: all('.workspace-tabs a[aria-current]').map(a => a.textContent.trim()),
    indexRows: all('.index-table tbody tr').map(r => `${r.cells[0].textContent}|${r.cells[2].textContent}`), indexScrollFocusable: scroll?.getAttribute('tabindex') === '0',
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  };
  if (history) { history.click(); await sleep(400); }
  seen.after = location.hash;
  seen.barOnHistory = bar.hidden;
  seen.historyRows = all('.history-table tbody tr').map(r => `${r.cells[0].textContent}|${r.getAttribute('aria-current')}`);
  seen.historyFits = de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();

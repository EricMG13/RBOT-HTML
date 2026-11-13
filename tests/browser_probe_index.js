(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.fc-card, .overview-part, .missing-state'); i++) await sleep(50);
  const all = selector => [...document.querySelectorAll(selector)];
  const bar = document.getElementById('context-bar'), de = document.documentElement, content = document.getElementById('content');
  const history = bar.querySelector('a[href^="#W-Report/history"]');
  const seen = {
    shown: !bar.hidden && bar.getBoundingClientRect().height > 0, text: bar.querySelector('.context-run')?.textContent,
    historyHref: history?.getAttribute('href'), historyText: history?.textContent, popovers: all('#context-bar details').length,
    tabs: all('.workspace-tabs a').map(a => a.textContent.trim()), current: all('.workspace-tabs a[aria-current]').map(a => a.textContent.trim()),
    // The run's charts are cards on the Forecast page: each one's title and the view it opens on.
    indexRows: all('.fc-card').map(card => `${card.querySelector('h3').textContent}|${card.dataset.view}`),
    indexScrollFocusable: all('.fc-card [data-pane="chart"] .fc-fig').length > 0 && all('.fc-card [data-pane="chart"] .fc-fig').every(f => f.getAttribute('tabindex') === '0'),
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  };
  if (history) { history.click(); await sleep(400); }
  seen.after = location.hash;
  seen.barOnHistory = bar.hidden;
  seen.historyRows = all('.tl-i').map(r => `${r.querySelector('.tl-d').textContent}|${r.getAttribute('aria-current')}`);
  seen.historyFits = de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.appendChild(out);
})();

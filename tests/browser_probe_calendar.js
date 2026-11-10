(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.event-lanes'); i++) await sleep(50);
  const all = selector => [...document.querySelectorAll(selector)];
  const first = document.querySelector('.lane-event');
  if (first) first.focus();
  const de = document.documentElement, content = document.getElementById('content');
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    lanes: all('.lane-row').length, points: all('.lane-event.point').length, spans: all('.lane-event.span').length,
    laneName: document.querySelector('.lane-name')?.textContent, tableRows: all('.event-table tbody tr').length,
    focusable: Boolean(first) && document.activeElement === first,
    tableAfterLanes: Boolean(document.querySelector('.lane-row') && document.querySelector('.event-table')) && Boolean(document.querySelector('.lane-row').compareDocumentPosition(document.querySelector('.event-table')) & Node.DOCUMENT_POSITION_FOLLOWING),
    tabs: all('.workspace-tabs a[aria-current]').map(a => a.textContent.trim()),
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  });
  document.body.appendChild(out);
})();

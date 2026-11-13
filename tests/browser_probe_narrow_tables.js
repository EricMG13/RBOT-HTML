// Narrow-page check (W1). Headless Chrome will not open a window below 500px, so the content column is set to 340px (a 375px phone's
// width less its padding); the page must not widen, and every table must sit in a focusable scroll region that holds its own overflow.
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.dates-table, .history-table, .ev-tbl table'); i++) await sleep(50);
  const de = document.documentElement, content = document.getElementById('content');
  content.style.width = '340px'; content.style.maxWidth = '340px'; content.style.minWidth = '0';
  await sleep(100);
  const tables = [...document.querySelectorAll('.dates-table, .history-table, .ev-tbl table')];
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    pageFits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
    tables: tables.length,
    inRegion: tables.filter(t => {
      const region = t.parentElement;
      return (region.classList.contains('table-scroll') || region.classList.contains('ev-tbl')) && region.getAttribute('role') === 'region' && region.getAttribute('tabindex') === '0' && !!region.getAttribute('aria-label');
    }).length,
    scrolling: tables.filter(t => t.parentElement.scrollWidth > t.parentElement.clientWidth).length,
  });
  document.body.append(out);
})();

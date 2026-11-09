(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('#analysis .table-card'); i++) await sleep(50);
  const content = document.getElementById('content'), de = document.documentElement;
  const tables = [...document.querySelectorAll('#analysis .table-card')];
  // A card is never wider than the analysis part; a wide table scrolls inside it.
  const part = document.getElementById('analysis').getBoundingClientRect();
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    pageFits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
    tablesInCards: tables.every(t => t.getBoundingClientRect().right <= part.right + 1),
    tables: tables.length,
    registerScrollsInside: tables.some(t => t.scrollWidth > t.clientWidth),
  });
  document.body.append(out);
})();

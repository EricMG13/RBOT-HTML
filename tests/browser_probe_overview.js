(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.summary-chart .chart-row'); i++) await sleep(50);
  // The real library lays out three 349px cards at 1440; the fixture has fewer, so force that card width to measure the tightest case.
  for (const grid of document.querySelectorAll('.summary-charts')) grid.style.gridTemplateColumns = 'repeat(3, 349px)';
  const rows = [...document.querySelectorAll('.summary-chart .chart-row strong')];
  const content = document.getElementById('content');
  const inside = rows.every(s => {
    const card = s.closest('.summary-chart').getBoundingClientRect(), box = s.getBoundingClientRect();
    return box.right <= card.right && box.left >= card.left;
  });
  const de = document.documentElement;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    rows: rows.length, valueInCard: inside,
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  });
  document.body.append(out);
})();

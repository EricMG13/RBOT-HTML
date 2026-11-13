(async () => {
  // The period labels of a Forecast chart card: no two draw over each other, and a chart wider than
  // its card scrolls in its own focusable region instead of widening the card or the page.
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('.fc-card .column-chart .chart-label'); i++) await sleep(50);
  await sleep(300);
  const labels = [...document.querySelectorAll('.fc-card .column-chart .chart-label')].map(el => el.getBoundingClientRect());
  const crossing = [];
  labels.forEach((a, i) => labels.slice(i + 1).forEach((b, j) => {
    if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) crossing.push([i, i + 1 + j]);
  }));
  const region = document.querySelector('.fc-card .column-chart').closest('.fc-fig');
  const card = region.closest('.fc-card');
  const seen = {labels: labels.length, crossing, fits: document.documentElement.scrollWidth <= innerWidth,
    chartScrolls: region.scrollWidth > region.clientWidth, regionFocusable: region.getAttribute('tabindex') === '0',
    regionInsideCard: region.getBoundingClientRect().right <= card.getBoundingClientRect().right + 1};
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();

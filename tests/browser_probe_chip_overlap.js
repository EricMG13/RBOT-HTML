(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('#overview-charts .chip-count'); i++) await sleep(50);
  await sleep(300);
  const chips = [...document.querySelectorAll('.overview-aside .chip-count')].map(el => el.getBoundingClientRect());
  const crossing = [];
  chips.forEach((a, i) => chips.slice(i + 1).forEach((b, j) => {
    if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) crossing.push([i, i + 1 + j]);
  }));
  const chart = document.querySelector('.overview-aside .column-chart');
  const seen = {chips: chips.length, crossing, fits: document.documentElement.scrollWidth <= innerWidth,
    chartScrolls: chart.scrollWidth > chart.clientWidth, chartInsideAside: chart.getBoundingClientRect().right <=
      document.querySelector('.overview-aside').getBoundingClientRect().right + 1};
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();

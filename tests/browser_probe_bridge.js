(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.story-module .vector-chart'); i++) await sleep(50);
  const chart = document.querySelector('.story-module .vector-chart');
  const card = chart?.closest('.panel-card');
  const form = card?.querySelector('details.chart-table');
  const de = document.documentElement, content = document.getElementById('content');
  const boxes = chart ? [...chart.querySelectorAll('rect')].map(r => r.getBoundingClientRect()) : [];
  const frame = chart ? chart.getBoundingClientRect() : null;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    title: card?.querySelector('h4')?.textContent,
    points: chart ? chart.querySelectorAll('a.plot-point').length : 0,
    totals: chart ? chart.querySelectorAll('rect.total').length : 0,
    outflows: chart ? chart.querySelectorAll('rect.outflow').length : 0,
    barsInside: boxes.length > 0 && boxes.every(b => b.left >= frame.left - 1 && b.right <= frame.right + 1),
    formRows: form ? form.querySelectorAll('tbody tr').length : 0,
    formHidden: form ? !form.open : null,
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  });
  document.body.appendChild(out);
})();

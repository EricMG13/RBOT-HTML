(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.story-module .limits-chart'); i++) await sleep(50);
  const story = document.querySelector('.limits-chart')?.closest('.story-module');
  const count = selector => story ? story.querySelectorAll(selector).length : 0;
  const de = document.documentElement, content = document.getElementById('content');
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    segments: count('.stack-seg'), bulletRows: count('.bullet-row'), limitRows: count('.limit-row'),
    markers: count('.bullet-row .marker'), ticks: count('.bullet-row .tick, .limit-row .tick'),
    forms: count('details.chart-table'), formsClosed: story ? [...story.querySelectorAll('details.chart-table')].every(d => !d.open) : false,
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  });
  document.body.appendChild(out);
})();

(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.story-module .chart-row'); i++) await sleep(50);
  const rows = [...document.querySelectorAll('.story-module .panel-card .chart-row strong')];
  const content = document.getElementById('content');
  const inside = rows.every(s => {
    const card = s.closest('.panel-card').getBoundingClientRect(), box = s.getBoundingClientRect();
    return box.right <= card.right && box.left >= card.left;
  });
  const register = [...document.querySelectorAll('table.register tbody tr[data-group]')];
  const shown = () => register.filter(row => !row.hidden).length;
  const before = shown(), established = register.filter(row => row.dataset.established === 'true').length;
  const box = document.getElementById('register-all');
  box.checked = true;
  box.dispatchEvent(new Event('change', { bubbles: true }));
  const after = shown();
  const de = document.documentElement;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    rows: rows.length, valueInCard: inside,
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
    before, after, established, total: register.length,
  });
  document.body.append(out);
})();

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
  // Untick the box and filter to the group of a not-assessable row: when none is shown the "No findings match" row is.
  const hidden = register.find(row => row.dataset.established === 'false');
  const empty = document.querySelector('table.register tr.register-empty');
  const emptyBefore = !empty.hidden;
  box.checked = false;
  const group = document.getElementById('register-group');
  group.value = hidden.dataset.group;
  group.dispatchEvent(new Event('change', { bubbles: true }));
  const filtered = { shown: shown(), emptyShown: !empty.hidden };
  // Design pass: the navigator lists the report's parts and a click scrolls to one; the tables do not scroll on their own; prose cells are not monospace; coverage cells keep codes.
  const outline = [...document.querySelectorAll('#module-list .section-outline a')];
  const scrollers = [...document.querySelectorAll('.run-section .table-scroll')].filter(box => box.scrollHeight > box.clientHeight + 1).length;
  const monoProse = [...content.querySelectorAll('td')].filter(td => /Mono/.test(getComputedStyle(td).fontFamily) && td.textContent.trim().split(/\s+/).length > 6).length;
  const coverage = [...document.querySelectorAll('.coverage .cov')].map(a => a.textContent);
  outline.find(a => a.textContent === 'Module matrix').click();
  await sleep(200);
  const matrix = document.getElementById('run-matrix').getBoundingClientRect(), frame = content.getBoundingClientRect();
  const jump = { hash: location.hash.split('?')[0], current: [...document.querySelectorAll('#module-list [aria-current="location"]')].map(a => a.textContent), inView: matrix.top >= frame.top && matrix.top < frame.bottom };
  const de = document.documentElement;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    rows: rows.length, valueInCard: inside,
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
    before, after, established, total: register.length, emptyBefore, filtered,
    outline: outline.map(a => a.textContent), scrollers, monoProse, coverage, jump,
  });
  document.body.append(out);
})();

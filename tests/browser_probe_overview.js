(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.overview-part'); i++) await sleep(50);
  const content = document.getElementById('content'), de = document.documentElement;
  const shown = id => getComputedStyle(document.getElementById(id)).display !== 'none';
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    parts: [...document.querySelectorAll('.overview-part')].map(part => part.id),
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
    navigatorShown: shown('navigator'), moduleToggleShown: shown('module-toggle'),
    outline: document.querySelectorAll('#module-list .section-outline').length,
    dates: [...document.querySelectorAll('.dates-table tbody tr')].map(row => row.textContent.trim()),
    lead: document.querySelector('#overview-lead').textContent,
    bottomLines: [...document.querySelectorAll('.bottom-entry')].map(entry => entry.querySelector('h3').textContent.trim()),
  });
  document.body.append(out);
})();

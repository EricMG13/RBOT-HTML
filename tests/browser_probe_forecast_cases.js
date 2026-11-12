(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.forecast-cashflow table.cashflow'); i++) await sleep(50);
  const main = '.forecast-cashflow > .table-scroll';
  const text = els => [...els].map(x => x.textContent);
  const details = document.querySelector('details.cashflow-other');
  const pf = document.querySelector(`${main} tbody tr:not(.band-row)`)?.querySelectorAll('td')[8];
  const seen = {
    groups: text(document.querySelectorAll(`${main} thead tr:first-child th[scope=colgroup]`)),
    summary: document.querySelector('details.cashflow-other summary')?.textContent ?? null,
    otherGroups: details ? details.querySelectorAll('table.cashflow thead tr:first-child th[scope=colgroup]').length : 0,
    otherOpen: details ? details.open : null,
    otherName: details?.querySelector('[role=region]')?.getAttribute('aria-label') ?? null,
    pf: pf ? { text: pf.textContent, label: pf.getAttribute('aria-label') } : null,
    ids: document.querySelectorAll('[id]').length === new Set([...document.querySelectorAll('[id]')].map(x => x.id)).size,
  };
  if (details) details.open = true;
  await sleep(200);
  seen.fits = document.documentElement.scrollWidth <= window.innerWidth;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();

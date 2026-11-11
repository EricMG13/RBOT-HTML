(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const seen = {};
  const within = selector => [...document.querySelectorAll(selector)].every(s => {
    const card = s.closest('.panel-card').getBoundingClientRect(), box = s.getBoundingClientRect();
    return box.right <= card.right && box.left >= card.left;
  });
  const inside = () => within('.chart-row strong');
  const measure = name => {
    const de = document.documentElement;
    seen[name] = {fits: de.scrollWidth <= de.clientWidth && document.getElementById('content').scrollWidth <= document.getElementById('content').clientWidth, valueInCard: inside(), chipsInCard: within('.chart-row .chip'), rows: document.querySelectorAll('.chart-row').length};
  };
  for (let i = 0; i < 200 && !document.querySelector('#findings .basis-link'); i++) await sleep(50);
  measure('closed');
  const rowButton = document.querySelector('#numbers .chart-open');
  rowButton.focus();
  const box = rowButton.getBoundingClientRect();
  seen.rowFocus = {focused: document.activeElement === rowButton, box: box.width > 0 && box.height > 0};
  // A finding's citations sit behind its Basis button (decision 14, H7); activating it opens the inspector on the page it cites.
  const chip = document.querySelector('#findings .basis-link');
  chip.focus();
  chip.click();
  await sleep(300);
  const inspector = document.getElementById('inspector');
  seen.open = {
    hidden: inspector.hidden, excerpt: inspector.querySelector('.excerpt')?.textContent ?? null,
    mark: inspector.querySelector('.excerpt mark')?.textContent ?? null, text: inspector.textContent,
    pressed: chip.getAttribute('aria-pressed'), focusInInspector: inspector.contains(document.activeElement),
    hash: location.hash, open: inspector.querySelector('a.btn')?.getAttribute('href') ?? null,
  };
  measure('inspector');
  document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
  await sleep(300);
  seen.escaped = {hidden: inspector.hidden, focusOnChip: document.activeElement === chip, hash: location.hash};
  const link = [...document.querySelectorAll('a.section-item')].find(a => a.textContent === 'Key numbers');
  link.click();
  await sleep(300);
  seen.anchor = {hash: location.hash, current: document.querySelector('a.section-item[aria-current]')?.textContent, chipStillThere: document.body.contains(chip)};
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();

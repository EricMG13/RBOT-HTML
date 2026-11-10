(async () => {
  // Reads a route into the module page: which fold opened, where the section sits, and where focus returns after Esc.
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const content = document.getElementById('content'), de = document.documentElement, seen = {};
  for (let i = 0; i < 200 && !document.getElementById('reference'); i++) await sleep(50);
  await sleep(300);
  const reference = document.getElementById('reference');
  const wanted = (location.hash.match(/\/(s-\d+)/) || [])[1], target = wanted && document.getElementById(wanted);
  const view = content.getBoundingClientRect();
  seen.referenceOpen = reference.open;
  seen.target = wanted ? { found: Boolean(target), inReference: Boolean(target && reference.contains(target)) } : null;
  if (target) {
    const box = target.getBoundingClientRect();
    seen.target.topInside = box.top >= view.top - 1 && box.top < view.bottom;
  }
  seen.inspectorHidden = document.getElementById('inspector').hidden;
  if (!seen.inspectorHidden) {
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await sleep(300);
    const focused = document.activeElement;
    seen.escaped = { hidden: document.getElementById('inspector').hidden, onChip: Boolean(focused && focused.classList.contains('chip') && reference.contains(focused)), key: focused && focused.dataset.evidence };
  }
  // With every fold open, the page still fits the canvas.
  for (const fold of document.querySelectorAll('details.fold, details.audit')) fold.open = true;
  await sleep(200);
  seen.fits = de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth;
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();

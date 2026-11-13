(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const seen = {};
  // The Basis control of the UNKEYED paragraph in Analysis (two citations with no page), not the first control on the page.
  const unkeyed = () => [...document.querySelectorAll('#analysis .analysis-text')].find(p => p.textContent.includes('The figure is printed in Z'))?.querySelector('.basis-link');
  for (let i = 0; i < 200 && !unkeyed(); i++) await sleep(50);
  const control = unkeyed();
  // The control is an icon button: its name is its aria-label, not text.
  seen.control = control ? control.getAttribute('aria-label') : null;
  seen.verified = document.querySelectorAll('.chip.verified').length;
  seen.proseChips = document.querySelectorAll('#analysis .chip, #analysis .chip-count').length;
  if (control) {
    control.focus();
    control.click();
    await sleep(300);
    const inspector = document.getElementById('inspector');
    seen.open = {hidden: inspector.hidden, items: inspector.querySelectorAll('.chip-source').length, hash: location.hash, focusInInspector: inspector.contains(document.activeElement), pressed: control.getAttribute('aria-pressed')};
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
    await sleep(300);
    seen.escaped = {hidden: inspector.hidden, focusOnControl: document.activeElement === control, hash: location.hash};
  }
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();

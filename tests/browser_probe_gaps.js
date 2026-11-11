(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const seen = {};
  // The count under the UNKEYED paragraph in Analysis (two citations), not the first count on the page (a finding row with one).
  // Earlier-format chips sit behind the paragraph's Basis control (the disclosure after it); the reader opens it first.
  const unkeyed = () => [...document.querySelectorAll('#analysis .analysis-text')].find(p => p.textContent.includes('The figure is printed in Z'))?.nextElementSibling;
  for (let i = 0; i < 200 && !unkeyed(); i++) await sleep(50);
  const fold = unkeyed();
  if (fold) fold.open = true;
  const count = fold?.querySelector('.chip-count');
  seen.count = count ? count.textContent : null;
  seen.verified = document.querySelectorAll('.chip.verified').length;
  seen.singleGaps = [...document.querySelectorAll('.chip.gap')].filter(c => !/Not supplied/.test(c.textContent)).length;
  if (count) {
    const expected = Number(count.textContent.match(/^\d+/)[0]);
    count.focus();
    count.click();
    await sleep(300);
    const inspector = document.getElementById('inspector');
    seen.open = {hidden: inspector.hidden, items: inspector.querySelectorAll('.chip-source').length, expected, hash: location.hash, focusInInspector: inspector.contains(document.activeElement)};
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
    await sleep(300);
    seen.escaped = {hidden: inspector.hidden, focusOnCount: document.activeElement === count, hash: location.hash};
  }
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify(seen);
  document.body.append(out);
})();

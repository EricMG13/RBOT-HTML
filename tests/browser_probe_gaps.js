(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const seen = {};
  for (let i = 0; i < 200 && !document.querySelector('.chip-count'); i++) await sleep(50);
  const count = document.querySelector('.chip-count');
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

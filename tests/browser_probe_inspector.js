(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('#content [data-paragraph]'); i++) await sleep(50);
  const inspector = document.getElementById('inspector');
  const seen = [];
  // Every paragraph control on the page: open the inspector from it and read the Basis items it draws.
  for (const control of [...document.querySelectorAll('#content [data-paragraph]')]) {
    control.focus();
    control.click();
    await sleep(100);
    seen.push({
      key: control.dataset.paragraph,
      figure: control.dataset.figure ?? null,
      hidden: inspector.hidden,
      items: [...inspector.querySelectorAll('.basis-items > li')].map(li => ({
        text: li.textContent,
        links: [...li.querySelectorAll('a')].map(a => a.getAttribute('href')),
        cells: [...li.querySelectorAll('dl dt, dl dd')].map(cell => cell.textContent),
      })),
    });
    document.activeElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
    await sleep(100);
  }
  const pre = document.createElement('pre');
  pre.id = 'probe';
  pre.textContent = JSON.stringify(seen);
  document.body.append(pre);
})();

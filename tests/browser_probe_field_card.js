(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector('#content .basis-link'); i++) await sleep(50);
  document.querySelector('#content .basis-link:not([data-figure])').click();
  await sleep(400);
  const card = document.querySelector('.inspector-body .evidence-fields > div'), cs = getComputedStyle(card);
  const body = document.querySelector('.inspector-body'), bs = getComputedStyle(body);
  const seen = {padding: cs.padding, borderLeft: cs.borderLeftWidth, display: cs.display, columns: cs.gridTemplateColumns.split(' ')[0],
    valueWidth: card.querySelector(':scope > div').getBoundingClientRect().width,
    bodyContent: body.clientWidth - parseFloat(bs.paddingLeft) - parseFloat(bs.paddingRight)};
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();

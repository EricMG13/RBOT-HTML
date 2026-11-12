(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 200 && !document.querySelector(PROBE.figure); i++) await sleep(50);
  const style = sel => { const cs = getComputedStyle(document.querySelector(sel));
    return {family: cs.fontFamily, size: cs.fontSize, weight: cs.fontWeight, color: cs.color, decoration: cs.textDecorationStyle}; };
  const seen = {figure: style(PROBE.figure), basis: style(PROBE.basis)};
  const out = document.createElement('pre'); out.id = 'probe';
  out.textContent = JSON.stringify(seen); document.body.appendChild(out);
})();

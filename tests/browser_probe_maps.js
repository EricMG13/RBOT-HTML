(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.map-card svg'); i++) await sleep(50);
  const all = selector => [...document.querySelectorAll(selector)];
  const scroll = document.querySelector('.map-scroll');
  if (scroll) scroll.focus();
  const de = document.documentElement, content = document.getElementById('content');
  const svg = document.querySelector('.map-card svg'), table = document.querySelector('.map-table');
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    nodes: all('.map-node').length, edges: all('.map-edge').length, labels: all('.map-edge-label').length,
    cutEdges: all('.map-edge.cut').length, tableRows: all('.map-table tbody tr').length,
    scrollFocusable: Boolean(scroll) && document.activeElement === scroll,
    tableAfterDiagram: Boolean(svg && table) && Boolean(svg.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING),
    statusItems: all('.status-item').length,
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  });
  document.body.appendChild(out);
})();

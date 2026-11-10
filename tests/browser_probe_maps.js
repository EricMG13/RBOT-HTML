(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 200 && !document.querySelector('.map-card svg'); i++) await sleep(50);
  const all = selector => [...document.querySelectorAll(selector)];
  const scroll = document.querySelector('.map-card .map-scroll');
  if (scroll) scroll.focus();
  const de = document.documentElement, content = document.getElementById('content');
  const svg = document.querySelector('.map-card svg'), table = document.querySelector('.map-card .map-table');
  const out = document.createElement('pre');
  out.id = 'probe';
  out.textContent = JSON.stringify({
    nodes: all('.map-card .map-node').length, edges: all('.map-card .map-edge').length, labels: all('.map-card .map-edge-label').length,
    cutEdges: all('.map-card .map-edge.cut').length, tableRows: all('.map-card .map-table tbody tr').length,
    scrollFocusable: Boolean(scroll) && document.activeElement === scroll,
    tableAfterDiagram: Boolean(svg && table) && Boolean(svg.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING),
    wide: Boolean(svg && scroll) && svg.getBoundingClientRect().width > scroll.clientWidth,
    scrolls: Boolean(scroll) && scroll.scrollWidth > scroll.clientWidth,
    statusNodes: all('.status-map .map-node').length, statusStates: all('.status-map .map-state').length,
    statusItems: all('.status-item').length,
    fits: de.scrollWidth <= de.clientWidth && content.scrollWidth <= content.clientWidth,
  });
  document.body.appendChild(out);
})();

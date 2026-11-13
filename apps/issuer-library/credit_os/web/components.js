'use strict';
// Components: one function per component, each turning data into markup (or, for the toast and the pill, acting on the page).
// Classic script: sets window.Components, and module.exports where `module` exists (the node tests), the way reader.js and shapes.js do.
// No state is shared between components except the toast host.
(() => {
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

  // The inner markup of the SVG files in web/icons/ (a test compares this table with the files), so the page can draw them inline without fetching.
  // `trace` is the layers icon: the one mark for "show where this comes from".
  const ICON_PATHS = {
    "activity": "<path d=\"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2\" />",
    "arrow-left": "<path d=\"m12 19-7-7 7-7\" /><path d=\"M19 12H5\" />",
    "arrow-right": "<path d=\"M5 12h14\" /><path d=\"m12 5 7 7-7 7\" />",
    "calendar-days": "<path d=\"M8 2v3\" /><path d=\"M16 2v3\" /><rect x=\"3\" y=\"3\" width=\"18\" height=\"18\" rx=\"2\" /><path d=\"M3 9h18\" /><path d=\"M8 13h.01\" /><path d=\"M12 13h.01\" /><path d=\"M16 13h.01\" /><path d=\"M8 17h.01\" /><path d=\"M12 17h.01\" /><path d=\"M16 17h.01\" />",
    "chart-no-axes-combined": "<path d=\"M12 16v5\" /><path d=\"M16 14.639V21\" /><path d=\"M20 10.656V21\" /><path d=\"m22 3-8.646 8.646a.5.5 0 0 1-.708 0L9.354 8.354a.5.5 0 0 0-.707 0L2 15\" /><path d=\"M4 18.463V21\" /><path d=\"M8 14.656V21\" />",
    "check": "<path d=\"M20 6 9 17l-5-5\" />",
    "chevron-down": "<path d=\"m6 9 6 6 6-6\" />",
    "chevron-right": "<path d=\"m9 18 6-6-6-6\" />",
    "circle-check": "<circle cx=\"12\" cy=\"12\" r=\"10\" /><path d=\"m9 12 2 2 4-4\" />",
    "download": "<path d=\"M12 15V3\" /><path d=\"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4\" /><path d=\"m7 10 5 5 5-5\" />",
    "file-text": "<path d=\"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z\" /><path d=\"M14 2v5a1 1 0 0 0 1 1h5\" /><path d=\"M10 9H8\" /><path d=\"M16 13H8\" /><path d=\"M16 17H8\" />",
    "files": "<path d=\"M15 2h-4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8\" /><path d=\"M16.706 2.706A2.4 2.4 0 0 0 15 2v5a1 1 0 0 0 1 1h5a2.4 2.4 0 0 0-.706-1.706z\" /><path d=\"M5 7a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 1.732-1\" />",
    "folder-open": "<path d=\"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2\" />",
    "git-compare": "<circle cx=\"18\" cy=\"18\" r=\"3\" /><circle cx=\"6\" cy=\"6\" r=\"3\" /><path d=\"M13 6h3a2 2 0 0 1 2 2v7\" /><path d=\"M11 18H8a2 2 0 0 1-2-2V9\" />",
    "layers": "<path d=\"M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z\" /><path d=\"M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12\" /><path d=\"M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17\" />",
    "layout-grid": "<rect width=\"7\" height=\"7\" x=\"3\" y=\"3\" rx=\"1\" /><rect width=\"7\" height=\"7\" x=\"14\" y=\"3\" rx=\"1\" /><rect width=\"7\" height=\"7\" x=\"14\" y=\"14\" rx=\"1\" /><rect width=\"7\" height=\"7\" x=\"3\" y=\"14\" rx=\"1\" />",
    "panel-left": "<rect width=\"18\" height=\"18\" x=\"3\" y=\"3\" rx=\"2\" /><path d=\"M9 3v18\" />",
    "plus": "<path d=\"M5 12h14\" /><path d=\"M12 5v14\" />",
    "refresh-cw": "<path d=\"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8\" /><path d=\"M21 3v5h-5\" /><path d=\"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16\" /><path d=\"M8 16H3v5\" />",
    "search": "<path d=\"m21 21-4.34-4.34\" /><circle cx=\"11\" cy=\"11\" r=\"8\" />",
    "settings-2": "<path d=\"M14 17H5\" /><path d=\"M19 7h-9\" /><circle cx=\"17\" cy=\"17\" r=\"3\" /><circle cx=\"7\" cy=\"7\" r=\"3\" />",
    "triangle-alert": "<path d=\"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3\" /><path d=\"M12 9v4\" /><path d=\"M12 17h.01\" />",
    "x": "<path d=\"M18 6 6 18\" /><path d=\"m6 6 12 12\" />",
    "trace": "<path d=\"M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z\" /><path d=\"M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12\" /><path d=\"M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17\" />"
  };

  // C-icon: inline SVG that takes the text colour of its parent and is hidden from assistive technology (the control carries the name).
  function icon(name) {
    if (!Object.hasOwn(ICON_PATHS, name)) throw new Error(`Components.icon: no icon named ${name}`);
    return `<svg class="i" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${ICON_PATHS[name]}</svg>`;
  }

  // C22 opener: the trace icon of a paragraph, a figure group or a table row. 24px hit area, 16px mark. `items` are the raw Basis references the
  // control carries (reader.js paragraphView); the data attributes are the ones the click handler and the inspector read.
  function traceButton(key, label, items = []) {
    return `<button type="button" class="basis-link" data-paragraph="${escapeHtml(key)}" data-basis="${escapeHtml(JSON.stringify(items))}" aria-label="${escapeHtml(label)}">${icon('trace')}</button>`;
  }

  // The same icon for a table row whose evidence is opened by key (no Basis items): the control that stood as the "Row" chip.
  function traceRow(key, label, title = label) {
    return `<button type="button" class="basis-link trace-row" data-evidence="${escapeHtml(key)}" title="${escapeHtml(title)}" aria-label="${escapeHtml(label)}">${icon('trace')}</button>`;
  }

  // C1: header chips under the issuer name. `chips` is [{text, tone?: 'amber', href?}]; a chip with an href is a link.
  function chip({text, tone, href}) {
    const cls = `hchip${tone ? ` ${tone}` : ''}`;
    return href ? `<a class="${cls}" href="${escapeHtml(href)}">${escapeHtml(text)}</a>` : `<span class="${cls}">${escapeHtml(text)}</span>`;
  }
  function headerChips(chips) {
    const shown = chips.filter(c => c && c.text);
    return shown.length ? `<p class="hchips">${shown.map(chip).join('')}</p>` : '';
  }

  // C1: the sliding pill of the run tabs. One pill is drawn by CSS from three custom properties on the container; the container keeps them
  // between routes, so the pill glides from the old tab to the new one. Without a measured tab there is no pill and CSS shows the plain active state.
  function placePill(container) {
    const active = container.querySelector('[aria-current]');
    if (!active || !active.offsetWidth) { container.classList.remove('has-pill'); return false; }
    container.style.setProperty('--pill-x', `${active.offsetLeft}px`);
    container.style.setProperty('--pill-w', `${active.offsetWidth}px`);
    container.style.setProperty('--pill-h', `${active.offsetHeight}px`);
    container.style.setProperty('--pill-y', `${active.offsetTop}px`);
    container.classList.add('has-pill');
    return true;
  }

  // C23: one status host fixed bottom-right; each message removes itself after 3 seconds.
  const TOAST_MS = 3000;
  function toast(text) {
    let host = document.getElementById('toast-host');
    if (!host) {
      host = document.createElement('div');
      host.id = 'toast-host';
      host.className = 'toast-host';
      host.setAttribute('role', 'status');
      document.body.append(host);
    }
    const message = document.createElement('p');
    message.className = 'toast';
    message.textContent = text;
    host.append(message);
    setTimeout(() => message.remove(), TOAST_MS);
  }

  // C24: a control that names itself by `data-tip` always also carries the same text as its accessible name; the bubble is CSS only.
  function tipAttributes(text) {
    return `data-tip="${escapeHtml(text)}" aria-label="${escapeHtml(text)}"`;
  }

  const Components = {icon, traceButton, traceRow, headerChips, placePill, toast, tipAttributes, ICON_PATHS};
  if (typeof window !== 'undefined') window.Components = Components;
  if (typeof module !== 'undefined') module.exports = Components;
})();

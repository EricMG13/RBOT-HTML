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
    "copy": "<rect width=\"14\" height=\"14\" x=\"8\" y=\"8\" rx=\"2\" ry=\"2\" /><path d=\"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2\" />",
    "chevron-down": "<path d=\"m6 9 6 6 6-6\" />",
    "chevron-right": "<path d=\"m9 18 6-6-6-6\" />",
    "circle-check": "<circle cx=\"12\" cy=\"12\" r=\"10\" /><path d=\"m9 12 2 2 4-4\" />",
    "download": "<path d=\"M12 15V3\" /><path d=\"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4\" /><path d=\"m7 10 5 5 5-5\" />",
    "file-text": "<path d=\"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z\" /><path d=\"M14 2v5a1 1 0 0 0 1 1h5\" /><path d=\"M10 9H8\" /><path d=\"M16 13H8\" /><path d=\"M16 17H8\" />",
    "files": "<path d=\"M15 2h-4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V8\" /><path d=\"M16.706 2.706A2.4 2.4 0 0 0 15 2v5a1 1 0 0 0 1 1h5a2.4 2.4 0 0 0-.706-1.706z\" /><path d=\"M5 7a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h8a2 2 0 0 0 1.732-1\" />",
    "folder-open": "<path d=\"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2\" />",
    "git-compare": "<circle cx=\"18\" cy=\"18\" r=\"3\" /><circle cx=\"6\" cy=\"6\" r=\"3\" /><path d=\"M13 6h3a2 2 0 0 1 2 2v7\" /><path d=\"M11 18H8a2 2 0 0 1-2-2V9\" />",
    "info": "<circle cx=\"12\" cy=\"12\" r=\"10\" /><path d=\"M12 16v-4\" /><path d=\"M12 8h.01\" />",
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
  // The host is made empty at load (and on first use if it was not), so a screen reader already watches it when the first message arrives.
  function toastHost() {
    let host = document.getElementById('toast-host');
    if (!host) {
      host = document.createElement('div');
      host.id = 'toast-host';
      host.className = 'toast-host';
      host.setAttribute('role', 'status');
      document.body.append(host);
    }
    return host;
  }
  function toast(text) {
    const host = toastHost();
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

  // ---- The module page (Task 4). The text helpers are reader.js's: node requires the file, the page already holds its globals.
  const readerText = () => (typeof module !== 'undefined' ? require('./reader.js') : {richText, figureSpans, figuredHtml, paragraphBody, chartNumber, plainText, numericColumn});
  const shapes = () => (typeof module !== 'undefined' ? require('./shapes.js') : window.Shapes);
  // One paragraph of a passage: its body as read (Basis line, list marker and line breaks gone) and `show(from, to)`, the inline HTML of a stretch of it.
  // A figure is the page's own control when `figure(line, index, text)` gives one, else its exact text.
  function prose(entry, figure) {
    const reader = readerText();
    const {body} = reader.paragraphBody(entry.text);
    const figures = reader.figureSpans(body);
    const show = (from, to) => reader.figuredHtml(body, figures, from, to, (i, text) => (figure && figure(entry.line, i, text)) || escapeHtml(text));
    return {body, show};
  }
  const paragraphs = (texts, figure) => texts.map(entry => ({entry, ...prose(entry, figure)})).filter(p => p.body.trim() !== '');
  const traceOf = (trace, entry) => (trace ? trace(entry.line) : '');
  // A sentence ends at ". " before a capital letter or at the end of the text; the first one is whole, never cut.
  function firstSentence(body) {
    const end = /\.\s+(?=[A-Z])/.exec(body);
    return end ? {lead: [0, end.index + 1], rest: [end.index + end[0].length, body.length]} : {lead: [0, body.length], rest: [body.length, body.length]};
  }

  // C2: the Bottom line. The first sentence of the first paragraph is the large lead; what follows is at body size, a trace button ends each paragraph.
  function verdictPanel(texts, trace, figure) {
    const [first, ...later] = paragraphs(texts, figure);
    if (!first) return '';
    const cut = firstSentence(first.body), hasRest = cut.rest[1] > cut.rest[0];
    const row = (inner, entry) => `<div class="row-end"><p class="verdict-body">${inner}</p>${traceOf(trace, entry)}</div>`;
    const lead = `<div class="row-end"><p class="verdict-lead">${first.show(...cut.lead)}</p>${hasRest ? '' : traceOf(trace, first.entry)}</div>`;
    const rest = hasRest ? row(first.show(...cut.rest), first.entry) : '';
    return `<div class="verdict"><h4 class="eyebrow">Bottom line</h4>${lead}${rest}${later.map(p => row(p.show(0, p.body.length), p.entry)).join('')}</div>`;
  }

  // C5: Key findings as a numbered list. A block is one finding: a `**bold lead**` is its title and the rest its body, else the first sentence is the title.
  function findingsFeed(texts, trace, figure) {
    const items = paragraphs(texts, figure).map((p, at) => {
      const bold = /^\*\*(.+?)\*\*\s*/.exec(p.body);
      const title = bold ? [2, 2 + bold[1].length] : firstSentence(p.body).lead, rest = bold ? [bold[0].length, p.body.length] : firstSentence(p.body).rest;
      const body = rest[1] > rest[0] ? `<p class="feed-body">${p.show(...rest)}</p>` : '';
      return `<li class="feed-item"><span class="feed-num">${at + 1}</span><div><div class="feed-title">${p.show(...title)}</div>${body}</div>${traceOf(trace, p.entry)}</li>`;
    });
    return items.length ? `<ol class="feed">${items.join('')}</ol>` : '';
  }

  // C6: the left-rule callout for "what would change the view".
  function callout(title, texts, trace, figure) {
    const items = paragraphs(texts, figure).map(p => `<p>${p.show(0, p.body.length)}${traceOf(trace, p.entry)}</p>`);
    return items.length ? `<div class="callout"><h4>${icon('git-compare')}${escapeHtml(title)}</h4>${items.join('')}</div>` : '';
  }

  // The Limitations: a compact list, and beside it the count of gaps the module records, with the way to them in Evidence. No gap, no signal.
  function limitationsBlock(texts, gapCount, evidenceHref, trace, figure) {
    const items = paragraphs(texts, figure).map(p => `<li>${icon('triangle-alert')}<span>${p.show(0, p.body.length)}</span>${traceOf(trace, p.entry)}</li>`);
    if (!items.length) return '';
    const signal = gapCount > 0
      ? `<div class="gapsig"><div class="gapsig-n" data-count>${gapCount}</div><div class="gapsig-w">${gapCount === 1 ? 'gap' : 'gaps'} recorded</div><a class="gapsig-link" href="${escapeHtml(evidenceHref)}">Open in Evidence${icon('arrow-right')}</a></div>`
      : '';
    return `<div class="lim-row"><ul class="lim-compact">${items.join('')}</ul>${signal}</div>`;
  }

  // The fallback for a table nothing else recognises: one card per row, the first visible column its title, the other visible columns label and value.
  // Source, id and inter-module columns are left out, and so is a cell findingCell holds back (an identifier or a calculation ID); the trace icon opens the row,
  // source cells included, in the drawer. A cell with no text has nothing to show; a cell held back for an identifier leaves a link to Evidence in its place.
  function recordCards(block, ctx) {
    const shown = visibleColumns(block, 'records', ctx);
    if (!shown.length || !block.rows.length) return '';
    const [titleCol, ...otherCols] = shown;
    const cards = block.rows.map(row => {
      const title = String(row.cells[titleCol.at] ?? '').trim(), titleHtml = fieldHtml(title, ctx);
      const fields = otherCols.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => `<div><dt>${escapeHtml(col.label)}</dt><dd>${html}</dd></div>`).join('');
      const label = `Row ${title || row.line}: where it comes from`;
      return `<article class="rec-card"><div class="rec-head">${titleHtml ? `<p class="rec-title">${titleHtml}</p>` : '<span></span>'}${traceFor(ctx, row, label)}</div>${fields ? `<dl class="rec-fields">${fields}</dl>` : ''}</article>`;
    });
    return `<div class="rec-cards"${ctx.caption ? ` role="group" aria-label="${escapeHtml(ctx.caption)}"` : ''}>${cards.join('')}</div>`;
  }

  // ---- The numeric shape components (Task 5). A table of figures is drawn by what its columns are, not by what it is called.
  // Every cell is drawn with the handoff's own characters (findingCell); a number is parsed only to place a mark, and the text beside the mark is the cell.
  // `ctx` is what the module page gives: {id, section, module, trace(row, label), key(row), evidenceHref, caption, tokens, pairing}.
  const cellText = (row, at) => String(row.cells[at] ?? '').trim();
  const numberOf = text => readerText().chartNumber(text);
  const unitOf = text => { const t = readerText().plainText(text).trim(); return t.endsWith('%') ? '%' : t.endsWith('x') ? 'x' : ''; };
  const escapeRegex = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const NUMBER_LED = /^[-−–(]?\s*(?:(?:USD|EUR|GBP|US\$|[$€£])\s*)?\d/;
  const startsWithNumber = text => NUMBER_LED.test(readerText().plainText(text).trim());
  // A column reads as numbers when at least half of its cells that have a value lead with one ("6.01x", "USD 4,173 million", "7.07 (7.07x)").
  function numericLike(block, at) {
    const cells = block.rows.map(row => cellText(row, at)).filter(text => text !== '' && !/^(?:n\.?a\.?|[—–-])$/i.test(text));
    return cells.length > 0 && cells.filter(startsWithNumber).length * 2 >= cells.length;
  }

  // The one cell rule. (a) only references (calculation IDs, file names, handoff names): omitted, reached by the row's trace control. (b) an identifier
  // of the module, or a calculation ID, inside other text: omitted, and the row links to Evidence. (c) anything else: drawn as rich text.
  const CALC_IN_TEXT = /\bcalculations?\s+[A-Z]{1,2}\d{2}\b/i;
  const STRONG_REFERENCE = [/^calculations?\s+[A-Z]{1,2}\d{2}$/i, /^[^\s;,]+\.(?:jsonl|htm|html|pdf|xlsx?|csv|md|json|txt)$/i, /\(CP-[0-9A-Z]+\)$/, /^CP-[0-9A-Z]+$/];
  const WEAK_REFERENCE = [/^[A-Z]{1,2}\d{2}$/, /^pages?\s+\d+(?:\s*[-–]\s*\d+)?$/i];
  function referencesOnly(text) {
    const parts = text.split(/\s*[;,]\s*/).filter(part => part !== '');
    return parts.length > 0 && parts.every(part => [...STRONG_REFERENCE, ...WEAK_REFERENCE].some(rx => rx.test(part))) && parts.some(part => STRONG_REFERENCE.some(rx => rx.test(part)));
  }
  const tokenPatterns = new WeakMap();
  function tokensIn(text, tokens) {
    if (!Array.isArray(tokens) || !tokens.length) return [];
    if (!tokenPatterns.has(tokens)) tokenPatterns.set(tokens, new RegExp(`(?<![A-Za-z0-9_])(?:${[...tokens].sort((a, b) => b.length - a.length).map(escapeRegex).join('|')})(?![A-Za-z0-9_])`, 'g'));
    return [...new Set(String(text).match(tokenPatterns.get(tokens)) ?? [])];
  }
  function findingCell(text, ctx = {}) {
    const raw = String(text ?? '').trim();
    if (raw === '' || referencesOnly(raw)) return {omitted: true};
    if (CALC_IN_TEXT.test(raw) || tokensIn(raw, ctx.tokens).length) return {omitted: true, inEvidence: true};
    return {html: readerText().richText(raw)};
  }
  const evidenceLink = ctx => (ctx.evidenceHref ? `<a class="in-ev" href="${escapeHtml(ctx.evidenceHref)}">In Evidence</a>` : '');
  // The cell as markup: its text, or the small link to Evidence where an identifier kept it back, or nothing.
  function fieldHtml(text, ctx) {
    const cell = findingCell(text, ctx);
    return cell.html ?? (cell.inEvidence ? evidenceLink(ctx) : '');
  }
  const MISSING = '<span class="na" title="Empty in the handoff">n.a.</span>';
  const valueHtml = (text, ctx) => (String(text).trim() === '' ? MISSING : fieldHtml(text, ctx));

  // A column header that holds an identifier of the module is the name of that case when the module pairs its cases; "(0.15)" after it is dropped
  // when it is only a number. Any other remainder, or no pairing, has no name to give: null, and the column is not drawn on a findings page.
  function resolveHeader(header, ctx) {
    const text = String(header ?? '').trim(), found = tokensIn(text, ctx.tokens);
    if (!found.length) return CALC_IN_TEXT.test(text) ? null : text;
    const at = found.length === 1 && ctx.pairing ? ctx.pairing.ids.indexOf(found[0]) : -1;
    if (at < 0 || !ctx.pairing.names[at]) return null;
    const rest = text.replace(new RegExp(escapeRegex(found[0])), '').trim();
    return rest === '' || /^\(\s*[-+\d.,%x]+\s*\)$/.test(rest) ? ctx.pairing.names[at] : null;
  }
  // The columns a findings page may draw: not source, id or inter-module, and with a header it can name. `at` is the column's place in the table.
  function visibleColumns(block, shape, ctx) {
    const hidden = new Set(shapes().hiddenColumns(block.headers, shape)), out = [];
    block.headers.forEach((header, at) => {
      const label = hidden.has(at) ? null : resolveHeader(header, ctx);
      if (label !== null) out.push({at, label, kind: shapes().columnKind(header)});
    });
    return out;
  }
  const traceFor = (ctx, row, label) => (ctx.trace ? ctx.trace(row, label) : ctx.key ? traceRow(ctx.key(row), label) : '');
  const traceOfBlock = (ctx, block) => (block.rows.length ? traceFor(ctx, block.rows[0], `${ctx.caption || 'This table'}: where it comes from`) : '');

  // ---- scales: only mark positions come from the figures
  const plainNumber = value => String(Number(value.toPrecision(12)));
  const percent = value => plainNumber(Math.round(value * 100) / 100);
  function niceCeil(value) {
    if (!(value > 0)) return 0;
    const unit = 10 ** Math.floor(Math.log10(value));
    return Number([1, 2, 2.5, 5, 10].map(m => m * unit).find(m => m >= value * (1 - 1e-12)).toPrecision(12));
  }
  // 0 to a rounded maximum (and down to a rounded minimum when a value is negative).
  function axisOf(values) {
    const max = niceCeil(Math.max(0, ...values)), min = -niceCeil(-Math.min(0, ...values));
    return max === min ? {min, max: min + 1} : {min, max};
  }
  const positionOn = (axis, value) => percent((value - axis.min) / (axis.max - axis.min) * 100);

  // ---- shared markup
  const viewToggle = (label, options) => `<div class="seg" data-i="0" role="group" aria-label="${escapeHtml(label)}"><span class="seg-thumb"></span>${options.map(([value, text], n) => `<button type="button" data-view-pick="${value}" aria-pressed="${n === 0}">${escapeHtml(text)}</button>`).join('')}</div>`;
  const pane = (name, html, shown) => `<div data-pane="${name}"${shown ? '' : ' hidden'}>${html}</div>`;
  const shapeBlock = (cls, ctx, state, inner) => `<div class="shape-block ${cls}" data-block${state ? ` ${state}` : ''} role="group"${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}>${inner}</div>`;
  const shapeBar = (left, right) => `<div class="shape-bar"><div class="shape-bar-l">${left}</div><div class="shape-bar-r">${right}</div></div>`;
  // A designed table: the block's columns as given, numbers right-aligned, the first column the row header.
  function designedTable(block, cols, ctx, className = 'dtbl') {
    const numeric = new Set(cols.filter((col, n) => n > 0 && numericLike(block, col.at)).map(col => col.at));
    const head = cols.map((col, n) => `<th scope="col"${numeric.has(col.at) ? ' class="num"' : ''}>${escapeHtml(col.label)}</th>`).join('');
    const rows = block.rows.map(row => `<tr>${cols.map((col, n) => {
      const html = fieldHtml(cellText(row, col.at), ctx);
      return n === 0 ? `<th scope="row">${html}</th>` : `<td${numeric.has(col.at) ? ' class="num"' : ''} data-label="${escapeHtml(col.label)}">${html}</td>`;
    }).join('')}</tr>`).join('');
    return `<div class="dtbl-wrap" role="region" tabindex="0"${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}><table class="${className}"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  // C3: one metric tile. `value` is the cell as it stands; a cell longer than 24 characters is text, so its tile is wide and the cell is not set large.
  const WIDE_AT = 24;
  function tile({label, value, raw, below = '', notes = [], tags = [], caption = '', info = ''}) {
    const wide = String(raw).trim().length > WIDE_AT;
    return `<div class="${wide ? 'tile wide' : 'tile'}"><div class="tile-h"><p class="tile-k">${label}</p>${info}</div><p class="tile-v">${value}</p>${below ? `<p class="tile-b">${below}</p>` : ''}${notes.map(note => `<p class="tile-n">${note}</p>`).join('')}${tags.join('')}${caption ? `<p class="tile-c">${caption}</p>` : ''}</div>`;
  }
  const tag = (label, html) => `<span class="tag"><span class="tag-k">${escapeHtml(label)}</span>${html}</span>`;
  // C24: a definition in a tooltip on an info icon; it also prints, since a tooltip does not.
  const infoTip = text => `<button type="button" class="info" ${tipAttributes(text)}>${icon('info')}</button><span class="tip-print">${escapeHtml(text)}</span>`;

  // ---- cases: named cases as columns
  // C8 over C3 and C10. Every case's tile set is in the markup (the page prints them all); the selected one is shown.
  function trackRow(row, label, caseCols, names, selected, ctx) {
    const cells = caseCols.map(col => cellText(row, col.at)), numbers = cells.map(numberOf);
    if (numbers.some(n => n === null) || new Set(cells.map(unitOf)).size !== 1) return '';
    const unit = unitOf(cells[0]), axis = axisOf(numbers), at = numbers.map(n => Number(positionOn(axis, n)));
    const order = numbers.map((n, k) => k).sort((a, b) => numbers[a] - numbers[b]);
    const marks = cells.map((cell, k) => {
      const side = order.indexOf(k) % 2 === 0 ? 'up' : 'dn', edge = at[k] < 10 ? ' lo' : at[k] > 90 ? ' hi' : '';
      return `<button type="button" class="mk ${side}${k === selected ? ' on' : ''}" style="left:${at[k]}%" data-case-pick="${k}" aria-label="${escapeHtml(`${names[k]} ${cell}`)}, show this case"><span class="mk-l${edge}"><span>${escapeHtml(names[k])}</span><b>${readerText().richText(cell)}</b></span></button>`;
    }).join('');
    const lo = Math.min(...at), hi = Math.max(...at);
    return `<div class="rtrack-row"><div class="rtrack-name">${label}</div><div class="rtrack"><div class="rtrack-line"></div><div class="rtrack-range" style="left:${lo}%;width:${percent(hi - lo)}%"></div>${marks}</div><div class="rtrack-ends"><span data-tick>${plainNumber(axis.min)}${unit}</span><span data-tick>${plainNumber(axis.max)}${unit}</span></div></div>`;
  }
  function casesBlock(block, ctx) {
    const cols = visibleColumns(block, 'cases', ctx), labelCol = cols[0];
    const caseCols = cols.slice(1).filter(col => col.kind === 'case' || col.kind === 'period');
    if (!labelCol || caseCols.length < 2 || !block.rows.length) return recordCards(block, ctx);
    const consequence = cols.find(col => col.kind === 'consequence'), extras = cols.slice(1).filter(col => !caseCols.includes(col) && col !== consequence);
    const names = caseCols.map(col => col.label), selected = names.length >= 3 ? 1 : 0;
    const sets = names.map((name, k) => {
      const tiles = block.rows.map(row => {
        const raw = cellText(row, caseCols[k].at), first = cellText(row, caseCols[0].at);
        return tile({label: fieldHtml(cellText(row, labelCol.at), ctx), value: valueHtml(raw, ctx), raw,
          below: k === 0 || first === '' ? '' : `${escapeHtml(names[0])}: ${fieldHtml(first, ctx)}`,
          notes: extras.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => `<span class="tag-k">${escapeHtml(col.label)}</span> ${html}`),
          caption: consequence ? fieldHtml(cellText(row, consequence.at), ctx) : ''});
      }).join('');
      return `<div class="tile-set" data-set="${k}"${k === selected ? '' : ' hidden'}><p class="tile-set-name">${escapeHtml(name)}</p><div class="tiles">${tiles}</div></div>`;
    }).join('');
    const tracks = block.rows.map(row => trackRow(row, fieldHtml(cellText(row, labelCol.at), ctx), caseCols, names, selected, ctx)).filter(Boolean);
    const chart = sets + (tracks.length ? `<div class="tracks"><p class="eyebrow">Across the cases</p>${tracks.join('')}</div>` : '');
    const choose = `<div class="case-seg" role="group" aria-label="Case">${names.map((name, k) => `<button type="button" class="case-opt" data-case-pick="${k}" aria-pressed="${k === selected}">${escapeHtml(name)}</button>`).join('')}</div>`;
    return shapeBlock('shape-cases', ctx, `data-case="${selected}" data-view="chart"`,
      shapeBar(choose, traceOfBlock(ctx, block) + viewToggle('Chart or table', [['chart', 'Chart'], ['table', 'Table']])) + pane('chart', chart, true) + pane('table', designedTable(block, cols, ctx), false));
  }

  // ---- caseRows: one row per case
  const LEVEL = {high: 3, medium: 2, low: 1};
  const meter = (word, header) => `<span class="cr-conf"><span class="k">${escapeHtml(header)}</span><span class="meter" aria-hidden="true">${[1, 2, 3].map(n => (n <= LEVEL[word.toLowerCase()] ? '<i class="f"></i>' : '<i></i>')).join('')}</span><span class="meter-w">${escapeHtml(word)}</span></span>`;
  const isLevel = text => Object.hasOwn(LEVEL, text.toLowerCase());
  // "a, b, c": items short enough to be chips; the commas stay in the text (hidden) so the cell reads as written.
  function chipItems(text) {
    const items = text.split(/,\s+/);
    return items.length >= 2 && text.length <= 220 && items.every(item => item.length <= 48 && !/[.;:]\s/.test(item)) ? items : null;
  }
  const chipList = (items, ctx) => `<ul class="cr-chips">${items.map((item, n) => `<li class="cr-chip">${fieldHtml(item, ctx)}${n < items.length - 1 ? '<span class="sr-only">, </span>' : ''}</li>`).join('')}</ul>`;
  function caseTitle(row, n, block, ctx) {
    const paired = ctx.pairing && ctx.pairing.names.length === block.rows.length ? ctx.pairing.names[n] : null;
    if (paired) return {html: escapeHtml(paired), name: paired};
    const own = cellText(row, 0), cell = findingCell(own, ctx);
    return cell.html !== undefined && !shapes().hiddenColumns(block.headers, 'caseRows').includes(0) ? {html: cell.html, name: own} : {html: '', name: '', badge: n + 1};
  }
  function caseRowsBlock(block, ctx) {
    const cols = visibleColumns(block, 'caseRows', ctx).filter(col => col.at !== 0);
    if (!cols.length || !block.rows.length) return recordCards(block, ctx);
    const numericCols = cols.filter(col => numericLike(block, col.at));
    if (numericCols.length * 2 > cols.length) return caseRowsPanel(block, cols, ctx);
    const lead = cols.filter(col => block.rows.every(row => { const text = cellText(row, col.at); return startsWithNumber(text) && text.length <= 14 && findingCell(text, ctx).html !== undefined; })).slice(0, 2);
    const rest = cols.filter(col => !lead.includes(col));
    const cards = block.rows.map((row, n) => {
      const title = caseTitle(row, n, block, ctx);
      const figures = lead.map(col => `<span class="cr-fig-wrap"><span class="cr-fig">${fieldHtml(cellText(row, col.at), ctx)}</span><span class="cr-fig-l">${escapeHtml(col.label)}</span></span>`).join('');
      let pill = '', foot = '';
      const fields = rest.map(col => {
        const text = cellText(row, col.at), cell = findingCell(text, ctx);
        if (cell.html !== undefined && isLevel(text) && (/^confidence$/i.test(col.label) || block.rows.every(r => isLevel(cellText(r, col.at))))) { foot += meter(text, col.label); return ''; }
        if (cell.html !== undefined && /category/i.test(col.label) && text.length <= 40 && !/[,;.]/.test(text)) { pill = `<span class="pill">${cell.html}</span>`; return ''; }
        const items = cell.html !== undefined ? chipItems(text) : null, body = items ? chipList(items, ctx) : fieldHtml(text, ctx);
        return body === '' ? '' : `<div><dt>${escapeHtml(col.label)}</dt><dd>${body}</dd></div>`;
      }).join('');
      const head = `${title.badge ? `<span class="cr-badge">${title.badge}</span>` : `<h4 class="cr-title">${title.html}</h4>`}${traceFor(ctx, row, `${title.name || `Case ${n + 1}`}: where it comes from`)}`;
      return `<article class="cr-card"><div class="cr-head">${head}</div>${pill ? `<div class="cr-pill">${pill}</div>` : ''}${figures ? `<div class="cr-figs">${figures}</div>` : ''}${fields ? `<dl class="rec-fields">${fields}</dl>` : ''}${foot ? `<div class="cr-foot">${foot}</div>` : ''}</article>`;
    });
    return `<div class="cr-cards"${ctx.caption ? ` role="group" aria-label="${escapeHtml(ctx.caption)}"` : ''}>${cards.join('')}</div>`;
  }
  // Rows are cases and columns are measures: a compact panel, numbers right-aligned and the cell text as written. A phone reads each case as a card.
  function caseRowsPanel(block, cols, ctx) {
    const head = `<th scope="col">${block.headers[0] !== undefined && visibleColumns(block, 'caseRows', ctx).some(col => col.at === 0) ? escapeHtml(block.headers[0]) : ''}</th>${cols.map(col => `<th scope="col"${numericLike(block, col.at) ? ' class="num"' : ''}>${escapeHtml(col.label)}</th>`).join('')}`;
    const rows = block.rows.map((row, n) => {
      const title = caseTitle(row, n, block, ctx);
      const name = title.badge ? `<span class="cr-badge">${title.badge}</span>` : title.html;
      return `<tr><th scope="row">${name}${traceFor(ctx, row, `${title.name || `Case ${n + 1}`}: where it comes from`)}</th>${cols.map(col => `<td${numericLike(block, col.at) ? ' class="num"' : ''} data-label="${escapeHtml(col.label)}">${fieldHtml(cellText(row, col.at), ctx)}</td>`).join('')}</tr>`;
    }).join('');
    return `<div class="dtbl-wrap" role="region" tabindex="0"${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}><table class="dtbl cr-panel"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  // ---- ranked: C11, the break-point ladder
  // The smallest round step that puts the axis in at most eight intervals, and the axis maximum above the largest level.
  function ladderAxis(largest) {
    const target = Math.max(largest, Number.MIN_VALUE) * 1.05;
    for (let exponent = Math.floor(Math.log10(target / 8)) - 1; ; exponent += 1) {
      for (const m of [1, 2, 2.5, 5]) {
        const step = Number((m * 10 ** exponent).toPrecision(12));
        if (Math.ceil(target / step) <= 8) return {step, max: Number((step * Math.ceil(target / step)).toPrecision(12))};
      }
    }
  }
  const REACHED = /^(?:breached|reached|hit|triggered|exceeded|yes|met)\b/i;
  const stateMark = (text, ctx) => `<span class="st${REACHED.test(text) ? ' on' : ''}"><i aria-hidden="true"></i>${fieldHtml(text, ctx)}</span>`;
  function rankedLadder(block, ctx) {
    const cols = visibleColumns(block, 'ranked', ctx);
    const rankCol = cols.find(col => col.at === 0), labelCol = cols.filter(col => col !== rankCol)[0];
    const levelCol = cols.filter(col => col !== rankCol && col !== labelCol).find(col => block.rows.every(row => numberOf(cellText(row, col.at)) !== null));
    const levels = levelCol ? block.rows.map(row => numberOf(cellText(row, levelCol.at))) : [];
    if (!rankCol || !labelCol || !levelCol || levels.some(n => n < 0) || new Set(block.rows.map(row => unitOf(cellText(row, levelCol.at)))).size !== 1) return recordCards(block, ctx);
    const unit = unitOf(cellText(block.rows[0], levelCol.at)), axis = ladderAxis(Math.max(...levels));
    const states = cols.filter(col => col !== rankCol && col !== labelCol && col !== levelCol);
    const x = value => `${percent(value / axis.max * 100)}%`;
    const ticks = Array.from({length: Math.round(axis.max / axis.step) + 1}, (_, n) => Number((n * axis.step).toPrecision(12)));
    const tiers = block.rows.length > 2 ? 2 : 1;
    const marks = block.rows.map((row, n) => {
      const side = n % 2 === 0 ? 'up' : 'dn', tier = Math.floor(n / 2) % tiers, at = levels[n] / axis.max * 100;
      const edge = at < 14 ? ' lo' : at > 86 ? ' hi' : '', level = cellText(row, levelCol.at), rank = cellText(row, rankCol.at), label = cellText(row, labelCol.at);
      return `<i class="ll-line ll-${side} t${tier}" style="left:${x(levels[n])}"></i><div class="ll ll-${side} t${tier}${edge}" style="left:${x(levels[n])}">${fieldHtml(label, ctx)}<b>${readerText().richText(level)}</b></div><div class="lm" tabindex="0" style="left:${x(levels[n])}" aria-label="${escapeHtml(`Break ${rank}, ${readerText().plainText(label)}, ${level}`)}"><span class="lm-n">${escapeHtml(rank)}</span></div>`;
    }).join('');
    const axisHtml = `<div class="ladder t${tiers}" role="group" aria-label="${escapeHtml(`${labelCol.label} on an axis of ${levelCol.label}`)}"><div class="lax"></div>${ticks.map(v => `<i class="ltick" style="left:${x(v)}"></i><span class="ltick-l" data-tick style="left:${x(v)}">${plainNumber(v)}${unit}</span>`).join('')}<p class="lax-t">${escapeHtml(levelCol.label)}</p>${marks}</div>`;
    const legend = states.length ? `<div class="lead-leg" style="--c:${states.length}"><div class="leg-row hd"><span></span><span>${escapeHtml(labelCol.label)}</span><span class="p">${escapeHtml(levelCol.label)}</span>${states.map(col => `<span>${escapeHtml(col.label)}</span>`).join('')}</div>${block.rows.map(row => `<div class="leg-row"><span class="n">${escapeHtml(cellText(row, rankCol.at))}</span><span>${fieldHtml(cellText(row, labelCol.at), ctx)}</span><span class="p">${readerText().richText(cellText(row, levelCol.at))}</span>${states.map(col => stateMark(cellText(row, col.at), ctx)).join('')}</div>`).join('')}</div>` : '';
    const phone = `<div class="lad-phone">${block.rows.map((row, n) => `<div class="lp-item"><span class="n">${escapeHtml(cellText(row, rankCol.at))}</span><div><p class="lp-l">${fieldHtml(cellText(row, labelCol.at), ctx)}</p><div class="lp-track"><i style="left:${x(levels[n])}"></i></div><div class="lp-ends"><span data-tick>0${unit}</span><b>${readerText().richText(cellText(row, levelCol.at))}</b><span data-tick>${plainNumber(axis.max)}${unit}</span></div>${states.length ? `<div class="lp-marks">${states.map(col => `<span><span class="lp-case">${escapeHtml(col.label)}</span> ${stateMark(cellText(row, col.at), ctx)}</span>`).join('')}</div>` : ''}</div></div>`).join('')}</div>`;
    return shapeBlock('shape-ranked', ctx, '', shapeBar('', traceOfBlock(ctx, block)) + axisHtml + legend + phone);
  }

  // ---- statement: lines by periods
  const SERIES = ['p0', 'p1', 'p2'];
  function statementCard(block, ctx) {
    const cols = visibleColumns(block, 'statement', ctx), labelCol = cols[0], periodCols = cols.slice(1).filter(col => col.kind === 'period');
    if (!labelCol || !periodCols.length || !block.rows.length) return recordCards(block, ctx);
    const captions = cols.slice(1).filter(col => !periodCols.includes(col));
    const parsed = block.rows.map(row => periodCols.map(col => numberOf(cellText(row, col.at))));
    const all = parsed.flat().filter(n => n !== null);
    const high = Math.max(0, ...all), low = Math.min(0, ...all), span = (high - low) || 1, zero = percent(-low / span * 100);
    const rows = block.rows.map((row, n) => {
      const bars = periodCols.map((col, k) => {
        const value = parsed[n][k];
        if (value === null) return '';
        const width = percent(Math.abs(value) / span * 100), from = value < 0 ? `right:${percent(100 - Number(zero))}%` : `left:${zero}%`;
        return `<span class="st-bar ${SERIES[k % 3]}${value < 0 ? ' neg' : ''}" style="${from};width:${width}%"></span>`;
      }).join('');
      const cap = captions.map(col => fieldHtml(cellText(row, col.at), ctx)).filter(html => html !== '').map(html => `<p class="st-cap">${html}</p>`).join('');
      const values = periodCols.map((col, k) => `<span class="st-pv"><i class="sw ${SERIES[k % 3]}" aria-hidden="true"></i><span class="st-ph">${escapeHtml(col.label)}</span>${valueHtml(cellText(row, col.at), ctx)}</span>`).join('');
      return `<div class="st-row"><div class="st-l"><p class="st-name">${fieldHtml(cellText(row, labelCol.at), ctx)}</p>${cap}</div><div class="st-bars" style="height:${periodCols.length * 12 - 3}px">${bars ? `${low < 0 ? `<i class="st-zero" style="left:${zero}%"></i>` : ''}${bars}` : ''}</div><div class="st-v">${values}</div></div>`;
    }).join('');
    const key = periodCols.map((col, k) => `<span class="st-key"><i class="sw ${SERIES[k % 3]}" aria-hidden="true"></i>${escapeHtml(col.label)}</span>`).join('');
    return shapeBlock('shape-statement', ctx, 'data-view="bars"',
      shapeBar(`<span class="st-keys">${key}</span>`, traceOfBlock(ctx, block) + viewToggle('Bars or figures', [['bars', 'Bars'], ['figures', 'Figures']])) + pane('bars', `<div class="st-rows">${rows}</div>`, true) + pane('figures', designedTable(block, cols, ctx), false));
  }

  // ---- metric and measure: tiles
  // The latest period is the one whose header names the latest year (the first, when none does); the others, in order, are the earlier ones.
  function periodOrder(periodCols) {
    const year = col => Number((/\d{4}/.exec(col.label) || [0])[0]);
    const latest = periodCols.reduce((best, col) => (year(col) > year(best) ? col : best), periodCols[0]);
    return {latest, earlier: periodCols.filter(col => col !== latest)};
  }
  const earlierHtml = (col, text, ctx) => (startsWithNumber(text) ? {below: `${escapeHtml(col.label)} ${fieldHtml(text, ctx)}`} : {note: fieldHtml(text, ctx)});
  function metricTiles(block, ctx) {
    const cols = visibleColumns(block, 'metric', ctx), labelCol = cols[0], periodCols = cols.slice(1).filter(col => col.kind === 'period');
    if (!labelCol || !periodCols.length || !block.rows.length) return recordCards(block, ctx);
    const {latest, earlier} = periodOrder(periodCols), definition = cols.find(col => /definition|identity/i.test(col.label));
    const others = cols.slice(1).filter(col => !periodCols.includes(col) && col !== definition);
    const tiles = block.rows.map(row => {
      const raw = cellText(row, latest.at), below = [], notes = [];
      for (const col of earlier) {
        const text = cellText(row, col.at), shown = text === '' ? {} : earlierHtml(col, text, ctx);
        if (shown.below) below.push(shown.below); else if (shown.note) notes.push(shown.note);
      }
      const defText = definition ? cellText(row, definition.at) : '';
      return tile({label: fieldHtml(cellText(row, labelCol.at), ctx), value: valueHtml(raw, ctx), raw, below: below.join(' · '), notes: notes.concat(others.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => `${escapeHtml(col.label)} ${html}`)),
        info: defText !== '' && findingCell(defText, ctx).html !== undefined ? infoTip(defText) : ''});
    }).join('');
    const table = designedTable(block, cols, ctx);
    return shapeBlock('shape-metric', ctx, 'data-view="tiles"', shapeBar('', traceOfBlock(ctx, block) + viewToggle('Tiles or table', [['tiles', 'Tiles'], ['table', 'Table']])) + pane('tiles', `<div class="tiles tiles-dense">${tiles}</div>`, true) + pane('table', table, false));
  }
  function measureTiles(block, ctx) {
    const cols = visibleColumns(block, 'measure', ctx), labelCol = cols[0];
    const consequence = cols.find(col => col.kind === 'consequence'), valueCols = cols.slice(1).filter(col => col.kind === 'period');
    const main = valueCols.length ? periodOrder(valueCols) : {latest: cols.slice(1).find(col => col !== consequence), earlier: []};
    if (!labelCol || !main.latest || !block.rows.length) return recordCards(block, ctx);
    const tagCols = cols.slice(1).filter(col => col !== main.latest && !main.earlier.includes(col) && col !== consequence);
    const tiles = block.rows.map(row => {
      const raw = cellText(row, main.latest.at), below = [], notes = [];
      for (const col of main.earlier) {
        const text = cellText(row, col.at), shown = text === '' ? {} : earlierHtml(col, text, ctx);
        if (shown.below) below.push(shown.below); else if (shown.note) notes.push(shown.note);
      }
      return tile({label: fieldHtml(cellText(row, labelCol.at), ctx), value: valueHtml(raw, ctx), raw, below: below.join(' · '), notes,
        tags: tagCols.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => tag(col.label, html)),
        caption: consequence ? fieldHtml(cellText(row, consequence.at), ctx) : ''});
    }).join('');
    return shapeBlock('shape-measure', ctx, '', shapeBar('', traceOfBlock(ctx, block)) + `<div class="tiles tiles-4">${tiles}</div>`);
  }

  // ---- change: C19, before and after
  function changeCards(block, ctx) {
    const cols = visibleColumns(block, 'change', ctx), norm = col => col.label.trim().toLowerCase();
    const labelCol = cols[0], before = cols.find(col => norm(col) === 'earlier'), after = cols.find(col => norm(col) === 'current');
    if (!labelCol || !before || !after || !block.rows.length) return recordCards(block, ctx);
    const others = cols.filter(col => ![labelCol, before, after].includes(col));
    const cards = block.rows.map(row => {
      const [a, b] = [cellText(row, before.at), cellText(row, after.at)], [na, nb] = [numberOf(a), numberOf(b)];
      const title = cellText(row, labelCol.at);
      let dumb = '';
      if (na !== null && nb !== null && unitOf(a) === unitOf(b)) {
        const axis = axisOf([na, nb]);
        dumb = `<div class="dumb" role="img" aria-label="${escapeHtml(`${before.label} ${a}, ${after.label} ${b}`)}"><i class="dumb-line"></i><i class="dm e" style="left:${positionOn(axis, na)}%"></i><i class="dm c" style="left:${positionOn(axis, nb)}%"></i></div>`;
      }
      const fields = others.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => `<div><dt>${escapeHtml(col.label)}</dt><dd>${html}</dd></div>`).join('');
      const side = (col, text) => `<div class="chg-side"><p class="chg-k">${escapeHtml(col.label)}</p><p class="chg-v">${valueHtml(text, ctx)}</p></div>`;
      return `<article class="chg-card"><div class="chg-head"><p class="chg-title">${fieldHtml(title, ctx)}</p>${traceFor(ctx, row, `${readerText().plainText(title) || `Line ${row.line}`}: where it comes from`)}</div><div class="chg-pair">${side(before, a)}<span class="chg-arrow">${icon('arrow-right')}</span>${side(after, b)}</div>${dumb}${fields ? `<dl class="rec-fields">${fields}</dl>` : ''}</article>`;
    });
    return `<div class="chg-cards"${ctx.caption ? ` role="group" aria-label="${escapeHtml(ctx.caption)}"` : ''}>${cards.join('')}</div>`;
  }

  // The dispatch: one component per shape; every shape without one is a record card. Later tasks add their shapes to this table.
  const SHAPE_COMPONENTS = {cases: casesBlock, caseRows: caseRowsBlock, ranked: rankedLadder, statement: statementCard, metric: metricTiles, measure: measureTiles, change: changeCards};
  const render = (shape, block, ctx) => (Object.hasOwn(SHAPE_COMPONENTS, shape) ? SHAPE_COMPONENTS[shape] : recordCards)(block, ctx);

  // The page's own state for these components: which case is chosen, which view is shown. Called from screen.js's click handler; true when the click was handled.
  function handleClick(target) {
    const pick = target?.closest?.('[data-case-pick]'), view = target?.closest?.('[data-view-pick]');
    const root = (pick || view)?.closest('[data-block]');
    if (!root) return false;
    if (pick) {
      const chosen = pick.dataset.casePick;
      root.dataset.case = chosen;
      root.querySelectorAll('.case-opt').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.casePick === chosen)));
      root.querySelectorAll('[data-set]').forEach(set => { set.hidden = set.dataset.set !== chosen; });
      root.querySelectorAll('.mk').forEach(mark => mark.classList.toggle('on', mark.dataset.casePick === chosen));
      return true;
    }
    const wanted = view.dataset.viewPick, toggle = view.closest('.seg');
    root.dataset.view = wanted;
    const buttons = toggle ? toggle.querySelectorAll('[data-view-pick]') : [view];
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.viewPick === wanted)));
    if (toggle) toggle.dataset.i = String([...buttons].findIndex(button => button.dataset.viewPick === wanted));
    root.querySelectorAll('[data-pane]').forEach(item => { item.hidden = item.dataset.pane !== wanted; });
    return true;
  }

  // C33: the in-page index. `items` are {id, label, count?, href?}; the page marks the current one (screen.js) and a link without an href stays on the page.
  function sectionRail(items) {
    if (!items.length) return '';
    const link = ({id, label, count, href}) => `<a class="rail-item" data-part="${escapeHtml(id)}" href="${escapeHtml(href ?? `#${id}`)}">${escapeHtml(label)}${count === undefined || count === null ? '' : `<span class="rail-count">${escapeHtml(count)}</span>`}</a>`;
    return `<nav class="sec-rail" aria-label="On this page"><p class="eyebrow">On this page</p>${items.map(link).join('')}</nav>`;
  }

  const Components = {icon, traceButton, traceRow, headerChips, placePill, toast, toastHost, tipAttributes, verdictPanel, findingsFeed, callout, limitationsBlock, recordCards, findingCell, render, casesBlock, caseRowsBlock, rankedLadder, statementCard, metricTiles, measureTiles, changeCards, handleClick, sectionRail, ICON_PATHS};
  if (typeof window !== 'undefined') window.Components = Components;
  if (typeof document !== 'undefined' && document.body) toastHost();
  if (typeof module !== 'undefined') module.exports = Components;
})();

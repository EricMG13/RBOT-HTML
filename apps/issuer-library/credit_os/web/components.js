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
    "arrow-up-right": "<path d=\"M7 7h10v10\" /><path d=\"M7 17 17 7\" />",
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
    "history": "<path d=\"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8\" /><path d=\"M3 3v5h5\" /><path d=\"M12 7v5l4 2\" />",
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
    "arrow-down": "<path d=\"M12 5v14\" /><path d=\"m19 12-7 7-7-7\" />",
    "banknote": "<rect width=\"20\" height=\"12\" x=\"2\" y=\"6\" rx=\"2\" /><circle cx=\"12\" cy=\"12\" r=\"2\" /><path d=\"M6 12h.01M18 12h.01\" />",
    "building": "<rect width=\"16\" height=\"20\" x=\"4\" y=\"2\" rx=\"2\" /><path d=\"M9 22v-4h6v4\" /><path d=\"M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01\" />",
    "globe": "<circle cx=\"12\" cy=\"12\" r=\"10\" /><path d=\"M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20\" /><path d=\"M2 12h20\" />",
    "scale": "<path d=\"m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z\" /><path d=\"m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z\" /><path d=\"M7 21h10\" /><path d=\"M12 3v18\" /><path d=\"M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2\" />",
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

  // C23: one status host fixed bottom-right; each message removes itself after 3 seconds, or after 8 when it carries a control (time to reach it), or at once on Escape.
  const TOAST_MS = 3000, TOAST_LINK_MS = 8000;
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
  // `action` is {label, onClick}: a button that runs onClick (for a message the reader may act on).
  function toast(text, action = null) {
    const host = toastHost();
    const message = document.createElement('p');
    message.className = 'toast';
    message.textContent = text;
    if (action) {
      const button = document.createElement('button');
      button.setAttribute('type', 'button');
      button.textContent = action.label;
      button.onclick = action.onClick;
      message.append(' ', button);
    }
    host.append(message);
    setTimeout(() => message.remove(), action ? TOAST_LINK_MS : TOAST_MS);
  }
  function dismissToasts() {
    for (const message of [...toastHost().children]) message.remove();
  }

  // C24: a control that names itself by `data-tip` always also carries the same text as its accessible name; the bubble is CSS only.
  function tipAttributes(text) {
    return `data-tip="${escapeHtml(text)}" aria-label="${escapeHtml(text)}"`;
  }

  // ---- The module page (Task 4). The text helpers are reader.js's: node requires the file, the page already holds its globals.
  const readerText = () => (typeof module !== 'undefined' ? require('./reader.js') : {richText, figureSpans, figuredHtml, paragraphBody, chartNumber, plainText, numericColumn});
  // The words of a paragraph as the page reads them: its Basis line, list marker and line breaks gone.
  const paragraphText = text => readerText().paragraphBody(text).body;
  const shapes = () => (typeof module !== 'undefined' ? require('./shapes.js') : window.Shapes);
  // One paragraph of a passage: its body as read (Basis line, list marker and line breaks gone) and `show(from, to)`, the inline HTML of a stretch of it.
  // A figure is the page's own control when `figure(line, index, text)` gives one, else its exact text.
  function prose(entry, figure) {
    const reader = readerText();
    const {body} = reader.paragraphBody(entry.text);
    const figures = reader.figureSpans(body);
    const marks = [...body.matchAll(/\*\*/g)].map(m => m.index);
    const button = (i, text) => (figure && figure(entry.line, i, text)) || escapeHtml(text);
    // A stretch cut inside **bold** is drawn with the open mark closed at the cut (and reopened at the start of the next stretch): the only characters added are those marks.
    const show = (from, to) => {
      const inside = marks.filter(m => m >= from && m + 2 <= to);
      if (inside.length % 2 === 0) return reader.figuredHtml(body, figures, from, to, button);
      const lead = marks.indexOf(inside[0]) % 2 === 1 ? '**' : '', tail = lead ? '' : '**';  // the odd mark is a closer (the stretch starts in bold) or an opener (it ends in bold)
      const framed = `${body.slice(0, from)}${lead}${body.slice(from, to)}${tail}`;
      return reader.figuredHtml(framed, figures.map(f => (f.start >= from ? {...f, start: f.start + lead.length, end: f.end + lead.length} : f)), from, to + lead.length + tail.length, button);
    };
    return {body, show};
  }
  const paragraphs = (texts, figure) => texts.map(entry => ({entry, ...prose(entry, figure)})).filter(p => p.body.trim() !== '');
  const traceOf = (trace, entry) => (trace ? trace(entry.line) : '');
  // A sentence ends at ". " before a capital letter (its own opening ** or ` marks do not count) or at the end of the text; the first one is whole, never cut.
  // A stop inside a `code span` is no boundary; a closing mark right after the full stop belongs to the sentence, so no stretch is left with an unbalanced mark.
  function firstSentence(body) {
    const stop = /\.(\*\*|`)?\s+(?=(?:\*\*|`)?[A-Z])/g;
    for (let end = stop.exec(body); end; end = stop.exec(body)) {
      const spans = (body.slice(0, end.index).match(/`/g) ?? []).length, closer = end[1] === '`' ? 1 : 0;
      if ((spans + closer) % 2 === 1) continue;                                 // inside an open code span
      const close = end[1] ? end[1].length : 0;                                  // a closing mark right after the full stop belongs to the sentence
      return {lead: [0, end.index + 1 + close], rest: [end.index + end[0].length, body.length]};
    }
    return {lead: [0, body.length], rest: [body.length, body.length]};
  }

  const LONG_LEAD = 140;
  // C2: the Bottom line. The first sentence of the first paragraph is the large lead; what follows is at body size, a trace button ends each paragraph.
  // `tag` is the heading level of the eyebrow: the page that holds the panel sets it so headings stay in order.
  function verdictPanel(texts, trace, figure, tag = 'h4') {
    const [first, ...later] = paragraphs(texts, figure);
    if (!first) return '';
    const cut = firstSentence(first.body), hasRest = cut.rest[1] > cut.rest[0];
    const row = (inner, entry) => `<div class="row-end"><p class="verdict-body">${inner}</p>${traceOf(trace, entry)}</div>`;
    // A lead sentence longer than 140 characters is a paragraph, not a headline: it is set at the size of the text beneath it.
    const long = readerText().plainText(first.body.slice(...cut.lead)).length > LONG_LEAD;
    const lead = `<div class="row-end"><p class="verdict-lead${long ? ' is-long' : ''}">${first.show(...cut.lead)}</p>${hasRest ? '' : traceOf(trace, first.entry)}</div>`;
    const rest = hasRest ? row(first.show(...cut.rest), first.entry) : '';
    return `<div class="verdict"><${tag} class="eyebrow">Bottom line</${tag}>${lead}${rest}${later.map(p => row(p.show(0, p.body.length), p.entry)).join('')}</div>`;
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
  function callout(title, texts, trace, figure, tag = 'h4') {
    const items = paragraphs(texts, figure).map(p => `<p>${p.show(0, p.body.length)}${traceOf(trace, p.entry)}</p>`);
    return items.length ? `<div class="callout"><${tag}>${icon('git-compare')}${escapeHtml(title)}</${tag}>${items.join('')}</div>` : '';
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
      const label = rowLabelOf(block, ctx, row, title);
      return `<article class="rec-card"><div class="rec-head">${titleHtml ? `<p class="rec-title">${titleHtml}</p>` : '<span></span>'}${traceFor(ctx, row, label)}</div>${fields ? `<dl class="rec-fields">${fields}</dl>` : ''}${extraList(block, row, ctx)}</article>`;
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
  const calculationId = () => shapes().CALCULATION_ID;  // the one pattern, owned by shapes.js
  // The one list of file extensions an issuer document or handoff can carry (longest first), and the file-name and long-hash patterns built on it: shapes.js's, so that a column
  // is classed and a cell is read by the same words.
  const {FILE_EXTENSIONS, FILE_NAME: FILE_NAME_IN_TEXT, LONG_HEX} = shapes();
  const STRONG_REFERENCE = [{test: part => new RegExp(`^(?:${calculationId().source})$`).test(part)}, new RegExp(`^[^\\s;,]+\\.(?:${FILE_EXTENSIONS})$`, 'i'), /\(CP-[0-9A-Z]+\)$/, /^CP-[0-9A-Z]+$/];
  const WEAK_REFERENCE = [/^[A-Z]{1,2}\d{2}$/, /^pages?\s+\d+(?:\s*[-–]\s*\d+)?$/i];
  function referencesOnly(text) {
    const parts = text.split(/\s*[;,]\s*/).filter(part => part !== '');
    return parts.length > 0 && parts.every(part => [...STRONG_REFERENCE, ...WEAK_REFERENCE].some(rx => rx.test(part))) && parts.some(part => STRONG_REFERENCE.some(rx => rx.test(part)));
  }
  const REFERENCE_IN_TEXT = [/[\w-]+\.[A-Za-z]{2,5}\b/, /\bCP-[A-Za-z0-9]+/, /\b[0-9a-f]{16,}\b/i, new RegExp(`(?<![\\w.-])[\\w.-]+(?:\\/[\\w.-]+){2,}|(?<![\\w.-])[\\w.-]+\\/[\\w-]+\\.(?:${FILE_EXTENSIONS})\\b`, 'i')];  // a file name, a module code, a hex id of 16 or more, a slash path (two or more slashes, or a last segment with a file extension; "FY23/FY24" and "and/or" are phrases)
  const CELL_REFERENCE = [FILE_NAME_IN_TEXT, LONG_HEX];
  const STRICT_REFERENCE = [/\b(?=[0-9]*[a-f])[0-9a-f]{16,}\b/i, /\bsc\d+\b/i, /\bCP-[0-9A-Z]+\s+[A-Z]{1,2}\d{2}\b/];
  const tokenPatterns = new WeakMap();
  function tokensIn(text, tokens) {
    if (!Array.isArray(tokens) || !tokens.length) return [];
    if (!tokenPatterns.has(tokens)) tokenPatterns.set(tokens, new RegExp(`(?<![A-Za-z0-9_])(?:${[...tokens].sort((a, b) => b.length - a.length).map(escapeRegex).join('|')})(?![A-Za-z0-9_])`, 'g'));
    return [...new Set(String(text).match(tokenPatterns.get(tokens)) ?? [])];
  }
  function findingCell(text, ctx = {}) {
    const raw = String(text ?? '').trim();
    if (raw === '' || referencesOnly(raw)) return {omitted: true};
    const found = tokensIn(raw, ctx.tokens);
    // Only identifiers (an id cell such as "s00"): rule (a), plain omission. An identifier inside other text: rule (b), the link to Evidence.
    if (found.length && /^[\s;,&]*$/.test(found.reduce((text, token) => text.split(token).join(''), raw))) return {omitted: true};
    if (calculationId().test(raw) || found.length) return {omitted: true, inEvidence: true};
    // A file name (an issuer document extension, chained too) or a hash of 32 or more hex characters inside a cell is held back the same way, on every findings page. A passage is not read here: the page draws
    // a module's own paragraphs, a cell is read by this function.
    // `ctx.strict` (the Forecast page) adds a hash of 16 or more hex characters, a scenario id in any case and a module code followed by an id-shaped word. An id value of the run's own tables is held by `ctx.tokens` as everywhere; another id-shaped word (G20, P50, EU27) is ordinary text.
    // A module code on its own is not held: the page names it. Ordinary prose stays: 3.5x, 2.36x, U.S. GAAP, e.g., Sep. 2024, $1.2bn, FY2024, 10-K, Under U.S.GAAP rules, 10-K.Item 7.
    const plainRaw = readerText().plainText(raw);
    if (CELL_REFERENCE.some(rx => rx.test(plainRaw)) || (ctx.strict && STRICT_REFERENCE.some(rx => rx.test(plainRaw)))) return {omitted: true, inEvidence: true};
    return {html: readerText().richText(raw)};
  }
  const evidenceLink = ctx => (ctx.evidenceHref ? `<a class="in-ev" href="${escapeHtml(ctx.evidenceHref)}">In Evidence</a>` : '');
  // The cell as markup: its text, or the small link to Evidence where an identifier kept it back, or nothing.
  function fieldHtml(text, ctx) {
    const cell = findingCell(text, ctx);
    return cell.html ?? (cell.inEvidence ? evidenceLink(ctx) : '');
  }
  // An empty cell is a dash that says so, not a word: "n.a." would read as the module's own n/a. The dash is read aloud as the title says.
  const MISSING = '<span class="na" role="img" title="Empty in the handoff" aria-label="Empty in the handoff">—</span>';
  const valueHtml = (text, ctx) => (String(text).trim() === '' ? MISSING : fieldHtml(text, ctx));
  // A row can hold more cells than the table has headers. Those cells have no label to draw under, but they are the handoff's: each goes through
  // findingCell like any other and is drawn after the row's other fields.
  const extrasOf = (block, row, ctx) => row.cells.slice(block.headers.length).map(cell => fieldHtml(String(cell ?? '').trim(), ctx)).filter(html => html !== '');
  const extraWidth = block => Math.max(0, ...block.rows.map(row => row.cells.length - block.headers.length));

  // A column header that holds an identifier of the module is the name of that case when the module pairs its cases; "(0.15)" after it is dropped
  // when it is only a number. Any other remainder, or no pairing, has no name to give: null, and the column is not drawn on a findings page.
  function resolveHeader(header, ctx) {
    const text = String(header ?? '').trim(), found = tokensIn(text, ctx.tokens);
    if (!found.length) return calculationId().test(text) ? null : text;
    const at = found.length === 1 && ctx.pairing ? ctx.pairing.ids.indexOf(found[0]) : -1;
    if (at < 0 || !ctx.pairing.names[at]) return null;
    const rest = text.replace(new RegExp(escapeRegex(found[0])), '').trim();
    return rest === '' || /^\(\s*[-+\d.,%x]+\s*\)$/.test(rest) ? ctx.pairing.names[at] : null;
  }
  // The columns a findings page may draw: not source, id or inter-module, and with a header it can name. `at` is the column's place in the table.
  function visibleColumns(block, shape, ctx) {
    const hidden = new Set(shapes().hiddenColumns(block.headers, shape, block.rows)), kinds = shapes().columnKinds(block), out = [];
    block.headers.forEach((header, at) => {
      const label = hidden.has(at) ? null : resolveHeader(header, ctx);
      if (label !== null) out.push({at, label, kind: kinds[at]});
    });
    return out;
  }
  const traceFor = (ctx, row, label) => (ctx.trace ? ctx.trace(row, label) : ctx.key ? traceRow(ctx.key(row), label) : '');
  const traceOfBlock = (ctx, block) => (block.rows.length && !ctx.noTrace ?  // `noTrace`: the card already carries the table's one trace control
    traceFor(ctx, block.rows[0], `${ctx.caption || 'This table'}: where it comes from`) : '');

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
  // `shown` is the option on view (the first unless a page that redraws the block says otherwise).
  const viewToggle = (label, options, shown = options[0][0]) => `<div class="seg" data-i="${Math.max(0, options.findIndex(([value]) => value === shown))}" role="group" aria-label="${escapeHtml(label)}"><span class="seg-thumb"></span>${options.map(([value, text]) => `<button type="button" data-view-pick="${value}" aria-pressed="${value === shown}">${escapeHtml(text)}</button>`).join('')}</div>`;
  const pane = (name, html, shown) => `<div data-pane="${name}"${shown ? '' : ' hidden'}>${html}</div>`;
  const shapeBlock = (cls, ctx, state, inner) => `<div class="shape-block ${cls}" data-block${state ? ` ${state}` : ''} role="group"${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}>${inner}</div>`;
  const shapeBar = (left, right) => `<div class="shape-bar"><div class="shape-bar-l">${left}</div><div class="shape-bar-r">${right}</div></div>`;
  // A designed table: the block's columns as given, numbers right-aligned, the first column the row header.
  function designedTable(block, cols, ctx, className = 'dtbl') {
    const numeric = new Set(cols.filter((col, n) => n > 0 && numericLike(block, col.at)).map(col => col.at));
    const head = cols.map((col, n) => `<th scope="col"${numeric.has(col.at) ? ' class="num"' : ''}>${escapeHtml(col.label)}</th>`).join('') + '<th scope="col"></th>'.repeat(extraWidth(block));
    const rows = block.rows.map(row => `<tr>${cols.map((col, n) => {
      const html = fieldHtml(cellText(row, col.at), ctx);
      return n === 0 ? `<th scope="row">${html}</th>` : `<td${numeric.has(col.at) ? ' class="num"' : ''} data-label="${escapeHtml(col.label)}">${html}</td>`;
    }).join('')}${Array.from({length: extraWidth(block)}, (_, k) => `<td>${fieldHtml(cellText(row, block.headers.length + k), ctx)}</td>`).join('')}</tr>`).join('');
    return `<div class="dtbl-wrap" role="region" tabindex="0"${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}><table class="${className}"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  // The table inside a chart card: the contract's rows as written, minus the columns a findings page never draws (source, id, inter-module).
  const chartTable = (block, ctx) => designedTable(block, visibleColumns(block, 'records', ctx), ctx, 'dtbl chart-dtbl');

  // C3: one metric tile. `value` is the cell as it stands; a cell longer than 24 characters is text, so its tile is wide and the cell is not set large.
  const WIDE_AT = 24;
  function tile({label, value, raw, below = '', notes = [], tags = [], absences = [], caption = '', info = ''}) {
    const wide = String(raw).trim().length > WIDE_AT;
    return `<div class="${wide ? 'tile wide' : 'tile'}"><div class="tile-h"><p class="tile-k">${label}</p>${info}</div><p class="tile-v">${value}</p>${below ? `<p class="tile-b">${below}</p>` : ''}${notes.map(note => `<p class="tile-n">${note}</p>`).join('')}${tags.join('')}${absences.map(html => `<p class="tile-a">${html}</p>`).join('')}${caption ? `<p class="tile-c">${caption}</p>` : ''}</div>`;
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
          notes: extras.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => `<span class="tag-k">${escapeHtml(col.label)}</span> ${html}`).concat(extrasOf(block, row, ctx)),
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
  const levelOf = word => (Object.hasOwn(LEVEL, word.toLowerCase()) ? LEVEL[word.toLowerCase()] : 0);
  const meter = (word, header) => `<span class="cr-conf"><span class="k">${escapeHtml(header)}</span><span class="meter" aria-hidden="true">${[1, 2, 3].map(n => (n <= levelOf(word) ? '<i class="f"></i>' : '<i></i>')).join('')}</span><span class="meter-w">${escapeHtml(word)}</span></span>`;
  const isLevel = text => Object.hasOwn(LEVEL, text.toLowerCase());
  // "a, b, c": items short enough to be chips; the commas stay in the text (hidden) so the cell reads as written.
  function chipItems(text) {
    const items = text.split(/,\s+/);
    return items.length >= 2 && text.length <= 220 && items.every(item => item.length <= 48 && !/[.;:]\s/.test(item)) ? items : null;
  }
  const chipList = (items, ctx) => `<ul class="cr-chips">${items.map((item, n) => `<li class="cr-chip">${fieldHtml(item, ctx)}${n < items.length - 1 ? '<span class="sr-only">, </span>' : ''}</li>`).join('')}</ul>`;
  // A case's name comes from its scenario id, never from its position: a row whose first cell is an id of the module's pairing (Shapes.casePairing) takes that id's case name.
  const pairedName = (cell, ctx) => {
    const text = String(cell ?? '').replace(/^[*_`~\s]+|[*_`~\s]+$/g, ''), at = ctx.pairing && text !== '' ? ctx.pairing.ids.indexOf(text) : -1;
    return at >= 0 && ctx.pairing.names[at] ? ctx.pairing.names[at] : null;
  };
  // A case's title: its paired name; else a number, with its first cell as the title when that is text, or the link to Evidence when the cell held an identifier in a sentence.
  function caseTitle(row, n, block, ctx) {
    const own = cellText(row, 0), name = pairedName(own, ctx);
    if (name) return {html: escapeHtml(name), name, link: ''};
    const numbered = (html, link) => ({html, name: html ? own : '', badge: n + 1, link});
    if (shapes().hiddenColumns(block.headers, 'caseRows', block.rows).includes(0)) return numbered('', '');
    const cell = findingCell(own, ctx);
    return cell.html !== undefined ? numbered(cell.html, '') : numbered('', cell.inEvidence ? evidenceLink(ctx) : '');
  }
  function caseRowsBlock(block, ctx) {
    const cols = visibleColumns(block, 'caseRows', ctx).filter(col => col.at !== 0);  // column 0 is each row's title
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
      const head = `${title.badge ? `<span class="cr-badge">${title.badge}</span>${title.link}` : ''}${title.html ? `<h4 class="cr-title">${title.html}</h4>` : ''}${traceFor(ctx, row, `${title.name || `Case ${n + 1}`}: where it comes from`)}`;
      return `<article class="cr-card"><div class="cr-head">${head}</div>${pill ? `<div class="cr-pill">${pill}</div>` : ''}${figures ? `<div class="cr-figs">${figures}</div>` : ''}${fields ? `<dl class="rec-fields">${fields}</dl>` : ''}${extrasOf(block, row, ctx).map(html => `<p class="cr-extra">${html}</p>`).join('')}${foot ? `<div class="cr-foot">${foot}</div>` : ''}</article>`;
    });
    return `<div class="cr-cards"${ctx.caption ? ` role="group" aria-label="${escapeHtml(ctx.caption)}"` : ''}>${cards.join('')}</div>`;
  }
  // Rows are cases and columns are measures: a compact panel, numbers right-aligned and the cell text as written. A phone reads each case as a card.
  function caseRowsPanel(block, cols, ctx) {
    const head = `<th scope="col">${block.headers[0] !== undefined && visibleColumns(block, 'caseRows', ctx).some(col => col.at === 0) ? escapeHtml(block.headers[0]) : ''}</th>${cols.map(col => `<th scope="col"${numericLike(block, col.at) ? ' class="num"' : ''}>${escapeHtml(col.label)}</th>`).join('')}${'<th scope="col"></th>'.repeat(extraWidth(block))}`;
    const rows = block.rows.map((row, n) => {
      const title = caseTitle(row, n, block, ctx);
      const name = (title.badge ? `<span class="cr-badge">${title.badge}</span>` : '') + title.html + title.link;
      return `<tr><th scope="row">${name}${traceFor(ctx, row, `${title.name || `Case ${n + 1}`}: where it comes from`)}</th>${cols.map(col => `<td${numericLike(block, col.at) ? ' class="num"' : ''} data-label="${escapeHtml(col.label)}">${fieldHtml(cellText(row, col.at), ctx)}</td>`).join('')}${Array.from({length: extraWidth(block)}, (_, k) => `<td>${fieldHtml(cellText(row, block.headers.length + k), ctx)}</td>`).join('')}</tr>`;
    }).join('');
    return `<div class="dtbl-wrap" role="region" tabindex="0"${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}><table class="dtbl cr-panel"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  // ---- ranked: C11, the break-point ladder
  // The smallest round step that puts the axis in at most eight intervals, and the axis maximum above the largest level.
  // When no level is above 0 there is nothing to scale: a fixed axis of 0 to 100 for percentages and 0 to 1 for anything else, ticks at its two ends only.
  function ladderAxis(largest, unit) {
    if (!(largest > 0) || !Number.isFinite(largest)) { const max = unit === '%' ? 100 : 1; return {step: max, max}; }
    const target = largest * 1.05;
    if (!Number.isFinite(target)) return null;  // levels at the top of the float range have no axis to draw
    const first = Math.floor(Math.log10(target / 8)) - 1;
    if (!Number.isFinite(first)) return null;  // a level so small that a step of it underflows to 0 has no axis to draw
    for (let exponent = first; ; exponent += 1) {
      for (const m of [1, 2, 2.5, 5]) {
        const step = Number((m * 10 ** exponent).toPrecision(12));
        if (Math.ceil(target / step) <= 8) { const max = Number((step * Math.ceil(target / step)).toPrecision(12)); return Number.isFinite(max) ? {step, max} : null; }
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
    if (!rankCol || !labelCol || !levelCol || levels.some(n => !Number.isFinite(n) || n < 0) || new Set(block.rows.map(row => unitOf(cellText(row, levelCol.at)))).size !== 1) return recordCards(block, ctx);
    const unit = unitOf(cellText(block.rows[0], levelCol.at)), axis = ladderAxis(Math.max(...levels), unit);
    if (!axis) return recordCards(block, ctx);
    const states = cols.filter(col => col !== rankCol && col !== labelCol && col !== levelCol);
    const x = value => `${percent(value / axis.max * 100)}%`;
    const ticks = Array.from({length: Math.round(axis.max / axis.step) + 1}, (_, n) => Number((n * axis.step).toPrecision(12)));
    const tiers = block.rows.length > 2 ? 2 : 1;
    const marks = block.rows.map((row, n) => {
      const side = n % 2 === 0 ? 'up' : 'dn', tier = Math.floor(n / 2) % tiers, at = levels[n] / axis.max * 100;
      const edge = at < 14 ? ' lo' : at > 86 ? ' hi' : '', level = cellText(row, levelCol.at), rank = cellText(row, rankCol.at), label = cellText(row, labelCol.at);
      return `<i class="ll-line ll-${side} t${tier}" style="left:${x(levels[n])}"></i><div class="ll ll-${side} t${tier}${edge}" style="left:${x(levels[n])}">${fieldHtml(label, ctx)}<b>${readerText().richText(level)}</b>${extrasOf(block, row, ctx).map(html => `<span class="ll-x">${html}</span>`).join('')}</div><div class="lm" role="img" style="left:${x(levels[n])}" aria-label="${escapeHtml(`Break ${rank}, ${readerText().plainText(label)}, ${level}`)}"><span class="lm-n">${escapeHtml(rank)}</span></div>`;
    }).join('');
    const axisHtml = `<div class="ladder t${tiers}" role="group" aria-label="${escapeHtml(`${labelCol.label} on an axis of ${levelCol.label}`)}"><div class="lax"></div>${ticks.map(v => `<i class="ltick" style="left:${x(v)}"></i><span class="ltick-l" data-tick style="left:${x(v)}">${plainNumber(v)}${unit}</span>`).join('')}<p class="lax-t">${escapeHtml(levelCol.label)}</p>${marks}</div>`;
    const legend = states.length ? `<div class="lead-leg" style="--c:${states.length}"><div class="leg-row hd"><span></span><span>${escapeHtml(labelCol.label)}</span><span class="p">${escapeHtml(levelCol.label)}</span>${states.map(col => `<span>${escapeHtml(col.label)}</span>`).join('')}</div>${block.rows.map(row => `<div class="leg-row"><span class="n">${escapeHtml(cellText(row, rankCol.at))}</span><span>${fieldHtml(cellText(row, labelCol.at), ctx)}</span><span class="p">${readerText().richText(cellText(row, levelCol.at))}</span>${states.map(col => stateMark(cellText(row, col.at), ctx)).join('')}</div>`).join('')}</div>` : '';
    const phone = `<div class="lad-phone">${block.rows.map((row, n) => `<div class="lp-item"><span class="n">${escapeHtml(cellText(row, rankCol.at))}</span><div><p class="lp-l">${fieldHtml(cellText(row, labelCol.at), ctx)}</p>${extrasOf(block, row, ctx).map(html => `<p class="lp-x">${html}</p>`).join('')}<div class="lp-track"><i style="left:${x(levels[n])}"></i></div><div class="lp-ends"><span data-tick>0${unit}</span><b>${readerText().richText(cellText(row, levelCol.at))}</b><span data-tick>${plainNumber(axis.max)}${unit}</span></div>${states.length ? `<div class="lp-marks">${states.map(col => `<span><span class="lp-case">${escapeHtml(col.label)}</span> ${stateMark(cellText(row, col.at), ctx)}</span>`).join('')}</div>` : ''}</div></div>`).join('')}</div>`;
    return shapeBlock('shape-ranked', ctx, '', shapeBar('', traceOfBlock(ctx, block)) + axisHtml + legend + phone);
  }

  // ---- statement: lines by periods
  const SERIES = ['p0', 'p1', 'p2'];
  function statementCard(block, ctx) {
    const cols = visibleColumns(block, 'statement', ctx), labelCol = cols[0], periodCols = cols.slice(1).filter(col => col.kind === 'period');
    if (!labelCol || !periodCols.length || !block.rows.length) return recordCards(block, ctx);
    const captions = cols.slice(1).filter(col => !periodCols.includes(col));
    const parsed = block.rows.map(row => periodCols.map(col => numberOf(cellText(row, col.at))));
    // One bar scale for the rows that share a unit. When the table's Unit cells differ, a row's bars are scaled within the rows of its own unit, and a row whose unit no other row shares draws its figures with no bar.
    const unitCol = captions.find(col => /^units?$/i.test(col.label.trim())), unitKey = row => (unitCol ? cellText(row, unitCol.at) : '');
    const mixed = new Set(block.rows.map(unitKey)).size > 1, group = n => block.rows.map((row, at) => at).filter(at => !mixed || unitKey(block.rows[at]) === unitKey(block.rows[n]));
    const scaleOf = n => {
      const all = group(n).flatMap(at => parsed[at]).filter(value => value !== null);
      const high = Math.max(0, ...all), low = Math.min(0, ...all), span = (high - low) || 1;
      return {low, span, zero: percent(-low / span * 100)};
    };
    const rows = block.rows.map((row, n) => {
      const {low, span, zero} = scaleOf(n), alone = mixed && group(n).length < 2;
      const bars = alone ? '' : periodCols.map((col, k) => {
        const value = parsed[n][k];
        if (value === null) return '';
        const width = percent(Math.abs(value) / span * 100), from = value < 0 ? `right:${percent(100 - Number(zero))}%` : `left:${zero}%`;
        return `<span class="st-bar ${SERIES[k % 3]}${value < 0 ? ' neg' : ''}" style="${from};width:${width}%"></span>`;
      }).join('');
      const cap = captions.map(col => fieldHtml(cellText(row, col.at), ctx)).concat(extrasOf(block, row, ctx)).filter(html => html !== '').map(html => `<p class="st-cap">${html}</p>`).join('');
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
      return tile({label: fieldHtml(cellText(row, labelCol.at), ctx), value: valueHtml(raw, ctx), raw, below: below.join(' · '), notes: notes.concat(others.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => `${escapeHtml(col.label)} ${html}`)).concat(extrasOf(block, row, ctx)),
        info: defText === '' ? '' : findingCell(defText, ctx).html !== undefined ? infoTip(defText) : fieldHtml(defText, ctx)});
    }).join('');
    const table = designedTable(block, cols, ctx);
    return shapeBlock('shape-metric', ctx, 'data-view="tiles"', shapeBar('', traceOfBlock(ctx, block) + viewToggle('Tiles or table', [['tiles', 'Tiles'], ['table', 'Table']])) + pane('tiles', `<div class="tiles tiles-dense">${tiles}</div>`, true) + pane('table', table, false));
  }
  // C4, the Overview's figure strip: the rows of one metric table whose label the lead text names, as one joined strip. A row is shown when its label, read as plain text,
  // is a whole phrase of `text` (case aside), in the table's own order and at most four; none matches, no strip. Each cell is the label (a link to the module that holds the
  // table: `link` is {href, title}), the latest period's cell as written, the earlier periods' numeric cells beneath, and the row's trace control. Nothing is picked by position.
  const STRIP_MAX = 4;
  const phrasesIn = (phrase, text) => (phrase === '' ? [] : [...text.matchAll(new RegExp(`(?<![\\p{L}\\p{N}])${escapeRegex(phrase)}(?![\\p{L}\\p{N}])`, 'giu'))].map(m => [m.index, m.index + m[0].length]));
  function metricStrip(block, ctx, text, link) {
    const cols = visibleColumns(block, 'metric', ctx), labelCol = cols[0], periodCols = cols.slice(1).filter(col => col.kind === 'period');
    if (!labelCol || !periodCols.length || !block.rows.length) return '';
    const {latest, earlier} = periodOrder(periodCols), reader = readerText();
    const plainText = reader.plainText(text);
    const named = block.rows.filter(row => fieldHtml(cellText(row, labelCol.at), ctx) !== '').map(row => ({row, spans: phrasesIn(reader.plainText(cellText(row, labelCol.at)).trim(), plainText)})).filter(item => item.spans.length);
    // A label found only inside the span of a longer label the text names ("EBITDA" in "EBITDA margin") is not cited on its own; one that also stands alone elsewhere stays.
    const inside = (span, other) => other.spans.some(o => o[0] <= span[0] && span[1] <= o[1] && o[1] - o[0] > span[1] - span[0]);
    const cells = named.filter(item => item.spans.some(span => !named.some(other => other !== item && inside(span, other)))).map(item => item.row)
      .slice(0, STRIP_MAX).map(row => {
        const label = cellText(row, labelCol.at);
        const below = earlier.map(col => [col, cellText(row, col.at)]).filter(([, value]) => value !== '' && startsWithNumber(value)).map(([col, value]) => `${escapeHtml(col.label)} ${fieldHtml(value, ctx)}`).join(' · ');
        return `<div class="strip-i"><div class="strip-t"><a class="strip-k" href="${escapeHtml(link.href)}" title="${escapeHtml(`Open ${link.title}`)}">${fieldHtml(label, ctx)}</a>${traceFor(ctx, row, rowLabelOf(block, ctx, row, label))}</div><p class="strip-v${cellText(row, latest.at).length > WIDE_AT ? ' wide' : ''}">${valueHtml(cellText(row, latest.at), ctx)}</p>${below ? `<p class="strip-b">${below}</p>` : ''}</div>`;
      });
    return cells.length ? `<div class="strip" role="group" aria-label="Figures the bottom line cites, ${escapeHtml(latest.label)}">${cells.join('')}</div>` : '';
  }
  const TILE_ABSENCE = /^(?:not (?:supplied|calculated)\b|none identified\b)/i;
  function measureTiles(block, ctx) {
    const cols = visibleColumns(block, 'measure', ctx), labelCol = cols[0];
    const consequence = cols.find(col => col.kind === 'consequence'), valueCols = cols.slice(1).filter(col => col.kind === 'period');
    const main = valueCols.length ? periodOrder(valueCols) : {latest: cols.slice(1).find(col => col !== consequence), earlier: []};
    if (!labelCol || !main.latest || !block.rows.length) return recordCards(block, ctx);
    const tagCols = cols.slice(1).filter(col => col !== main.latest && !main.earlier.includes(col) && col !== consequence);
    // A stated absence ("Not calculated: ...") is a sentence, not a value: a tile draws it as its own absence line, no tag; when every tile states the same one, the strip says it once beneath.
    const absent = (row, col) => TILE_ABSENCE.test(plain(cellText(row, col.at)).trim()) && fieldHtml(cellText(row, col.at), ctx) !== '';
    const common = tagCols.filter(col => block.rows.every(row => absent(row, col) && cellText(row, col.at) === cellText(block.rows[0], col.at)));
    const tiles = block.rows.map(row => {
      const raw = cellText(row, main.latest.at), below = [], notes = [];
      for (const col of main.earlier) {
        const text = cellText(row, col.at), shown = text === '' ? {} : earlierHtml(col, text, ctx);
        if (shown.below) below.push(shown.below); else if (shown.note) notes.push(shown.note);
      }
      return tile({label: fieldHtml(cellText(row, labelCol.at), ctx), value: valueHtml(raw, ctx), raw, below: below.join(' · '), notes: notes.concat(extrasOf(block, row, ctx)),
        tags: tagCols.filter(col => !absent(row, col)).map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => tag(col.label, html)),
        absences: tagCols.filter(col => absent(row, col) && !common.includes(col)).map(col => fieldHtml(cellText(row, col.at), ctx)),
        caption: consequence ? fieldHtml(cellText(row, consequence.at), ctx) : ''});
    }).join('');
    return shapeBlock('shape-measure', ctx, '', shapeBar('', traceOfBlock(ctx, block)) + `<div class="tiles tiles-4">${tiles}</div>` + common.map(col => `<p class="tiles-absent">${fieldHtml(cellText(block.rows[0], col.at), ctx)}</p>`).join(''));
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
      // A tile whose earlier and current cells are both empty has no pair to show: the empty marks beside an arrow would read as a change from nothing to nothing.
      const pair = a === '' && b === '' ? '' : `<div class="chg-pair">${side(before, a)}<span class="chg-arrow">${icon('arrow-right')}</span>${side(after, b)}</div>`;
      return `<article class="chg-card"><div class="chg-head"><p class="chg-title">${fieldHtml(title, ctx)}</p>${traceFor(ctx, row, rowLabelOf(block, ctx, row, title))}</div>${pair}${dumb}${fields ? `<dl class="rec-fields">${fields}</dl>` : ''}${extrasOf(block, row, ctx).map(html => `<p class="chg-x">${html}</p>`).join('')}</article>`;
    });
    return `<div class="chg-cards"${ctx.caption ? ` role="group" aria-label="${escapeHtml(ctx.caption)}"` : ''}>${cards.join('')}</div>`;
  }

  // ---- The non-numeric shape components (Task 6). A table of words is drawn by what its columns are, not by what it is called.
  // Every cell goes through fieldHtml (findingCell): a cell kept back for an identifier leaves its "In Evidence" link, a reference-only cell leaves nothing, and the
  // row's trace control reaches the rest. A table that does not fit its component (the column it needs is missing) is drawn by recordCards, never dropped.
  const plain = text => readerText().plainText(text);
  const labelNorm = col => col.label.trim().toLowerCase().replace(/_/g, ' ').replace(/\s+/g, ' ');
  // A trace control's name is drawn text (tooltip, accessible name): the title cell as the page shows it, and when findingCell held that cell back, its place in the table.
  const rowLabelOf = (block, ctx, row, title, subject = false) => `${findingCell(title, ctx).html !== undefined || (subject && isModuleName(title, ctx)) ? plain(title).trim() : `Row ${block.rows.indexOf(row) + 1}`}: where it comes from`;
  // The cells of a row beyond the table's headers have no label to stand under; each is drawn unlabelled, through findingCell, after the row's other fields.
  const extraList = (block, row, ctx) => extrasOf(block, row, ctx).map(html => `<p class="rec-x">${html}</p>`).join('');
  const levelColumn = (block, at) => { const cells = block.rows.map(row => cellText(row, at)).filter(text => text !== ''); return cells.length > 0 && cells.every(isLevel); };
  const levelMeter = word => `<span class="cr-conf"><span class="meter" aria-hidden="true">${[1, 2, 3].map(n => (n <= levelOf(word) ? '<i class="f"></i>' : '<i></i>')).join('')}</span><span class="meter-w">${escapeHtml(word)}</span></span>`;
  // The columns of a row that a card shows as label and value; a level column (every cell High, Medium or Low) is the three-segment meter with its word (C29).
  function fieldList(row, cols, ctx, levels = new Set()) {
    const items = cols.map(col => {
      const text = cellText(row, col.at), html = levels.has(col.at) && findingCell(text, ctx).html !== undefined ? levelMeter(text) : fieldHtml(text, ctx);
      return html === '' ? '' : `<div><dt>${escapeHtml(col.label)}</dt><dd>${html}</dd></div>`;
    }).join('');
    return items ? `<dl class="rec-fields">${items}</dl>` : '';
  }
  // "Bear (weakly)", "Documentary Fact (estimates)": the word, and what the cell says in its closing brackets as a tag. Both are the cell's own characters.
  function withQualifier(text) {
    const found = /^(.*?)\s*\(([^()]*)\)\s*$/.exec(text.trim());
    return found && found[1].trim() !== '' ? {word: found[1].trim(), qualifier: found[2].trim()} : {word: text.trim(), qualifier: ''};
  }
  const qualifierTag = (qualifier, ctx) => (qualifier === '' ? '' : `<span class="tag q-tag">${fieldHtml(qualifier, ctx)}</span>`);

  // A state word and the mark beside it. The word is the cell; the table of words below only picks which icon and which status token (state is never colour alone).
  const STATE_RULES = [
    ['bad', 'x', /\b(?:fail(?:s|ed|ure)?|blocked|breach(?:ed)?|rejected|refuted|removed|dropped)\b/i],
    ['warn', 'triangle-alert', /\b(?:needed|needs|partly|partial(?:ly)?|pending|unverified|unresolved|missing|absent|unavailable|unclear|open|insufficient|withheld|restricted|limited|requires)\b/i],
    ['ok', 'circle-check', /\b(?:ready|met|pass(?:ed)?|yes|complete[d]?|confirmed|sufficient|answered|supported|resolved|verified|cleared)\b/i],
    ['new', 'plus', /^(?:new|added)\b/i],
    ['same', 'check', /^(?:unchanged|same|no change)\b/i],
  ];
  // A state that is negated or cleared ("Not breached", "No breach", "Breach cleared", "No longer blocked") is neutral: neither failure nor success. The three
  // phrases named below are the key's own absent-data states and keep their warning mark.
  const ABSENT_STATE = /^not (?:in source set|found|assessable)\b/i, NEGATED_STATE = /^(?:not|no)\b|\bcleared\b|\bno longer\b/i;
  const NEUTRAL_STATE = {tone: 'info', icon: 'info'};
  function stateOf(text) {
    const word = plain(text).trim();
    if (ABSENT_STATE.test(word)) return {tone: 'warn', icon: 'triangle-alert'};
    if (NEGATED_STATE.test(word)) return NEUTRAL_STATE;
    const hit = STATE_RULES.find(([, , rx]) => rx.test(word));
    return hit ? {tone: hit[0], icon: hit[1]} : NEUTRAL_STATE;
  }
  function stateBadge(text, ctx) {
    const cell = findingCell(text, ctx);
    if (cell.html === undefined) return `<span class="state info">${icon('info')}${cell.inEvidence ? evidenceLink(ctx) : MISSING}</span>`;
    const {tone, icon: name} = stateOf(text);
    return `<span class="state ${tone}">${icon(name)}<span class="state-w">${cell.html}</span></span>`;
  }
  const listGroup = (cls, ctx, inner) => `<div class="${cls}" role="group"${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}>${inner}</div>`;

  // ---- status: C12, a checklist row per item, the state word beside its icon
  function statusChecklist(block, ctx) {
    const cols = visibleColumns(block, 'status', ctx), stateCol = cols.find(col => /status$/.test(labelNorm(col))), labelCol = cols.find(col => col !== stateCol);
    if (!stateCol || !labelCol || !block.rows.length) return recordCards(block, ctx);
    const rest = cols.filter(col => col !== stateCol && col !== labelCol), levels = new Set(rest.filter(col => levelColumn(block, col.at)).map(col => col.at));
    const rows = block.rows.map(row => {
      const title = cellText(row, labelCol.at), titleHtml = fieldHtml(title, ctx);
      return `<li class="ck-row"><div class="ck-head"><p class="ck-label">${titleHtml}</p>${stateBadge(cellText(row, stateCol.at), ctx)}${traceFor(ctx, row, rowLabelOf(block, ctx, row, title))}</div>${fieldList(row, rest, ctx, levels)}${extraList(block, row, ctx)}</li>`;
    }).join('');
    return `<ul class="ck-list" data-block${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}>${rows}</ul>`;
  }

  // ---- sided: C7, two columns chosen from the cell's own side word
  const OPPOSING_SIDES = [['bull', 'bear'], ['support', 'contradict'], ['for', 'against'], ['positive', 'negative'], ['upside', 'downside']];
  function sidedBoard(block, ctx) {
    const cols = visibleColumns(block, 'sided', ctx), sideCol = cols.find(col => /^side\b/.test(labelNorm(col))), labelCol = cols.find(col => col !== sideCol);
    if (!sideCol || !labelCol || !block.rows.length) return recordCards(block, ctx);
    const figCol = cols.find(col => col !== sideCol && col !== labelCol && numericLike(block, col.at)), rest = cols.filter(col => ![sideCol, labelCol, figCol].includes(col));
    const entries = block.rows.map(row => {
      const text = cellText(row, sideCol.at), {word, qualifier} = withQualifier(text), wordHtml = word === '' ? '' : fieldHtml(word, ctx);
      return {row, word: wordHtml === '' ? '' : word, wordHtml, qualifier, key: wordHtml === '' ? '' : plain(word).toLowerCase().replace(/^(support|contradict)s$/, '$1')};  // support and supports are one side word
    });
    const tally = new Map();
    entries.filter(entry => entry.key !== '').forEach(entry => tally.set(entry.key, {key: entry.key, n: (tally.get(entry.key)?.n ?? 0) + 1, first: tally.get(entry.key)?.first ?? entry}));
    // The two columns: a recognised opposing pair when both its words are in the table (left is the pair's first), else the first two distinct words in written order.
    const pair = OPPOSING_SIDES.find(([a, b]) => tally.has(a) && tally.has(b)), sides = pair ? pair.map(key => tally.get(key)) : [...tally.values()].slice(0, 2);
    const place = entry => (sides[0]?.key === entry.key ? 0 : sides[1]?.key === entry.key ? 1 : 2);
    // Each side's heading is the first thing in its own column, so the page reads one side, then the other.
    const heading = k => (sides[k] ? `<p class="sd-hs sd-s${k}"><i class="sd-dot" aria-hidden="true"></i>${sides[k].first.wordHtml}<b class="sd-n">${sides[k].n}</b></p>` : '');
    const caption = rest.length === 1 && entries.some(entry => fieldHtml(cellText(entry.row, rest[0].at), ctx) !== '') ? rest[0].label : '';
    const line = entry => {
      const at = place(entry), title = cellText(entry.row, labelCol.at), figure = figCol ? fieldHtml(cellText(entry.row, figCol.at), ctx) : '';
      // A card in a column titled with its side word does not draw the word again (screen readers keep it); a card on neither side draws it.
      const word = entry.wordHtml === '' ? '' : at === 2 ? `<span class="sd-side"><i class="sd-dot" aria-hidden="true"></i>${entry.wordHtml}</span>` : `<span class="sr-only">${entry.wordHtml}</span>`;
      const side = word === '' && entry.qualifier === '' ? '' : `${word}${qualifierTag(entry.qualifier, ctx)}`;
      // With one more field, its header is said once by the board; with several, each card keeps its labels.
      const fields = caption ? [rest[0]].map(col => fieldHtml(cellText(entry.row, col.at), ctx)).filter(html => html !== '').map(html => `<p class="sd-read">${html}</p>`).join('') : fieldList(entry.row, rest, ctx);
      // The trace control sits in the card's head row, beside the figure (beside the name when there is no figure); the side word and qualifier, when drawn, are a row above it.
      const name = `<p class="sd-name">${fieldHtml(title, ctx)}</p>`, fig = figure ? `<p class="sd-fig">${figure}</p>` : '';
      const drawnSide = (at === 2 && entry.wordHtml !== '') || entry.qualifier !== '';
      const card = `<article class="sd-entry">${drawnSide ? `<div class="sd-top">${side}</div>` : side}<div class="sd-head">${fig || name}${traceFor(ctx, entry.row, rowLabelOf(block, ctx, entry.row, title))}</div>${fig ? name : ''}${fields}${extraList(block, entry.row, ctx)}</article>`;
      return `<div class="sd-line sd-s${at}">${card}</div>`;
    };
    // Each side is its own column, its entries from the top in the table's order; a row on neither side stands full width beneath.
    const column = k => `<div class="sd-col sd-s${k}">${heading(k)}${entries.filter(entry => place(entry) === k).map(line).join('')}</div>`;
    const columns = sides.length ? `<div class="sd-cols">${column(0)}${column(1)}</div>` : '';
    return `<div class="sd-board" data-block role="group"${ctx.caption ? ` aria-label="${escapeHtml(ctx.caption)}"` : ''}>${caption ? `<p class="sd-cap">${escapeHtml(caption)}</p>` : ''}${columns}${entries.filter(entry => place(entry) === 2).map(line).join('')}</div>`;
  }

  // The module name of a row is the handoff's own text for what the row is about: "Source readiness (CP-0)" is drawn as written, though a lone "(CP-0)" would be a reference.
  // Only a cell that is one part (no `;` or `,`) of the form "<words> (CP-x)" and names no calculation or file; any other cell is read by findingCell like every cell.
  const MODULE_NAME = /^[^;,]*\S\s*\(CP-[0-9A-Z]+\)$/, FILE_NAME = new RegExp(`\\.(?:${FILE_EXTENSIONS})\\b`, 'i');
  // True when the bypass applies: findingCell omitted the cell as a reference only, and it is a module name. A period label (FY24) among the words is not an identifier.
  function isModuleName(text, ctx) {
    const cell = findingCell(text, ctx), raw = String(text).trim(), words = raw.slice(0, raw.lastIndexOf('('));
    // The words before the bracket hold no identifier of the module, no bare calculation-ID-shaped word and no file name, or the cell stays as findingCell read it.
    const idShaped = (words.match(/\b[A-Z]{1,2}\d{2}\b/g) ?? []).some(word => !shapes().PERIOD_LABEL.test(word.toLowerCase()));
    return cell.omitted && !cell.inEvidence && MODULE_NAME.test(raw) && tokensIn(words, ctx.tokens).length === 0 && !idShaped && !FILE_NAME.test(raw) && !calculationId().test(raw);
  }
  const subjectHtml = (text, ctx) => (isModuleName(text, ctx) ? readerText().richText(String(text).trim()) : fieldHtml(text, ctx));

  // ---- moduleState: C20, tiles; a state that repeats collapses to one tile with the state, the count and the rows in a <details>.
  // `ctx.countNoun` (a fixed word the page supplies, "modules") is the caption after the count; without it the caption is the name column's header, as written.
  const titleOf = (cls, html) => (html === '' ? '<span></span>' : `<p class="${cls}">${html}</p>`);  // a held-back title leaves a spacer, not an empty paragraph
  function moduleStateTiles(block, ctx) {
    const cols = visibleColumns(block, 'moduleState', ctx), stateCol = cols.find(col => labelNorm(col) === 'status'), nameCol = cols.find(col => col !== stateCol);
    if (!stateCol || !nameCol || !block.rows.length) return recordCards(block, ctx);
    const rest = cols.filter(col => col !== stateCol && col !== nameCol), stateKey = row => cellText(row, stateCol.at);  // identical text only: a variant of case or markup is its own tile
    const sizes = new Map();
    block.rows.forEach(row => sizes.set(stateKey(row), (sizes.get(stateKey(row)) ?? 0) + 1));
    const repeated = key => key !== '' && sizes.get(key) > 1, done = new Set(), tiles = [];
    for (const row of block.rows) {
      const key = stateKey(row), title = cellText(row, nameCol.at);
      if (!repeated(key)) {
        tiles.push(`<article class="ms-tile"><div class="ms-head">${titleOf('ms-title', subjectHtml(title, ctx))}${traceFor(ctx, row, rowLabelOf(block, ctx, row, title, true))}</div>${stateBadge(cellText(row, stateCol.at), ctx)}${fieldList(row, rest, ctx)}${extraList(block, row, ctx)}</article>`);
      } else if (!done.has(key)) {
        done.add(key);
        const same = block.rows.filter(other => stateKey(other) === key);
        const items = same.map(other => `<li><div class="ms-head">${titleOf('ms-name', subjectHtml(cellText(other, nameCol.at), ctx))}${traceFor(ctx, other, rowLabelOf(block, ctx, other, cellText(other, nameCol.at), true))}</div>${fieldList(other, rest, ctx)}${extraList(block, other, ctx)}</li>`).join('');
        tiles.push(`<article class="ms-tile ms-group"><div class="ms-head">${stateBadge(cellText(row, stateCol.at), ctx)}</div><details class="ms-list"><summary><b class="ms-n">${same.length}</b> ${ctx.countNoun ? '' : '· '}<span class="ms-nl">${escapeHtml(ctx.countNoun ?? nameCol.label)}</span><span class="ms-ch" aria-hidden="true">${icon('chevron-down')}</span></summary><ul>${items}</ul></details></article>`);
      }
    }
    return listGroup('ms-tiles', ctx, tiles.join(''));
  }

  // C20 on the Overview: one native-accordion tile per module, in the order the module rail groups them. `groups` is [{title, items}]; an item is {title, href, state, texts, trace, figure}
  // (its Bottom line paragraphs) or {title, href, choose: {count, href}} (saved outputs and none chosen). The collapsed tile shows the module's declared state (word and icon) and the
  // first sentence of its Bottom line; open, it shows the whole Bottom line and the link to the module. Every tile shares one `name`, so the browser keeps one open at a time.
  const NO_BOTTOM_LINE = 'No bottom line in this handoff.';
  const NOT_ASSESSABLE_MARK = '<span class="badge badge-gray">Not assessable</span>';
  function moduleTile(item, group) {
    // One line under the title for the marks (the module rail's Not assessable mark, the declared state): they never wrap and never sit beside the title.
    const marks = `${item.blocked ? NOT_ASSESSABLE_MARK : ''}${item.state ? stateBadge(item.state, {}) : ''}`, state = marks ? `<span class="mt-state">${marks}</span>` : '';
    const eyebrow = `<span class="eyebrow mt-group">${escapeHtml(group)}</span>`;
    if (item.choose) return `<div class="mt mt-plain">${eyebrow}<p class="mt-top"><span class="mt-name">${escapeHtml(item.title)}</span></p><p class="mt-lead">${item.choose.count} saved outputs, none chosen. <a class="in-ev" href="${escapeHtml(item.choose.href)}">Choose one</a></p></div>`;
    const [first] = paragraphs(item.texts || [], null);
    const lead = first ? first.show(...firstSentence(first.body).lead) : NO_BOTTOM_LINE;
    const body = paragraphs(item.texts || [], item.figure).map(p => `<p class="mt-p">${p.show(0, p.body.length)}${traceOf(item.trace, p.entry)}</p>`).join('');
    return `<details class="mt" name="overview-modules"><summary class="mt-head">${eyebrow}<span class="mt-top"><span class="mt-name">${escapeHtml(item.title)}</span><span class="mt-ch" aria-hidden="true">${icon('chevron-down')}</span></span>${state}<span class="mt-lead">${lead}</span></summary><div class="mt-body">${body}<a class="mt-open" href="${escapeHtml(item.href)}" aria-label="${escapeHtml(`Open module: ${item.title}`)}">Open module${icon('arrow-right')}</a></div></details>`;
  }
  // One continuous grid in the catalogue's order; each tile names its group in a small eyebrow, so no heading stands between rows.
  function moduleTiles(groups) {
    const tiles = groups.flatMap(group => group.items.map(item => moduleTile(item, group.title)));
    return tiles.length ? `<div class="mt-grid">${tiles.join('')}</div>` : '';
  }
  // C21 (library redesign, Task 11): one dot per module of a run, in the order given, coloured only by the state tokens and always carrying the state's icon, so a state is never colour alone.
  // `items` are {title, state, blocked, choose}: the module's catalogue title, its declared state as written (a usable one picks the tone and icon; its word joins the label), whether the
  // handoff says it is not assessable, and whether saved outputs were left unchosen. A module with no usable state is a hollow dot. Each dot is an image named by its label and shows it as a tooltip.
  function moduleDots(items) {
    if (!items.length) return '';
    const dot = item => {
      const usable = item.state && findingCell(item.state, {}).html !== undefined;
      // A module that ran has a glyph: its declared state's icon, the warning mark when not assessable, else the check of a completed module. Only unchosen saved outputs are a hollow ring.
      const mark = item.blocked ? {tone: 'warn', icon: 'triangle-alert'} : usable ? stateOf(item.state) : item.choose ? null : {tone: 'done', icon: 'check'};
      const word = item.blocked ? 'Not assessable' : usable ? plain(item.state).trim() : item.choose ? 'saved outputs, none chosen' : '';
      // The info tone is classed `neutral`: `.info` is the page's tooltip-button rule (raised, overlapping, hidden in print), which a dot must not meet.
      const tone = mark ? (mark.tone === 'info' ? 'neutral' : mark.tone) : 'none';
      return `<li class="mdot ${tone}"><span role="img" tabindex="0" ${tipAttributes(word ? `${item.title}: ${word}` : item.title)}>${mark ? icon(mark.icon) : ''}</span></li>`;
    };
    return `<ul class="mdots" aria-label="Modules in this run: ${items.length}">${items.map(dot).join('')}</ul>`;
  }
  // The first sentence of the first paragraph of a passage, as inline markup (the figures as the page draws them); '' when the passage has no text.
  function firstSentenceOf(texts, figure) {
    const [first] = paragraphs(texts || [], figure);
    return first ? first.show(...firstSentence(first.body).lead) : '';
  }
  // C31 (Task 11): the mark of a run's status. A running run shows a small lattice loader, which moves only inside the stylesheet's no-preference media query; every status has its word.
  // A stalled run (running or waiting) is a warning mark with its word, never colour alone, and no loader.
  const RUN_MARKS = {running: ['new', 'Running'], queued: ['same', 'Waiting'], done: ['ok', 'Done'], failed: ['bad', 'Failed'], stalled: ['warn', 'Stalled']};
  const LATTICE = `<span class="lat" aria-hidden="true">${'<i></i>'.repeat(9)}</span>`;
  function runMark(status, note = '', after = '') {
    if (!Object.hasOwn(RUN_MARKS, status)) return '';
    const [tone, word] = RUN_MARKS[status], glyph = {running: LATTICE, queued: icon('history'), done: icon('circle-check'), failed: icon('x'), stalled: icon('triangle-alert')}[status];
    return `<span class="state ${tone} rmark ${status}">${glyph}<span class="state-w">${word}${note ? ` · ${escapeHtml(note)}` : ''}</span>${after}</span>`;
  }
  // C13 (Task 11): a run's progress as connected steps, one segment per module in the order given. `steps` are {title, state} with state done, running or waiting (anything else waits).
  // Under the segments: the module(s) running now and how many are done of how many (counts of listed items). Only the running segment moves, by the stylesheet's own rule.
  // A running step may carry `note` (a clock reading, drawn after its name; `since` is the start time the page's re-load measures it from); done and waiting steps never draw one.
  const STEP_WORDS = {done: 'done', running: 'running', waiting: 'waiting'};
  // `options.labelled` draws each step as its module name with its C31 mark (a check, the loader or the queued mark, each with its word), so state reads without colour or hover;
  // the steps wrap. Without it the segments are unlabelled (the library home's compact row). A running step's note then sits on that step, and the caption keeps only the count.
  function runSteps(steps, options = {}) {
    if (!steps.length) return '';
    const kind = step => (Object.hasOwn(STEP_WORDS, step.state) ? step.state : 'waiting'), done = steps.filter(step => kind(step) === 'done').length;
    const running = steps.filter(step => kind(step) === 'running');
    const runningName = step => `${escapeHtml(step.title)}${step.note ? `<span class="steps-el"${step.since ? ` data-since="${escapeHtml(step.since)}"` : ''}> · ${escapeHtml(step.note)}</span>` : ''}`;
    const segment = step => `<li class="step ${kind(step)}" ${tipAttributes(`${step.title}: ${STEP_WORDS[kind(step)]}`)}></li>`;
    const clock = step => (step.note ? `<span class="steps-el"${step.since ? ` data-since="${escapeHtml(step.since)}"` : ''}> · ${escapeHtml(step.note)}</span>` : '');
    // State mark first, then the module name; a running step's clock is part of its mark ("Running · 37 min into the run"), so the phrase stays on the mark's line and wraps as one.
    const labelled = step => `<li class="step ${kind(step)}">${runMark({done: 'done', running: step.stalled ? 'stalled' : 'running', waiting: 'queued'}[kind(step)], '', kind(step) === 'running' ? clock(step) : '')}<span class="st-n">${escapeHtml(step.title)}</span></li>`;
    if (options.labelled) return `<div class="steps-w"><ol class="steps steps-l" aria-label="Modules, ${done} of ${steps.length} done">${steps.map(labelled).join('')}</ol><p class="steps-t"><span class="steps-n">${done} of ${steps.length} done</span></p></div>`;
    return `<div class="steps-w"><ol class="steps" aria-label="Modules, ${done} of ${steps.length} done">${steps.map(segment).join('')}</ol><p class="steps-t">${running.length ? `<span class="steps-now"><span class="steps-k">Running</span> ${running.map(runningName).join(', ')}</span>` : ''}<span class="steps-n">${done} of ${steps.length} done</span></p></div>`;
  }
  // Where a block on the Overview comes from: a link to the module page that holds it.
  const attribution = ({title, href}) => `<p class="from"><a href="${escapeHtml(href)}">From ${escapeHtml(title)}${icon('arrow-right')}</a></p>`;

  // ---- qa: C18, a native accordion; the answer-state column, when the table has one, is the badge
  function qaAccordion(block, ctx) {
    const cols = visibleColumns(block, 'qa', ctx), qCol = cols[0];
    if (!qCol || !block.rows.length) return recordCards(block, ctx);
    const stateCol = cols.find(col => col !== qCol && /(?:^|\s)(?:state|status)$|^answer$/.test(labelNorm(col))), rest = cols.filter(col => col !== qCol && col !== stateCol);
    const levels = new Set(rest.filter(col => levelColumn(block, col.at)).map(col => col.at));
    const items = block.rows.map(row => {
      const question = cellText(row, qCol.at), q = `<span class="qa-q">${fieldHtml(question, ctx)}</span>`, badge = stateCol ? stateBadge(cellText(row, stateCol.at), ctx) : '', body = fieldList(row, rest, ctx, levels) + extraList(block, row, ctx);
      const open = body ? `<details class="qa-d"><summary>${q}${badge}<span class="qa-ch" aria-hidden="true">${icon('chevron-down')}</span></summary><div class="qa-body">${body}</div></details>` : `<div class="qa-plain">${q}${badge}</div>`;
      return `<div class="qa-item">${open}${traceFor(ctx, row, rowLabelOf(block, ctx, row, question))}</div>`;
    }).join('');
    return listGroup('qa-list', ctx, items);
  }

  // ---- facts: C17, definition lists grouped by the category column
  function factList(block, ctx) {
    const cols = visibleColumns(block, 'facts', ctx), catCol = cols.find(col => labelNorm(col) === 'category'), factCol = cols.find(col => labelNorm(col) === 'fact');
    const labelCol = cols.find(col => col !== catCol && col !== factCol);
    if (!factCol || !labelCol || !block.rows.length) return recordCards(block, ctx);
    const rest = cols.filter(col => ![catCol, factCol, labelCol].includes(col)), groups = new Map();
    for (const row of block.rows) {
      const {word, qualifier} = catCol ? withQualifier(cellText(row, catCol.at)) : {word: '', qualifier: ''};
      if (!groups.has(word)) groups.set(word, []);
      groups.get(word).push({row, qualifier});
    }
    const sections = [...groups].map(([category, items]) => {
      const rows = items.map(({row, qualifier}) => {
        const label = cellText(row, labelCol.at), extra = rest.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => `<span class="fl-x"><b>${escapeHtml(col.label)}</b> ${html}</span>`).join('') + extrasOf(block, row, ctx).map(html => `<span class="fl-x">${html}</span>`).join('');
        return `<div class="fl-row"><dt>${fieldHtml(label, ctx)}</dt><dd><span class="fl-v">${valueHtml(cellText(row, factCol.at), ctx)}</span>${qualifierTag(qualifier, ctx)}${extra}${traceFor(ctx, row, rowLabelOf(block, ctx, row, label))}</dd></div>`;
      }).join('');
      const heading = category === '' ? '' : `<p class="fl-head">${fieldHtml(category, ctx)}<b class="fl-n">${items.length}</b></p>`;
      return `<section class="fl-group">${heading}<dl class="fl">${rows}</dl></section>`;
    }).join('');
    return listGroup('fl-groups', ctx, sections);
  }

  // ---- matrix: C16, the table's own row and column labels in their written order; the classification word is the cell's own
  const CLASS_WORDS = ['critical', 'high', 'medium', 'low'];
  const classOf = text => { const word = plain(text).trim().toLowerCase(); return CLASS_WORDS.includes(word) ? ` rm-c-${word}` : ''; };
  function riskMatrix(block, ctx) {
    const cols = visibleColumns(block, 'matrix', ctx), probCol = cols.find(col => labelNorm(col) === 'probability'), impCol = cols.find(col => labelNorm(col) === 'impact');
    const titleCol = cols.find(col => col !== probCol && col !== impCol);
    if (!probCol || !impCol || !titleCol || !block.rows.length) return recordCards(block, ctx);
    const classCol = cols.find(col => ![titleCol, probCol, impCol].includes(col) && /classification|rating|level|severity/.test(labelNorm(col))), rest = cols.filter(col => ![titleCol, probCol, impCol, classCol].includes(col));
    const rowsOf = [], colsOf = [], placed = [], loose = [];
    for (const row of block.rows) {
      const p = cellText(row, probCol.at), i = cellText(row, impCol.at);
      if (p === '' || i === '' || fieldHtml(p, ctx) === '' || fieldHtml(i, ctx) === '') { loose.push(row); continue; }
      if (!rowsOf.includes(p)) rowsOf.push(p);
      if (!colsOf.includes(i)) colsOf.push(i);
      placed.push({row, p, i});
    }
    // An axis whose labels all belong to Low / Medium / High (Moderate for Medium) is ordered by level: likelihood rows High to Low as the approved mock draws it, impact columns Low to High.
    const LEVEL_RANK = {low: 0, medium: 1, moderate: 1, high: 2}, byLevel = (labels, down) => (labels.every(label => Object.hasOwn(LEVEL_RANK, plain(label).trim().toLowerCase())) ? [...labels].sort((a, b) => (LEVEL_RANK[plain(a).trim().toLowerCase()] - LEVEL_RANK[plain(b).trim().toLowerCase()]) * (down ? -1 : 1)) : labels);
    rowsOf.splice(0, rowsOf.length, ...byLevel(rowsOf, true));
    colsOf.splice(0, colsOf.length, ...byLevel(colsOf, false));
    const chip = row => {
      const title = cellText(row, titleCol.at), word = classCol ? cellText(row, classCol.at) : '', wordHtml = word === '' ? '' : fieldHtml(word, ctx);
      const extra = rest.map(col => [col, fieldHtml(cellText(row, col.at), ctx)]).filter(([, html]) => html !== '').map(([col, html]) => `<span class="rm-x"><b>${escapeHtml(col.label)}</b> ${html}</span>`).join('') + extrasOf(block, row, ctx).map(html => `<span class="rm-x">${html}</span>`).join('');
      return `<li class="rm-chip${classCol ? classOf(word) : ''}"><div class="rm-top"><p class="rm-t">${fieldHtml(title, ctx)}</p>${traceFor(ctx, row, rowLabelOf(block, ctx, row, title))}</div>${wordHtml ? `<p class="rm-k"><span class="sr-only">${escapeHtml(classCol.label)}: </span>${wordHtml}</p>` : ''}${extra}</li>`;
    };
    const corner = `<span class="rm-cx">${escapeHtml(impCol.label)}${icon('arrow-right')}</span><span class="rm-cy">${escapeHtml(probCol.label)}${icon('arrow-right')}</span>`;
    const body = rowsOf.map(p => `<tr><th scope="row">${fieldHtml(p, ctx)}</th>${colsOf.map(i => { const here = placed.filter(entry => entry.p === p && entry.i === i); return `<td>${here.length ? `<ul class="rm-cell">${here.map(entry => chip(entry.row)).join('')}</ul>` : ''}</td>`; }).join('')}</tr>`).join('');
    const grid = rowsOf.length ? `<div class="rm-wrap" role="region" tabindex="0" aria-label="${escapeHtml(`${ctx.caption || 'Matrix'}: ${probCol.label} by ${impCol.label}`)}"><table class="rm-tbl" style="--cols:${colsOf.length}"><caption class="sr-only">${escapeHtml(`${ctx.caption || 'Matrix'}: ${probCol.label} down, ${impCol.label} across`)}</caption><thead><tr><th scope="col" class="rm-corner">${corner}</th>${colsOf.map(i => `<th scope="col">${fieldHtml(i, ctx)}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>` : '';
    const words = classCol ? [...new Set(block.rows.map(row => cellText(row, classCol.at)).filter(text => text !== '' && fieldHtml(text, ctx) !== ''))] : [];
    const legend = words.length ? `<p class="rm-lg"><span class="rm-lg-k">${escapeHtml(classCol.label)}</span>${words.map(word => `<span class="rm-lg-i${classOf(word)}"><i aria-hidden="true"></i>${fieldHtml(word, ctx)}</span>`).join('')}</p>` : '';
    const rest2 = loose.length ? `<div class="rm-loose"><p class="eyebrow">Not placed in the grid</p><ul class="rm-cell">${loose.map(chip).join('')}</ul></div>` : '';
    return shapeBlock('shape-matrix', ctx, '', shapeBar('', traceOfBlock(ctx, block)) + grid + legend + rest2);
  }

  // ---- watch: indicator, a leading or lagging icon with its word, the threshold as written, the limitation folded
  const WATCH_ICON = {leading: 'arrow-up-right', lagging: 'history'};
  const watchIcon = word => (Object.hasOwn(WATCH_ICON, word) ? WATCH_ICON[word] : 'activity');
  function watchList(block, ctx) {
    const cols = visibleColumns(block, 'watch', ctx), leadCol = cols.find(col => /leading/.test(labelNorm(col))), nameCol = cols.find(col => col !== leadCol);
    if (!leadCol || !nameCol || !block.rows.length) return recordCards(block, ctx);
    const limitCol = cols.find(col => col.kind === 'limitation'), thresholdCol = cols.find(col => ![leadCol, nameCol, limitCol].includes(col));
    const rest = cols.filter(col => ![leadCol, nameCol, limitCol, thresholdCol].includes(col));
    const items = block.rows.map(row => {
      const title = cellText(row, nameCol.at), word = cellText(row, leadCol.at), wordHtml = fieldHtml(word, ctx), threshold = thresholdCol ? fieldHtml(cellText(row, thresholdCol.at), ctx) : '';
      const mark = wordHtml === '' ? '' : `<span class="wl-lead">${icon(watchIcon(plain(word).trim().toLowerCase()))}${wordHtml}</span>`;
      const limit = limitCol ? fieldHtml(cellText(row, limitCol.at), ctx) : '', more = fieldList(row, rest, ctx) + extraList(block, row, ctx);
      const head = `<span class="wl-t">${fieldHtml(title, ctx)}</span>${mark}${threshold ? `<span class="wl-th">${threshold}</span>` : ''}`;
      const body = `${limit ? `<p class="wl-lim"><b>${escapeHtml(limitCol.label)}</b> ${limit}</p>` : ''}${more}`;
      return `<div class="wl-item">${body ? `<details class="wl-d"><summary>${head}<span class="wl-ch" aria-hidden="true">${icon('chevron-down')}</span></summary><div class="wl-body">${body}</div></details>` : `<div class="wl-plain">${head}</div>`}${traceFor(ctx, row, rowLabelOf(block, ctx, row, title))}</div>`;
    }).join('');
    return listGroup('wl-list', ctx, items);
  }

  // ---- C32: the empty state. A drawing the module states it could not make: its stated reasons, as written, beside ghost bars.
  const NOT_ESTABLISHED = 'Not established for this run';
  const STATED_ABSENCE = /^(?:not supplied:|none identified\b)/i;
  const emptyState = (title, reasons, tools = '') => `<div class="empty-state" role="status"><div class="ghost" aria-hidden="true"><i></i><i></i><i></i><i></i></div><div class="es-body"><p class="es-t">${escapeHtml(title)}</p>${reasons.length ? `<ul class="es-r">${reasons.map(html => `<li>${html}</li>`).join('')}</ul>` : ''}</div>${tools}</div>`;
  // The stated reasons of a table: its cells that state an absence ("Not supplied: <reason>", "None identified ..."), each distinct one once and as written. A visible column's reason goes through
  // findingCell (an identifier keeps the Evidence link in its place). A hidden column's cell that itself states an absence is the module's reason too (a map's last cell says why no edge can be
  // drawn), but only when it is clean: findingCell accepts it and it holds no file name, module code or hash; otherwise it is held back (`held`) and the Evidence link stands in.
  // An inter-module cell is drawn nowhere. `pure`: every visible cell with text states an absence. `found`: how many distinct stated cells there are.
  function statedReasons(block, cols, ctx) {
    const seen = new Set(), reasons = [], shownAt = new Set(cols.map(col => col.at)), out = {reasons, held: false, pure: true, found: 0};
    const stated = text => STATED_ABSENCE.test(plain(text).trim());
    const take = (text, hidden) => {
      if (seen.has(text)) return;
      seen.add(text); out.found += 1;
      const cell = findingCell(text, ctx);
      if (hidden && (cell.html === undefined || REFERENCE_IN_TEXT.some(rx => rx.test(plain(text))))) { out.held = true; return; }
      const html = fieldHtml(text, ctx);
      if (html !== '') reasons.push(html);
    };
    for (const row of block.rows) {
      const visible = [...cols.map(col => cellText(row, col.at)), ...row.cells.slice(block.headers.length).map(cell => String(cell ?? '').trim())].filter(text => text !== '');
      if (visible.some(text => !stated(text))) out.pure = false;
      visible.filter(stated).forEach(text => take(text, false));
      row.cells.slice(0, block.headers.length).forEach((cell, at) => {
        const text = String(cell ?? '').trim();
        if (!shownAt.has(at) && text !== '' && stated(text) && shapes().columnKind(block.headers[at]) !== 'intermodule') take(text, true);
      });
    }
    return out;
  }
  const absenceOf = (block, cols, ctx) => { const found = statedReasons(block, cols, ctx); return found.pure && found.found > 0 ? found : null; };
  const stateTools = (block, ctx, held) => `<div class="es-trace">${traceOfBlock(ctx, block)}</div>${held ? evidenceLink(ctx) : ''}`;
  // A dated table holds a dated event when some row's date cell states a date rather than an absence ("Not supplied: ...", "None identified ...") or nothing.
  const hasDatedEvent = block => block.rows.some(row => { const when = cellText(row, 0); return when !== '' && !STATED_ABSENCE.test(plain(when).trim()); });
  const absentBlock = (block, ctx, absent) => emptyState(NOT_ESTABLISHED, absent.reasons, stateTools(block, ctx, absent.held));
  // A drawing whose table states none (a chart the module could not draw): the empty state with the table's stated reasons, the same path as a lane or a map.
  // `stated` is the reason the build holds for the drawing: it stands in when the table itself states none.
  const gapState = (block, ctx, stated = '') => {
    const found = statedReasons(block, visibleColumns(block, 'records', ctx), ctx);
    const reasons = found.reasons.length || String(stated).trim() === '' ? found.reasons : [fieldHtml(String(stated).trim(), ctx)].filter(html => html !== '');
    return emptyState(NOT_ESTABLISHED, reasons, stateTools(block, ctx, found.held));
  };

  // ---- dated: C15, the dated timeline. Events stand in the table's own order, equally spaced; a date is drawn as written and no axis is invented.
  // Six events or fewer run across from 992px, more run down the page (grouped by year when every date opens with one); a page that gives the block a narrow column sets `ctx.stacked` to run them down. A category word is drawn with its icon;
  // the other cells (status, relevance, ...) are the event's detail; the Source column is the row's trace control only.
  const CATEGORY_ICONS = [[/debt|capital|financ|liquid/i, 'banknote'], [/corporate|company|governance|ownership/i, 'building'], [/legal|covenant|document/i, 'scale'], [/macro|rate|market|econom|currenc|hedg/i, 'globe']];
  const categoryIcon = word => (CATEGORY_ICONS.find(([rx]) => rx.test(word)) ?? [null, 'calendar-days'])[1];
  const ISO_DATE = /^(\d{4})(?:-\d{2}(?:-\d{2})?)?$/, HORIZONTAL_MAX = 6;
  function datedTimeline(block, ctx) {
    const cols = visibleColumns(block, 'dated', ctx), dateCol = cols.find(col => col.at === 0);
    const eventCol = cols.find(col => col !== dateCol && /^event\b/.test(labelNorm(col)) && !/\b(?:date|category|type)\b/.test(labelNorm(col)));
    if (!dateCol || !eventCol || !block.rows.length) return recordCards(block, ctx);
    const absent = absenceOf(block, cols, ctx);
    if (absent) return absentBlock(block, ctx, absent);
    const catCol = cols.find(col => col !== dateCol && col !== eventCol && /category/.test(labelNorm(col))), rest = cols.filter(col => ![dateCol, eventCol, catCol].includes(col));
    // `ctx.slot(row, n)` is markup the page adds under an entry (the library's run history puts a state mark, a module dot strip and a link there), `ctx.current(row, n)` marks the entry
    // the reader is on, and `ctx.unit` is the [singular, plural] the count names (default event). The entries stay the component's own.
    const unit = ctx.unit ?? ['event', 'events'];
    // One more column: its header is said once above the list, and each event carries the value alone.
    const lone = rest.length === 1 && block.rows.some(row => fieldHtml(cellText(row, rest[0].at), ctx) !== '') ? rest[0] : null;
    const items = block.rows.map((row, n) => {
      const when = cellText(row, dateCol.at), title = cellText(row, eventCol.at), word = catCol ? cellText(row, catCol.at) : '', wordHtml = word === '' ? '' : fieldHtml(word, ctx);
      const mark = icon(wordHtml === '' ? 'calendar-days' : categoryIcon(plain(word))), more = (lone ? [fieldHtml(cellText(row, lone.at), ctx)].filter(html => html !== '').map(html => `<p class="rec-x">${html}</p>`).join('') : fieldList(row, rest, ctx)) + extraList(block, row, ctx);
      const kind = wordHtml === '' ? '' : `<span class="tl-cat">${mark}${wordHtml}</span>`;
      return {when, html: `<li class="tl-i"${ctx.current?.(row, n) ? ' aria-current="true"' : ''}><div class="tl-d">${fieldHtml(when, ctx)}</div><div class="tl-row"><span class="tl-dot" aria-hidden="true">${mark}</span></div><div class="tl-b"><p class="tl-t">${fieldHtml(title, ctx)}</p>${kind}${more ? `<div class="tl-more">${more}</div>` : ''}${ctx.slot?.(row, n) ?? ''}${traceFor(ctx, row, rowLabelOf(block, ctx, row, title))}</div></li>`};
    });
    const years = items.map(item => ISO_DATE.exec(item.when)?.[1]);
    const vertical = Boolean(ctx.stacked) || items.length > HORIZONTAL_MAX, grouped = vertical && years.every(Boolean) && new Set(years).size > 1;
    const list = items.map((item, n) => (grouped && years[n] !== years[n - 1] ? `<li class="tl-yr" data-tick>${years[n]}</li>` : '') + item.html).join('');
    const bar = shapeBar(`<span class="eyebrow"><span data-count>${items.length}</span> ${items.length === 1 ? unit[0] : unit[1]}</span>`, lone ? `<span class="shape-cap">${escapeHtml(lone.label)}</span>` : '');
    return shapeBlock('shape-dated', ctx, '', `${bar}<ol class="tl ${vertical ? 'tl-v' : 'tl-h'}">${list}</ol>`);
  }

  // ---- edges: C14, the pathway. One layered diagram (a box per node, a curve per edge, the edge type its line style and its word), a legend of the type words, and a
  // relationship panel that opens on the box or line the reader selects. Below 768px, and in print, the diagram is a step list. Every cell the diagram cannot name is in the panel and the list.
  // A layer is the longest path from a node with no incoming edge; an edge that would close a loop is cut by first-seen row order and still drawn, below the nodes. Nothing is weighted.
  function mapLayers(edges, nodes = []) {
    const into = new Map(), out = new Map(), layer = new Map(), names = [];
    const reaches = (from, to, seen = new Set()) => from === to || (!seen.has(from) && seen.add(from) && (out.get(from) || []).some(next => reaches(next, to, seen)));
    const cut = edges.map(({from, to}) => {
      for (const name of [from, to]) if (!names.includes(name)) names.push(name);
      if (reaches(to, from)) return true;
      out.set(from, [...(out.get(from) || []), to]); into.set(to, [...(into.get(to) || []), from]);
      return false;
    });
    for (const name of nodes) if (!names.includes(name)) names.push(name);
    const depth = name => { if (!layer.has(name)) layer.set(name, Math.max(-1, ...(into.get(name) || []).map(depth)) + 1); return layer.get(name); };
    names.forEach(depth);
    return {names, layer: new Map(names.map(name => [name, layer.get(name)])), cut};
  }
  // A label wraps word-wise to what one line holds (`step` units wide, `char` per character), in at most `most` lines. `hard`: a word wider than a line breaks across lines, whole, before
  // any ellipsis; 'keep' leaves it whole on its own line; otherwise it is cut with an ellipsis. Text left after the last line ends in an ellipsis.
  function wrapLabel(label, step, char, hard, most) {
    const room = Math.max(4, Math.floor((step - 6) / char)), lines = [];
    for (const long of label.split(' ').filter(Boolean)) {
      let word = long;
      while (hard === true && word.length > room) { lines.push(word.slice(0, room)); word = word.slice(room); }
      const w = word.length > room && hard !== 'keep' ? `${word.slice(0, room - 1)}…` : word, last = lines.length - 1;
      if (last >= 0 && lines[last].length + 1 + w.length <= room && !lines[last].endsWith('…')) lines[last] += ` ${w}`;
      else lines.push(w);
    }
    if (lines.length <= most) return lines.length ? lines : [label];
    const kept = lines.slice(0, most), end = kept[most - 1].split(' ');
    while (end.length > 1 && end.join(' ').length + 1 > room) end.pop();
    const tail = end.join(' ');
    kept[most - 1] = tail.endsWith('…') ? tail : tail.length + 1 > room && hard !== 'keep' ? `${tail.slice(0, room - 1)}…` : `${tail}…`;
    return kept;
  }
  const MAP_DASH = ['', '7 4', '2 4', '9 3 2 3', '12 5 2 5'], BOX = {w: 150, h: 54, gx: 120, gy: 22, pad: 12}, MAP_CHAR = 6.6;
  const MAP_T = Array.from({length: 39}, (_, i) => (i + 1) / 40).sort((a, b) => Math.abs(a - .5) - Math.abs(b - .5));
  const LABEL_CHAR = 6.6, LABEL_STEP = 15, LABEL_MARGIN = 20, LABEL_STEPS = 24, LABEL_WRAP = 106, LABEL_LINES = 2, LABEL_LINE = 13;
  // The layered SVG of `edges` ([{from, to, type}], plain text). `uid` names its arrow marker; `svgAttrs` is the <svg> element's role and name; `nodeAttrs(name, at)` and `edgeAttrs(at)`,
  // when given, make each node and each edge a control (an edge then is a group of its hit area, line and label). Returns the markup, the loops cut and the line style of each type word.
  function pathwayDiagram(edges, {uid, svgAttrs, nodeAttrs, edgeAttrs}) {
    const {names, layer, cut} = mapLayers(edges), {w, h, gy, pad} = BOX;
    // The column gap holds the longest label of an edge drawn between columns (a cut edge's label sits below the nodes), never under BOX.gx, so a map of short labels stays compact.
    // A label wraps on whole words to at most two lines (LABEL_WRAP holds 15 characters; one longer word keeps its own line), so the gap follows the longest line.
    const wrap = edges.map(edge => (edge.type === '' ? [] : wrapLabel(edge.type, LABEL_WRAP, LABEL_CHAR, 'keep', LABEL_LINES))), wide = wrap.map(lines => Math.max(0, ...lines.map(line => line.length)) * LABEL_CHAR);
    const gx = Math.max(BOX.gx, Math.ceil(Math.max(0, ...wide.filter((_, i) => !cut[i])) + LABEL_MARGIN));
    const slot = new Map(), filled = [], types = [...new Set(edges.map(edge => edge.type).filter(type => type !== ''))];
    for (const name of names) { const l = layer.get(name); slot.set(name, filled[l] ?? 0); filled[l] = (filled[l] ?? 0) + 1; }
    const at = name => ({x: pad + layer.get(name) * (w + gx), y: pad + slot.get(name) * (h + gy)});
    const width = pad * 2 + filled.length * (w + gx) - gx, loops = cut.filter(Boolean).length, base = pad * 2 + Math.max(...filled) * (h + gy) - gy + (loops ? 46 : 0);
    const path = ({from, to}, back) => {
      const a = at(from), b = at(to), mid = (a.x + b.x + w) / 2;
      if (!back) return {d: `M${a.x + w} ${a.y + h / 2}C${mid} ${a.y + h / 2} ${mid} ${b.y + h / 2} ${b.x} ${b.y + h / 2}`, c: [[a.x + w, a.y + h / 2], [mid, a.y + h / 2], [mid, b.y + h / 2], [b.x, b.y + h / 2]]};
      const low = Math.max(a.y, b.y) + h + 34, x1 = a.x + w / 2 + (from === to ? -30 : 0), x2 = b.x + w / 2 + (from === to ? 30 : 0);
      return {d: `M${x1} ${a.y + h}C${x1} ${low} ${x2} ${low} ${x2} ${b.y + h}`, c: [[x1, a.y + h], [x1, low], [x2, low], [x2, b.y + h]]};
    };
    const bezier = (c, t) => [0, 1].map(k => (1 - t) ** 3 * c[0][k] + 3 * (1 - t) ** 2 * t * c[1][k] + 3 * (1 - t) * t * t * c[2][k] + t ** 3 * c[3][k]);
    const boxes = names.map(name => ({...at(name), w, h})), placed = [], paths = edges.map((edge, i) => path(edge, cut[i]));
    const near = paths.map(p => Array.from({length: 61}, (_, k) => bezier(p.c, k / 60)));
    const gap = (pts, x, y) => Math.min(...pts.map(([px, py]) => Math.hypot(px - x, py - y)));
    // A label is a box: its longest line wide, 12px tall a line (13px apart), centred on its spot. It tries a spot on its own line, then moves up or down by whole steps,
    // to the first clear spot (no placed label, no node) that is not nearer another edge than its own. Where another edge crosses its middle it tries nearer its source end
    // (t .25) or its target end (t .75) first, alternating by edge, so crossing labels are not stacked at the shared middle. Room is made, not borrowed: a spot below the drawing grows its height.
    const span = (y, n) => [y - 9 - (n - 1) * LABEL_LINE / 2, y + 3 + (n - 1) * LABEL_LINE / 2];
    const clear = (x, y, lw, n) => { const [top, bot] = span(y, n); return placed.every(o => Math.abs(o.x - x) >= (o.w + lw) / 2 || top >= o.bot + 2 || o.top >= bot + 2) && boxes.every(b => x + lw / 2 <= b.x - 2 || x - lw / 2 >= b.x + b.w + 2 || bot <= b.y - 2 || top >= b.y + b.h + 2); };
    const spot = (i, lw, n) => {
      const c = paths[i].c, steps = [0]; for (let k = 1; k <= LABEL_STEPS; k++) steps.push(-k, k);
      const [mx, my] = bezier(c, .5), crossed = near.some((pts, k) => k !== i && gap(pts, mx, my) < LABEL_STEP * 2), pref = i % 2 ? .75 : .25, ts = crossed ? [...MAP_T].sort((p, q) => Math.abs(p - pref) - Math.abs(q - pref)) : MAP_T;
      for (const own of [true, false]) for (const dy of steps) for (const t of ts) {
        const [x, y] = bezier(c, t), top = y - 4 + dy * LABEL_STEP;
        if (top - (n - 1) * LABEL_LINE / 2 >= 10 && clear(x, top, lw, n) && (!own || near.every((pts, k) => k === i || gap(pts, x, top - 4) >= gap(near[i], x, top - 4)))) return {x, y: top};
      }
      // LABEL_STEPS (24 steps, 360px) is the bound; past it the label sits at the line's midpoint, over its neighbours, rather than grow the drawing without end.
      const [x, y] = bezier(c, .5); return {x, y: y - 4};
    };
    const marker = `map-arrow-${uid}`, round = n => Math.round(n * 10) / 10;
    const drawn = edges.map((edge, i) => {
      const dash = edge.type === '' ? '' : MAP_DASH[types.indexOf(edge.type) % MAP_DASH.length];
      const line = `<path class="map-edge${cut[i] ? ' cut' : ''}" d="${paths[i].d}" marker-end="url(#${marker})"${dash ? ` stroke-dasharray="${dash}"` : ''}/>`;
      let label = '';
      if (edge.type !== '') {
        const lines = wrap[i], q = spot(i, wide[i], lines.length), [top, bot] = span(q.y, lines.length), y0 = q.y - (lines.length - 1) * LABEL_LINE / 2;
        placed.push({...q, w: wide[i], top, bot});
        label = `<text class="map-edge-label" x="${round(q.x)}" y="${round(y0)}" text-anchor="middle">${lines.map((text, k) => `<tspan x="${round(q.x)}" dy="${k ? LABEL_LINE : 0}">${escapeHtml(text)}</tspan>`).join('')}${lines.join(' ') === edge.type ? '' : `<title>${escapeHtml(edge.type)}</title>`}</text>`;
      }
      return edgeAttrs ? `<g class="map-eg" ${edgeAttrs(i)}><path class="map-hit" d="${paths[i].d}"/>${line}${label}</g>` : line + label;
    }).join('');
    const height = Math.ceil(Math.max(base, ...placed.map(o => o.bot + 3)));
    const nodes = names.map((name, i) => {
      const p = at(name), lines = wrapLabel(name, w - 10, MAP_CHAR, true, 3);
      return `<g class="map-node"${nodeAttrs ? ` ${nodeAttrs(name, i)}` : ''}><title>${escapeHtml(name)}</title><rect x="${p.x}" y="${p.y}" width="${w}" height="${h}" rx="4"/><text x="${p.x + 8}" y="${p.y + h / 2 + 4 - 7 * (lines.length - 1)}">${lines.map((line, k) => `<tspan x="${p.x + 8}" dy="${k ? 14 : 0}">${escapeHtml(line)}</tspan>`).join('')}</text></g>`;
    }).join('');
    const defs = `<defs><marker id="${marker}" viewBox="0 0 8 8" refX="8" refY="4" markerWidth="8" markerHeight="8" orient="auto"><path class="map-arrow" d="M0 0L8 4L0 8z"/></marker></defs>`;
    return {names, types, dash: type => MAP_DASH[types.indexOf(type) % MAP_DASH.length], loops, svg: `<svg ${svgAttrs} width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${defs}${drawn}${nodes}</svg>`};
  }
  const loopNote = loops => (loops ? `<p class="map-note">${loops} edge${loops === 1 ? '' : 's'} would close a loop: drawn below the nodes, in the order the handoff states them.</p>` : '');

  const legendLine = dash => `<svg class="map-lg" width="34" height="8" viewBox="0 0 34 8" aria-hidden="true" focusable="false"><line x1="0" y1="4" x2="34" y2="4" stroke="currentColor" stroke-width="2"${dash ? ` stroke-dasharray="${dash}"` : ''}/></svg>`;
  function pathwayFlow(block, ctx) {
    const cols = visibleColumns(block, 'edges', ctx), column = rx => cols.find(col => rx.test(labelNorm(col)));
    const fromCol = column(/^from$/), toCol = column(/^to$/), relCol = column(/^relationship/), typeCol = column(/^edge type$|\btype$/);
    if (!fromCol || !toCol || !block.rows.length) return recordCards(block, ctx);
    const absent = absenceOf(block, cols, ctx);
    if (absent) return absentBlock(block, ctx, absent);
    // A node is its cell as the page reads it; a cell the page holds back cannot name a node, and the table is then drawn as record cards, never with a node left out.
    const nameOf = (row, col) => (findingCell(cellText(row, col.at), ctx).html === undefined ? '' : plain(cellText(row, col.at)).trim());
    const edges = block.rows.map(row => ({from: nameOf(row, fromCol), to: nameOf(row, toCol), type: typeCol ? nameOf(row, typeCol) : ''}));
    if (edges.some(edge => edge.from === '' || edge.to === '')) return recordCards(block, ctx);
    const rest = cols.filter(col => ![fromCol, toCol, relCol, typeCol].includes(col)), uid = `${ctx.id ?? 'o'}-${block.line ?? 0}`.replace(/\W/g, '-'), label = `${ctx.caption || 'Pathway'}`;
    const names = mapLayers(edges).names, touching = name => edges.flatMap((edge, k) => (edge.from === name || edge.to === name ? [k] : []));
    const ends = k => [names.indexOf(edges[k].from), names.indexOf(edges[k].to)].join(' ');
    const diagram = pathwayDiagram(edges, {
      uid, svgAttrs: `role="group" aria-label="${escapeHtml(`${label}: ${names.length} nodes, ${edges.length} edges`)}"`,
      nodeAttrs: (name, i) => `role="button" tabindex="0" aria-pressed="false" aria-label="${escapeHtml(name)}" data-map-pick="n:${i}" data-map-edges="${touching(name).join(' ')}" data-map-nodes="${[i, ...touching(name).flatMap(k => ends(k).split(' ').map(Number))].filter((n, p, all) => all.indexOf(n) === p).join(' ')}"`,
      edgeAttrs: k => `role="button" tabindex="0" aria-pressed="false" aria-label="${escapeHtml(`${edges[k].from} to ${edges[k].to}${edges[k].type ? `, ${edges[k].type}` : ''}`)}" data-map-pick="e:${k}" data-map-edges="${k}" data-map-nodes="${ends(k)}"`,
    });
    const detail = (row, edge) => {
      const rel = relCol ? fieldHtml(cellText(row, relCol.at), ctx) : '';
      return {rel, trace: traceFor(ctx, row, `${edge.from} to ${edge.to}: where it comes from`), more: fieldList(row, rest, ctx) + extraList(block, row, ctx)};
    };
    const arrowTo = (edge, mark) => `<span>${escapeHtml(edge.from)}</span>${mark}<span>${escapeHtml(edge.to)}</span>${edge.type ? `<span class="pw-et">${escapeHtml(edge.type)}</span>` : ''}`;
    const panels = block.rows.map((row, k) => { const d = detail(row, edges[k]); return `<div class="rel" data-rel="${k}" hidden><p class="rel-ft">${arrowTo(edges[k], icon('arrow-right'))}${d.trace}</p>${d.rel ? `<p class="rel-t">${d.rel}</p>` : ''}${d.more}</div>`; }).join('');
    const steps = block.rows.map((row, k) => {
      const d = detail(row, edges[k]), edge = edges[k];
      return `<li class="pw-step"><span class="pw-n" data-count>${k + 1}</span><div class="pw-fr">${escapeHtml(edge.from)}</div><div class="pw-ar">${icon('arrow-down')}${edge.type ? `<span class="pw-et">${escapeHtml(edge.type)}</span>` : ''}</div><div class="pw-fr">${escapeHtml(edge.to)}</div>${d.rel ? `<p class="pw-rl">${d.rel}</p>` : ''}${d.more}${d.trace}</li>`;
    }).join('');
    const legend = diagram.types.length ? `<div class="map-legend">${diagram.types.map(type => `<span>${legendLine(diagram.dash(type))}${escapeHtml(type)}</span>`).join('')}</div>` : '';
    const region = `${label}. Select a box or a line to read the relationship; scroll horizontally if the drawing is wider than its card`;
    const wideMap = `<div class="map-wide"><div class="map-scroll" role="region" aria-label="${escapeHtml(region)}" tabindex="0">${diagram.svg}</div>${loopNote(diagram.loops)}${legend}<div class="map-panel" data-map-panel aria-live="polite"><p class="map-hint" data-map-hint>Select a box or a line to read the relationship.</p>${panels}</div></div>`;
    const bar = shapeBar(`<span class="eyebrow"><span data-count>${edges.length}</span> ${edges.length === 1 ? 'relationship' : 'relationships'}</span>`, '');
    return shapeBlock('shape-pathway', ctx, 'data-selected=""', `${bar}${wideMap}<ol class="map-steps">${steps}</ol>`);
  }

  // A node or an edge of a pathway was chosen (click or Enter): it is pressed, its relationships are shown in the panel, the boxes at their ends are marked. Choosing it again clears the panel.
  function selectOnMap(pick) {
    const root = pick.closest('.shape-pathway'), key = root.dataset.selected === pick.dataset.mapPick ? '' : pick.dataset.mapPick;
    root.dataset.selected = key;
    const list = value => (value ? value.split(' ') : []), shown = key === '' ? [] : list(pick.dataset.mapEdges), marked = key === '' ? [] : list(pick.dataset.mapNodes);
    root.querySelectorAll('[data-map-pick]').forEach(item => item.setAttribute('aria-pressed', String(key !== '' && item.dataset.mapPick === key)));
    root.querySelectorAll('[data-rel]').forEach(rel => { rel.hidden = !shown.includes(rel.dataset.rel); });
    root.querySelectorAll('[data-map-hint]').forEach(hint => { hint.hidden = key !== ''; });
    root.querySelectorAll('[data-map-pick]').forEach(item => item.classList.toggle('on', key !== '' && item.dataset.mapPick === key));
    root.querySelectorAll('.map-node').forEach(node => node.classList.toggle('hl', marked.includes(node.dataset.mapPick.slice(2))));
    root.querySelectorAll('.map-eg').forEach(edge => edge.classList.toggle('hl', shown.includes(edge.dataset.mapPick.slice(2))));
  }

  // The dispatch: one component per shape; every shape without one (and any table a component cannot place) is a record card.
  const SHAPE_COMPONENTS = {cases: casesBlock, caseRows: caseRowsBlock, ranked: rankedLadder, statement: statementCard, metric: metricTiles, measure: measureTiles, change: changeCards,
    status: statusChecklist, sided: sidedBoard, moduleState: moduleStateTiles, qa: qaAccordion, facts: factList, records: recordCards, matrix: riskMatrix, watch: watchList, dated: datedTimeline, edges: pathwayFlow};
  // Documented fail-open (review M4): a table a component cannot draw is logged (its caption and the error) and drawn as this stated empty state with its Evidence link; the other blocks of the page are untouched.
  const BLOCK_FAILED = 'This table could not be drawn';
  function render(shape, block, ctx) {
    try {
      return (Object.hasOwn(SHAPE_COMPONENTS, shape) ? SHAPE_COMPONENTS[shape] : recordCards)(block, ctx);
    } catch (error) {
      console.error(`Components.render: the ${shape} table "${ctx?.caption ?? (block?.headers ?? []).join(' | ')}" could not be drawn`, error);
      return emptyState(BLOCK_FAILED, [], ctx ? evidenceLink(ctx) : '');
    }
  }

  // Print shows the text of a folded <details>: the ones these components draw are opened for the print and put back as they were. `root` is the document.
  const FOLDS = '.qa-d, .wl-d, .ms-list, .mt, .chg-fold, .change-module';
  function foldsForPrint(root, printing) {
    root.querySelectorAll(FOLDS).forEach(fold => {
      if (printing) { if (fold.dataset.wasOpen === undefined) fold.dataset.wasOpen = String(fold.open); fold.open = true; } else if (fold.dataset.wasOpen !== undefined) { fold.open = fold.dataset.wasOpen === 'true'; delete fold.dataset.wasOpen; }
    });
  }
  if (typeof window !== 'undefined' && typeof document !== 'undefined' && window.addEventListener) {
    window.addEventListener('beforeprint', () => foldsForPrint(document, true));
    window.addEventListener('afterprint', () => foldsForPrint(document, false));
  }

  // The page's own state for these components: which case is chosen, which view is shown. Called from screen.js's click handler; true when the click was handled.
  function handleClick(target) {
    const mapPick = target?.closest?.('[data-map-pick]');
    if (mapPick) { selectOnMap(mapPick); return true; }
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

  const Components = {stateOf, stateBadge, moduleDots, firstSentenceOf, runMark, runSteps, icon, traceButton, traceRow, headerChips, placePill, toast, dismissToasts, toastHost, tipAttributes, verdictPanel, findingsFeed, callout, limitationsBlock, recordCards, findingCell, render, casesBlock, caseRowsBlock, rankedLadder, statementCard, metricTiles, measureTiles, changeCards, statusChecklist, sidedBoard, moduleStateTiles, hasDatedEvent, metricStrip, moduleTiles, attribution, qaAccordion, factList, riskMatrix, watchList, datedTimeline, pathwayFlow, emptyState, gapState, chartTable, viewToggle, pane, visibleColumns, loopNote, mapLayers, pathwayDiagram, foldsForPrint, paragraphText, handleClick, sectionRail, ICON_PATHS};
  if (typeof window !== 'undefined') window.Components = Components;
  if (typeof document !== 'undefined' && document.body) {
    toastHost();
    document.addEventListener('keydown', event => { if (event.key === 'Escape') dismissToasts(); });
  }
  if (typeof module !== 'undefined') module.exports = Components;
})();

'use strict';
// Pure reader logic for the 2026-11-11 handoff contract (docs/rulings/2026-11-11-reader-and-issuer-report.md, H1 to H7):
// no DOM, no store, no globals read. Browser: the functions below are globals. Node: module.exports.
// Inputs are the store's shapes: a section is {heading, level, line, blocks[]}; a text block is {type:'text', text}.

const PASSAGE_HEADINGS = {
  bottom: 'Bottom line',
  key: 'Key findings',
  contrary: 'Contrary evidence and what would change the view',
  limits: 'Limitations',
};

// The H3 sections under the first `## Findings` H2, in order; empty when the handoff has none.
function findingsH3(sections) {
  const list = sections || [];
  const start = list.findIndex(s => s.level === 2 && s.heading === 'Findings');
  if (start < 0) return [];
  const found = [];
  for (const section of list.slice(start + 1)) {
    if (section.level === 2) break;
    if (section.level === 3) found.push(section);
  }
  return found;
}

// H1: the four reader passages, each the H3 section with the exact heading under Findings, or null.
function readerPassages(sections) {
  const h3 = findingsH3(sections);
  const out = {};
  for (const [key, heading] of Object.entries(PASSAGE_HEADINGS)) out[key] = h3.find(s => s.heading === heading) || null;
  return out;
}

// H7: new format iff the first H3 after `## Findings` is `Bottom line`.
function isNewFormat(sections) {
  const h3 = findingsH3(sections);
  return h3.length > 0 && h3[0].heading === PASSAGE_HEADINGS.bottom;
}

// H7: a run is "Earlier format" when any of its handoffs (each a sections array) is not new format.
function earlierFormatRun(outputsSections) {
  return (outputsSections || []).some(sections => !isNewFormat(sections));
}

const sectionText = section => (section ? section.blocks.filter(b => b.type === 'text').map(b => b.text).join('\n') : '');

// Not assessable: new format by the engine contract (the launcher makes a blocked module's Bottom line BEGIN exactly `Not assessable: `
// and forbids the phrase in a non-blocked Bottom line); earlier format by the store's own state.established === false.
function blocked(sections, state) {
  if (isNewFormat(sections)) {
    const bottom = readerPassages(sections).bottom;
    const first = bottom && bottom.blocks.find(b => b.type === 'text');
    return !!first && first.text.startsWith('Not assessable:');
  }
  return !!state && state.established === false;
}

// H3: the paragraph's last line, when it starts exactly `Basis: `, is the Basis line. Items split on "; ", one final full stop dropped.
// `known` (optional) lists source file names: a known name that itself contains "; " is kept whole (with its ", page N" tail) instead of
// being split into two items. With no list, or no match, the split is on every "; ".
function splitBasis(text, known = []) {
  const lines = String(text).split('\n');
  const last = lines[lines.length - 1];
  if (!last.startsWith('Basis: ')) return {body: String(text), items: []};
  const pieces = last.slice('Basis: '.length).trimEnd().replace(/\.$/, '').split('; ');
  const split = known.filter(name => name.includes('; ')).sort((a, b) => b.length - a.length);
  const items = [];
  for (let i = 0; i < pieces.length; i += 1) {
    const hit = split.map(name => ({name, take: name.split('; ').length})).find(({name, take}) => {
      const joined = pieces.slice(i, i + take).join('; ');
      return joined === name || joined.startsWith(`${name},`);
    });
    if (hit) { items.push(pieces.slice(i, i + hit.take).join('; ').trim()); i += hit.take - 1; }
    else items.push(pieces[i].trim());
  }
  return {body: lines.slice(0, -1).join('\n'), items: items.filter(item => item !== '')};
}

// One page or range, and a list of them (decision 3 of the 2026-11-12 ruling extends H3: `pages 71, 121`, `pages 55, 63, 120–123`).
const SPAN = '\\d+(?:\\s*[–-]\\s*\\d+)?', PAGES = new RegExp(`^(?:, (pages?) (${SPAN}(?:, ${SPAN})*))?$`);
const spansOf = text => [...text.matchAll(/(\d+)(?:\s*[–-]\s*(\d+))?/g)].map(m => (m[2] === undefined ? {page: Number(m[1])} : {page: Number(m[1]), pageEnd: Number(m[2])}));
// A source item: `page`/`pageEnd` for one page or range, `spans` for a list (a singular marker lists one page only); null when the tail is no page list.
function sourceItem(file, tail) {
  const pages = PAGES.exec(tail);
  if (!pages) return null;
  const out = {kind: 'source', file};
  if (pages[1] === undefined) return out;
  const spans = spansOf(pages[2]);
  if (spans.length === 1) return Object.assign(out, spans[0]);
  return pages[1] === 'pages' ? Object.assign(out, {spans}) : null;
}

// H3 item forms. Anything else is kept as text, never dropped. `known` (optional) lists source file names: an item that is exactly a known name
// (with an optional ", page N" / ", pages N-M" tail) is a source even when the name has no extension; nothing else is guessed.
function basisItem(item, known = []) {
  const calculation = /^calculation (\S+)$/.exec(item);
  if (calculation) return {kind: 'calculation', id: calculation[1]};
  const upstream = /^(.+) \((CP-[A-Z0-9]+)\)$/.exec(item);
  if (upstream) return {kind: 'module', name: upstream[1], code: upstream[2]};
  // Array.prototype.map passes an index as a second argument: anything but a list is no list.
  for (const name of [...(Array.isArray(known) ? known : [])].sort((a, b) => b.length - a.length)) {
    if (item === name || item.startsWith(`${name},`)) {
      const found = sourceItem(name, item.slice(name.length));
      if (found) return found;
    }
  }
  const source = /^(.+?\.[A-Za-z][A-Za-z0-9]{0,4})((?:, pages? .+)?)$/.exec(item);
  return (source && sourceItem(source[1], source[2])) || {kind: 'text', text: item};
}

// The source file names at hand for a paragraph: `ctx.files` when the caller supplies the run's files, and the file of every source-page chip of the key.
function knownFiles(ctx) {
  return [...new Set([...(ctx.files || []), ...ctx.chips.filter(c => c.kind === 'issuer_page' && c.file).map(c => c.file)])];
}

// One Basis item resolved for the inspector (H3), shared by the page and its tests. `ctx` is {sections, chips, ran(code)}: the handoff's sections
// (for `calculation <id>`), the chips the build holds for the paragraph's key, and whether a module code ran in this run. A source item takes the
// issuer_page chips of its file (and page when it names one); a calculation item takes its `## Calculations` row (or null); a module item says
// whether it ran; any other item is `text`, verbatim.
// A source item names the chip's page when it names no page, the same page, or a page of its list.
const pageHit = (item, chip) => (item.spans ? item.spans.some(s => s.page === chip.page) : item.page === undefined || chip.page === item.page);
function inspectorItem(raw, ctx) {
  const item = basisItem(raw, knownFiles(ctx));
  const out = {...item, raw};
  if (item.kind === 'source') out.chips = ctx.chips.filter(c => c.kind === 'issuer_page' && c.file === item.file && pageHit(item, c));
  else if (item.kind === 'calculation') out.row = calculationRow(ctx.sections, item.id);
  else if (item.kind === 'module') out.ran = Boolean(ctx.ran(item.code));
  return out;
}

// The chips of one key with a chip the build holds twice listed once (same content), in first-seen order.
function uniqueChips(chips) {
  const seen = new Set();
  return chips.filter(chip => { const id = JSON.stringify(chip); return seen.has(id) ? false : (seen.add(id), true); });
}

// The inspector's Basis items for one paragraph's text (new format), in the handoff's order.
function inspectorItems(text, ctx) {
  return splitBasis(text, knownFiles(ctx)).items.map(raw => inspectorItem(raw, ctx));
}

// The pages of a source item as words: "page 41", "pages 43–45", "pages 71, 121", or nothing.
function itemPages(item) {
  if (item.spans) return `pages ${item.spans.map(s => (s.pageEnd === undefined ? s.page : `${s.page}–${s.pageEnd}`)).join(', ')}`;
  return item.pageEnd !== undefined ? `pages ${item.page}–${item.pageEnd}` : item.page !== undefined ? `page ${item.page}` : '';
}

// One resolved Basis item (inspectorItem) as the inspector's <li>, in words. `deps` are the page's drawing helpers: chipSection(chip) (HTML of one
// source-page chip), moduleHref(code), icon(name).
function inspectorItemHtml(item, deps) {
  if (item.kind === 'source') {
    const pages = itemPages(item);
    return `<li><strong>${escapeHtml(item.file)}</strong>${pages ? `, ${escapeHtml(pages)}` : ''}${item.chips.map(c => deps.chipSection(c)).join('')}</li>`;
  }
  if (item.kind === 'calculation') {
    const row = item.row;
    if (!row) return `<li>${escapeHtml(item.raw)}<span class="small"> (no row with this ID in the handoff's Calculations table)</span></li>`;
    return `<li>Calculation ${escapeHtml(item.id)}<dl class="calculation-row">${row.headers.map((header, i) => `<div><dt>${escapeHtml(header)}</dt><dd>${richText(row.cells[i] ?? '')}</dd></div>`).join('')}</dl></li>`;
  }
  if (item.kind === 'module') {
    return item.ran ? `<li><a class="text-action" href="${deps.moduleHref(item.code)}">${escapeHtml(item.name)}${deps.icon('arrow-right')}</a></li>`
      : `<li>${escapeHtml(item.name)}<span class="small"> · Not run in this run</span></li>`;
  }
  return `<li>${escapeHtml(item.raw)}</li>`;
}

// The inspector's whole Basis block for one paragraph: its items (inspectorItems) as a list in the handoff's order, each drawn by drawItem(item)
// (the page's resolver of one item to its <li>, normally inspectorItemHtml with the page's helpers). An earlier-format paragraph lists its
// citations as written. No items: no block. The app draws exactly this; the node tests read it.
function inspectorBasisBlock(text, earlier, ctx, drawItem) {
  if (earlier) {
    const raw = earlierBasis(text).items;
    return raw.length ? `<div class="basis"><h3>Basis</h3><ul class="basis-items">${raw.map(r => `<li>${escapeHtml(r)}</li>`).join('')}</ul></div>` : '';
  }
  const items = inspectorItems(text, ctx);
  return items.length ? `<div class="basis"><h3>Basis</h3><ul class="basis-items">${items.map(item => drawItem(item)).join('')}</ul></div>` : '';
}

// ---- Figures (H6 check 8). A figure is a number with optional thousands commas and decimals, with its currency prefix and unit
// suffix as written. Not figures: a number touching a letter or hyphen-joined to one (10-K, B-1, FY2024, 3rd), a four-digit year
// 1900-2099, a date or a day/year beside a month name, a whole number below 100 that carries no currency, no symbolic unit
// (%, x, bp, bps, pp, basis/percentage points) and no scale word (a count, or a span of time).
const MONTH = '(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\\.?';
const DATE_PATTERNS = [
  /\d{4}-\d{2}-\d{2}/g, /\d{4}-(?:0[1-9]|1[0-2])(?!\d)/g, /\d{4}-Q[1-4]/g,
  new RegExp(`\\b${MONTH}\\s+\\d{1,2}(?:,?\\s+\\d{4})?(?!\\d)`, 'g'),
  new RegExp(`\\b\\d{1,2}\\s+${MONTH}(?:,?\\s+\\d{4})?(?!\\d)`, 'g'),
  new RegExp(`\\b${MONTH}\\s+\\d{4}(?!\\d)`, 'g'),
];
const NUMBER = /\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?/g;
const SYMBOLIC_UNIT = /^(?:%|x(?![A-Za-z])|bps(?![A-Za-z])|bp(?![A-Za-z])|pp(?![A-Za-z])|\s(?:basis points|percentage points)(?![A-Za-z])|\s(?:bps|bp|pp)(?![A-Za-z]))/;
const SCALE_UNIT = /^(?:\s?(?:thousand|million|billion|trillion|bn|k|m)(?![A-Za-z]))/;
const OTHER_UNIT = /^\s(?:times|notches|notch|days|day|weeks|week|months|month|quarters|quarter|years|year)(?![A-Za-z])/;
const SYMBOLS = '$€£¥';
// ISO 4217 codes a credit handoff uses; only these count as a currency prefix (not AGM, IAS, LTM, ECB).
const CURRENCY_CODES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'SEK', 'NOK', 'DKK', 'HKD', 'SGD', 'CNY', 'INR', 'BRL', 'MXN', 'ZAR', 'TRY', 'PLN', 'CZK'];
const CURRENCY_BEFORE = new RegExp(`(?:^|[^A-Za-z])(?:${CURRENCY_CODES.join('|')})$`);

function dateRanges(text) {
  const ranges = [];
  for (const pattern of DATE_PATTERNS) for (const m of text.matchAll(pattern)) ranges.push([m.index, m.index + m[0].length]);
  return ranges;
}

function figureSpans(text) {
  text = String(text);
  const dates = dateRanges(text);
  const spans = [];
  for (const m of text.matchAll(NUMBER)) {
    const start = m.index, end = start + m[0].length, rest = text.slice(end);
    if (dates.some(([from, to]) => start >= from && end <= to)) continue;
    const before = text[start - 1] || '';
    if (/[A-Za-z]/.test(before) || (before === '-' && /[A-Za-z]/.test(text[start - 2] || ''))) continue;
    if (/^-[A-Za-z]/.test(rest)) continue;
    const symbolic = SYMBOLIC_UNIT.exec(rest), scale = SCALE_UNIT.exec(rest), other = OTHER_UNIT.exec(rest);
    const unit = symbolic || scale || other;
    if (!unit && /^[A-Za-z]/.test(rest)) continue;
    let from = start;
    if (SYMBOLS.includes(before)) from = start - 1;
    else if (before === ' ' && CURRENCY_BEFORE.test(text.slice(0, start - 1))) from = start - 4;
    const prefixed = from !== start;
    const plain = !m[0].includes(',') && !m[0].includes('.');
    if (!prefixed && !symbolic && !scale && plain) {
      const value = Number(m[0]);
      if (value < 100) continue;
      if (m[0].length === 4 && value >= 1900 && value <= 2099) continue;
    }
    const to = unit ? end + unit[0].length : end;
    spans.push({start: from, end: to, text: text.slice(from, to)});
  }
  return spans;
}

// H6 check 7: lower case, Basis line dropped, punctuation removed, whitespace collapsed.
function normaliseLimitation(text) {
  return splitBasis(text).body.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, '').replace(/\s+/g, ' ').trim();
}

// ---- Earlier format (H7): a bracket citation or chip that ends a sentence or the paragraph moves, verbatim, to the items.
const CITATION = /\[[^\]]*\]|【[^】]*】/g;
// Only bracketed text that looks like a citation moves: a module code, a page marker, a register code (letter and digits), a dagger or the 【】 form.
// Other brackets ([sic], [TBD], [emphasis added], a status word) are wording and stay in the sentence.
const CITATION_SHAPE = /CP-[A-Z0-9]+|\bpp?\.|\bpages?\b|\b[A-Z]\d{1,3}\b|†|^【/;
const SENTENCE_END_BEFORE = /[.!?]["')”’]*\s?$/;
const SENTENCE_END_AFTER = /^(?:\s*$|[.!?]+["')”’]*(?:\s|$))/;

function earlierBasis(text) {
  text = String(text);
  const found = [...text.matchAll(CITATION)].filter(m => CITATION_SHAPE.test(m[0])).map(m => ({start: m.index, end: m.index + m[0].length, text: m[0]}));
  const clusters = [];
  for (const citation of found) {
    const last = clusters[clusters.length - 1];
    if (last && /^\s*$/.test(text.slice(last[last.length - 1].end, citation.start))) last.push(citation);
    else clusters.push([citation]);
  }
  const items = [];
  const cut = [];
  for (const cluster of clusters) {
    const first = cluster[0], tail = text.slice(cluster[cluster.length - 1].end);
    const ends = SENTENCE_END_AFTER.test(tail) || (SENTENCE_END_BEFORE.test(text.slice(0, first.start)) && /^(?:\s|$)/.test(tail));
    if (!ends) continue;
    for (const citation of cluster) {
      items.push(citation.text);
      cut.push([text[citation.start - 1] === ' ' ? citation.start - 1 : citation.start, citation.end]);
    }
  }
  let body = '', at = 0;
  for (const [from, to] of cut) { body += text.slice(at, from); at = to; }
  return {body: body + text.slice(at), items};
}

// ---- Prose and tables of a handoff, as HTML strings (decisions 7 and 14, H3, H4, H7). Pure: the page and the node tests draw with the same code.
const escapeHtml = value => String(value ?? '').replace(/[&<>"'\r]/g, c => ({'\r': '&#13;', '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const plainText = value => String(value).replace(/\*\*|`/g, '');
const richText = value => escapeHtml(value).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');

// A number as a chart or a table column reads it: thousands commas, a bracketed negative, an optional % or x.
function chartNumber(value) {
  const clean = plainText(value).trim().replace(/,/g, '');
  if (!/^(?:[-+]?\d+(?:\.\d+)?|\(\d+(?:\.\d+)?\))(?:%|x)?$/.test(clean)) return null;
  const number = Number(clean.replace(/[()%x]/g, '')) * (clean.startsWith('(') ? -1 : 1);
  return Number.isFinite(number) ? number : null;
}
const MISSING_CELL = /^(|[—–-]|Not supplied)$/i;
// A cell that says there is no value; it neither makes a column numeric nor stops it being numeric.
const NO_VALUE = /^(|[—–-]|n\.?a\.?|Not supplied\b[\s\S]*)$/i;
// A column is numeric when every cell that has a value parses as a number, and at least one does.
function numericColumn(block, c) {
  const cells = block.rows.map(r => plainText(r.cells[c] ?? '').trim()).filter(text => !NO_VALUE.test(text));
  return c > 0 && cells.length > 0 && cells.every(text => chartNumber(text) !== null);
}
// `after` is markup placed inside the cell, after its text.
function cellView(cell, numeric, after = '') {
  const text = plainText(cell ?? '').trim();
  if (MISSING_CELL.test(text)) return `<td${numeric ? ' class="num"' : ''}><span class="na" title="${escapeHtml(text || 'Empty in the handoff')}">n.a.</span>${after}</td>`;
  // A number in a column that also holds text keeps the figure face where it stands; only a wholly numeric column aligns right.
  return `<td${numeric ? ' class="num"' : chartNumber(text) !== null ? ' class="fig"' : ''}>${richText(text)}${after}</td>`;
}

// The quiet "Basis" control. `items` are the raw references it carries (a Basis line's items, or an earlier paragraph's bracket citations).
function basisButton(key, items, label) {
  return `<button type="button" class="basis-link" data-paragraph="${escapeHtml(key)}" data-basis="${escapeHtml(JSON.stringify(items))}" aria-label="${escapeHtml(label)}">Basis</button>`;
}

// A paragraph's text as read: `item` when it is a "- " list item, the body on one line, and the raw references taken out of it
// (new format: the Basis line's items; earlier format: the trailing bracket citations, H7).
function paragraphBody(text, earlier = false) {
  const split = earlier ? earlierBasis(text) : splitBasis(text);
  const item = !earlier && split.body.startsWith('- ');
  return {item, body: (item ? split.body.slice(2) : split.body).replace(/\n/g, ' '), items: split.items};
}

// One prose paragraph's inline HTML. New format (decision 7): the Basis line is never printed; each figure of a paragraph that has Basis items or
// chips is a button wrapping the figure's exact text; a paragraph with no figure gets one quiet Basis button at its end. Earlier format
// (decision 14, H7): the wording stays, its trailing citations sit behind one Basis button; an earlier paragraph with no citation and no chip in the build gets none (decision 7: nothing when neither).
// `chips` is how many chips the build holds for the paragraph's key.
function paragraphView(text, key, {earlier = false, chips = 0} = {}) {
  const {item, body, items} = paragraphBody(text, earlier);
  const referenced = items.length > 0 || chips > 0;
  const figures = !earlier && referenced ? figureSpans(body) : [];
  // Each figure is replaced by a sentinel so the **bold** / `code` markup can still span it. The sentinel character is the first private-use
  // character the paragraph does not itself contain, so no text of the handoff can be mistaken for one.
  let sentinel = 0xE000;
  while (body.includes(String.fromCharCode(sentinel))) sentinel += 1;
  const mark = String.fromCharCode(sentinel);
  let marked = '', at = 0;
  figures.forEach((figure, i) => { marked += `${body.slice(at, figure.start)}${mark}${i}${mark}`; at = figure.end; });
  marked += body.slice(at);
  const attributes = `data-paragraph="${escapeHtml(key)}" data-basis="${escapeHtml(JSON.stringify(items))}"`;
  let html = richText(marked).replace(new RegExp(`${mark}(\\d+)${mark}`, 'g'), (_, i) => `<button type="button" class="figure" ${attributes} data-figure="${i}">${escapeHtml(figures[Number(i)].text)}</button>`);
  if (referenced && !figures.length) html += ` ${basisButton(key, items, `Basis for paragraph: ${plainText(body).split(/\s+/).slice(0, 8).join(' ')}`)}`;
  return {item, html};
}

// The index (among the row's chips) of the first source-page chip that a Source cell names: an item `<file>, page(s) <list>` whose file and a listed page
// a chip holds. -1 when none does; the cell is then left as plain text.
function sourceCellChip(text, chips) {
  for (const item of plainText(text).split('; ')) {
    const m = new RegExp(`^(.+?), pages? (${SPAN}(?:, ${SPAN})*)$`).exec(item.trim());
    if (!m) continue;
    const spans = spansOf(m[2]);
    const at = chips.findIndex(c => c.kind === 'issuer_page' && c.file === m[1] && spans.some(s => c.page <= (s.pageEnd ?? s.page) && (c.page_end ?? c.page) >= s.page));
    if (at >= 0) return at;
  }
  return -1;
}

// A cell of a new-format table exactly as written: a missing, dash or "Not supplied" cell is drawn as it stands, never as "n.a." (H4).
// `open` is {key, index}: the text is then one button on that row chip (a Source cell), unchanged.
function writtenCell(cell, numeric, after = '', open = null) {
  const text = String(cell ?? '');
  const shown = open ? `<button type="button" class="source-cell" data-chip="${escapeHtml(open.key)}" data-index="${open.index}">${richText(text)}</button>` : richText(text);
  return `<td${numeric ? ' class="num"' : chartNumber(text) !== null ? ' class="fig"' : ''}>${shown}${after}</td>`;
}

// A table of a new-format handoff exactly as written: its own columns and cells, none of the app's. A row the build holds chips for carries a
// quiet Basis button in its first cell, so the chips stay reachable; a cell of a column headed exactly `Source` becomes a button on the row chip that
// holds its file and page. `ctx` is {id, chips(key), chipList(key)?}; `caption` is the table's accessible name.
function tableView(caption, block, ctx) {
  const numeric = block.headers.map((_, c) => numericColumn(block, c));
  const head = block.headers.map((header, c) => `<th scope="col"${numeric[c] ? ' class="num"' : ''}>${escapeHtml(header)}</th>`).join('');
  const rows = block.rows.map(row => {
    const key = `${ctx.id}:${row.line}`;
    const control = ctx.chips(key) ? ` ${basisButton(key, [], `Basis for row: ${plainText(row.cells[0] ?? '')}`)}` : '';
    const chips = ctx.chipList?.(key) || [];
    const open = cell => { const index = chips.length ? sourceCellChip(cell, chips) : -1; return index >= 0 ? {key, index} : null; };
    return `<tr>${row.cells.map((cell, c) => writtenCell(cell, numeric[c], c === 0 ? control : '', block.headers[c] === 'Source' ? open(cell) : null)).join('')}</tr>`;
  }).join('');
  return `<div class="table-card"><table><caption class="sr-only">${escapeHtml(caption)}</caption><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
}

// A new-format section's content: prose paragraphs (list items grouped in one list) and, when `ctx.tables`, its tables.
// ctx: {id (the output), tables, chips(key) -> count, caption(heading) -> text}.
function sectionBodyHtml(section, ctx) {
  let html = '', open = false;
  const close = () => { if (open) html += '</ul>'; open = false; };
  for (const block of section.blocks) {
    if (block.type === 'table') {
      if (!ctx.tables) continue;
      close();
      html += tableView(ctx.caption(section.heading), block, ctx);
      continue;
    }
    const key = `${ctx.id}:${block.line}`;
    const {item, html: inner} = paragraphView(block.text, key, {chips: ctx.chips(key)});
    if (item && !open) html += '<ul class="passage-list">';
    if (!item) close();
    open = item;
    html += item ? `<li>${inner}</li>` : `<p class="passage-text">${inner}</p>`;
  }
  close();
  return html;
}

// `calculation <id>` (H3): the row of the handoff's `## Calculations` tables (the H2 and its H3 children) whose ID column (header `ID`
// or ending ` ID`, any case) equals the id; its headers and every cell as written. Null when there is none.
function calculationRow(sections, id) {
  const list = sections || [];
  const start = list.findIndex(s => s.level === 2 && s.heading === 'Calculations');
  if (start < 0) return null;
  for (let i = start; i < list.length && (i === start || list[i].level > 2); i++) {
    for (const block of list[i].blocks.filter(b => b.type === 'table')) {
      const column = block.headers.findIndex(header => /^id$|\sid$/i.test(header.trim()));
      const row = column < 0 ? undefined : block.rows.find(r => (r.cells[column] ?? '').trim() === id);
      if (row) return {headers: block.headers, cells: row.cells, line: row.line};
    }
  }
  return null;
}

// ---- Report history (decision 4): as-of date descending, then first start time descending (no time sorts after a time), then folder.
function historyRows(runs) {
  const started = run => (run.record && run.record.steps && run.record.steps[0] && run.record.steps[0].started) || null;
  const compare = (a, b) => (a < b) - (a > b);  // descending
  return [...runs].sort((a, b) => {
    const dates = compare(a.asOf || '', b.asOf || '');
    if (dates) return dates;
    const [sa, sb] = [started(a), started(b)];
    if (sa !== sb) {
      if (sa === null) return 1;
      if (sb === null) return -1;
      return compare(sa, sb);
    }
    return -compare(a.folder, b.folder);
  });
}

// The pathway id as words: "credit_snapshot" is "Credit snapshot"; no id is null (the caller says "Not recorded").
const PATHWAY_TITLES = {short_snapshot: 'Short credit snapshot'};
function pathwayTitle(id) {
  if (Object.hasOwn(PATHWAY_TITLES, String(id))) return PATHWAY_TITLES[id];
  const words = String(id || '').split(/[_\s-]+/).filter(word => word !== '').map(word => word.toLowerCase());
  return words.length ? words.join(' ').replace(/^./, first => first.toUpperCase()) : null;
}

// The modules of a run that hold an output, in the run's own order (record.steps), then any the record does not list.
function runModuleCodes(run) {
  const held = Object.entries(run.modules || {}).filter(([, entry]) => entry.outputs && entry.outputs.length).map(([code]) => code);
  const ordered = ((run.record && run.record.steps) || []).map(step => step.module).filter(code => held.includes(code));
  return [...new Set([...ordered, ...held])];
}

// The last day of a period dated to a month (YYYY-MM), a quarter (YYYY-Qn) or a year (YYYY) as YYYY-MM-DD; null for any other text.
function periodEnd(date) {
  const text = String(date);
  const pad = n => String(n).padStart(2, '0');
  const endOfMonth = (year, month) => `${year}-${pad(month)}-${pad(new Date(Date.UTC(Number(year), month, 0)).getUTCDate())}`;
  let found = /^(\d{4})-(\d{2})$/.exec(text);
  if (found) return Number(found[2]) >= 1 && Number(found[2]) <= 12 ? endOfMonth(found[1], Number(found[2])) : null;
  found = /^(\d{4})-Q([1-4])$/.exec(text);
  if (found) return endOfMonth(found[1], 3 * Number(found[2]));
  found = /^(\d{4})$/.exec(text);
  return found ? `${found[1]}-12-31` : null;
}

// H5.5 / drafting choice 8: the next n items (five) in total on or after asOf, nearest first. A day-dated item (YYYY-MM-DD) sorts by that day; an item
// dated only to a month, quarter or year sorts by its period end; both kinds share one ordering. Ties: a day-dated item before a period-dated one,
// then input order. An item with no such date is left out. The caller tells the kinds apart by the date text.
function nearestDates(items, asOf, n = 5) {
  const entries = items.map((item, index) => {
    const day = /^\d{4}-\d{2}-\d{2}$/.test(String(item.date));
    return {item, index, day, key: day ? String(item.date) : periodEnd(item.date)};
  }).filter(entry => entry.key !== null && entry.key >= asOf);
  const order = (a, b) => (a.key < b.key ? -1 : a.key > b.key ? 1 : a.day !== b.day ? (a.day ? -1 : 1) : a.index - b.index);
  return entries.sort(order).slice(0, n).map(entry => entry.item);
}

if (typeof module !== 'undefined') module.exports = {escapeHtml, plainText, richText, chartNumber, numericColumn, cellView, basisButton, writtenCell, paragraphBody, paragraphView, tableView, sectionBodyHtml, calculationRow, readerPassages, isNewFormat, earlierFormatRun, blocked, splitBasis, basisItem, inspectorItem, inspectorItems, inspectorItemHtml, inspectorBasisBlock, uniqueChips, figureSpans, normaliseLimitation, earlierBasis, historyRows, pathwayTitle, runModuleCodes, nearestDates};

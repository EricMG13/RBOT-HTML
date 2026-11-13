'use strict';
// Components: the icon table, the trace control, header chips, the tab pill, the toast and the tooltip attributes.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const C = require('./components.js');

test('every icon of the table is the markup of its file in icons/, and trace is the layers icon', () => {
  const dir = path.join(__dirname, 'icons');
  const files = fs.readdirSync(dir).filter(name => name.endsWith('.svg'));
  assert.ok(files.length >= 20);
  for (const file of files) {
    const name = file.replace('.svg', '');
    const inner = fs.readFileSync(path.join(dir, file), 'utf8').replace(/^[\s\S]*?>\s*/, '').replace(/<\/svg>\s*$/, '').replace(/\s+/g, ' ').replace(/> </g, '><').trim();
    assert.equal(C.ICON_PATHS[name], inner, name);
  }
  assert.equal(C.ICON_PATHS.trace, C.ICON_PATHS.layers);
  assert.deepEqual(Object.keys(C.ICON_PATHS).sort(), [...files.map(f => f.replace('.svg', '')), 'trace'].sort());
});

test('icon: inline SVG in the text colour, hidden from assistive technology; an unknown name throws', () => {
  const svg = C.icon('check');
  assert.ok(svg.startsWith('<svg ') && svg.includes('stroke="currentColor"') && svg.includes('aria-hidden="true"') && svg.includes('width="16"'));
  assert.ok(svg.includes(C.ICON_PATHS.check));
  assert.throws(() => C.icon('nope'), /no icon named nope/);
});

test('traceButton: a real button with an accessible name, the paragraph key and the Basis items as data attributes', () => {
  const html = C.traceButton('o:9', 'Show the basis of this paragraph', ['Q4.pdf, page 7']);
  assert.ok(html.startsWith('<button type="button" class="basis-link" data-paragraph="o:9" data-basis="[&quot;Q4.pdf, page 7&quot;]" aria-label="Show the basis of this paragraph">'));
  assert.ok(html.includes('<svg') && html.endsWith('</svg></button>'));
  assert.ok(!/>\s*Basis\s*</.test(html), 'the icon is the control; no Basis word');
  assert.ok(C.traceButton('o:9', 'x').includes('data-basis="[]"'));
  assert.ok(C.traceButton('k"><i>', 'a"b').includes('data-paragraph="k&quot;&gt;&lt;i&gt;"') && C.traceButton('k', 'a"b').includes('aria-label="a&quot;b"'));
});

test('traceRow: the same icon for a row opened by evidence key, with the row title and accessible name', () => {
  const html = C.traceRow('o:16', 'Table row, line 16');
  assert.ok(html.includes('data-evidence="o:16"') && html.includes('aria-label="Table row, line 16"') && html.includes('title="Table row, line 16"') && html.includes('<svg'));
});

test('headerChips: a chip per text, a link where there is an href, and nothing when there is nothing', () => {
  assert.equal(C.headerChips([]), '');
  assert.equal(C.headerChips([{text: ''}, null]), '');
  const html = C.headerChips([{text: '31 December 2025'}, {text: 'Credit snapshot'}, {text: 'Methods changed since this run', tone: 'amber', href: '#W-Evidence/record?c=r&x=1&y=2'}]);
  assert.equal(html, '<p class="hchips"><span class="hchip">31 December 2025</span><span class="hchip">Credit snapshot</span><a class="hchip amber" href="#W-Evidence/record?c=r&amp;x=1&amp;y=2">Methods changed since this run</a></p>');
});

test('tipAttributes: the tooltip text is also the accessible name', () => {
  assert.equal(C.tipAttributes('Copy "this"'), 'data-tip="Copy &quot;this&quot;" aria-label="Copy &quot;this&quot;"');
});

function fakeDocument() {
  const made = [];
  const node = tag => {
    const n = {tag, children: [], attrs: {}, id: '', className: '', textContent: '', removed: false,
      setAttribute(k, v) { this.attrs[k] = v; }, append(...kids) { this.children.push(...kids); }, remove() { this.removed = true; }};
    made.push(n);
    return n;
  };
  const body = node('body');
  return {made, body, createElement: node, getElementById: id => body.children.find(c => c.id === id) || null};
}

test('toast: one role=status host; each message is a child that removes itself after 3 seconds', t => {
  const doc = fakeDocument();
  global.document = doc;
  t.after(() => { delete global.document; });
  t.mock.timers.enable({apis: ['setTimeout']});
  C.toast('Copied');
  C.toast('Saved');
  const hosts = doc.body.children;
  assert.equal(hosts.length, 1, 'a single host');
  assert.equal(hosts[0].attrs.role, 'status');
  assert.deepEqual(hosts[0].children.map(c => c.textContent), ['Copied', 'Saved']);
  t.mock.timers.tick(2999);
  assert.ok(hosts[0].children.every(c => !c.removed));
  t.mock.timers.tick(1);
  assert.ok(hosts[0].children.every(c => c.removed));
});

test('toastHost: the role=status host exists, empty, before the first message and is reused', t => {
  const doc = fakeDocument();
  global.document = doc;
  t.after(() => { delete global.document; });
  const host = C.toastHost();
  assert.equal(host.attrs.role, 'status');
  assert.equal(host.children.length, 0);
  assert.equal(C.toastHost(), host);
  assert.equal(doc.body.children.length, 1);
});

test('placePill: the pill follows the active tab through custom properties; no measured tab, no pill', () => {
  const set = {}, classes = new Set();
  const box = active => ({querySelector: () => active, style: {setProperty: (k, v) => { set[k] = v; }}, classList: {add: c => classes.add(c), remove: c => classes.delete(c)}});
  assert.equal(C.placePill(box({offsetLeft: 40, offsetWidth: 90, offsetHeight: 36, offsetTop: 10})), true);
  assert.deepEqual(set, {'--pill-x': '40px', '--pill-w': '90px', '--pill-h': '36px', '--pill-y': '10px'});
  assert.ok(classes.has('has-pill'));
  assert.equal(C.placePill(box(null)), false);
  assert.ok(!classes.has('has-pill'));
  assert.equal(C.placePill(box({offsetLeft: 0, offsetWidth: 0, offsetHeight: 0, offsetTop: 0})), false, 'a hidden tab has no width');
});

// ---- Module page components (library redesign, task 4). Expected text is written by hand in each test.
const T = (text, line) => ({ text, line });
const mark = line => `<button type="button" class="basis-link" data-paragraph="o:${line}">T${line}</button>`;
const figureButton = (line, i, text) => `<button type="button" class="figure" data-figure="${i}">${text}</button>`;
const noMarkdown = html => { assert.ok(!html.includes('Basis:') && !html.includes('**') && !/(?:^|>)\s*- /.test(html), html); };

test('verdictPanel: the lead is the whole first sentence, the rest of the paragraph and the later paragraphs follow at body size, one trace button per paragraph', () => {
  const html = C.verdictPanel([
    T('Creditors face refinancing risk, not weak earnings: net debt is USD 1,390 million at 4.2x. The next maturities fall inside two years. Cover is thin.\nBasis: A.pdf, page 4', 17),
    T('A second paragraph.\nBasis: B.pdf', 19),
  ], mark);
  assert.ok(html.includes('<p class="verdict-lead">Creditors face refinancing risk, not weak earnings: net debt is USD 1,390 million at 4.2x.</p>'), html);
  assert.ok(html.includes('<p class="verdict-body">The next maturities fall inside two years. Cover is thin.</p>'), html);
  assert.ok(html.includes('<p class="verdict-body">A second paragraph.</p>'));
  assert.equal((html.match(/class="basis-link"/g) || []).length, 2);
  assert.ok(html.indexOf('T17') > html.indexOf('Cover is thin.') && html.indexOf('T19') > html.indexOf('A second paragraph.'));
  noMarkdown(html);
});

test('verdictPanel: a one-sentence paragraph keeps its whole sentence as the lead and its trace button beside it; a decimal point or an abbreviation before a lower-case word does not end a sentence', () => {
  const one = C.verdictPanel([T('Not assessable: the documents give no monthly cash forecast.', 3)], mark);
  assert.ok(one.includes('<p class="verdict-lead">Not assessable: the documents give no monthly cash forecast.</p>') && !one.includes('verdict-body') && one.includes('T3'), one);
  const decimal = C.verdictPanel([T('Leverage is 4.2x, down from 5.1x in e.g. fiscal 2023. Next.', 1)], mark);
  assert.ok(decimal.includes('<p class="verdict-lead">Leverage is 4.2x, down from 5.1x in e.g. fiscal 2023.</p>'), decimal);
  assert.equal(C.verdictPanel([], mark), '');
});

test('verdictPanel: a lead sentence longer than 140 characters is marked is-long (set at text size, not as a headline); 140 characters or fewer is not', () => {
  const at = n => `${'a'.repeat(n - 1)}.`;
  const edge = C.verdictPanel([T(`${at(140)} Next sentence.`, 1)], mark), over = C.verdictPanel([T(`${at(141)} Next sentence.`, 1)], mark);
  assert.ok(edge.includes('<p class="verdict-lead">') && !edge.includes('is-long'), 'exactly 140 characters is a headline');
  assert.ok(over.includes('<p class="verdict-lead is-long">'), '141 characters is not');
  assert.ok(C.verdictPanel([T(`**${'b'.repeat(70)}** ${'c'.repeat(70)}. Next.`, 1)], mark).includes('is-long'), 'the characters counted are the words shown, not the markup');
});

test('verdictPanel: a figure inside the lead is the figure button when a figure callback is given, its exact text otherwise', () => {
  const text = 'Net debt of USD 1,390 million is 4.2x earnings. Refinance soon.';
  const plain = C.verdictPanel([T(text, 5)], mark);
  assert.ok(plain.includes('Net debt of USD 1,390 million is 4.2x earnings.</p>') && !plain.includes('class="figure"'));
  const html = C.verdictPanel([T(text, 5)], mark, figureButton);
  assert.ok(html.includes('<p class="verdict-lead">Net debt of <button type="button" class="figure" data-figure="0">USD 1,390 million</button> is <button type="button" class="figure" data-figure="1">4.2x</button> earnings.</p>'), html);
});

test('findingsFeed: one numbered item per block; a bold lead is the title and the rest the body; without one the first sentence is the title; no Markdown reaches the page', () => {
  const html = C.findingsFeed([
    T('- **Leverage is moderate.** Net debt is 4.2x EBITDA, so there is little room for a miss.\nBasis: A.pdf', 8),
    T('- A large part of the debt comes due soon: 38% matures within 24 months. Refinancing access decides the view.\nBasis: B.pdf', 10),
    T('No list marker and one sentence only', 12),
  ], mark);
  assert.equal((html.match(/<li class="feed-item">/g) || []).length, 3);
  assert.ok(html.includes('<span class="feed-num">1</span>') && html.includes('<span class="feed-num">3</span>'));
  assert.ok(html.includes('<div class="feed-title">Leverage is moderate.</div><p class="feed-body">Net debt is 4.2x EBITDA, so there is little room for a miss.</p>'), html);
  assert.ok(html.includes('<div class="feed-title">A large part of the debt comes due soon: 38% matures within 24 months.</div><p class="feed-body">Refinancing access decides the view.</p>'), html);
  assert.ok(html.includes('<div class="feed-title">No list marker and one sentence only</div>') && !/No list marker[^<]*<\/div><p class="feed-body">/.test(html));
  assert.ok(html.indexOf('T8') < html.indexOf('feed-num">2') && html.includes('T10') && html.includes('T12'));
  noMarkdown(html);
});

test('findingsFeed: text is escaped, an inner **bold** span becomes <strong>, and no items give an empty string', () => {
  const html = C.findingsFeed([T('- **A < B.** It is **bold** & <b>raw</b>.', 1)], () => '');
  assert.ok(html.includes('<div class="feed-title">A &lt; B.</div>') && html.includes('It is <strong>bold</strong> &amp; &lt;b&gt;raw&lt;/b&gt;.'), html);
  assert.equal(C.findingsFeed([], mark), '');
});

test('callout: the left-rule panel carries its title, one paragraph per block with its trace button, no Basis text', () => {
  const html = C.callout('What would change the view', [
    T('The strongest evidence against concern is the earnings record. A signed refinancing would move the view.\nBasis: Q4.pdf, page 7', 20),
    T('The company has not said how it will fund the step-down.', 22),
  ], mark);
  assert.ok(html.startsWith('<div class="callout">') && html.includes('What would change the view</h4>') && html.includes('<svg'), html);
  assert.ok(html.includes('<p>The strongest evidence against concern is the earnings record. A signed refinancing would move the view.') && html.includes('T20'));
  assert.ok(html.includes('<p>The company has not said how it will fund the step-down.<button') && html.includes('T22</button></p>'));
  noMarkdown(html);
  assert.equal(C.callout('x', [], mark), '');
});

test('limitationsBlock: a compact list with a warning icon each, and a gap signal with the count, the words and the Evidence link; with no gaps there is no signal', () => {
  const texts = [T('- The covenant package was not reviewed.\nBasis: calculation K1', 30), T('- Peer leverage was not compared.', 31)];
  const html = C.limitationsBlock(texts, 3, '#W-Evidence/gaps?c=r&m=CP-2', () => '');
  assert.equal((html.match(/<li>/g) || []).length, 2);
  assert.equal((html.match(/<li><svg/g) || []).length, 2, 'a warning icon opens each item');
  assert.ok(html.includes('<span>The covenant package was not reviewed.</span>') && html.includes('<span>Peer leverage was not compared.</span>'));
  assert.ok(html.includes('<div class="gapsig-n" data-count>3</div>') && html.includes('gaps recorded') && html.includes('<a class="gapsig-link" href="#W-Evidence/gaps?c=r&amp;m=CP-2">Open in Evidence'), html);
  noMarkdown(html);
  for (const none of [0, undefined, null]) {
    const bare = C.limitationsBlock(texts, none, '#W-Evidence/gaps', () => '');
    assert.ok(!bare.includes('gapsig') && !bare.includes('data-count') && !bare.includes('Open in Evidence') && bare.includes('<li>'), bare);
  }
  assert.ok(C.limitationsBlock(texts, 1, '#x', () => '').includes('gap recorded') && !C.limitationsBlock(texts, 1, '#x', () => '').includes('gaps recorded'));
  assert.equal(C.limitationsBlock([], 4, '#x', () => ''), '');
});

test('recordCards: one card per row, the first visible column its title, the others label and value, hidden columns omitted, every other cell kept, one trace button per card', () => {
  const block = { headers: ['ID', 'Item', 'Status', 'Source', 'Note'], rows: [
    { line: 5, cells: ['EV-001', 'Revolver', 'Undrawn **for now**', 'A.pdf, page 9', 'Steps down in 2027'] },
    { line: 6, cells: ['EV-002', 'Term loan', '', 'B.pdf', 'Matures 2028'] },
  ] };
  const html = C.recordCards(block, { key: row => `o:${row.line}`, caption: 'Facilities' });
  assert.equal((html.match(/<article class="rec-card">/g) || []).length, 2);
  assert.ok(html.includes('aria-label="Facilities"') && html.includes('<p class="rec-title">Revolver</p>') && html.includes('<p class="rec-title">Term loan</p>'), html);
  assert.ok(html.includes('<dt>Status</dt><dd>Undrawn <strong>for now</strong></dd>') && html.includes('<dt>Note</dt><dd>Steps down in 2027</dd>') && html.includes('<dd>Matures 2028</dd>'));
  for (const hidden of ['EV-001', 'EV-002', 'A.pdf', 'B.pdf', '<dt>Source</dt>', '<dt>ID</dt>']) assert.ok(!html.includes(hidden), `${hidden} is a hidden column`);
  assert.ok(!html.includes('<dt>Status</dt><dd></dd>'), 'an empty cell has nothing to show');
  assert.equal((html.match(/class="basis-link trace-row"/g) || []).length, 2);
  assert.ok(html.includes('data-evidence="o:5"') && html.includes('data-evidence="o:6"'));
  noMarkdown(html);
});

test('recordCards: a table with no row or only hidden columns draws nothing; unknown column names still draw every cell', () => {
  assert.equal(C.recordCards({ headers: ['A', 'B'], rows: [] }, { key: () => 'k' }), '');
  assert.equal(C.recordCards({ headers: ['ID', 'Source'], rows: [{ line: 1, cells: ['x', 'y'] }] }, { key: () => 'k' }), '');
  const odd = C.recordCards({ headers: ['Zeta', 'Omega', 'Psi'], rows: [{ line: 4, cells: ['one', '2.5x', 'three'] }] }, { key: row => `k:${row.line}` });
  for (const text of ['one', '2.5x', 'three', '<dt>Omega</dt>', '<dt>Psi</dt>']) assert.ok(odd.includes(text), text);
});

test('sectionRail: a labelled nav of links with optional counts; the current item is marked by the page, not here', () => {
  const html = C.sectionRail([{ id: 'bottom-line', label: 'Bottom line', href: '#CP-2/bottom-line' }, { id: 'limitations', label: 'Limitations', count: 3 }]);
  assert.ok(html.startsWith('<nav class="sec-rail" aria-label="On this page">'), html);
  assert.ok(html.includes('<a class="rail-item" data-part="bottom-line" href="#CP-2/bottom-line">Bottom line</a>'));
  assert.ok(html.includes('<a class="rail-item" data-part="limitations" href="#limitations">Limitations<span class="rail-count">3</span></a>'));
  assert.equal(C.sectionRail([]), '');
});

// ---- Numeric shape components (library redesign, task 5): the answer key's real tables are the inputs.
const Shapes = require('./shapes.js');
const KEY = require(path.join(__dirname, '..', '..', 'fixtures', 'shape-key.json'));
const keyBlock = t => ({ headers: t.headers, rows: t.rows.map((cells, i) => ({ line: i + 1, cells })) });
const keyTables = (module, shape) => KEY.tables.filter(t => t.module === module && (!shape || t.shape === shape));
// What the module page gives a component: the module's id tokens and case pairing, one trace control per call, the Evidence link.
function pageCtx(module, over = {}) {
  const blocks = KEY.tables.filter(t => t.module === module).map(keyBlock);
  const sections = blocks.map(block => ({ blocks: [{ type: 'table', ...block }] }));
  return { id: 'o', module, section: {}, key: row => `o:${row.line}`, trace: (row, label) => C.traceRow(`o:${row.line}`, label || `Row ${row.line}`), evidenceHref: '#W-Evidence/registers?m=' + module, caption: 'Table',
    tokens: Shapes.idTokens(sections), pairing: Shapes.casePairing(blocks), ...over };
}
const decode = text => text.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#13;/g, '\r').replace(/&amp;/g, '&');
const textOf = html => decode(html.replace(/<[^>]*>/g, ''));
const plainCell = value => String(value).replace(/\*\*|`/g, '').trim();
// Every cell of a column the key does not hide, whose header the page can name and which findingCell does not omit, must be in the drawing.
function expectedCells(t, ctx) {
  const out = [];
  t.headers.forEach((header, at) => {
    if (t.hidden.includes(at)) return;
    if (/\bSC\d\b|\bs00\b/.test(header) && !ctx.pairing) return;
    for (const cells of t.rows) { const cell = plainCell(cells[at]); if (cell && C.findingCell(cell, ctx).html !== undefined) out.push(cell); }
  });
  return out;
}
const idTextOf = ctx => ctx.tokens.filter(token => /[A-Za-z]/.test(token));

const SHAPE_COMPONENT = { cases: 'casesBlock', caseRows: 'caseRowsBlock', ranked: 'rankedLadder', statement: 'statementCard', metric: 'metricTiles', measure: 'measureTiles', change: 'changeCards' };

test('render: each of the seven numeric shapes goes to its component and the output holds every drawn cell of every key table of that shape', () => {
  for (const [shape, name] of Object.entries(SHAPE_COMPONENT)) {
    const found = KEY.tables.filter(t => t.shape === shape);
    assert.ok(found.length >= 1, shape);
    assert.equal(typeof C[name], 'function', name);
    for (const t of found) {
      const ctx = pageCtx(t.module), block = keyBlock(t);
      assert.equal(Shapes.tableShape(block), shape, `${t.module} ${t.heading}`);
      const html = C.render(shape, block, ctx);
      assert.equal(html, C[name](block, ctx), `${shape} is drawn by ${name}`);
      assert.ok(html.length > 200, `${t.module} ${t.heading} draws`);
      const text = textOf(html);
      const missing = expectedCells(t, ctx).filter(cell => !text.includes(cell));
      assert.deepEqual(missing, [], `${shape} ${t.module} ${t.heading}: cells not drawn`);
      noMarkdown(html);
      assert.ok(/<button[^>]*class="basis-link trace-row"/.test(html), `${shape}: a trace control`);
    }
  }
});

test('render: a shape with no numeric component, and a shape nobody knows, go to recordCards', () => {
  const block = { headers: ['Zeta', 'Omega'], rows: [{ line: 3, cells: ['one', 'two'] }] };
  const ctx = { key: row => `k:${row.line}` };
  assert.equal(C.render('records', block, ctx), C.recordCards(block, ctx));
  assert.equal(C.render('dated', block, ctx), C.recordCards(block, ctx));
  assert.equal(C.render('nothing-knows-this', block, ctx), C.recordCards(block, ctx));
  assert.equal(C.render(undefined, block, ctx), C.recordCards(block, ctx));
});

test('no numeric component draws an identifier of the module, a calculation ID, a source or a hidden column', () => {
  for (const t of KEY.tables.filter(x => Object.hasOwn(SHAPE_COMPONENT, x.shape))) {
    const ctx = pageCtx(t.module), html = C.render(t.shape, keyBlock(t), ctx), text = textOf(html);
    for (const token of idTextOf(ctx)) assert.ok(!new RegExp(`(?<![A-Za-z0-9_])${token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![A-Za-z0-9_])`).test(text), `${t.module} ${t.heading} draws ${token}`);
    assert.ok(!/calculations? [A-Z]{1,2}\d{2}/i.test(text) && !text.includes('calculation D'), `${t.module} ${t.heading} draws a calculation ID`);
    assert.ok(!/\.jsonl|\.htm\b|sha256|Basis:/.test(text), 'no file name or Basis');
    t.headers.forEach((header, at) => {
      if (!t.hidden.includes(at)) return;
      for (const cells of t.rows) { const cell = plainCell(cells[at]); if (cell.length > 12) assert.ok(!text.includes(cell), `${t.module} ${t.heading}: hidden column ${header} drawn`); }
    });
  }
});

test('findingCell (a): a cell that is only references (calculation IDs, file names, handoff names) is omitted with no link', () => {
  const ctx = { tokens: ['SC1'], evidenceHref: '#e' };
  for (const text of ['calculation D17', 'Calculations C21, C22', 'Calculation C05', 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 121', 'Financial data foundation (CP-1)',
    'Financial data foundation (CP-1); Business and transaction fact pack (CP-1A)', 'Fundamental credit synthesis (CP-2), calculation D17', 'results.pdf; notes.xlsx']) {
    assert.deepEqual(C.findingCell(text, ctx), { omitted: true }, text);
  }
  assert.deepEqual(C.findingCell('', ctx), { omitted: true });
  assert.deepEqual(C.findingCell(undefined, ctx), { omitted: true });
});

test('findingCell (b): an identifier inside other text is omitted and the row links to Evidence; whole words only', () => {
  const ctx = { tokens: ['SC1', 'SC2', 'EV-01'], evidenceHref: '#e' };
  for (const text of ['As SC1; also OEM build-rate knock-on and refinancing coupon resets', 'See EV-01 for the excerpt', 'Term loans plus six secured notes; calculation C23', 'House definition; calculations C15, C16', 'FCF after dividends; Calculation C17 applies'])
    assert.deepEqual(C.findingCell(text, ctx), { omitted: true, inEvidence: true }, text);
  for (const text of ['SC10 stays', 'ASC1', 'EV-010 is another', 'SC1x']) assert.notEqual(C.findingCell(text, ctx).omitted, true, text);
});

test('findingCell (c): any other cell is drawn with the rich-text treatment', () => {
  const ctx = { tokens: ['SC1'], evidenceHref: '#e' };
  assert.deepEqual(C.findingCell('Higher aftermarket margin (mix), defense offset', ctx), { html: 'Higher aftermarket margin (mix), defense offset' });
  assert.deepEqual(C.findingCell('Undrawn **for now** & <b>', ctx), { html: 'Undrawn <strong>for now</strong> &amp; &lt;b&gt;' });
  assert.deepEqual(C.findingCell('Reported supplemental', {}), { html: 'Reported supplemental' });
  assert.deepEqual(C.findingCell('7,940'), { html: '7,940' });
});

test('casesBlock: a segmented control over the case headers (second case pressed), one tile set per case, tracks by parsed number, a Chart/Table toggle', () => {
  const t = keyTables('CP-2A', 'cases')[0], ctx = pageCtx('CP-2A'), html = C.casesBlock(keyBlock(t), ctx);
  const pressed = [...html.matchAll(/<button type="button" class="case-opt" data-case-pick="(\d)" aria-pressed="(true|false)"[^>]*>([^<]*)</g)].map(m => [m[1], m[2], m[3]]);
  assert.deepEqual(pressed, [['0', 'false', 'Base FY2024 (control)'], ['1', 'true', 'Moderate scenario'], ['2', 'false', 'Severe scenario']]);
  const sets = [...html.matchAll(/<div class="tile-set" data-set="(\d)"( hidden)?>/g)].map(m => [m[1], Boolean(m[2])]);
  assert.deepEqual(sets, [['0', true], ['1', false], ['2', true]], 'all case sets are in the markup; only the selected one is shown');
  const second = html.slice(html.indexOf('data-set="1"'), html.indexOf('data-set="2"'));
  assert.ok(second.includes('<p class="tile-v">15% / 2.59%</p>') && second.includes('Base FY2024 (control): 0 / 0') && second.includes('Earnings cushion falls'));
  const first = html.slice(html.indexOf('data-set="0"'), html.indexOf('data-set="1"'));
  assert.ok(first.includes('<p class="tile-v">USD 4,173 million</p>') && !first.includes('Base FY2024 (control): '), 'the first case has nothing beneath');
  assert.equal((html.match(/<div class="rtrack-row">/g) || []).length, 3, 'tracks only for the rows whose three cells parse with one unit: the three x-multiple rows');
  assert.equal((html.match(/class="mk (?:up|dn)(?: on)?"/g) || []).length, 9);
  assert.equal((html.match(/class="mk (?:up|dn) on"/g) || []).length, 3, 'the selected case is filled on each track');
  const track = html.slice(html.indexOf('<div class="rtrack-row">'), html.indexOf('</div></div>', html.indexOf('rtrack-ends')));
  assert.ok(track.includes('<b>6.01x</b>') && track.includes('<b>7.07x</b>') && track.includes('<b>8.71x</b>'), 'each marker is labelled with its verbatim cell');
  assert.ok(track.includes('<span data-tick>0x</span><span data-tick>10x</span>'), 'axis ends are positional: 0 to a rounded maximum');
  assert.ok(track.includes('style="left:60.1%"') && track.includes('style="left:87.1%"'), 'positions are the parsed numbers on that axis');
  assert.ok(html.includes('<button type="button" data-view-pick="chart" aria-pressed="true">Chart</button>'));
  assert.ok(html.includes('data-view-pick="table"'));
  assert.ok(/<table class="dtbl">/.test(html) && /<th scope="col" class="num">Moderate scenario<\/th>/.test(html) && /<td class="num" data-label="Moderate scenario">15% \/ 2\.59%<\/td>/.test(html), 'the Table view is a designed table with numbers right-aligned');
  assert.equal((html.match(/class="basis-link trace-row"/g) || []).length, 1, 'one trace control for the block');
  assert.ok(html.includes('data-block data-case="1" data-view="chart" role="group"'), 'the block carries its state');
});

test('casesBlock: the first case is the default with two cases; the consequence column is the caption; an extra column is kept', () => {
  const block = { headers: ['Measure', 'Base', 'Severe', 'Creditor consequence', 'Note'], rows: [{ line: 1, cells: ['Leverage', '6.0x', '8.0x', 'Rises', 'Gross'] }] };
  const html = C.casesBlock(block, { key: r => `k:${r.line}` });
  assert.ok(html.includes('data-case-pick="0" aria-pressed="true"') && html.includes('data-case-pick="1" aria-pressed="false"'));
  const textAll = textOf(html);
  for (const cell of ['Leverage', '6.0x', '8.0x', 'Rises', 'Gross']) assert.ok(textAll.includes(cell), cell);
});

test('Review Focus 2: a cell that does not parse is shown as its text with no mark, and the component still draws', () => {
  const cases = { headers: ['Measure', 'Base', 'Moderate', 'Severe'], rows: [{ line: 1, cells: ['Leverage', '6.0x', 'n/a', '8.0x'] }, { line: 2, cells: ['Cover', '3.6x', '3.0x', '2.4x'] }, { line: 3, cells: ['Note', 'Not calculable: FY2022 comparatives not used', '1', '2'] }] };
  const html = C.casesBlock(cases, { key: r => `k:${r.line}` });
  assert.ok(html.length > 100);
  assert.equal((html.match(/<div class="rtrack-row">/g) || []).length, 1, 'only the row whose cells all parse has a track');
  for (const text of ['n/a', 'Not calculable: FY2022 comparatives not used']) assert.ok(textOf(html).includes(text), text);
  assert.ok(!/class="mk[^"]*"[^>]*>(?:(?!<\/button>).)*n\/a/.test(html), 'no mark for n/a');
  const metric = { headers: ['Metric', 'FY2024', 'FY2023', 'Definition / identity'], rows: [{ line: 1, cells: ['Revenue growth', '20.58%', 'Not calculable: FY2022 comparatives not used', 'Reported'] }, { line: 2, cells: ['Margin', 'n/a', 'n/a', 'Reported'] }] };
  const tiles = C.metricTiles(metric, { key: r => `k:${r.line}` });
  assert.ok(tiles.length > 100);
  for (const text of ['20.58%', 'Not calculable: FY2022 comparatives not used', 'n/a', 'Margin']) assert.ok(textOf(tiles).includes(text), text);
  assert.ok(!/class="mk |class="st-bar /.test(tiles), 'no mark in the metric tiles');
  const statement = { headers: ['Line', 'FY2024', 'FY2023'], rows: [{ line: 1, cells: ['Sales', '100', '90'] }, { line: 2, cells: ['Note', 'n/a', 'Not calculable: FY2022 comparatives not used'] }] };
  const card = C.statementCard(statement, { key: r => `k:${r.line}` });
  for (const text of ['n/a', 'Not calculable: FY2022 comparatives not used']) assert.ok(textOf(card).includes(text), text);
  assert.equal((card.match(/<span class="st-bar /g) || []).length, 2, 'bars only for the row that parses');
});

test('caseRows with text columns: cards titled with the paired case name; confidence is a three-segment meter with its word; a category is a pill; items are chips; an ID inside a cell links to Evidence', () => {
  const t = keyTables('CP-2A', 'caseRows')[0], ctx = pageCtx('CP-2A'), html = C.caseRowsBlock(keyBlock(t), ctx);
  const titles = [...html.matchAll(/<h4 class="cr-title">([^<]*)<\/h4>/g)].map(m => m[1]);
  assert.deepEqual(titles, ['Base FY2024 (control)', 'Moderate scenario', 'Severe scenario']);
  assert.equal((html.match(/<article class="cr-card">/g) || []).length, 3);
  assert.equal((html.match(/<span class="meter" aria-hidden="true">/g) || []).length, 3);
  assert.deepEqual([...html.matchAll(/<span class="meter-w">([^<]*)</g)].map(m => m[1]), ['High', 'Medium', 'Low']);
  assert.deepEqual([...html.matchAll(/<span class="meter" aria-hidden="true">(.*?)<\/span>/g)].map(m => (m[1].match(/class="f"/g) || []).length), [3, 2, 1]);
  assert.ok(html.includes('<span class="pill">Analyst Interpretation</span>') && html.includes('<span class="pill">Documentary Fact</span>'));
  assert.ok(html.includes('<li class="cr-chip">Higher aftermarket margin (mix)<span class="sr-only">, </span></li>'), 'comma-separated items become chips that keep the text');
  assert.ok(html.includes('<span class="cr-fig">0.1500</span>') && html.includes('EBITDA decline s'), 'the first two short numbers lead, with their column headers');
  assert.ok(html.includes('class="in-ev" href="#W-Evidence/registers?m=CP-2A">In Evidence</a>'), 'As SC1; ... is not drawn, the row links to Evidence');
  assert.ok(!textOf(html).includes('As SC1') && !/\bSC[12]\b|\bs00\b/.test(textOf(html)));
});

test('caseRows without a pairing: a numbered badge, no invented word; an id column is never drawn', () => {
  const t = keyTables('CP-2A', 'caseRows')[0], block = keyBlock(t), ctx = pageCtx('CP-2A', { pairing: null });
  const html = C.caseRowsBlock(block, ctx);
  assert.deepEqual([...html.matchAll(/<span class="cr-badge">(\d)<\/span>/g)].map(m => m[1]), ['1', '2', '3']);
  assert.ok(!/Base|Moderate|Severe/.test(html) && !/<h4 class="cr-title">/.test(html));
  assert.ok(!/\bSC[12]\b|\bs00\b/.test(textOf(html)));
});

test('caseRows with numeric columns: a case-by-measure panel, numbers right-aligned, the cell text verbatim, titled by case name through its scenario ids', () => {
  const t = keyTables('CP-2A', 'caseRows')[1], ctx = pageCtx('CP-2A'), html = C.caseRowsBlock(keyBlock(t), ctx);
  assert.ok(html.includes('class="dtbl cr-panel"') && !html.includes('cr-card'));
  // Its first column ("Scenario") is not an id column but its cells are the pairing ids: each row is titled by the case that id names.
  for (const name of ['Base FY2024 (control)', 'Moderate scenario', 'Severe scenario']) assert.ok(html.includes(`<th scope="row">${name}`), name);
  assert.ok(!/cr-badge/.test(html) && !/\bs00\b|\bSC[12]\b/.test(textOf(html)));
  assert.ok(html.includes('<td class="num" data-label="Total debt / EBITDA">7.0672812619 (7.07x)</td>'), html);
  assert.ok(html.includes('<th scope="col" class="num">Stressed EBITDA (USD m)</th>'));
  assert.ok(!/\bSC[12]\b|\bs00\b/.test(textOf(html)));
});

test('rankedLadder: numbered markers on a 0-to-rounded axis with positional ticks, labels on alternating leader lines, a state mark per case, a phone list', () => {
  const t = keyTables('CP-2A', 'ranked')[0], ctx = pageCtx('CP-2A'), html = C.rankedLadder(keyBlock(t), ctx);
  assert.equal((html.match(/class="lm"/g) || []).length, 4);
  assert.deepEqual([...html.matchAll(/<span class="lm-n">(\d)<\/span>/g)].map(m => m[1]), ['1', '2', '3', '4']);
  const ticks = [...html.matchAll(/<span class="ltick-l" data-tick[^>]*>([^<]*)</g)].map(m => m[1]);
  assert.equal(ticks[0], '0%');
  assert.ok(ticks.length >= 4 && ticks.every(x => /^\d+%$/.test(x)), ticks.join());
  assert.ok(Number(ticks[ticks.length - 1].replace('%', '')) > 72.25, 'the axis ends above the largest level');
  assert.ok(html.includes('<b>23.47%</b>') && html.includes('Pro forma net leverage reaches 7.25x incurrence watch level'));
  assert.deepEqual([...html.matchAll(/class="ll ll-(up|dn)/g)].map(m => m[1]), ['up', 'dn', 'up', 'dn'], 'labels alternate above and below');
  assert.ok(html.includes('<span class="st on"><i aria-hidden="true"></i>Breached</span>') && html.includes('<span class="st"><i aria-hidden="true"></i>Not reached</span>'));
  assert.ok(html.includes('Not reached') && html.includes('Moderate scenario') && html.includes('Severe scenario'), 'state marks carry the cell word and the paired case name');
  assert.ok(html.includes('class="lad-phone"') && (html.match(/class="lp-item"/g) || []).length === 4);
  assert.ok(!html.includes('lcase'), 'no case line on the axis: the case level is not a cell of this table');
  assert.ok(!/SC1|SC2|0\.15|0\.31/.test(textOf(html)), 'the column headers are the case names');
});

test('rankedLadder: a level column that does not parse for every row falls back to recordCards', () => {
  const block = { headers: ['Rank', 'Break', 'Level'], rows: [{ line: 1, cells: ['1', 'First', '12%'] }, { line: 2, cells: ['2', 'Second', 'n/a'] }] };
  const ctx = { key: r => `k:${r.line}` };
  assert.equal(C.rankedLadder(block, ctx), C.recordCards(block, ctx));
});

test('statementCard: one row per line, paired bars from a zero baseline, the verbatim cells, a Bars/Figures toggle, other text columns as captions', () => {
  const t = keyTables('CP-1', 'statement')[1], ctx = pageCtx('CP-1'), html = C.statementCard(keyBlock(t), ctx);
  assert.equal((html.match(/<div class="st-row">/g) || []).length, 13);
  assert.ok(html.includes('data-view-pick="bars"') && html.includes('data-view-pick="figures"') && html.includes('data-pane="figures" hidden'));
  assert.ok(/<span class="st-bar p0 neg" style="[^"]*"><\/span>/.test(html), 'a bracketed number is a negative bar');
  assert.ok(html.includes('class="st-zero"'), 'a zero baseline when a value is negative');
  assert.ok(html.includes('(165)') && html.includes('(139)') && html.includes('2,045'));
  const income = C.statementCard(keyBlock(keyTables('CP-1', 'statement')[0]), ctx);
  assert.ok(income.includes('<p class="st-cap">Revenue, positive</p>') && income.includes('class="st-zero"'), 'one line prints (28), so there is a zero baseline');
  const positive = C.statementCard({ headers: ['Line', 'FY2024', 'FY2023'], rows: [{ line: 1, cells: ['Sales', '200', '100'] }] }, { key: r => `k:${r.line}` });
  assert.ok(!positive.includes('class="st-zero"') && !positive.includes(' neg"'), 'no negative value, no baseline');
  assert.ok(positive.includes('style="left:0%;width:100%"') && positive.includes('style="left:0%;width:50%"'), 'bars are scaled to the card\'s largest value');
  assert.ok(/<th scope="col" class="num">FY2024<\/th>/.test(income), 'Figures: a designed table');
});

test('metricTiles: the latest period large, the earlier beneath when it is a number, a long cell is a wide text tile, the definition is a tooltip unless it is only references', () => {
  const t = keyTables('CP-1', 'metric')[0], ctx = pageCtx('CP-1'), html = C.metricTiles(keyBlock(t), ctx);
  assert.equal((html.match(/<div class="tile(?: wide)?">/g) || []).length, 35);
  assert.ok(html.includes('<p class="tile-v">7,940</p>') && html.includes('FY2023 6,585'));
  assert.ok(html.includes('data-tip="Net income + D&amp;A + interest expense-net + tax"') && html.includes('aria-label="Net income + D&amp;A + interest expense-net + tax"'), 'C24 tooltip carries the definition');
  assert.ok(!html.includes('data-tip="Calculation') && !/data-tip="[^"]*calculation/i.test(html), 'a definition that is only a calculation ID has no tooltip');
  assert.ok(html.includes('class="tile wide"') && textOf(html).includes('Not calculable: FY2022 comparatives not used'));
  assert.ok(html.includes('data-view-pick="tiles"') && html.includes('data-view-pick="table"'));
  assert.ok(html.includes('class="tip-print"') && textOf(html).includes('Filing summary of credit agreement'), 'the definition also prints');
});

test('measureTiles: tiles in rows of up to four, the latest value large, the earlier beneath, the change as a tag, the consequence as the caption', () => {
  const t = keyTables('CP-1A', 'measure')[0], ctx = pageCtx('CP-1A'), html = C.measureTiles(keyBlock(t), ctx);
  assert.ok(html.includes('class="tiles tiles-4"'));
  assert.ok(html.includes('<p class="tile-v">USD 7,940 million</p>') && html.includes('FY2023 USD 6,585 million'));
  assert.ok(html.includes('<span class="tag"><span class="tag-k">Change</span>USD 1,355 million (20.58%)</span>'));
  assert.ok(html.includes('<p class="tile-c">Growth funds debt service but partly bought via acquisitions</p>'));
  const value = keyTables('CP-2', 'measure').find(x => x.headers[1] === 'Value');
  const plain = C.measureTiles(keyBlock(value), pageCtx('CP-2'));
  assert.ok(plain.includes('<p class="tile-v">USD 7,267 million</p>') && plain.includes('2024-09-30'), 'with no period column the first value column leads');
});

test('changeCards: earlier and current side by side with an arrow, cause and effect as labelled lines, a dumbbell only when both parse; nothing computed', () => {
  const t = keyTables('CP-8', 'change')[0], ctx = pageCtx('CP-8'), html = C.changeCards(keyBlock(t), ctx);
  assert.equal((html.match(/<article class="chg-card">/g) || []).length, 6);
  assert.ok(html.includes('<p class="chg-title">Total debt / EBITDA</p>') && html.includes('<p class="chg-v">6.01x (FY2024)</p>'));
  assert.ok(html.includes('<dt>Cause</dt><dd>Unresolved</dd>') && html.includes('<dt>Effect on the credit view</dt>'));
  assert.ok(html.includes('class="i"') && html.includes('chg-arrow'));
  assert.ok(!html.includes('class="dumb"'), 'these cells carry text beside the number, so they do not parse');
  assert.ok(!/\b(?:increased|decreased|rose|fell|up by|down by)\b/i.test(html.replace(/<dd>[^<]*<\/dd>/g, '')), 'no direction is stated by the component');
  const parsed = C.changeCards({ headers: ['Measure', 'Earlier', 'Current', 'Cause'], rows: [{ line: 1, cells: ['Leverage', '6.01x', '7.25x', 'Debt'] }, { line: 2, cells: ['Cover', '3.6x', '12%', 'Mixed units'] }] }, { key: r => `k:${r.line}` });
  assert.equal((parsed.match(/class="dumb"/g) || []).length, 1, 'both parse and share a unit');
  assert.ok(parsed.includes('aria-label="Earlier 6.01x, Current 7.25x"') || parsed.includes('Earlier 6.01x, Current 7.25x'));
});

// A minimal element tree: just what handleClick reads.
function fakeTree() {
  const matches = (el, sel) => sel.split(',').some(part => { part = part.trim(); const attr = /^\[([\w-]+)\]$/.exec(part); return attr ? el.attrs[attr[1]] !== undefined || (attr[1].startsWith('data-') && el.dataset[attr[1].slice(5).replace(/-(\w)/g, (_, c) => c.toUpperCase())] !== undefined) : part.startsWith('.') ? el.classes.has(part.slice(1)) : false; });
  const make = (props = {}) => {
    const el = { attrs: {}, dataset: {}, classes: new Set(), children: [], parent: null, hidden: false, style: {}, ...props };
    el.classList = { toggle: (c, on) => { if (on) el.classes.add(c); else el.classes.delete(c); }, add: c => el.classes.add(c), remove: c => el.classes.delete(c), contains: c => el.classes.has(c) };
    el.setAttribute = (k, v) => { el.attrs[k] = String(v); };
    el.add = (...kids) => { kids.forEach(k => { k.parent = el; el.children.push(k); }); return el; };
    el.closest = sel => { for (let n = el; n; n = n.parent) if (matches(n, sel)) return n; return null; };
    el.querySelectorAll = sel => { const out = []; const walk = n => n.children.forEach(k => { if (matches(k, sel)) out.push(k); walk(k); }); walk(el); return out; };
    return el;
  };
  return make;
}

test('handleClick: choosing a case (segment or track marker) moves aria-pressed, the shown tile set and the filled markers; the toggle swaps the panes; anything else is left alone', () => {
  const make = fakeTree();
  const root = make({ dataset: { block: '', case: '1', view: 'chart' } });
  const segs = [0, 1, 2].map(n => make({ dataset: { casePick: String(n) }, classes: new Set(['case-opt']) }));
  const sets = [0, 1, 2].map(n => make({ dataset: { set: String(n) }, hidden: n !== 1 }));
  const marks = [0, 1, 2].map(n => make({ dataset: { casePick: String(n) }, classes: new Set(['mk', n === 1 ? 'on' : 'x']) }));
  const seg = make({ classes: new Set(['seg']), dataset: { i: '0' } });
  const chart = make({ dataset: { viewPick: 'chart' } }), table = make({ dataset: { viewPick: 'table' } });
  const panes = [make({ dataset: { pane: 'chart' } }), make({ dataset: { pane: 'table' }, hidden: true })];
  seg.add(chart, table);
  root.add(...segs, ...sets, ...marks, seg, ...panes);
  assert.equal(C.handleClick(segs[2]), true);
  assert.equal(root.dataset.case, '2');
  assert.deepEqual(segs.map(s => s.attrs['aria-pressed']), ['false', 'false', 'true']);
  assert.deepEqual(sets.map(s => s.hidden), [true, true, false]);
  assert.deepEqual(marks.map(m => m.classes.has('on')), [false, false, true]);
  assert.equal(C.handleClick(marks[0]), true);
  assert.deepEqual(sets.map(s => s.hidden), [false, true, true]);
  assert.equal(C.handleClick(table), true);
  assert.equal(root.dataset.view, 'table');
  assert.deepEqual([chart, table].map(b => b.attrs['aria-pressed']), ['false', 'true']);
  assert.deepEqual(panes.map(p => p.hidden), [true, false]);
  assert.equal(seg.dataset.i, '1');
  assert.equal(C.handleClick(chart), true);
  assert.deepEqual(panes.map(p => p.hidden), [false, true]);
  assert.equal(seg.dataset.i, '0');
  assert.equal(C.handleClick(make({})), false);
  assert.equal(C.handleClick(null), false);
});

test('Shapes.casePairing and the page: a header that holds an id is named by the paired case; the rest of a numeric bracket is dropped; any other remainder hides the column', () => {
  const pairing = { names: ['Base', 'Moderate', 'Severe'], ids: ['s00', 'SC1', 'SC2'] };
  const block = { headers: ['Rank', 'Break', 'Level', 'SC1 (0.15)', 'SC2 note text', 'Other SC9'], rows: [{ line: 1, cells: ['1', 'First', '10%', 'Breached', 'x', 'y'] }] };
  const html = C.rankedLadder(block, { key: r => `k:${r.line}`, tokens: ['s00', 'SC1', 'SC2', 'SC9'], pairing, evidenceHref: '#e' });
  assert.ok(html.includes('Moderate') && html.includes('Breached'));
  assert.ok(!html.includes('SC2') && !html.includes('note text') && !/\bx\b/.test(textOf(html).replace(/Level/g, '')), 'SC2 note text is hidden: its header has a remainder that is not a number');
  assert.ok(!html.includes('SC9'));
});

test('every component draws at least the label, and a table of one row, without error', () => {
  const rows = [{ line: 1, cells: ['Only', '1', '2', 'x'] }];
  for (const [shape, headers] of [['cases', ['Measure', 'Base', 'Severe', 'Creditor consequence']], ['caseRows', ['Scenario', 'A', 'B', 'C']], ['ranked', ['Rank', 'Break', 'Level', 'State']], ['statement', ['Line', 'FY2024', 'FY2023', 'Sign']], ['metric', ['Metric', 'FY2024', 'FY2023', 'Definition']], ['measure', ['Measure', 'FY2024', 'FY2023', 'Creditor consequence']], ['change', ['Measure', 'Earlier', 'Current', 'Cause']]]) {
    const html = C.render(shape, { headers, rows }, { key: r => `k:${r.line}` });
    assert.ok(html.length > 50 && textOf(html).includes('Only') || shape === 'caseRows' || shape === 'ranked', shape);
  }
});

// ---- Non-numeric shape components (library redesign, task 6): the answer key's real tables are the inputs.
const countOf = (html, re) => (html.match(re) || []).length;
const WORD_COMPONENT = { status: 'statusChecklist', sided: 'sidedBoard', moduleState: 'moduleStateTiles', qa: 'qaAccordion', facts: 'factList', records: 'recordCards', matrix: 'riskMatrix', watch: 'watchList' };
const keyHeaderIs = (t, at, rx) => rx.test(String(t.headers[at]).trim().toLowerCase());
// The cells the drawing must hold. A side cell and a category cell are the word and, apart, what stands in their closing brackets; the module name of a
// moduleState row is the handoff's own text, drawn even where it ends in a module code.
function wordCells(t, ctx) {
  const out = [];
  t.headers.forEach((header, at) => {
    if (t.hidden.includes(at)) return;
    for (const cells of t.rows) {
      const cell = plainCell(cells[at]);
      if (cell === '') continue;
      const subject = t.shape === 'moduleState' && at === 0;
      if (!subject && C.findingCell(cell, ctx).html === undefined) continue;
      const split = (t.shape === 'sided' && keyHeaderIs(t, at, /^side\b/)) || (t.shape === 'facts' && keyHeaderIs(t, at, /^category$/)) ? /^(.*?)\s*\(([^()]*)\)$/.exec(cell) : null;
      out.push(...(split ? [split[1], split[2]] : [cell]));
    }
  });
  return out;
}

test('render: each of the eight remaining shapes goes to its component, and the output holds every drawn cell of every key table of that shape', () => {
  for (const [shape, name] of Object.entries(WORD_COMPONENT)) {
    const found = KEY.tables.filter(t => t.shape === shape);
    assert.ok(found.length >= 1, shape);
    assert.equal(typeof C[name], 'function', name);
    for (const t of found) {
      const ctx = pageCtx(t.module), block = keyBlock(t);
      assert.equal(Shapes.tableShape(block), shape, `${t.module} ${t.heading}`);
      const html = C.render(shape, block, ctx);
      assert.equal(html, C[name](block, ctx), `${shape} is drawn by ${name}`);
      assert.ok(html.length > 200, `${t.module} ${t.heading} draws`);
      const text = textOf(html);
      assert.deepEqual(wordCells(t, ctx).filter(cell => !text.includes(cell)), [], `${shape} ${t.module} ${t.heading}: cells not drawn`);
      noMarkdown(html);
      assert.ok(/<button[^>]*class="basis-link trace-row"/.test(html), `${shape}: a trace control`);
      assert.ok(!/<table/.test(html) || shape === 'matrix', `${shape}: no raw grid`);
    }
  }
});

test('no word component draws an identifier of the module, a calculation ID, a source or a hidden column', () => {
  for (const t of KEY.tables.filter(x => Object.hasOwn(WORD_COMPONENT, x.shape))) {
    const ctx = pageCtx(t.module), html = C.render(t.shape, keyBlock(t), ctx), text = textOf(html);
    for (const token of idTextOf(ctx)) assert.ok(!new RegExp(`(?<![A-Za-z0-9_])${token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![A-Za-z0-9_])`).test(text), `${t.module} ${t.heading} draws ${token}`);
    assert.ok(!/calculations? [A-Z]{1,2}\d{2}/i.test(text), `${t.module} ${t.heading} draws a calculation ID`);
    assert.ok(!/\.jsonl|\.htm\b|sha256|Basis:/.test(text), 'no file name or Basis');
    t.headers.forEach((header, at) => {
      if (!t.hidden.includes(at)) return;
      for (const cells of t.rows) { const cell = plainCell(cells[at]); if (cell.length > 12) assert.ok(!text.includes(cell), `${t.module} ${t.heading}: hidden column ${header} drawn`); }
    });
  }
});

// A table of each shape with the key's own headers and a row built from `make(header, column)`.
const keyShapes = () => Object.keys(WORD_COMPONENT).map(shape => KEY.tables.find(t => t.shape === shape));
test('variants: one row, empty cells, a row shorter or longer than its headers, HTML metacharacters and a very long token draw without error, and every cell is escaped text', () => {
  for (const t of keyShapes()) {
    const ctx = { key: row => `k:${row.line}`, evidenceHref: '#e', caption: 'Variant' }, name = WORD_COMPONENT[t.shape];
    const make = (fill, n = t.headers.length) => ({ headers: t.headers, rows: [{ line: 1, cells: Array.from({ length: n }, (_, at) => fill(at)) }] });
    // one row, every cell empty: the component still answers (a string), and does not throw
    assert.equal(typeof C[name](make(() => ''), ctx), 'string', `${t.shape}: empty cells`);
    for (const n of [1, 2, t.headers.length + 2]) assert.equal(typeof C[name](make(at => `cell ${at}`, n), ctx), 'string', `${t.shape}: ${n} cells for ${t.headers.length} headers`);
    // metacharacters: escaped in every drawn cell, and the visible text is the cell as written
    const meta = C[name](make(at => (t.hidden.includes(at) ? 'hidden' : '<b>&" x')), ctx);
    assert.ok(!meta.includes('<b>&"') && !meta.includes('<b>&amp;') && meta.includes('&lt;b&gt;&amp;'), `${t.shape}: metacharacters are escaped`);
    assert.ok(textOf(meta).includes('<b>&" x'), `${t.shape}: the visible text is the cell as written`);
    // a very long unbroken token is drawn whole (CSS wraps it)
    const long = 'Q'.repeat(300), big = C[name](make(at => (t.hidden.includes(at) ? 'hidden' : long)), ctx);
    assert.ok(textOf(big).includes(long), `${t.shape}: the long token is whole`);
    // no row at all draws nothing (and does not throw)
    assert.equal(typeof C[name]({ headers: t.headers, rows: [] }, ctx), 'string');
  }
});

test('Review Focus 1: a table a component cannot place, and a table of an unknown shape, is a record card with every non-hidden cell', () => {
  const ctx = { key: row => `k:${row.line}`, evidenceHref: '#e' };
  const odd = { headers: ['Zeta', 'Omega', 'Source'], rows: [{ line: 3, cells: ['one', 'two', 'src.pdf'] }, { line: 4, cells: ['three', '4.5x', 'src.pdf'] }] };
  for (const name of Object.values(WORD_COMPONENT).filter(n => n !== 'qaAccordion')) assert.equal(C[name](odd, ctx), C.recordCards(odd, ctx), `${name} falls back to recordCards`);
  const unknown = textOf(C.render('shape-from-the-future', odd, ctx));
  for (const cell of ['one', 'two', 'three', '4.5x', 'Omega']) assert.ok(unknown.includes(cell), cell);
  assert.ok(!unknown.includes('src.pdf'));
  // each component's own missing column: status without a status column, sided without a side column, and so on
  const rows = [{ line: 1, cells: ['a', 'b', 'c'] }];
  for (const [name, headers] of [['statusChecklist', ['Item', 'Detail', 'Effect']], ['sidedBoard', ['Driver', 'Figure', 'Reading']], ['moduleStateTiles', ['Module', 'Cause', 'Why']], ['facts', ['Item', 'Category', 'Note']], ['riskMatrix', ['Event', 'Probability', 'Likelihood']], ['watchList', ['Indicator', 'Threshold', 'Limitation']]]) {
    const block = { headers, rows }, fn = name === 'facts' ? 'factList' : name;
    assert.equal(C[fn](block, ctx), C.recordCards(block, ctx), `${fn} without its column`);
  }
});

test('statusChecklist: a row per item, the state word always beside its icon, tone from the word, other columns as labelled lines', () => {
  const t = keyTables('CP-5', 'status')[0], ctx = pageCtx('CP-5'), html = C.statusChecklist(keyBlock(t), ctx);
  assert.equal(countOf(html, /<li class="ck-row">/g), 5);
  const states = [...html.matchAll(/<span class="state (\w+)">(<svg [^>]*>.*?<\/svg>)<span class="state-w">([^<]*)<\/span><\/span>/g)].map(m => [m[1], m[3]]);
  assert.deepEqual(states, [['ok', 'Committee-Ready'], ['warn', 'Remediation Needed'], ['ok', 'Committee-Ready'], ['ok', 'Committee-Ready'], ['warn', 'Remediation Needed']]);
  assert.equal(countOf(html, /<span class="state /g), 5, 'every state is an icon with its word');
  for (const label of ['Lineage class', 'Re-performed', 'Creditor consequence']) assert.ok(html.includes(`<dt>${label}</dt>`), label);
  assert.ok(!html.includes('<dt>Source') && !html.includes('calculation V'));
  const legal = C.statusChecklist(keyBlock(keyTables('CP-4', 'status')[0]), pageCtx('CP-4'));
  assert.ok(legal.includes('<span class="state warn">') && legal.includes('Not in source set; incorporated by reference only') && legal.includes('<span class="state-w">Unverified summary</span>'));
  assert.ok(/class="ck-list" data-block aria-label="Table"/.test(legal));
});

test('statusChecklist: the state tone comes from the word; an unknown word is neutral; an empty state is n.a. with the neutral icon; a level column is the three-segment meter', () => {
  const block = { headers: ['Item', 'Status', 'Confidence'], rows: [['A', 'Passed', 'High'], ['B', 'Gate fails', 'Low'], ['C', 'Not found', 'Medium'], ['D', 'Unchanged', 'Low'], ['E', 'New', 'High'], ['F', 'Frobnicated', 'Low'], ['G', '', 'Low']].map((cells, i) => ({ line: i + 1, cells })) };
  const html = C.statusChecklist(block, { key: r => `k:${r.line}` });
  assert.deepEqual([...html.matchAll(/<span class="state (\w+)">/g)].map(m => m[1]), ['ok', 'bad', 'warn', 'same', 'new', 'info', 'info']);
  assert.ok(html.includes('<span class="na" title="Empty in the handoff">n.a.</span>'));
  assert.equal(countOf(html, /<span class="meter-w">/g), 7);
  assert.ok(html.includes('<span class="meter-w">Medium</span>') && !html.includes('<dd>High</dd>'));
});

test('statusChecklist: a cell holding an identifier leaves a link to Evidence in its place, and the identifier is not drawn', () => {
  const block = { headers: ['Item', 'Status', 'Effect'], rows: [{ line: 1, cells: ['Gate', 'Blocked', 'Waits on EV-9 before release'] }] };
  const html = C.statusChecklist(block, { key: r => `k:${r.line}`, tokens: ['EV-9'], evidenceHref: '#W-Evidence/registers?m=X' });
  assert.ok(html.includes('<dt>Effect</dt><dd><a class="in-ev" href="#W-Evidence/registers?m=X">In Evidence</a></dd>') && !html.includes('EV-9'));
});

test('sidedBoard: two columns from the cell\'s own side word, a count per side, entries in the table\'s order, a qualifier as a tag', () => {
  const t = keyTables('CP-6', 'sided')[0], ctx = pageCtx('CP-6'), html = C.sidedBoard(keyBlock(t), ctx);
  assert.ok(html.includes('<p class="sd-hs sd-s0"><i class="sd-dot" aria-hidden="true"></i>Bull<b class="sd-n">3</b></p>') && html.includes('<p class="sd-hs sd-s1"><i class="sd-dot" aria-hidden="true"></i>Bear<b class="sd-n">5</b></p>'));
  const lines = [...html.matchAll(/<div class="sd-line sd-s(\d)">.*?<span class="sd-side"><i class="sd-dot" aria-hidden="true"><\/i>(\w+)<\/span>(?:<span class="tag q-tag">([^<]*)<\/span>)?/g)].map(m => [m[1], m[2], m[3]]);
  assert.deepEqual(lines, [['0', 'Bull', undefined], ['0', 'Bull', undefined], ['0', 'Bull', undefined], ['1', 'Bear', undefined], ['1', 'Bear', undefined], ['1', 'Bear', undefined], ['1', 'Bear', undefined], ['1', 'Bear', 'weakly']]);
  assert.ok(html.includes('<p class="sd-fig">USD 526.39 million / 2.36x</p>') && html.includes('<p class="sd-name">Junior minus senior running yield</p>') && html.includes('<dt>Chair reading</dt><dd>Junior pickup unproven</dd>'));
  assert.ok(!html.includes('Bear (weakly)'), 'the cell is the word and its tag');
});

test('sidedBoard: "Bear (weakly)" is placed right with the tag "weakly"; a side word neither column uses, and an empty one, go full width beneath, not dropped', () => {
  const rows = [['Cover', '3.6x', 'Bull', 'a'], ['Leverage', '8.7x', 'Bear (weakly)', 'b'], ['Yield', '1.1 pp', 'Bear', 'c'], ['Liquidity', '2.3x', 'Bull', 'd'], ['Mix', '9%', 'Neutral (unclear)', 'e'], ['Pending', '1x', '', 'f']].map((cells, i) => ({ line: i + 1, cells }));
  const html = C.sidedBoard({ headers: ['Driver', 'Figure', 'Side it supports', 'Reading'], rows }, { key: r => `k:${r.line}` });
  const line = n => html.split('<div class="sd-line').slice(1)[n];
  // Document order is now column by column (left side, right side, then the rows on neither): Cover, Liquidity | Leverage, Yield | Mix, Pending.
  assert.ok(line(2).startsWith(' sd-s1">') && line(2).includes('<span class="tag q-tag">weakly</span>') && line(2).includes('>Bear</span>') && line(2).includes('Leverage'));
  assert.ok(line(4).startsWith(' sd-s2">') && line(4).includes('Neutral') && line(4).includes('<span class="tag q-tag">unclear</span>') && line(4).includes('Mix'));
  assert.ok(line(5).startsWith(' sd-s2">') && line(5).includes('Pending') && !line(5).includes('sd-side'), 'an empty side cell: the row is drawn beneath with no side word');
  assert.ok(!html.includes('sd-node'), 'no spine node tied to a row position');
  assert.deepEqual([...html.matchAll(/<div class="sd-col sd-s(\d)">(.*?)<\/div><\/div>(?=<div class="sd-col|<\/div>)/gs)].map(m => [m[1], [...m[2].matchAll(/<p class="sd-name">([^<]*)</g)].map(n => n[1])]), [['0', ['Cover', 'Liquidity']], ['1', ['Leverage', 'Yield']]], 'two independent columns, each from the top in written order');
});

test('moduleStateTiles: a page that supplies countNoun gets that word as the caption of the count, not the name column\'s header; the text of every row is unchanged', () => {
  const t = keyTables('CP-8', 'moduleState')[0], ctx = pageCtx('CP-8'), plain = C.moduleStateTiles(keyBlock(t), ctx), named = C.moduleStateTiles(keyBlock(t), {...ctx, countNoun: 'modules'});
  assert.deepEqual([...named.matchAll(/<summary><b class="ms-n">(\d+)<\/b> <span class="ms-nl">([^<]*)</g)].map(m => [m[1], m[2]]), [['8', 'modules'], ['4', 'modules']]);
  assert.ok(!named.includes('Module</span>') && plain.includes('<b class="ms-n">8</b> · <span class="ms-nl">Module</span>'), 'without it, as before');
  for (const row of t.rows) assert.ok(textOf(named).includes(row[0]) && textOf(named).includes(row[3]), row[0]);
});

test('moduleStateTiles: a repeated state is one tile (icon, word, count, the modules in a details); a state seen once stays a full tile with its module name as the title', () => {
  const t = keyTables('CP-8', 'moduleState')[0], ctx = pageCtx('CP-8'), html = C.moduleStateTiles(keyBlock(t), ctx);
  assert.equal(countOf(html, /<article class="ms-tile ms-group">/g), 2);
  assert.equal(countOf(html, /<article class="ms-tile">/g), 0, 'no title-less tile');
  assert.ok(/<span class="state same">.*?<span class="state-w">Unchanged<\/span><\/span>/.test(html) && /<span class="state new">.*?<span class="state-w">New<\/span><\/span>/.test(html));
  assert.deepEqual([...html.matchAll(/<summary><b class="ms-n">(\d+)<\/b> · <span class="ms-nl">(\w+)</g)].map(m => [m[1], m[2]]), [['8', 'Module'], ['4', 'Module']]);
  assert.equal(countOf(html, /<details class="ms-list">/g), 2);
  for (const row of t.rows) assert.ok(textOf(html).includes(row[0]) && textOf(html).includes(row[3]), row[0]);
  assert.ok(!/<details[^>]* open/.test(html), 'folded');
  assert.equal(countOf(html, /class="basis-link trace-row"/g), 12, 'every module row stays reachable');
  const mixed = C.moduleStateTiles({ headers: ['Module', 'Status', 'Why'], rows: [['Alpha', 'Unchanged', 'same'], ['Beta', 'Unchanged', 'same'], ['Gamma', 'Changed', 'moved']].map((cells, i) => ({ line: i + 1, cells })) }, { key: r => `k:${r.line}` });
  assert.ok(mixed.includes('<article class="ms-tile"><div class="ms-head"><p class="ms-title">Gamma</p>') && mixed.includes('<dt>Why</dt><dd>moved</dd>') && countOf(mixed, /ms-group/g) === 1);
  assert.ok(mixed.indexOf('ms-group') < mixed.indexOf('Gamma'), 'tiles keep the order of the first row of each');
  assert.ok(!/ms-(?:id|code)|CP-\d/.test(mixed), 'no module id is added');
});

test('qaAccordion: a native details per question with the answer-state badge; a question with nothing to unfold is a plain row; without a state column there is no badge', () => {
  const t = keyTables('CP-DR', 'qa')[0], ctx = pageCtx('CP-DR'), html = C.qaAccordion(keyBlock(t), ctx);
  assert.equal(countOf(html, /<div class="qa-item">/g), 6);
  assert.deepEqual([...html.matchAll(/<span class="state (\w+)">.*?<span class="state-w">([^<]*)<\/span>/g)].map(m => [m[1], m[2]]), [['warn', 'Partly (issuer view)'], ['warn', 'Partly (issuer only)'], ['warn', 'Not found'], ['ok', 'Answered'], ['warn', 'Partly (issuer view)'], ['ok', 'Answered']]);
  assert.equal(countOf(html, /<details/g), 0, 'the key table has no column to unfold, so no empty accordion');
  const wide = C.qaAccordion({ headers: ['Question', 'Answer state', 'Finding'], rows: [{ line: 1, cells: ['Is it secured?', 'Answered', 'Yes, first lien'] }, { line: 2, cells: ['Who guarantees?', 'Not found', ''] }] }, { key: r => `k:${r.line}` });
  assert.ok(/<details class="qa-d"><summary><span class="qa-q">Is it secured\?<\/span><span class="state ok">.*?Answered<\/span><\/span><span class="qa-ch"/.test(wide) && wide.includes('<dt>Finding</dt><dd>Yes, first lien</dd>'));
  assert.equal(countOf(wide, /<details/g), 1, 'an empty answer has nothing to unfold');
  const none = C.qaAccordion({ headers: ['Question', 'Basis note'], rows: [{ line: 1, cells: ['Why?', 'Because of the filing'] }] }, { key: r => `k:${r.line}` });
  assert.ok(!none.includes('class="state') && none.includes('<dt>Basis note</dt><dd>Because of the filing</dd>'), 'no state column, no badge, and no state inferred from prose');
});

test('factList: definition groups by the category column, a bracketed qualifier as a tag, the count of facts per group; flat without a category column', () => {
  const t = keyTables('CP-1A', 'facts')[0], ctx = pageCtx('CP-1A'), html = C.factList(keyBlock(t), ctx);
  assert.deepEqual([...html.matchAll(/<p class="fl-head">([^<]*)<b class="fl-n">(\d+)<\/b><\/p>/g)].map(m => [m[1], m[2]]), [['Documentary Fact', '6'], ['Management Language', '2']]);
  assert.ok(html.includes('<span class="tag q-tag">leadership claim is Management Language</span>') && html.includes('<span class="tag q-tag">estimates</span>'));
  assert.equal(countOf(html, /<div class="fl-row">/g), 8);
  assert.ok(html.includes('<dt>Business</dt>') && html.includes('<dt>Workforce</dt>') && !html.includes('TDG_2024'));
  const flat = C.factList({ headers: ['Item', 'Fact'], rows: [{ line: 1, cells: ['Domicile', 'Delaware'] }] }, { key: r => `k:${r.line}` });
  assert.ok(!flat.includes('fl-head') && flat.includes('<dt>Domicile</dt>') && flat.includes('Delaware'));
});

test('recordCards: one card per row, the first non-hidden column its label, every other non-hidden cell a labelled line (the records shape)', () => {
  for (const t of KEY.tables.filter(x => x.shape === 'records')) {
    const ctx = pageCtx(t.module), html = C.render('records', keyBlock(t), ctx);
    assert.equal(countOf(html, /<article class="rec-card">/g), t.rows.length);
    assert.equal(countOf(html, /<p class="rec-title">/g), t.rows.length, 'every card has its label');
    const first = t.headers.findIndex((h, at) => !t.hidden.includes(at));
    for (const cells of t.rows) assert.ok(html.includes(`<p class="rec-title">${plainCell(cells[first])}</p>`), cells[first]);
  }
});

test('riskMatrix: the table\'s own row and column labels in their written order, a real table with header associations, several items in one cell, the classification word in each chip', () => {
  const t = keyTables('CP-2A', 'matrix')[0], ctx = pageCtx('CP-2A'), html = C.riskMatrix(keyBlock(t), ctx);
  assert.deepEqual([...html.matchAll(/<th scope="row">([^<]*)<\/th>/g)].map(m => m[1]), ['High', 'Medium']);
  assert.deepEqual([...html.matchAll(/<th scope="col">([^<]*)<\/th>/g)].map(m => m[1]), ['Low', 'Medium', 'High'], 'an ordinal axis runs low to high');
  assert.ok(html.includes('<th scope="col" class="rm-corner">') && html.includes('<caption class="sr-only">'));
  const cells = [...html.matchAll(/<tr><th scope="row">(\w+)<\/th>(.*?)<\/tr>/g)].map(m => [m[1], [...m[2].matchAll(/<td>(.*?)<\/td>/g)].map(c => [...c[1].matchAll(/<p class="rm-t">([^<]*)<\/p>/g)].map(x => x[1]))]);
  assert.deepEqual(cells, [['High', [['Securitization fully drawn', 'Post-period buybacks'], [], ['Special dividend paid']]], ['Medium', [['Securitization maturity'], ['2027 subordinated notes maturity'], ['FY2028 maturity cluster']]]]);
  assert.ok(html.includes('<li class="rm-chip rm-c-critical">') && html.includes('<span class="sr-only">P/I Classification: </span>Critical'));
  assert.equal(countOf(html, /<li class="rm-chip/g), 6);
  assert.ok(/<p class="rm-lg"><span class="rm-lg-k">P\/I Classification<\/span>.*Critical.*Medium.*Low.*High/.test(html), 'the legend lists the words the table uses, in its order');
});

test('riskMatrix: no ramp from position; a classification word the table invents gets no colour; a row with no probability or impact is listed beneath, not dropped', () => {
  const rows = [['Fire', 'Rare', 'Severe', 'Escalate'], ['Flood', 'Likely', 'Minor', 'Watch'], ['Theft', '', 'Minor', 'Watch'], ['Quake', 'Rare', 'Minor', 'Watch']].map((cells, i) => ({ line: i + 1, cells }));
  const html = C.riskMatrix({ headers: ['Event', 'Probability', 'Impact', 'Rating'], rows }, { key: r => `k:${r.line}` });
  assert.deepEqual([...html.matchAll(/<th scope="row">([^<]*)<\/th>/g)].map(m => m[1]), ['Rare', 'Likely']);
  assert.deepEqual([...html.matchAll(/<th scope="col">([^<]*)<\/th>/g)].map(m => m[1]), ['Severe', 'Minor']);
  assert.ok(!/rm-c-/.test(html), 'Escalate and Watch are not colours');
  assert.ok(/Not placed in the grid.*Theft/.test(html) && countOf(html, /<li class="rm-chip/g) === 4);
  assert.ok(!/data-h=|rm-heat/.test(html), 'no heat from position');
});

test('watchList: indicator, a leading or lagging icon with its word, the threshold as written, the limitation in a details; no limitation, no details', () => {
  const t = keyTables('CP-2A', 'watch')[0], ctx = pageCtx('CP-2A'), html = C.watchList(keyBlock(t), ctx);
  assert.equal(countOf(html, /<div class="wl-item">/g), t.rows.length);
  assert.equal(countOf(html, /<details class="wl-d">/g), t.rows.length);
  assert.ok(html.includes(`<span class="wl-lead">${C.icon('arrow-up-right')}Leading</span>`) && html.includes(`<span class="wl-lead">${C.icon('history')}Lagging</span>`));
  for (const cells of t.rows) {
    assert.ok(html.includes(`<span class="wl-th">${plainCell(cells[3])}</span>`), cells[3]);
    assert.ok(html.includes(`<p class="wl-lim"><b>Limitation</b> ${plainCell(cells[7])}</p>`), cells[7]);
  }
  assert.ok(!/<details[^>]* open/.test(html) && !html.includes('Trigger ID') && !html.includes('CP-2A-MON'));
  const plain = C.watchList({ headers: ['Indicator', 'Leading / Lagging', 'Threshold', 'Limitation'], rows: [{ line: 1, cells: ['Spread', 'Concurrent', 'Above 400bp', ''] }] }, { key: r => `k:${r.line}` });
  assert.ok(!plain.includes('<details') && plain.includes('Above 400bp') && plain.includes(`<span class="wl-lead">${C.icon('activity')}Concurrent</span>`));
});

test('every drawn cell sits in an element whose CSS wraps a long unbroken token', () => {
  const css = fs.readFileSync(path.join(__dirname, 'screen.css'), 'utf8');
  for (const cls of ['ck-label', 'sd-name', 'sd-fig', 'ms-title', 'qa-q', 'fl-v', 'rm-t', 'wl-t', 'wl-th', 'state']) {
    const rule = new RegExp(`(?:^|[},\\n])[^{}]*\\.${cls}\\b[^{}]*\\{[^}]*overflow-wrap:anywhere`);
    assert.ok(rule.test(css), `.${cls} wraps`);
  }
});

test('print: the folds of these components are opened for the print and put back as they were', () => {
  const fold = open => ({ open, dataset: {} }), folds = [fold(false), fold(true)];
  const root = { querySelectorAll: selector => { assert.equal(selector, '.qa-d, .wl-d, .ms-list, .mt, .chg-fold, .change-module'); return folds; } };
  C.foldsForPrint(root, true);
  assert.deepEqual(folds.map(f => f.open), [true, true]);
  C.foldsForPrint(root, false);
  assert.deepEqual(folds.map(f => f.open), [false, true]);
  assert.deepEqual(folds.map(f => f.dataset), [{}, {}]);
});

test('the state icons come from icon files: the two new ones are in the table', () => {
  for (const name of ['arrow-up-right', 'history']) assert.ok(Object.hasOwn(C.ICON_PATHS, name), name);
});


// ---- Fix round 1
const { spawnSync } = require('node:child_process');
const WEB = __dirname;
function inChild(source) {
  const run = spawnSync(process.execPath, ['-e', `const C=require(${JSON.stringify(path.join(WEB, 'components.js'))});${source}`], { timeout: 5000, encoding: 'utf8' });
  return { returned: !run.error && run.status === 0, out: run.stdout, err: run.stderr };
}
const tb = (headers, rows) => ({ headers, rows: rows.map((cells, i) => ({ line: i + 1, cells })) });
const plainCtx = over => ({ key: r => `k:${r.line}`, evidenceHref: '#e', caption: 'T', tokens: [], pairing: null, ...over });

test('rankedLadder terminates when the largest level is 0 and still draws the ladder, on a fixed axis with ticks at its two ends only', () => {
  for (const rows of [[['1', 'Already breached', '0%', 'Breached']], [['1', 'A', '0', 'Reached'], ['2', 'B', '0', 'Not reached']], [['1', 'A', '12%', 'Not reached']]]) {
    const block = JSON.stringify(rows);
    const run = inChild(`const b={headers:['Rank','Break','Decline at break','Base case'],rows:${block}.map((cells,i)=>({line:i+1,cells}))};const h=C.rankedLadder(b,{key:r=>'o:'+r.line});process.stdout.write(String(h.includes('class="ladder')));`);
    assert.ok(run.returned, `did not return within 5 s for ${block}`);
    assert.equal(run.out, 'true', block);
  }
  const zero = C.rankedLadder(tb(['Rank', 'Break', 'Decline at break', 'Base case'], [['1', 'Already breached', '0%', 'Breached']]), plainCtx());
  for (const cell of ['Already breached', '0%', 'Breached']) assert.ok(textOf(zero).includes(cell), cell);
  assert.deepEqual([...zero.matchAll(/<span class="ltick-l" data-tick[^>]*>([^<]*)</g)].map(m => m[1]), ['0%', '100%']);
  assert.ok(zero.includes('class="lm" role="img" style="left:0%"'));
  const plain = C.rankedLadder(tb(['Rank', 'Break', 'Level'], [['1', 'A', '0'], ['2', 'B', '0']]), plainCtx());
  assert.deepEqual([...plain.matchAll(/<span class="ltick-l" data-tick[^>]*>([^<]*)</g)].map(m => m[1]), ['0', '1']);
});

test('rankedLadder: a level that is not a finite number falls back to record cards', () => {
  const block = tb(['Rank', 'Break', 'Level'], [['1', 'A', '12%'], ['2', 'B', '1e999']]);
  assert.equal(C.rankedLadder(block, plainCtx()), C.recordCards(block, plainCtx()));
});

test('ladder markers are images with a name, not focusable controls', () => {
  const html = C.rankedLadder(keyBlock(keyTables('CP-2A', 'ranked')[0]), pageCtx('CP-2A'));
  assert.equal((html.match(/<div class="lm" role="img" style="[^"]*" aria-label="Break \d, [^"]+"><span class="lm-n">/g) || []).length, 4, html.slice(0, 600));
  assert.ok(!/class="lm"[^>]*tabindex/.test(html));
});

const casesT = tb(['Measure', 'Base case', 'Moderate scenario', 'Severe scenario'], [['Leverage', '6.0x', '7.0x', '8.7x']]);
const defsT = tb(['Scenario ID', 'Decline', 'Anchor'], [['s00', '0', 'Control'], ['SC1', '0.15', 'Half share'], ['SC2', '0.31', 'Full share']]);
const otherT = tb(['Scenario', 'Narrative', 'Trigger'], [['Severe: aftermarket collapse', 'Full share lost', 'Recession'], ['Base: steady state', 'Nothing changes', 'None'], ['Moderate: partial loss', 'Half share lost', 'Slowdown']]);

test('case names apply by scenario id, never by position', () => {
  const tables = [casesT, defsT, otherT];
  const pairing = Shapes.casePairing(tables);
  assert.deepEqual({ names: pairing.names, ids: pairing.ids }, { names: ['Base case', 'Moderate scenario', 'Severe scenario'], ids: ['s00', 'SC1', 'SC2'] });
  const ctx = plainCtx({ tokens: Shapes.idTokens([{ blocks: tables.map(b => ({ type: 'table', ...b })) }]), pairing });
  const titles = html => [...html.matchAll(/<h4 class="cr-title">([^<]*)<\/h4>/g)].map(m => m[1]);
  assert.deepEqual(titles(C.caseRowsBlock(defsT, ctx)), ['Base case', 'Moderate scenario', 'Severe scenario']);
  // the reviewer's second table: no row's first cell is an id: numbered badges and the first cell drawn as its title
  const unpaired = C.caseRowsBlock(otherT, ctx);
  assert.deepEqual(titles(unpaired), ['Severe: aftermarket collapse', 'Base: steady state', 'Moderate: partial loss']);
  assert.deepEqual([...unpaired.matchAll(/<span class="cr-badge">(\d)<\/span>/g)].map(m => m[1]), ['1', '2', '3']);
  assert.ok(!/Base case|Moderate scenario|Severe scenario/.test(unpaired));
  for (const cell of ['Full share lost', 'Recession', 'Nothing changes', 'Slowdown']) assert.ok(textOf(unpaired).includes(cell), cell);
  // the ids in another order: each row takes the name of its own id
  const reordered = tb(['Scenario', 'Narrative', 'Trigger'], [['SC2', 'Full share lost', 'Recession'], ['s00', 'Nothing changes', 'None'], ['SC1', 'Half share lost', 'Slowdown']]);
  assert.deepEqual(titles(C.caseRowsBlock(reordered, ctx)), ['Severe scenario', 'Base case', 'Moderate scenario']);
  // a column with two ids and one other text: two rows are named, the third is numbered and its first cell is drawn
  const mixed = tb(['Scenario', 'Narrative', 'Trigger'], [['SC1', 'Half share lost', 'Slowdown'], ['Reverse stress', 'Total loss', 'Default'], ['SC2', 'Full share lost', 'Recession']]);
  const mixedHtml = C.caseRowsBlock(mixed, ctx);
  assert.deepEqual(titles(mixedHtml), ['Moderate scenario', 'Reverse stress', 'Severe scenario']);
  assert.deepEqual([...mixedHtml.matchAll(/<span class="cr-badge">(\d)<\/span>/g)].map(m => m[1]), ['2']);
  // no pairing, no names
  assert.equal(Shapes.casePairing([casesT, otherT]), null);
  assert.deepEqual(titles(C.caseRowsBlock(reordered, plainCtx({ tokens: ['s00', 'SC1', 'SC2'] }))), []);
});

test('idTokens: a token holds a digit and is not a period label; word-only ids and periods are ordinary text', () => {
  const sections = [{ blocks: [{ type: 'table', ...tb(['Case ID', 'Description'], [['Base', 'x'], ['High', 'x'], ['FY24', 'x'], ['FY2024A', 'x'], ['2024', 'x'], ['Q3 2024', 'x'], ['H1 24', 'x'], ['LTM', 'x'], ['SC1', 'x'], ['EV-01', 'x']]) }] }];
  assert.deepEqual(Shapes.idTokens(sections), ['SC1', 'EV-01']);
  const ctx = { tokens: Shapes.idTokens(sections) };
  assert.equal(C.findingCell('Leverage is high in the Base view', ctx).html, 'Leverage is high in the Base view');
  assert.equal(C.findingCell('Revenue in FY24 rose', ctx).html, 'Revenue in FY24 rose');
  assert.equal(C.findingCell('Under SC1 leverage rises', ctx).inEvidence, true);
});

test('one calculation-ID pattern, shared by findingCell and methodNote: capital C, one space, plural allowed', () => {
  assert.ok(Shapes.CALCULATION_ID instanceof RegExp && !Shapes.CALCULATION_ID.flags.includes('i'));
  assert.deepEqual(C.findingCell('See calculation FY24 note', {}), { html: 'See calculation FY24 note' });
  assert.deepEqual(C.findingCell('Per calculations D03 and D04, leverage rises', {}), { omitted: true, inEvidence: true });
  assert.deepEqual(C.findingCell('Leverage (calculation D03).', {}), { omitted: true, inEvidence: true });
  assert.equal(Shapes.methodNote('See calculation FY24 note', []), null);
  assert.equal(Shapes.methodNote('Per calculations D03 and D04', []), 'calculations');
  assert.equal(Shapes.methodNote('Per Calculation D03', []), 'calculations');
});

test('an omitted cell that holds an identifier in a sentence leaves the Evidence link; an id token alone is plain omission', () => {
  assert.deepEqual(C.findingCell('s00', { tokens: ['s00', 'SC1'] }), { omitted: true });
  assert.deepEqual(C.findingCell('SC1; s00', { tokens: ['s00', 'SC1'] }), { omitted: true });
  const metric = tb(['Metric', 'FY2024', 'FY2023', 'Definition / identity'], [['FCF', '1,880', '1,236', 'House definition; calculations C15, C16'], ['Cash', '7,267', '6,000', 'Reported']]);
  const tiles = C.metricTiles(metric, plainCtx());
  assert.equal((tiles.slice(0, tiles.indexOf('data-pane="table"')).match(/class="in-ev"/g) || []).length, 1, 'the tile view links to Evidence for the omitted definition');
  assert.ok(!textOf(tiles).includes('House definition'));
  const rows = tb(['Scenario', 'Decline', 'Note', 'Basis'], [['As SC1; also more', '0.1', 'first note', 'text one'], ['SC2', '0.2', 'second note', 'text two'], ['Plain name', '0.3', 'third note', 'text three']]);
  const html = C.caseRowsBlock(rows, plainCtx({ tokens: ['SC1', 'SC2'] }));
  assert.deepEqual([...html.matchAll(/<span class="cr-badge">(\d)<\/span>/g)].map(m => m[1]), ['1', '2', '3']);
  assert.equal((html.match(/class="in-ev"/g) || []).length, 1, 'a sentence with an identifier links once; a bare id does not');
  assert.ok(html.includes('<h4 class="cr-title">Plain name</h4>'));
});

test('a row with more cells than headers keeps the extra cells in every numeric component', () => {
  const extra = 'EXTRA-CELL-BEYOND-HEADERS';
  const rows = {
    cases: tb(['Measure', 'Base case', 'Moderate scenario'], [['Leverage', '6.0x', '7.0x', extra]]),
    caseRows: tb(['Scenario', 'Decline', 'Anchor'], [['Base', '0', 'Control', extra]]),
    caseRowsNumeric: tb(['Scenario', 'EBITDA', 'Cover'], [['Base', '4,173', '3.60x', extra]]),
    ranked: tb(['Rank', 'Break', 'Decline at break', 'Base case'], [['1', 'Leverage watch', '23.47%', 'Not reached', extra]]),
    statement: tb(['Line', 'FY2024', 'FY2023'], [['Sales', '100', '90', extra]]),
    metric: tb(['Metric', 'FY2024', 'FY2023', 'Definition'], [['Cover', '3.60x', '4.1x', 'EBITDA / interest', extra]]),
    measure: tb(['Operating measure', 'FY2024', 'FY2023', 'Change', 'Creditor consequence'], [['Net sales', '100', '90', '+10', 'Growth', extra]]),
    change: tb(['Measure', 'Earlier', 'Current', 'Cause'], [['Leverage', '6.01x', '7.1x', 'Debt', extra]]),
  };
  const shapeOf = { cases: 'cases', caseRows: 'caseRows', caseRowsNumeric: 'caseRows', ranked: 'ranked', statement: 'statement', metric: 'metric', measure: 'measure', change: 'change' };
  for (const [name, block] of Object.entries(rows)) {
    const shape = Shapes.tableShape(block);
    assert.equal(shape, shapeOf[name], name);
    const html = C.render(shape, block, plainCtx());
    assert.ok(textOf(html).includes(extra), `${name}: the extra cell is drawn`);
  }
  const ctxTok = plainCtx({ tokens: ['SC1'] });
  assert.ok(!textOf(C.render('cases', tb(['Measure', 'Base case', 'Moderate scenario'], [['Leverage', '6.0x', '7.0x', 'As SC1 only']]), ctxTok)).includes('As SC1'), 'an extra cell goes through findingCell');
});

// ---- Task 6 fix round 1
const quietKey = r => `o:${r.line}`;
test('fix 1: the module-name bypass applies only to one part of the form "<words> (CP-x)"; a file name or calculation ID beside it is held back', () => {
  const names = ['report.pdf, Source readiness (CP-0)', 'calculation C05; Stress (CP-2A)', 'CP-0.jsonl; Gate (CP-4)'];
  const rows = names.map((name, i) => ({ line: i + 1, cells: [name, `State ${i}`, 'why'] }));
  const html = C.moduleStateTiles({ headers: ['Module', 'Status', 'Why'], rows }, { key: quietKey, evidenceHref: '#e' }), text = textOf(html);
  for (const bad of ['report.pdf', 'calculation C05', 'CP-0.jsonl', 'Source readiness', 'Stress', 'Gate']) assert.ok(!text.includes(bad), `${bad} is held back`);
  const ok = textOf(C.moduleStateTiles({ headers: ['Module', 'Status'], rows: [{ line: 1, cells: ['Source readiness (CP-0)', 'New'] }] }, { key: quietKey }));
  assert.ok(ok.includes('Source readiness (CP-0)'), 'a single module name is the handoff\'s own text');
});

test('fix 2: a title cell findingCell held back is not drawn in a trace label; the label is "Row <n>" by position, in every component that writes one', () => {
  const ctx = { key: quietKey, trace: (r, l) => C.traceRow(`o:${r.line}`, l), evidenceHref: '#e', tokens: ['EV-9'], caption: 'T' };
  const blk = (headers, rows) => ({ headers, rows: rows.map((cells, i) => ({ line: 40 + i, cells })) });
  const tables = {
    status: blk(['Gate item', 'Status'], [['Fine', 'Met'], ['Waiver EV-9', 'Met'], ['Per calculation C05', 'Met'], ['TDG_10-K.htm', 'Met']]),
    sided: blk(['Decision driver', 'Side it supports'], [['Fine', 'Bull'], ['Waiver EV-9', 'Bear'], ['Per calculation C05', 'Bear'], ['TDG_10-K.htm', 'Bull']]),
    moduleState: blk(['Module', 'Status'], [['Fine', 'New'], ['Waiver EV-9', 'Unchanged'], ['Per calculation C05', 'Gone'], ['TDG_10-K.htm', 'Other']]),
    qa: blk(['Question', 'Answer state'], [['Fine?', 'Answered'], ['Is EV-9 waived?', 'Answered'], ['Per calculation C05?', 'Answered'], ['TDG_10-K.htm', 'Answered']]),
    facts: blk(['Item', 'Fact'], [['Fine', 'Yes'], ['Waiver EV-9', 'Yes'], ['Per calculation C05', 'Yes'], ['TDG_10-K.htm', 'Yes']]),
    matrix: blk(['Event', 'Probability', 'Impact'], [['Fine', 'High', 'Low'], ['Waiver EV-9', 'High', 'Low'], ['Per calculation C05', 'High', 'Low'], ['TDG_10-K.htm', 'High', 'Low']]),
    watch: blk(['Indicator', 'Leading / Lagging'], [['Fine', 'Leading'], ['Waiver EV-9', 'Leading'], ['Per calculation C05', 'Leading'], ['TDG_10-K.htm', 'Leading']]),
    records: blk(['Zeta', 'Omega'], [['Fine', 'a'], ['Waiver EV-9', 'b'], ['Per calculation C05', 'c'], ['TDG_10-K.htm', 'd']]),
    change: blk(['Measure', 'Earlier', 'Current'], [['Fine', '1x', '2x'], ['Waiver EV-9', '1x', '2x'], ['Per calculation C05', '1x', '2x'], ['TDG_10-K.htm', '1x', '2x']]),
  };
  for (const [shape, block] of Object.entries(tables)) {
    const html = C.render(shape, block, ctx), attrs = (html.match(/(?:title|aria-label)="[^"]*"/g) || []);
    assert.deepEqual(attrs.filter(a => /EV-9|calculation C05|\.htm/.test(a)), [], `${shape}: a held-back cell is in an attribute`);
    for (const n of [2, 3, 4]) assert.ok(html.includes(`aria-label="Row ${n}: where it comes from"`), `${shape}: Row ${n}`);
    assert.ok(attrs.includes(`aria-label="${shape === 'qa' ? 'Fine?' : 'Fine'}: where it comes from"`), `${shape}: the first row is labelled with its title`);
  }
});

test('fix 3: a negated or cleared state is neutral, never the failure mark and never the success mark; the key\'s states keep their marks; keywords are whole words', () => {
  const tone = state => /class="state (\w+)"/.exec(C.statusChecklist({ headers: ['Item', 'Status'], rows: [{ line: 1, cells: ['x', state] }] }, { key: quietKey }))[1];
  for (const s of ['Not breached', 'No breach', 'Not failed', 'Breach cleared', 'Not blocked', 'Not rejected', 'No longer blocked', 'No', 'Not ready', 'Not passed', 'Frobnicated']) assert.equal(tone(s), 'info', s);
  for (const [s, want] of [['Committee-Ready', 'ok'], ['Remediation Needed', 'warn'], ['Not in source set; incorporated by reference only', 'warn'], ['Not found', 'warn'], ['Not assessable: no document', 'warn'], ['Partly (issuer view)', 'warn'], ['Answered', 'ok'], ['Unchanged', 'same'], ['New', 'new'], ['Gate fails', 'bad'], ['Blocked', 'bad'], ['Passed', 'ok']]) assert.equal(tone(s), want, s);
  for (const s of ['Breachfree', 'Unblocked', 'Failover']) assert.equal(tone(s), 'info', `${s} is no whole-word keyword`);
});

test('fix 4: only identical state texts collapse; a variant stays its own tile and its text is drawn', () => {
  const rows = [['Alpha', 'Unchanged', 'w1'], ['Beta', 'UNCHANGED', 'w2'], ['Gamma', 'Unchanged', 'w3'], ['Delta', '**Unchanged**', 'w4']].map((cells, i) => ({ line: i + 1, cells }));
  const html = C.moduleStateTiles({ headers: ['Module', 'Status', 'Why'], rows }, { key: quietKey });
  assert.equal(countOf(html, /ms-group/g), 1);
  assert.equal(countOf(html, /<article class="ms-tile">/g), 2);
  assert.ok(textOf(html).includes('UNCHANGED') && html.includes('<strong>Unchanged</strong>') && textOf(html).includes('w2') && textOf(html).includes('w4'));
});

test('fix 5: sided columns are a recognised opposing pair when both words are present, else the first two distinct words in written order; the rest are beneath', () => {
  const board = (words, header = 'Side it supports') => C.sidedBoard({ headers: ['Driver', header], rows: words.map((w, i) => ({ line: i + 1, cells: [`D${i}`, w] })) }, { key: quietKey });
  const cols = html => [...html.matchAll(/<div class="sd-line sd-s(\d)">/g)].map(m => m[1]).join('');
  const heads = html => [...html.matchAll(/<p class="sd-hs sd-s\d"><i[^>]*><\/i>([^<]*)<b class="sd-n">(\d+)/g)].map(m => `${m[1]}:${m[2]}`);
  let html = board(['Bull', 'Neutral', 'Neutral', 'Bear']);
  assert.deepEqual(heads(html), ['Bull:1', 'Bear:1']); assert.equal(cols(html), '0122');
  html = board(['Bear', 'Bear', 'Bull']);
  assert.deepEqual(heads(html), ['Bull:1', 'Bear:2'], 'left is the first of the pair as listed'); assert.equal(cols(html), '011');
  for (const [a, b] of [['Support', 'Contradict'], ['Supports', 'Contradicts'], ['For', 'Against'], ['Positive', 'Negative'], ['Upside', 'Downside']]) {
    html = board([b, 'Other', 'Other', a]);
    assert.deepEqual(heads(html), [`${a}:1`, `${b}:1`], `${a} / ${b}`); assert.equal(cols(html), '0122');
  }
  html = board(['Neutral', 'Bear', 'Bear', 'Other', 'Other', 'Other']);
  assert.deepEqual(heads(html), ['Neutral:1', 'Bear:2'], 'no pair: the first two distinct words in written order'); assert.equal(cols(html), '011222');
});

test('fix 6: the collapsed tile shows its count with the header as written; Evidence heads do not count notes as calculations', () => {
  const html = C.moduleStateTiles({ headers: ['Analysis', 'Status'], rows: [['A', 'New'], ['B', 'New'], ['C', 'New']].map((cells, i) => ({ line: i + 1, cells })) }, { key: quietKey });
  assert.ok(html.includes('<b class="ms-n">3</b> · <span class="ms-nl">Analysis</span>') && !/analysiss/i.test(html));
});

test('fix 8: an axis whose labels are all Low/Medium/High (or Moderate) is ordered low to high, rows High to Low as the mock draws likelihood; any other set keeps its written order', () => {
  const rows = [['A', 'Low', 'High'], ['B', 'High', 'Low'], ['C', 'Medium', 'Moderate']].map((cells, i) => ({ line: i + 1, cells }));
  const html = C.riskMatrix({ headers: ['Event', 'Probability', 'Impact'], rows }, { key: quietKey });
  assert.deepEqual([...html.matchAll(/<th scope="row">([^<]*)<\/th>/g)].map(m => m[1]), ['High', 'Medium', 'Low']);
  assert.deepEqual([...html.matchAll(/<th scope="col">([^<]*)<\/th>/g)].map(m => m[1]), ['Low', 'Moderate', 'High'], 'labels drawn as written');
  const mixed = C.riskMatrix({ headers: ['Event', 'Probability', 'Impact'], rows: [['A', 'Likely', 'High'], ['B', 'Rare', 'Severe']].map((cells, i) => ({ line: i + 1, cells })) }, { key: quietKey });
  assert.deepEqual([...mixed.matchAll(/<th scope="row">([^<]*)<\/th>/g)].map(m => m[1]), ['Likely', 'Rare']);
  assert.deepEqual([...mixed.matchAll(/<th scope="col">([^<]*)<\/th>/g)].map(m => m[1]), ['High', 'Severe'], 'one label outside the set: written order');
});

test('fix 9: beforeprint twice without afterprint does not overwrite the remembered state', () => {
  const fold = open => ({ open, dataset: {} }), folds = [fold(false)], root = { querySelectorAll: () => folds };
  C.foldsForPrint(root, true); C.foldsForPrint(root, true); C.foldsForPrint(root, false);
  assert.equal(folds[0].open, false);
});

test('fix 10: a cell beyond the header count is drawn unlabelled through findingCell in every component and in recordCards; one holding an identifier is the Evidence link', () => {
  const ctx = { key: quietKey, evidenceHref: '#e', tokens: ['EV-9'], caption: 'T' };
  const tables = {
    status: [['Gate item', 'Status'], ['Item', 'Met']], sided: [['Driver', 'Side it supports'], ['Item', 'Bull']], moduleState: [['Module', 'Status'], ['Item', 'New']],
    qa: [['Question', 'Answer state'], ['Item?', 'Answered']], facts: [['Item', 'Fact'], ['Item', 'Yes']], matrix: [['Event', 'Probability', 'Impact'], ['Item', 'High', 'Low']],
    watch: [['Indicator', 'Leading / Lagging'], ['Item', 'Leading']], records: [['Zeta', 'Omega'], ['Item', 'x']],
  };
  for (const [shape, [headers, cells]] of Object.entries(tables)) {
    const html = C.render(shape, { headers, rows: [{ line: 1, cells: [...cells, 'Extra beyond', 'Also EV-9 here'] }] }, ctx), text = textOf(html);
    assert.ok(text.includes('Extra beyond'), `${shape}: the extra cell is drawn`);
    assert.ok(!text.includes('Also EV-9 here') && html.includes('class="in-ev"'), `${shape}: an identifier in it is the link`);
  }
});

// ---- Fix round 2
test('rankedLadder: levels at the top of the float range terminate and fall back to record cards', () => {
  for (const level of ['175' + '0'.repeat(306), '17' + '0'.repeat(307)]) {
    const run = inChild(`const b={headers:['Rank','Break','Level'],rows:[{line:1,cells:['1','A',${JSON.stringify(level)}]}]};const h=C.rankedLadder(b,{key:r=>'k'});process.stdout.write(h.includes('class="ladder')?'ladder':'cards');`);
    assert.ok(run.returned, `did not return for ${level.slice(0, 6)}...: ${run.err.slice(0, 80)}`);
    assert.equal(run.out, 'cards');
  }
  const mid = inChild(`const b={headers:['Rank','Break','Level'],rows:[{line:1,cells:['1','A','1'+'0'.repeat(300)]}]};process.stdout.write(C.rankedLadder(b,{key:r=>'k'}).includes('class="ladder')?'ladder':'cards');`);
  assert.equal(mid.out, 'ladder', '1e300 is still a ladder');
});

test('casePairing: the source is the one caseRows table whose FIRST column is an id column, with unique ids', () => {
  const evRows = tb(['Scenario', 'Narrative', 'Evidence ID'], [['Base', 'Steady', 'EV-01'], ['Moderate', 'Half', 'EV-02'], ['Severe', 'Full', 'EV-03']]);
  assert.equal(Shapes.casePairing([casesT, evRows]), null, 'an id column that is not column 0 is not a pairing source');
  assert.deepEqual(Shapes.casePairing([casesT, evRows, defsT]).ids, ['s00', 'SC1', 'SC2'], 'the real Scenario ID table still pairs, and EV ids do not');
  const dup = tb(['Scenario ID', 'Decline', 'Anchor'], [['SC1', '0', 'a'], ['SC1', '0.15', 'b'], ['SC2', '0.31', 'c']]);
  assert.equal(Shapes.casePairing([casesT, dup]), null, 'duplicate ids: no pairing');
  const second = tb(['Scenario ID', 'Decline', 'Anchor'], [['a1', '0', 'a'], ['a2', '0.15', 'b'], ['a3', '0.31', 'c']]);
  assert.equal(Shapes.casePairing([casesT, defsT, second]), null, 'two id-first tables with the right row count are ambiguous');
  const ctx = plainCtx({ tokens: ['EV-01', 'EV-02', 'EV-03', 's00', 'SC1', 'SC2'], pairing: Shapes.casePairing([casesT, evRows, defsT]) });
  const html = C.caseRowsBlock(tb(['Scenario', 'Note', 'Trigger'], [['EV-02', 'The dividend', 'x']]), ctx);
  assert.ok(!html.includes('Moderate scenario'), 'an EV id names no case');
});

test('a column 0 cell wrapped in emphasis or code marks names its case by id', () => {
  const pairing = Shapes.casePairing([casesT, defsT]);
  const ctx = plainCtx({ tokens: ['s00', 'SC1', 'SC2'], pairing });
  for (const cell of ['**SC1**', '`SC1`', ' SC1 ', '_SC1_']) {
    const html = C.caseRowsBlock(tb(['Scenario', 'Narrative', 'Trigger'], [[cell, 'Half share lost', 'Slowdown']]), ctx);
    assert.ok(html.includes('<h4 class="cr-title">Moderate scenario</h4>') && !html.includes('cr-badge'), cell);
  }
});

test('period labels of every form are not id tokens; ratings and filing names in an id column still are', () => {
  const vals = ['1H24', 'H1 2024', '9M24', 'LTM Q3 2024', 'LTM', 'FY2024-25', 'Q3 FY24', 'FY24E', 'H1 24', 'B2', 'Ba3', '10-K', 'SC1'];
  assert.deepEqual(Shapes.idTokens([{ blocks: [{ type: 'table', ...tb(['Case ID', 'D'], vals.map(v => [v, 'x'])) }] }]), ['B2', 'Ba3', '10-K', 'SC1']);
});

test('a calculation reference-only cell uses the one shared pattern: "Calculation FY24" alone is drawn', () => {
  assert.deepEqual(C.findingCell('Calculation FY24', {}), { html: 'Calculation FY24' });
  assert.deepEqual(C.findingCell('Calculations C21, C22', {}), { omitted: true });
  assert.deepEqual(C.findingCell('Calculation D17', {}), { omitted: true });
});

// ---- Task 6 fix round 2
test('fix A: a moduleState tile draws exactly its words, no stray character (compared whole, tags stripped)', () => {
  const html = C.moduleStateTiles({ headers: ['Module', 'Status'], rows: [{ line: 1, cells: ['Alpha', 'Ready'] }, { line: 2, cells: ['Beta', 'Pending'] }] }, { key: quietKey });
  assert.equal(textOf(html).replace(/\s+/g, ' ').trim(), 'AlphaReadyBetaPending');
  const grouped = C.moduleStateTiles({ headers: ['Module', 'Status', 'Why'], rows: [{ line: 1, cells: ['Alpha', 'New', 'w1'] }, { line: 2, cells: ['Beta', 'New', 'w2'] }] }, { key: quietKey });
  assert.equal(textOf(grouped).replace(/\s+/g, ' ').trim(), 'New2 · ModuleAlphaWhyw1BetaWhyw2');
});

test('fix B: the module-name bypass refuses a name holding an identifier of the module, a bare calculation-ID-shaped word or a file name', () => {
  const ctx = { key: quietKey, evidenceHref: '#e', tokens: ['EV-9', 's00'] };
  const draw = name => textOf(C.moduleStateTiles({ headers: ['Module', 'Status'], rows: [{ line: 1, cells: [name, 'Ready'] }] }, ctx));
  for (const [name, held] of [['EV-9 review (CP-4)', 'EV-9'], ['s00 (CP-4)', 's00'], ['C05 (CP-4)', 'C05'], ['report.pdf (CP-4)', 'report.pdf']]) assert.ok(!draw(name).includes(held), name);
  assert.ok(C.moduleStateTiles({ headers: ['Module', 'Status'], rows: [{ line: 1, cells: ['EV-9 review (CP-4)', 'Ready'] }] }, ctx).includes('class="basis-link trace-row"'), 'a held-back name (findingCell omits it) leaves the row reachable by its trace control');
  assert.ok(draw('Gate review (CP-4)').includes('Gate review (CP-4)'), 'a plain module name is drawn as written');
  assert.ok(draw('EV-90 review (CP-4)').includes('EV-90 review (CP-4)'), 'whole words only');
});

test('fix C: support and supports, contradict and contradicts, are one pair; the heading is the word as first written', () => {
  const heads = words => [...C.sidedBoard({ headers: ['Driver', 'Side'], rows: words.map((s, i) => ({ line: i + 1, cells: [`D${i}`, s] })) }, { key: quietKey }).matchAll(/<p class="sd-hs sd-s\d">.*?<\/i>(.*?)<b/g)].map(m => m[1]).join('|');
  assert.equal(heads(['Neutral', 'Neutral', 'Supports', 'Contradict']), 'Supports|Contradict');
  assert.equal(heads(['Contradicts', 'Support', 'Neutral', 'Supports']), 'Support|Contradicts', 'left is the pair\'s first word, as first written');
});

// ---- Overview components (library redesign, task 8). Expected text is written by hand in each test.
const STRIP_BLOCK = {
  headers: ['Metric', 'FY2024', 'FY2023', 'Source'],
  rows: [
    { line: 10, cells: ['Net leverage', '6.01x', '6.40x', 'Annual report, page 4'] },
    { line: 11, cells: ['Interest cover', '2.1x', '2.5x', 'Annual report, page 5'] },
    { line: 12, cells: ['Free cash flow', 'USD 1,100 million', 'USD 900 million', 'Annual report, page 6'] },
    { line: 13, cells: ['EBITDA margin', '40.0%', '39.0%', 'Annual report, page 7'] },
    { line: 14, cells: ['Revenue growth', '9.0%', '8.0%', 'Annual report, page 8'] },
    { line: 15, cells: ['Dividend cover', '1.2x', '1.1x', 'Annual report, page 9'] },
  ],
};
const stripCtx = { key: r => `k:${r.line}` }, stripLink = { href: '#CP-1/x', title: 'Financial foundation' };
const stripLabels = html => [...html.matchAll(/<a class="strip-k"[^>]*>(.*?)<\/a>/g)].map(m => m[1]);

test('metricStrip: only rows whose label is a whole phrase of the text, case aside, in table order, at most four; none matching draws nothing', () => {
  const text = 'Net leverage is 6.01x. INTEREST COVER holds, and the dividend cover and free cash flow and ebitda margin are fine; revenue growth too.';
  assert.deepEqual(stripLabels(C.metricStrip(STRIP_BLOCK, stripCtx, text, stripLink)), ['Net leverage', 'Interest cover', 'Free cash flow', 'EBITDA margin'], 'the fifth and sixth matches are dropped, the order is the table\'s');
  assert.deepEqual(stripLabels(C.metricStrip(STRIP_BLOCK, stripCtx, 'Cover is thin; the leverage is high; margins and growth are fine.', stripLink)), [], 'a part of a label is not the label');
  assert.equal(C.metricStrip(STRIP_BLOCK, stripCtx, 'Nothing the table names appears here.', stripLink), '');
  assert.equal(C.metricStrip(STRIP_BLOCK, stripCtx, 'Prenet leverage and interest covers.', stripLink), '', 'a whole phrase: not inside another word');
  assert.deepEqual(stripLabels(C.metricStrip(STRIP_BLOCK, stripCtx, 'Dividend cover is 1.2x.', stripLink)), ['Dividend cover'], 'one match is one cell, not the first four rows');
});

test('metricStrip: each cell is the label as a link to its module, the latest period as written, the earlier period beneath, one trace icon, and no Source text', () => {
  const html = C.metricStrip(STRIP_BLOCK, stripCtx, 'Net leverage and free cash flow.', stripLink);
  assert.ok(html.includes('<a class="strip-k" href="#CP-1/x" title="Open Financial foundation">Net leverage</a>'), html);
  assert.ok(html.includes('<p class="strip-v">6.01x</p>') && html.includes('<p class="strip-b">FY2023 6.40x</p>'), html);
  assert.ok(html.includes('<p class="strip-v">USD 1,100 million</p>') && html.includes('FY2023 USD 900 million'));
  assert.equal((html.match(/data-evidence="k:1[02]"/g) || []).length, 2);
  assert.ok(!html.includes('Annual report') && !html.includes('Source'), 'the Source column is not drawn');
  assert.ok(html.startsWith('<div class="strip" role="group" aria-label="Figures the bottom line cites, FY2024">'));
});

test('metricStrip: cells with markup characters are escaped; a label held back for an identifier draws no cell', () => {
  const block = { headers: ['Metric', 'FY2024'], rows: [{ line: 1, cells: ['<b>Cover</b> & "more"', '<i>2x</i> & "y"'] }, { line: 2, cells: ['EV-9', '3x'] }] };
  const html = C.metricStrip(block, { key: r => `k:${r.line}`, tokens: ['EV-9'] }, 'The <b>Cover</b> & "more" and EV-9 are cited.', stripLink);
  assert.ok(!html.includes('<b>') && !html.includes('<i>'), html);
  assert.ok(html.includes('&lt;b&gt;Cover&lt;/b&gt;') && html.includes('&amp;'), html);
  assert.equal(stripLabels(html).length, 1, 'the identifier row has no cell');
});

const TILE_TEXTS = [T('Creditors are covered, but only just. Cover is thin.\nBasis: A.pdf, page 4', 5), T('A second paragraph.\nBasis: B.pdf', 7)];
test('moduleTiles: one details per module in one grid, all sharing one name so only one is open; the group is an eyebrow inside the tile, the state word and its icon on their own line under the title, then the first sentence; open, the whole Bottom line and the link', () => {
  const html = C.moduleTiles([{ title: 'Business and evidence', items: [
    { title: 'Source readiness', href: '#CP-0/x', state: 'Restricted', blocked: true, texts: TILE_TEXTS, trace: mark },
    { title: 'Financial foundation', href: '#CP-1/x', state: null, texts: [T('One sentence only.', 9)], trace: mark },
  ] }, { title: 'Empty group', items: [] }, { title: 'Outlook', items: [{ title: 'Downside', href: '#CP-2/x', state: null, texts: [T('Down.', 1)] }] }]);
  assert.equal((html.match(/<details class="mt" name="overview-modules">/g) || []).length, 3);
  assert.equal((html.match(/<div class="mt-grid">/g) || []).length, 1, 'one continuous grid, no heading between rows');
  assert.ok(!html.includes('Empty group') && !/<h[1-6]/.test(html));
  assert.deepEqual([...html.matchAll(/<span class="eyebrow mt-group">([^<]*)<\/span>/g)].map(m => m[1]), ['Business and evidence', 'Business and evidence', 'Outlook']);
  const first = html.slice(0, html.indexOf('Financial foundation'));
  assert.ok(first.includes('</span></span><span class="mt-state"><span class="badge badge-gray">Not assessable</span><span class="state warn">'), 'the marks follow the title row, in their own line: the rail\'s Not assessable mark, then the declared state');
  assert.ok(first.includes('<span class="state-w">Restricted</span>') && first.includes('<svg'), 'the word is always shown with its icon');
  assert.ok(first.indexOf('mt-state') < first.indexOf('mt-lead'));
  assert.ok(first.includes('<span class="mt-lead">Creditors are covered, but only just.</span>'), first);
  assert.ok(first.includes('<p class="mt-p">Creditors are covered, but only just. Cover is thin.') && first.includes('<p class="mt-p">A second paragraph.'), 'open, the whole Bottom line');
  assert.equal((first.match(/class="basis-link"/g) || []).length, 2);
  assert.ok(first.includes('<a class="mt-open" href="#CP-0/x" aria-label="Open module: Source readiness">Open module'), 'the accessible name contains the visible text');
  assert.ok(!html.slice(html.indexOf('Financial foundation')).includes('mt-state'), 'no mark and no state: no marks line');
  noMarkdown(html);
});

test('moduleTiles: a first sentence that ends inside bold closes the mark at the cut; no raw ** reaches the tile', () => {
  const html = C.moduleTiles([{ title: 'G', items: [{ title: 'M', href: '#M', texts: [T('Leverage is **5.5x. The covenant** is loose.', 1)] }] }]);
  assert.ok(html.includes('<span class="mt-lead">Leverage is <strong>5.5x.</strong></span>') && !html.includes('**'), html);
});

test('firstSentence marks: a stretch cut inside bold has its open mark closed at the cut and reopened after it, adding nothing else', () => {
  const html = C.verdictPanel([T('Leverage is **5.5x. The covenant** is loose.', 1)], mark);
  assert.ok(html.includes('<p class="verdict-lead">Leverage is <strong>5.5x.</strong></p>') && html.includes('<p class="verdict-body"><strong>The covenant</strong> is loose.</p>'), html);
  const feed = C.findingsFeed([T('- **Leverage is high. It rises.** The rest follows.', 1)], mark);
  assert.ok(feed.includes('<div class="feed-title">Leverage is high. It rises.</div>') && feed.includes('<p class="feed-body">The rest follows.</p>') && !feed.includes('**'), 'a bold lead is the title');
  const plain = C.findingsFeed([T('- Leverage is **5.5x. The covenant** is loose.', 1)], mark);
  assert.ok(plain.includes('<div class="feed-title">Leverage is <strong>5.5x.</strong></div>') && plain.includes('<p class="feed-body"><strong>The covenant</strong> is loose.</p>'), plain);
  assert.ok(C.moduleTiles([{ title: 'G', items: [{ title: 'M', href: '#M', texts: [T('**Hold the position.** Leverage is high.', 1)] }] }]).includes('<span class="mt-lead"><strong>Hold the position.</strong></span>'), 'a closing ** after the full stop belongs to the sentence');
});

test('hasDatedEvent: a date cell that states a date counts; an absence statement or an empty cell does not', () => {
  const block = rows => ({ headers: ['Event date', 'Event'], rows: rows.map((d, i) => ({ line: i + 1, cells: [d, 'x'] })) });
  assert.equal(C.hasDatedEvent(block(['Not supplied: no date', 'None identified in the file', ''])), false);
  assert.equal(C.hasDatedEvent(block(['Not supplied: no date', '2025-07-11'])), true);
});

test('metricStrip: a label found only inside a longer cited label is dropped; one that also stands alone elsewhere stays', () => {
  const block = { headers: ['Metric', 'FY2024'], rows: [['EBITDA', '1'], ['EBITDA margin', '2'], ['Leverage', '3'], ['Net leverage', '4']].map((cells, i) => ({ line: i + 1, cells })) };
  const draw = text => stripLabels(C.metricStrip(block, stripCtx, text, stripLink));
  assert.deepEqual(draw('Net leverage of 6.01x and an EBITDA margin of 30.0% decide it.'), ['EBITDA margin', 'Net leverage']);
  assert.deepEqual(draw('Net leverage is 6.01x. Leverage on a gross basis is 7.2x.'), ['Leverage', 'Net leverage'], 'Leverage is also cited on its own');
  assert.deepEqual(draw('EBITDA is flat; EBITDA margin is 30%.'), ['EBITDA', 'EBITDA margin']);
});

test('moduleTiles: no Bottom line says so; saved outputs with none chosen is a plain tile with the way to choose; text is escaped', () => {
  const html = C.moduleTiles([{ title: 'G', items: [
    { title: '<b>Odd</b> & "name"', href: '#a', state: '<i>x</i>', texts: [] },
    { title: 'Chosen later', href: '#b', choose: { count: 2, href: '#CP-0?c=run-a' } },
  ] }]);
  assert.ok(html.includes('<span class="mt-lead">No bottom line in this handoff.</span>'));
  assert.ok(html.includes('2 saved outputs, none chosen. <a class="in-ev" href="#CP-0?c=run-a">Choose one</a>') && !html.slice(html.indexOf('Chosen later')).includes('<details'));
  assert.ok(!html.includes('<b>') && !html.includes('<i>x') && html.includes('&lt;b&gt;Odd&lt;/b&gt; &amp; &quot;name&quot;'), html);
  assert.equal(C.moduleTiles([]), '');
});

test('moduleTiles: print opens every tile and puts them back', () => {
  const fold = { dataset: {}, open: false };
  const root = { querySelectorAll: selector => (selector.split(',').map(part => part.trim()).includes('.mt') ? [fold] : []) };
  C.foldsForPrint(root, true);
  assert.equal(fold.open, true);
  C.foldsForPrint(root, false);
  assert.equal(fold.open, false);
});

test('attribution: a link to the module the block comes from, escaped', () => {
  assert.equal(C.attribution({ title: 'Committee <decision>', href: '#CP-6/x?a=1&b=2' }).replace(/<svg.*<\/svg>/, ''), '<p class="from"><a href="#CP-6/x?a=1&amp;b=2">From Committee &lt;decision&gt;</a></p>');
});

test('verdictPanel and callout take the heading level the page needs, h4 when none is given', () => {
  assert.ok(C.verdictPanel([T('A.', 1)], mark, undefined, 'h3').includes('<h3 class="eyebrow">Bottom line</h3>'));
  assert.ok(C.verdictPanel([T('A.', 1)], mark).includes('<h4 class="eyebrow">Bottom line</h4>'));
  const html = C.callout('What would change the view', [T('B.', 2)], mark, undefined, 'h2');
  assert.ok(html.includes('What would change the view</h2>') && !html.includes('</h4>'));
});

test('metricStrip: a latest cell longer than a figure is text, set at body size (the wide class), not as a headline figure', () => {
  const block = { headers: ['Metric', 'FY2024'], rows: [{ line: 1, cells: ['Revolver test', '7.50x net (8.00x after material acquisition) if usage above 40%'] }, { line: 2, cells: ['Cover', '2.1x'] }] };
  const html = C.metricStrip(block, { key: r => `k:${r.line}` }, 'Revolver test and cover.', stripLink);
  assert.ok(html.includes('<p class="strip-v wide">7.50x net') && html.includes('<p class="strip-v">2.1x</p>'), html);
});

test('findingCell strict (the Forecast page): a file name, hash or scenario id inside text is held back, a module code is not; the default reading is unchanged', () => {
  const text = 'Annual; K_10.htm.jsonl, pages 71';
  assert.ok(C.findingCell(text, {}).html !== undefined, 'the module page reading is unchanged');
  assert.deepEqual(C.findingCell(text, { strict: true }), { omitted: true, inEvidence: true });
  assert.deepEqual(C.findingCell('Downside is SC1: a rate rise', { strict: true }), { omitted: true, inEvidence: true });
  assert.ok(C.findingCell('CP-1 prints no line', { strict: true }).html !== undefined, 'the page names a module code');
  assert.equal(C.findingCell('Cash rose 5.55x on 2.09 turns', { strict: true }).html, 'Cash rose 5.55x on 2.09 turns');
});

test('gapState: the stated reason of the build stands in only when the table states none', () => {
  const block = { headers: ['Period', 'Limit'], rows: [{ line: 1, cells: ['FY24', 'Not supplied: nothing read'] }] };
  assert.ok(C.gapState(block, {}, 'The build says').includes('Not supplied: nothing read') && !C.gapState(block, {}, 'The build says').includes('The build says'));
  const none = { headers: ['Period', 'Limit'], rows: [{ line: 1, cells: ['FY24', '1.2'] }] };
  assert.ok(C.gapState(none, {}, 'The build says').includes('The build says'));
});

// ---- Library home and report history (library redesign, Task 11): the module dot strip, the run mark, the run steps, the shared toggle and timeline extensions.
const tagText = html => html.replace(/<[^>]+>/g, '');
const dotLabelsOf = html => [...html.matchAll(/<span role="img" data-tip="([^"]*)" aria-label="([^"]*)"/g)].map(m => [m[1], m[2]]);

test('moduleDots (C21): one dot per module in the order given, each an image named by its title (and its state word) with the tooltip attributes; state is icon and token, never colour alone', () => {
  const html = C.moduleDots([{ title: 'Source readiness', state: 'Ready' }, { title: 'Downside', state: null, blocked: true }, { title: 'Committee decision', state: 'Restricted' }, { title: 'Liquidity', state: null }, { title: 'Pricing', choose: true }, { title: 'Review', state: 'Failed' }]);
  assert.deepEqual(dotLabelsOf(html), [['Source readiness: Ready', 'Source readiness: Ready'], ['Downside: Not assessable', 'Downside: Not assessable'], ['Committee decision: Restricted', 'Committee decision: Restricted'], ['Liquidity', 'Liquidity'], ['Pricing: saved outputs, none chosen', 'Pricing: saved outputs, none chosen'], ['Review: Failed', 'Review: Failed']]);
  assert.deepEqual([...html.matchAll(/<li class="mdot (\w+)">/g)].map(m => m[1]), ['ok', 'warn', 'warn', 'none', 'none', 'bad']);
  assert.ok(html.startsWith('<ul class="mdots" aria-label="Modules in this run: 6">'));
  const dots = html.split('<li ').slice(1);
  assert.ok(dots.filter((_, n) => [0, 1, 2, 5].includes(n)).every(dot => dot.includes('<svg class="i"')), 'a dot with a state carries its icon');
  assert.ok(dots.filter((_, n) => [3, 4].includes(n)).every(dot => !dot.includes('<svg')), 'a module with no usable state is a hollow dot');
  assert.equal(tagText(html), '', 'the module names are labels, not text');
  assert.equal(C.moduleDots([]), '');
});

test('moduleDots: a state the findings rule holds back (an identifier) is not a state word; text is escaped', () => {
  const html = C.moduleDots([{ title: 'A <b>&"x"', state: 'CP-1' }, { title: 'B', state: 'Ready <i>' }]);
  assert.ok(html.includes('data-tip="A &lt;b&gt;&amp;&quot;x&quot;"') && html.includes('data-tip="B: Ready &lt;i&gt;"'), html);
  assert.ok(!html.includes('<b>') && !html.includes('<i>'));
});

test('stateOf and stateBadge are exported for the library pages: a word with its icon, an unusable state has no word', () => {
  assert.deepEqual(C.stateOf('Restricted'), { tone: 'warn', icon: 'triangle-alert' });
  assert.ok(C.stateBadge('Restricted', {}).startsWith('<span class="state warn"><svg class="i"') && C.stateBadge('Restricted', {}).includes('<span class="state-w">Restricted</span>'));
});

test('firstSentenceOf: the first sentence of the first paragraph, figures as plain text; nothing for no text', () => {
  assert.equal(C.firstSentenceOf([T('Hold the position. Leverage is 5.5x.\nBasis: file.pdf, page 1', 3)], null), 'Hold the position.');
  assert.equal(C.firstSentenceOf([T('**Hold.** Next.', 3)], null), '<strong>Hold.</strong>');
  assert.equal(C.firstSentenceOf([], null), '');
  assert.equal(C.firstSentenceOf(undefined, null), '');
});

test('runMark (C31): the status as its icon and word; running shows the lattice loader and may carry a note; an unknown status draws nothing', () => {
  const running = C.runMark('running');
  assert.ok(running.startsWith('<span class="state new rmark running"><span class="lat" aria-hidden="true">') && (running.match(/<i><\/i>/g) || []).length === 9 && running.endsWith('<span class="state-w">Running</span></span>'));
  assert.ok(C.runMark('running', 'stalled <b>').includes('<span class="state-w">Running · stalled &lt;b&gt;</span>'));
  assert.deepEqual(['queued', 'done', 'failed'].map(status => tagText(C.runMark(status))), ['Waiting', 'Done', 'Failed']);
  assert.ok(['queued', 'done', 'failed'].every(status => C.runMark(status).includes('<svg class="i"')), 'every status but running is an icon and a word');
  assert.equal(C.runMark('finished'), '');
});

test('runSteps (C13): one segment per module in order, the running module and done of total in words; a state it does not know waits; text is escaped', () => {
  const html = C.runSteps([{ title: 'Source readiness', state: 'done' }, { title: 'Financial <foundation>', state: 'running' }, { title: 'Downside', state: 'waiting' }, { title: 'Pricing', state: 'odd' }]);
  assert.deepEqual([...html.matchAll(/<li class="step (\w+)"/g)].map(m => m[1]), ['done', 'running', 'waiting', 'waiting']);
  assert.ok(html.includes('<ol class="steps" aria-label="Modules, 1 of 4 done">') && html.includes('data-tip="Financial &lt;foundation&gt;: running"'));
  assert.ok(html.includes('<span class="steps-k">Running</span> Financial &lt;foundation&gt;') && html.includes('<span class="steps-n">1 of 4 done</span>'));
  assert.ok(!C.runSteps([{ title: 'A', state: 'done' }]).includes('steps-now'), 'nothing running, no running line');
  assert.equal(C.runSteps([]), '');
});

test('viewToggle takes the option on view; the default is the first', () => {
  const two = [['cards', 'Cards'], ['list', 'List']];
  assert.ok(C.viewToggle('Issuers', two).includes('data-i="0"') && C.viewToggle('Issuers', two).includes('data-view-pick="cards" aria-pressed="true"'));
  const list = C.viewToggle('Issuers', two, 'list');
  assert.ok(list.includes('data-i="1"') && list.includes('data-view-pick="list" aria-pressed="true"') && list.includes('data-view-pick="cards" aria-pressed="false"'));
});

test('datedTimeline: a page adds its markup under an entry, marks the current one and names the count; without them the entry is unchanged', () => {
  const block = { headers: ['Date', 'Event'], rows: [{ cells: ['31 December 2025', 'Credit snapshot'], line: 1 }, { cells: ['31 March 2025', 'Credit snapshot'], line: 2 }] };
  const plain = C.datedTimeline(block, { stacked: true });
  assert.ok(plain.includes('<span data-count>2</span> events') && !plain.includes('aria-current'));
  const html = C.datedTimeline(block, { stacked: true, unit: ['run', 'runs'], current: (row, n) => n === 1, slot: (row, n) => `<p class="slot">${n}:${row.cells[0]}</p>` });
  assert.ok(html.includes('<span data-count>2</span> runs') && html.includes('<p class="slot">0:31 December 2025</p>') && html.includes('<p class="slot">1:31 March 2025</p>'));
  assert.deepEqual([...html.matchAll(/<li class="tl-i"( aria-current="true")?>/g)].map(m => Boolean(m[1])), [false, true]);
  assert.ok(html.includes('<ol class="tl tl-v">'));
  assert.equal(C.datedTimeline({ headers: ['Date', 'Event'], rows: [{ cells: ['31 March 2025', 'Credit snapshot'], line: 1 }] }, { stacked: true, unit: ['run', 'runs'] }).includes('<span data-count>1</span> run<'), true, 'one entry, singular');
});

test('strict file names (N1): any issuer document extension, chained too, is held; U.S.GAAP and 10-K.Item are not file names', () => {
  for (const name of ['lender-notes.docx', 'q3_deck.PPTX', 'filing.xml', 'annual-report.xhtml', 'a.tar.zip', 'x.json.md', 'sheet.xlsm', 'rows.tsv', 'memo.doc']) assert.deepEqual(C.findingCell(`Schedule; ${name}, page 4`, { strict: true }), { omitted: true, inEvidence: true }, name);
  for (const text of ['Under U.S.GAAP rules', '10-K.Item 7 states it', 'Sep. 2024 quarter']) assert.ok(C.findingCell(text, { strict: true }).html !== undefined, text);
});

test('strict id words (L3): a bare id-shaped word is held only when it is an id value of the run (ctx.tokens); calculation ids and module-code ids stay held always', () => {
  const words = ['G20 economies', 'P50 production case', 'EU27 sales', 'V03 case'];
  for (const text of words) assert.ok(C.findingCell(text, { strict: true }).html !== undefined, `${text} drawn without a token`);
  const tokens = ['V03'];
  assert.deepEqual(C.findingCell('V03 case', { strict: true, tokens }), { omitted: true, inEvidence: true });
  assert.ok(C.findingCell('EU27 sales', { strict: true, tokens }).html !== undefined, 'another word is still drawn');
  assert.deepEqual(C.findingCell('calculation C05 shows it', { strict: true }), { omitted: true, inEvidence: true });
  assert.deepEqual(C.findingCell('CP-1 C48 states it', { strict: true }), { omitted: true, inEvidence: true });
});

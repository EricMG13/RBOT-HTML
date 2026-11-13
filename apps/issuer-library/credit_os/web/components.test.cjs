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
  for (const text of ['calculation D17', 'Calculations C21, C22', 'calculation c05', 'TDG_2024-09-30_10-K_0001260221-24-000083_tdg-20240930.htm.jsonl, page 121', 'Financial data foundation (CP-1)',
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

test('caseRows with numeric columns: a case-by-measure panel, numbers right-aligned, the cell text verbatim, titled by the paired name', () => {
  const t = keyTables('CP-2A', 'caseRows')[1], ctx = pageCtx('CP-2A'), html = C.caseRowsBlock(keyBlock(t), ctx);
  assert.ok(html.includes('class="dtbl cr-panel"') && !html.includes('cr-card'));
  for (const name of ['Base FY2024 (control)', 'Moderate scenario', 'Severe scenario']) assert.ok(html.includes(`<th scope="row">${name}`), name);
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

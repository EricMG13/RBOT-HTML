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

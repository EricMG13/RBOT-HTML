'use strict';
// Library redesign, Task 7: the dated timeline (C15), the pathway (C14) and the empty state (C32), through Components.render.
// Expected values are written from the answer key (fixtures/shape-key.json) and from small tables written here; none is read back from the component.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const C = require('./components.js');
const S = require('./shapes.js');

const KEY = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'fixtures', 'shape-key.json'), 'utf8'));
const decode = t => t.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const textOf = html => decode(html.replace(/<[^>]*>/g, ''));
const blk = (headers, rows, line = 10) => ({type: 'table', line, headers, rows: rows.map((cells, i) => ({line: line + 2 + i, cells}))});
const ctx = (over = {}) => ({key: r => `o:${r.line}`, evidenceHref: '#W-Evidence/registers', caption: 'T', tokens: [], id: 'o', ...over});
const count = (html, re) => (html.match(re) || []).length;
const tablesOf = shape => KEY.tables.filter(t => t.shape === shape);
const asBlock = t => blk(t.headers, t.rows);

const DATED = ['Event date', 'Date precision', 'Published', 'Event', 'Status', 'Source', 'Credit relevance'];
const ev = (date, desc = 'Something happens', extra = {}) => [date, extra.precision ?? 'day', '—', desc, extra.status ?? 'Scheduled — as stated', 'K_10-K.htm.jsonl, page 3', extra.rel ?? 'Why it matters'];
const EDGE = ['From', 'Relationship', 'Edge type', 'To', 'Evidence'];
const eg = (from, rel, type, to, evidence = 'Annual filing page 9') => [from, rel, type, to, evidence];

// ---- the two required tests ----
test('a dated table with one "Not supplied: ..." row draws the empty state with the stated reason, not a timeline', () => {
  const block = blk(DATED, [Array(6).fill('Not supplied: not assessable, no executed governing document available').concat(['Not supplied: no legal event is settled here'])]);
  const html = C.render(S.tableShape(block), block, ctx());
  assert.equal(S.tableShape(block), 'dated');
  assert.ok(html.includes('class="empty-state"') && html.includes('role="status"'));
  assert.ok(textOf(html).includes('Not established for this run'));
  assert.ok(textOf(html).includes('Not supplied: not assessable, no executed governing document available'), 'the reason, verbatim');
  assert.equal(count(textOf(html), /not assessable, no executed governing document available/g), 1, 'a reason stated six times is drawn once');
  assert.ok(!html.includes('class="tl ') && !html.includes('tl-i') && !html.includes('<ol'));
  assert.ok(html.includes('class="ghost" aria-hidden="true"'), 'ghost bars are decoration');
});

test('an edges table whose Evidence column states the basis draws the Evidence text nowhere', () => {
  for (const t of tablesOf('edges').filter(table => table.rows.length > 1)) {
    const html = C.render('edges', asBlock(t), ctx());
    for (const row of t.rows) assert.ok(!textOf(html).includes(row[4]) && !html.includes(row[4]), `${t.module} ${t.heading}: ${row[4]}`);
  }
});

// ---- the answer key: every non-hidden, non-omitted cell of every key table is drawn ----
function lost(shape, html, block, c) {
  const text = textOf(html), hidden = new Set(S.hiddenColumns(block.headers, shape)), missing = [];
  block.rows.forEach(row => row.cells.forEach((cell, at) => {
    const t = String(cell ?? '').trim();
    if (!t || hidden.has(at) || at >= block.headers.length || C.findingCell(t, c).html === undefined) return;
    if (!text.includes(t.replace(/\*\*|`/g, ''))) missing.push(`[${at}] ${t}`);
  }));
  return missing;
}
test('every non-hidden, non-omitted cell of each of the 8 key dated tables is drawn, and the Source cell is not', () => {
  const tables = tablesOf('dated');
  assert.equal(tables.length, 8);
  for (const t of tables) {
    const block = asBlock(t), html = C.render('dated', block, ctx());
    assert.deepEqual(lost('dated', html, block, ctx()), [], `${t.module} ${t.heading}`);
    const source = t.headers.indexOf('Source');
    for (const row of t.rows) assert.ok(!html.includes(decode(row[source]).slice(0, 40)) || /^Not supplied/.test(row[source]), `${t.heading}: the Source cell stays in the trace`);
  }
});
test('every non-hidden, non-omitted cell of each of the 7 key edges tables is drawn', () => {
  const tables = tablesOf('edges');
  assert.equal(tables.length, 7);
  for (const t of tables) {
    const block = asBlock(t), html = C.render('edges', block, ctx());
    assert.deepEqual(lost('edges', html, block, ctx()), [], `${t.module} ${t.heading}`);
  }
});
test('a key table of each shape draws its own component: the layout follows the count of events, and the maps are interactive diagrams', () => {
  const layout = Object.fromEntries(tablesOf('dated').map(t => [`${t.module}:${t.heading}`, /class="tl (tl-[hv])"/.exec(C.render('dated', asBlock(t), ctx()))?.[1] ?? 'none']));
  assert.deepEqual(layout, {
    'CP-0:Events: Sources': 'tl-v', 'CP-1A:Events: Issuer history': 'tl-v', 'CP-2A:T5.2 Catalyst Calendar': 'tl-h', 'CP-2E:Events: Hedges': 'tl-h',
    'CP-3:Events: Instruments': 'tl-v', 'CP-4:Events: Legal': 'none', 'CP-6:Events: Decision and watch': 'none', 'CP-DR:Events: Research catalysts': 'tl-h',
  });
  for (const t of tablesOf('edges')) {
    const html = C.render('edges', asBlock(t), ctx());
    if (t.rows.length === 1) { assert.ok(html.includes('class="empty-state"') && !html.includes('map-steps') && !html.includes('role="button"'), `${t.heading}: a stated absence`); continue; }
    assert.ok(html.includes('<svg') && html.includes('role="button"') && html.includes('class="map-steps"'), t.heading);
  }
});

// ---- the timeline ----
test('timeline: a category column gives each event an icon beside its word; the date is drawn as written, in the table order, equally spaced, with no axis tick', () => {
  const t = tablesOf('dated').find(x => x.heading.includes('Catalyst Calendar'));
  const html = C.render('dated', asBlock(t), ctx());
  assert.deepEqual([...html.matchAll(/<div class="tl-d">(.*?)<\/div>/g)].map(m => m[1]), t.rows.map(r => r[0]));
  assert.equal(count(html, /class="tl-cat"/g), t.rows.length);
  for (const row of t.rows) assert.ok(new RegExp(`<span class="tl-cat"><svg[^>]*>.*?</svg>${row[2].replace(/[&]/g, '&amp;')}</span>`).test(html), row[2]);
  assert.ok(!html.includes('data-tick') && !/style="[^"]*left:/.test(html), 'no axis, no scaled position');
  assert.ok(!/<span class="tl-cat"><svg[^>]*><\/svg>/.test(html), 'an icon is never alone');
});
test('timeline: one event; six are horizontal; seven are vertical, grouped by year when every date parses with a year', () => {
  const one = C.render('dated', blk(DATED, [ev('2025-03-31')]), ctx());
  assert.ok(one.includes('class="tl tl-h"') && count(one, /<li class="tl-i">/g) === 1);
  const six = C.render('dated', blk(DATED, [1, 2, 3, 4, 5, 6].map(n => ev(`2025-0${n}-01`))), ctx());
  assert.ok(six.includes('class="tl tl-h"') && count(six, /<li class="tl-i">/g) === 6 && !six.includes('tl-yr'));
  const seven = C.render('dated', blk(DATED, [...[1, 2, 3, 4, 5, 6].map(n => ev(`2025-0${n}-01`)), ev('2026-01-15')]), ctx());
  assert.ok(seven.includes('class="tl tl-v"') && count(seven, /<li class="tl-i">/g) === 7);
  assert.deepEqual([...seven.matchAll(/<li class="tl-yr">(.*?)<\/li>/g)].map(m => m[1]), ['2025', '2026']);
});
test('timeline: dates that do not parse are drawn as written, equally spaced, in the table order, with no year heading and no tick', () => {
  const dates = ['Quarter ended 2024-12-28', 'H2 2025', 'Q1 FY26', 'Before the next refinancing', 'FY2027', '2028-13-45', 'Late 2028'];
  const html = C.render('dated', blk(DATED, dates.map(d => ev(d))), ctx());
  assert.deepEqual([...html.matchAll(/<div class="tl-d">(.*?)<\/div>/g)].map(m => m[1]), dates);
  assert.ok(!html.includes('tl-yr') && !html.includes('data-tick') && !/style="[^"]*left:/.test(html));
});
test('timeline: two events on one date are both drawn, in the table order', () => {
  const html = C.render('dated', blk(DATED, [ev('2025-03-31', 'First on the day'), ev('2025-03-31', 'Second on the day')]), ctx());
  assert.ok(html.indexOf('First on the day') < html.indexOf('Second on the day') && count(html, /<div class="tl-d">2025-03-31<\/div>/g) === 2);
});
test('timeline: a row with fewer cells than headers and a row with more are drawn without losing a cell or throwing', () => {
  const block = blk(DATED, [['2025-03-31', 'day'], ev('2025-04-30', 'Full row').concat(['An extra cell beyond the headers']), []]);
  const html = C.render('dated', block, ctx());
  assert.ok(html.includes('An extra cell beyond the headers') && html.includes('Full row') && count(html, /<li class="tl-i">/g) === 3);
});
test('timeline: markup in a cell is escaped; a 200-character unbroken token is drawn whole', () => {
  const token = 'x'.repeat(200), bad = '<b>&"\'';
  const html = C.render('dated', blk(DATED, [ev('2025-03-31', `${bad} ${token}`, {rel: `${bad} relevance`})]), ctx({caption: bad}));
  assert.ok(!html.includes('<b>&"') && html.includes(token) && textOf(html).includes(`${bad} ${token}`));
  assert.equal(count(html, /<script/gi), 0);
});
test('timeline: the trace icon is one per event and opens the row; the Source column is drawn nowhere', () => {
  const html = C.render('dated', blk(DATED, [ev('2025-03-31', 'Note matures'), ev('2025-06-30', 'Call window')]), ctx());
  assert.equal(count(html, /class="basis-link trace-row"/g), 2);
  assert.ok(html.includes('data-evidence="o:12"') && html.includes('data-evidence="o:13"') && html.includes('aria-label="Note matures: where it comes from"'));
  assert.ok(!html.includes('.jsonl') && !html.includes('K_10-K'));
});
test('timeline: a held-back cell is in no attribute; its row is named by its place in the table', () => {
  const block = blk(DATED, [ev('2025-03-31', 'Refinancing per calculation V01 and EV-007')]);
  const html = C.render('dated', block, ctx({tokens: ['EV-007']}));
  assert.ok(!html.includes('V01') && !html.includes('EV-007') && html.includes('aria-label="Row 1: where it comes from"') && html.includes('In Evidence'));
});
test('timeline: a table with no event column is drawn as record cards with every cell', () => {
  const block = blk(['Date/Window', 'Thing', 'Why'], [['2025', 'A', 'B']]);
  const html = C.render('dated', block, ctx());
  assert.ok(html.includes('rec-card') && !html.includes('class="tl ') && textOf(html).includes('2025') && textOf(html).includes('Why'));
});
test('timeline: an absence in only some rows is still a timeline, the absent cell drawn as written', () => {
  const html = C.render('dated', blk(DATED, [ev('2025-03-31', 'Real event', {rel: 'Not supplied: no view stated'})]), ctx());
  assert.ok(html.includes('class="tl tl-h"') && textOf(html).includes('Not supplied: no view stated') && !html.includes('empty-state'));
});
test('timeline: the empty state also reads "None identified ..." and keeps each distinct reason once', () => {
  const block = blk(['Date/Window', 'Event Description', 'Event Category', 'Source'], [['None identified in the supplied sources', 'None identified in the supplied sources', 'None identified in the supplied sources', 'x.jsonl']]);
  const html = C.render('dated', block, ctx());
  assert.ok(html.includes('class="empty-state"') && count(textOf(html), /None identified in the supplied sources/g) === 1 && !html.includes('x.jsonl'));
});

// ---- the pathway ----
test('pathway: a node and an edge are real keyboard controls with aria-pressed, the step list holds every edge, and the legend names each edge type once', () => {
  const block = blk(EDGE, [eg('A driver', 'drives', 'Documentary Fact', 'A mechanism'), eg('A mechanism', 'squeezes', 'Management Language', 'An outcome'), eg('A driver', 'also hits', 'Documentary Fact', 'An outcome')]);
  const html = C.render('edges', block, ctx());
  assert.equal(count(html, /<g class="map-node"[^>]*role="button" tabindex="0" aria-pressed="false"/g), 3);
  assert.equal(count(html, /<g class="map-eg"[^>]*role="button" tabindex="0" aria-pressed="false"/g), 3);
  assert.equal(count(html, /<li class="pw-step">/g), 3);
  const legend = /<div class="map-legend">(.*?)<\/div>/s.exec(html)[1];
  assert.deepEqual([...legend.matchAll(/<\/svg>(.*?)<\/span>/g)].map(m => m[1]), ['Documentary Fact', 'Management Language']);
  assert.ok(html.includes('data-map-panel') && html.includes('data-map-hint') && count(html, /data-rel="\d"/g) === 3);
  assert.ok(!html.includes('Annual filing page 9') && !html.includes('<table'));
});
test('pathway: the edge style follows the type word, one style per word', () => {
  const rows = [eg('A', 'r1', 'Supports', 'B'), eg('B', 'r2', 'Contradicts', 'C'), eg('C', 'r3', 'Supports', 'D')];
  const html = C.render('edges', blk(EDGE, rows), ctx());
  const dash = [...html.matchAll(/<path class="map-edge[^"]*"[^>]*?(?:stroke-dasharray="([^"]*)")?\/>/g)].map(m => m[1] ?? '');
  assert.equal(dash.length, 3);
  assert.equal(dash[0], dash[2]);
  assert.notEqual(dash[0], dash[1]);
});
test('pathway: a node that appears in no other edge, a self-edge and a cycle are all drawn, each node once', () => {
  const rows = [eg('Alone', 'points at', 'Supports', 'Hub'), eg('Hub', 'loops on itself', 'Supports', 'Hub'), eg('Hub', 'goes round', 'Supports', 'Ring'), eg('Ring', 'comes back', 'Supports', 'Hub')];
  const html = C.render('edges', blk(EDGE, rows), ctx());
  assert.equal(count(html, /<g class="map-node"/g), 3);
  assert.equal(count(html, /<g class="map-eg"/g), 4);
  assert.equal(count(html, /<li class="pw-step">/g), 4);
  assert.ok(html.includes('would close a loop'), 'the cut edges are stated');
});
test('pathway: a ragged table keeps every cell it can name; markup is escaped; a 200-character name is whole in the step list and the node title', () => {
  const name = 'y'.repeat(200), bad = '<b>&"\'';
  const rows = [eg(name, `${bad} relation`, 'Supports', 'Short'), ['Short', 'only four cells', 'Supports', 'Mid'], eg('Short', 'extra', 'Supports', 'Last', 'e').concat(['A cell beyond the headers'])];
  const block = blk(EDGE, rows);
  let html;
  assert.doesNotThrow(() => { html = C.render('edges', block, ctx()); });
  assert.ok(textOf(html).includes(`${bad} relation`) && !html.includes('<b>&"'));
  assert.ok(html.includes(`<title>${name}</title>`) && html.includes(`<div class="pw-fr">${name}</div>`));
  assert.ok(html.includes('A cell beyond the headers'));
});
test('pathway: a table whose node cell cannot be drawn (an identifier) is drawn as record cards with every other cell, never dropped', () => {
  const block = blk(EDGE, [eg('EV-009', 'drives', 'Supports', 'Outcome'), eg('Driver', 'feeds', 'Supports', 'Outcome')]);
  const html = C.render('edges', block, ctx({tokens: ['EV-009']}));
  assert.ok(html.includes('rec-card') && !html.includes('<svg class="map-svg"') && textOf(html).includes('feeds') && !html.includes('EV-009'));
});
test('pathway: the relationship panel and step list carry the row\'s non-hidden cells and a trace control per row; nothing held back is in an attribute', () => {
  const rows = [eg('Driver', 'Moves the outcome by calculation V03', 'Supports', 'Outcome'), eg('Outcome', 'Feeds the next', 'Supports', 'Result')];
  const html = C.render('edges', blk(EDGE, rows), ctx());
  assert.ok(!html.includes('V03'), 'a cell naming a calculation is held back everywhere');
  assert.equal(count(html, /class="basis-link trace-row"/g) >= 2, true);
  assert.ok(/aria-label="Driver to Outcome, Supports"/.test(html));
  assert.ok(html.includes('class="rel" data-rel="1" hidden'));
});
test('pathway: a stated absence is the empty state with the module\'s reason (the one in the Evidence column too), not a diagram', () => {
  const t = tablesOf('edges').find(x => x.heading.includes('legal entities'));
  const html = C.render('edges', asBlock(t), ctx());
  assert.ok(html.includes('class="empty-state"') && !html.includes('map-steps') && textOf(html).includes(t.rows[0][4]), 'the module states why no edge can be drawn in its last cell');
  assert.equal(count(textOf(html), /not assessable, no executed governing document available/g), 1);
});

// ---- the page's own state: a click or Enter on a node or an edge ----
function fakeMap() {
  const mk = (dataset, hidden = false) => { const e = {dataset, hidden, attrs: {}, cls: new Set(), setAttribute(k, v) { this.attrs[k] = v; }, classList: null}; e.classList = {toggle(c, on) { if (on) e.cls.add(c); else e.cls.delete(c); }}; return e; };
  const nodes = [mk({mapPick: 'n:0', mapEdges: '0', mapNodes: '0 1'}), mk({mapPick: 'n:1', mapEdges: '0 1', mapNodes: '1 0 2'}), mk({mapPick: 'n:2', mapEdges: '1', mapNodes: '2 1'})];
  const edges = [mk({mapPick: 'e:0', mapEdges: '0', mapNodes: '0 1'}), mk({mapPick: 'e:1', mapEdges: '1', mapNodes: '1 2'})];
  const rels = [mk({rel: '0'}, true), mk({rel: '1'}, true)], hint = mk({}, false), nodeEls = nodes.map(n => mk({node: n.dataset.mapPick.slice(2)}));
  const root = {dataset: {}, querySelectorAll: sel => ({'[data-map-pick]': [...nodes, ...edges], '[data-rel]': rels, '[data-map-hint]': [hint], '.map-node': nodes, '.map-eg': edges}[sel] ?? [])};
  for (const p of [...nodes, ...edges]) p.closest = sel => (sel === '[data-map-pick]' ? p : sel === '.shape-pathway' ? root : null);
  return {root, nodes, edges, rels, hint, click: p => C.handleClick(p)};
}
test('handleClick: selecting a node opens its edges\' panels and presses it; selecting it again closes them', () => {
  const m = fakeMap();
  assert.equal(m.click(m.nodes[1]), true);
  assert.equal(m.root.dataset.selected, 'n:1');
  assert.deepEqual(m.rels.map(r => r.hidden), [false, false]);
  assert.equal(m.hint.hidden, true);
  assert.equal(m.nodes[1].attrs['aria-pressed'], 'true');
  assert.equal(m.nodes[0].attrs['aria-pressed'], 'false');
  m.click(m.nodes[1]);
  assert.equal(m.root.dataset.selected, '');
  assert.deepEqual(m.rels.map(r => r.hidden), [true, true]);
  assert.equal(m.hint.hidden, false);
});
test('handleClick: selecting an edge shows only its panel and presses only it', () => {
  const m = fakeMap();
  m.click(m.edges[1]);
  assert.deepEqual(m.rels.map(r => r.hidden), [true, false]);
  assert.deepEqual([...m.nodes, ...m.edges].map(p => p.attrs['aria-pressed']), ['false', 'false', 'false', 'false', 'true']);
  m.click(m.nodes[0]);
  assert.deepEqual([...m.nodes, ...m.edges].map(p => p.attrs['aria-pressed']), ['true', 'false', 'false', 'false', 'false']);
  assert.deepEqual(m.rels.map(r => r.hidden), [false, true]);
});

'use strict';
// shapes.js against the controller's answer key (fixtures/shape-key.json), which this file does not edit.
// The key's shapes were assigned by section heading; Shapes.tableShape sees only the block.
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const KEY = require(path.join(__dirname, '..', '..', 'fixtures', 'shape-key.json'));
const Shapes = require('./shapes.js');

const block = (headers, rows) => ({headers, rows: rows.map(cells => ({cells}))});

test('sectionRole reproduces all section roles of the key', () => {
  assert.equal(KEY.sections.length, 321);
  const wrong = KEY.sections.filter(s => Shapes.sectionRole(s.chain, s.placement) !== s.role)
    .map(s => `${s.module}#${s.index} ${s.chain.join(' > ')}: ${Shapes.sectionRole(s.chain, s.placement)} != ${s.role}`);
  assert.deepEqual(wrong, []);
});

test('tableShape reproduces all table shapes of the key from headers and cells alone', () => {
  assert.equal(KEY.tables.length, 41);
  const wrong = KEY.tables.filter(t => Shapes.tableShape(block(t.headers, t.rows)) !== t.shape)
    .map(t => `${t.module} ${t.heading}: ${Shapes.tableShape(block(t.headers, t.rows))} != ${t.shape}`);
  assert.deepEqual(wrong, []);
});

test('hiddenColumns reproduces all hidden column indices of the key', () => {
  const wrong = KEY.tables.filter(t => JSON.stringify(Shapes.hiddenColumns(t.headers, t.shape)) !== JSON.stringify(t.hidden))
    .map(t => `${t.module} ${t.heading}: ${Shapes.hiddenColumns(t.headers, t.shape)} != ${t.hidden}`);
  assert.deepEqual(wrong, []);
});

test('every note of the key is a note, and ordinary sentences are prose', () => {
  assert.equal(KEY.notes.length, 5);
  for (const n of KEY.notes) assert.equal(Shapes.blockRole(n.starts), 'note', n.starts);
  for (const text of [
    'The base period is FY2024, the only twelve-month period with a full fact set in CP-1.',
    'The summary table shows that leverage crosses the watch levels long before cash flow or interest cover fails, in both analyst scenarios.',
    'The control row s00 reconciles exactly to CP-1 calculations C05, C11, C12 and C31.',
  ]) assert.equal(Shapes.blockRole(text), 'prose', text);
});

test('a zero-row table and an unrecognised header set are records, never dropped', () => {
  const statement = KEY.tables.find(t => t.shape === 'statement');
  assert.equal(Shapes.tableShape(block(statement.headers, [])), 'records');
  assert.equal(Shapes.tableShape(block(['Widget', 'Colour', 'Mass'], [['a', 'b', 'c']])), 'records');
  assert.equal(Shapes.tableShape(block([], [])), 'records');
});

test('headers differing only in case or outer spaces classify the same', () => {
  for (const t of KEY.tables) {
    const messy = t.headers.map((h, i) => (i % 2 ? ` ${h.toUpperCase()} ` : `  ${h.toLowerCase()}`));
    assert.equal(Shapes.tableShape(block(messy, t.rows)), t.shape, `${t.module} ${t.heading}`);
    assert.deepEqual(Shapes.hiddenColumns(messy, t.shape), t.hidden, `${t.module} ${t.heading}`);
  }
});

test('a statement whose second period cell is "Not calculated" is still a statement', () => {
  const t = KEY.tables.find(x => x.shape === 'statement');
  const rows = t.rows.map(r => r.map((c, i) => (i === 2 ? 'Not calculated' : c)));
  assert.equal(Shapes.tableShape(block(t.headers, rows)), 'statement');
});

test('columnKind and promoted', () => {
  assert.equal(Shapes.columnKind('Source'), 'source');
  assert.equal(Shapes.columnKind('Scenario ID'), 'id');
  assert.equal(Shapes.columnKind('Use in this module'), 'intermodule');
  assert.equal(Shapes.columnKind('FY2024'), 'period');
  assert.equal(Shapes.columnKind('Hedge limitation'), 'limitation');
  assert.equal(Shapes.columnKind('Creditor consequence'), 'consequence');
  assert.equal(Shapes.columnKind('Moderate scenario'), 'case');
  assert.equal(Shapes.columnKind('Exposure'), 'label');
  assert.equal(Shapes.columnKind('Creditor view'), 'text');
  for (const s of ['matrix', 'watch', 'dated']) assert.equal(Shapes.promoted(s), true);
  assert.equal(Shapes.promoted('statement'), false);
});

test('audit columns are hidden by pattern, not by exact name', () => {
  const cp4 = ['Test', 'Test Type', 'Threshold', 'Current Basis', 'Formula', 'Headroom', 'Status', 'Limitation', 'Risk Mechanic', 'Credit Implication', 'Evidence ID'];
  assert.deepEqual(Shapes.hiddenColumns(cp4, Shapes.tableShape(block(cp4, [cp4]))), [10]);
  assert.equal(Shapes.columnKind('Evidence ID'), 'id');
  assert.equal(Shapes.columnKind('Topic ID'), 'id');
  assert.equal(Shapes.columnKind('Sources'), 'source');
  assert.equal(Shapes.columnKind('Source / Clause'), 'source');
  assert.equal(Shapes.columnKind('Evidence'), 'source');
  assert.equal(Shapes.columnKind('Resource'), 'text');
});

test('an unknown level-2 heading and its children are registers; only the explicit list is hidden', () => {
  assert.equal(Shapes.sectionRole(['Appendix'], 'audit'), 'registers');
  assert.equal(Shapes.sectionRole(['Method notes', 'Sub'], 'audit'), 'registers');
  assert.equal(Shapes.sectionRole(['Request'], 'audit'), 'hidden');
  assert.equal(Shapes.sectionRole(['Appendix', 'Cross-Module Handoff Register'], 'audit'), 'hidden');
});

test('period labels with actual/estimate suffixes or two-digit years are periods', () => {
  for (const h of ['FY2024A', 'FY2025E', 'FY24', 'FY23', 'FY2024']) assert.equal(Shapes.columnKind(h), 'period', h);
  assert.equal(Shapes.tableShape(block(['Line', 'FY2024A', 'FY2025E', 'Source'], [['a', '1', '2', 's']])), 'statement');
  assert.equal(Shapes.tableShape(block(['Line', 'FY24', 'FY23', 'Source'], [['a', '1', '2', 's']])), 'statement');
  assert.equal(Shapes.tableShape(block(['Metric', 'FY24', 'FY23', 'Definition', 'Source'], [['a', '1', '2', 'd', 's']])), 'metric');
});

test('notes: SKILL is case-sensitive, helper scripts alone is prose, "Confidence is" needs a number', () => {
  assert.equal(Shapes.blockRole('Management has shown skill in pricing aftermarket parts, which supports margin.'), 'prose');
  assert.equal(Shapes.blockRole('Helper scripts were not run.'), 'prose');
  assert.equal(Shapes.blockRole('Confidence is low that the 2026 maturities refinance at current spreads.'), 'prose');
  assert.equal(Shapes.blockRole('Confidence is 61 out of 100, Medium.'), 'note');
  assert.equal(Shapes.blockRole('The SKILL output profile defines the table.'), 'note');
});

test('source and evidence columns hide only whole or with an audit qualifier', () => {
  for (const h of ['Source', 'Sources', 'Evidence', 'Source / Clause', 'Source trace', 'Source locator', 'Evidence ID', 'Evidence document', 'Source file', 'Evidence page', 'Source reference', 'Evidence link', 'Source hash', 'Source register'])
    assert.equal(['source', 'id'].includes(Shapes.columnKind(h)), true, h);
  for (const h of ['Evidence Status', 'Source Conflict', 'Evidence Quality', 'Evidence Pattern', 'Source Type', 'Source of repayment', 'Sources of liquidity', 'Evidence strength'])
    assert.equal(['source', 'id', 'intermodule'].includes(Shapes.columnKind(h)), false, h);
});

test('a plain Module header is not an inter-module column', () => {
  assert.deepEqual(Shapes.hiddenColumns(['Issue', 'Module', 'Severity', 'Evidence Status'], 'records'), []);
});

test('note matching is case-insensitive except SKILL', () => {
  assert.equal(Shapes.blockRole('module status: Completed with Limitations.'), 'note');
  assert.equal(Shapes.blockRole('Management skill is evident.'), 'prose');
});

test('inter-module: the machine name downstream_use addresses another module; a register column headed "Downstream Use" is kept', () => {
  assert.equal(Shapes.columnKind('downstream_use'), 'intermodule');
  assert.equal(Shapes.columnKind('consumer_module_id'), 'intermodule');
  assert.notEqual(Shapes.columnKind('Downstream Use'), 'intermodule');
  assert.deepEqual(Shapes.hiddenColumns(['Source', 'Downstream Use', 'downstream_use']), [0, 2]);
});

// ---- idTokens and casePairing (Task 5): the key's real tables, as the module page holds them (sections of table blocks with {line, cells} rows)
const keyBlock = t => ({type: 'table', headers: t.headers, rows: t.rows.map((cells, i) => ({line: i + 1, cells}))});
const keySections = module => KEY.tables.filter(t => t.module === module).map(t => ({blocks: [keyBlock(t)]}));

test('idTokens: the distinct values of every id column of the module, none that is only digits or one character', () => {
  const tokens = Shapes.idTokens(keySections('CP-2A'));
  for (const token of ['s00', 'SC1', 'SC2', 'EV-01', 'CP-2A-MON-001', 'CP-2A-DP-001']) assert.ok(tokens.includes(token), token);
  assert.equal(new Set(tokens).size, tokens.length, 'distinct');
  assert.ok(!tokens.includes('Base FY2024 (control)') && !tokens.includes('High'), 'only id columns');
  const numbered = Shapes.idTokens(keySections('CP-0'));
  assert.ok(numbered.every(token => !/^\d+$/.test(token)), 'a running row number is not an identifier');
  const small = Shapes.idTokens([{blocks: [block(['ID', 'Note'], [['A', 'x'], ['12', 'y'], ['', 'z'], ['EV-7', 'w']])].map(b => ({type: 'table', ...b}))}]);
  assert.deepEqual(small, ['EV-7']);
  assert.deepEqual(Shapes.idTokens([]), []);
  assert.deepEqual(Shapes.idTokens([{blocks: [{type: 'text', text: 'x'}]}]), []);
});

test('casePairing: the CP-2A tables pair the three case columns with the three scenario rows; a count mismatch, two cases tables or none give null', () => {
  const blocks = keySections('CP-2A').flatMap(s => s.blocks);
  assert.deepEqual(Shapes.casePairing(blocks), {names: ['Base FY2024 (control)', 'Moderate scenario', 'Severe scenario'], ids: ['s00', 'SC1', 'SC2']});
  const cases = blocks.find(b => Shapes.tableShape(b) === 'cases');
  const rowsOf = blocks.filter(b => Shapes.tableShape(b) === 'caseRows');
  assert.equal(rowsOf.length, 2);
  const short = {headers: rowsOf[0].headers, rows: rowsOf[0].rows.slice(0, 2)};
  assert.equal(Shapes.casePairing([cases, short]), null, 'two rows for three case columns');
  assert.equal(Shapes.casePairing([cases, cases, rowsOf[0]]), null, 'two cases tables');
  assert.equal(Shapes.casePairing([rowsOf[0]]), null, 'no cases table');
  assert.equal(Shapes.casePairing([]), null);
  assert.equal(Shapes.casePairing(undefined), null);
  const plain = {headers: ['Scenario', 'Note'], rows: ['a', 'b', 'c'].map(x => ({cells: [x, 'n']}))};
  assert.deepEqual(Shapes.casePairing([cases, plain]), {names: ['Base FY2024 (control)', 'Moderate scenario', 'Severe scenario'], ids: ['a', 'b', 'c']}, 'no id column: the first column');
});

test('methodNote: a calculation name makes a Calculations note, an identifier of the module a Registers note, anything else is findings prose (whole words only)', () => {
  const tokens = ['EV-01', 'SC1'];
  assert.equal(Shapes.methodNote('Net debt follows calculation D17.', tokens), 'calculations');
  assert.equal(Shapes.methodNote('See Calculations C21 and the bridge.', []), 'calculations');
  assert.equal(Shapes.methodNote('EV-01 is the special dividend.', tokens), 'registers');
  assert.equal(Shapes.methodNote('Under SC1 leverage rises.', tokens), 'registers');
  assert.equal(Shapes.methodNote('Both EV-01 and calculation D17 apply.', tokens), 'calculations', 'a calculation ID wins');
  for (const prose of ['EV-010 is another event.', 'ASC1 is not an identifier.', 'Leverage is moderate.', 'calculation K1 has one digit', '']) assert.equal(Shapes.methodNote(prose, tokens), null, prose);
  assert.equal(Shapes.methodNote('EV-01 stands', undefined), null);
  assert.equal(Shapes.methodNote(undefined, tokens), null);
});

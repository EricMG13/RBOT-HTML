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

test('A1: the five source-qualifier headers hide; a findings column that begins with Source stays', () => {
  for (const h of ['Source Document Name', 'Source and basis', 'Source(s)', ' source row/section/quote ', 'sha256 hash'])
    assert.equal(Shapes.columnKind(h), 'source', h);
  for (const h of ['Sources of liquidity', 'Source of repayment', 'Source and use'])
    assert.equal(Shapes.columnKind(h), 'text', h);
});

test('A2: casePairing matches ids written in bold in the pairing source', () => {
  const t = (headers, rows) => ({type: 'table', headers, rows: rows.map((cells, i) => ({line: i + 1, cells}))});
  const cases = t(['Measure', 'Base case', 'Severe scenario'], [['Leverage', '6.0x', '8.7x']]);
  const defs = t(['Scenario ID', 'Decline'], [['**s00**', '0'], ['**SC1**', '0.15']]);
  assert.deepEqual(Shapes.casePairing([cases, defs]).ids, ['s00', 'SC1']);
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
  const pairing = Shapes.casePairing(blocks);
  assert.deepEqual({names: pairing.names, ids: pairing.ids}, {names: ['Base FY2024 (control)', 'Moderate scenario', 'Severe scenario'], ids: ['s00', 'SC1', 'SC2']});
  assert.equal(pairing.table, blocks.find(b => b.headers[0] === 'Scenario ID'), 'the paired table is the one with the id column');
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
  assert.equal(Shapes.casePairing([cases, plain]), null, 'a caseRows table without an id column is never paired');
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

test('isLedger: a table that lists a comparison\'s limitations by the earlier and the current reference is a ledger; no other table is, and the section heading is not read', () => {
  const ledger = {headers: ['Earlier ref', 'Current ref', 'Limitation', 'Status', 'What closed it'], rows: [{cells: ['E1', '—', 'x', 'No longer stated', '—']}]};
  assert.equal(Shapes.isLedger(ledger), true);
  assert.equal(Shapes.isLedger({...ledger, headers: ['earlier_ref', ' CURRENT REF ', 'Limitation']}), true, 'case, spacing and underscores as columnKind reads them');
  for (const headers of [['Earlier', 'Current', 'Cause'], ['Earlier ref', 'Limitation'], ['Current ref', 'Limitation'], ['Gap', 'Severity'], []]) assert.equal(Shapes.isLedger({headers, rows: ledger.rows}), false, headers.join('|'));
  assert.equal(Shapes.isLedger({headers: ledger.headers, rows: []}), false, 'no row, no ledger');
  assert.equal(Shapes.isLedger(null), false);
  assert.equal(Shapes.isLedger({headers: ['Earlier ref', 'Current ref'], rows: [{cells: ['a', 'b']}]}), true);
  assert.equal(Shapes.tableShape(ledger), 'status', 'the shape classifier is unchanged');
});

test('M1(b): source words (hash, sha, file name, locator, citation, Where found) class a column as source; Reference, Ref and Code are id columns only by their cells', () => {
  for (const h of ['Hash', 'SHA256 value', 'sha', 'Document hash', 'File name', 'Filename', 'Locator', 'Page locator', 'Citation', 'Citations', 'Where found', 'where_found']) assert.equal(Shapes.columnKind(h), 'source', h);
  for (const h of ['Share count', 'Cash', 'Where found it', 'Shadow price']) assert.notEqual(Shapes.columnKind(h), 'source', h);
  for (const h of ['Reference', 'References', 'Ref', 'Ref.', 'Code', 'reference']) {
    assert.equal(Shapes.columnKind(h), 'text', `${h} without cells is a findings column`);
    assert.equal(Shapes.columnKind(h, ['REF-0007', 'REF-0008', 'x']), 'id', `${h}: two of three cells are id-shaped`);
    assert.equal(Shapes.columnKind(h, ['REF-0007', 'plain', 'words', 'here']), 'text', `${h}: one of four`);
    assert.equal(Shapes.columnKind(h, ['', '  ', 'a.pdf']), 'id', `${h}: empty cells do not count`);
    assert.equal(Shapes.columnKind(h, ['d41d8cd98f00b204e9800998ecf8427e', 'n/a']), 'id', `${h}: a 32-character hash is id-shaped`);
  }
  for (const h of ['Reference rate', 'Currency code', 'Code of conduct']) assert.equal(Shapes.columnKind(h, ['ROW-1', 'ROW-2']), 'text', h);
  assert.equal(Shapes.columnKind('Code', ['USD', 'EUR', 'Floating']), 'text', 'a Code column of words stays a findings column');
  assert.deepEqual(Shapes.hiddenColumns(['Line', 'Reference', 'Code'], 'records', [{cells: ['a', 'REF-1', 'USD']}, {cells: ['b', 'REF-2', 'EUR']}]), [1]);
  assert.deepEqual(Shapes.columnKinds({headers: ['Line', 'Reference'], rows: [{cells: ['a', 'ROW-1']}]}), ['label', 'id']);
  assert.deepEqual(Shapes.idTokens([{blocks: [{type: 'table', headers: ['Item', 'Reference'], rows: [{cells: ['a', 'REF-0007']}, {cells: ['b', 'REF-0008']}]}]}]), ['REF-0007', 'REF-0008']);
});

test('M2: the inter-module headers the ruling names are read by their normalised whole name; a findings column that starts the same way is not', () => {
  for (const h of ['Next command', 'Next commands', 'next_module', 'Next-Modules', 'Downstream consumers', 'downstream_consumer', 'Downstream Module Affected', 'Downstream modules affected', 'Downstream Handoff Impact', 'downstream-owners', 'Affected consumers', 'Affected Modules']) assert.equal(Shapes.columnKind(h), 'intermodule', h);
  for (const h of ['Downstream revenue', 'Next maturity', 'Affected assets', 'Downstream Use', 'Modules']) assert.notEqual(Shapes.columnKind(h), 'intermodule', h);
});

test('M1: the file-name and hash patterns read a 5,000-character cell in linear time (no quadratic backtracking on a long word or dotted run)', () => {
  const cells = ['A'.repeat(5000), 'a-'.repeat(2500), 'a.'.repeat(2500), 'a.b-'.repeat(1250), 'word '.repeat(1000)];
  const started = process.hrtime.bigint();
  for (let n = 0; n < 40; n += 1) for (const cell of cells) { Shapes.FILE_NAME.test(cell); Shapes.LONG_HEX.test(cell); }
  const ms = Number(process.hrtime.bigint() - started) / 1e6;
  assert.ok(ms < 400, `200 reads of long cells took ${ms} ms`);
  assert.equal(Shapes.FILE_NAME.test(`${'a.'.repeat(2500)}pdf`), true, 'and a file name at the end of a long dotted run is still found');
});

test('LONG_HEX holds a hash (a letter a-f in a 32+ character hex run), never a 32-digit number or a run of zeros', () => {
  for (const hash of ['4e5e4b7b'.repeat(8), 'a'.repeat(32), '0'.repeat(31) + 'f', `sha ${'0123456789abcdef'.repeat(4)} end`]) assert.ok(Shapes.LONG_HEX.test(hash), hash);
  for (const figure of ['1'.repeat(32), '0'.repeat(40), `Balance ${'9'.repeat(33)} units`]) assert.ok(!Shapes.LONG_HEX.test(figure), figure);
});

test('sectionRole reads the top heading by own key: "constructor", "toString" and "__proto__" are ordinary unknown headings', () => {
  for (const heading of ['constructor', 'toString', '__proto__', 'hasOwnProperty']) assert.equal(Shapes.sectionRole([heading]), 'registers', heading);
});

test('isEsgHeading: a heading that leads with a T2G.<digits> code is an ESG heading, at any heading level; nothing else is', () => {
  for (const heading of ['T2G.1 — Environmental/social disclosure inventory', 'T2G.8 — environmental, social and transition gaps', 'T2G.5 Sustainability-linked mechanics', 'T2G.3']) assert.equal(Shapes.isEsgHeading(heading), true, heading);
  for (const heading of ['T2F.9 — Macro gaps ledger', 'T2G — overview', 'T2G.x — a', 'T12G.1 — a', 'XT2G.1 — a', 'Credit implication', 'Note on T2G.1 — inventory', 'T2G.12b — a', '']) assert.equal(Shapes.isEsgHeading(heading), false, heading);
});

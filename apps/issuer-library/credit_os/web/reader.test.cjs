'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {readerPassages, isNewFormat, earlierFormatRun, blocked, splitBasis, basisItem, figureSpans, normaliseLimitation, earlierBasis, historyRows, pathwayTitle, runModuleCodes, nearestDates} = require('./reader.js');

// Shapes are store.py's: section {heading, level, line, blocks[]}, text block {type, line, end, text}. Expected values are literals.
const text = (body, line = 1) => ({type: 'text', line, end: line, text: body});
const section = (heading, level, ...blocks) => ({heading, level, line: 1, blocks});
const newFormat = bottom => [
  section('CP-2D handoff', 1), section('Request', 2, text('x')),
  section('Findings', 2), section('Bottom line', 3, text(bottom)), section('Key findings', 3, text('- one')),
  section('Contrary evidence and what would change the view', 3, text('against')), section('Limitations', 3, text('- l')),
  section('Calculations', 2), section('Gaps', 2),
];
const earlier = [section('Findings', 2), section('Reader summary', 3, {type: 'table', line: 1, headers: ['Bottom line'], rows: []})];
const fixture = name => fs.readFileSync(path.join(__dirname, '..', '..', 'fixtures', 'synthetic-new-format', `SYNTHETIC-${name}.md`), 'utf8').split('\n');

test('readerPassages finds the four H3 sections under Findings by exact heading', () => {
  const sections = newFormat('The view.');
  const passages = readerPassages(sections);
  assert.equal(passages.bottom, sections[3]);
  assert.equal(passages.key, sections[4]);
  assert.equal(passages.contrary, sections[5]);
  assert.equal(passages.limits, sections[6]);
});

test('readerPassages ignores the same heading outside Findings and near-miss headings', () => {
  const sections = [
    section('Findings', 2), section('Bottom Line', 3), section('Key finding', 3),
    section('Gaps', 2), section('Limitations', 3), section('Bottom line', 3),
  ];
  assert.deepEqual(readerPassages(sections), {bottom: null, key: null, contrary: null, limits: null});
  assert.deepEqual(readerPassages([]), {bottom: null, key: null, contrary: null, limits: null});
  assert.deepEqual(readerPassages(undefined), {bottom: null, key: null, contrary: null, limits: null});
});

test('isNewFormat is true only when the first H3 after Findings is Bottom line', () => {
  assert.equal(isNewFormat(newFormat('x')), true);
  assert.equal(isNewFormat(earlier), false);
  assert.equal(isNewFormat([section('Findings', 2)]), false);
  assert.equal(isNewFormat([]), false);
  assert.equal(isNewFormat([section('Findings', 2), section('Key findings', 3), section('Bottom line', 3)]), false);
  assert.equal(isNewFormat([section('Bottom line', 3), section('Findings', 2)]), false);
});

test('earlierFormatRun is true when any handoff is not new format', () => {
  assert.equal(earlierFormatRun([newFormat('a'), newFormat('b')]), false);
  assert.equal(earlierFormatRun([newFormat('a'), earlier]), true);
  assert.equal(earlierFormatRun([]), false);
});

test('blocked reads the Bottom line wording for new format and state.established for earlier format', () => {
  assert.equal(blocked(newFormat('Liquidity is not assessable: no forecast.'), {established: true}), true);
  assert.equal(blocked(newFormat('Liquidity is Not Assessable here.'), undefined), true);
  assert.equal(blocked(newFormat('Debt service looks adequate.'), {established: false}), false);
  assert.equal(blocked(earlier, {established: false}), true);
  assert.equal(blocked(earlier, {established: true}), false);
  assert.equal(blocked(earlier, undefined), false);
});

test('splitBasis takes the last line starting exactly "Basis: " and drops one final full stop', () => {
  assert.deepEqual(splitBasis('Text here.\nBasis: a.pdf, page 3; b.pdf.'), {body: 'Text here.', items: ['a.pdf, page 3', 'b.pdf']});
  assert.deepEqual(splitBasis('- Item\nBasis: Liquidity (CP-2D).'), {body: '- Item', items: ['Liquidity (CP-2D)']});
  assert.deepEqual(splitBasis('Basis: x.pdf'), {body: '', items: ['x.pdf']});
  assert.deepEqual(splitBasis('T\nBasis: a.pdf, pages 43–45; calculation K1'), {body: 'T', items: ['a.pdf, pages 43–45', 'calculation K1']});
});

test('splitBasis does not treat other lines as a Basis line', () => {
  const notLast = 'Intro.\nBasis: a.pdf\nMore text.';
  assert.deepEqual(splitBasis(notLast), {body: notLast, items: []});
  for (const line of ['Basis:a.pdf', 'basis: a.pdf', ' Basis: a.pdf', 'The Basis: a.pdf']) {
    assert.deepEqual(splitBasis(`Body\n${line}`), {body: `Body\n${line}`, items: []});
  }
  assert.deepEqual(splitBasis('No basis here.'), {body: 'No basis here.', items: []});
});

test('basisItem reads the three H3 forms and keeps anything else as text', () => {
  assert.deepEqual(basisItem('NBG_2025-03-31_annual-report.pdf'), {kind: 'source', file: 'NBG_2025-03-31_annual-report.pdf'});
  assert.deepEqual(basisItem('NBG_2025-03-31_annual-report.pdf, page 41'), {kind: 'source', file: 'NBG_2025-03-31_annual-report.pdf', page: 41});
  assert.deepEqual(basisItem('NBG_2025-03-31_annual-report.pdf, pages 43–45'), {kind: 'source', file: 'NBG_2025-03-31_annual-report.pdf', page: 43, pageEnd: 45});
  assert.deepEqual(basisItem('Annual report 2025.pdf, page 3'), {kind: 'source', file: 'Annual report 2025.pdf', page: 3});
  assert.deepEqual(basisItem('Liquidity (CP-2D)'), {kind: 'module', name: 'Liquidity', code: 'CP-2D'});
  assert.deepEqual(basisItem('calculation K1'), {kind: 'calculation', id: 'K1'});
});

test('basisItem keeps an unrecognised item verbatim', () => {
  for (const odd of ['NBG_2025-03-31_annual-report.pdf, pages 43-45', 'see note 3.5', 'Liquidity (not a code)', 'calculation', 'management said so']) {
    assert.deepEqual(basisItem(odd), {kind: 'text', text: odd});
  }
});

const figures = s => figureSpans(s).map(f => f.text);

test('figureSpans covers currency prefix and unit suffix with exact offsets', () => {
  const sentence = 'Revenue was USD 1,250 million, margin 38% and leverage 4.2x.';
  assert.deepEqual(figureSpans(sentence), [
    {start: 12, end: 29, text: 'USD 1,250 million'},
    {start: 38, end: 41, text: '38%'},
    {start: 55, end: 59, text: '4.2x'},
  ]);
  assert.deepEqual(figureSpans('$12.5 million'), [{start: 0, end: 13, text: '$12.5 million'}]);
  assert.deepEqual(figures('Costs of €40 million and £3.5bn, 150 bps, 25 basis points'), ['€40 million', '£3.5bn', '150 bps', '25 basis points']);
  assert.deepEqual(figures('USD 7 and 12 million shares'), ['USD 7', '12 million']);
});

test('figureSpans leaves out years, dates, period labels and small whole numbers', () => {
  const exempt = 'In 2024 the 10-K for FY2024 rated B-1 on 2024-09-30 and March 5, 2025, 5 March 2025, Q4 and H1 and 9M and LTM, 12 loans over 24 months in 2025-Q3 and 2025-03.';
  assert.deepEqual(figureSpans(exempt), []);
  assert.deepEqual(figureSpans('The 3rd lien (11) CP-2 and CP-2D'), []);
});

test('figureSpans keeps numbers that carry no unit as figures, and years out of range', () => {
  assert.deepEqual(figures('Debt of 1,250 and 2.5 and 1850 and 2100 and 100'), ['1,250', '2.5', '1850', '2100', '100']);
  assert.deepEqual(figures('Margin 0.5% and 99%'), ['0.5%', '99%']);
});

test('figureSpans of the synthetic CP-2 bottom line', () => {
  const line = fixture('CP-2').find(l => l.startsWith('Creditors are exposed'));
  assert.deepEqual(figures(line), ['USD 1,390 million', '4.2x']);
});

test('normaliseLimitation lowercases, drops the Basis line and punctuation, collapses spacing', () => {
  assert.equal(normaliseLimitation('- The Covenant package was not reviewed,  so covenant headroom is not assessed.\nBasis: a.pdf'), 'the covenant package was not reviewed so covenant headroom is not assessed');
  assert.equal(normaliseLimitation('  A—B;  "C"!  '), 'ab c');
});

test('normaliseLimitation makes the synthetic CP-1A and CP-2 covenant limitations equal', () => {
  const one = fixture('CP-1A').find(l => l.startsWith('- The covenant package'));
  const two = fixture('CP-2').find(l => l.startsWith('- The Covenant package'));
  assert.notEqual(one, two);
  assert.equal(normaliseLimitation(one), 'the covenant package was not reviewed so covenant headroom is not assessed');
  assert.equal(normaliseLimitation(two), 'the covenant package was not reviewed so covenant headroom is not assessed');
});

test('synthetic CP-2 Basis lines resolve to every item form', () => {
  const lines = fixture('CP-2').filter(l => l.startsWith('Basis: '));
  const kinds = new Set(lines.flatMap(l => splitBasis(l).items.map(i => basisItem(i).kind)));
  assert.deepEqual([...kinds].sort(), ['calculation', 'module', 'source']);
  assert.deepEqual(splitBasis(lines[0]).items, ['NBG_2025-03-31_annual-report.pdf, page 41', 'calculation K1']);
  assert.deepEqual(basisItem(splitBasis(lines[2]).items[0]), {kind: 'source', file: 'NBG_2025-03-31_annual-report.pdf', page: 43, pageEnd: 45});
});

test('earlierBasis moves a citation ending a sentence or the paragraph, with only its preceding space', () => {
  assert.deepEqual(earlierBasis('Cash was strong [CP-1: D4]. Next sentence [CP-2: F1].'), {body: 'Cash was strong. Next sentence.', items: ['[CP-1: D4]', '[CP-2: F1]']});
  assert.deepEqual(earlierBasis('Cash was 5. [CP-1: D4] Next sentence.'), {body: 'Cash was 5. Next sentence.', items: ['[CP-1: D4]']});
  assert.deepEqual(earlierBasis('No stop [x]'), {body: 'No stop', items: ['[x]']});
  assert.deepEqual(earlierBasis('Line one.\nLine two [x]'), {body: 'Line one.\nLine two', items: ['[x]']});
  assert.deepEqual(earlierBasis('Two  spaces [x].  Next'), {body: 'Two  spaces.  Next', items: ['[x]']});
  assert.deepEqual(earlierBasis('Rose [a] [b].'), {body: 'Rose.', items: ['[a]', '[b]']});
});

test('earlierBasis moves chips like 【4:2†source】 verbatim', () => {
  assert.deepEqual(earlierBasis('Interest was paid.【4:2†source】'), {body: 'Interest was paid.', items: ['【4:2†source】']});
  assert.deepEqual(earlierBasis('Interest was paid 【4:2†source】. Debt rose.'), {body: 'Interest was paid. Debt rose.', items: ['【4:2†source】']});
});

test('earlierBasis leaves a citation in mid-sentence and text without citations unchanged', () => {
  for (const same of ['Cash [CP-1: D4] was strong.', 'Plain text, nothing cited.', 'An array a[0] is not cited here but a[0] and more.']) {
    assert.deepEqual(earlierBasis(same), {body: same, items: []});
  }
});

const run = (folder, asOf, started) => ({folder, asOf, record: {steps: started ? [{module: 'CP-0', started}] : []}});

test('historyRows orders by as-of date, then start time descending, then folder', () => {
  const runs = [
    run('r-b', '2025-03-31', '2026-11-02T10:00:00Z'),
    run('r-d', '2025-03-31', null),
    run('r-e', '2024-12-31', '2026-11-09T10:00:00Z'),
    run('r-a', '2025-03-31', '2026-11-05T10:00:00Z'),
    run('r-c', '2025-03-31', null),
    run('r-f', '2025-06-30', null),
    run('r-0', '2025-03-31', '2026-11-02T10:00:00Z'),
  ];
  const before = runs.map(r => r.folder);
  assert.deepEqual(historyRows(runs).map(r => r.folder), ['r-f', 'r-a', 'r-0', 'r-b', 'r-c', 'r-d', 'r-e']);
  assert.deepEqual(runs.map(r => r.folder), before);
  assert.deepEqual(historyRows([{folder: 'x', asOf: '2025-03-31'}]).map(r => r.folder), ['x']);
});

test('nearestDates returns the next n items on or after the as-of date, ascending', () => {
  const dates = ['2025-12-15', '2024-12-31', '2025-05-15', '2026-03-31', '2025-01-31', '2025-03-31', '2025-09-30', '2025-06-30', '2025-11-14'];
  const items = dates.map(date => ({date}));
  assert.deepEqual(nearestDates(items, '2025-03-31').map(i => i.date), ['2025-03-31', '2025-05-15', '2025-06-30', '2025-09-30', '2025-11-14']);
  assert.deepEqual(nearestDates(items, '2025-03-31', 2).map(i => i.date), ['2025-03-31', '2025-05-15']);
  assert.deepEqual(nearestDates(items, '2026-01-01').map(i => i.date), ['2026-03-31']);
  assert.deepEqual(nearestDates(items, '2027-01-01'), []);
});

test('nearestDates ignores items without a day date and keeps input order for equal dates', () => {
  const items = [{date: '2025-Q3', id: 1}, {date: '2025', id: 2}, {date: '2025-06-30', id: 3}, {date: '2025-06-30', id: 4}, {id: 5}];
  assert.deepEqual(nearestDates(items, '2025-01-01').map(i => i.id), [3, 4]);
});

test('figureSpans: only an ISO currency code is a prefix', () => {
  const t = text => figureSpans(text).map(f => f.text);
  assert.deepEqual(t('The AGM 2025 approved the dividend.'), []);
  assert.deepEqual(t('Leases under IAS 17 were restated.'), []);
  assert.deepEqual(t('The LTM 2024 figures were restated.'), []);
  assert.deepEqual(t('The ECB 2024 stress test passed.'), []);
  assert.deepEqual(t('Net debt was USD 1,250 million.'), ['USD 1,250 million']);
});

test('earlierBasis moves a citation written straight after sentence punctuation', () => {
  assert.deepEqual(earlierBasis('Revenue rose.[CP-1: D4] Margin fell.'), {body: 'Revenue rose. Margin fell.', items: ['[CP-1: D4]']});
  assert.deepEqual(earlierBasis('Interest was paid.【4:2†source】【4:3†source】 Debt rose.'), {body: 'Interest was paid. Debt rose.', items: ['【4:2†source】', '【4:3†source】']});
  assert.deepEqual(earlierBasis('**[Insufficient Information]** for the point.'), {body: '**[Insufficient Information]** for the point.', items: []});
});

test('pathwayTitle reads the id as words, first word capitalised; no id is null', () => {
  assert.equal(pathwayTitle('credit_snapshot'), 'Credit snapshot');
  assert.equal(pathwayTitle('full-credit_review'), 'Full credit review');
  assert.equal(pathwayTitle(null), null);
  assert.equal(pathwayTitle(''), null);
});

test('runModuleCodes lists the modules that hold an output in record order, then the unrecorded ones', () => {
  const entry = outputs => ({outputs, default: outputs[0] || null});
  const run = {
    modules: {'CP-2': entry(['a']), 'CP-0': entry(['b']), 'CP-9': entry([]), 'CP-1': entry(['c']), 'CP-3': entry(['d'])},
    record: {steps: [{module: 'CP-0'}, {module: 'CP-1'}, {module: 'CP-9'}, {module: 'CP-2'}]},
  };
  assert.deepEqual(runModuleCodes(run), ['CP-0', 'CP-1', 'CP-2', 'CP-3']);
  assert.deepEqual(runModuleCodes({modules: {'CP-1': entry(['c']), 'CP-0': entry(['b'])}}), ['CP-1', 'CP-0']);
  assert.deepEqual(runModuleCodes({}), []);
});

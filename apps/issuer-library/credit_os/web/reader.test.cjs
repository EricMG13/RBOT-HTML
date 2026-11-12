'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {readerPassages, isNewFormat, earlierFormatRun, blocked, splitBasis, basisItem, inspectorItems, uniqueChips, figureSpans, normaliseLimitation, earlierBasis, historyRows, pathwayTitle, runModuleCodes, nearestDates, inspectorBasisBlock} = require('./reader.js');

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
  assert.equal(blocked(newFormat('Not assessable: no forecast.'), {established: true}), true);
  assert.equal(blocked(newFormat('Not assessable: no forecast.\n\nSecond paragraph.'), undefined), true);
  assert.equal(blocked(newFormat('Liquidity is not assessable: no forecast.'), {established: false}), false, 'a mid-sentence mention is not the marker');
  assert.equal(blocked(newFormat('Liquidity is Not Assessable here.'), undefined), false);
  assert.equal(blocked(newFormat('not assessable: wrong case.'), undefined), false, 'exact case');
  assert.equal(blocked(newFormat(' Not assessable: leading space.'), undefined), false, 'exact start of the text');
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

test('splitBasis drops the final full stop even when white space follows it', () => {
  assert.deepEqual(splitBasis('Text.\nBasis: a.pdf, page 4. ').items, ['a.pdf, page 4']);
  assert.deepEqual(splitBasis('Text.\nBasis: a.pdf; b.pdf.\t').items, ['a.pdf', 'b.pdf']);
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
  for (const odd of ['NBG_2025-03-31_annual-report.pdf, pages 43-x', 'see note 3.5', 'Liquidity (not a code)', 'calculation', 'management said so']) {
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
  assert.deepEqual(earlierBasis('No stop [D4]'), {body: 'No stop', items: ['[D4]']});
  assert.deepEqual(earlierBasis('Line one.\nLine two [D4]'), {body: 'Line one.\nLine two', items: ['[D4]']});
  assert.deepEqual(earlierBasis('Two  spaces [D4].  Next'), {body: 'Two  spaces.  Next', items: ['[D4]']});
  assert.deepEqual(earlierBasis('Rose [D1] [D2].'), {body: 'Rose.', items: ['[D1]', '[D2]']});
});

test('earlierBasis moves only bracketed text that looks like a citation: module code, page marker, register code, dagger or the 【】 form', () => {
  for (const cite of ['[CP-1: D1]', '[K, p.41]', '[K, pp. 41-43]', '[Annual report, page 12]', '[F1]', '[C9, D4]', '[4:2†source]', '【4:2】']) {
    assert.deepEqual(earlierBasis(`Cash rose. ${cite}`), {body: 'Cash rose.', items: [cite]}, cite);
  }
  for (const word of ['[sic]', '[TBD]', '[emphasis added]', '[Insufficient Information]', '[●]']) {
    const text = `The quarter was called transformative ${word}. Margins rose.`;
    assert.deepEqual(earlierBasis(text), {body: text, items: []}, word);
  }
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

test('nearestDates ignores an item with no date or a date that is not a day, month, quarter or year, and keeps input order for equal dates', () => {
  const items = [{date: 'sometime', id: 1}, {date: '2025-06-30', id: 3}, {date: '2025-06-30', id: 4}, {id: 5}, {date: '2025-13', id: 6}, {date: '2025-Q5', id: 7}];
  assert.deepEqual(nearestDates(items, '2025-01-01').map(i => i.id), [3, 4]);
});

test('nearestDates lists after the day-dated items those dated only to a month, quarter or year whose period ends on or after the as-of date, in the one nearest-first ordering', () => {
  const items = [{date: '2025-Q3', id: 'q3'}, {date: '2025', id: 'y'}, {date: '2025-06-30', id: 'd'}, {date: '2025-03', id: 'mar'}, {date: '2025-02', id: 'feb'}, {date: '2024', id: 'old'}, {date: '2025-Q1', id: 'q1'}];
  // As of 2025-03-31: February and 2024 have ended; March and Q1 end on that day; Q3 ends 2025-09-30; the year ends 2025-12-31.
  // One ordering by day or period end: mar and q1 (03-31, input order), d (06-30), q3 (09-30), y (12-31).
  assert.deepEqual(nearestDates(items, '2025-03-31').map(i => i.id), ['mar', 'q1', 'd', 'q3', 'y']);
  assert.deepEqual(nearestDates(items, '2025-04-01').map(i => i.id), ['d', 'q3', 'y']);
});

test('nearestDates shows five items in total, day-dated and period-dated merged, nearest first; a tie keeps day-dated before period-dated, then input order', () => {
  // As of 2025-03-31. Period ends: 2025-04 -> 04-30, 2025-Q2 -> 06-30, 2025-07 -> 07-31.
  const days = ['01', '02', '03', '04', '05', '06'].map(day => ({date: `2025-07-${day}`, id: day}));
  const periods = [{date: '2025-07', id: 'jul'}, {date: '2025-04', id: 'apr'}, {date: '2025-Q2', id: 'q2'}];
  assert.deepEqual(nearestDates([...days, ...periods], '2025-03-31').map(i => i.id), ['apr', 'q2', '01', '02', '03']);
  assert.equal(nearestDates([...days, ...periods], '2025-03-31').length, 5);
  // A day equal to a period end sorts before it; two periods ending the same day keep input order.
  const tie = [{date: '2025-Q2', id: 'q2'}, {date: '2025-06', id: 'jun'}, {date: '2025-06-30', id: 'day'}];
  assert.deepEqual(nearestDates(tie, '2025-03-31').map(i => i.id), ['day', 'q2', 'jun']);
});

test('splitBasis and basisItem: an ASCII hyphen page range reads like an en dash', () => {
  assert.deepEqual(basisItem('Q3.pdf, pages 43-45'), {kind: 'source', file: 'Q3.pdf', page: 43, pageEnd: 45});
  assert.deepEqual(basisItem('Q3.pdf, pages 43–45'), {kind: 'source', file: 'Q3.pdf', page: 43, pageEnd: 45});
});

test('basisItem used as a map callback (its second argument is an index) reads as with no list', () => {
  assert.deepEqual(['a.pdf, page 2'].map(basisItem), [{kind: 'source', file: 'a.pdf', page: 2}]);
});

test('splitBasis keeps a known file name containing "; " whole; without the list the split is as before', () => {
  const text = 'T.\nBasis: Q3 results; final.pdf, page 4; other.pdf';
  assert.deepEqual(splitBasis(text, ['Q3 results; final.pdf']).items, ['Q3 results; final.pdf, page 4', 'other.pdf']);
  assert.deepEqual(splitBasis(text).items, ['Q3 results', 'final.pdf, page 4', 'other.pdf']);
  assert.deepEqual(splitBasis(text, ['unrelated.pdf']).items, ['Q3 results', 'final.pdf, page 4', 'other.pdf']);
  assert.deepEqual(basisItem('Q3 results; final.pdf, page 4', ['Q3 results; final.pdf']), {kind: 'source', file: 'Q3 results; final.pdf', page: 4});
});

test('inspectorItems: a "; " file name never resolves to another file\'s chips; an extension-less name resolves only on an exact known name', () => {
  const split = {kind: 'issuer_page', file: 'Q3 results; final.pdf', page: 4};
  const other = {kind: 'issuer_page', file: 'final.pdf', page: 4};
  const bare = {kind: 'issuer_page', file: 'Annual report 2024', page: 4};
  const ctx = {sections: [], chips: [split, other, bare], ran: () => false};
  const items = inspectorItems('x\nBasis: Q3 results; final.pdf, page 4', ctx);
  assert.deepEqual(items.map(i => i.raw), ['Q3 results; final.pdf, page 4']);
  assert.deepEqual(items[0].chips, [split], 'the whole name resolves to its own chips, not final.pdf\'s');
  const noExt = inspectorItems('x\nBasis: Annual report 2024, page 4; Annual report 2023, page 4', ctx);
  assert.deepEqual(noExt.map(i => i.kind), ['source', 'text']);
  assert.deepEqual(noExt[0].chips, [bare]);
});

test('inspectorItems: a run supplying "Q3 results; final.pdf" whose key holds only a final.pdf page-4 chip: the fragment does not take final.pdf\'s chip', () => {
  const other = {kind: 'issuer_page', file: 'final.pdf', page: 4};
  const ctx = {sections: [], chips: [other], files: ['Q3 results; final.pdf'], ran: () => false};
  const items = inspectorItems('x\nBasis: Q3 results; final.pdf, page 4', ctx);
  assert.deepEqual(items.map(i => [i.raw, i.chips]), [['Q3 results; final.pdf, page 4', []]]);
});

test('screen.js passes the run\'s supplied file names, so a "; " file name is not split into another file\'s chips', () => {
  const other = {kind: 'issuer_page', file: 'final.pdf', page: 4};
  const text = 'Cash is thin.\nBasis: Q3 results; final.pdf, page 4';
  const html = inspectorDrawnFor(0, 0, [other], {sources: [{name: 'Q3 results; final.pdf'}], unused: [], unrecorded: []}, text);
  assert.ok(html.includes('<li><strong>Q3 results; final.pdf</strong>, page 4</li>'), html);
  assert.ok(html.includes('Other citations') && html.includes('final.pdf p.4'), 'the final.pdf chip is listed apart, not taken by the item');
});

test('an earlier-format citation keeps class basis (styling); the page\'s name rewriting now reads inside it (no module code is shown)', () => {
  const html = inspectorBasisBlock('Leverage is 5.2x [CP-1 T3].', true, {sections: [], chips: [], ran: () => false}, () => '');
  assert.match(html, /^<div class="basis">/);
  assert.ok(html.includes('<li>[CP-1 T3]</li>'));
  const screen = fs.readFileSync(path.join(__dirname, 'screen.js'), 'utf8');
  assert.ok(screen.includes("parent.closest('.ref,.excerpt')") && !screen.includes("'.ref,.excerpt,.basis"), 'nameCodes reads a Basis block: only register references and source excerpts stay as written');
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

// ---- Prose and tables (decisions 7 and 14, H3, H4, H7). Expected strings are written by hand.
const {paragraphView, paragraphBody, sectionBodyHtml, tableView, calculationRow} = require('./reader.js');
const visible = html => html.replace(/<[^>]+>/g, '');

test('paragraphView: each figure is a button wrapping exactly its text; the Basis line is not printed', () => {
  const {html} = paragraphView('Net debt of USD 1,390 million is 4.2x EBITDA, up 38%.\nBasis: A.pdf, page 4; calculation K1', 'o:7');
  const data = '[&quot;A.pdf, page 4&quot;,&quot;calculation K1&quot;]';
  assert.equal(html, `Net debt of <button type="button" class="figure" data-paragraph="o:7" data-basis="${data}" data-figure="0">USD 1,390 million</button> is `
    + `<button type="button" class="figure" data-paragraph="o:7" data-basis="${data}" data-figure="1">4.2x</button> EBITDA, up `
    + `<button type="button" class="figure" data-paragraph="o:7" data-basis="${data}" data-figure="2">38%</button>.`);
  assert.equal(visible(html), 'Net debt of USD 1,390 million is 4.2x EBITDA, up 38%.');
  assert.ok(!html.includes('Basis:'));
});

test('paragraphView: a figure inside bold keeps its markup and its exact text', () => {
  const {html} = paragraphView('Leverage is **4.2x** net.\nBasis: A.pdf', 'o:1');
  assert.ok(html.startsWith('Leverage is <strong><button type="button" class="figure" data-paragraph="o:1"'));
  assert.ok(html.includes('data-figure="0">4.2x</button></strong> net.'));
});

test('paragraphView: no figure and a Basis line gives one quiet Basis button at the end, named by the first words', () => {
  const {html} = paragraphView('Liquidity rests on an undrawn revolver that steps down over the coming year.\nBasis: Q4.pdf, page 7', 'o:9');
  assert.equal(html, 'Liquidity rests on an undrawn revolver that steps down over the coming year. '
    + '<button type="button" class="basis-link" data-paragraph="o:9" data-basis="[&quot;Q4.pdf, page 7&quot;]" aria-label="Basis for paragraph: Liquidity rests on an undrawn revolver that steps">Basis</button>');
  assert.equal(visible(html), 'Liquidity rests on an undrawn revolver that steps down over the coming year. Basis');
});

test('paragraphView: no Basis items and no chips means no button, even with figures; chips alone make the control', () => {
  assert.equal(paragraphView('Leverage is 4.2x.', 'o:2').html, 'Leverage is 4.2x.');
  assert.equal(paragraphView('No source here.', 'o:3').html, 'No source here.');
  assert.ok(paragraphView('Leverage is 4.2x.', 'o:2', {chips: 1}).html.includes('class="figure"'));
  assert.ok(paragraphView('No figure here.', 'o:3', {chips: 2}).html.includes('class="basis-link"'));
});

test('paragraphView: a list item loses its marker and the item flag is set; text is escaped', () => {
  const view = paragraphView('- Debt <b> & 12%\nBasis: A.pdf', 'o:4');
  assert.equal(view.item, true);
  assert.equal(visible(view.html), 'Debt &lt;b&gt; &amp; 12%');
  assert.ok(!view.html.includes('<b>'));
});

test('paragraphView, earlier format: trailing citations move behind one Basis button, the wording is otherwise untouched, no figure buttons', () => {
  const {html} = paragraphView('Cash interest was 1,158 in FY2024 [K, page:123]. A mid-sentence [note] stays.', 'o:5', {earlier: true});
  assert.equal(visible(html), 'Cash interest was 1,158 in FY2024. A mid-sentence [note] stays. Basis');
  assert.ok(html.includes('data-basis="[&quot;[K, page:123]&quot;]"') && !html.includes('class="figure"'));
  // Ruling (a): no moved citation and no chip in the build (the handoff-row chip is not one) means no Basis button.
  assert.equal(paragraphView('Plain earlier paragraph.', 'o:6', {earlier: true}).html, 'Plain earlier paragraph.');
  assert.ok(paragraphView('Plain earlier paragraph.', 'o:6', {earlier: true, chips: 1}).html.includes('class="basis-link"'), 'a chip of the build opens from it');
});

test('paragraphBody: the Basis items and the body on one line', () => {
  assert.deepEqual(paragraphBody('- One\ntwo\nBasis: A.pdf; B.pdf, page 2.'), {item: true, body: 'One two', items: ['A.pdf', 'B.pdf, page 2']});
});

test('sectionBodyHtml: list items share one list, paragraphs stand alone, tables only when asked, tables as written with a row control only where chips exist', () => {
  const section = {heading: 'Findings', level: 3, line: 1, blocks: [
    {type: 'text', line: 2, end: 2, text: '- A 5%\nBasis: X.pdf'}, {type: 'text', line: 4, end: 4, text: '- B'},
    {type: 'text', line: 6, end: 6, text: 'Plain.'},
    {type: 'table', line: 8, headers: ['Item', 'Source'], rows: [{line: 10, cells: ['Debt', 'X.pdf, page 3']}, {line: 11, cells: ['Cash', 'X.pdf, page 4']}]},
  ]};
  const ctx = {id: 'o', tables: true, chips: key => (key === 'o:11' ? 1 : 0), caption: heading => heading};
  const html = sectionBodyHtml(section, ctx);
  assert.ok(html.startsWith('<ul class="passage-list"><li>A <button type="button" class="figure" data-paragraph="o:2"'));
  assert.ok(html.includes('</button></li><li>B</li></ul><p class="passage-text">Plain.</p><div class="table-card">'));
  assert.ok(html.includes('<thead><tr><th scope="col">Item</th><th scope="col">Source</th></tr></thead>'), 'the handoff\'s own columns, none added');
  assert.equal((html.match(/<th /g) || []).length, 2);
  assert.ok(html.includes('<td>Debt</td><td>X.pdf, page 3</td>') && html.includes('<td>Cash <button type="button" class="basis-link" data-paragraph="o:11"'));
  assert.ok(!sectionBodyHtml(section, {...ctx, tables: false}).includes('<table>'));
});

test('tableView (H4): a missing cell is drawn as written, never "n.a."; a numeric column aligns', () => {
  const html = tableView('T', {headers: ['Item', 'Value'], rows: [{line: 1, cells: ['A', '1,200']}, {line: 2, cells: ['B', '—']}]}, {id: 'o', chips: () => 0});
  assert.ok(html.includes('<th scope="col" class="num">Value</th>') && html.includes('<td class="num">1,200</td>'));
  assert.ok(html.includes('<td class="num">—</td>') && !html.includes('n.a.'));
  const blank = tableView('T', {headers: ['Item', 'Value'], rows: [{line: 1, cells: ['A', '']}, {line: 2, cells: ['B', 'Not supplied']}]}, {id: 'o', chips: () => 0});
  assert.ok(blank.includes('<td></td>') && blank.includes('<td>Not supplied</td>') && !blank.includes('n.a.'));
});

test('calculationRow: the row of the Calculations table whose ID column equals the id, headers and cells as written', () => {
  const sections = [
    {heading: 'Findings', level: 2, line: 1, blocks: [{type: 'table', line: 2, headers: ['ID', 'x'], rows: [{line: 3, cells: ['K1', 'wrong table']}]}]},
    {heading: 'Calculations', level: 2, line: 5, blocks: [{type: 'table', line: 6, headers: ['Calculation ID', 'Name', 'Steps'], rows: [{line: 8, cells: ['K1', 'Net debt', 'a less b']}, {line: 9, cells: ['K2', 'Cover', 'c over d']}]}]},
    {heading: 'Detail', level: 3, line: 11, blocks: [{type: 'table', line: 12, headers: ['id', 'Result'], rows: [{line: 14, cells: ['K3', '4.2x']}]}]},
    {heading: 'Gaps', level: 2, line: 16, blocks: [{type: 'table', line: 17, headers: ['ID'], rows: [{line: 19, cells: ['K4']}]}]},
  ];
  assert.deepEqual(calculationRow(sections, 'K2'), {headers: ['Calculation ID', 'Name', 'Steps'], cells: ['K2', 'Cover', 'c over d'], line: 9});
  assert.deepEqual(calculationRow(sections, 'K3'), {headers: ['id', 'Result'], cells: ['K3', '4.2x'], line: 14}, 'an H3 child of Calculations, header ID in any case');
  assert.equal(calculationRow(sections, 'K4'), null, 'a table outside Calculations is not searched');
  assert.equal(calculationRow(sections.slice(0, 1), 'K1'), null);
  assert.equal(calculationRow(sections, 'K9'), null);
});

test('inspectorItems: a paragraph\'s Basis items resolved in the handoff\'s order (the list the inspector draws)', () => {
  const sections = [{heading: 'Calculations', level: 2, line: 5, blocks: [{type: 'table', line: 6, headers: ['ID', 'Steps'], rows: [{line: 8, cells: ['K1', 'a less b']}]}]}];
  const chip = {kind: 'issuer_page', file: 'A.pdf', page: 7};
  const other = {kind: 'issuer_page', file: 'A.pdf', page: 8};
  const ctx = {sections, chips: [chip, other], ran: code => code === 'CP-1'};
  const items = inspectorItems('- Debt is 4.2x.\nBasis: A.pdf, page 7; B.pdf; calculation K1; calculation K9; Foundation (CP-1); Ghost (CP-9Z); odd text.', ctx);
  assert.deepEqual(items.map(i => i.raw), ['A.pdf, page 7', 'B.pdf', 'calculation K1', 'calculation K9', 'Foundation (CP-1)', 'Ghost (CP-9Z)', 'odd text']);
  assert.deepEqual(items.map(i => i.kind), ['source', 'source', 'calculation', 'calculation', 'module', 'module', 'text']);
  assert.deepEqual(items[0].chips, [chip], 'a page-named source takes only that page\'s chips');
  assert.deepEqual(items[1].chips, [], 'another file\'s chips are not taken');
  assert.deepEqual(inspectorItems('x\nBasis: A.pdf', ctx)[0].chips, [chip, other], 'a source without a page takes the file\'s chips');
  assert.deepEqual(items[2].row, {headers: ['ID', 'Steps'], cells: ['K1', 'a less b'], line: 8});
  assert.equal(items[3].row, null);
  assert.deepEqual([items[4].ran, items[5].ran], [true, false]);
  assert.deepEqual(inspectorItems('No basis here.', ctx), []);
});

// The inspector's drawn Basis list: screen.js paragraphBasisHtml (the real text, stand-ins for its globals) over the synthetic CP-2 handoff.
// Expected <li> items are written by hand from the Basis lines of apps/issuer-library/fixtures/synthetic-new-format/SYNTHETIC-CP-2.md (lines 18, 23, 25).
function inspectorDrawnFor(firstLine, lastLine, chips = [], evidence = {}, paragraphText = null) {
  const text = fs.readFileSync(path.join(__dirname, 'screen.js'), 'utf8');
  const start = text.indexOf('function chipSection('), end = text.indexOf('function showInspector(');
  const reader = require('./reader.js');
  const draw = new Function('esc', 'icon', 'inspectorItem', 'inspectorItemHtml', 'inspectorBasisBlock', 'uniqueChips', 'isNewFormat', 'paragraphBody', 'figureSpans', 'defaultOutput', 'moduleHref', 'contexts', `${text.slice(start, end)}; return paragraphBasisHtml;`)(
    reader.escapeHtml, n => `<img src="${n}">`, reader.inspectorItem, reader.inspectorItemHtml, reader.inspectorBasisBlock, reader.uniqueChips, reader.isNewFormat, reader.paragraphBody, reader.figureSpans, code => code === 'CP-1', code => `#/${code}`, {r: {evidence}});
  const lines = fixture('CP-2');
  const calculations = {heading: 'Calculations', level: 2, line: 44, blocks: [{type: 'table', line: 46, headers: ['ID', 'Calculation', 'Steps', 'Result'], rows: [{line: 48, cells: ['K1', 'Net debt to EBITDA', 'Gross debt 1,700 less cash 310 gives net debt 1,390; divided by EBITDA 331', '4.2x']}]}]};
  const paragraph = paragraphText ?? lines.slice(firstLine - 1, lastLine).join('\n');
  return draw('k', {text: paragraph}, {sections: [calculations, ...newFormat('b')], run: 'r', href: '../runs/r/d/CP-2.md', source: 'd/CP-2.md'}, 'p', chips);
}
const basisList = lis => `<div class="basis"><h3>Basis</h3><ul class="basis-items">${lis.join('')}</ul></div>`;

test('the inspector draws every Basis item of the CP-2 bottom line in the handoff order: source with page, then the calculation row', () => {
  assert.equal(inspectorDrawnFor(17, 18), basisList([
    '<li><strong>NBG_2025-03-31_annual-report.pdf</strong>, page 41</li>',
    '<li>Calculation K1<dl class="calculation-row"><div><dt>ID</dt><dd>K1</dd></div><div><dt>Calculation</dt><dd>Net debt to EBITDA</dd></div><div><dt>Steps</dt><dd>Gross debt 1,700 less cash 310 gives net debt 1,390; divided by EBITDA 331</dd></div><div><dt>Result</dt><dd>4.2x</dd></div></dl></li>',
  ]));
});

test('R5: an upstream-handoff Basis item shows its written name only, linked or not run; its link target is unchanged', () => {
  const {inspectorItemHtml, inspectorItem} = require('./reader.js'), deps = {moduleHref: code => `#/${code}`, icon: n => `<img src="${n}">`};
  const item = ran => inspectorItem('Liquidity (CP-2D)', {sections: [], chips: [], ran: () => ran});
  assert.equal(inspectorItemHtml(item(true), deps), '<li><a class="text-action" href="#/CP-2D">Liquidity<img src="arrow-right"></a></li>');
  assert.equal(inspectorItemHtml(item(false), deps), '<li>Liquidity<span class="small"> · Not run in this run</span></li>');
});

test('the inspector draws two sources, then a page range and an upstream module, for the CP-2 key findings', () => {
  assert.equal(inspectorDrawnFor(22, 23), basisList([
    '<li><strong>NBG_2024-12-31_Q4-results.pdf</strong></li>',
    '<li><strong>NBG_2025-03-31_annual-report.pdf</strong>, page 41</li>',
  ]));
  assert.equal(inspectorDrawnFor(24, 25), basisList([
    '<li><strong>NBG_2025-03-31_annual-report.pdf</strong>, pages 43–45</li>',
    '<li><a class="text-action" href="#/CP-1">Financial foundation<img src="arrow-right"></a></li>',
  ]));
});

test('an earlier-format paragraph lists its citations in a div of class basis (so name rewriting skips it)', () => {
  const html = require('./reader.js').inspectorBasisBlock('Cash rose. [CP-1: D4]', true, {sections: [], chips: [], ran: () => false}, () => '');
  assert.equal(html, '<div class="basis"><h3>Basis</h3><ul class="basis-items"><li>[CP-1: D4]</li></ul></div>');
});

test('screen.js draws each resolved Basis item as it is: it does not resolve an item again or rebuild the drawing helpers per item', () => {
  const text = fs.readFileSync(path.join(__dirname, 'screen.js'), 'utf8');
  const draw = text.slice(text.indexOf('function basisItemHtml('), text.indexOf('// The inspector part for a paragraph'));
  assert.ok(!draw.includes('inspectorItem(') && !draw.includes('chipSection:'), draw);
  assert.equal((text.match(/inspectorItemHtml\(/g) || []).length, 1);
});

test('paragraphView: text holding the private-use marker characters is drawn as written, one button per figure', () => {
  for (const digit of ['0', '7']) {
    const html = paragraphView(`Code \uE000${digit}\uE001 then 4.2x leverage.\nBasis: a.pdf`, 'k:1').html;
    assert.equal((html.match(/class="figure"/g) || []).length, 1);
    assert.ok(html.includes(`Code \uE000${digit}\uE001 then <button`), html);
    assert.ok(html.includes('>4.2x</button> leverage.'));
  }
  const plain = paragraphView('Code 7 then 4.2x leverage.\nBasis: a.pdf', 'k:2').html;
  assert.ok(plain.startsWith('Code 7 then <button') && (plain.match(/class="figure"/g) || []).length === 1);
});

test('uniqueChips: a chip the build holds twice is listed once, in first-seen order; distinct chips stay', () => {
  const a = {kind: 'issuer_page', file: 'A.pdf', page: 7, quote: 'x'};
  const b = {kind: 'issuer_page', file: 'A.pdf', page: 8, quote: 'x'};
  assert.deepEqual(uniqueChips([a, b, {...a}, {kind: 'gap', label: 'Citation gap'}, {kind: 'gap', label: 'Citation gap'}, {...b}]), [a, b, {kind: 'gap', label: 'Citation gap'}]);
  assert.deepEqual(uniqueChips([]), []);
});

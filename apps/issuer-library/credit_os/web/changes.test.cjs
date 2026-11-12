'use strict';
// The Changes tab's rendering. Shapes are store.py's (section {heading, level, line, blocks[]}; table block {type, headers, rows[{line, cells}]}) and
// the pack's (schema cpos-changes/2). Expected values are literals hand-copied from the pack of the TransDigm comparison and from CP-8's handoff for it;
// nothing is derived by calling the code under test.
const test = require('node:test');
const assert = require('node:assert/strict');
const {changesState, measureVerdict, differenceText, analysisPart, withUnit, leadBottom, changesHtml, FIRST_RUN} = require('./changes.js');

const fmtDate = iso => ({'2024-09-30': '30 September 2024', '2025-03-31': '31 March 2025', '2023-09-30': '30 September 2023'}[iso] || iso);
const text = (body, line = 1) => ({type: 'text', line, end: line, text: body});
const table = (headers, ...rows) => ({type: 'table', headers, rows: rows.map((cells, i) => ({line: i + 1, cells}))});
const h3 = (heading, ...blocks) => ({heading, level: 3, line: 1, blocks});
const side = (value, period, unit = 'x') => ({label: 'm', unit, value, period, definition: 'd', definition_resolved: false, definition_written: null});
const measure = (key, label, unit, comparable, prior, current, difference, extra = {}) => ({key, label, unit, comparable, reason: 'the label or definition text differs; CP-8 judges', prior, current, difference, same_period: true, ...extra});

const PACK = {
  schema: 'cpos-changes/2',
  prior: {run: 'cpos-tdg-sol-medium-all-001', as_of: '2024-09-30', pathway: 'credit_snapshot', format: 'earlier', methods_changed: []},
  current: {as_of: '2024-09-30', pathway: 'credit_snapshot', format: 'current'},
  measures: [
    measure('leverage', 'Total debt / EBITDA', 'x', 'judge', side('6.57', 'FY2024 / 2024-09-30'), side('6.01', 'FY2024'), '-0.56'),
    measure('coverage', 'EBITDA / cash interest', 'x', 'judge', side('3.29', 'FY2024'), side('3.60', 'FY2024'), '0.31'),
    measure('cash', 'Cash', 'US$m', 'judge', side('6261', '2024-09-30', 'US$m'), side('6261', '2024-09-30', 'US$m'), '0'),
  ],
  maturity_profile: {unit: 'US$m', rows: [{period: 'FY2025', prior: '93', current: '93', difference: '0'}, {period: 'FY2028', prior: '6637', current: '6637', difference: '0'}]},
  omitted: {net_debt_change: 'gross debt is not stated in either run'},
  modules: [
    {module: 'CP-0', title: 'Source readiness', ran_prior: true, ran_current: true, prior_bottom_line: 'Begin bounded historical financial work.', current_bottom_line: 'The supplied sources support a bounded snapshot.'},
    {module: 'CP-2E', title: 'Rates, FX and hedging', ran_prior: true, ran_current: false, prior_bottom_line: 'Hedging is partial.', current_bottom_line: null},
  ],
  limitations: {earlier: [{ref: 'E1', module: 'CP-0', text: 'x'}], current: [{ref: 'C1', module: 'CP-1A', text: 'y'}]},
};

const ISSUER_HEAD = ['Measure or fact', 'Earlier', 'Current', 'Cause', 'Effect on the credit view'];
const CP8 = [
  {heading: 'Findings', level: 2, line: 1, blocks: []},
  h3('Bottom line', text('The credit picture is about the same since the earlier run, and the change is the analysis\'s, not the issuer\'s.\nBasis: CP-1 handoff; calculation C01.')),
  h3('Key findings', text('- Cash is unchanged at USD 6,261 million.'), text('- Leverage is 6.01x on EBITDA as defined against 6.57x on reported EBITDA, not comparable.')),
  h3('Contrary evidence and what would change the view', text('A covenant test below 7.0x would change the view.')),
  h3('Limitations', text('The earlier run was in the earlier format.')),
  h3('What changed: the issuer', table(ISSUER_HEAD,
    ['Total debt / EBITDA', '6.57x (FY2024 / 2024-09-30)', '6.01x (FY2024)', 'Unresolved', 'Not comparable: reported EBITDA against EBITDA As Defined.'],
    ['EBITDA / cash interest', '3.29x (FY2024)', '3.60x (FY2024)', 'Unresolved', 'Same definition; coverage rose.'],
    ['Cash', '6,261 US$m (2024-09-30)', '6,261 US$m (2024-09-30)', 'Unresolved', 'Same definition; unchanged at USD 6,261 million.'])),
  h3('What changed: the analysis', table(['Module', 'Status', 'Cause', 'Why'],
    ['Source readiness (CP-0)', 'Unchanged', 'Presentation', 'The headings differ only.'],
    ['Rates, FX and hedging (CP-2E)', 'Not run this time', 'Unresolved', 'Not in the current run.'])),
  h3('Limitations ledger', table(['Earlier ref', 'Current ref', 'Limitation', 'Status', 'What closed it'],
    ['E1', '—', 'An earlier limitation in words.', 'No longer stated', '—'],
    ['E2', '—', 'Another earlier limitation.', 'No longer stated', '—'],
    ['E3', 'C1', 'Carried over.', 'Remaining', '—'],
    ['—', 'C2', 'A current limitation in words.', 'New', '—'])),
];
const here = {key: 'k3', href: '#W-Changes/changes/k3', asOf: '2024-09-30', runId: 'r-now', current: true, bottom: 'Now.', metrics: {}, changes: null, cp8: null};
const base = (over = {}) => ({changes: {lead: 'CP-2', pack: PACK, note: null, problem: null}, cp8: CP8, pathway: 'Credit snapshot', fmtDate, runs: [here], ...over});
const count = (html, needle) => html.split(needle).length - 1;

test('a run with no comparison is a first run: the one line and nothing else', () => {
  const expected = `<div class="changes"><p class="changes-first">${FIRST_RUN}</p></div>`;
  assert.equal(FIRST_RUN, 'First run of this pathway');
  assert.equal(changesHtml(base({changes: {lead: 'CP-2', first_run: true, pack: null, note: null, problem: null}})), expected);
  assert.equal(changesState({pack: null, note: null, problem: 'is not valid JSON'}), 'unreadable');
  assert.equal(changesState({pack: PACK, note: 'changes: not produced — why', problem: null}), 'not_produced');
});

test('a full Changes tab: heading, CP-8 passages verbatim, the issuer, the analysis, the ledger counts, over time', () => {
  const html = changesHtml(base());
  assert.ok(html.includes('<h2 class="changes-heading">Since 30 September 2024 · Credit snapshot</h2>'));
  // Part 1: the passage text as written; the Basis line is a source line, not part of the sentence.
  assert.ok(html.includes('The credit picture is about the same since the earlier run, and the change is the analysis&#39;s, not the issuer&#39;s.<small class="changes-basis">Basis: CP-1 handoff; calculation C01</small>'));
  assert.ok(html.includes('<li>Cash is unchanged at USD 6,261 million.</li>'));
  assert.ok(html.includes('Leverage is 6.01x on EBITDA as defined against 6.57x on reported EBITDA, not comparable.'));
  // Part 2: the pack's values with unit and period; the register verbatim.
  assert.ok(html.includes('<td>6.57x (FY2024 / 2024-09-30)</td><td>6.01x (FY2024)</td>'));
  assert.ok(html.includes('<td>6261 US$m (2024-09-30)</td><td>6261 US$m (2024-09-30)</td><td>0 US$m</td>'));
  assert.ok(html.includes('Net debt change is not shown: gross debt is not stated in either run.'));
  assert.ok(html.includes('<th scope="row">FY2028</th><td>6637</td><td>6637</td><td>0</td>'));
  assert.ok(html.includes('Same definition; unchanged at USD 6,261 million.'));
  assert.ok(html.includes('Debt maturities, US$m'));
  // Part 3: one row per pack module, CP-8's status by the code in its first cell.
  assert.equal(count(html, '<details class="change-module">'), 2);
  assert.ok(html.includes('<span class="badge badge-gray change-status">Unchanged</span>'));
  assert.ok(html.includes('<span class="badge badge-gray change-status">Not run this time</span>'));
  assert.ok(html.includes('<small>Current</small>Did not run'));
  assert.ok(html.includes('<p>The supplied sources support a bounded snapshot.</p>'));
  // Part 4: the four counts as one bar (E1, E2 no longer stated; E3/C1 remaining; C2 new), then the ledger.
  assert.ok(html.includes('aria-label="Limitations: Closed 0, Remaining 1, New 1, No longer stated 2"'));
  assert.equal(count(html, 'class="ledger-bar"'), 1);
  assert.ok(html.includes('<td>An earlier limitation in words.</td>'));
  // Part 5 is present.
  assert.ok(html.includes('id="changes-over-time"'));
});

test('a measure that is not comparable shows both values, no difference, no joining line and no arrow', () => {
  const html = changesHtml(base());
  // Total debt / EBITDA: CP-8 says Not comparable although the pack holds a difference of -0.56.
  assert.ok(!html.includes('-0.56'), 'its difference is printed nowhere');
  assert.ok(html.includes('<strong>Not comparable</strong><small>Not comparable: reported EBITDA against EBITDA As Defined.</small>'));
  assert.ok(html.includes('Earlier 6.57x (FY2024 / 2024-09-30) · Current 6.01x (FY2024) · Not comparable'));
  // Cash (same period, difference 0) is joined; coverage is one period with two values (0.31) and leverage is Not comparable: no line for either.
  assert.equal(count(html, 'class="dumbbell-link"'), 1);
  assert.ok(!/[←-⇿▲△▼▽⬆⬇]/.test(html), 'no direction arrow anywhere');
  // comparable "no" from the pack itself: unit differs.
  const pack = {...PACK, measures: [measure('leverage', 'Total debt / EBITDA', 'x', 'no', side('6.57', 'FY2024'), side('62', 'FY2024', '%'), null, {reason: 'the units differ'})]};
  const no = changesHtml(base({changes: {lead: 'CP-2', pack, note: null, problem: null}}));
  assert.ok(no.includes('<td>6.57x (FY2024)</td><td>62% (FY2024)</td><td><strong>Not comparable</strong><small>the units differ</small></td>'));
  assert.equal(count(no, 'class="dumbbell-link"'), 0);
});

test('a judge measure without a verdict from CP-8 is left unjudged, with no difference', () => {
  const pack = {...PACK, measures: [PACK.measures[0]]};
  const html = changesHtml(base({changes: {lead: 'CP-2', pack, note: null, problem: null}, cp8: null}));
  assert.ok(html.includes('<strong>Comparability not judged</strong>'));
  assert.ok(!html.includes('-0.56'));
  assert.equal(count(html, 'class="dumbbell-link"'), 0);
  assert.deepEqual(measureVerdict(PACK.measures[2], null), {kind: 'unjudged', label: 'Comparability not judged', reason: 'the label or definition text differs; CP-8 judges'});
  assert.equal(measureVerdict({...PACK.measures[2], comparable: 'yes'}, null).kind, 'comparable');
});

test('a value the pack does not state is shown as not stated, never as zero', () => {
  const pack = {...PACK, measures: [measure('coverage', 'EBITDA / cash interest', 'x', 'no', side('3.29', 'FY2024'), null, null, {reason: 'the current run does not state it'})]};
  const html = changesHtml(base({changes: {lead: 'CP-2', pack, note: null, problem: null}}));
  assert.ok(html.includes('<td>3.29x (FY2024)</td><td>Not stated</td><td><strong>Not comparable</strong>'));
  assert.ok(html.includes('Earlier 3.29x (FY2024) · Current Not stated · Not comparable'));
  assert.equal(count(html, 'class="dumbbell-dot'), 1, 'one point, the stated one');
  assert.equal(withUnit('0', 'US$m'), '0 US$m');
  assert.equal(withUnit('4.51', 'x'), '4.51x');
  assert.equal(withUnit('-0.56', 'x'), '-0.56x');
});

test('a CP-8 that was not produced says so plainly with its recorded reason and shows the pack-derived parts only', () => {
  const note = 'changes: not produced — cpos_live_not_accepted: CP-8 not accepted within bounds';
  const html = changesHtml(base({changes: {lead: 'CP-2', pack: PACK, note, problem: null}, cp8: null}));
  assert.ok(html.includes('The explanation of what changed was not produced for this run.'));
  assert.ok(html.includes('Recorded reason: cpos_live_not_accepted: CP-8 not accepted within bounds'));
  assert.ok(html.includes('Since 30 September 2024 · Credit snapshot'));
  assert.ok(!html.includes('id="changes-what"'), 'no CP-8 passage');
  assert.ok(!html.includes('id="changes-limitations"'), 'no ledger');
  assert.ok(html.includes('id="changes-issuer"') && html.includes('id="changes-analysis"') && html.includes('id="changes-over-time"'));
  assert.equal(count(html, 'Explanation not produced'), 2, 'each module row says so');
  assert.ok(!html.includes('Each change and its cause'));
  assert.ok(!html.includes('-0.56') && !html.includes('0.31'), 'no difference without CP-8’s verdict');
  // The delivery may hold the reason and no pack: the statement and Over time only.
  const bare = changesHtml(base({changes: {lead: 'CP-2', pack: null, note, problem: null}, cp8: null}));
  assert.ok(bare.includes('Since the earlier run · Credit snapshot'));
  assert.ok(bare.includes('Recorded reason: cpos_live_not_accepted'));
  assert.ok(!bare.includes('id="changes-issuer"') && bare.includes('id="changes-over-time"'));
});

test('a pack that could not be read is stated and is never shown as a first run', () => {
  const html = changesHtml(base({changes: {lead: 'CP-2', pack: null, note: null, problem: 'deliveries/x/changes.json is not valid JSON'}, cp8: null}));
  assert.ok(html.includes('The comparison with the earlier run could not be read.'));
  assert.ok(html.includes('deliveries/x/changes.json is not valid JSON'));
  assert.ok(!html.includes(FIRST_RUN));
});

test('handoff and pack text is escaped before it reaches the page', () => {
  const evil = '<script>alert(1)</script><img src=x onerror=alert(2)>';
  const pack = {...PACK, measures: [measure('cash', evil, 'US$m', 'yes', side('1', evil, evil), side('2', 'p', 'US$m'), '1')],
    modules: [{module: 'CP-0', title: evil, ran_prior: true, ran_current: true, prior_bottom_line: evil, current_bottom_line: evil}],
    maturity_profile: {unit: evil, rows: [{period: evil, prior: evil, current: '1', difference: evil}]}, omitted: {net_debt_change: evil}};
  const cp8 = CP8.map(s => (s.heading === 'Bottom line' ? h3('Bottom line', text(evil)) : s.heading === 'Limitations ledger' ? h3('Limitations ledger', table(['Earlier ref', 'Current ref', 'Limitation', 'Status', 'What closed it'], ['E1', '—', evil, evil, evil])) : s));
  const runs = [{...here, bottom: evil, metrics: {cash: {value: evil, unit: evil, period: evil}}}];
  const html = changesHtml(base({changes: {lead: 'CP-2', pack, note: null, problem: null}, cp8, runs, pathway: evil}));
  assert.ok(!html.includes('<script') && !html.includes('<img'), 'no tag of the model’s survives');
  assert.ok(html.includes('&lt;script&gt;alert(1)&lt;/script&gt;'));
  const note = changesHtml(base({changes: {lead: 'CP-2', pack: null, note: `changes: not produced — ${evil}`, problem: null}, cp8: null}));
  assert.ok(!note.includes('<script') && note.includes('&lt;script&gt;'));
  const problem = changesHtml(base({changes: {lead: 'CP-2', pack: null, note: null, problem: evil}, cp8: null}));
  assert.ok(!problem.includes('<script') && !problem.includes('<img'));
});

test('Over time lists every run earliest first; a line joins two points only where the later run compares them under one definition', () => {
  const metric = (value, period) => ({leverage: {value, unit: 'x', period, basis: 'b'}});
  const packOf = (priorRun, comparable, prior, current, pp = 'FY2022', pc = 'FY2023') => ({...PACK, prior: {...PACK.prior, run: priorRun}, measures: [measure('leverage', 'Total debt / EBITDA', 'x', comparable, side(prior, pp), side(current, pc), '0.50', {same_period: false})]});
  const runs = [
    {key: 'a', href: '#a', asOf: '2023-09-30', runId: 'r-a', current: false, bottom: 'Earlier view.', metrics: metric('5.00', 'FY2022'), changes: null, cp8: null},
    {key: 'b', href: '#b', asOf: '2024-09-30', runId: 'r-b', current: false, bottom: null, metrics: metric('5.50', 'FY2023'), changes: {pack: packOf('r-a', 'yes', '5.00', '5.50')}, cp8: null},
    {key: 'c', href: '#c', asOf: '2025-03-31', runId: 'r-c', current: true, bottom: 'Latest view.', metrics: metric('6.00', 'FY2024'), changes: {pack: packOf('r-b', 'yes', '5.50', '6.00', 'FY2023', 'FY2024')}, cp8: null},
  ];
  const lines = html => (/<li><strong>Total debt \/ EBITDA<\/strong>(.*?)<\/li>/.exec(html)[1].match(/<line /g) || []).length;
  const html = changesHtml(base({runs}));
  assert.equal(lines(html), 2, 'both neighbours are compared under one definition by the later run’s pack');
  const over = html.slice(html.indexOf('id="changes-over-time"'));
  assert.ok(over.indexOf('30 September 2023') < over.indexOf('30 September 2024') && over.indexOf('30 September 2024') < over.indexOf('31 March 2025'));
  assert.ok(html.includes('<td>5.00x<small>FY2022</small></td>') && html.includes('<td>6.00x<small>FY2024</small></td>'));
  assert.ok(html.includes('<td>Earlier view.</td>') && html.includes('<td>Not stated</td>') && html.includes('<td>Latest view.</td>'));
  // Not comparable in the later run's pack: points only.
  const apart = changesHtml(base({runs: [runs[0], {...runs[1], changes: {pack: packOf('r-a', 'no', '5.00', '5.50')}}, runs[2]]}));
  assert.equal(lines(apart), 1);
  // A pack that compares other values than the two points, or another prior run, joins nothing.
  const other = changesHtml(base({runs: [runs[0], {...runs[1], changes: {pack: packOf('r-x', 'yes', '5.00', '5.50')}}, {...runs[2], changes: {pack: packOf('r-b', 'yes', '5.51', '6.00', 'FY2023', 'FY2024')}}]}));
  assert.equal(lines(other), 0);
  // Units that differ between runs are not put on one scale.
  const mixed = changesHtml(base({runs: [runs[0], {...runs[1], metrics: {leverage: {value: '50', unit: '%', period: 'FY2023'}}}]}));
  assert.ok(mixed.includes('Not drawn: the runs state it in different units or without a number.'));
});

test('the lead module’s bottom line is the handoff’s first Bottom line paragraph, or an earlier-format summary’s', () => {
  const newFormat = [{heading: 'Findings', level: 2, line: 1, blocks: []}, h3('Bottom line', text('Lead view.\nBasis: CP-1 handoff.'))];
  assert.equal(leadBottom(newFormat, null), 'Lead view.');
  assert.equal(leadBottom([], {bottomLine: 'Summary view.'}), 'Summary view.');
  assert.equal(leadBottom([], null), null);
});

test('the chart has a text alternative, is keyboard reachable and every row names its values', () => {
  const html = changesHtml(base());
  assert.ok(html.includes('class="dumbbell-chart changes-chart" role="group" aria-label="Then and now: each measure on its own scale. The table below gives the same values." tabindex="0"'));
  assert.ok(html.includes('<table class="history-table"><caption>Measures the pack states, earlier and current</caption>'));
  assert.equal(count(html, 'aria-hidden="true"') >= 3, true, 'tracks are decoration; the text beside them carries the values');
});

test('one period with two values is the analysis changing: no line, and the difference only under Same definition beside its cause', () => {
  const lev = (extra = {}) => measure('leverage', 'Total debt / EBITDA', 'x', 'yes', side('6.57', 'FY2024'), side('6.01', 'FY2024'), '-0.56', extra);
  const withRow = effect => [h3('What changed: the issuer', table(ISSUER_HEAD, ['Total debt / EBITDA', '6.57x', '6.01x', 'Correction', effect]))];
  const draw = (cp8, measures) => changesHtml(base({changes: {lead: 'CP-2', pack: {...PACK, measures}, note: null, problem: null}, cp8}));
  const issuer = html => html.slice(html.indexOf('id="changes-issuer"'), html.indexOf('id="changes-analysis"'));
  const same = issuer(draw(withRow('Same definition; corrected.'), [lev()]));
  assert.ok(same.includes('<td>-0.56x<small>The analysis changed, not the issuer: Correction</small></td>'));
  assert.ok(!same.includes('dumbbell-link'));
  for (const html of [issuer(draw(withRow('Not comparable: basis.'), [lev()])), issuer(draw(null, [lev()]))]) {
    assert.ok(!html.includes('-0.56') && !html.includes('dumbbell-link'));
    assert.ok(html.includes('Earlier 6.57x (FY2024) · Current 6.01x (FY2024)'));
  }
  // The same period with a zero difference is unaffected.
  const zero = issuer(draw(null, [measure('cash', 'Cash', 'US$m', 'yes', side('6261', 'FY2024', 'US$m'), side('6261', 'FY2024', 'US$m'), '0')]));
  assert.ok(zero.includes('<td>0 US$m</td>') && zero.includes('dumbbell-link'));
  // Over time draws no segment between two values of one period.
  const runs = [{...here, key: 'a', runId: 'r-a', current: false, metrics: {leverage: {value: '6.57', unit: 'x', period: 'FY2024'}}}, {...here, key: 'b', runId: 'r-b', metrics: {leverage: {value: '6.01', unit: 'x', period: 'FY2024'}}, changes: {pack: {...PACK, prior: {...PACK.prior, run: 'r-a'}, measures: [lev()]}}}];
  assert.ok(!/<line /.test(changesHtml(base({runs}))));
});

test('a run that records no comparison is not a first run: it says so, and still shows Over time when other runs are listed', () => {
  const other = {...here, key: 'a', runId: 'r-a', asOf: '2023-09-30', current: false, bottom: 'Earlier view.'};
  for (const changes of [null, {lead: 'CP-2', first_run: false, pack: null, note: null, problem: null}]) {
    const alone = changesHtml(base({changes}));
    assert.ok(alone.includes('No comparison was recorded for this run') && !alone.includes('First run of this pathway') && !alone.includes('changes-over-time'));
    const html = changesHtml(base({changes, runs: [other, here]}));
    assert.ok(html.includes('No comparison was recorded for this run') && !html.includes('First run of this pathway') && html.includes('id="changes-over-time"'));
  }
  assert.equal(changesState({pack: null, note: null, problem: null, first_run: true}), 'first');
});

test('Over time joins only points whose periods are the periods the later pack compares', () => {
  const metric = (value, period) => ({leverage: {value, unit: 'x', period}});
  const packWith = (pp, pc) => ({...PACK, prior: {...PACK.prior, run: 'r-a'}, measures: [measure('leverage', 'Total debt / EBITDA', 'x', 'yes', side('5', pp), side('6', pc), '1', {same_period: false})]});
  const runs = pack => [{...here, key: 'a', runId: 'r-a', current: false, metrics: metric('5', 'FY2022')}, {...here, key: 'b', runId: 'r-b', metrics: metric('6', 'FY2023'), changes: {pack}}];
  const lines = html => (html.match(/<line /g) || []).length;
  assert.equal(lines(changesHtml(base({runs: runs(packWith('FY2022', 'FY2023'))}))), 1);
  assert.equal(lines(changesHtml(base({runs: runs(packWith('H1 FY2022', 'H1 FY2023'))}))), 0);
});

// The rows tests/test_changes.py shows the CP-8 checker accepting or refusing (one shared fixture): every row the checker accepts is read here to the verdict written beside it.
const SEAM = JSON.parse(require('node:fs').readFileSync(require('node:path').join(__dirname, '../../../../tests/fixtures/changes-seam/rows.json'), 'utf8'));
test('a row the checker accepts is read by the tab to the verdict the shared fixture states', () => {
  for (const c of SEAM.measure_rows.filter(r => r.accepted)) {
    const m = SEAM.measures[c.measure];
    const verdict = measureVerdict(m, table(ISSUER_HEAD, c.cells));
    assert.equal(verdict.kind, c.verdict, c.name);
    assert.equal(differenceText(m, verdict), c.difference, c.name);
  }
});
test('a module cell the checker accepts is found by the tab and shows the status written in it', () => {
  const pack = {...PACK, modules: [{module: 'CP-2', title: 'Credit view', ran_prior: true, ran_current: true, prior_bottom_line: null, current_bottom_line: null}]};
  for (const c of SEAM.module_cells.filter(r => r.accepted)) {
    const parts = {analysis: table(['Module', 'Status', 'Cause', 'Why'], [c.cell, c.status, 'New period', 'Why.'])};
    assert.ok(analysisPart(pack, parts).includes(`change-status">${c.status}<`), c.name);
  }
});

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
// What the library's build derives from CP-8's registers (`changes.verdicts`, from changes_check.page_verdicts) for the handoff above: literals, hand-written.
const verdict = (kind, label, reason = null, analysis_change = null) => ({kind, label, reason, analysis_change});
const VERDICTS = {
  measures: {
    leverage: verdict('not_comparable', 'Not comparable', 'Not comparable: reported EBITDA against EBITDA As Defined.'),
    coverage: verdict('comparable', 'Same definition', null, 'Unresolved'),
    cash: verdict('comparable', 'Same definition'),
  },
  modules: {
    'CP-0': {status: 'Unchanged', cause: 'Presentation', why: 'The headings differ only.'},
    'CP-2E': {status: 'Not run this time', cause: 'Unresolved', why: 'Not in the current run.'},
  },
  ledger: [['Closed', 0], ['Remaining', 1], ['New', 1], ['No longer stated', 2]],
};
const here = {key: 'k3', href: '#W-Changes/changes/k3', asOf: '2024-09-30', runId: 'r-now', current: true, bottom: 'Now.', metrics: {}, changes: null, cp8: null};
const base = (over = {}) => ({changes: {lead: 'CP-2', pack: PACK, note: null, problem: null, verdicts: VERDICTS}, cp8: CP8, pathway: 'Credit snapshot', fmtDate, runs: [here], ...over});
const count = (html, needle) => html.split(needle).length - 1;
// The text of a page: tags removed, entities decoded (the five the page writes), spaces collapsed.
const INLINE = '(?:button|b|strong|em|i|code|a|span|small)';
const textOf = html => html.replace(new RegExp(`</?${INLINE}\\b[^>]*>`, 'g'), '').replace(/<[^>]*>/g, ' ').replace(/&(?:amp|lt|gt|quot|#39);/g, m => ({'&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'"}[m])).replace(/\s+/g, ' ');

test('a run with no comparison is a first run: the designed empty state with the line the page states and the way to the Overview, and nothing drawn as a comparison', () => {
  const html = changesHtml(base({changes: {lead: 'CP-2', first_run: true, pack: null, note: null, problem: null}}));
  assert.equal(FIRST_RUN, 'First run of this pathway');
  assert.ok(html.includes(`<li>${FIRST_RUN}</li>`) && html.includes('class="empty-state" role="status"'), 'C32 with the fixed line as its reason');
  assert.ok(html.includes('<a class="text-action" href="#W-Overview/overview">Open the Overview'));
  assert.ok(html.includes('href="#W-Overview/x"') === false && changesHtml(base({overviewHref: '#W-Overview/x', changes: {first_run: true, pack: null}})).includes('href="#W-Overview/x"'));
  for (const gone of ['changes-heading', '<table', 'chg-card', 'ms-tile', 'changes-over-time', 'ledger-bar']) assert.ok(!html.includes(gone), gone);
  assert.equal(count(html, '<h1'), 0);
  assert.equal(changesState({pack: null, note: null, problem: 'is not valid JSON'}), 'unreadable');
  assert.equal(changesState({pack: PACK, note: 'changes: not produced — why', problem: null}), 'not_produced');
});

test('a full Changes tab: heading, CP-8 passages, the issuer, the analysis, the ledger counts, over time', () => {
  const html = changesHtml(base());
  assert.ok(html.includes('<h2 class="changes-heading">Since 30 September 2024 · Credit snapshot</h2>'));
  // Part 1: the passages' sentences as written (the page's text, tags removed); the Basis line is not part of the sentence and is not on the page (it is Evidence's).
  const page = textOf(html);
  assert.ok(page.includes('The credit picture is about the same since the earlier run, and the change is the analysis\'s, not the issuer\'s.'));
  assert.ok(!html.includes('Basis:') && !page.includes('CP-1 handoff; calculation C01'));
  assert.ok(page.includes('Cash is unchanged at USD 6,261 million.'));
  assert.ok(page.includes('Leverage is 6.01x on EBITDA as defined against 6.57x on reported EBITDA, not comparable.'));
  // Part 2: the pack's values with unit and period.
  assert.ok(html.includes('<td>6.57x (FY2024 / 2024-09-30)</td><td>6.01x (FY2024)</td>'));
  assert.ok(html.includes('<td>6261 US$m (2024-09-30)</td><td>6261 US$m (2024-09-30)</td><td>0 US$m</td>'));
  assert.ok(html.includes('Net debt change is not shown: gross debt is not stated in either run.'));
  assert.ok(html.includes('<th scope="row">FY2028</th><td>6637</td><td>6637</td><td>0</td>'));
  assert.ok(html.includes('Debt maturities, US$m'));
  // CP-8's own tables: each change row is a card, the cause and the effect in words.
  assert.equal(count(html, '<article class="chg-card">'), 3);
  assert.ok(page.includes('Same definition; unchanged at USD 6,261 million.'));
  // Part 3: one row per pack module, CP-8's status by the code in its first cell; CP-8's own table is the tiles.
  assert.equal(count(html, '<details class="change-module">'), 2);
  assert.ok(html.includes('<span class="badge badge-gray change-status">Unchanged</span>'));
  assert.ok(html.includes('<span class="badge badge-gray change-status">Not run this time</span>'));
  assert.ok(html.includes('<small>Current</small>Did not run'));
  assert.ok(html.includes('<p>The supplied sources support a bounded snapshot.</p>'));
  assert.equal(count(html, '<article class="ms-tile'), 2);
  // Part 4: the four counts as one bar (E1, E2 no longer stated; E3/C1 remaining; C2 new); the ledger itself is Evidence's: its rows are not on this page.
  assert.ok(html.includes('aria-label="Limitations: Closed 0, Remaining 1, New 1, No longer stated 2"'));
  assert.equal(count(html, 'class="ledger-bar"'), 1);
  for (const row of ['An earlier limitation in words.', 'Another earlier limitation.', 'Carried over.', 'A current limitation in words.']) assert.ok(!page.includes(row), row);
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
  const verdicts = {measures: {leverage: verdict('not_comparable', 'Not comparable', 'the units differ')}};
  const no = changesHtml(base({changes: {lead: 'CP-2', pack, note: null, problem: null, verdicts}}));
  assert.ok(no.includes('<td>6.57x (FY2024)</td><td>62% (FY2024)</td><td><strong>Not comparable</strong><small>the units differ</small></td>'));
  assert.equal(count(no, 'class="dumbbell-link"'), 0);
});

test('a judge measure without a verdict from CP-8 is left unjudged, with no difference', () => {
  const pack = {...PACK, measures: [PACK.measures[0]]};
  const html = changesHtml(base({changes: {lead: 'CP-2', pack, note: null, problem: null}, cp8: null}));
  assert.ok(html.includes('<strong>Comparability not judged</strong>'));
  assert.ok(!html.includes('-0.56'));
  assert.equal(count(html, 'class="dumbbell-link"'), 0);
  const unjudged = {kind: 'unjudged', label: 'Comparability not judged', reason: 'the label or definition text differs; CP-8 judges'};
  assert.deepEqual(measureVerdict(PACK.measures[2], {verdicts: null}), unjudged);
  assert.deepEqual(measureVerdict(PACK.measures[2], {verdicts: {measures: {}}}), unjudged);
  // The page never reads a pack's `yes` or a register itself: only the build's verdict makes a measure comparable.
  assert.deepEqual(measureVerdict({...PACK.measures[2], comparable: 'yes'}, null), unjudged);
  assert.deepEqual(measureVerdict(PACK.measures[2], {verdicts: {measures: {cash: verdict('comparable', 'Same definition', null, 'Correction')}}}), {kind: 'comparable', label: 'Same definition', reason: null, analysisChange: 'Correction'});
});

test('a value the pack does not state is shown as not stated, never as zero', () => {
  const pack = {...PACK, measures: [measure('coverage', 'EBITDA / cash interest', 'x', 'no', side('3.29', 'FY2024'), null, null, {reason: 'the current run does not state it'})]};
  const verdicts = {measures: {coverage: verdict('not_comparable', 'Not comparable', 'the current run does not state it')}};
  const html = changesHtml(base({changes: {lead: 'CP-2', pack, note: null, problem: null, verdicts}}));
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
  const packOf = (priorRun, comparable, prior, current, pp = 'FY2022', pc = 'FY2023') => ({pack: {...PACK, prior: {...PACK.prior, run: priorRun}, measures: [measure('leverage', 'Total debt / EBITDA', 'x', comparable, side(prior, pp), side(current, pc), '0.50', {same_period: false})]}, verdicts: {measures: {leverage: comparable === 'yes' ? verdict('comparable', 'Comparable') : verdict('not_comparable', 'Not comparable', 'unit')}}});
  const runs = [
    {key: 'a', href: '#a', asOf: '2023-09-30', runId: 'r-a', current: false, bottom: 'Earlier view.', metrics: metric('5.00', 'FY2022'), changes: null, cp8: null},
    {key: 'b', href: '#b', asOf: '2024-09-30', runId: 'r-b', current: false, bottom: null, metrics: metric('5.50', 'FY2023'), changes: packOf('r-a', 'yes', '5.00', '5.50'), cp8: null},
    {key: 'c', href: '#c', asOf: '2025-03-31', runId: 'r-c', current: true, bottom: 'Latest view.', metrics: metric('6.00', 'FY2024'), changes: packOf('r-b', 'yes', '5.50', '6.00', 'FY2023', 'FY2024'), cp8: null},
  ];
  const lines = html => (/<li><strong>Total debt \/ EBITDA<\/strong>(.*?)<\/li>/.exec(html)[1].match(/<line /g) || []).length;
  const html = changesHtml(base({runs}));
  assert.equal(lines(html), 2, 'both neighbours are compared under one definition by the later run’s pack');
  const over = html.slice(html.indexOf('id="changes-over-time"'));
  assert.ok(over.indexOf('30 September 2023') < over.indexOf('30 September 2024') && over.indexOf('30 September 2024') < over.indexOf('31 March 2025'));
  assert.ok(html.includes('<td>5.00x<small>FY2022</small></td>') && html.includes('<td>6.00x<small>FY2024</small></td>'));
  assert.ok(html.includes('<td>Earlier view.</td>') && html.includes('<td>Not stated</td>') && html.includes('<td>Latest view.</td>'));
  // Not comparable in the later run's pack: points only.
  const apart = changesHtml(base({runs: [runs[0], {...runs[1], changes: packOf('r-a', 'no', '5.00', '5.50')}, runs[2]]}));
  assert.equal(lines(apart), 1);
  // A pack that compares other values than the two points, or another prior run, joins nothing.
  const other = changesHtml(base({runs: [runs[0], {...runs[1], changes: packOf('r-x', 'yes', '5.00', '5.50')}, {...runs[2], changes: packOf('r-b', 'yes', '5.51', '6.00', 'FY2023', 'FY2024')}]}));
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

test('one period with two values is the analysis changing: no line, and the difference only under the build\u2019s Same definition beside its cause', () => {
  const lev = (extra = {}) => measure('leverage', 'Total debt / EBITDA', 'x', 'yes', side('6.57', 'FY2024'), side('6.01', 'FY2024'), '-0.56', extra);
  const draw = (leverage, measures) => changesHtml(base({changes: {lead: 'CP-2', pack: {...PACK, measures}, note: null, problem: null, verdicts: leverage ? {measures: {leverage, cash: verdict('comparable', 'Comparable')}} : null}}));
  const issuer = html => html.slice(html.indexOf('id="changes-issuer"'), html.indexOf('id="changes-analysis"'));
  const same = issuer(draw(verdict('comparable', 'Same definition', null, 'Correction'), [lev()]));
  assert.ok(same.includes('<td>-0.56x<small>The analysis changed, not the issuer: Correction</small></td>'));
  assert.ok(!same.includes('dumbbell-link'));
  for (const html of [issuer(draw(verdict('not_comparable', 'Not comparable', 'Not comparable: basis.'), [lev()])), issuer(draw(verdict('unjudged', 'Comparability not judged'), [lev()])), issuer(draw(null, [lev()]))]) {
    assert.ok(!html.includes('-0.56') && !html.includes('dumbbell-link'));
    assert.ok(html.includes('Earlier 6.57x (FY2024) · Current 6.01x (FY2024)'));
  }
  // The same period with a zero difference is unaffected.
  const zero = issuer(draw(verdict('comparable', 'Comparable'), [measure('cash', 'Cash', 'US$m', 'yes', side('6261', 'FY2024', 'US$m'), side('6261', 'FY2024', 'US$m'), '0')]));
  assert.ok(zero.includes('<td>0 US$m</td>') && zero.includes('dumbbell-link'));
  // Over time draws no segment between two values of one period.
  const runs = [{...here, key: 'a', runId: 'r-a', current: false, metrics: {leverage: {value: '6.57', unit: 'x', period: 'FY2024'}}}, {...here, key: 'b', runId: 'r-b', metrics: {leverage: {value: '6.01', unit: 'x', period: 'FY2024'}}, changes: {pack: {...PACK, prior: {...PACK.prior, run: 'r-a'}, measures: [lev()]}, verdicts: {measures: {leverage: verdict('comparable', 'Same definition', null, 'Correction')}}}}];
  assert.ok(!/<line /.test(changesHtml(base({runs}))));
});

test('only a comparable verdict shows a difference and a joining line; not comparable, not judged, an unknown kind and no verdicts show neither', () => {
  const lev = measure('leverage', 'Total debt / EBITDA', 'x', 'yes', side('6.57', 'FY2023'), side('6.01', 'FY2024'), '-0.56', {same_period: false});
  const draw = verdicts => changesHtml(base({changes: {lead: 'CP-2', pack: {...PACK, measures: [lev]}, note: null, problem: null, verdicts}}));
  const comparable = draw({measures: {leverage: verdict('comparable', 'Comparable')}});
  assert.ok(comparable.includes('<td>-0.56x</td>') && comparable.includes('dumbbell-link'));
  for (const verdicts of [{measures: {leverage: verdict('not_comparable', 'Not comparable', 'basis')}}, {measures: {leverage: verdict('unjudged', 'Comparability not judged')}}, {measures: {leverage: verdict('maybe', 'Comparable')}}, {measures: {}}, {}, null]) {
    const html = draw(verdicts);
    assert.ok(!html.includes('-0.56') && !html.includes('dumbbell-link') && !/<line /.test(html), JSON.stringify(verdicts));
    assert.ok(html.includes('Earlier 6.57x (FY2023) · Current 6.01x (FY2024)'));
  }
  // Over time reads the later run's verdicts, never a register: a join needs a comparable verdict.
  const runs = verdicts => [{...here, key: 'a', runId: 'r-a', current: false, metrics: {leverage: {value: '6.57', unit: 'x', period: 'FY2023'}}}, {...here, key: 'b', runId: 'r-b', metrics: {leverage: {value: '6.01', unit: 'x', period: 'FY2024'}}, changes: {pack: {...PACK, prior: {...PACK.prior, run: 'r-a'}, measures: [lev]}, verdicts}}];
  const lines = verdicts => (changesHtml(base({runs: runs(verdicts)})).match(/<line /g) || []).length;
  assert.equal(lines({measures: {leverage: verdict('comparable', 'Comparable')}}), 1);
  assert.equal(lines({measures: {leverage: verdict('not_comparable', 'Not comparable')}}), 0);
  assert.equal(lines(null), 0);
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
  const runs = pack => [{...here, key: 'a', runId: 'r-a', current: false, metrics: metric('5', 'FY2022')}, {...here, key: 'b', runId: 'r-b', metrics: metric('6', 'FY2023'), changes: {pack, verdicts: {measures: {leverage: verdict('comparable', 'Comparable')}}}}];
  const lines = html => (html.match(/<line /g) || []).length;
  assert.equal(lines(changesHtml(base({runs: runs(packWith('FY2022', 'FY2023'))}))), 1);
  assert.equal(lines(changesHtml(base({runs: runs(packWith('H1 FY2022', 'H1 FY2023'))}))), 0);
});

// The shared fixture (tests/fixtures/changes-seam/rows.json) states, per case, the verdict kind the build derives (`page`, checked in tests/test_changes.py and
// tests/test_update_library.py): the tab shows a difference for a comparable verdict and for no other.
const SEAM = JSON.parse(require('node:fs').readFileSync(require('node:path').join(__dirname, '../../../../tests/fixtures/changes-seam/rows.json'), 'utf8'));
test('the tab shows a difference exactly where the fixture states a comparable verdict', () => {
  for (const c of SEAM.measure_rows) {
    const m = SEAM.measures[c.measure];
    const changes = {verdicts: {measures: {[c.measure]: verdict(c.page, c.page)}}};
    assert.equal(differenceText(m, measureVerdict(m, changes)), c.page === 'comparable' ? c.difference : null, c.name);
  }
});
test('a module row is the build\u2019s: its status and reason are shown, and a module with no entry is not stated by CP-8', () => {
  const pack = {...PACK, modules: [{module: 'CP-2', title: 'Credit view', ran_prior: true, ran_current: true, prior_bottom_line: null, current_bottom_line: null}]};
  const changes = status => ({verdicts: {modules: status ? {'CP-2': {status, cause: 'New period', why: 'Why.'}} : {}}});
  for (const c of SEAM.module_cells.filter(r => r.accepted)) {
    const html = analysisPart(pack, {}, changes(c.status));
    assert.ok(html.includes(`change-status">${c.status}<`) && html.includes('<p class="change-why">New period · Why.</p>'), c.name);
  }
  assert.ok(analysisPart(pack, {}, changes(null)).includes('change-status">Not stated by Changes since the last run<'));
  assert.ok(analysisPart(pack, {}, null).includes('change-status">Not stated by Changes since the last run<'));
  assert.ok(analysisPart(pack, null, changes('Unchanged')).includes('change-status">Explanation not produced<'));
});
test('the ledger bar is the build\u2019s counts; a ledger it could not read draws no bar, and no ledger row is on the Changes page either way', () => {
  const unread = changesHtml(base({changes: {lead: 'CP-2', pack: PACK, note: null, problem: null, verdicts: {...VERDICTS, ledger: null}}}));
  assert.ok(!unread.includes('class="ledger-bar"') && !textOf(unread).includes('An earlier limitation in words.'));
  assert.ok(unread.includes('Unresolved differences in Evidence'), 'the one link stays');
  const other = changesHtml(base({changes: {lead: 'CP-2', pack: PACK, note: null, problem: null, verdicts: {...VERDICTS, ledger: [['Closed', 0], ['Remaining', 0], ['New', 0], ['No longer stated', 0], ['Other', 3]]}}}));
  assert.ok(other.includes('aria-label="Limitations: Closed 0, Remaining 0, New 0, No longer stated 0, Other 3"'));
});

test('what the Changes tab itself writes names things and shows no module code', () => {
  // The pack and handoff text are stored data (a code there is named by screen.js, the library browser test reads it); these carry none.
  const clean = {...PACK, measures: PACK.measures.map(m => ({...m, reason: 'the definition text differs'}))};
  const noCode = /\bCP-[A-Z0-9]+\b/;
  const html = changesHtml(base({changes: {lead: 'CP-2', pack: clean, note: null, problem: null, verdicts: {measures: {}, modules: {}, ledger: []}}, cp8: []}));
  assert.ok(html.includes('The Changes handoff has no') && html.includes('Not stated in the Changes handoff.'));
  assert.ok(html.includes('change-status">Not stated by Changes since the last run<'));
  assert.ok(html.includes('<span class="change-name">Source readiness</span>') && !html.includes('module-code'));
  assert.ok(!noCode.test(html.replace(/ (?:href|data-[a-z-]+)="[^"]*"/g, '')), html.match(noCode)?.[0]);
  const notHeld = changesHtml(base({changes: {lead: 'CP-2', pack: clean, note: null, problem: null, verdicts: null}, cp8: null}));
  assert.ok(notHeld.includes('The explanation of the changes is not held for this run.') && !noCode.test(notHeld.replace(/ (?:href|data-[a-z-]+)="[^"]*"/g, '')));
});

// ---- The net debt change of one period (owner, 2026-11-12): the analysis changed, not the issuer. Literals are hand-written.
const {netDebtView} = require('./changes.js');
const ND = {unit: 'US$m', prior_net_debt: '6190', change_in_gross_debt: '-110', change_in_cash: '-30', current_net_debt: '6110', convention: 'net debt = gross debt - cash',
  same_period: true, prior_period: 'FY2024', current_period: 'FY2024 / 2024-09-30', prior_gross_debt: '7100', prior_cash: '910', current_gross_debt: '6990', current_cash: '880'};

test('one period with two net debt values: both runs, their periods, the sentence, no change figure and no direction', () => {
  const html = netDebtView(ND);
  for (const shown of ['7100 US$m', '910 US$m', '6190 US$m', '6990 US$m', '880 US$m', '6110 US$m', 'Earlier gross debt (FY2024)', 'Current net debt (FY2024 / 2024-09-30)'])
    assert.ok(html.includes(shown), shown);
  assert.ok(html.includes('Both runs state net debt for the same date; the difference is between the two analyses, not a change in the issuer.'));
  for (const hidden of ['-110 US$m', '-30 US$m', 'Change in', 'rose', 'fell']) assert.ok(!html.includes(hidden), hidden);
});

test('one period with equal net debt values, two periods, and a pack without the flag render as a change', () => {
  const zero = netDebtView({...ND, change_in_gross_debt: '0', change_in_cash: '0'});
  assert.ok(zero.includes('Change in gross debt (FY2024 to FY2024 / 2024-09-30)') && !zero.includes('Both runs state'));
  const two = netDebtView({...ND, same_period: false, prior_period: 'FY2023', current_period: 'FY2024'});
  assert.ok(two.includes('-110 US$m') && two.includes('Change in cash (FY2023 to FY2024)') && !two.includes('Both runs state'));
  const {same_period, prior_period, current_period, prior_gross_debt, prior_cash, current_gross_debt, current_cash, ...old} = ND;
  const older = netDebtView(old);
  assert.ok(older.includes('<dt>Change in cash</dt><dd>-30 US$m</dd>') && !older.includes('Both runs state'));
});

test('net debt periods and values are escaped', () => {
  const evil = '<img src=x onerror=alert(1)>';
  const html = netDebtView({...ND, prior_period: evil, prior_cash: evil});
  assert.ok(!html.includes('<img') && html.includes('&lt;img'));
});

// ---- Task 9: the page is CP-8's own passages and tables drawn by the shared components. Fixture with unique lines, Basis lines, a Source column and a ledger.
const R_ISSUER_HEAD = ['Measure or fact', 'Earlier', 'Current', 'Cause', 'Effect on the credit view', 'Source'];
const R_ISSUER = [
  ['Total debt / EBITDA', '6.01x (FY2024)', '6.01x (FY2024)', 'Unresolved', 'Same definition: difference 0.00x at the same date.', 'changes.json; prior/CP-1.md, page 4'],
  ['Net debt / EBITDA', '4.51x', '4.40x', 'Unresolved', 'Same definition, so the leverage view is unchanged.', 'changes.json'],
  ['Undrawn facilities', 'USD 1,200 million', 'USD 1,900 million', 'Definition', 'Not comparable: the current run adds the securitization.', 'changes.json'],
];
const R_STATE = [
  ['Source readiness (CP-0)', 'Unchanged', 'Presentation', 'The headings differ only.'],
  ['Financial data foundation (CP-1)', 'Unchanged', 'Presentation', 'The same pack is sufficient.'],
  ['Debt structure (CP-2B)', 'Unchanged', 'None', 'The same structure is read.'],
  ['Credit view (CP-2)', 'Unchanged', 'None', 'The same credit conclusion.'],
  ['Hedging (CP-2E)', 'Not run this time', 'Unresolved', 'Not in the current run.'],
  ['Forward model (CP-5)', 'Added', 'New module', 'A module with no earlier counterpart.'],
];
const R_LEDGER = [['E1', '—', 'LEDGERROW one limitation.', 'No longer stated', '—'], ['E2', 'C1', 'LEDGERROW two carried over.', 'Remaining', '—'], ['—', 'C2', 'LEDGERROW three is new.', 'New', '—']];
const para = (line, body) => ({type: 'text', line, end: line, text: body});
const CP8R = [
  {heading: 'Request', level: 2, line: 1, blocks: [para(2, 'HIDDEN request text.')]},
  {heading: 'Findings', level: 2, line: 10, blocks: []},
  h3('Bottom line', para(12, 'About the same: the credit picture has not changed since the earlier run. Every difference is the analysis’s, not the issuer’s.\nBasis: changes.json; prior/CP-1.md, page 4'), para(14, 'Total debt is 6.01x EBITDA As Defined in both runs.\nBasis: calculation C01; TDG_10-K.htm.jsonl, page 5')),
  h3('Key findings', para(16, '- **The issuer did not change.** No part of the view should be re-priced on this comparison. Cash is USD 6,261 million.\nBasis: changes.json'), para(18, '- The analysis changed by addition. Four modules were added this time.\nBasis: prior/CP-1.md, page 6')),
  h3('Contrary evidence and what would change the view', para(20, 'A covenant test below 7.0x would change the view. A new filing would too.\nBasis: changes.json')),
  h3('Limitations', para(22, '- Both runs share the as-of date. The conclusion holds by construction.\nBasis: changes.json'), para(24, '- Net debt balances could not be compared.')),
  h3('What changed: the issuer', {type: 'table', headers: R_ISSUER_HEAD, rows: R_ISSUER.map((cells, i) => ({line: 30 + i, cells}))}),
  h3('What changed: the analysis', {type: 'table', headers: ['Module', 'Status', 'Cause', 'Why'], rows: R_STATE.map((cells, i) => ({line: 40 + i, cells}))}),
  h3('Limitations ledger', {type: 'table', headers: ['Earlier ref', 'Current ref', 'Limitation', 'Status', 'What closed it'], rows: R_LEDGER.map((cells, i) => ({line: 50 + i, cells}))}),
  {heading: 'Calculations', level: 2, line: 60, blocks: [para(61, 'CALCSECTION text'), {type: 'table', headers: ['ID', 'Item'], rows: [{line: 62, cells: ['D01', 'CALCROW']}]}]},
  {heading: 'Gaps', level: 2, line: 70, blocks: [{type: 'table', headers: ['Gap', 'Effect'], rows: [{line: 71, cells: ['GAPROW', 'No change figure']}]}]},
  {heading: 'Next module', level: 2, line: 80, blocks: [para(81, 'NEXTMODULE text')]},
];
const OUT = {id: 'o8', module: 'CP-8', run: 'run-x', chips: () => 0};
const rich = (over = {}) => base({cp8: CP8R, output: OUT, ...over});
const reasonless = html => html.replace(/ (?:href|data-paragraph|data-basis|data-evidence|data-figure)="[^"]*"/g, '');

test('every sentence of the CP-8 passages is on the page as written; the Basis lines are not', () => {
  const html = changesHtml(rich()), page = textOf(html);
  const sentences = [
    'About the same: the credit picture has not changed since the earlier run.', 'Every difference is the analysis’s, not the issuer’s.', 'Total debt is 6.01x EBITDA As Defined in both runs.',
    'The issuer did not change.', 'No part of the view should be re-priced on this comparison.', 'Cash is USD 6,261 million.', 'The analysis changed by addition.', 'Four modules were added this time.',
    'A covenant test below 7.0x would change the view.', 'A new filing would too.', 'Both runs share the as-of date.', 'The conclusion holds by construction.', 'Net debt balances could not be compared.',
  ];
  for (const sentence of sentences) assert.ok(page.includes(sentence), sentence);
  for (const gone of ['Basis', 'changes.json', 'prior/CP-1.md', 'calculation C01', 'TDG_10-K.htm.jsonl']) assert.ok(!page.includes(gone), gone);
  // Each passage in its component: C2, C5, C6, the Limitations list.
  assert.ok(html.includes('class="verdict"') && html.includes('class="feed"') && html.includes('class="callout"') && html.includes('class="lim-compact"'));
  assert.equal(count(html, '<li class="feed-item">'), 2);
});

test('every cell of the change and moduleState tables is drawn, except a Source column, which the row’s trace control reaches', () => {
  const html = changesHtml(rich()), page = textOf(html);
  for (const row of R_ISSUER) for (const cell of row.slice(0, 5)) assert.ok(page.includes(cell), cell);
  for (const row of R_STATE) for (const cell of row) assert.ok(page.includes(cell), cell);
  assert.ok(!page.includes('changes.json') && !html.includes('>Source<'));
  assert.equal(count(html, '<article class="chg-card">'), 3);
  assert.equal(count(html, 'class="dumb"'), 1, 'the one row of two plain numbers carries a dumbbell');
  assert.ok(!html.includes('<table class="history-table"><caption>Each change'), 'no plain grid of the handoff’s table');
});

test('the modules whose state repeats collapse to one tile whose count is the rows collapsed', () => {
  const html = changesHtml(rich());
  const group = /<article class="ms-tile ms-group">(.*?)<\/article>/s.exec(html)[1];
  assert.equal(count(html, 'ms-group'), 1);
  assert.ok(group.includes('Unchanged') && /<b class="ms-n">4<\/b>/.test(group));
  assert.equal(count(group, '<li>'), 4, 'the count equals the rows collapsed');
  for (const name of ['Source readiness (CP-0)', 'Financial data foundation (CP-1)', 'Debt structure (CP-2B)', 'Credit view (CP-2)']) assert.ok(group.includes(name), name);
  assert.equal(count(html, '<article class="ms-tile">'), 2, 'the two states that occur once are single tiles');
  assert.ok(html.includes('Not run this time') && html.includes('Added'));
});

test('the ledger is not on the Changes route: no row, no heading, no table; one counted link to Evidence’s Gaps tab', () => {
  const html = changesHtml(rich()), page = textOf(html);
  for (const gone of ['LEDGERROW', 'Earlier ref', 'Limitations ledger', 'What closed it', 'CALCSECTION', 'CALCROW', 'GAPROW', 'NEXTMODULE', 'HIDDEN request']) assert.ok(!page.includes(gone), gone);
  assert.ok(html.includes('<a class="text-action" href="#W-Evidence/gaps?c=run-x&amp;m=CP-8">Unresolved differences in Evidence<span class="chg-n">3</span>'));
  assert.equal(count(html, 'Unresolved differences in Evidence'), 1);
  assert.ok(html.includes('class="gapsig"') && html.includes('<div class="gapsig-n" data-count>4</div>'), 'the gap signal counts what the Gaps tab lists: 1 gap and 3 ledger rows');
  // The same rows are on Evidence’s Gaps tab for the module.
  const Evidence = require('./evidence.js');
  assert.equal(Evidence.ledgerTotal(CP8R), 3);
  assert.equal(Evidence.gapTotal(CP8R), 4);
});

test('nothing audit-like is on the page: no Basis, file, hash, calculation or method code, run code or inter-module text, in text or in attributes (trace keys apart)', () => {
  const html = reasonless(changesHtml(rich({changes: {lead: 'CP-2', pack: PACK, note: null, problem: null, verdicts: VERDICTS}})));
  for (const [name, rx] of [['Basis', /Basis:/], ['file', /\.(?:jsonl|htm|html|pdf|md|json)\b/], ['hash', /sha256|\b[0-9a-f]{32,}\b/i], ['calculation', /\b[Cc]alculations? [A-Z]{1,2}\d{2}\b/], ['method code', /\bT\d[A-Z]?\.\d/],
    ['run code', /run-x|r-now/], ['id', /\b(?:EV|GAP|MON|DP|SRC)-\d{2,3}\b|\bSC\d\b/]]) assert.ok(!rx.test(html), `${name}: ${rx.exec(html)?.[0]}`);
});

test('Review Focus 3: no CP-8 handoff, no change table, no moduleState table, an earlier-format handoff: nothing throws, no empty heading, and each says what it shows', () => {
  const withoutTable = (...names) => CP8R.map(s => (names.includes(s.heading) ? {...s, blocks: []} : s));
  const emptyHeadings = html => [...html.matchAll(/<h2[^>]*>([^<]*)<\/h2>\s*<\/(?:section|div)>/g)].map(m => m[1]);
  const none = changesHtml(rich({cp8: null}));
  assert.ok(none.includes('The explanation of the changes is not held for this run.') && !none.includes('id="changes-what"') && !none.includes('class="chg-card"') && none.includes('id="changes-issuer"'));
  const noChange = changesHtml(rich({cp8: withoutTable('What changed: the issuer')}));
  assert.ok(noChange.includes('The Changes handoff has no table of what changed in the issuer.') && !noChange.includes('chg-card') && noChange.includes('ms-tile') && noChange.includes('class="verdict"'));
  const noState = changesHtml(rich({cp8: withoutTable('What changed: the analysis')}));
  assert.ok(noState.includes('The Changes handoff has no table of what changed in the analysis.') && !noState.includes('ms-tile') && noState.includes('chg-card') && noState.includes('change-module'));
  const earlier = changesHtml(rich({cp8: [{heading: 'Reader summary', level: 2, line: 1, blocks: [para(2, 'An earlier-format summary.')]}]}));
  assert.ok(earlier.includes('Not stated in the Changes handoff. It is in the earlier format, which has no bottom line or key findings; the comparison pack is shown on its own.'));
  assert.ok(earlier.includes('id="changes-issuer"') && earlier.includes('id="changes-analysis"') && earlier.includes('id="changes-over-time"') && !earlier.includes('class="verdict"') && !earlier.includes('An earlier-format summary.'));
  const nothing = changesHtml(rich({cp8: CP8R.slice(0, 2)}));
  assert.ok(nothing.includes('Not stated in the Changes handoff.'));
  for (const html of [none, noChange, noState, earlier, nothing]) {
    assert.deepEqual(emptyHeadings(html), []);
    assert.ok(!/undefined|NaN|\[object/.test(html));
    assert.equal(count(html, '<h1'), 0);
  }
});

test('a handoff with only some passages draws only those; a passage with no text leaves no card', () => {
  const only = CP8R.filter(s => !['Key findings', 'Contrary evidence and what would change the view', 'Limitations'].includes(s.heading) && !/ledger/i.test(s.heading));
  const html = changesHtml(rich({cp8: only, changes: {lead: 'CP-2', pack: PACK, note: null, problem: null, verdicts: {...VERDICTS, ledger: null}}}));
  assert.ok(html.includes('class="verdict"') && !html.includes('class="feed"') && !html.includes('class="callout"') && !html.includes('id="changes-limitations"') && !html.includes('chg-why'));
  const keyOnly = changesHtml(rich({cp8: CP8R.filter(s => s.heading !== 'Contrary evidence and what would change the view')}));
  assert.ok(keyOnly.includes('<div class="c24"><div class="rd-card"><h3 class="rd-h">Key findings</h3>') && !keyOnly.includes('class="callout"'));
});

test('a finding section whose shape no component names keeps its own heading and is drawn as cards, never a raw grid', () => {
  const extra = h3('Watch items', {type: 'table', headers: ['Item', 'Why it matters'], rows: [{line: 90, cells: ['A refinancing', 'It would move leverage.']}]});
  const html = changesHtml(rich({cp8: [...CP8R.slice(0, 8), extra, ...CP8R.slice(8)]}));
  assert.ok(html.includes('<h2>Watch items</h2>') && html.includes('rec-card') && textOf(html).includes('It would move leverage.'));
});

test('cells and text with <b>&" are escaped on every block of the page', () => {
  const evil = '<b>&"x</b>';
  const cp8 = CP8R.map(s => {
    if (s.heading === 'Bottom line') return h3('Bottom line', para(12, `${evil} is the bottom line.`));
    if (s.heading === 'What changed: the issuer') return h3(s.heading, table(R_ISSUER_HEAD, [evil, evil, evil, evil, evil, 'src']));
    if (s.heading === 'What changed: the analysis') return h3(s.heading, table(['Module', 'Status', 'Cause', 'Why'], [evil, 'Unchanged', evil, evil], [`${evil}2`, 'Unchanged', evil, evil]));
    return s;
  });
  const html = changesHtml(rich({cp8}));
  assert.ok(!/<b>&"x/.test(html) && !html.includes('&"x'), 'no raw <b>&" survives');
  assert.ok(html.includes('&amp;&quot;x'), 'its text is on the page, escaped');
  assert.equal(count(html, '<script'), 0);
});

test('earlier run: CP-8 not held and no change table leaves the pack parts; the first-run, unrecorded and unreadable states keep their own text', () => {
  const unrecorded = changesHtml(base({changes: null}));
  assert.ok(unrecorded.includes('<li>No comparison was recorded for this run</li>') && unrecorded.includes('empty-state'));
  const unreadable = changesHtml(rich({changes: {lead: 'CP-2', pack: null, note: null, problem: 'could not read', verdicts: null}, cp8: null}));
  assert.ok(unreadable.includes('could not be read') && !unreadable.includes('empty-state') && !unreadable.includes('id="changes-what"'));
});

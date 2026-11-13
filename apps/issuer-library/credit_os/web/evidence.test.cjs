'use strict';
// Evidence page (library redesign, task 3): the pure parts of evidence.js, read through a small inline fixture of two modules.
const test = require('node:test');
const assert = require('node:assert/strict');
const Evidence = require('./evidence.js');

const RUN = 'run-a';
const table = (line, headers, rows) => ({type: 'table', line, headers, rows: rows.map((cells, i) => ({line: line + 2 + i, cells}))});
const text = (line, body) => ({type: 'text', line, text: body});
const sec = (heading, level, line, blocks = []) => ({heading, level, line, blocks});

// CP-2A: one section of every role, a hidden one, and a table that is left with one column.
const CP2A = [
  sec('Findings', 2, 1),
  sec('Bottom line', 3, 3, [text(4, 'Downside is manageable.\nBasis: calculation C-1; TDG_10-K.htm.jsonl, page 5')]),
  sec('Leverage bridge', 3, 6, [
    table(8, ['Line', 'FY2024', 'Source'], [['Net debt', '9,100', 'TDG_10-K.htm.jsonl p.5'], ['Cash', '1,200', 'TDG_10-K.htm.jsonl p.9']]),
    text(14, 'Module status: accepted with limits.'),
    text(15, 'A finding with a Basis line.\nBasis: TDG_10-K.htm.jsonl, page 7'),
  ]),
  sec('Chart data: Net debt', 3, 18, [table(19, ['Period', 'Value'], [['FY2023', '8,900']])]),
  sec('Downstream handoff', 3, 25, [table(26, ['Metric', 'downstream_use'], [['ONLYCELL', 'for CP-6']])]),
  sec('Request', 2, 30, [text(31, 'SECRET REQUEST TEXT'), table(32, ['Zzhiddenheader', 'Other'], [['hidden cell', 'x']])]),
  sec('Calculations', 2, 40, [
    text(41, 'Calculation notes are written once.'),
    table(42, ['Calc ID', 'Formula', 'Result', 'Use in this module'], [['C-1', 'a / b', '2.1x', 'Used by CP-6'], ['C-2', 'c / d', '3.4x', 'Used by CP-6']]),
  ]),
  sec('Gaps', 2, 50, [table(51, ['Gap', 'Severity', 'Required source', 'Consumer'], [['Missing lease schedule', 'High', 'Lease note', 'CP-6'], ['No peer set', 'Low', 'Peer file', 'CP-6']])]),
  sec('Sources', 2, 60, [table(61, ['Source', 'sha256', 'Role in this run'], [['TDG_10-K.htm.jsonl', 'a'.repeat(64), 'Primary']])]),
  sec('Analytical appendix', 2, 70),
  sec('Maturity register', 3, 72, [table(73, ['Instrument', 'Amount'], [['Term loan', '4,000']])]),
];
const CP6 = [
  sec('Findings', 2, 1),
  sec('Key findings', 3, 3, [text(4, 'Recommendation holds.\nBasis: Downside (CP-2A)')]),
  sec('Gaps', 2, 10, [table(11, ['Gap', 'Severity'], [['Thin liquidity note', 'Medium']])]),
];
const NAMES = {'CP-2A': 'Downside', 'CP-6': 'Committee decision'};
const EV = {
  sources: [{name: 'A <report>.pdf', sha256: 'a'.repeat(64), type: 'pdf', documentDate: null, readBy: ['CP-2A', 'CP-6']}],
  unused: [{name: 'C_unread.htm.jsonl', sha256: 'c'.repeat(64), type: 'htm.jsonl', documentDate: '2024-12-31', readBy: []}],
  unrecorded: [], noSourcesModules: [],
  handoffs: [{module: 'CP-2A', name: 'CP-2A.md', href: '../runs/r/CP-2A.md?sha256=1'}, {module: 'CP-6', name: 'CP-6.md', href: '../runs/r/CP-6.md?sha256=2'}],
  zip: 'downloads/r/handoffs.zip',
  downloads: [{label: 'Model m', href: '/files/m.html'}],
  record: {
    hashes: [{name: 'instructions/CP-2A.md', sha256: '2'.repeat(64)}, {name: 'delivery-x.json', sha256: 'd'.repeat(64)}],
    instructions: [{module: 'CP-2A', href: '../runs/r/instructions/CP-2A.md', sha256: 'e'.repeat(64)}],
    calls: [
      {module: 'CP-2A', attempt: 0, started: '2026-11-09T15:13:51Z', http_status: 200, error_class: null, settled_usd: '0.00941950'},
      {module: 'CP-2A', attempt: 1, started: '2026-11-09T15:14:51Z', http_status: 429, error_class: 'rate_limit', settled_usd: '0.00000000'},
      {module: 'CP-6', attempt: 0, started: '2026-11-09T15:20:00Z', http_status: 200, error_class: null, settled_usd: '0.01000000'},
    ],
    cap: '12',
  },
};
const out = (id, sections) => ({id, sections, placement: sections.map(() => 'view')});
const input = (over = {}) => ({
  run: {context: RUN, code: 'RUN-A', evidence: EV, methodChanges: ['CP-2A: methods/cp2a.md changed'], steps: [{module: 'CP-2A', started: '2026-11-09T15:13:50Z', accepted: '2026-11-09T15:19:00Z'}, {module: 'CP-6', started: '2026-11-09T15:19:00Z', accepted: '2026-11-09T15:25:00Z'}]},
  modules: [{id: 'CP-2A', outputs: [out('o1', CP2A)]}, {id: 'CP-6', outputs: [out('o2', CP6)]}],
  chips: {'o1:4': [{kind: 'issuer_page', file: 'TDG_10-K.htm.jsonl', page: 5, excerpt: 'Net debt was 9,100.', hash_matches_inventory: true}]},
  deps: {moduleTitle: code => NAMES[code] || code, hashLabel: name => name, methodChange: line => line},
  ...over,
});
const view = (tab, module = null, over) => Evidence.view(input(over), {tab, module});
const ALL_TABS = ['summary', 'trace', 'sources', 'calculations', 'gaps', 'registers', 'record'];
const everyTab = module => ALL_TABS.map(tab => view(tab, module)).join('\n');
// An href inside markup is escaped (& as &amp;).
const attr = (tab, module) => Evidence.href(tab, module, RUN).replace(/&/g, '&amp;');
const strip = html => html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();

test('routes: a deep link and the old Evidence route open the right tab and module (Review Focus 5)', () => {
  const ids = ['CP-2A', 'CP-6'];
  assert.deepEqual(Evidence.parseHash(`#W-Evidence/gaps?c=${RUN}&m=CP-2A`, ids), {tab: 'gaps', module: 'CP-2A'});
  assert.deepEqual(Evidence.parseHash(`#W-Evidence/sources?c=${RUN}`, ids), {tab: 'sources', module: null});
  assert.deepEqual(Evidence.parseHash(`#W-Evidence/trace?c=${RUN}&m=CP+2%2FD%3F`, ['CP 2/D?']), {tab: 'trace', module: 'CP 2/D?'});
  assert.deepEqual(Evidence.parseHash(`#W-Evidence/nonsense?c=${RUN}`, ids), {tab: 'summary', module: null}, 'an unknown tab opens the summary');
  assert.deepEqual(Evidence.parseHash(`#W-Evidence?c=${RUN}`, ids), {tab: 'summary', module: null});
  assert.deepEqual(Evidence.parseHash(`#W-Evidence/%E0%A4%A?c=${RUN}`, ids), {tab: 'summary', module: null}, 'an escape that cannot be decoded names no tab');
  assert.deepEqual(Evidence.parseHash(`#W-Evidence/record?c=${RUN}&m=CP-XX`, ids), {tab: 'record', module: null}, 'a module the run lacks is ignored');
  for (const tab of ALL_TABS) assert.deepEqual(Evidence.parseHash(`#W-Evidence/${tab}`, ids).tab, tab);
});

test('routes: href writes the run and the module the way routeHref and traceHref do', () => {
  assert.equal(Evidence.href('gaps', 'CP-2A', RUN), '#W-Evidence/gaps?c=run-a&m=CP-2A');
  assert.equal(Evidence.href('sources', null, RUN), '#W-Evidence/sources?c=run-a');
  assert.equal(Evidence.href('trace', 'CP 2/D?', 'run-b'), '#W-Evidence/trace?c=run-b&m=CP+2%2FD%3F');
  assert.equal(Evidence.href('summary'), '#W-Evidence/summary');
});

test('rule 7: a hidden section is drawn on no tab, with or without a module filter', () => {
  for (const module of [null, 'CP-2A', 'CP-6']) {
    const html = everyTab(module);
    assert.ok(!html.includes('SECRET REQUEST TEXT'), 'hidden text');
    assert.ok(!html.includes('Zzhiddenheader') && !html.includes('hidden cell'), 'hidden table');
  }
});

test('rule 7: an inter-module column is dropped from every table; a source and an id column stay', () => {
  const html = view('registers', 'CP-2A') + view('calculations', 'CP-2A') + view('gaps', 'CP-2A');
  for (const gone of ['Use in this module', 'Used by CP-6', 'Consumer', 'downstream_use']) assert.ok(!html.includes(gone), gone);
  const registers = view('registers', 'CP-2A');
  assert.ok(registers.includes('>Source<') && registers.includes('TDG_10-K.htm.jsonl p.5'), 'the source column of a finding table');
  assert.ok(registers.includes('>sha256<') && registers.includes('a'.repeat(64)), 'the Sources table');
  const calc = view('calculations', 'CP-2A');
  assert.ok(calc.includes('>Calc ID<') && calc.includes('>C-1<') && calc.includes('a / b') && calc.includes('2.1x'));
});

test('a table is drawn while one non-inter-module column remains; only a table with no column left is not drawn', () => {
  assert.ok(everyTab('CP-2A').includes('ONLYCELL'), 'a one-column table keeps its cells');
  assert.equal(Evidence.tableView({line: 1, headers: ['Consumer', 'downstream_use'], rows: [{line: 2, cells: ['x', 'y']}]}), null);
  assert.equal(Evidence.tableView({line: 1, headers: ['Only'], rows: []}), null, 'no row, nothing to lose');
  assert.deepEqual(Evidence.tableView({line: 1, headers: ['Only'], rows: [{line: 2, cells: ['x']}]}).headers, ['Only']);
  assert.deepEqual(Evidence.tableView({line: 1, headers: ['A', 'Consumer', 'B'], rows: [{line: 2, cells: ['1', 'c', '2']}]}).headers, ['A', 'B']);
  const only = [sec('Findings', 2, 1), sec('Consumers', 3, 2, [table(3, ['Consumer', 'downstream_use'], [['SECRETCELL', 'y']])])];
  assert.ok(!Evidence.view(input({modules: [{id: 'CP-2A', outputs: [out('o1', only)]}]}), {tab: 'registers', module: 'CP-2A'}).includes('SECRETCELL'));
});

test('every column header carries scope="col"', () => {
  const html = view('calculations', 'CP-2A') + view('registers', 'CP-2A') + view('record');
  const heads = html.match(/<th[ >][^>]*>/g) || [];
  assert.ok(heads.length > 5 && heads.every(h => h.includes('scope="col"')), heads.join(' '));
});

test('the tab badge counts what tabCounts counts: the counted [data-hay] elements of the panel are exactly that number, search or no search', () => {
  for (const tab of ['trace', 'sources', 'calculations', 'gaps', 'registers', 'record']) {
    const html = view(tab, 'CP-2A');
    const badge = Number(new RegExp(`id="ev-tab-${tab}"[^>]*aria-current="page"><span>[^<]*</span><span class="ev-cnt" data-count>(\\d+)<`).exec(html)[1]);
    const panel = html.slice(html.indexOf('id="ev-panel"'), html.indexOf('class="ev-card ev-foot"'));
    assert.equal((panel.match(/data-hay="/g) || []).length, badge, tab);
  }
  assert.ok(view('trace', 'CP-2A').includes('<p class="ev-match" role="status"></p>'), 'matches of a query have their own text; the status is in the tree, empty, from the start');
});

test('Run record under a module filter says so when the run records instructions but none for that module', () => {
  assert.ok(view('record', 'CP-6').includes('No instructions recorded for this module.'));
  assert.ok(!view('record', 'CP-2A').includes('No instructions recorded for this module.'));
});

test('Registers needs a module: without one it is a designed prompt, with one it holds the as-written tables and the method notes', () => {
  const prompt = view('registers');
  assert.ok(prompt.includes('class="ev-empty"') && prompt.includes('Pick a module'), prompt);
  assert.ok(!prompt.includes('Maturity register') && !prompt.includes('<table'));
  assert.ok(prompt.includes(`href="${attr('registers', 'CP-6')}"`), 'the prompt links to each module');
  const html = view('registers', 'CP-2A');
  assert.ok(!html.includes('Pick a module'));
  for (const want of ['Maturity register', 'Term loan', 'Tables as written', 'Leverage bridge', 'Net debt', 'Chart data: Net debt', 'FY2023', 'Method notes', 'Module status: accepted with limits.']) assert.ok(html.includes(want), want);
  assert.ok(!html.includes('A finding with a Basis line.'), 'a finding paragraph that is no method note is not a register note');
  assert.ok(/<details class="ev-reg" open/.test(html), 'registers are open so they print and read at once');
});

test('Evidence is complete: every cell and paragraph of a sources, calculations, gaps or registers section is on a tab of its module', () => {
  const union = ALL_TABS.map(tab => strip(view(tab, 'CP-2A'))).join(' ');
  for (const want of ['Calculation notes are written once.', 'C-1', 'c / d', '3.4x', 'Missing lease schedule', 'High', 'Lease note', 'No peer set', 'Peer file', 'Primary', 'Term loan', '4,000']) assert.ok(union.includes(want), want);
});

test('Trace lists statements that carry a Basis line, 40 at a time, with the Basis as written', () => {
  const html = view('trace', 'CP-2A');
  assert.ok(html.includes('Downside is manageable.') && html.includes('calculation C-1') && html.includes('TDG_10-K.htm.jsonl, page 5'));
  assert.ok(!html.includes('Basis:'), 'the Basis line is split off the sentence');
  assert.equal((html.match(/class="ev-trow"/g) || []).length, 2, 'the bottom line and the finding with a Basis line');
  const many = Array.from({length: 45}, (_, i) => text(100 + i, `Statement ${i}.\nBasis: calculation C-${i}`));
  const big = Evidence.view(input({modules: [{id: 'CP-2A', outputs: [out('o1', [sec('Findings', 2, 1), sec('Key findings', 3, 2, many)])]}]}), {tab: 'trace', module: 'CP-2A'});
  assert.equal((big.match(/class="ev-trow"/g) || []).length, 45);
  assert.equal((big.match(/class="ev-trow" hidden/g) || []).length, 5, 'the first 40 are shown');
  assert.ok(big.includes('data-more') && big.includes('Show more'));
  assert.ok(big.includes('Show more (5 remaining)'));
  assert.equal(Evidence.searchPlan({tables: [], items: Array(45).fill('x')}, '', 40).remaining, 5);
});

test('Trace opens a row to the excerpts the build holds for it, by the paragraph key', () => {
  const rows = Evidence.traceRows(input()).filter(r => r.mod === 'CP-2A');
  assert.equal(rows[0].key, 'o1:4');
  const body = Evidence.traceBody(rows[0], input().chips, input().deps);
  assert.ok(body.includes('Net debt was 9,100.') && body.includes('page 5') && body.includes('hash matches inventory'));
  assert.ok(Evidence.traceBody(rows[1], input().chips, input().deps).includes('No excerpt recorded for this statement.'));
});

test('Gaps: a table with a Severity column is cards with the three-segment meter; the cells keep their words', () => {
  const html = view('gaps', 'CP-2A');
  assert.equal((html.match(/class="ev-gap"/g) || []).length, 2);
  assert.ok(html.includes('Missing lease schedule') && html.includes('Required source') && html.includes('Lease note'));
  const high = html.slice(html.indexOf('Missing lease schedule'), html.indexOf('No peer set'));
  assert.equal((high.match(/<i class="f">/g) || []).length, 3, 'High fills three');
  assert.equal(((html.slice(html.indexOf('No peer set')).match(/<i class="f">/g)) || []).length, 1, 'Low fills one');
  assert.ok(html.includes('>High<') && html.includes('>Low<'), 'the word stays beside the meter');
});

test('summary: counts are of listed items only and carry data-count; the guide to the tabs is all the body there is', () => {
  const html = view('summary');
  assert.ok(html.includes('Governance summary'));
  assert.ok(html.includes('<span class="ev-big" data-count>1</span>'), 'one source file listed');
  assert.ok(html.includes('<span class="ev-big" data-count>3</span>'), 'three gap rows across the modules');
  assert.ok(html.includes('<span class="ev-big" data-count>2</span>'), 'two calculation rows');
  assert.ok(html.includes('1 supplied, not used'));
  for (const tab of ALL_TABS.slice(1)) assert.ok(html.includes(`href="${attr(tab, null)}"`), tab);
  assert.ok(html.includes('class="ev-guide"'));
  assert.ok(!html.includes('<table'));
  assert.ok(html.includes('Provider cap USD 12') && html.includes('2026-11-09T15:25:00Z'));
  assert.ok(html.includes('methods/cp2a.md changed'));
});

test('the filter bar and the tabs are on every tab; the active tab and module are marked and linked', () => {
  for (const tab of ALL_TABS) {
    const html = view(tab, 'CP-6');
    assert.ok(html.includes('ev-fbar') && html.includes('id="ev-q"') && html.includes('class="ev-tabs"'), tab);
    assert.ok(html.includes(`id="ev-tab-${tab}" href="${attr(tab, 'CP-6')}" aria-current="page"`), tab);
    assert.ok(html.includes(`id="ev-mod-CP-6" href="${attr(tab, 'CP-6')}" aria-current="true"`), tab);
    assert.ok(html.includes(`id="ev-mod-all" href="${attr(tab, null)}"`), tab);
  }
});

test('Sources: file cards with the hash, a copy button, and the reader stack; supplied but unused files are counted', () => {
  const html = view('sources');
  assert.ok(html.includes('A &lt;report&gt;.pdf') && !html.includes('<report>'));
  assert.ok(html.includes(`data-copy="${'a'.repeat(64)}"`) && html.includes('aria-label="Copy hash of A &lt;report&gt;.pdf"'));
  assert.ok(html.includes('Not recorded'), 'a document date the run does not record');
  assert.ok(html.includes('Supplied, not used') && html.includes('C_unread.htm.jsonl') && html.includes('2024-12-31'));
  assert.equal((html.match(/class="ev-av"/g) || []).length, 2, 'two modules read the file');
  assert.ok(!/<a [^>]*>[^<]*unread/.test(html), 'no link for a source file');
  const one = view('sources', 'CP-6');
  assert.ok(one.includes('A &lt;report&gt;.pdf') && !one.includes('C_unread'), 'a module filter lists the files that module read');
  const none = view('sources', 'CP-6', {run: {...input().run, evidence: {...EV, sources: [{...EV.sources[0], readBy: ['CP-2A']}]}}});
  assert.ok(none.includes('No source file is recorded as read by Committee decision.'));
});

test('Sources: nothing recorded says so; files with no recorded use are "Use not recorded", not "Supplied, not used"', () => {
  const blank = {...EV, sources: [], unused: [], unrecorded: [], noSourcesModules: []};
  const emptyRun = Evidence.view(input({run: {...input().run, evidence: blank}}), {tab: 'sources', module: null});
  assert.ok(emptyRun.includes('The run record lists no supplied files.'));
  const ev = {...blank, unrecorded: [{name: 'D_file.pdf', sha256: 'd'.repeat(64), type: 'pdf', documentDate: null, readBy: []}], noSourcesModules: ['CP-2A', 'CP-6']};
  const html = Evidence.view(input({run: {...input().run, evidence: ev}}), {tab: 'sources', module: null});
  assert.ok(html.includes('Use not recorded') && html.includes('has a Sources section') && html.includes('D_file.pdf') && !html.includes('Supplied, not used'));
  const some = Evidence.view(input({run: {...input().run, evidence: {...EV, noSourcesModules: ['CP-6']}}}), {tab: 'sources', module: null});
  assert.ok(some.includes('No Sources section in the handoff of Committee decision') && !some.includes('Use not recorded'));
  const all = Evidence.view(input({run: {...input().run, evidence: {...EV, unused: []}}}), {tab: 'sources', module: null});
  assert.ok(all.includes('Every supplied file is named in a handoff’s Sources section.'));
});

test('Run record: steps, hashes in full with a copy button, instructions, the cap as written and model calls grouped per module', () => {
  const html = view('record');
  assert.ok(html.includes('class="ev-steps"') && html.includes('2026-11-09T15:13:50Z') && html.includes('2026-11-09T15:25:00Z'));
  assert.ok(html.includes('d'.repeat(64)) && html.includes(`data-copy="${'d'.repeat(64)}"`));
  assert.ok(html.includes('Provider cap USD 12'));
  assert.equal((html.match(/<details class="ev-call"/g) || []).length, 2);
  assert.ok(html.includes('2 calls') && html.includes('1 call<'), html);
  assert.ok(html.includes('0.00941950') && html.includes('rate_limit') && html.includes('Not recorded'), 'a missing error class is not a value');
  assert.ok(html.includes('href="../runs/r/instructions/CP-2A.md" download') && html.includes(`data-copy="${'e'.repeat(64)}"`));
  assert.ok(!/<details class="ev-call"[^>]* open/.test(html), 'model calls are collapsed');
  const one = view('record', 'CP-6');
  assert.equal((one.match(/<details class="ev-call"/g) || []).length, 1);
  assert.ok(!one.includes('rate_limit'));
  const blank = {...EV, record: {hashes: [], instructions: [], calls: [], cap: null}};
  const bare = Evidence.view(input({run: {...input().run, evidence: blank, steps: []}}), {tab: 'record', module: null});
  for (const want of ['The run records no hash.', 'The run records no instructions.', 'The run records no model call.', 'Provider cap not recorded']) assert.ok(bare.includes(want), want);
});

test('every tab ends with the original handoffs, Download all and the Model files, as links', () => {
  for (const tab of ALL_TABS) {
    const html = view(tab);
    assert.ok(html.includes('href="../runs/r/CP-2A.md?sha256=1" download') && html.includes('aria-label="Download Downside handoff"'), tab);
    assert.ok(html.includes('href="downloads/r/handoffs.zip" download') && html.includes('href="/files/m.html" download'), tab);
  }
});

test('every interpolated value is escaped', () => {
  const evil = [sec('Findings', 2, 1), sec('Calculations', 2, 2, [table(3, ['A', 'B'], [['<img src=x onerror=1>', '**bold** & `code`']])])];
  const html = Evidence.view(input({modules: [{id: 'CP-2A', outputs: [out('o1', evil)]}]}), {tab: 'calculations', module: 'CP-2A'});
  assert.ok(!html.includes('<img') && html.includes('&lt;img src=x onerror=1&gt;'));
  assert.ok(html.includes('<strong>bold</strong>') && html.includes('<code>code</code>'));
});

const PLAN = {
  tables: [{head: 'Downside: Leverage bridge Line FY2024 Source', rows: ['downside net debt 9,100', 'downside cash 1,200']}, {head: 'Downside: Maturities Instrument Amount', rows: ['downside term loan 4,000']}],
  items: ['downside hash line abc123', 'downside a note about cash'],
};

test('search plan: a header-only match shows that table with every row and counts once', () => {
  const plan = Evidence.searchPlan(PLAN, 'fy2024');
  assert.deepEqual(plan.tables, [{show: true, rows: [true, true]}, {show: false, rows: [false]}]);
  assert.equal(plan.matches, 1);
  assert.deepEqual(plan.items, [false, false]);
});

test('search plan: a match in one row shows that row only, and counts it', () => {
  const plan = Evidence.searchPlan(PLAN, 'NET   debt');
  assert.deepEqual(plan.tables, [{show: true, rows: [true, false]}, {show: false, rows: [false]}]);
  assert.equal(plan.matches, 1);
});

test('search plan: a query spanning two rows matches nothing', () => {
  const plan = Evidence.searchPlan(PLAN, 'debt 9,100 downside cash');
  assert.equal(plan.matches, 0);
  assert.ok(plan.tables.every(t => !t.show) && plan.items.every(v => !v));
  assert.equal(plan.empty, false, 'a query was typed: Nothing matches shows');
});

test('search plan: a match only in an uncounted item (a hash line) counts one; a note counts too', () => {
  const plan = Evidence.searchPlan(PLAN, 'abc123');
  assert.deepEqual(plan.items, [true, false]);
  assert.equal(plan.matches, 1);
  assert.equal(Evidence.searchPlan(PLAN, 'about cash').matches, 1);
  assert.equal(Evidence.searchPlan(PLAN, 'cash').matches, 2, 'one table row and one note');
});

test('search plan: an empty or blank query restores everything with nothing to count', () => {
  for (const q of ['', '   ']) {
    const plan = Evidence.searchPlan(PLAN, q);
    assert.equal(plan.empty, true);
    assert.equal(plan.matches, 0);
    assert.deepEqual(plan.tables, [{show: true, rows: [true, true]}, {show: true, rows: [true]}]);
    assert.deepEqual(plan.items, [true, true]);
  }
});

test('search plan: a module name or caption in a table head shows the whole table', () => {
  assert.deepEqual(Evidence.searchPlan(PLAN, 'maturities').tables, [{show: false, rows: [false, false]}, {show: true, rows: [true]}]);
});

test('search plan: items beyond the limit are held back and counted as remaining', () => {
  const plan = Evidence.searchPlan({tables: [], items: ['alpha one', 'beta', 'alpha two', 'alpha three']}, 'ALPHA', 2);
  assert.deepEqual(plan.items, [true, false, true, false]);
  assert.equal(plan.matches, 2, 'the count is the visible matched items');
  assert.equal(plan.remaining, 1);
});

test('search plan: an empty or blank query filters nothing but keeps the trace limit', () => {
  for (const q of ['', '   ']) {
    const plan = Evidence.searchPlan({tables: [], items: ['a', 'b', 'c']}, q, 2);
    assert.deepEqual(plan.items, [true, true, false]);
    assert.equal(plan.remaining, 1);
    assert.equal(plan.matches, 0);
    assert.equal(plan.empty, true);
  }
});

test('search plan: paging 100 trace rows with no query: 40/60, then 80/20, then 100/0', () => {
  const items = Array.from({length: 100}, (_, i) => `statement ${i}${i < 50 ? ' alpha' : ''}`);
  for (const [limit, visible, remaining] of [[40, 40, 60], [80, 80, 20], [120, 100, 0]]) {
    const plan = Evidence.searchPlan({tables: [], items}, '', limit);
    assert.equal(plan.items.filter(Boolean).length, visible);
    assert.equal(plan.remaining, remaining);
    assert.ok(plan.items.slice(0, visible).every(Boolean));
  }
});

test('search plan: with a query, the limit applies to matched items; count = visible matched, remaining = matched held back', () => {
  const items = Array.from({length: 100}, (_, i) => `statement ${i}${i < 50 ? ' alpha' : ''}`);
  let plan = Evidence.searchPlan({tables: [], items}, 'ALPHA', 40);
  assert.equal(plan.items.filter(Boolean).length, 40);
  assert.equal(plan.matches, 40);
  assert.equal(plan.remaining, 10);
  plan = Evidence.searchPlan({tables: [], items}, 'ALPHA', 80);
  assert.equal(plan.matches, 50);
  assert.equal(plan.remaining, 0);
  plan = Evidence.searchPlan({tables: [], items: ['alpha one', 'beta', 'alpha two', 'alpha three']}, 'ALPHA', 2);
  assert.deepEqual(plan.items, [true, false, true, false]);
  assert.equal(plan.matches, 2);
  assert.equal(plan.remaining, 1);
});

test('search plan: an empty query with a limit shows every table and row; the limit pages items only', () => {
  const plan = Evidence.searchPlan(PLAN, '', 1);
  assert.deepEqual(plan.tables, [{show: true, rows: [true, true]}, {show: true, rows: [true]}]);
  assert.deepEqual(plan.items, [true, false]);
  assert.equal(plan.remaining, 1);
  assert.equal(plan.matches, 0);
});

test('tables carry their head text; the registers table is counted by data-hay with the head as its text', () => {
  const html = view('registers', 'CP-2A');
  const wrapper = /<div class="ev-tbl"[^>]*aria-label="Downside: Leverage bridge"[^>]*>/.exec(html)[0];
  assert.ok(wrapper.includes('data-head="downside downside: leverage bridge line fy2024 source"'), wrapper);
  assert.ok(wrapper.includes('data-hay="'));
  assert.ok(!/data-hay="[^"]*9,100/.test(wrapper), 'the wrapper holds its head, not its cells');
});

test('a run with no evidence record says so', () => {
  assert.ok(Evidence.view(input({run: {...input().run, evidence: null}}), {tab: 'trace', module: null}).includes('No evidence record was read'));
});

test('classify is the one helper that gives each section its heading chain from the level-2 ancestor and its role (the module page uses it too)', () => {
  const E = require('./evidence.js');
  const sec = (heading, level) => ({ heading, level, line: 1, blocks: [] });
  const out = E.classify([sec('CP-9 handoff', 1), sec('Findings', 2), sec('Bottom line', 3), sec('Events: Dates', 3), sec('Gaps', 2)], []);
  assert.deepEqual(out.map(o => [o.chain, o.role]), [[[], 'registers'], [['Findings'], 'finding'], [['Findings', 'Bottom line'], 'passage'], [['Findings', 'Events: Dates'], 'drawing'], [['Gaps'], 'gaps']]);
});

// Ruling 2026-11-13: a finding paragraph that holds an identifier of the module, or names a calculation, is a method note, drawn in Evidence.
const CP9 = [
  sec('Findings', 2, 1),
  sec('Liquidity', 3, 3, [
    table(5, ['Event ID', 'Event'], [['EV-1', 'Fire'], ['EV-2', 'Flood']]),
    text(10, 'The EV-1 bridge needs review.\nBasis: TDG_10-K.htm.jsonl, page 7'),
    text(11, 'Net debt is shown in calculation D17.'),
    text(12, 'EV-10 is another event, plain finding prose.'),
    text(13, 'Module status: accepted with limits.'),
  ]),
  sec('Bottom line', 3, 20, [text(21, 'The EV-1 line is a passage paragraph and is not a method note.')]),
];
const nine = () => input({modules: [{id: 'CP-2A', outputs: [out('o1', CP2A)]}, {id: 'CP-9', outputs: [out('o9', CP9)]}]});
const nineView = (tab, module = 'CP-9') => Evidence.view(nine(), {tab, module});
const hayCount = html => (html.slice(html.indexOf('id="ev-panel"'), html.indexOf('class="ev-card ev-foot"')).match(/data-hay="/g) || []).length;
const badgeOf = (html, tab) => Number(new RegExp(`id="ev-tab-${tab}"[^>]*aria-current="page"><span>[^<]*</span><span class="ev-cnt" data-count>(\\d+)<`).exec(html)[1]);

test('method notes: an identifier paragraph is under Registers, a calculation paragraph under Calculations; both counted, searchable and complete', () => {
  const registers = nineView('registers'), calcs = nineView('calculations');
  assert.ok(registers.includes('Method notes') && registers.includes('The EV-1 bridge needs review.') && registers.includes('Module status: accepted with limits.'));
  assert.ok(!registers.includes('Net debt is shown in calculation D17.') && !registers.includes('EV-10 is another event') && !registers.includes('is a passage paragraph'), 'only identifier notes, and not findings prose or a passage');
  assert.ok(calcs.includes('Method notes') && calcs.includes('Net debt is shown in calculation D17.') && !calcs.includes('The EV-1 bridge needs review.'));
  assert.ok(/<p class="ev-note" data-hay="cp-9 the ev-1 bridge needs review\./.test(registers), 'the note is searchable by the module name and its words');
  // the tab badge is the number of counted elements, which now include the notes (the status note stays searched, not counted)
  assert.equal(hayCount(registers), badgeOf(registers, 'registers'));
  // A17 (re-ruled): a tab badge is the number its summary tile shows; the Calculations tile counts calculation rows, so a method note is counted by its own group head, not by the badge.
  assert.equal(badgeOf(calcs, 'calculations'), 0, 'no calculation row, so the tile and the badge say 0');
  assert.equal(hayCount(calcs), 1, 'the note is still a counted, searchable element');
  assert.ok(/<span data-count>1<\/span> method note</.test(calcs), 'its own head counts it');
  assert.equal(badgeOf(registers, 'registers'), 2, 'the Liquidity table as written plus the note');
});

test('method notes: the Trace tab still lists the paragraph with its Basis line, and a search plan finds a note as an item', () => {
  const trace = nineView('trace');
  assert.ok(trace.includes('The EV-1 bridge needs review.'));
  const plan = Evidence.searchPlan({tables: [], items: ['downside the ev-1 bridge needs review.', 'other note']}, 'bridge needs');
  assert.deepEqual(plan.items, [true, false]);
  assert.equal(plan.matches, 1);
});

test('method notes: a module with no identifier and no calculation name has none, and the Calculations tab of a module with only a note is not empty', () => {
  const plainOnly = Evidence.view(input(), {tab: 'registers', module: 'CP-2A'});
  assert.ok(!plainOnly.includes('The EV-1 bridge'));
  const onlyCalc = input({modules: [{id: 'CP-9', outputs: [out('o9', [sec('Findings', 2, 1), sec('Bridge', 3, 3, [text(5, 'Uses calculation D17 for net debt.')])])]}]});
  const html = Evidence.view(onlyCalc, {tab: 'calculations', module: 'CP-9'});
  assert.ok(html.includes('Uses calculation D17 for net debt.') && !html.includes('No calculation table is listed'));
});

test('fix 6: a Calculations group head counts calculations only; its method notes carry their own count, and a module with only notes is headed by them', () => {
  const calc = nine().modules[0].outputs[0];
  const html = Evidence.view(input({modules: [{id: 'CP-2A', outputs: [out('o1', [CP2A[0], sec('Bridge', 3, 2, [text(2, 'Net debt follows calculation D17.')]), ...CP2A.slice(1)])]}]}), {tab: 'calculations', module: 'CP-2A'});
  assert.ok(html.includes('<span data-count>2</span> calculations'), 'two calculation rows');
  assert.ok(/<h4 class="ev-sub">Method notes <span class="ev-cnt"><span data-count>1<\/span><\/span><\/h4>/.test(html), 'the note count is its own');
  const onlyNotes = nineView('calculations');
  assert.ok(onlyNotes.includes('<span data-count>1</span> method note') && !/<span data-count>\d+<\/span> calculation/.test(onlyNotes), 'no calculation is counted where there is none');
  assert.ok(calc);
});

// ---- Task 9: the comparison ledger is a Gaps-tab table, as written, counted and searchable.
const LEDGER_HEAD = ['Earlier ref', 'Current ref', 'Limitation', 'Status', 'What closed it', 'Consumer'];
const CP8 = [
  sec('Findings', 2, 1),
  sec('Limitations ledger', 3, 5, [text(6, 'How the two runs\' limitations line up.'), table(7, LEDGER_HEAD, [['E1', '—', 'Earlier <b>limit</b> & "more"', 'No longer stated', '—', 'CP-9'], ['E2', 'C1', 'Carried over', 'Remaining', '—', 'CP-9'], ['—', 'C2', 'A new one', 'New', '—', 'CP-9']])]),
  sec('Other register', 3, 20, [table(21, ['Item', 'Value'], [['Kept', 'in Registers']])]),
  sec('Gaps', 2, 30, [table(31, ['Gap', 'What the pack could not compare', 'Effect', 'Source'], [['Net debt', 'Gross debt is not stated', 'No change figure', 'pack']])]),
];
const cp8Input = () => input({modules: [{id: 'CP-8', outputs: [out('o8', CP8)]}]});
const cp8View = tab => Evidence.view(cp8Input(), {tab, module: 'CP-8'});

test('ledger: its rows are on the Gaps tab, as written minus the inter-module column, and no longer under Registers', () => {
  const gaps = cp8View('gaps'), registers = cp8View('registers');
  for (const cell of ['Earlier ref', 'Current ref', 'What closed it', 'No longer stated', 'Carried over', 'A new one', 'E2', 'C2']) assert.ok(gaps.includes(cell), cell);
  assert.ok(gaps.includes('Earlier &lt;b&gt;limit&lt;/b&gt; &amp; &quot;more&quot;'), 'escaped, not markup');
  assert.ok(!gaps.includes('Consumer') && !gaps.includes('CP-9'), 'the inter-module column is dropped');
  assert.ok(gaps.includes('Limitations ledger'), 'under its own heading');
  assert.ok(gaps.includes('Net debt') && gaps.includes('ev-gap'), 'the Gaps section stays cards');
  assert.ok(!registers.includes('Carried over') && !registers.includes('Earlier ref'), 'drawn once');
  assert.ok(registers.includes('Kept') && registers.includes('How the two runs'), 'other registers and the section\'s prose stay');
});

test('ledger: the Gaps badge, the group count and the counted [data-hay] elements agree (1 gap + 3 ledger rows)', () => {
  const html = cp8View('gaps'), badge = /id="ev-tab-gaps"[^>]*aria-current="page"><span>[^<]*<\/span><span class="ev-cnt" data-count>(\d+)</.exec(html)[1];
  const panel = html.slice(html.indexOf('id="ev-panel"'), html.indexOf('class="ev-card ev-foot"'));
  // A17 (re-ruled): the badge is the number the Gaps tile shows (gap rows); the 3 ledger rows are counted by their own head. Old pin: badge '4' = the panel's 4 counted elements.
  assert.equal(badge, '1', 'the badge is Evidence.gapCount, the number of the tile');
  assert.equal(panel.match(/data-hay=/g).length, 4, 'the panel still lists 1 gap and 3 ledger rows, each counted by its own head');
  // Ruling: ledger rows are not gaps. The gap group's head counts the 1 gap, the ledger's own head counts its 3 rows.
  assert.ok(/<span data-count>1<\/span> gap</.test(panel) && /<span data-count>3<\/span> ledger rows</.test(panel), 'each head says what its number is');
  assert.ok(!/<span data-count>4<\/span>/.test(panel));
  assert.equal(Evidence.gapCount(cp8Input(), 'CP-8'), 1);
  assert.equal(Evidence.ledgerCount(cp8Input(), 'CP-8'), 3);
  assert.equal(Evidence.gapCount(cp8Input()), 1, 'the run-wide count is of gaps too');
  assert.equal(Evidence.gapTotal, undefined, 'one enumeration: the sections-only helper is gone');
  assert.equal(Evidence.ledgerTotal, undefined);
});

test('one gap enumeration: a second saved output of the module is counted by the count, the tab\'s badge and the group head alike', () => {
  const second = [sec('Findings', 2, 1), sec('Gaps', 2, 30, [table(31, ['Gap', 'Severity'], [['Gap B', 'Low'], ['Gap C', 'Low']])])];
  const two = input({modules: [{id: 'CP-8', outputs: [out('o8', CP8), out('o9', second)]}]});
  const html = Evidence.view(two, {tab: 'gaps', module: 'CP-8'});
  assert.equal(Evidence.gapCount(two, 'CP-8'), 3);
  assert.ok(/<span data-count>3<\/span> gaps</.test(html) && /<span data-count>3<\/span> ledger rows</.test(html));
  // A17 (re-ruled): the badge is the gap count (old pin: 6 = 3 gaps + 3 ledger rows; the ledger's 3 are in its own head, asserted above).
  assert.ok(/id="ev-tab-gaps"[^>]*aria-current="page"><span>[^<]*<\/span><span class="ev-cnt" data-count>3</.test(html), 'the badge is the number the tile shows');
  // The governance summary's tile is the same count.
  assert.ok(/Gaps recorded<\/div><span class="ev-big" data-count>3</.test(html));
});

test('the comparison\'s own figures, built from the two runs\' packs, are listed with the calculations of the module that holds the comparison, counted and searchable', () => {
  const comparison = {module: 'CP-8', entries: [{heading: 'Comparison figures', notes: ['Listed as the comparison computed them.'], tables: [{line: 0, headers: ['Measure', 'Earlier', 'Current', 'Difference computed by the comparison'], rows: [{line: 0, cells: ['Coverage', '3.29x (FY2024)', '3.60x (FY2024)', '0.31x']}]}]}]};
  const withIt = input({run: {...input().run, comparison}, modules: [{id: 'CP-8', outputs: [out('o8', CP8)]}, {id: 'CP-6', outputs: [out('o2', CP6)]}]});
  const calc = Evidence.view(withIt, {tab: 'calculations', module: 'CP-8'}), other = Evidence.view(withIt, {tab: 'calculations', module: 'CP-6'});
  assert.ok(calc.includes('Difference computed by the comparison') && calc.includes('0.31x') && calc.includes('Comparison figures'));
  assert.ok(!other.includes('0.31x'), 'only the named module lists it');
  const badge = /id="ev-tab-calculations"[^>]*aria-current="page"><span>[^<]*<\/span><span class="ev-cnt" data-count>(\d+)</.exec(calc)[1];
  // A17 (re-ruled): the badge counts calculation rows only (the tile's number); the comparison's row is counted by its own head. Old pin: badge = every counted element of the panel.
  const panel = calc.slice(calc.indexOf('id="ev-panel"'), calc.indexOf('class="ev-card ev-foot"'));
  assert.equal(panel.match(/data-hay=/g).length, Number(badge) + 1, 'calculation rows by the badge, the one comparison row by its head');
  assert.ok(/<span data-count>1<\/span> comparison row</.test(panel));
  assert.ok(/<tr data-hay="[^"]*coverage[^"]*0\.31x/.test(calc), 'searchable by row');
});

test('ledger: its rows are searchable like the rest of the tab (each row has its own search text, the head matches the whole table)', () => {
  const html = cp8View('gaps'), row = /<tr data-hay="([^"]*)"(?: data-line="\d+")?><td[^>]*>E2</.exec(html);
  assert.ok(row && row[1].includes('carried over') && row[1].includes('remaining'));
  assert.ok(/data-head="[^"]*earlier ref[^"]*"/.test(html));
});

test('ledger: a ledger beside a table that is not one in one section keeps each where it belongs; a section with no ledger is unchanged', () => {
  const mixed = [sec('Findings', 2, 1), sec('Mixed register', 3, 2, [text(3, 'Note kept.'), table(4, ['Earlier ref', 'Current ref', 'Limitation'], [['E1', 'C1', 'L']]), table(9, ['Item', 'Value'], [['Other', '1']])])];
  const html = (tab) => Evidence.view(input({modules: [{id: 'CP-8', outputs: [out('o8', mixed)]}]}), {tab, module: 'CP-8'});
  assert.ok(html('gaps').includes('>E1<') && !html('gaps').includes('>Other<'));
  assert.ok(html('registers').includes('>Other<') && html('registers').includes('Note kept.') && !html('registers').includes('>E1<'));
  const one = input({modules: [{id: 'CP-8', outputs: [out('o8', mixed)]}]});
  assert.equal(Evidence.ledgerCount(one, 'CP-8'), 1);
  assert.equal(Evidence.gapCount(one, 'CP-8'), 0, 'a ledger row is not a gap');
  assert.equal(Evidence.gapCount(input(), 'CP-2A'), 2, 'only the Gaps section counts there');
});

// ---- Task 9 fix round 2: the comparison has its own group and count, and is never unreachable.
const COMPARISON = {module: 'CP-8', entries: [{heading: 'Comparison measures', notes: [], tables: [{line: 0, headers: ['Measure', 'Difference computed by the comparison'], rows: [{line: 0, cells: ['Coverage', '0.31x']}, {line: 0, cells: ['Cash', '0']}]}]}]};
const withComparison = (modules = [{id: 'CP-8', outputs: [out('o8', CP8)]}, {id: 'CP-6', outputs: [out('o2', CP6)]}]) => input({run: {...input().run, comparison: COMPARISON}, modules});

test('the comparison is a group of its own in Calculations, headed by its own row count; the module\'s calculation count and the summary tile name only calculation rows; the badge is both', () => {
  const html = Evidence.view(withComparison([{id: 'CP-2A', outputs: [out('o1', CP2A)]}, {id: 'CP-8', outputs: [out('o8', CP8)]}]), {tab: 'calculations', module: null});
  const panel = html.slice(html.indexOf('id="ev-panel"'), html.indexOf('class="ev-card ev-foot"'));
  assert.ok(/<span data-count>2<\/span> comparison rows</.test(panel) && /<span data-count>2<\/span> calculations</.test(panel), 'each head says what its number is');
  assert.ok(/Calculations recorded<\/div><span class="ev-big" data-count>2</.test(html) && html.includes('rows in the modules’ Calculations tables'), 'the tile counts calculation rows, as its caption says');
  const badge = Number(/id="ev-tab-calculations"[^>]*><span>[^<]*<\/span><span class="ev-cnt" data-count>(\d+)</.exec(html)[1]);
  // A17 (re-ruled): the badge is the tile's number (2 calculation rows); the 2 comparison rows are counted by their own head. Old pin: badge 4 = both.
  assert.equal(badge, 2, 'the badge is the number the tile shows');
  assert.equal(panel.match(/data-hay=/g).length, badge + 2, 'badge parity: calculation rows by the badge, comparison rows by their head');
});

test('a run with a comparison and no entry for the module that holds it lists the figures under a run-level "Comparison" group', () => {
  const html = Evidence.view(withComparison([{id: 'CP-6', outputs: [out('o2', CP6)]}]), {tab: 'calculations', module: null});
  assert.ok(html.includes('>Comparison<') && html.includes('0.31x') && /<span data-count>2<\/span> comparison rows</.test(html));
  const badge = Number(/id="ev-tab-calculations"[^>]*><span>[^<]*<\/span><span class="ev-cnt" data-count>(\d+)</.exec(html)[1]);
  // A17 (re-ruled): no calculation row here, so the badge is 0; the 2 comparison rows are counted by their own head (asserted above).
  assert.equal(badge, 0);
  assert.equal(html.slice(html.indexOf('id="ev-panel"'), html.indexOf('class="ev-card ev-foot"')).match(/data-hay=/g).length, 2, 'the comparison rows are still listed and counted by their head');
  assert.ok(!Evidence.view(withComparison([{id: 'CP-6', outputs: [out('o2', CP6)]}]), {tab: 'calculations', module: 'CP-6'}).includes('0.31x'), 'not under another module');
});

test('net debt, maturity and measure text with <b>&" is escaped where the comparison is drawn', () => {
  const C = require('./changes.js'), evil = '<b>&"x</b>';
  const pack = {measures: [{key: 'k', label: evil, unit: 'x', prior: {value: evil, unit: evil}, current: {value: '2', unit: 'x'}, difference: evil}], net_debt_change: {unit: evil, prior_net_debt: evil, current_net_debt: '1', change_in_gross_debt: evil, change_in_cash: '0', prior_period: evil, current_period: 'FY2', convention: evil},
    maturity_profile: {unit: evil, rows: [{period: evil, prior: evil, current: '1', difference: evil}]}, omitted: {x: evil}};
  const html = Evidence.view(input({run: {...input().run, comparison: C.comparisonEvidence(pack, {verdicts: {measures: {k: {kind: 'comparable', label: evil}}}}, 'CP-8')}, modules: [{id: 'CP-8', outputs: [out('o8', CP8)]}]}), {tab: 'calculations', module: 'CP-8'});
  assert.ok(html.includes('&lt;b&gt;&amp;&quot;x&lt;/b&gt;'));
  assert.ok(!/<b>&"x/.test(html) && !html.includes('&"x'), 'no raw markup survives');
});

test('A13: tableView draws every cell of a ragged row, the extra cell under an empty header', () => {
  const view = Evidence.tableView({line: 1, headers: ['A', 'Consumer', 'B'], rows: [{line: 2, cells: ['1', 'c', '2', 'EXTRA']}, {line: 3, cells: ['3', 'c', '4']}]});
  assert.deepEqual(view.headers, ['A', 'B', '']);
  assert.deepEqual(view.rows.map(row => row.cells), [['1', '2', 'EXTRA'], ['3', '4', '']]);
});

// ---- Whole-branch fix wave 2: M6 (a handoff the build could not read) and L1 (a Gaps section with no table, a "None" row).
const UNREAD = [sec('Unstructured handoff', 1, 1, [text(1, '## Request\nUNREAD-REQUEST-TEXT\n\n## Gaps\n\n| Gap | Effect |\n| --- | --- |\n| Missing schedule | UNREAD-GAP-ROW\n\n## Next module\nUNREAD-NEXT-TEXT')])];
const withUnread = () => input({modules: [{id: 'CP-2A', outputs: [out('o1', CP2A)]}, {id: 'CP-6', outputs: [out('o2', UNREAD)]}]});
const unreadView = (tab, module = 'CP-6') => Evidence.view(withUnread(), {tab, module});

test('M6: an unstructured handoff is drawn as no text; the page says it could not be read and links its file; every count for the module reads "Not read", never 0', () => {
  const STATEMENT = "This module's handoff could not be read into sections. Its file is in the run's downloads.";
  for (const tab of ['trace', 'calculations', 'gaps', 'sources', 'registers']) {
    const html = unreadView(tab);
    assert.ok(!/UNREAD-(REQUEST|GAP-ROW|NEXT)/.test(html), `${tab}: no raw text of the file`);
    assert.ok(strip(html).replace(/&#39;/g, "'").includes(STATEMENT), `${tab}: the statement`);
    assert.ok(html.includes('href="../runs/r/CP-6.md?sha256=2" download'), `${tab}: the module's own download link`);
    assert.ok(new RegExp(`id="ev-tab-${tab}"[^>]*aria-current="page"><span>[^<]*</span><span class="ev-cnt">Not read</span>`).test(html), `${tab}: the badge reads Not read`);
  }
  const summary = unreadView('summary');
  assert.equal((summary.match(/<span class="ev-cnt">Not read<\/span>/g) || []).length, 10, 'the five count tabs, and the five guide cards under them');
  assert.ok(!/id="ev-tab-record"[^>]*><span>[^<]*<\/span><span class="ev-cnt">Not read/.test(summary), 'the run record is the build\'s own, not the handoff\'s');
  const gov = Evidence.view(withUnread(), {tab: 'gaps', module: null});
  assert.ok(gov.includes('aria-label="Committee decision: Not read"'), 'the governance gap bar of the module reads Not read');
  assert.ok(!/Committee decision: 0 gaps/.test(gov));
  assert.ok(!gov.includes('UNREAD-'), 'the whole-run tabs draw none of it either');
  const none = Evidence.view(withUnread(), {tab: 'registers', module: 'CP-6'});
  assert.ok(!none.includes('This module has no register'), 'a bare "nothing listed" does not stand beside the statement');
  assert.equal(Evidence.gapCount(withUnread(), 'CP-6'), 0, 'the pure count is unchanged; the page words its state');
});

test('M6: a module with one readable and one unstructured output keeps its readable content and still reads Not read', () => {
  const both = input({modules: [{id: 'CP-6', outputs: [out('o2', CP6), out('o3', UNREAD)]}]});
  const html = Evidence.view(both, {tab: 'gaps', module: 'CP-6'});
  assert.ok(html.includes('Thin liquidity note') && !html.includes('UNREAD-') && /id="ev-tab-gaps"[^>]*><span>[^<]*<\/span><span class="ev-cnt">Not read</.test(html));
});

test('L1: a Gaps section that holds text and no table is "Listed as text", not 0; a row whose first cell says None, No, Nil or N/A is not a gap', () => {
  const bullets = [sec('Findings', 2, 1), sec('Gaps', 2, 10, [text(11, '- Covenant package not read.\n- Facility agreement not parsed.')])];
  const noneRows = [sec('Findings', 2, 1), sec('Gaps', 2, 10, [table(11, ['Gap', 'Effect'], [['None', 'n/a']])])];
  const mixed = [sec('Findings', 2, 1), sec('Gaps', 2, 10, [text(11, 'These gaps stay open.'), table(12, ['Gap', 'Effect'], [['**None**.', 'x'], ['N/A', 'x'], ['nil', 'x'], ['No', 'x'], ['Missing lease note', 'High'], ['None of the leases are read', 'x']])])];
  const run = sections => input({modules: [{id: 'CP-6', outputs: [out('o2', sections)]}]});
  assert.equal(Evidence.gapCount(run(bullets), 'CP-6'), 0);
  assert.equal(Evidence.gapCount(run(noneRows), 'CP-6'), 0, 'a None row is not a gap');
  assert.equal(Evidence.gapCount(run(mixed), 'CP-6'), 2, 'only the two real rows; "None of the leases are read" is a gap');
  const textual = Evidence.view(run(bullets), {tab: 'gaps', module: 'CP-6'});
  assert.ok(textual.includes('Listed as text') && !/<span data-count>0<\/span> gaps/.test(textual), 'the group head says how the gaps are written');
  assert.ok(textual.includes('aria-label="Committee decision: Listed as text"') || textual.includes('CP-6: Listed as text'), 'and so does the governance bar');
  const nothing = Evidence.view(run(noneRows), {tab: 'gaps', module: 'CP-6'});
  assert.ok(nothing.includes('None stated') && !/<span data-count>0<\/span> gaps/.test(nothing), 'a table that says only "None" is the module saying so, not a count of 0');
  assert.ok(nothing.includes('Committee decision: None stated'), 'and so is its governance bar');
  const noSection = Evidence.view(run([sec('Findings', 2, 1)]), {tab: 'gaps', module: 'CP-6'});
  assert.ok(Evidence.gapCount(run([sec('Findings', 2, 1)]), 'CP-6') === 0 && !noSection.includes('None stated') && !noSection.includes('Listed as text'), 'a module with no Gaps section keeps the plain zero of the bar');
  assert.ok(Evidence.view(run([sec('Findings', 2, 1)]), {tab: 'summary', module: null}).includes('Committee decision: 0 gaps'));
  assert.ok(Evidence.view(run(mixed), {tab: 'gaps', module: 'CP-6'}).includes('<span data-count>2</span> gaps'));
});

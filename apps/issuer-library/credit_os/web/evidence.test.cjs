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
  assert.equal(hayCount(calcs), badgeOf(calcs, 'calculations'));
  assert.equal(badgeOf(calcs, 'calculations'), 1);
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

'use strict';
// Static assertions on the Credit OS shell: library and issuer pages only, no run controls, no server calls.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const read = name => fs.readFileSync(path.join(__dirname, name), 'utf8');

test('index.html carries no run-control destinations', () => {
  const html = read('index.html');
  for (const forbidden of ['W-NewRun', 'W-Settings', 'W-Help']) {
    assert.ok(!html.includes(forbidden), `index.html still contains ${forbidden}`);
  }
  assert.ok(html.includes('href="#CP-OS/activity"'), 'the rail links to Run activity');
});

test('the shell has no run controls: no form, no start/resume/stop button, no run strip', () => {
  for (const name of ['index.html', 'static-boot.js', 'views.js', 'screen.js', 'shared.js']) {
    const text = read(name);
    // The only form is the library's client-side filter (it submits nothing); no other form exists.
    const forms = [...text.matchAll(/<form[\s>][^>]*/gi)].map(m => m[0]);
    assert.ok(forms.every(f => f.includes('id="library-filters"')), `${name} contains a form: ${forms}`);
    assert.ok(!text.includes('run-strip'), `${name} contains run-strip`);
    for (const button of text.matchAll(/<button\b[^>]*>[^<]*/gi)) {
      assert.ok(!/start|resume|stop|new run/i.test(button[0]), `${name} has a run-control button: ${button[0]}`);
    }
  }
});

test('scripts make no server calls and poll nothing', () => {
  for (const name of ['static-boot.js', 'views.js', 'screen.js', 'shared.js']) {
    const text = read(name);
    assert.ok(!text.includes('fetch('), `${name} contains fetch(`);
    assert.ok(!text.includes('setInterval('), `${name} contains setInterval(`);
  }
});

test('scripts make no server calls or intervals; the only re-load is swapActivityScript, called from the activity timer', () => {
  for (const name of ['static-boot.js', 'views.js', 'screen.js', 'shared.js']) {
    const text = read(name);
    for (const banned of ['fetch(', 'XMLHttpRequest', 'WebSocket', 'setInterval(']) assert.ok(!text.includes(banned), `${name} contains ${banned}`);
  }
  const calls = name => ['static-boot.js', 'views.js', 'screen.js', 'shared.js'].flatMap(f => [...read(f).matchAll(new RegExp(`${name}\\(`, 'g'))].map(() => f));
  assert.deepEqual(calls('swapActivityScript'), ['views.js', 'screen.js', 'screen.js'], 'one definition, two calls');
  const screen = read('screen.js');
  const timer = screen.slice(screen.indexOf('function syncActivityTimer('), screen.indexOf('let lastActivity'));
  assert.strictEqual(timer.split('swapActivityScript(').length - 1, 2, 'both calls (on entering, on the tick) sit inside syncActivityTimer');
});

test('installDestinations keys are exactly the library and issuer pages plus Run activity', () => {
  const text = read('views.js');
  const start = text.indexOf('const destinations={');
  assert.ok(start >= 0, 'destinations table not found');
  const end = text.indexOf('};', start);
  const keys = [...text.slice(start, end).matchAll(/^\s*'([^']+)':\[/gm)].map(m => m[1]);
  assert.deepEqual(keys, ['W-Library', 'W-Overview', 'W-Calendar', 'W-Reports', 'W-Evidence', 'W-Forecast', 'CP-OS']);
  const row = text.slice(text.indexOf("'CP-OS':["), end);
  assert.deepEqual([...row.matchAll(/\['([^']+)','[^']*',\[\]\]/g)].map(m => m[1]), ['activity']);
});

// Pull the pure activityView out of views.js and run it with a stand-in esc and icon.
const activityView = () => {
  const text = read('views.js');
  const start = text.indexOf('function activityView(');
  const end = text.indexOf('function workspaceView(');
  assert.ok(start >= 0 && end > start, 'activityView not found');
  const esc = v => String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  return new Function('esc', 'icon', `${text.slice(start, end)}; return activityView;`)(esc, n => `<img src="icons/${n}.svg">`);
};

test('Run activity lists excluded folders with reasons, then issues', () => {
  const html = activityView()({ excluded: [['run-half', 'no <CP-1A> output'], ['legacy', 'not a run']], issues: ['store: bad pin'] });
  for (const want of ['run-half', 'no &lt;CP-1A&gt; output', 'legacy', 'not a run', 'store: bad pin', 'Run folders not shown']) {
    assert.ok(html.includes(want), `missing ${want}`);
  }
  assert.ok(!/<(button|form|input|a )/i.test(html), 'Run activity carries no control');
});

test('Run activity says so when there is nothing to report', () => {
  const html = activityView()({ excluded: [], issues: [] });
  assert.ok(html.includes('Nothing to report') && !html.includes('<li'));
});

test('Run activity never shows the all-clear when its data is missing', () => {
  const html = activityView()(null);
  assert.ok(html.includes('could not be read'));
  assert.ok(!html.includes('Nothing to report') && !html.includes('raised no issues'));
  const boot = read('static-boot.js');
  assert.ok(boot.includes('activity=null') && !boot.includes('activity={excluded:[],issues:[]}'));
});

test('Forecast for a run with no CP-2G output says no model was published', () => {
  const views = read('views.js');
  assert.ok(views.includes('if(!models.length)return forecastEmpty(context);'));
  assert.ok(views.includes('No forecast model was published from this run’s files'));
});

test('calendar.js loads before the screens and screen.js carries no hard-coded event dates', () => {
  const boot = read('static-boot.js');
  assert.ok(boot.indexOf("'calendar.js'") >= 0 && boot.indexOf("'calendar.js'") < boot.indexOf("'views.js'"));
  assert.ok(!read('screen.js').includes('May 8, 2023'));
  assert.ok(!read('screen.js').includes('const order={') && !read('views.js').includes('data[pins[module]]?.run'));
});

test('the navigator names every module in catalog.json', () => {
  const catalog = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'catalog.json'), 'utf8'));
  const text = read('screen.js');
  const start = text.indexOf('const groups = ['), end = text.indexOf('const unnamed');
  const listed = new Set([...text.slice(start, end).matchAll(/\['(CP-[A-Z0-9]+)',/g)].map(m => m[1]));
  assert.equal(Object.keys(catalog).length, 20);
  for (const id of Object.keys(catalog)) assert.ok(listed.has(id), `${id} missing from the navigator groups`);
  // Owner ruling 2026-11-09: a module with no saved output reads "No output found" in the navigator and on the canvas.
  assert.ok(read('views.js').includes("const NO_OUTPUT='No output found'"));
});

// ---- The module report: views.js evaluated over a hand-written output, with stand-ins for the screen.js globals it calls.
const OUT = 'run-a/deliveries/d1/CP-1.md';
// The workspace's module names, as the fixtures use them.
const NAMES = { 'CP-0': 'Source readiness', 'CP-1': 'Financial foundation', 'CP-1A': 'Business & governance', 'CP-6': 'Committee decision' };
const table = (line, headers, rows) => ({ type: 'table', line, headers, rows: rows.map(([n, ...cells]) => ({ line: n, cells })) });
const text = (line, body) => ({ type: 'text', line, text: body });
// `where` is the placement the store would give the section (Task 1); report() turns it into the output's parallel `placement` list.
const sec = (heading, level, line, where, blocks) => ({ heading, level, line, where, blocks });
const ref = (heading, line, blocks) => sec(heading, 3, line, 'reference', blocks);
const view = (heading, line, blocks) => sec(heading, 3, line, 'view', blocks);
// The store's summary.findings for the Reader summary below (the page draws these, not the tables).
const READER_FINDINGS = [{ finding: 'Leverage rose.', impact: 'Higher gross leverage.', confidence: 'High', line: 16 }, { finding: 'Cash rose.', impact: 'More cushion.', confidence: 'Medium', line: 17 }];
const SECTIONS = [
  sec('Reader summary', 3, 10, 'consumed', [
    table(12, ['Bottom line', 'Confidence', 'Main limitation'], [[13, 'Cash up.', 'Medium', 'Synthetic.']]),
    table(15, ['Finding', 'Creditor impact', 'Confidence'], [[16, 'Leverage rose.', 'Higher gross leverage.', 'High'], [17, 'Cash rose.', 'More cushion.', 'Medium']]),
  ]),
  ref('Liquidity table', 20, [
    table(22, ['Measure', 'FY2023', 'FY2024', 'Unit', 'Note', 'Extra1', 'Extra2'], [
      [23, 'Cash', '3,472', '6,261', 'US$m', 'a very long note that is longer than twenty-four characters', 'e1', 'e2'],
      [24, 'Coupons', 'Not supplied', '', 'US$m', 'x', 'e1', 'e2'], [25, 'A', '1', '2', 'US$m', 'x', 'e1', 'e2'], [26, 'B', '1', '2', 'US$m', 'x', 'e1', 'e2'],
      [27, 'C', '1', '2', 'US$m', 'x', 'e1', 'e2'], [28, 'D', '1', '2', 'US$m', 'x', 'e1', 'e2'], [29, 'E', '1', '2', 'US$m', 'x', 'e1', 'e2'], [30, 'F', '1', '2', 'US$m', 'x', 'e1', 'e2'], [31, 'G', '1', '2', 'US$m', 'x', 'e1', 'e2'],
    ]),
  ]),
  view('Liquidity view', 34, [text(35, 'Liquidity is **ample** through FY2025.')]),
  view('T2F.1 — Macro source gate', 36, [text(37, 'The macro gate is open.')]),
  sec('Chart data: leverage', 3, 40, 'consumed', [table(42, ['Period', 'Total debt / EBITDA', 'Reporting unit', 'Basis'], [[43, 'FY2024', '6.57', 'x', 'K, page:123'], [44, 'FY2023', '', 'x', 'none']])]),
  ref('Debt register', 45, [table(46, ['Instrument', 'Maturity', 'Amount'], [[47, 'Term loan', 'FY2028', '1,200'], [48, 'Notes', 'FY2030', '700']])]),
  sec('Gaps', 2, 50, 'limits', [text(52, 'Coupons are **not supplied**.')]),
  sec('Calculation trace', 3, 56, 'calculations', [text(57, 'Net debt is 1,200 less 3,472.')]),
  sec('Sources', 2, 60, 'audit', [text(62, 'K.')]),
  sec('Extra notes', 2, 64, 'audit', [text(65, 'Reviewer note.')]),
];
// Hand-written word counts per placement (the store computes them; the page prints them).
const WORDS = { view: 12, reference: 40, calculations: 8, limits: 5, audit: 9 };
const CHIPS = {
  [`${OUT}:16`]: [
    { kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 123, page_end: null, quote: '6.57', quote_found: true, excerpt: 'Debt 6.57 times', reason: null, hash_matches_inventory: true },
    { kind: 'issuer_page', source: 'M', file: 'M.jsonl', page: 70, page_end: 71, hash_matches_inventory: null, quote_found: null, excerpt: null },
    { kind: 'upstream', module: 'CP-1A', codes: ['E2'] },
    { kind: 'upstream', module: null, codes: ['D1', 'D3'] },
  ],
  [`${OUT}:777`]: [{ kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 1, page_end: null, quote_found: null, reason: 'Annual PDF marked alternate in CP-0' }, { kind: 'upstream', module: 'CP-9Z', codes: ['D1'] }],
  [`${OUT}:43`]: [{ kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 123, page_end: null }],
  [`${OUT}:52`]: [{ kind: 'gap', label: 'Not supplied', reason: 'the row says so', codes: [] }, { kind: 'gap', label: 'no page', codes: [] }, { kind: 'gap', label: 'p.145 · no key', codes: [] }],
  [`${OUT}:53`]: [{ kind: 'gap', label: 'no page', codes: [] }, { kind: 'gap', label: 'p.7 · no key', codes: [] }],
  [`${OUT}:54`]: [{ kind: 'gap', label: 'Annual p.9 · ambiguous', codes: [] }],
};
const DEFAULT_MODULES = [
  ['summary', 'Reader summary', ['Reader summary']], ['liquidity', 'Liquidity table', ['Liquidity table']], ['view', 'Liquidity view', ['Liquidity view']],
  ['gate', 'T2F.1 — Macro source gate', ['T2F.1 — Macro source gate']], ['leverage', 'Chart data', ['Chart data']], ['debt', 'Debt register', ['Debt register']],
  ['gaps', 'Gaps & limitations', ['Gaps']], ['calc', 'Calculation trace', ['Calculation trace']], ['sources', 'Sources', ['Sources']], ['extra', 'Extra notes', ['Extra notes']],
  ['audit', 'Technical audit', ['Request']],
];
function report(overrides = {}, modSections = null) {
  const src = read('views.js');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const plain = v => String(v).replace(/\*\*|`/g, '');
  const rich = v => esc(v).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  const sections = overrides.sections || SECTIONS;
  const out = { module: 'CP-1', run: 'run-a', source: 'deliveries/d1/CP-1.md', href: '../runs/run-a/deliveries/d1/CP-1.md', label: 'CP-1', sections,
    placement: sections.map(s => s.where), state: { established: true, declared: null }, words: WORDS,
    summary: { bottomLine: 'Cash up.', confidence: 'Medium', limitation: 'Synthetic.', line: 13, findings: READER_FINDINGS }, charts: [{ title: 'Leverage', unit: 'x', table: 42, columns: [1] }], ...overrides };
  const data = { [OUT]: out };
  const modules = { [OUT]: { sections: modSections || DEFAULT_MODULES } };
  const evidence = new Map();
  for (const s of out.sections) for (const b of s.blocks) {
    if (b.type === 'table') for (const r of b.rows) evidence.set(`${OUT}:${r.line}`, { module: 'CP-1', line: r.line });
    else evidence.set(`${OUT}:${b.line}`, { module: 'CP-1', line: b.line });
  }
  const win = { CREDIT_OS_DATA: { chips: CHIPS }, DESIGN_CATALOGUE: { real: [{ id: 'run-a', checklist: null }] }, DESIGN_WORKSPACE: { reports: [] } };
  const sectionData = (id, sid) => out.sections.filter(s => modules[id].sections.find(x => x[0] === sid)[2].some(p => s.heading.startsWith(p)));
  const names = ['window', 'data', 'modules', 'contexts', 'store', 'moduleNames', 'esc', 'plain', 'rich', 'icon', 'pins', 'evidence', 'current', 'isAnalytical', 'sectionData', 'lastFile', 'aliases'];
  const args = [win, data, modules, { 'run-a': { folder: 'run-a', modules: { 'CP-1': { outputs: [OUT], default: OUT } } } }, {}, NAMES, esc, plain, rich, n => `<img src="icons/${n}.svg">`, {}, evidence, { context: 'run-a', section: 'head', module: 'CP-1' }, id => !id.startsWith('W-'), sectionData, new Map(), { 'CP-6A': 'CP-6' }];
  return new Function(...names, `${src}; return {moduleReport, reportParts, reportAnalysis, reportReference, reportCalculations, reportHead, chipsMarkup, chipView, keyNumbers, reportLimits, reportAudit, reportBand, outlineMarkup, navigationSections, drawnAnchors, availability, unavailableView, REPORT_PARTS, METHOD_CODE, moduleTitle, handoffLabel};`)(...args);
}
const strip = html => html.replace(/<[^>]+>/g, '');
const summaryOf = (html, id) => strip(new RegExp(`<details[^>]*id="${id}"[^>]*><summary>(.*?)</summary>`).exec(html)[1]);
const NINE = ['head', 'bottom-line', 'numbers', 'findings', 'analysis', 'limits', 'reference', 'calculations', 'audit'];
const NINE_RE = /\bid="(head|bottom-line|numbers|findings|analysis|limits|reference|calculations|audit)"/g;
const anchorsOf = (html, re = NINE_RE) => [...html.matchAll(re)].map(m => m[1]);

test('(a) the module report has the nine anchors once each, in order', () => {
  const html = report().moduleReport(OUT);
  assert.deepEqual(anchorsOf(html), NINE);
  assert.deepEqual(report().REPORT_PARTS.map(p => p[0]), NINE);
  assert.deepEqual(report().REPORT_PARTS.map(p => p[1]), ['Module', 'Bottom line', 'Key numbers', 'Findings', 'Analysis', 'Limits & monitoring', 'Statements and registers', 'Calculations', 'Evidence & audit']);
  // The head names the module by its name alone: no code line, no title; the file name and section count are production detail (Evidence & audit).
  assert.ok(html.includes('Candidate · not accepted') && html.includes('<h2>Financial foundation</h2>') && !html.includes('class="sub"'));
  assert.ok(!html.includes('Current methodology') && !html.includes('<code>CP-1.md</code>'));
  // The band's link says what it does; the module's handoff and line are its title.
  assert.ok(html.includes('Quoted from the handoff') && html.includes('title="Financial foundation handoff, line 13">View source</button>'));
  const r = report();
  assert.deepEqual(r.reportParts(OUT).map(p => p[0]), NINE);
  assert.deepEqual(r.navigationSections('CP-1', 'run-a', OUT).map(s => s[0]), NINE);
  assert.equal(r.reportParts(OUT).map(p => p[2]).join(''), html);
});

test('(b) a handoff with no view and no calculations section omits both parts, their outline entries and any empty-part text', () => {
  const r = report({ sections: SECTIONS.filter(s => s.where !== 'view' && s.where !== 'calculations') });
  const html = r.moduleReport(OUT);
  assert.deepEqual(anchorsOf(html), ['head', 'bottom-line', 'numbers', 'findings', 'limits', 'reference', 'audit']);
  assert.ok(!html.includes('id="analysis"') && !html.includes('id="calculations"') && !html.includes('part-empty'));
  const outline = r.outlineMarkup(OUT);
  assert.ok(!outline.includes('>Analysis<') && !outline.includes('>Calculations<'));
  assert.equal(outline.match(/class="section-item"/g).length, 7);
});

test('a handoff with nothing to read keeps only its head and the audit list, and says nothing about the rest', () => {
  const html = report({ summary: null, call: null, charts: [], sections: [] }).moduleReport(OUT);
  assert.deepEqual(anchorsOf(html), ['head', 'audit']);
  assert.ok(!html.includes('part-empty') && !html.includes('No bottom line'));
});

test('(c) a not-assessable module has head, band, findings, limits, one closed fold and the audit list', () => {
  const r = report({ state: { established: false, declared: null } });
  const html = r.moduleReport(OUT);
  assert.deepEqual(anchorsOf(html, /\bid="(head|bottom-line|numbers|findings|limits|handoff-text|audit)"/g), ['head', 'bottom-line', 'findings', 'limits', 'handoff-text', 'audit']);
  const tag = /<details[^>]*id="handoff-text"[^>]*>/.exec(html)[0];
  assert.ok(!/\bopen\b/.test(tag), tag);
  assert.equal(summaryOf(html, 'handoff-text'), 'Full handoff text · 60 words'); // 12 view + 40 reference + 8 calculations
  assert.ok(html.indexOf('id="handoff-text"') < html.indexOf('id="analysis"') && html.indexOf('id="analysis"') < html.indexOf('id="audit"'));
  assert.ok(!html.includes('id="numbers"'));
  assert.deepEqual(r.navigationSections('CP-1', 'run-a', OUT).map(s => s[0]), ['head', 'bottom-line', 'findings', 'limits', 'handoff-text', 'audit']);
});

test('(d) a module with no reader summary keeps the full page with no band and no fold', () => {
  // No reader summary means no Reader summary section: the fixture drops it with the summary.
  const html = report({ state: { established: null, declared: null }, summary: null, sections: SECTIONS.filter(s => s.heading !== 'Reader summary') }).moduleReport(OUT);
  assert.deepEqual(anchorsOf(html), ['head', 'numbers', 'analysis', 'limits', 'reference', 'calculations', 'audit']);
  assert.ok(!html.includes('handoff-text'));
});

test('(e) Statements and registers is a closed fold of the reference sections, whole, in handoff order', () => {
  const r = report(), html = r.reportReference(OUT);
  assert.ok(!/\bopen\b/.test(/<details[^>]*id="reference"[^>]*>/.exec(html)[0]));
  assert.equal(summaryOf(html, 'reference'), 'Statements and registers · 2 tables · 11 rows'); // Liquidity table 9 rows, Debt register 2
  assert.ok(html.indexOf('id="s-20"') > 0 && html.indexOf('id="s-20"') < html.indexOf('id="s-45"'));
  assert.equal(html.match(/<tr><td>/g).length, 11); // no row dropped
  assert.ok(html.includes('>Extra2<') && html.includes('a very long note that is longer than twenty-four characters') && !html.includes('more rows'));
  assert.ok(!html.includes('Reader summary') && !html.includes('Chart data') && !html.includes('Liquidity view') && !html.includes('Calculation trace'));
  assert.equal(summaryOf(report({ sections: SECTIONS.filter(s => s.heading !== 'Debt register') }).reportReference(OUT), 'reference'), 'Statements and registers · 1 table · 9 rows');
});

test('(f) Calculations is a closed fold of the calculations sections, whole', () => {
  const html = report().reportCalculations(OUT);
  assert.ok(!/\bopen\b/.test(/<details[^>]*id="calculations"[^>]*>/.exec(html)[0]));
  assert.equal(summaryOf(html, 'calculations'), 'Calculations · 8 words');
  assert.ok(html.includes('id="s-56"') && html.includes('Net debt is 1,200 less 3,472.') && html.includes('aria-label="Handoff row, line 57"'));
});

test('(g) a leading method code is dropped from a displayed heading and kept nowhere', () => {
  const sections = ['T2F.1 — Macro source gate', 'cp2b.cp_model_catalysts — blocked interface', 'TDR.1 — Research brief', 'Net debt — bridge'].map((h, i) => view(h, 100 + 10 * i, [text(101 + 10 * i, 'x')]));
  const html = report({ sections }).reportAnalysis(OUT);
  assert.ok(html.includes('<h4>Macro source gate</h4>'));
  assert.ok(html.includes('<h4>blocked interface</h4>'));
  assert.ok(html.includes('<h4>Research brief</h4>'));
  assert.ok(!/<h4 title=/.test(html), 'no title keeps the id');
  assert.ok(html.includes('<h4>Net debt — bridge</h4>'));
  assert.equal(report().METHOD_CODE.source, '^([A-Z][A-Z0-9]*\\.[A-Z]?\\d+|[a-z0-9]+(\\.[a-z0-9_]+)+)\\s+—\\s+');
  // The code goes from Limits, Reference and Calculations headings too, and stays in the audit list (the handoff's own section names).
  const coded = [sec('C.1 — Gap list', 2, 100, 'limits', [text(101, 'g')]), ref('T4.D1 — Register', 110, [table(111, ['A', 'B'], [[112, 'x', 'y']])]), sec('T2F.2 — Trace', 3, 120, 'calculations', [text(121, 'c')]), sec('T3D.1 — Source map', 3, 130, 'audit', [text(131, 'a')])];
  const r = report({ sections: coded }, [['gap', 'C.1 — Gap list', ['C.1']], ['reg', 'T4.D1 — Register', ['T4.D1']], ['trace', 'T2F.2 — Trace', ['T2F.2']], ['map', 'T3D.1 — Source map', ['T3D.1']]]);
  assert.ok(r.reportLimits(OUT).includes('<h4>Gap list</h4>'));
  assert.ok(r.reportReference(OUT).includes('<h4>Register</h4>'));
  assert.ok(r.reportCalculations(OUT).includes('<h4>Trace</h4>'));
  const audit = r.reportAudit(OUT);
  assert.ok(audit.includes('T3D.1 — Source map') && !audit.includes('T2F.2 — Trace') && !audit.includes('Gap list'));
});

test('(h) a section placed audit is in the Evidence & audit list and in no other part', () => {
  const r = report(), html = r.moduleReport(OUT);
  const audit = r.reportAudit(OUT), rest = html.replace(audit, '');
  assert.ok(audit.includes('Extra notes') && audit.includes('<span>L64</span>'));
  assert.ok(!rest.includes('Extra notes') && !rest.includes('Reviewer note.') && !html.includes('id="s-64"'));
  // Consumed and audit sections are listed; what a part draws is not.
  for (const listed of ['Reader summary', 'Chart data', 'Sources', 'Technical audit']) assert.ok(audit.includes(listed), listed);
  for (const drawn of ['Liquidity table', 'Liquidity view', 'Debt register', 'Gaps &amp; limitations', 'Calculation trace']) assert.ok(!audit.includes(drawn), drawn);
});

test('(i) the declared status is a badge beside the acceptance badge; none declared means the acceptance badge only', () => {
  const blocked = report({ state: { established: true, declared: 'Blocked' } }).reportHead(OUT);
  assert.ok(blocked.includes('<span class="badge badge-gray" title="Status the module declares in its handoff">Blocked</span>') && blocked.includes('Candidate · not accepted'));
  assert.equal(blocked.match(/class="badge badge-gray"/g).length, 2);
  assert.ok(blocked.indexOf('Candidate · not accepted') < blocked.indexOf('>Blocked<'));
  const none = report({ state: { established: true, declared: null } }).reportHead(OUT);
  assert.equal(none.match(/class="badge badge-gray"/g).length, 1);
  assert.ok(!none.includes('Blocked'));
});

test('(j) Analysis holds only the view sections, open, in handoff order, each with its line id', () => {
  const html = report().reportAnalysis(OUT);
  assert.ok(html.startsWith('<section class="part" id="analysis"><h3>Analysis</h3>') && !html.includes('<details'));
  assert.deepEqual([...html.matchAll(/class="analysis-section" id="(s-\d+)"/g)].map(m => m[1]), ['s-34', 's-36']);
  assert.ok(html.includes('Liquidity is <strong>ample</strong> through FY2025.') && html.includes('aria-label="Handoff row, line 35"'));
  for (const other of ['Liquidity table', 'Debt register', 'Calculation trace', 'Coupons', 'Reader summary', 'Extra notes']) assert.ok(!html.includes(other), other);
});

test('the sections a part draws are the routable s-<line> anchors; audit and consumed sections are not', () => {
  const ids = [...report().drawnAnchors(OUT)];
  assert.deepEqual(ids.sort(), ['s-20', 's-34', 's-36', 's-45', 's-50', 's-56']);
});

test('chip labels and avatars follow the data, one chip per dict', () => {
  const { chipsMarkup } = report();
  const html = chipsMarkup(`${OUT}:16`);
  const chips = [...html.matchAll(/<button[^>]*class="chip[^"]*"[^>]*>.*?<\/button>/g)].map(m => m[0].replace(/<[^>]+>/g, '|').replace(/\|+/g, '|'));
  assert.deepEqual(chips, ['|Handoff|', '|K|p.123|', '|M|p.70–71|', '|Business &amp; governance · E2|', '|Financial foundation · D1 · D3|']);
  assert.ok(html.includes('data-chip="run-a/deliveries/d1/CP-1.md:16" data-index="3"') && html.includes('data-evidence="run-a/deliveries/d1/CP-1.md:16"'));
});

test('Not supplied renders as a gap chip; other gaps fold into one count', () => {
  const html = report().chipsMarkup(`${OUT}:52`);
  assert.ok(html.includes('</span>Not supplied<span') && html.includes('<span class="av gap">?</span>') && html.includes('title="the row says so"'));
  assert.equal(html.match(/class="chip gap"/g).length, 1);
  assert.equal(html.includes('no page<span') || html.includes('no key<span'), false);
  assert.equal(html.match(/class="chip-count"/g).length, 1);
  assert.ok(html.includes(`data-gaps="${OUT}:52"`) && html.includes('>2 citations without a page</button>'));
});

test('a key of only unresolved chips has no gap chip and one count; one reads in the singular', () => {
  const { chipsMarkup } = report();
  const two = chipsMarkup(`${OUT}:53`);
  assert.equal(two.includes('class="chip gap"'), false);
  assert.equal(two.match(/class="chip-count"/g).length, 1);
  assert.ok(two.includes('>2 citations without a page</button>'));
  assert.ok(chipsMarkup(`${OUT}:54`).includes('>1 citation without a page</button>'));
});

test('a quote found on the page marks the chip verified', () => {
  const html = report().chipsMarkup(`${OUT}:16`);
  assert.ok(html.includes('class="chip verified"') && html.includes('title="Quote found on page"'));
  assert.equal(html.match(/class="chip verified"/g).length, 1);
  assert.equal(html.includes('chip-count'), false);
});

test('a key with no chips and no evidence draws nothing', () => {
  assert.equal(report().chipsMarkup('run-a/deliveries/d1/CP-1.md:999'), '');
});

test('key numbers: the first reader table with two numeric columns, 8 rows, 5+source columns, n.a. with a title', () => {
  const html = report().keyNumbers(OUT);
  assert.equal(html.match(/<tr>/g).length, 9);
  assert.equal(html.match(/<th scope="col"/g).length, 6);
  assert.ok(!html.includes('Note<') && !html.includes('Extra2<') && html.includes('Extra1<') && html.includes('>Source<'));
  assert.ok(html.includes('<span class="na" title="Not supplied">n.a.</span>') && html.includes('<span class="na" title="Empty in the handoff">n.a.</span>'));
  assert.ok(html.includes('1 more rows are under Statements and registers.'));
  assert.ok(!/<td[^>]*>\s*[—–-]\s*<\/td>/.test(html));
});

test('no table with two numeric columns means no key-numbers table', () => {
  assert.equal(report({ sections: SECTIONS.filter(s => s.heading !== 'Liquidity table') }).keyNumbers(OUT), '');
});

test('every chart row holds its exact value and a chip set', () => {
  const html = report().moduleReport(OUT);
  const rows = [...html.matchAll(/<div class="chart-row"[^>]*>.*?<\/div>/g)].map(m => m[0]);
  assert.equal(rows.length, 2);
  assert.ok(rows[0].includes('%">6.57</strong>') && rows[0].includes('class="chips"') && rows[0].includes('</span>p.123<span'));
  for (const row of rows) assert.match(row, /<strong[^>]*>[^<]+<\/strong>/);
});

test('findings are articles with impact, confidence and chips', () => {
  const html = report().moduleReport(OUT);
  assert.equal(html.match(/<article class="finding">/g).length, 2);
  assert.ok(html.includes('<b>Creditor impact</b>Higher gross leverage.') && html.includes('<span class="pill">High</span>'));
});

test('limits come from the limits-placed sections with chips and their line ids; audit lists the rest by line', () => {
  const r = report();
  const limits = r.reportLimits(OUT);
  assert.ok(limits.includes('id="s-50"') && limits.includes('Coupons are <strong>not supplied</strong>.') && limits.includes('Not supplied'));
  const audit = r.reportAudit(OUT);
  assert.ok(audit.includes('<span>L10</span>') && audit.includes('<span>L60</span>') && audit.includes('<span>L64</span>') && !audit.includes('<span>L20</span>') && !audit.includes('Gaps &amp; limitations'));
  assert.ok(audit.includes('<details class="audit" id="audit">') && audit.includes('hidden'));
});

test('the outline is the nine anchors under On this page', () => {
  const html = report().outlineMarkup(OUT);
  assert.equal(html.match(/class="section-item"/g).length, 9);
  assert.ok(html.includes('aria-label="On this page"') && html.includes('aria-current="location"') && html.includes('>Statements and registers<') && html.includes('>Calculations<'));
});

test('no output reads No output found, once, in the state word and on the canvas', () => {
  const r = report();
  assert.equal(r.availability('CP-9', 'run-a'), 'No output found');
  assert.equal(r.availability('CP-1', 'run-a'), 'Output available');
  const text = read('views.js');
  assert.equal([...text.matchAll(/No output found/g)].length, 1);
  assert.ok(!text.includes('Not run in this run') && !text.includes('no saved output'));
});

test('screen.css sets no font-size below 11px and the report styles exist', () => {
  const css = read('screen.css');
  for (const m of css.matchAll(/font(?:-size)?\s*:\s*(?:[^;}]*?\s)?(\d+(?:\.\d+)?)px/g)) assert.ok(Number(m[1]) >= 11, m[0]);
  for (const sel of ['.chip{', '.chip .av{', '.dot{', 'article.finding{', '.limits{', 'details.audit{', '.band{', '.panel-card{', '.table-card{']) assert.ok(css.includes(sel), sel);
});

test('key numbers read the reference sections whatever the module (CP-2E: a hedge register)', () => {
  // Answer key from the fixture: the T2F.4 register is the only reference table with two numeric columns.
  const sections = [ref('T2F.4 Hedge register', 70, [table(72, ['Instrument', 'Amount', 'Margin / Coupon'], [[73, 'Swap', '500', '3.1'], [74, 'Collar', '250', '2.4']])])];
  const html = report({ module: 'CP-2E', sections }, [['hedges', 'Hedge register', ['T2F.4']]]).keyNumbers(OUT);
  assert.equal(html.match(/<tr>/g).length, 3);
  assert.ok(html.includes('>Amount<') && html.includes('>Margin / Coupon<') && html.includes('>500<'));
});

test('the chart-row button is a real box, not display:contents', () => {
  const css = read('screen.css');
  assert.ok(!/\.chart-open\{[^}]*display:contents/.test(css));
  assert.ok(/\.column-chart \.chart-open,\.column-chart button\.chart-row\{display:grid/.test(css));
});

test('Open source file is omitted when the build says the source text is missing', () => {
  const text = read('screen.js');
  const start = text.indexOf('function chipSection('), end = text.indexOf('function showInspector(');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const section = new Function('esc', 'icon', `${text.slice(start, end)}; return chipSection;`)(esc, n => `<img src="${n}">`);
  const output = { href: '../runs/r/deliveries/d/CP-1.md', source: 'deliveries/d/CP-1.md' };
  const base = { kind: 'issuer_page', source: 'PDF', file: 'a.pdf', page: 1, page_end: null, sha256: 'ab', quote: null, quote_found: null, excerpt: null, hash_matches_inventory: null };
  const gone = section({ ...base, reason: 'source text file not found' }, output);
  assert.ok(!gone.includes('Open source file') && gone.includes('source text file not found'));
  const there = section({ ...base, excerpt: 'text', hash_matches_inventory: true, reason: null }, output);
  assert.ok(there.includes('href="../runs/r/source-text/a.pdf"') && there.includes('Open source file'));
});

test('key numbers look past a reference table without numbers, and ignore tables not placed reference', () => {
  // Answer key from the fixture: T2G.1 holds only a text table; T2F.4 is the numeric register; the audit-placed table is never a candidate.
  const sections = [
    sec('Sources', 2, 55, 'audit', [table(56, ['Name', 'A', 'B'], [[57, 'K', '1', '2']])]),
    ref('T2G.1 ESG notes', 60, [table(62, ['Topic', 'View'], [[63, 'Governance', 'Stable']])]),
    ref('T2F.4 Hedge register', 70, [table(72, ['Instrument', 'Amount', 'Margin / Coupon'], [[73, 'Swap', '500', '3.1']])]),
  ];
  const html = report({ module: 'CP-2E', sections }, [['src', 'Sources', ['Sources']], ['esg', 'ESG notes', ['T2G.1']], ['hedges', 'Hedge register', ['T2F.4']]]).keyNumbers(OUT);
  assert.ok(html.includes('>Amount<') && html.includes('>500<') && !html.includes('>Governance<') && !html.includes('>K<'));
});

// ---- The hedge chart: views.js evaluated over a hand-written CP-2E table and a run whose as-of is 2024-09-30.
function chartFn(name, headers, rows, asOf = '2024-09-30') {
  const text = read('views.js');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const id = 'run-a/deliveries/d1/CP-2E.md';
  const out = { module: 'CP-2E', run: 'run-a', period: '', sections: [{ heading: 'T2F.4', line: 1, blocks: [table(80, headers, rows)] }] };
  const names = ['data', 'contexts', 'esc', 'rich', 'plain', 'evidence', 'modules', 'moduleNames', 'current', 'icon', 'window', 'store', 'pins', 'lastFile', 'isAnalytical', 'sectionData'];
  const fn = new Function(...names, `${text}; return ${name};`)({ [id]: out }, { 'run-a': { asOf } }, esc, esc, esc, new Map(), {}, {}, {}, () => '', { CREDIT_OS_DATA: { chips: {} } }, {}, {}, new Map(), () => true, () => []);
  return [fn, id];
}
function hedgeHtml(headers, rows, asOf) {
  const [fn, id] = chartFn('hedgeChart', headers, rows, asOf);
  return fn(id, { kind: 'hedges', table: 80, title: 'Hedges', unit: null });
}
test('a chart row whose value is text prints n.a., keeps the text in title, draws no bar and keeps its evidence key', () => {
  const [fn, id] = chartFn('comparisonChart', ['Item', 'Value'], [[81, 'Prior availability', 'Not supplied: prior-year facility availability not extracted'], [82, 'Cash', '1,200']]);
  const html = fn(id, { kind: 'bars', table: 80, column: 1, title: 'Liquidity', unit: 'USDm' });
  const [text, num] = [...html.matchAll(/<button class="chart-row"[^>]*>.*?<\/button>/g)].map(m => m[0]);
  assert.ok(text.includes('data-evidence="run-a/deliveries/d1/CP-2E.md:81"'));
  assert.ok(text.includes('<strong title="Not supplied: prior-year facility availability not extracted">n.a.</strong>'));
  assert.ok(text.includes('class="track missing"'));
  assert.ok(!text.includes('<i ') && !text.includes('—'));
  assert.ok(num.includes('<strong>1,200</strong>') && num.includes('<i class="series-0" style="width:100%"'));
});
const HEDGE_ROWS = [
  [81, 'Swap', '500', '2022-12-31 to 2025-06-30', 'USDm', 'Reviewed 2019-05-01'],
  [82, 'Cap', '250', '2025-01-31 to 2028-03-31', 'EURm', '2030-01-01'],
  [83, 'FX forwards', '90', 'Up to 12 months', '', '2019-05-01'],
];
const leftOf = (html, cls) => [...html.matchAll(new RegExp(`class="${cls}[^"]*" style="left:([\\d.]+)%(?:;width:([\\d.]+)%)?`, 'g'))].map(m => [Number(m[1]), m[2] === undefined ? null : Number(m[2])]);

test('hedge chart axis, base rule, forward flag and units come from the table and the as-of', () => {
  // Hand-computed: start 2022-12-31 (earlier than as-of minus 18 months), end 2028-03-31 (later than as-of plus 36 months); 1917 days.
  // As-of 2024-09-30 is day 639 (1/3); Swap spans days 0-912; Cap starts day 762.
  // The 'Reviewed' column holds dates (2019-05-01, 2030-01-01) outside that range; they are not in the date column, so the axis and the two-date rows ignore them.
  const html = hedgeHtml(['Instrument', 'Amount', 'Maturity window', 'Unit', 'Reviewed'], HEDGE_ROWS);
  assert.deepEqual([...html.matchAll(/<span style="left:[^"]*">([^<]*)<\/span>/g)].map(m => m[1]), ['Dec 2022', 'Sep 2024 base', 'Mar 2028']);
  assert.ok(Math.abs(leftOf(html, 'base-rule')[0][0] - 100 / 3) < 0.001);
  const [swap, cap] = leftOf(html, 'hedge-span');
  assert.ok(Math.abs(swap[0]) < 0.001 && Math.abs(swap[1] - 912 / 1917 * 100) < 0.001);
  assert.ok(Math.abs(cap[0] - 762 / 1917 * 100) < 0.001);
  assert.equal([...html.matchAll(/hedge-span future/g)].length, 1);
  assert.ok(html.includes('500 USDm') && html.includes('250 EURm') && html.includes('Duration only'));
  assert.ok(!/90 [A-Za-z]/.test(html.replace(/<[^>]+>/g, ' ').replace(/Up to 12 months/, '')));
});

test('hedge chart falls back to as-of minus 18 and plus 36 months and prints no unit without a unit column', () => {
  // As-of 2025-03-31: 2023-09-30 .. 2028-03-31; dates inside that window do not move the ends.
  const html = hedgeHtml(['Instrument', 'Amount', 'Window'], [[81, 'Swap', '500', '2024-01-31 to 2026-06-30']], '2025-03-31');
  assert.deepEqual([...html.matchAll(/<span style="left:[^"]*">([^<]*)<\/span>/g)].map(m => m[1]), ['Sep 2023', 'Mar 2025 base', 'Mar 2028']);
  assert.ok(html.includes('<small>500 </small>') || html.includes('<small>500</small>'));
  assert.ok(!html.includes('USDm'));
});

test('views.js holds no hard-coded hedge dates, labels or units', () => {
  const text = read('views.js');
  for (const literal of ['2024-09-30', 'Mar 2023', 'Sep 2027', "'FX forwards'", 'USDm']) assert.ok(!text.includes(literal), literal);
});

test('Open source file is hidden by the structural condition only, not by the reason text', () => {
  const text = read('screen.js');
  const start = text.indexOf('function chipSection('), end = text.indexOf('function showInspector(');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const section = new Function('esc', 'icon', `${text.slice(start, end)}; return chipSection;`)(esc, n => `<img src="${n}">`);
  const output = { href: '../runs/r/deliveries/d/CP-1.md', source: 'deliveries/d/CP-1.md' };
  const withFile = { kind: 'issuer_page', source: 'PDF', file: 'a.pdf', page: 1, page_end: null, sha256: 'ab', quote: null, quote_found: null, excerpt: 'text', hash_matches_inventory: true };
  assert.ok(section({ ...withFile, reason: 'the line is missing from page 1' }, output).includes('Open source file'));
});

test('an audit item that cannot be drawn says so instead of staying silent', () => {
  const text = read('screen.js');
  const start = text.indexOf('function openAuditSection('), end = text.indexOf('function showNavigator(');
  const body = { hidden: true, dataset: {}, innerHTML: '' }, button = { dataset: { audit: 'x' }, getAttribute: () => 'b', setAttribute() {} };
  const errors = [], log = console.error;
  console.error = e => errors.push(e);
  try {
    new Function('$', 'current', 'sectionView', `${text.slice(start, end)}; openAuditSection(arguments[3]);`)(() => body, { output: 'o' }, () => { throw new Error('boom'); }, button);
  } finally { console.error = log; }
  assert.ok(body.innerHTML.includes('Couldn’t present this item') && errors.length === 1 && body.hidden === false && !body.dataset.drawn);
});

// ---- Final fix round: avatar and match come from the build (R23, R25); one numeric rule (R26); one section count (R27).
function inspectorSection(chip) {
  const text = read('screen.js');
  const start = text.indexOf('function chipSection('), end = text.indexOf('function showInspector(');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const section = new Function('esc', 'icon', `${text.slice(start, end)}; return chipSection;`)(esc, n => `<img src="${n}">`);
  return section(chip, { href: '../runs/r/deliveries/d/CP-1.md', source: 'deliveries/d/CP-1.md' });
}
const found = { kind: 'issuer_page', source: 'Annual filing', avatar: 'AF', file: 'a.jsonl', page: 3, page_end: null, sha256: 'ab', quote: '3472', quote_found: true, hash_matches_inventory: true };

test('the inspector marks the span the build matched, not the quote', () => {
  const html = inspectorSection({ ...found, excerpt: 'Net sales were 3,472 in the year', match: '3,472', match_at: 15 });
  assert.ok(html.includes('<mark>3,472</mark>') && !html.includes('<mark>3472</mark>') && html.includes('Quote found on page'));
  assert.ok(html.includes('Net sales were <mark>3,472</mark> in the year'));
  const bracket = inspectorSection({ ...found, quote: '-11', excerpt: 'loss of (11) before tax', match: '(11)', match_at: 8 });
  assert.ok(bracket.includes('loss of <mark>(11)</mark> before tax'));
});

test('the inspector marks where the build says, and nowhere else, and never searches for the quote', () => {
  const twice = inspectorSection({ ...found, excerpt: 'a 11 and 211 and 11', quote: '11', match: '11', match_at: 17 });
  assert.ok(twice.includes('a 11 and 211 and <mark>11</mark>'));
  const none = inspectorSection({ ...found, excerpt: 'Net sales were 3,472', quote_found: true });
  assert.ok(!none.includes('<mark>') && none.includes('Net sales were 3,472'));
  const missing = inspectorSection({ ...found, quote_found: false, excerpt: 'Net sales were 3,472' });
  assert.ok(!missing.includes('<mark>') && missing.includes('Quote not found'));
});

test('the avatar is the build avatar and the inspector names the full key', () => {
  assert.equal(chipViewOf(found).av, 'AF');
  assert.equal(chipViewOf({ ...found, avatar: undefined, source: 'K' }).av, 'K');
  assert.ok(inspectorSection({ ...found, excerpt: 'x' }).includes('Cited as Annual filing'));
});
function chipViewOf(chip) { return report().chipView(chip, 'CP-1'); }

test('a key-numbers column with a prose cell is not numeric; "Not supplied" and n.a. do not count against it', () => {
  const prose = 'Drawn loan principal not separately printed in retained summary; 910 commitment, 843 available';
  const sections = [ref('Register', 90, [table(92, ['Item', 'Amount', 'Limit', 'Note'], [
    [93, 'Revolver', prose, '910', 'x'], [94, 'Term loan', '1,200', 'Not supplied: not printed', 'y'], [95, 'Notes', '500', 'n.a.', 'z'], [96, 'Other', '', '12', 'w'],
  ])])];
  const html = report({ sections }, [['register', 'Register', ['Register']]]).keyNumbers(OUT);
  assert.equal(html, '');
  const both = [ref('Register', 90, [table(92, ['Item', 'Amount', 'Limit'], [
    [93, 'Term loan', '1,200', '910'], [94, 'Notes', 'Not supplied: not printed', '500'], [95, 'Other', 'n.a.', '12'], [96, 'Bonds', '', '7'],
  ])])];
  const shown = report({ sections: both }, [['register', 'Register', ['Register']]]).keyNumbers(OUT);
  assert.equal(shown.match(/<th scope="col" class="num">/g).length, 2);
});

test('the audit summary gives the store\'s section count; the head carries no file name or count', () => {
  const sections = [...SECTIONS, sec('Empty', 2, 70, 'audit', []), sec('Also empty', 2, 72, 'audit', [])];
  const html = report({ sections }).moduleReport(OUT);
  assert.equal(sections.length, 12);
  assert.ok(!/class="module-head".*?<\/h2><div class="sub">(?:(?!<\/div>).)*(?:CP-1\.md|sections)/s.test(html));
  assert.ok(html.includes('<span>12 sections · unchanged from the handoff</span>'));
  assert.ok(!/\b(?:10|11) sections\b/.test(html));
});

// ---- Reference, Analysis and the other parts draw what the store placed; the page re-judges nothing.
const NARRATIVE = [
  sec('Debt structure', 3, 70, 'reference', [
    text(72, 'Debt is **mostly secured**.\nSecond line.'),
    table(74, ['Instrument', 'Maturity', 'Amount', 'Note'], [[75, 'Term loan', '2028', '1,200', 'first'], [76, 'Notes', '2030', 'Not supplied', ''], [77, 'Revolver', '2027', '300', 'undrawn']]),
    text(79, 'Closing remark.'),
  ]),
  sec('Sub topic', 4, 80, 'reference', [text(82, 'Nested text.')]),
];
const NARRATIVE_MODULES = [['debt', 'Debt structure', ['Debt structure']], ['sub', 'Sub topic', ['Sub topic']], ['sources', 'Sources', ['Sources']]];
test('a reference section renders whole inside Statements and registers, in order, with chips and relative heading tags', () => {
  const html = report({ sections: [...NARRATIVE, SECTIONS.find(s => s.heading === 'Sources')] }, NARRATIVE_MODULES).reportReference(OUT);
  const at = s => html.indexOf(s);
  // Answer key from NARRATIVE: the shallowest section is h4, its level-4 child h5; the text before the table before the closing remark.
  assert.ok(at('<h4>Debt structure</h4>') > 0 && at('<h5>Sub topic</h5>') > at('<h4>Debt structure</h4>'));
  assert.ok(at('Debt is <strong>mostly secured</strong>. Second line.') > at('Debt structure') && at('Term loan') > at('mostly secured') && at('Closing remark.') > at('Revolver'));
  assert.equal(html.match(/<tr><td>/g).length, 3); // the three register rows, none dropped
  assert.ok(html.includes('<span class="na" title="Not supplied">n.a.</span>') && html.includes('<span class="na" title="Empty in the handoff">n.a.</span>') && !html.includes('—'));
  for (const line of [72, 75, 77, 79, 82]) assert.ok(html.includes(`aria-label="Handoff row, line ${line}"`), line);
  assert.ok(html.includes('class="table-card"') && !html.includes('K.'));
});

test('the parts come in the ruled order on the page', () => {
  const page = report().moduleReport(OUT);
  const at = id => page.indexOf(`id="${id}"`);
  for (let i = 1; i < NINE.length; i++) assert.ok(at(NINE[i - 1]) < at(NINE[i]), `${NINE[i - 1]} before ${NINE[i]}`);
});

test('a section placed consumed, audit or limits is not drawn in Analysis or Reference', () => {
  const r = report();
  for (const html of [r.reportAnalysis(OUT), r.reportReference(OUT)]) for (const name of ['Reader summary', 'Chart data', 'Extra notes', 'Sources', 'Reviewer note.']) assert.ok(!html.includes(name), name);
});

test('a handoff with no output still reads one sentence on the canvas, and no part prints an empty-part sentence', () => {
  const text = read('views.js');
  assert.equal([...text.matchAll(/No output found/g)].length, 1);
  assert.ok(!text.includes('No further analysis sections') && !text.includes('part-empty') && !text.includes('EMPTY_PART'));
  for (const gone of ['function sectionGroups', 'analysisSections', 'limitsGroup', 'analysisBlocks', 'EVIDENCE_HEADING', 'isEvidenceSection']) assert.ok(!text.includes(gone), gone);
});

test('the shell landmark does not take the id of the Analysis part', () => {
  const shell = read('index.html');
  assert.ok(!/\bid="analysis"/.test(shell) && !shell.includes('href="#analysis"'));
  assert.ok(!read('screen.js').includes("$('analysis')"));
});

test('R31: sections the store placed audit stay out of every part and in the audit list', () => {
  const extra = [
    sec('Front matter', 1, 1, 'audit', [text(2, 'title: x')]),
    sec('Request', 2, 3, 'audit', [text(4, 'asked')]),
    sec('Sources', 2, 100, 'audit', [text(101, 'Parent text.')]),
    sec('Alpha register', 3, 102, 'audit', [table(103, ['Name', 'Hash'], [[104, 'K', 'abc']])]),
    view('Beta analysis', 110, [text(111, 'Real analysis.')]),
  ];
  const mods = [['front', 'Front matter', ['Front matter']], ['req', 'Request', ['Request']], ['alpha', 'Alpha register', ['Alpha register']], ['beta', 'Beta analysis', ['Beta analysis']], ['srcs', 'Sources', ['Sources']]];
  const r = report({ sections: extra, charts: [], summary: null }, mods);
  const page = r.moduleReport(OUT), audit = r.reportAudit(OUT);
  assert.ok(r.reportAnalysis(OUT).includes('Real analysis.'));
  for (const name of ['Front matter', 'Request', 'Alpha register', 'Sources']) assert.ok(audit.includes(name), name);
  assert.ok(!audit.includes('Beta analysis'));
  for (const name of ['Parent text.', 'asked', 'abc']) assert.ok(!page.replace(audit, '').includes(name), name);
});

test('R32: Analysis follows the handoff order of the sections it is given', () => {
  const sections = [view('Plain earlier', 120, [text(121, 'First by line.')]), view('T2G.1 — Later group', 140, [text(141, 'Second by line.')])];
  const html = report({ module: 'CP-2E', sections, summary: null, charts: [] }, [['plain', 'Plain earlier', ['Plain earlier']], ['esg', 'T2G.1 — Later group', ['T2G.1 — Later group']]]).reportAnalysis(OUT);
  assert.ok(html.indexOf('First by line.') > 0 && html.indexOf('First by line.') < html.indexOf('Second by line.'));
});

test('the page does not re-judge a heading: a view-placed "Exact source register" is drawn, an audit-placed "Resource bridge" is not', () => {
  const sections = [view('Exact source register', 200, [text(201, 'Drawn.')]), sec('Resource bridge and competing uses', 3, 210, 'audit', [text(211, 'Listed.')])];
  const html = report({ sections }, [['a', 'Exact source register', ['Exact source']], ['b', 'Resource bridge', ['Resource bridge']]]).reportAnalysis(OUT);
  assert.ok(html.includes('>Exact source register</h4>') && html.includes('Drawn.') && !html.includes('Resource bridge') && !html.includes('Listed.'));
});

test('R33a: heading tags are relative and capped at h6; the style sheet sets h4, h5 and h6 at 11px or more', () => {
  const sections = [3, 4, 5, 6, 7].map((level, i) => sec(`Level ${level}`, level, 300 + 10 * i, 'view', [text(301 + 10 * i, 'x')]));
  const html = report({ sections }, sections.map((s, i) => [`l${i}`, s.heading, [s.heading]])).reportAnalysis(OUT);
  assert.deepEqual([...html.matchAll(/<(h[3-6])>(Analysis|Level \d)</g)].map(m => m[1]), ['h3', 'h4', 'h5', 'h6', 'h6', 'h6']);
  const css = read('screen.css');
  for (const tag of ['h4', 'h5', 'h6']) assert.ok(css.includes(`.analysis-section>${tag}{font-size:`), tag);
});

test('a route into a closed part opens it: scrollToPart opens every details that is or holds the target', () => {
  const src = read('screen.js');
  const start = src.indexOf('function scrollToPart('), end = src.indexOf('function renderRoute(');
  assert.ok(start >= 0 && end > start);
  const node = (tag, parent) => ({ tag, parent, open: false, matches(sel) { return sel === 'details' && this.tag === 'details'; }, closest(sel) { for (let n = this; n; n = n.parent) if (n.matches(sel)) return n; return null; }, getBoundingClientRect: () => ({ top: 0 }) });
  const outer = node('details', null), inner = node('details', outer), target = node('div', inner);
  inner.parentElement = outer; target.parentElement = inner;
  const content = { scrollTop: 0, getBoundingClientRect: () => ({ top: 0 }) };
  new Function('$', `${src.slice(start, end)}; scrollToPart('s-9');`)(id => (id === 'content' ? content : id === 's-9' ? target : null));
  assert.ok(inner.open && outer.open && !target.open);
});

// ---- The run report: views.js evaluated over a four-module run, with the screen.js globals it calls stood in.
const RUN = 'run-a';
const outId = code => `${RUN}/deliveries/d1/${code}.md`;
const FINDINGS_HEADERS = ['Finding', 'Creditor impact', 'Confidence'];
const chartTable = (line, rows) => table(line, ['Period', 'Value', 'Reporting unit', 'Basis'], rows);
const runOutput = (code, extra) => ({ module: code, run: RUN, source: `deliveries/d1/${code}.md`, href: `../runs/${RUN}/deliveries/d1/${code}.md`, label: code, charts: [], call: null, ...extra });
const STATE_ON = { established: true, declared: null };
function runData(overrides = {}) {
  const cp1 = runOutput('CP-1', {
    sections: [
      sec('Reader summary', 3, 10, 'consumed', [table(15, FINDINGS_HEADERS, [[16, 'Leverage rose.', 'Higher gross leverage.', 'High'], [17, 'Cash rose.', 'More cushion.', 'Medium']])]),
      sec('Chart data: leverage', 3, 40, 'consumed', [chartTable(42, [[43, 'FY2024', '6.57', 'x', 'K']])]),
      sec('Chart data: cover', 3, 50, 'consumed', [chartTable(52, [[53, 'FY2024', '2.1', 'x', 'K']])]),
    ],
    state: { established: true, declared: 'Requires More Work' }, words: { view: 746, reference: 3000, calculations: 1145, limits: 940, audit: 972 },
    summary: { bottomLine: 'Cash is up and leverage is high.', confidence: 'Medium', limitation: 'Synthetic limit one.', line: 13, findings: READER_FINDINGS },
    charts: [{ title: 'Leverage', unit: 'x', table: 42, columns: [1] }, { title: 'Cover', unit: 'x', table: 52, columns: [1] }],
  });
  const cp2a = runOutput('CP-2A', {
    sections: [sec('Reader summary', 3, 10, 'consumed', [table(15, FINDINGS_HEADERS, [[16, 'Downside unmeasured.', 'No cushion test.', 'Low']])])],
    state: { established: false, declared: 'Blocked' }, words: { view: 20, reference: 30, calculations: 5, limits: 7, audit: 9 },
    summary: { bottomLine: 'No downside is drawn.', confidence: 'Not assessable', limitation: 'Downside inputs are missing.', line: 13, findings: [{ finding: 'Downside unmeasured.', impact: 'No cushion test.', confidence: 'Low', line: 16 }] },
  });
  const cp6 = runOutput('CP-6', {
    sections: [sec('Reader summary', 3, 10, 'consumed', [])],
    state: { established: false, declared: null }, words: { view: 1, reference: 2, calculations: 3, limits: 4, audit: 5 },
    summary: { bottomLine: 'Committee cannot decide yet.', confidence: 'Not assessable', limitation: 'Every upstream module is open.', line: 13, findings: [] },
  });
  const cpx = runOutput('CP-X', { sections: [], state: { established: null, declared: null }, words: { view: 100, reference: 200, calculations: 50, limits: 0, audit: 0 }, summary: null });
  return { [outId('CP-1')]: cp1, [outId('CP-2A')]: cp2a, [outId('CP-6')]: cp6, [outId('CP-X')]: cpx, ...overrides };
}
function runPage(mutate = d => d, reports = [], shape = modules => modules, more = {}) {
  const src = read('views.js');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const plain = v => String(v).replace(/\*\*|`/g, '');
  const rich = v => esc(v).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  const data = mutate(runData());
  const evidence = new Map();
  for (const [id, out] of Object.entries(data)) for (const s of out.sections) for (const b of s.blocks) {
    for (const r of b.type === 'table' ? b.rows : [b]) evidence.set(`${id}:${r.line}`, { module: out.module, line: r.line });
  }
  const groups = [['Business and evidence', [['CP-0', 'Source readiness']]], ['Financial performance', [['CP-1', 'Financial foundation'], ['CP-1B', 'Cash flow']]], ['Outlook and downside', [['CP-2A', 'Downside']]],
    ['Decision and review', [['CP-6', 'Committee decision']]], ['Other modules', [['CP-X', 'Unnamed module']]]];
  const moduleNames = Object.fromEntries(groups.flatMap(g => g[1]));
  const entry = code => ({ outputs: [outId(code)], default: outId(code) });
  const contexts = { [RUN]: { folder: RUN, modules: shape({ 'CP-0': { outputs: [], default: null }, ...Object.fromEntries(Object.values(data).map(out => [out.module, entry(out.module)])) }) }, ...more.contexts };
  const win = { CREDIT_OS_DATA: { chips: { [`${outId('CP-1')}:16`]: [{ kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 123, page_end: null }], ...more.chips } }, DESIGN_CATALOGUE: { real: more.catalogue || [{ id: RUN, checklist: null }] }, DESIGN_WORKSPACE: { reports, models: [] } };
  const libraryState = { selected: '', sortKey: '', direction: 'asc', hidden: '' };
  const names = ['LIBRARY_DEFAULTS', 'libraryState', 'LibraryLogic', 'libraryFilters', 'window', 'data', 'modules', 'contexts', 'store', 'moduleNames', 'groups', 'esc', 'plain', 'rich', 'icon', 'pins', 'evidence', 'current', 'isAnalytical', 'sectionData', 'lastFile', 'lastSection', 'aliases', 'sourceLink', 'classTag'];
  const args = [{ ratingScope: 'issuer' }, libraryState, new Function(`${read('screening.js')}; return LibraryLogic;`)(), { ratingScope: 'issuer' }, win, data, Object.fromEntries(Object.keys(data).map(id => [id, { first: 'head' }])), contexts, {}, moduleNames, groups, esc, plain, rich, n => `<img src="icons/${n}.svg">`, {}, evidence, { context: RUN, section: 'overview' }, id => !id.startsWith('W-'), () => [], new Map(), new Map(), { 'CP-6A': 'CP-6' }, (key, label) => `<button class="source-link" data-evidence="${esc(key)}">${esc(label)}</button>`, () => ''];
  return new Function(...names, `${src}; return {runReport, registerRowShown, readerChart, chartCards, cellView, libraryRow, libraryPath, libraryDetail, libraryPanel, libraryResults, reportList, reportView, libraryState, moduleHead, sourceInventory, namedText, moduleTitle, handoffLabel, current, modules};`)(...args);
}
const RUN_CP6_ESTABLISHED = d => { const cp6 = d[outId('CP-6')]; cp6.state = { established: true, declared: null }; cp6.summary = { ...cp6.summary, confidence: 'Low', bottomLine: 'Committee leans against.' }; return d; };
const countOf = (html, re) => (html.match(re) || []).length;
// A story module, from its opening tag to the next story module or the end of its group (flat regex over generated markup).
const storyModule = (html, code) => new RegExp(`<div class="story-module" data-module="${code}">.*?(?=<div class="story-module"|</section>)`, 's').exec(html)?.[0];
const groupOf = (html, title) => new RegExp(`<section class="story-group"[^>]*><h2>${title}</h2>.*?</section>`, 's').exec(html)?.[0];

test('run report: the count line reads from state, with the unsummarised module counted apart', () => {
  const html = runPage().runReport(RUN);
  assert.equal(strip(/<p class="run-count">(.*?)<\/p>/.exec(html)[1]), '1 of 4 modules reach a conclusion · 2 not assessable · 1 without a reader summary');
  assert.ok(html.includes('Candidate · not accepted'));
  const all = runPage(d => { delete d[outId('CP-X')]; d[outId('CP-2A')].state.established = true; d[outId('CP-6')].state.established = true; return d; }).runReport(RUN);
  assert.equal(strip(/<p class="run-count">(.*?)<\/p>/.exec(all)[1]), '3 of 3 modules reach a conclusion · 0 not assessable');
});

test('run report: coverage is four links in group order, the module name as label, only the established one filled', () => {
  const html = runPage().runReport(RUN);
  const cells = [...html.matchAll(/<a class="cov( filled)?" href="([^"]*)"[^>]*>(.*?)<\/a>/g)].map(m => [m[3], !!m[1], m[2]]);
  assert.deepEqual(cells.map(c => c[0]), ['Financial foundation', 'Downside', 'Committee decision', 'Unnamed module']);
  assert.deepEqual(cells.map(c => c[1]), [true, false, false, false]);
  assert.deepEqual(cells.map(c => c[2].split('/')[0]), ['#CP-1', '#CP-2A', '#CP-6', '#CP-X'], 'the route still carries the code');
});

test('run report: no band while CP-6 is not assessable; one band quoting CP-6 once it is established; no CALL_ORDER or summaryView', () => {
  assert.equal(countOf(runPage().runReport(RUN), /class="band"/g), 0);
  const html = runPage(RUN_CP6_ESTABLISHED).runReport(RUN);
  assert.equal(countOf(html, /class="band"/g), 1);
  assert.equal(countOf(html, /Committee leans against\./g), 2); // The band and the module's own story entry quote the same cell.
  assert.ok(html.indexOf('class="band"') < html.indexOf('class="story-group"'));
  const src = read('views.js');
  assert.ok(!src.includes('CALL_ORDER') && !src.includes('summaryView'));
});

test('run report: an established module reads bottom line, pill, status, findings with chips, limitation and both charts in one element', () => {
  const html = runPage().runReport(RUN);
  const mod = storyModule(html, 'CP-1');
  assert.ok(mod, 'CP-1 story-module');
  assert.ok(/<a class="text-action" href="#CP-1\//.test(mod) && mod.includes('Financial foundation'));
  assert.ok(mod.includes('Cash is up and leverage is high.'));
  assert.ok(mod.includes('<span class="pill">Medium</span>'));
  assert.ok(mod.includes('Requires More Work'));
  assert.equal(countOf(mod, /<article class="finding">/g), 2);
  assert.ok(mod.includes('Higher gross leverage.') && mod.includes('<span class="pill">High</span>') && mod.includes('p.123'));
  assert.ok(mod.includes('Synthetic limit one.'));
  assert.equal(countOf(mod, /<div class="panel-card">/g), 2);
  assert.equal(countOf(mod, /<div class="chart-row"/g), 2);
  const group = groupOf(html, 'Financial performance');
  assert.equal(countOf(group, /Missing values have no bar/g), 1);
  assert.equal(countOf(html, /Missing values have no bar/g), 1);
});

test('run report: the chart note prints once per group even when two modules draw charts', () => {
  const html = runPage(d => {
    d[outId('CP-2A')].sections.push(sec('Chart data: x', 3, 60, 'consumed', [chartTable(62, [[63, 'FY2024', '1.0', 'x', 'K']])]));
    d[outId('CP-2A')].charts = [{ title: 'X', unit: 'x', table: 62, columns: [1] }];
    d[outId('CP-2A')].state = { established: true, declared: null };
    return d;
  }).runReport(RUN);
  assert.equal(countOf(groupOf(html, 'Outlook and downside'), /Missing values have no bar/g), 1);
  assert.equal(countOf(html, /Missing values have no bar/g), 2); // One per group that draws a chart.
});

test('run report: the chart note prints once per group when two modules in the same group both draw charts', () => {
  const html = runPage(d => {
    d[outId('CP-1B')] = runOutput('CP-1B', {
      sections: [sec('Chart data: x', 3, 60, 'consumed', [chartTable(62, [[63, 'FY2024', '1.0', 'x', 'K']])])],
      state: STATE_ON, words: { view: 1, reference: 1, calculations: 1, limits: 1, audit: 1 },
      summary: { bottomLine: 'Cash flow is steady.', confidence: 'Medium', limitation: 'Synthetic limit two.', line: 13, findings: [] },
      charts: [{ title: 'X', unit: 'x', table: 62, columns: [1] }],
    });
    return d;
  }).runReport(RUN);
  const group = groupOf(html, 'Financial performance');
  assert.ok(storyModule(html, 'CP-1') && storyModule(html, 'CP-1B'));
  assert.equal(countOf(group, /<div class="panel-card">/g), 3); // CP-1 draws two charts, CP-1B one.
  assert.equal(countOf(group, /Missing values have no bar/g), 1);
});

test('run report: a module under Other modules with a summary has its register row and open item', () => {
  const html = runPage(d => {
    d[outId('CP-X')].state = STATE_ON;
    d[outId('CP-X')].summary = { bottomLine: 'Other is fine.', confidence: 'Medium', limitation: 'Other limit.', line: 13, findings: [{ finding: 'Other finding.', impact: 'Other impact.', confidence: 'Medium', line: 16 }] };
    d[outId('CP-X')].sections = [sec('Reader summary', 3, 10, 'consumed', [])];
    return d;
  }).runReport(RUN);
  const register = /<table class="register">.*?<\/table>/s.exec(html)[0];
  const row = /<tr data-group="Other modules"[^>]*>.*?<\/tr>/s.exec(register)[0];
  assert.deepEqual([...row.matchAll(/<td>(.*?)<\/td>/gs)].map(m => strip(m[1]).trim()), ['Other modules', 'Unnamed module', 'Other finding.', 'Other impact.', 'Medium']);
  assert.ok(!row.includes(' hidden'));
  const items = /<h2>Open items<\/h2>.*?<\/section>/s.exec(html)[0];
  assert.ok(/<tr><td>Other modules<\/td><th scope="row"><a[^>]*href="#CP-X\/limits[^"]*">Unnamed module<\/a><\/th><td>Other limit\.<\/td><\/tr>/.test(items), items);
});

test('run report: a not-assessable module is one line with name link, state, declared status and the limitation, and no finding', () => {
  const html = runPage().runReport(RUN);
  const lines = [...html.matchAll(/<p class="na-line">(.*?)<\/p>/gs)].map(m => m[1]);
  assert.equal(lines.length, 2);
  const line = lines.find(l => l.includes('Downside'));
  assert.ok(/<a class="text-action" href="#CP-2A\//.test(line));
  assert.equal(strip(line).replace(/\s+/g, ' ').trim(), 'Downside · Not assessable · Blocked · Downside inputs are missing.');
  assert.ok(!storyModule(html, 'CP-2A'));
  const group = groupOf(html, 'Outlook and downside');
  assert.ok(!group.includes('class="finding"') && group.includes('<h2>Outlook and downside</h2>'));
  assert.equal(strip(lines.find(l => l.includes('Committee decision'))).replace(/\s+/g, ' ').trim(), 'Committee decision · Not assessable · Every upstream module is open.');
});

test('run report: a module with no reader summary sits under Other modules as "<name> · No reader summary", counted in coverage and matrix', () => {
  const html = runPage().runReport(RUN);
  const group = groupOf(html, 'Other modules');
  assert.equal(strip(/<p class="nosum-line">(.*?)<\/p>/s.exec(group)[1]).replace(/\s+/g, ' ').trim(), 'Unnamed module · No reader summary');
  assert.ok(html.includes('>Unnamed module</a>') && /<th scope="row"><a[^>]*>Unnamed module/.test(html));
  assert.ok(!groupOf(html, 'Business and evidence'), 'a group with no output in the run is not listed');
});

test('run report: the register has the ruled columns, hides the not-assessable row, and marks it', () => {
  const html = runPage().runReport(RUN);
  const reg = /<table class="register">.*?<\/table>/s.exec(html)[0];
  assert.deepEqual([...reg.matchAll(/<th scope="col">(.*?)<\/th>/g)].map(m => m[1]), ['Group', 'Module', 'Finding', 'Creditor impact', 'Confidence']);
  const rows = [...reg.matchAll(/<tr data-group="([^"]*)" data-confidence="([^"]*)" data-established="(true|false)"([^>]*)>(.*?)<\/tr>/gs)];
  assert.equal(rows.length, 3);
  assert.deepEqual(rows.map(r => r[3]), ['true', 'true', 'false']);
  assert.deepEqual(rows.map(r => /\bhidden\b/.test(r[4])), [false, false, true]);
  assert.deepEqual(rows.map(r => r[2]), ['High', 'Medium', 'Low']);
  assert.ok(rows[2][5].includes('Not assessable') && !rows[0][5].includes('Not assessable'));
  assert.equal(strip(/<label for="register-all">(.*?)<\/label>/.exec(html)[1]), 'Include not-assessable modules (1)');
  assert.ok(/<input type="checkbox" id="register-all"/.test(html));
  for (const kind of ['group', 'confidence']) assert.ok(new RegExp(`<select id="register-${kind}" data-register-filter="${kind}"`).test(html) && html.includes(`<label for="register-${kind}">`), kind);
});

test('registerRowShown: a not-assessable row shows only with all; a group or confidence mismatch hides', () => {
  const { registerRowShown: shown } = runPage();
  const row = { group: 'Financial performance', confidence: 'High', established: true }, na = { ...row, established: false };
  const open = { group: '', confidence: '', all: false };
  assert.equal(shown(row, open), true);
  assert.equal(shown(na, open), false);
  assert.equal(shown(na, { ...open, all: true }), true);
  assert.equal(shown(row, { ...open, group: 'Outlook and downside' }), false);
  assert.equal(shown(row, { ...open, group: 'Financial performance' }), true);
  assert.equal(shown(row, { ...open, confidence: 'Low' }), false);
  assert.equal(shown(row, { ...open, confidence: 'High' }), true);
  assert.equal(shown(na, { group: 'Outlook and downside', confidence: 'High', all: true }), false);
});

test('run report: open items are one grouped row per module with a summary, each linking to its limits part', () => {
  const html = runPage().runReport(RUN);
  const open = /<table class="open-items">.*?<\/table>/s.exec(html)[0];
  const rows = [...open.matchAll(/<tr>(?:(?!<\/tr>).)*?<td>.*?<\/tr>/gs)].map(m => m[0]);
  assert.equal(rows.length, 3);
  assert.deepEqual(rows.map(r => /href="(#CP-[0-9A-Z]+)\/limits/.exec(r)?.[1]), ['#CP-1', '#CP-2A', '#CP-6']);
  assert.ok(rows[0].includes('Financial performance') && rows[0].includes('Synthetic limit one.'));
  assert.ok(rows[1].includes('Downside inputs are missing.') && rows[2].includes('Every upstream module is open.'));
  assert.ok(!open.includes('CP-X'));
});

test('run report: the matrix has a row per module with its confidence and declared status, and no word counts', () => {
  const html = runPage().runReport(RUN);
  const mat = /<table class="matrix">.*?<\/table>/s.exec(html)[0];
  assert.deepEqual([...mat.matchAll(/<th scope="col">(.*?)<\/th>/g)].map(m => m[1]), ['Module', 'Confidence', 'Declared status']);
  const rows = [...mat.matchAll(/<tr><th scope="row">(.*?)<\/th>(.*?)<\/tr>/gs)].map(m => [strip(m[1]).trim(), [...m[2].matchAll(/<td[^>]*>(.*?)<\/td>/gs)].map(c => strip(c[1]).trim())]);
  assert.deepEqual(rows.map(r => r[0]), ['Financial foundation', 'Downside', 'Committee decision', 'Unnamed module']);
  assert.deepEqual(rows[0][1], ['Medium', 'Requires More Work']);
  assert.deepEqual(rows[1][1], ['Not assessable', 'Blocked']);
  assert.deepEqual(rows[2][1], ['Not assessable', 'not declared']);
  assert.deepEqual(rows[3][1], ['No reader summary', 'not declared']);
  assert.ok(!/\b(?:746|4145)\b/.test(strip(mat)));
});

test('run report: deliverables and the source inventory link render after the matrix', () => {
  const report = { id: 'd1', label: 'Credit report', build: null, mode: 'candidate', qualification: 'unrun', builtFrom: [{ run: RUN, module: 'CP-1', source: outId('CP-1') }] };
  const html = runPage(d => d, [report]).runReport(RUN);
  const tail = html.slice(html.indexOf('class="matrix"'));
  assert.ok(tail.includes('Deliverables from this run') && tail.includes('href="#W-Reports/d1?c=run-a"') && tail.includes('Credit report'));
  assert.ok(tail.includes('href="#W-Evidence/sources?c=run-a"'));
  assert.ok(!runPage().runReport(RUN).includes('Deliverables from this run'));
});

test('run report: markup order follows the spec, and every interpolated cell is escaped', () => {
  const html = runPage(d => { d[outId('CP-1')].summary.bottomLine = '<img src=x onerror=1>'; d[outId('CP-1')].summary.limitation = '<b>L</b>'; return d; }).runReport(RUN);
  assert.ok(!html.includes('<img src=x') && !html.includes('<b>L</b>'));
  const order = ['class="run-count"', 'class="coverage"', 'class="story-group"', 'class="register"', 'class="open-items"', 'class="matrix"'].map(s => html.indexOf(s));
  assert.ok(order.every((at, i) => at >= 0 && (i === 0 || at > order[i - 1])), order.join());
});

test('screen.css drops the summary-card family and draws the run report', () => {
  const css = read('screen.css');
  for (const gone of ['.summary-lead', '.summary-card', '.summary-charts', '.summary-chart{', '.question-map', '.summary-text', '.summary-note']) assert.ok(!css.includes(gone), gone);
  for (const sel of ['.story-module', '.na-line', '.cov.filled', 'table.register', 'table.open-items', 'table.matrix']) assert.ok(css.includes(sel), sel);
  const screen = read('screen.js');
  assert.ok(screen.includes('registerRowShown') && screen.includes('data-register-filter') && screen.includes('register-all'));
});

// A module with saved outputs and no default (two unnumbered variants): counted, listed as a choose line, never given an output by the page.
const CP0_TWO = modules => ({ ...modules, 'CP-0': { outputs: [`${RUN}/deliveries/d1/CP-0-a.md`, `${RUN}/deliveries/d1/CP-0-b.md`], default: null } });
test('run report: a module with outputs but no default is counted, listed as a choose line, and adds no register rows', () => {
  const html = runPage(d => d, [], CP0_TWO).runReport(RUN);
  assert.equal(strip(/<p class="run-count">(.*?)<\/p>/.exec(html)[1]), '1 of 5 modules reach a conclusion · 2 not assessable · 1 without a reader summary · 1 without a chosen output');
  const line = /<p class="choose-line">(.*?)<\/p>/.exec(html)[1];
  assert.equal(strip(line), 'Source readiness · 2 saved outputs. Choose one');
  assert.ok(/<a [^>]*href="#CP-0\?c=run-a"[^>]*>Choose one/.test(line));
  assert.ok(groupOf(html, 'Business and evidence').includes('choose-line'));
  assert.ok(/<a class="cov" href="[^"]*"[^>]*>Source readiness<\/a>/.test(html));
  const matrix = /<table class="matrix">.*?<\/table>/s.exec(html)[0];
  const row = /<tr><th scope="row">(?:(?!<\/tr>).)*CP-0.*?<\/tr>/s.exec(matrix)[0];
  assert.ok(strip(row).includes('2 saved outputs'));
  assert.equal(countOf(html, /<tr data-group[^>]*>/g), countOf(runPage().runReport(RUN), /<tr data-group[^>]*>/g));
  assert.ok(!/without a chosen output/.test(runPage().runReport(RUN)));
});

test('run report: the register carries one hidden-unless-empty "No findings match" row', () => {
  const html = runPage(RUN_CP6_ESTABLISHED).runReport(RUN);
  assert.ok(/<tr class="register-empty" hidden><td colspan="5">No findings match<\/td><\/tr>/.test(html));
  const none = runPage(d => { d[outId('CP-1')].state.established = false; return d; }).runReport(RUN);
  assert.ok(/<tr class="register-empty"><td colspan="5">No findings match/.test(none));
  assert.ok(read('screen.js').includes('register-empty'));
});

// Live run activity: pull the live functions (between activityView and workspaceView) out of views.js.
const liveFns = () => {
  const text = read('views.js');
  const start = text.indexOf('function activityView('), end = text.indexOf('function workspaceView(');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  return new Function('esc', 'icon', `${text.slice(start, end)}; return {liveActivityView, reportHref, nextActivityReload, swapActivityScript, activityView};`)(esc, n => `<img src="icons/${n}.svg">`);
};
const { liveActivityView, reportHref, nextActivityReload, swapActivityScript, activityView: activityViewLive } = liveFns();

test('live run activity shows spend, chips and escapes names', () => {
  const html = liveActivityView({cap:'20', held:'', runs:[
    {id:'a', status:'running', pathway:'earnings_update', folder:'<img src=x onerror=1>', issuer_name:'Acme',
     started_at:'2026-11-09T13:41:00Z', spent:'3.10', files:['a.pdf'], modules:[['CP-0','done'],['CP-1','running'],['Report','waiting']]},
    {id:'b', status:'finished', pathway:'credit_snapshot', folder:'x', issuer_name:'Initech', spent:'8.42',
     report:'issuers/Initech (ini)/2026-11-09 credit_snapshot.html'},
    {id:'c', status:'running', pathway:'credit_snapshot', folder:'y', issuer_name:'Z', spent:null, modules:[]}]});
  assert.ok(!html.includes('<img'));
  assert.ok(html.includes('USD 3.10 of 20') && html.includes('spend could not be read'));
  assert.ok(html.includes('chip-done') && html.includes('chip-running') && html.includes('chip-waiting'));
  assert.ok(html.includes('href="../../issuers/Initech%20(ini)/2026-11-09%20credit_snapshot.html"'));
});
test('no live activity adds nothing', () => { assert.strictEqual(liveActivityView(undefined), ''); });

test('malformed live activity shows nothing and does not throw', () => {
  for (const bad of [null, 5, 'x', [], {}, { runs: 'no' }, { runs: {} }]) assert.strictEqual(liveActivityView(bad), '');
  const html = liveActivityView({ runs: [null, 3, [], {}, { status: 'queued' }] });
  assert.ok(html.includes('Waiting'));
});

test('live sections: waiting shows held, ended shows status, reason and the name warning, all escaped', () => {
  const html = liveActivityView({ cap: '20', held: 'daily limit <b>reached</b>', runs: [
    { id: 'q', status: 'queued', pathway: 'p', folder: 'f', issuer_name: 'Q' },
    { id: 'e', status: 'failed', pathway: 'p', folder: 'f', issuer_name: 'E', reason: '<script>x</script>', name_differs: true, ended_at: 'T', stalled: true }] });
  assert.ok(html.includes('daily limit &lt;b&gt;reached') && !html.includes('<b>') && !html.includes('<script>'));
  assert.ok(html.includes('failed') && html.includes('issuer name differs from earlier runs') && html.indexOf('Waiting') < html.indexOf('Ended'));
  assert.ok(!html.includes('<a '), 'a failed run has no report link');
});

test('a report path becomes a link only when it is a plain relative path', () => {
  assert.strictEqual(reportHref('issuers/A B/r.html'), '../../issuers/A%20B/r.html');
  for (const bad of ['/etc/passwd', 'a/../b', '../b', 'a//b', 'a/', '', './a', 'https://x/y', 'javascript:alert(1)', 'C:\\x', 'a\\b', null, undefined, 7,
    'inbox/earnings_update/evil.html', '_engine/library/index.html', 'library.html', 'x.html', '%2e%2e/x', ' /x',
    'issuers/a/b.txt', 'issuers/a/b/c.html', 'issuers/a.html', 'issuers/a/\ud800.html']) {
    assert.strictEqual(reportHref(bad), null, String(bad));
  }
  assert.strictEqual(reportHref('issuers/A/R.HTML'), '../../issuers/A/R.HTML');
  const html = liveActivityView({ runs: [{ status: 'finished', report: '../../x<y>' }] });
  assert.ok(!html.includes('<a ') && html.includes('&lt;y&gt;'));
});

test('Run activity puts live runs above the build-time content and still works without them', () => {
  const both = activityViewLive({ excluded: [['f', 'r']], issues: [] }, { runs: [{ status: 'running', folder: 'L' }] });
  assert.ok(both.indexOf('Running') >= 0 && both.indexOf('Running') < both.indexOf('Run folders not shown'));
  assert.ok(activityViewLive(null, { runs: [{ status: 'running', folder: 'L' }] }).includes('Running'));
  assert.ok(!activityViewLive({ excluded: [], issues: [] }, undefined).includes('Running'));
});

test('the 30 s re-load runs only for Run activity', () => {
  assert.strictEqual(nextActivityReload({ module: 'CP-OS', section: 'activity' }), 30000);
  for (const route of [{ module: 'W-Library' }, { module: 'W-Reports' }, { module: 'CP-1A' }, null, undefined]) assert.strictEqual(nextActivityReload(route), null);
  const screen = read('screen.js');
  assert.ok(screen.includes('nextActivityReload(current)') && !screen.includes('setInterval('));
  assert.ok(read('index.html').indexOf('../activity.js') > 0 && read('index.html').indexOf('../activity.js') < read('index.html').indexOf('static-boot.js'));
});

test('the script swap appends the new copy, removes the previous one, and starts with no previous', () => {
  const head = { kids: [], append(n) { this.kids.push(n); }, querySelector() { return this.kids.find(k => k.marked) || null; } };
  const doc = { head, createElement: () => { const n = { attrs: {}, setAttribute(k) { this.attrs[k] = ''; this.marked = true; }, remove() { head.kids = head.kids.filter(k => k !== this); } }; return n; } };
  swapActivityScript(doc, 111);
  assert.deepEqual(head.kids.map(k => k.src), ['../activity.js?t=111']);
  swapActivityScript(doc, 222);
  assert.deepEqual(head.kids.map(k => k.src), ['../activity.js?t=222']);
});

test('one bad value does not hide the Run activity view', () => {
  const lit = text => new Function(`return (${text});`)();
  for (const live of [
    lit('{"runs":[{"status":"finished","report":"issuers/A \\udc80 (a)/r.html"}]}'),
    lit('{"runs":[{"status":"running","folder":{"toString":1}}]}'),
    lit('{"held":{"toString":1,"valueOf":1},"runs":[]}'),
    lit('{"runs":[{"status":"running","modules":[[{"toString":null},"done"]]}]}')]) {
    assert.doesNotThrow(() => activityViewLive({ excluded: [], issues: [] }, live));
  }
  assert.ok(activityViewLive(null, { runs: [{ status: 'running', folder: { toString: 1 }, issuer_name: 'Kept' }] }).includes('Kept'));
});

test('the live section says how old the snapshot is, and the view re-loads at once when entered', () => {
  const html = liveActivityView({ updated: '2026-11-09T06:00:00Z <b>', runs: [{ status: 'running', folder: 'f' }] });
  assert.ok(html.indexOf('Updated') >= 0 && html.indexOf('Updated') < html.indexOf('Running') && html.includes('2026-11-09T06:00:00Z &lt;b&gt;'));
  // Run the real timer block against fake timers: entering swaps once straight away, a tick swaps again, staying does not.
  const screen = read('screen.js');
  const block = screen.slice(screen.indexOf('let activityTimer=null;'), screen.indexOf('window.onRunActivity='));
  const timers = new Map(); let id = 1; const swaps = []; const state = { current: { module: 'W-Library' } };
  const api = new Function('state', 'nextActivityReload', 'swapActivityScript', 'setTimeout', 'clearTimeout', 'document', 'Date',
    `${block.replace(/\bcurrent\b/g, 'state.current')}; return {syncActivityTimer};`)(
    state, nextActivityReload, (d, now) => swaps.push(now), (fn, ms) => { timers.set(id, fn); return id++; }, k => timers.delete(k), {}, { now: () => 5 });
  api.syncActivityTimer(); assert.deepEqual(swaps, [], 'not on Run activity: nothing');
  state.current = { module: 'CP-OS' }; api.syncActivityTimer(); assert.deepEqual(swaps, [5], 'entering re-loads once at once');
  api.syncActivityTimer(); assert.deepEqual(swaps, [5], 'still showing: no second immediate re-load');
  assert.strictEqual(timers.size, 1);
  const [fn] = timers.values(); timers.clear(); fn(); assert.deepEqual(swaps, [5, 5], 'the tick re-loads once'); assert.strictEqual(timers.size, 1);
  state.current = { module: 'W-Library' }; api.syncActivityTimer(); assert.strictEqual(timers.size, 0);
  state.current = { module: 'CP-OS' }; api.syncActivityTimer(); assert.strictEqual(swaps.length, 3, 're-entering re-loads at once');
});

test('a status adds no class names to the row', () => {
  const cls = status => liveActivityView({ runs: [{ status, folder: 'f' }] }).match(/<li class="([^"]*)"/)[1];
  assert.strictEqual(cls('x sr-only skip'), 'report-row live-run live-unknown');
  assert.strictEqual(cls('__proto__'), 'report-row live-run live-unknown');
  for (const ok of ['queued', 'running', 'finished', 'failed', 'capped', 'rejected', 'interrupted']) assert.strictEqual(cls(ok), `report-row live-run live-${ok}`);
  assert.ok(liveActivityView({ runs: [{ status: 'x sr-only skip', folder: 'f' }] }).includes('x sr-only skip'), 'the status text is still shown');
});

// The re-render helpers live in screen.js between these two markers; they take a root and the focused element.
const rerenderFns = () => {
  const text = read('screen.js');
  const block = text.slice(text.indexOf('function recordActivityView('), text.indexOf('window.onRunActivity='));
  return new Function(`${block}; return {recordActivityView, restoreActivityView};`)();
};
const stubEl = (tagName, run, extra = {}) => ({ tagName, open: false, focused: false, attrs: run === undefined ? {} : { 'data-run': run }, children: [], parentElement: null,
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }, focus() { this.focused = true; },
  querySelector(sel) { return this.children.find(c => c.tagName.toLowerCase() === sel) || null; }, ...extra });
const stubRoot = els => ({ querySelectorAll: () => els.filter(e => e.attrs['data-run'] !== undefined), contains: el => els.includes(el) || els.some(e => e.children.includes(el)) });
const withSummary = details => { const s = stubEl('SUMMARY'); s.parentElement = details; details.children.push(s); return s; };

test('a re-render keeps opened lists open and the focused control focused', () => {
  const { recordActivityView, restoreActivityView } = rerenderFns();
  const oldA = stubEl('DETAILS', 'a"1'), oldB = stubEl('DETAILS', 'b'), oldLink = stubEl('A', 'a"1');
  oldA.open = true; const oldSummary = withSummary(oldB); oldB.open = true;
  const oldRoot = stubRoot([oldA, oldB, oldLink]);
  const kept = recordActivityView(oldRoot, oldSummary);
  const newA = stubEl('DETAILS', 'a"1'), newB = stubEl('DETAILS', 'b'), newLink = stubEl('A', 'a"1'), newSummary = withSummary(newB), other = stubEl('DETAILS', 'c');
  restoreActivityView(stubRoot([newA, newB, newLink, other]), kept);
  assert.deepEqual([newA.open, newB.open, other.open], [true, true, false]);
  assert.ok(newSummary.focused && !newLink.focused, 'focus returns to the summary of the same run');
  const linkKept = recordActivityView(oldRoot, oldLink);
  const link2 = stubEl('A', 'a"1'), details2 = stubEl('DETAILS', 'a"1');
  restoreActivityView(stubRoot([details2, link2]), linkKept);
  assert.ok(link2.focused && !details2.focused, 'the same tag with the same run');
});

test('re-render helpers cope with nothing open, nothing focused and runs that have gone', () => {
  const { recordActivityView, restoreActivityView } = rerenderFns();
  const kept = recordActivityView(stubRoot([stubEl('DETAILS', 'a')]), undefined);
  assert.deepEqual(kept, { open: [], focus: null });
  assert.doesNotThrow(() => restoreActivityView(stubRoot([]), { open: ['gone'], focus: { run: 'gone', tag: 'A' } }));
  assert.doesNotThrow(() => restoreActivityView({}, kept));
  const outside = stubEl('A', 'a');
  assert.strictEqual(recordActivityView(stubRoot([]), outside).focus, null, 'focus outside the view is not recorded');
});

test('rows carry the run id for restoring, and unchanged data is not re-rendered', () => {
  const html = liveActivityView({ runs: [{ id: 'r"1', status: 'finished', folder: 'f', report: 'issuers/A/r.html', files: ['a'] }, { status: 'running', folder: 'g', files: ['b'] }] });
  assert.strictEqual([...html.matchAll(/<details class="run-files" data-run="r&quot;1">/g)].length, 1);
  assert.ok(html.includes('<a class="text-action" data-run="r&quot;1" href="../../issuers/A/r.html">'));
  assert.strictEqual([...html.matchAll(/data-run=/g)].length, 2, 'a run without an id gets no attribute');
  const screen = read('screen.js');
  const handler = screen.slice(screen.indexOf('window.onRunActivity='), screen.indexOf("window.addEventListener('hashchange',syncActivityTimer)"));
  assert.ok(handler.includes('JSON.stringify') && handler.includes('recordActivityView(') && handler.includes('restoreActivityView('));
  // Run the real handler against stubs: same runs and held again => no replacement, only the stamp text changes.
  const content = { scrollTop: 0, writes: 0, stamp: { textContent: '' }, set innerHTML(v) { this.writes++; }, get innerHTML() { return ''; }, querySelector: () => content.stamp };
  const win = { RUN_ACTIVITY: { updated: 'T1', held: '', runs: [{ id: 'a' }] } };
  const fn = new Function('window', 'document', '$', 'moduleBody', 'nameCodes', 'nextActivityReload', 'state',
    `${screen.slice(screen.indexOf('let lastActivity'), screen.indexOf('window.onRunActivity=')).replace(/\bcurrent\b/g, 'state.current')}${handler.replace(/\bcurrent\b/g, 'state.current')}; return window.onRunActivity;`)(
    win, {}, () => content, () => 'body', () => {}, () => 30000, { current: { module: 'CP-OS' } });
  fn(); assert.strictEqual(content.writes, 1);
  win.RUN_ACTIVITY = { updated: 'T2', held: '', runs: [{ id: 'a' }] }; fn();
  assert.strictEqual(content.writes, 1, 'unchanged runs: no replacement'); assert.strictEqual(content.stamp.textContent, 'T2');
  win.RUN_ACTIVITY = { updated: 'T3', held: '', runs: [{ id: 'a', status: 'running' }] }; fn();
  assert.strictEqual(content.writes, 2, 'changed runs: replaced');
  win.RUN_ACTIVITY = { updated: 'T4', cap: '20', held: '', runs: [{ id: 'a', status: 'running' }] }; fn();
  assert.strictEqual(content.writes, 3, 'a changed cap with the same runs: replaced');
});

// Design pass 2026-11-10 (docs/design/2026-11-10-impeccable-pass.md).
test('run report: every part carries an id and the label the navigator lists, in page order', () => {
  const html = runPage().runReport(RUN);
  const parts = [...html.matchAll(/<section class="[^"]*" id="(run-[a-z0-9-]+)" data-run-part="([^"]*)">/g)].map(m => [m[1], m[2]]);
  assert.deepEqual(parts, [['run-group-1', 'Financial performance'], ['run-group-2', 'Outlook and downside'], ['run-group-3', 'Decision and review'], ['run-group-4', 'Other modules'],
    ['run-register', 'Findings register'], ['run-open-items', 'Open items'], ['run-matrix', 'Module matrix']]);
  const screen = read('screen.js');
  assert.ok(screen.includes("querySelectorAll('[data-run-part]')") && screen.includes('run-[a-z0-9-]+'), 'the navigator lists the parts and the route scrolls to one');
});

test('run report: a coverage cell is the module name, its state in the title and the accessible label, and no code', () => {
  const html = runPage().runReport(RUN);
  assert.ok(/<a class="cov filled" href="[^"]*" title="Financial foundation · Reaches a conclusion" aria-label="Financial foundation, Reaches a conclusion">Financial foundation<\/a>/.test(html));
  assert.ok(/<a class="cov" href="[^"]*" title="Downside · Not assessable" aria-label="Downside, Not assessable">Downside<\/a>/.test(html));
  const strip = /<nav class="coverage".*?<\/nav>/s.exec(html)[0].replace(/ href="[^"]*"/g, '');
  assert.ok(!/\bCP-[A-Z0-9]+\b/.test(strip), 'no code in the strip');
});

test('charts: one chip-dot legend per set of charts, under the last card', () => {
  const html = runPage().chartCards(['<i>a</i>', '<i>b</i>', '<i>c</i>']);
  assert.equal(countOf(html, /class="legend"/g), 1);
  assert.equal(countOf(html, /class="panel-card"/g), 3);
  assert.ok(html.indexOf('class="legend"') > html.indexOf('<i>c</i>'));
  assert.equal(runPage().chartCards([]), '');
  // A chart without the heading is left as it is: its own h2 is not half-retagged.
  assert.equal(runPage().chartCards(['<h2>own</h2>']).includes('<h2>own</h2>'), true);
  assert.ok(runPage().chartCards(['<div class="section-heading"><h2>Cost $1 &amp; $&</h2></div>']).includes('<h4>Cost $1 &amp; $&</h4>'));
  // A card's chart title is an h4 (it sits under a module's h3); the rest of the chart is untouched.
  assert.equal(runPage().chartCards(['<div class="section-heading"><h2>Leverage</h2><span>x</span></div><h2>kept</h2>']), '<div class="panel-card"><div class="section-heading"><h4>Leverage</h4><span>x</span></div><h2>kept</h2><div class="legend"><span>Chip dot: <i class="dot"></i> issuer page · <i class="dot row"></i> handoff row · <i class="dot up"></i> upstream module · <i class="dot gap"></i> gap</span></div></div>');
});

test('screen.css: run-report tables run whole in the text face', () => {
  const css = read('screen.css');
  assert.ok(css.includes('.run-section .table-scroll{max-height:none;overflow:clip}'));
  assert.ok(css.includes("table.register td,table.open-items td,table.matrix td{font-family:'Red Hat Text',sans-serif"));
});

test('run report: a run with no module output says so and keeps the source inventory link; no empty strip, table or count line', () => {
  const html = runPage(() => ({})).runReport(RUN);
  assert.equal(strip(/<div class="missing-state">(.*?)<\/div>/.exec(html)[1]), 'No module output retained for this runThe run report is drawn from module handoffs, and this run holds none.');
  assert.ok(html.includes('href="#W-Evidence/sources?c=run-a"'));
  for (const gone of ['class="run-count"', 'class="coverage"', '<table']) assert.ok(!html.includes(gone), gone);
});

test('hardening: the module report\'s section title is an h2, fold arrows respect reduced motion, the page prints whole', () => {
  const screen = read('screen.js'), css = read('screen.css');
  assert.ok(screen.includes("const level=report?'h2':'h3';"));
  assert.ok(/@media\(prefers-reduced-motion:reduce\)\{[^}]*details\.fold>summary img[^}]*\{transition:none\}/.test(css));
  assert.ok(/@media print\{[^@]*#content\{[^}]*overflow:visible/.test(css));
  assert.ok(/@media\(forced-colors:active\)\{[^@]*a\.cov\.filled\{/.test(css));
});

test('module tables: a numeric column is .num, a number in a text column is .fig, a sentence has no figure class', () => {
  const { cellView } = runPage();
  assert.equal(cellView('1,299', true), '<td class="num">1,299</td>');
  assert.equal(cellView('1,299', false), '<td class="fig">1,299</td>');
  assert.equal(cellView('(12.5)%', false), '<td class="fig">(12.5)%</td>');
  assert.equal(cellView('Reported GAAP; Annual page:121', false), '<td>Reported GAAP; Annual page:121</td>');
  const css = read('screen.css');
  assert.ok(css.includes(".table-card td{font-family:'Red Hat Text',sans-serif}.table-card td.fig{font-family:'Red Hat Mono',monospace"));
});

test('library: a row is one item per column; what left the row is the cell title or the selected-run panel', () => {
  const { libraryRow } = runPage();
  const metric = (value, basis) => ({ value, unit: 'x', basis, period: 'FY2024' });
  const run = { id: 'run-z', name: 'Zed & Sons', issuer: 'ZED', title: 'Credit Snapshot', sector: 'Telecoms', date: '2024-09-30', period: 'FY-2024', completion: null, artifacts: [],
    metrics: { leverage: metric('6.5744', 'C9; same "basis"'), net_leverage: metric('0', 'Net of cash'), coverage: null }, ratings: [{ label: 'B+', agency: 'S&P', scope: 'issuer', date: '2024-06-30' }] };
  const cells = [...libraryRow(run, true, false).matchAll(/<td([^>]*)>(.*?)<\/td>/g)].map((m) => [m[1].trim(), m[2]]);
  // Ten columns, in the header's order; a cell holds one value and at most the one control that acts on it.
  assert.deepEqual(cells.map(([, body]) => strip(body)), ['Zed &amp; Sons', 'run-z', 'Telecoms', '30 Sept 2024', '6.5744×', '0×', 'n.a.', 'B+', 'Not assessed', 'Handoffs only']);
  assert.ok(cells.every(([, body]) => countOf(body, /<(?!\/)/g) <= 1));
  assert.ok(/^<button class="library-run-name" type="button" data-library-select="run-z" aria-expanded="true" aria-controls="run-detail"/.test(cells[0][1]));
  // A run the store does not hold has no link; its id is still shown.
  assert.deepEqual(cells[1], ['class="run-id" title="run-z"', 'run-z']);
  // The basis and the rating detail stay on the cell; a missing figure reads n.a., a zero is a zero.
  assert.equal(cells[4][0], 'title="C9; same &quot;basis&quot;"');
  assert.equal(cells[5][0], 'title="Net of cash"');
  assert.equal(cells[6][0], 'class="missing" title="Not available"');
  assert.equal(cells[7][0], 'title="S&amp;P · Issuer · 30 Jun 2024"');
  // A run the store holds opens from its id; a percentage and the not-screened note are single items too.
  const held = libraryRow({ ...run, id: RUN, completion: 75, ratings: [] }, false, true);
  assert.ok(held.includes(`<td class="run-id" title="${RUN}"><a href="#W-Overview/overview?c=${RUN}" aria-label="Open run: Zed &amp; Sons, ${RUN}">${RUN}</a></td>`), held);
  assert.ok(held.endsWith('<td class="missing" title="No rating recorded">n.a.</td><td>75%</td><td>No report · not screened</td></tr>'));
  const views = read('views.js'), screen = read('screen.js');
  // The selected-run panel carries the ticker, workflow and period the row no longer shows; the issuer rail is a select.
  assert.ok(views.includes("esc(`${run.issuer} · ${run.id} / ${run.title}`)") && views.includes("['Evidence date',libraryDate(run.date),run.period]"));
  assert.ok(views.includes("select('issuer','Issuer','All issuers')"));
  // The stylesheet right-aligns columns 5 to 7 by position: they are the three ratios.
  assert.ok(views.includes("[['name','Issuer'],[null,'Run'],[null,'Sector'],['date','Evidence date'],['leverage','Leverage'],['net_leverage','Net leverage'],['coverage','Coverage'],['rating','Rating'],['completion','Completeness'],[null,'Deliverable']]"));
  assert.ok(read('screen.css').includes('.library-table :is(th,td):nth-child(n+5):nth-child(-n+7){text-align:right}'));
  for (const gone of ['library-nav', 'data-library-issuer', 'cell-primary', 'Combined filters', 'class="eyebrow"']) assert.ok(!views.includes(gone) && !screen.includes(gone), gone);
});

test('hardening: unbroken strings wrap in the canvas, the inspector and the library table; narrow run tables scroll by their own width', () => {
  const css = read('screen.css');
  assert.ok(css.includes('#content,.inspector{overflow-wrap:break-word}'));
  assert.ok(/\.library-table\{width:100%;min-width:1000px;table-layout:fixed;/.test(css));
  // The ten fixed columns account for the whole table.
  const widths = [...css.matchAll(/\.library-table th:nth-child\(\d+\)\{width:([\d.]+)%\}/g)].map((m) => Number(m[1]));
  assert.equal(widths.length, 10);
  assert.ok(Math.abs(widths.reduce((a, b) => a + b, 0) - 100) < 1e-9);
  assert.ok(/\.run-section\{container-type:inline-size\}\s*@container \(max-width:600px\)\{\.run-section \.table-scroll\{overflow-x:auto\}/.test(css));
  // Paper has no sideways scroll: the minimum widths are dropped in print.
  assert.ok(/@media print\{[^@]*\.library-table,table\.register,table\.open-items,table\.matrix\{min-width:0\}/.test(css));
});

test('library: a file is linked only in the two forms the build writes, a presented report or a retained workspace file', () => {
  const { libraryPath } = runPage();
  for (const good of ['reports/run-a/9c5b/report.html', '../runs/run-a/deliveries/9c5b/CP-1.md', 'reports/A%20B/x/report.html', '../runs/a_b-c.d~e/x.md']) {
    assert.strictEqual(libraryPath(good), true, good);
  }
  for (const bad of ['/etc/passwd', '/files/runs/a/x.md', '//evil.example/x', 'https://x/y', 'javascript:alert(1)', 'file:///x', 'C:\\x', 'reports/../../x', '../../x', '../runs/../../x',
    'reports/./x', 'reports/%2e%2e/x', 'reports/%2E%2E/x', '..%2fx', '../runs/x%2f..%2fy', '../runs/x/%5c..%5cy', 'reports/a\\b', 'reports//x', 'reports/', '../', 'reports', 'x.html',
    'runs/a/x.md', 'reports/a?b', 'reports/a#b', ' reports/a', 'reports/a b', '', null, undefined, 7]) {
    assert.strictEqual(libraryPath(bad), false, String(bad));
  }
});

// Owner, 2026-11-10: "Charts with periods should be transposed, with period on the x axis". Every reader chart is a
// "Chart data:" table whose first column is Period (store.py _chart_table), so each one is drawn as columns over periods.
test('reader charts: periods run along the x axis, one group per period in table order, one column per series', () => {
  const [fn, id] = chartFn('readerChart', ['Period', 'Total debt / EBITDA', 'Net debt / EBITDA', 'Reporting unit', 'Basis'],
    [[81, 'FY2023 / 2023-09-30', '6.33', '5.22', 'x', 'K'], [82, 'FY2024', '6.57', '4.93', 'x', 'K'], [83, 'FY2025', 'Not supplied: no forecast', '4.10', 'x', 'K']]);
  const html = fn(id, { title: 'Leverage', unit: 'x', table: 80, columns: [1, 2] });
  assert.ok(html.includes('<div class="column-chart"') && !html.includes('horizontal-chart'));
  // The series are named once, in a legend, in column order.
  assert.ok(html.includes('<div class="chart-legend"><span><i class="series-0"></i>Total debt / EBITDA</span><span><i class="series-1"></i>Net debt / EBITDA</span></div>'));
  const groups = [...html.matchAll(/<button class="chart-row" data-evidence="([^"]+)"[^>]*>(.*?)<\/button>/g)];
  assert.deepEqual(groups.map((g) => g[1]), [`${id}:81`, `${id}:82`, `${id}:83`]);
  // The period label is the x-axis label under its columns, written exactly as the handoff has it.
  assert.deepEqual(groups.map((g) => /<span class="chart-label">(.*?)<\/span>$/.exec(g[2])?.[1]), ['FY2023 / 2023-09-30', 'FY2024', 'FY2025']);
  for (const [, , body] of groups) assert.equal(countOf(body, /<span class="col/g), 2);
  // Heights are to scale from a zero baseline; the largest value fills the plot.
  assert.ok(groups[1][2].includes('<i class="series-0" style="bottom:0%;height:100%"></i><strong style="bottom:100%">6.57</strong>'));
  assert.ok(groups[0][2].includes('<i class="series-1" style="bottom:0%;height:79.45%"></i><strong style="bottom:79.45%">5.22</strong>'));
  // A value that is text draws no column; n.a. keeps the text in its title.
  assert.ok(groups[2][2].includes('<span class="col missing"><strong style="bottom:0%" title="Not supplied: no forecast">n.a.</strong></span>'));
  assert.ok(groups[0][2].startsWith('<span class="plot"><span class="zero-rule" style="bottom:0%"></span>'));
  // The button names the period and every value, for a screen reader that does not see the columns.
  assert.ok(html.includes(`aria-label="FY2023 / 2023-09-30: Total debt / EBITDA 6.33, Net debt / EBITDA 5.22. View source"`));
});

test('reader charts: a negative value hangs below a raised zero baseline; chips sit under their period', () => {
  const [fn, id] = chartFn('readerChart', ['Period', 'Free cash flow', 'Reporting unit', 'Basis'], [[81, 'FY2023', '300', 'US$m', 'K'], [82, 'FY2024', '(100)', 'US$m', 'K']]);
  const html = fn(id, { title: 'FCF', unit: 'US$m', table: 80, columns: [1] }, true);
  assert.ok(html.includes('<span class="zero-rule" style="bottom:25%"></span>'));
  assert.ok(html.includes('<i class="series-0" style="bottom:25%;height:75%"></i><strong style="bottom:100%">300</strong>'));
  assert.ok(html.includes('<i class="series-0 negative" style="bottom:0%;height:25%"></i><strong class="below" style="bottom:0%">(100)</strong>'));
  // With chips each period is a group: its button holds the columns and label, its chips follow it.
  assert.equal(countOf(html, /<div class="chart-row" role="group" aria-label="FY202[34]"><button class="chart-open" data-evidence=/g), 2);
});

// ---- Package 1 views (2026-11-10): revenue and EBITDA, the liquidity bridge and the refinancing need. Every value below is synthetic.
const SYNTHETIC_BRIDGE = [[63, 'Opening accessible liquidity', '900', 'US$m', 'Synthetic.'], [64, 'Free cash flow', '120', 'US$m', 'Synthetic.'], [65, 'Debt repayment', '-450', 'US$m', 'Synthetic.'], [66, 'Closing accessible liquidity', '570', 'US$m', 'Synthetic.']];
const BRIDGE_CHART = { title: 'Liquidity bridge', unit: 'US$m', table: 62, kind: 'waterfall', amount: 1, columns: [1] };
const withBridge = d => {
  const cp1 = d[outId('CP-1')];
  cp1.sections.push(sec('Chart data: liquidity bridge', 3, 60, 'consumed', [table(62, ['Step', 'Amount', 'Reporting unit', 'Basis and limitation'], SYNTHETIC_BRIDGE)]));
  cp1.charts.push(BRIDGE_CHART);
  return d;
};

test('reader charts: a step table is a waterfall of its stated amounts, each bar linked to its handoff row', () => {
  const page = runPage(withBridge);
  const html = page.readerChart(outId('CP-1'), BRIDGE_CHART);
  assert.ok(html.includes('<div class="vector-chart">') && !html.includes('column-chart'));
  assert.equal(countOf(html, /<a class="plot-point"/g), 4);
  // The opening and the closing stand on the axis; the change between them hangs as stated.
  assert.equal(countOf(html, /<rect class="total"/g), 2);
  assert.equal(countOf(html, /<rect class="movement"/g), 1);
  assert.equal(countOf(html, /<rect class="outflow"/g), 1);
  assert.ok(html.includes('aria-label="Opening accessible liquidity, 900 US$m. View source"'));
  assert.ok(html.includes(`data-evidence="${outId('CP-1')}:66"`) && html.includes('>570</text>'));
  // The unit and period read in the heading; no module code or step id shows.
  assert.ok(html.includes('<h2>Liquidity bridge</h2><span>US$m</span>') && !/CP-\d/.test(strip(html)));
});

test('reader charts: every chart has its table form, the handoff table as written with its chips', () => {
  const page = runPage(withBridge);
  const html = page.readerChart(outId('CP-1'), BRIDGE_CHART);
  const form = /<details class="chart-table"><summary>Table form<\/summary>(.*?)<\/details>/s.exec(html)?.[1];
  assert.ok(form, 'a table form');
  assert.deepEqual([...form.matchAll(/<th scope="col"[^>]*>(.*?)<\/th>/g)].map(m => m[1]), ['Step', 'Amount', 'Reporting unit', 'Basis and limitation', 'Source']);
  assert.equal(countOf(form, /<tr><td/g), 4);
  assert.ok(form.includes('Closing accessible liquidity') && form.includes('>570<') && form.includes('>-450<'));
  const periods = runPage(d => d).readerChart(outId('CP-1'), { title: 'Leverage', unit: 'x', table: 42, columns: [1] });
  assert.ok(/<details class="chart-table"><summary>Table form<\/summary>.*<td>FY2024<\/td>.*<\/details>/s.test(periods));
});

test('reader charts: revenue and EBITDA and the refinancing need are columns per series over periods, a gap drawn as n.a.', () => {
  const page = runPage(d => {
    const cp1 = d[outId('CP-1')];
    cp1.sections.push(
      sec('Chart data: revenue and EBITDA', 3, 70, 'consumed', [table(72, ['Period', 'Revenue', 'Adjusted EBITDA', 'Reporting unit', 'Basis and limitation'], [[73, 'FY2023', '2,100', '410', 'US$m', 'Synthetic.'], [74, 'FY2024', '2,250', 'Not supplied: the measure is not stated', 'US$m', 'Synthetic.']])]),
      sec('Chart data: refinancing need', 3, 80, 'consumed', [table(82, ['Period', 'Debt maturing', 'Committed resources', 'Reporting unit', 'Basis and limitation'], [[83, 'FY2026', '500', '300', 'US$m', 'Synthetic.']])]));
    return d;
  });
  const id = outId('CP-1');
  const revenue = page.readerChart(id, { title: 'Revenue and EBITDA', unit: 'US$m', table: 72, columns: [1, 2] });
  assert.ok(revenue.includes('<h2>Revenue and EBITDA</h2><span>US$m</span>') && revenue.includes('<span><i class="series-1"></i>Adjusted EBITDA</span>'));
  assert.ok(revenue.includes('<span class="col missing"><strong style="bottom:0%" title="Not supplied: the measure is not stated">n.a.</strong></span>'));
  assert.ok(revenue.includes('<strong style="bottom:100%">2,250</strong>'));
  const need = page.readerChart(id, { title: 'Refinancing need', unit: 'US$m', table: 82, columns: [1, 2] });
  assert.equal(countOf(need, /<span class="col">/g), 2);
  assert.ok(need.includes('<span><i class="series-0"></i>Debt maturing</span><span><i class="series-1"></i>Committed resources</span>'));
  for (const html of [revenue, need]) assert.ok(html.includes('<details class="chart-table"><summary>Table form</summary>'));
});

test('reader charts: a bridge whose running position dips below zero is drawn inside its frame on a zero rule', () => {
  const rows = [[63, 'Opening accessible liquidity', '100'], [64, 'Debt repayment', '-300'], [65, 'New notes', '250'], [66, 'Closing accessible liquidity', '50']].map(([n, s, a]) => [n, s, a, 'US$m', 'Synthetic.']);
  const page = runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: liquidity bridge', 3, 60, 'consumed', [table(62, ['Step', 'Amount', 'Reporting unit', 'Basis and limitation'], rows)])); return d; });
  const html = page.readerChart(outId('CP-1'), BRIDGE_CHART);
  const rects = [...html.matchAll(/<rect class="(\w+)" x="[^"]*" y="([^"]*)" width="[^"]*" height="([^"]*)"/g)].map(m => ({ cls: m[1], top: Number(m[2]), bottom: Number(m[2]) + Number(m[3]) }));
  assert.equal(rects.length, 4);
  for (const r of rects) assert.ok(r.top >= -12 && r.bottom <= 210.001, JSON.stringify(r));
  // The zero rule sits where the opening and closing bars stand; the deepest point (-200) reaches the floor.
  const zero = Number(/<line x1="0" y1="([^"]*)" x2="660" y2="\1" class="axis zero-axis"\/>/.exec(html)[1]);
  assert.ok(zero < 210 && Math.abs(rects[0].bottom - zero) < 0.01 && Math.abs(rects[3].bottom - zero) < 0.01);
  assert.ok(Math.abs(rects[1].bottom - 210) < 0.01, 'the outflow ends at the lowest running position');
});

test('the "Missing values have no bar" note prints under the last period chart, not the bridge after it', () => {
  const page = runPage(d => {
    withBridge(d);
    return d;
  });
  // CP-1's charts are Leverage, Cover, then the bridge; the note is under Cover.
  const mod = storyModule(page.runReport(RUN), 'CP-1');
  assert.equal(countOf(mod, /Missing values have no bar/g), 1);
  const cards = mod.split('<div class="panel-card">').slice(1);
  assert.deepEqual(cards.map(c => c.includes('Missing values have no bar')), [false, true, false]);
  // A module with only a bridge prints no note, and leaves it for the next module that has period charts.
  const alone = runPage(d => { d[outId('CP-1')].charts = [BRIDGE_CHART]; return withBridge(d); });
  assert.equal(countOf(storyModule(alone.runReport(RUN), 'CP-1'), /Missing values have no bar/g), 0);
});

test('run report: the bridge is drawn in its module story beside the module\'s other charts', () => {
  const mod = storyModule(runPage(withBridge).runReport(RUN), 'CP-1');
  assert.ok(mod.includes('<div class="vector-chart">') && mod.includes('<div class="column-chart"'));
  assert.ok(mod.indexOf('column-chart') < mod.indexOf('vector-chart'), 'charts keep the handoff order');
});

// ---- Package 2 views (2026-11-10): the debt stack, covenant and rating-trigger headroom and portfolio limits. Every value below is synthetic.
const TAIL = ['Reporting unit', 'Basis and limitation'];
const STACK = { title: 'Debt stack', unit: 'US$m', table: 92, kind: 'stack', label: 0, rank: 1, secured: 2, amount: 3, leverage: 4, columns: [3, 4] };
const BULLET = { title: 'Covenant headroom', unit: '', table: 102, kind: 'bullet', label: [0], threshold: 1, current: 2, headroom: 3, direction: 4, columns: [1, 2] };
const LIMITS = { title: 'Portfolio limits', unit: '% NAV', table: 112, kind: 'limits', label: 0, current: 1, proposed: 2, limit: 3, columns: [1, 2, 3] };
const withStructure = d => {
  const cp1 = d[outId('CP-1')];
  cp1.sections.push(
    sec('Chart data: debt stack', 3, 90, 'consumed', [table(92, ['Facility', 'Ranking', 'Secured', 'Amount', 'Cumulative leverage', ...TAIL], [[93, 'Term loan', '1', 'Yes', '1,200', '2.4', 'US$m', 'Synthetic.'], [94, 'Notes', '2', 'No', '800', '4.0', 'US$m', 'Synthetic.'], [95, 'Subordinated', '3', 'No', 'Not supplied: not stated', 'Not supplied: no balance', 'US$m', 'Synthetic.']])]),
    sec('Chart data: covenant headroom', 3, 100, 'consumed', [table(102, ['Test', 'Threshold', 'Current', 'Headroom', 'Direction', ...TAIL], [[103, 'Net leverage', '5.0', '4.2', '0.8x', 'Passes at or below', 'x', 'Synthetic.'], [104, 'Interest cover', '2.0', '2.6', '0.6x', 'Passes at or above', 'x', 'Synthetic.'], [105, 'Liquidity', '100', 'Not supplied: not stated', 'Not supplied: no current', 'Passes at or above', 'US$m', 'Synthetic.']])]),
    sec('Chart data: portfolio limits', 3, 110, 'consumed', [table(112, ['Limit', 'Current exposure', 'Proposed exposure', 'Limit value', ...TAIL], [[113, 'Single issuer', '3.0', '4.0', '5.0', '% NAV', 'Synthetic.'], [114, 'High-yield bucket', '12.0', 'Not supplied: no proposal', '15.0', '% NAV', 'Synthetic.']])]));
  cp1.charts.push(STACK, BULLET, LIMITS);
  return d;
};

test('structure views: a debt stack is segments in stated rank order, widths from the stated amounts, leverage as stated', () => {
  const html = runPage(withStructure).readerChart(outId('CP-1'), STACK);
  const segments = [...html.matchAll(/<a class="stack-seg series-(\d)" href="[^"]*" data-evidence="[^"]*:(\d+)" style="width:([\d.]+)%"/g)].map(m => [m[1], m[2], m[3]]);
  assert.deepEqual(segments, [['0', '93', '60'], ['1', '94', '40']]);
  const key = strip(/<ol class="stack-key">(.*?)<\/ol>/s.exec(html)[1]);
  assert.ok(key.indexOf('Term loan') < key.indexOf('Notes') && key.indexOf('Notes') < key.indexOf('Subordinated'));
  assert.ok(key.includes('Secured') && key.includes('1,200') && key.includes('2.4x') && key.includes('4.0x'));
  // A gap is stated as n.a. in the key and has no segment; it is not a zero.
  assert.ok(/Subordinated.*n\.a\./s.test(key) && !/Subordinated.*>0</s.test(key));
  assert.ok(html.includes('<p class="matrix-note">A facility with no stated amount has no segment.</p>'));
  assert.ok(html.includes('<h2>Debt stack</h2><span>US$m</span>') && !/CP-\d/.test(strip(html)));
  assert.ok(html.includes('<details class="chart-table"><summary>Table form</summary>'));
});

test('structure views: a bullet chart marks the stated threshold and current, the passing side and the stated headroom', () => {
  const html = runPage(withStructure).readerChart(outId('CP-1'), BULLET);
  const row = html.split('<div class="bullet-row"')[1];
  assert.ok(row.includes('<i class="pass" style="left:0%;width:90.91%"></i>'), 'at or below passes under the threshold');
  assert.ok(row.includes('<i class="tick" style="left:90.91%"></i>') && row.includes('<i class="marker" style="left:76.36%"></i>'));
  assert.ok(strip(row).includes('Threshold 5.0') && strip(row).includes('Current 4.2') && strip(row).includes('Headroom 0.8x') && strip(row).includes('Passes at or below'));
  const above = html.split('<div class="bullet-row"')[2];
  assert.ok(above.includes('<i class="pass" style="left:'), 'at or above passes over the threshold');
  assert.equal(countOf(above, /<i class="pass" style="left:(\d+(?:\.\d+)?)%;width:(\d+(?:\.\d+)?)%"><\/i>/g), 1);
  // A current value that is not stated has no marker and is n.a., never the zero position.
  const gap = html.split('<div class="bullet-row"')[3];
  assert.ok(!gap.includes('class="marker"') && strip(gap).includes('Current n.a.') && gap.includes('class="tick"'));
  assert.ok(html.includes('<details class="chart-table"><summary>Table form</summary>'));
});

test('structure views: a rating-trigger row is labelled by agency and trigger, with no headroom claimed', () => {
  const chart = { ...BULLET, title: 'Rating triggers', unit: 'x', label: [0, 1], threshold: 2, current: 3, headroom: null, direction: 4, table: 122 };
  const page = runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: rating triggers', 3, 120, 'consumed', [table(122, ['Agency', 'Trigger', 'Threshold', 'Current', 'Direction', ...TAIL], [[123, 'Agency A', 'Net leverage review', '5.5', '4.2', 'Passes below', 'x', 'Synthetic.']])])); d[outId('CP-1')].charts.push(chart); return d; });
  const html = page.readerChart(outId('CP-1'), chart);
  assert.ok(strip(html).includes('Agency A') && strip(html).includes('Net leverage review') && !strip(html).includes('Headroom'));
  assert.ok(html.includes('<i class="pass" style="left:0%;width:'), 'below passes under the threshold');
});

test('structure views: portfolio limits are bars of the stated exposures with a tick at the stated limit', () => {
  const html = runPage(withStructure).readerChart(outId('CP-1'), LIMITS);
  const first = html.split('<div class="limit-row"')[1];
  assert.ok(first.includes('<i class="series-0" style="width:54.55%"></i>') && first.includes('<i class="series-1" style="width:72.73%"></i>'));
  assert.ok(first.includes('<i class="tick" style="left:90.91%"></i>') && strip(first).includes('Limit 5.0'));
  const gap = html.split('<div class="limit-row"')[2];
  assert.equal(countOf(gap, /<i class="series-1"/g), 0);
  assert.ok(strip(gap).includes('Proposed n.a.') && gap.includes('class="tick"'));
  assert.ok(html.includes('<details class="chart-table"><summary>Table form</summary>'));
});

test('structure views: no amber or red in the series, stack, tick or limit rules; a stated zero amount draws no note', () => {
  const css = read('screen.css').replace(/\/\*.*?\*\//gs, '').split('}').filter(r => /series-|stack|\.tick|limit-key/.test(r.split('{')[0]));
  assert.ok(css.length > 4 && css.every(r => !/amber|red\)|#8a5300|#b3261e/.test(r)));
  const html = runPage(d => { const t = withStructure(d)[outId('CP-1')].sections.flatMap(x => x.blocks).find(b => b.line === 92); t.rows[2].cells[3] = '0'; return d; }).readerChart(outId('CP-1'), STACK);
  assert.ok(!html.includes('no stated amount'));
});

test('structure views: only a period chart carries the missing-values note, once, under the last of them', () => {
  const mod = storyModule(runPage(withStructure).runReport(RUN), 'CP-1');
  assert.equal(countOf(mod, /Missing values have no bar\./g), 1);
  assert.ok(mod.indexOf('Missing values have no bar.') < mod.indexOf('stack-key'), 'the note sits under the period charts, before the structure views');
});

// ---- Screens pass (2026-11-10): what a reader acts on is shown; production detail (hashes, file names, word counts) is a title or behind a disclosure.
const HASH = 'f'.repeat(64);
const zedRun = (extra = {}) => ({ id: RUN, name: 'Zed & Sons', issuer: 'ZED', title: 'Credit Snapshot', sector: 'Telecoms', workflow: 'Credit Snapshot', date: '2024-09-30', period: 'FY-2024', completion: null, summary: 'Leverage is high.', gaps: [], ratings: [], currency: 'USD',
  metrics: { leverage: { value: '6.57', unit: 'x', basis: 'Total debt / EBITDA', period: 'FY2024' } },
  artifacts: [{ kind: 'report', label: HASH, state: 'candidate', relationship: 'direct', issue: '', available: true, href: `reports/${RUN}/${HASH}/report.html` }], ...extra });
const zedReport = (run, id = HASH) => ({ id, label: 'Zed & Sons · as of 30 September 2024', build: null, status: null, mode: 'candidate', qualification: 'partial', issuer: 'Zed & Sons', issuerKey: 'zed', href: `reports/${run}/${id}/report.html`, download: `reports/${run}/${id}/original.html`,
  builtFrom: [{ module: 'CP-1', run, source: `${run}/deliveries/${id}/CP-1.md`, sha256: 'a'.repeat(64), output: false }], files: [{ href: 'x/report.json', name: 'report.json' }] });

test('library panel: a deliverable is named by its report and its recorded acceptance; measures the run lacks are one line', () => {
  const page = runPage(d => d, [zedReport(RUN)]);
  page.libraryState.selected = RUN;
  const html = page.libraryDetail({ rows: [zedRun()] });
  const list = /<ul class="artifact-list">(.*?)<\/ul>/s.exec(html)[1];
  // The report's name is the link; the delivery folder's hash is not shown as text, and no build check is recited.
  assert.ok(list.includes('>Zed &amp; Sons · as of 30 September 2024</a><small>Candidate · not accepted</small>'), list);
  assert.ok(!strip(html).includes(HASH) && !html.includes('file hashes'));
  // The acceptance is stated beside the buttons that open the report.
  assert.ok(/<div class="detail-actions"><span class="badge badge-gray">Candidate · not accepted<\/span><a /.test(html));
  // One card for the measure the run has; the seven it lacks are named once, with no empty card.
  assert.equal(countOf(html, /class="metric-item"/g), 1);
  assert.ok(html.includes('<p class="metric-absent">Not established for this run: Revenue, EBITDA, Net leverage, Interest coverage, Closing cash, Undrawn facilities, Cash flow measure.</p>'));
  // A catalogued file the store does not hold keeps its own label; an accepted one says so.
  const other = page.libraryDetail({ rows: [zedRun({ artifacts: [{ kind: 'report', label: 'Board pack', state: 'accepted', relationship: 'direct', issue: '', available: true, href: 'reports/elsewhere/pack.html' }] })] });
  assert.ok(other.includes('>Board pack ↗</a><small>Accepted</small>'), other);
});

test('library filters: Reset shows only while something is filtered or sorted; Completeness is offered once a run records one', () => {
  const page = runPage(d => d, [], m => m, { catalogue: [zedRun()] });
  const idle = page.libraryPanel();
  assert.ok(idle.includes('<button id="library-clear" class="tertiary-action" type="button" hidden>Reset filters</button>'));
  assert.ok(!idle.includes('id="library-completion"'));
  page.libraryState.sortKey = 'name';
  assert.ok(page.libraryPanel().includes('<button id="library-clear" class="tertiary-action" type="button">Reset filters</button>'));
  const assessed = runPage(d => d, [], m => m, { catalogue: [zedRun({ completion: 75 })] }).libraryPanel();
  assert.ok(assessed.includes('id="library-completion"') && assessed.includes('75% or above'));
  // The address is read against the same options, so it cannot set a Completeness nothing can match.
  assert.ok(read('views.js').includes("completion:runs.some(run=>run.completion!=null)?[['75','75% or above']"));
});

test('reports: a report from another run names that run; the delivery hash is a title, never the row text; one provenance disclosure', () => {
  const OTHER = 'run-b', OTHER_HASH = 'e'.repeat(64);
  const reports = [zedReport(RUN), zedReport(OTHER, OTHER_HASH)];
  const contextsMore = { [OTHER]: { folder: OTHER, run: 'RUN-B', modules: {} } };
  const page = runPage(d => d, reports, m => m, { contexts: contextsMore });
  const list = page.reportList(RUN);
  const rows = [...list.matchAll(/<li class="report-row">(.*?)<\/li>/gs)].map(m => m[1]);
  assert.equal(rows.length, 2);
  const own = rows.find(r => r.includes(`title="Delivery ${HASH}"`)), other = rows.find(r => r.includes(`title="Delivery ${OTHER_HASH}"`));
  assert.ok(own && !own.includes('class="code"'), own);
  assert.ok(other.includes('<span class="code">RUN-B</span>'), other);
  assert.ok(!strip(list).includes(HASH) && !strip(list).includes(OTHER_HASH));
  // The heading already says the report was built from this run: no sentence repeats it.
  assert.ok(list.includes('<h2>Built from this run</h2>') && !list.includes('class="intro"'));
  // Reading one report: its sources and files are one disclosure in plain words; the way back is the rail and Change run.
  const view = page.reportView(reports[1], OTHER);
  assert.equal(countOf(view, /<details class="built-from">/g), 1);
  assert.ok(view.includes('<summary>Built from 1 handoff · each matches its run file · 1 file</summary>'));
  assert.ok(view.includes('<h3>Files in this deliverable</h3><ul><li><a href="x/report.json" download>report.json</a></li></ul></details>'));
  assert.ok(!view.includes('Return to library') && !view.includes('byte-identical'));
  // Reports of one issuer and date share a name, so the selector names the run too.
  assert.ok(view.includes(`<option value="${OTHER_HASH}" selected>Zed &amp; Sons · as of 30 September 2024 · RUN-B</option>`), view);
  // A handoff with no matching run file is still said, in place of the match.
  const loose = { ...reports[1], builtFrom: [{ module: 'CP-1', run: null, source: 'CP-1.md', sha256: 'b'.repeat(64) }] };
  assert.ok(page.reportView(loose, OTHER).includes('<summary>Built from 1 handoff · 1 with no matching run file · 1 file</summary>'));
});

test('run report: a finding shows its resolved chips; citations without a page are counted on the module page only', () => {
  const gap = { chips: { [`${outId('CP-1')}:17`]: [{ kind: 'gap', label: 'no page' }] } };
  const html = runPage(d => d, [], m => m, gap).runReport(RUN);
  const story = storyModule(html, 'CP-1');
  assert.ok(story.includes('aria-label="Handoff row, line 17"') && story.includes('data-chip='));
  assert.ok(!html.includes('chip-count') && !html.includes('without a page'));
});

test('screens pass: one word for a run, in-app actions carry no out-arrow, and the styles the markup needs exist', () => {
  const views = read('views.js'), css = read('screen.css'), screen = read('screen.js');
  assert.ok(!/Change case|another case|for this case|other cases/.test(views));
  assert.ok(views.includes('>Change run</a>') && !views.includes('View source ↗'));
  for (const sel of ['.metric-absent{', '.library-table td.run-id{white-space:nowrap', '.built-from h3{', '#run-matrix .table-scroll{max-width']) assert.ok(css.includes(sel), sel);
  // Never assessed is a fact, not an alert: the completeness note no longer uses the amber of states that need action.
  const box = css.slice(css.lastIndexOf('.completion-box{'));
  assert.ok(box.startsWith('.completion-box{border-color:var(--border-secondary);background:var(--gray-50)'));
  // The list of reports is a page of links: it has no pager.
  assert.ok(screen.includes("(next.module==='W-Reports'&&next.section==='list')"));
});

test('embedded report: the navigator uses the workspace\'s module names, keeping the report\'s own as the title', () => {
  const src = read('report-adapter.js');
  const last = src.slice(src.lastIndexOf('(() => {'));
  // Run the naming pass over a minimal document: one module link as the report renders it.
  const text = { nodeType: 3, data: 'Canonical data foundation' };
  const link = { title: '', getAttribute: attribute => (attribute === 'href' ? '#CP-1' : null), querySelector: () => ({ firstChild: text }) };
  const root = { querySelectorAll: selector => (selector === '.module-link' ? [link] : []) };
  const walker = { nextNode: () => false };
  const doc = { querySelectorAll: () => [root], createTreeWalker: () => walker };
  class Observer { observe() {} }
  new Function('document', 'MutationObserver', 'NodeFilter', 'Node', last.replace(/^\(\(\) => \{/, '').replace(/\}\)\(\);\s*$/, ''))(doc, Observer, { SHOW_TEXT: 4 }, { TEXT_NODE: 3 });
  assert.equal(text.data, 'Financial foundation');
  assert.equal(link.title, 'Canonical data foundation');
});

test('library table: the sorted column shows its direction; the others keep the two-way mark', () => {
  const page = runPage(d => d, [], m => m, { catalogue: [zedRun()] });
  Object.assign(page.libraryState, { sortKey: 'leverage', direction: 'desc' });
  const html = page.libraryResults({ runs: [zedRun()], rows: [zedRun()], skipped: new Set(), hidden: '' });
  assert.ok(html.includes('<th scope="col" aria-sort="descending"><button type="button" data-library-sort="leverage">Leverage <span aria-hidden="true">↓</span></button></th>'));
  assert.ok(html.includes('<th scope="col" aria-sort="none"><button type="button" data-library-sort="name">Issuer <span aria-hidden="true">↕</span></button></th>'));
  page.libraryState.direction = 'asc';
  assert.ok(page.libraryResults({ runs: [zedRun()], rows: [zedRun()], skipped: new Set(), hidden: '' }).includes('Leverage <span aria-hidden="true">↑</span>'));
});

// ---- Names, not codes (screens pass, 2026-11-10): no module code or methodology step id reaches a reader's screen. Register references (C9, G1, D1, GAP-001) stay.
// What a reader sees or hears of some markup: its text with each tag replaced by its title and aria-label values (href and data attributes are not read).
const readerText = html => html.replace(/<[^>]*>/g, tag => [...tag.matchAll(/ (?:title|aria-label)="([^"]*)"/g)].map(m => ` ${m[1]} `).join(' '));
const noCode = html => assert.ok(!/\bCP-[A-Z0-9]+\b/.test(readerText(html)), readerText(html).match(/.{0,40}\bCP-[A-Z0-9]+\b.{0,20}/)?.[0]);
const withInputs = modules => Object.fromEntries(Object.entries(modules).map(([id, entry]) => [id, { inputs: [], ...entry }]));

test('names, not codes: module heads, the Evidence tab and Built-from carry no module code in text, title or aria-label', () => {
  const page = runPage(d => { for (const out of Object.values(d)) Object.assign(out, { file: `${RUN}--deliveries--d1--${out.module}.md`, sha256: 'c'.repeat(64) }); return d; }, [zedReport(RUN)], withInputs);
  for (const id of Object.keys(runData())) page.modules[id] = { first: 'head' };
  const head = page.moduleHead({ module: 'CP-1', context: RUN, output: null });
  assert.ok(head.includes('<h2>Financial foundation</h2>') && !head.includes('title='));
  noCode(report().reportHead(OUT));
  const inventory = page.sourceInventory(RUN);
  assert.ok(inventory.includes('<h3>Financial foundation</h3>') && !inventory.includes('<h3>Financial foundation · CP-1'), 'the heading is the name only');
  assert.ok(inventory.includes('aria-label="Open output: Financial foundation"') && inventory.includes('aria-label="Download original handoff: Financial foundation"'));
  assert.ok(!inventory.includes('<p>CP-1</p>'), 'an output label equal to the module code is not shown');
  assert.ok(inventory.includes('<summary>File identity</summary><p>Financial foundation handoff</p><p class="hash">SHA-256 ' + 'c'.repeat(64)));
  noCode(inventory);
  const built = page.reportView(zedReport(RUN), RUN);
  assert.ok(/<th scope="row">Financial foundation<\/th><td>[^<]*<\/td><td><a href="[^"]*">Handoff<\/a><\/td>/.test(built));
  noCode(built);
  assert.equal(page.handoffLabel('deliveries/h/CP-1A.md'), 'Unnamed module handoff', 'a module no group names');
  assert.equal(page.handoffLabel('K.pdf'), 'K.pdf');
});

test('names, not codes: chips name their module, the handoff chip reads Handoff, titles from handoff text are named', () => {
  const r = report(), html = r.chipsMarkup(`${OUT}:16`) + r.chipsMarkup(`${OUT}:777`);
  noCode(html);
  assert.ok(html.includes('title="Handoff row, line 16" aria-label="Handoff row, line 16">Handoff<span class="dot row">'));
  assert.ok(!html.includes('class="av cp"') && !html.includes('class="av q"'), 'no code avatar');
  assert.ok(html.includes('<span class="av ">K</span>p.123'), 'an issuer-page chip keeps its source avatar');
  assert.ok(html.includes('title="Annual PDF marked alternate in Source readiness"'));
  assert.ok(html.includes('Unnamed module · D1'));
});

test('names, not codes: the band link, the evidence inspector and the library source details name the handoff', () => {
  assert.ok(report().reportBand(OUT).includes('title="Financial foundation handoff, line 13"'));
  const src = read('screen.js'), start = src.indexOf('function showInspector('), end = src.indexOf('function moduleBody(');
  const element = { hidden: true, classList: { add() {}, remove() {}, toggle() {} }, innerHTML: '' }, named = [];
  const r = report(), item = { module: 'CP-1', output: OUT, line: 54, title: 'Net sales', fields: [['Finding', 'Debt of CP-1A']], section: 'Financial summary' };
  const stored = { label: 'CP-1', file: 'run-a--deliveries--d1--CP-1.md', href: '../runs/run-a/deliveries/d1/CP-1.md', case: 'Zed & Sons · RUN-A' };
  const inspector = new Function('$', 'document', 'window', 'evidence', 'data', 'classification', 'esc', 'rich', 'icon', 'chipSection', 'unresolvedGap', 'nameCodes', 'moduleTitle', 'handoffLabel', 'returnTrigger',
    `${src.slice(start, end)}; return showInspector;`)(() => element, { querySelectorAll: () => [] }, { CREDIT_OS_DATA: { chips: {} } }, new Map([['k', item]]), { [OUT]: stored }, () => 'Not classified', v => String(v), v => String(v),
    n => `<i>${n}</i>`, () => '', () => false, (root, output, marks) => named.push([root, output, marks]), r.moduleTitle, r.handoffLabel, null);
  inspector('k');
  assert.ok(element.innerHTML.includes('>Financial foundation · Line 54<') && !element.innerHTML.includes('(CP-1)'));
  assert.ok(element.innerHTML.includes('Financial foundation handoff<br>Zed & Sons · RUN-A · saved output') && !element.innerHTML.includes('--CP-1.md'));
  assert.ok(element.innerHTML.includes('<a href="../runs/run-a/deliveries/d1/CP-1.md" download>'), 'the download link is unchanged');
  assert.deepEqual(named, [[element, OUT, false]], 'the inspector text is named, its register references left as they are');
  assert.ok(runPage().handoffLabel('runs/x/CP-0.md') === 'Source readiness handoff' && read('views.js').includes("`${handoffLabel(s.path)} · line ${s.line}`"));
});

test('names, not codes: a handoff code reads as its module name; a gap id as Gap n on its own page and elsewhere as the module\'s gap n', () => {
  const page = runPage(), name = text => page.namedText(text, null);
  assert.equal(name('Held by CP-6 and CP-6A; see CP-1.'), 'Held by Committee decision and Committee decision; see Financial foundation.');
  page.current.module = 'CP-6';
  assert.equal(name('CP-6-GAP-001 and CP-6A-GAP-012'), 'Gap 1 and Gap 12');
  page.current.module = 'CP-1';
  assert.equal(name('CP-6-GAP-001'), 'Committee decision gap 1');
  assert.equal(name('CP-2R and CP-2R-GAP-004'), 'unnamed module and unnamed module gap 4');
  assert.equal(name('C9 G1 D1 E1 AP3 GAP-001 EVT-01 K'), 'C9 G1 D1 E1 AP3 GAP-001 EVT-01 K', 'register references stay');
  assert.ok(read('screen.js').includes("groups.push(['Other modules',unnamed.map(id=>[id,'Unnamed module'])])") && page.moduleTitle('CP-NONE') === 'Unnamed module');
});

test('names, not codes: a step id becomes the step\'s own title, a range keeps its joining word, no title reads "a method step"', () => {
  const page = runPage(d => {
    d[outId('CP-1')].sections.push(sec('T1D.1 — Add-Back Register', 3, 70, 'reference', [text(71, 'x')]), ref('Steps', 80, [table(81, ['Step', 'Name', 'Role'], [[82, 'T4.1', 'Peer universe', 'a'], [83, 'T4.2', 'Peer metrics', 'b'], [84, 'T4.3', 'x'.repeat(90), 'c']])]));
    return d;
  }), id = outId('CP-1'), name = text => page.namedText(text, id);
  assert.equal(name('Use T1D.1 and T4.2.'), 'Use “Add-Back Register” and “Peer metrics”.', 'a title inside prose is quoted');
  assert.equal(name('See T4.2 for facility access'), 'See “Peer metrics” for facility access');
  assert.equal(name('Gap noted: T4.1 — x'), 'Gap noted: “Peer universe” — x', 'an id is dropped only at the start of the text');
  assert.equal(name('T4.2'), 'Peer metrics', 'no quotes when the id is the whole text');
  assert.equal(name('(T1.1–T1.4, T6.2, T8.1; P3/P5)'), '(method steps; P3/P5)', 'a run of untitled ids is one phrase');
  assert.equal(name('T5.1/T7.2 readiness and T5.3 and T9.1'), 'method steps readiness and method steps');
  assert.equal(name('T9.9 stands'), 'a method step stands');
  assert.equal(name('T4.D1 — Discovery source register / bounded attempt'), 'Discovery source register / bounded attempt', 'a lettered id leading its text is dropped whole');
  assert.equal(name('T2G.* remain registered; T4.D1.'), 'a method step remain registered; a method step.', 'a lettered or wildcard id is one id');
  assert.equal(name('T4.1–T4.2'), 'Peer universe to Peer metrics');
  assert.equal(name('T4.1 through T4.2'), 'Peer universe through Peer metrics');
  assert.equal(name('Guidance retained in T9.9; T4.3 is long'), 'Guidance retained in method steps is long', 'unknown ids and descriptions are no titles');
  assert.equal(name('T1D.1 — Add-Back Register'), 'Add-Back Register', 'an id leading its own title is dropped');
  assert.equal(page.namedText('T4.1', null), 'a method step');
  const nullChip = report().chipsMarkup(`${OUT}:16`);
  assert.ok(nullChip.includes('>Financial foundation · D1 · D3<'), 'a chip with no module names the row\'s own');
});

test('names, not codes: a table column of bare step ids is not drawn; a heading or caption loses its leading id and keeps no title', () => {
  const steps = ref('T4.11 — Cumulative gaps', 20, [table(22, ['Step', 'Name', 'Mixed'], [[23, 'T4.1', 'Peer universe', 'T4.1'], [24, 'T4.2', 'Peer metrics', 'n.a.']])]);
  const html = report({ sections: [steps] }, [['reg', 'T4.11 — Cumulative gaps', ['T4.11']]]).reportReference(OUT);
  assert.ok(!html.includes('>Step<') && !html.includes('<td>T4.2</td>') && !html.includes('<td>Peer metrics</td><td>T4.2'), 'the step column is gone, header and cells');
  assert.ok(html.includes('>Name<') && html.includes('>Peer universe<') && html.includes('>Mixed<') && html.includes('<td>T4.1</td>'), 'a column that is not all step ids stays (the screen then names the id)');
  assert.ok(html.includes('<caption class="sr-only">Cumulative gaps</caption>') && html.includes('<h4>Cumulative gaps</h4>') && !/title="T4\.11/.test(html));
});

// nameCodes over a minimal DOM: text nodes with a parent that knows which zones it sits in, and elements with title and aria-label.
function nameCodesIn(texts, elements = [], zone = '') {
  const src = read('screen.js'), body = src.slice(src.indexOf('const REFERENCE='), src.indexOf('for (const [id, output]'));
  const nodes = texts.map(data => ({ data, parentElement: { closest: selector => (selector.includes(zone) && zone ? {} : null) }, replaceWith(fragment) { this.fragment = fragment; } }));
  let at = -1;
  const document = { createTreeWalker: () => ({ currentNode: null, nextNode() { this.currentNode = nodes[++at]; return Boolean(this.currentNode); } }), createDocumentFragment: () => ({ parts: [], append(...p) { this.parts.push(...p); } }), createElement: () => ({}) };
  const page = runPage();
  page.current.module = 'CP-1';
  new Function('document', 'NodeFilter', 'namedText', 'current', `${body}; nameCodes({querySelectorAll: () => arguments[4]});`)(document, { SHOW_TEXT: 4 }, page.namedText, { output: null }, elements);
  return nodes;
}
test('names, not codes: nameCodes names an audit section, the Evidence tab and attributes; only [FKCS] references keep a mark', () => {
  for (const zone of ['details.audit', '.built-from', '.hash', '.chip', '.coverage', '.module-head .sub']) {
    assert.equal(nameCodesIn(['Held by CP-6 (CP-0 line 34)'], [], zone)[0].data, 'Held by Committee decision (Source readiness line 34)', `${zone} is not left alone`);
  }
  const attributes = { title: 'CP-0', 'aria-label': 'K, page:164 / CP-1: sales' }, element = { getAttribute: name => attributes[name] ?? null, setAttribute: (name, value) => { attributes[name] = value; } };
  nameCodesIn(['x'], [element]);
  assert.deepEqual(attributes, { title: 'Source readiness', 'aria-label': 'K, page:164 / Financial foundation: sales' });
  const [marked, chip] = [nameCodesIn(['Row F12 and CP-1'])[0], nameCodesIn(['Row F12 and CP-1'], [], '.chip')[0]];
  assert.deepEqual(marked.fragment.parts.map(p => p.textContent ?? p), ['Row ', 'F12', ' and Financial foundation']);
  assert.equal(chip.data, 'Row F12 and Financial foundation', 'a chip takes the name and keeps its reference as text');
  const screen = read('screen.js');
  assert.ok(!screen.includes('showsCodes') && !screen.includes('module-ref') && !/closest\('[^']*details\.audit/.test(screen));
  assert.ok(screen.includes('Retained fields from this historical run, with module codes and method step ids shown as names.') && !screen.includes('exact retained fields'));
  assert.ok(/function nameCodes[^]*?nameCodes\(\$\('search-results'\),null,false\)/.test(screen), 'search hits borrow no step title');
  assert.ok(/updateLibrary\([^]*?nameCodes\(\$\(id\)\)/.test(read('views.js')), 'a redrawn library is named');
  assert.ok(/function openAuditSection[^]*?body\.innerHTML=sectionView\([^;]*;nameCodes\(body\);/.test(screen), 'an audit section is named when it is drawn');
});

test('embedded report: codes are named in text, title and aria-label, the banners included', () => {
  const src = read('report-adapter.js'), last = src.slice(src.lastIndexOf('(() => {'));
  const text = { nodeType: 3, data: 'Annual report is later. (CP-0 line 34); CP-6-GAP-002 and CP-2R-GAP-001 and CP-2R; see CP-1.md, CP-0-a.md, CP-4_RUNBOOK.md, T4.D1, T2G.* and T5.1/T7.2, T9.1; T2 and T1.' };
  const attributes = { title: 'CP-1', 'aria-label': 'K, page:164 / CP-1: sales 3,809' };
  const element = { getAttribute: name => attributes[name] ?? null, setAttribute: (name, value) => { attributes[name] = value; } };
  const root = { querySelectorAll: selector => (selector === '.module-link' ? [] : [element]) };
  let selected = '';
  const doc = { querySelectorAll: selector => { selected = selector; return [root]; }, createTreeWalker: () => { let done = false; return { currentNode: text, nextNode: () => !done && (done = true) }; } };
  class Observer { observe() {} }
  new Function('document', 'MutationObserver', 'NodeFilter', 'Node', last.replace(/^\(\(\) => \{/, '').replace(/\}\)\(\);\s*$/, ''))(doc, Observer, { SHOW_TEXT: 4 }, { TEXT_NODE: 3 });
  assert.ok(selected.split(',').includes('#inspector-content'), 'the report\'s own inspector is named too');
  assert.ok(selected.split(',').includes('.banner'), 'the delivery banners are named too: they sit outside the view the pass observed');
  assert.equal(text.data, 'Annual report is later. (Source readiness line 34); Committee decision gap 2 and unnamed module gap 1 and unnamed module; see Financial foundation handoff, Source readiness handoff (a), Legal & covenants runbook, method steps; T2 and T1.');
  assert.deepEqual(attributes, { title: 'Financial foundation', 'aria-label': 'K, page:164 / Financial foundation: sales 3,809' });
});

test('names, not codes: a bare T<n> is ordinary text; the dot makes a step id; sub-rows, semicolons, ranges, files and runbooks read right', () => {
  const page = runPage(d => {
    d[outId('CP-1')].sections.push(ref('Steps', 80, [table(81, ['Step', 'Name'], [[82, 'T2E.2', 'Beginning register'], [83, 'T2E.4', 'Cash uses'], [84, 'T2E.3.r01', 'x']])]));
    return d;
  }), id = outId('CP-1'), name = text => page.namedText(text, id);
  for (const plainText of ['T2 Biosystems', 'Tier 2 (T2) notes', 'T12M EBITDA', 'Chiffre d’affaires T1 2025', 'T1 Energy and T3M price', 'T+1 settlement']) assert.equal(name(plainText), plainText);
  assert.equal(name('T2E.3.r01 and T9.9'), 'x and a method step', 'a sub-row id is one id, with its own title');
  assert.equal(name('T9.1; T9.2; T9.3 limits'), 'method steps limits');
  assert.equal(name('See T2E.2–T2E.4, T9.9 here'), 'See “Beginning register” to “Cash uses”, a method step here', 'an en dash reads "to" inside a longer run');
  assert.equal(name('T2E.2–T2E.4'), 'Beginning register to Cash uses');
  assert.equal(page.namedText('CP-0-a.md and CP-4_RUNBOOK.md and CP-1.md', null), 'Source readiness handoff (a) and unnamed module runbook and Financial foundation handoff');
  assert.equal(page.handoffLabel('r--deliveries--h--CP-0-a.md'), 'Source readiness handoff (a)');
  const files = page.reportView({ ...zedReport(RUN), files: [{ href: 'x/CP-1.md', name: 'CP-1.md' }, { href: 'x/report.json', name: 'report.json' }] }, RUN);
  assert.ok(files.includes('>Financial foundation handoff</a>') && files.includes('>report.json</a>') && !files.includes('>CP-1.md<'));
  const screen = read('screen.js'), adapter = read('report-adapter.js');
  assert.ok(screen.includes("parent.closest('.ref,.excerpt')"), 'a source excerpt is the issuer\'s text, as quoted');
  assert.ok(adapter.includes('"CP-MODEL":"Forecast"'), 'the app\'s word for the model');
});

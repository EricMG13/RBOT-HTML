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
const table = (line, headers, rows) => ({ type: 'table', line, headers, rows: rows.map(([n, ...cells]) => ({ line: n, cells })) });
const text = (line, body) => ({ type: 'text', line, text: body });
// `where` is the placement the store would give the section (Task 1); report() turns it into the output's parallel `placement` list.
const sec = (heading, level, line, where, blocks) => ({ heading, level, line, where, blocks });
const ref = (heading, line, blocks) => sec(heading, 3, line, 'reference', blocks);
const view = (heading, line, blocks) => sec(heading, 3, line, 'view', blocks);
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
    summary: { bottomLine: 'Cash up.', confidence: 'Medium', limitation: 'Synthetic.', line: 13 }, charts: [{ title: 'Leverage', unit: 'x', table: 42, columns: [1] }], ...overrides };
  const data = { [OUT]: out };
  const modules = { [OUT]: { sections: modSections || DEFAULT_MODULES } };
  const evidence = new Map();
  for (const s of out.sections) for (const b of s.blocks) {
    if (b.type === 'table') for (const r of b.rows) evidence.set(`${OUT}:${r.line}`, { module: 'CP-1', line: r.line });
    else evidence.set(`${OUT}:${b.line}`, { module: 'CP-1', line: b.line });
  }
  const win = { CREDIT_OS_DATA: { chips: CHIPS }, DESIGN_CATALOGUE: { real: [{ id: 'run-a', checklist: null }] }, DESIGN_WORKSPACE: { reports: [] } };
  const sectionData = (id, sid) => out.sections.filter(s => modules[id].sections.find(x => x[0] === sid)[2].some(p => s.heading.startsWith(p)));
  const names = ['window', 'data', 'modules', 'contexts', 'store', 'moduleNames', 'esc', 'plain', 'rich', 'icon', 'pins', 'evidence', 'current', 'isAnalytical', 'sectionData', 'lastFile'];
  const args = [win, data, modules, { 'run-a': { folder: 'run-a', modules: { 'CP-1': { outputs: [OUT], default: OUT } } } }, {}, { 'CP-1': 'Financial foundation' }, esc, plain, rich, n => `<img src="icons/${n}.svg">`, {}, evidence, { context: 'run-a', section: 'head' }, id => !id.startsWith('W-'), sectionData, new Map()];
  return new Function(...names, `${src}; return {moduleReport, reportParts, reportAnalysis, reportReference, reportCalculations, reportHead, chipsMarkup, chipView, keyNumbers, reportLimits, reportAudit, reportBand, outlineMarkup, navigationSections, drawnAnchors, availability, unavailableView, REPORT_PARTS, METHOD_CODE};`)(...args);
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
  assert.ok(html.includes('Candidate · not accepted') && html.includes('Current methodology') && html.includes('<code>CP-1.md</code> · 10 sections'));
  assert.ok(html.includes('Quoted from the handoff') && html.includes('CP-1.md · line 13'));
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

test('(g) a leading method code is dropped from a displayed heading and kept in title', () => {
  const sections = ['T2F.1 — Macro source gate', 'cp2b.cp_model_catalysts — blocked interface', 'TDR.1 — Research brief', 'Net debt — bridge'].map((h, i) => view(h, 100 + 10 * i, [text(101 + 10 * i, 'x')]));
  const html = report({ sections }).reportAnalysis(OUT);
  assert.ok(html.includes('<h4 title="T2F.1 — Macro source gate">Macro source gate</h4>'));
  assert.ok(html.includes('<h4 title="cp2b.cp_model_catalysts — blocked interface">blocked interface</h4>'));
  assert.ok(html.includes('<h4 title="TDR.1 — Research brief">Research brief</h4>'));
  assert.ok(html.includes('<h4>Net debt — bridge</h4>'));
  assert.equal(report().METHOD_CODE.source, '^([A-Z][A-Z0-9]*\\.[A-Z]?\\d+|[a-z0-9]+(\\.[a-z0-9_]+)+)\\s+—\\s+');
  // The code goes from Limits, Reference and Calculations headings too, and stays in the audit list.
  const coded = [sec('C.1 — Gap list', 2, 100, 'limits', [text(101, 'g')]), ref('T4.D1 — Register', 110, [table(111, ['A', 'B'], [[112, 'x', 'y']])]), sec('T2F.2 — Trace', 3, 120, 'calculations', [text(121, 'c')]), sec('T3D.1 — Source map', 3, 130, 'audit', [text(131, 'a')])];
  const r = report({ sections: coded }, [['gap', 'C.1 — Gap list', ['C.1']], ['reg', 'T4.D1 — Register', ['T4.D1']], ['trace', 'T2F.2 — Trace', ['T2F.2']], ['map', 'T3D.1 — Source map', ['T3D.1']]]);
  assert.ok(r.reportLimits(OUT).includes('<h4 title="C.1 — Gap list">Gap list</h4>'));
  assert.ok(r.reportReference(OUT).includes('<h4 title="T4.D1 — Register">Register</h4>'));
  assert.ok(r.reportCalculations(OUT).includes('<h4 title="T2F.2 — Trace">Trace</h4>'));
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
  assert.ok(blocked.includes('<span class="badge badge-gray">Blocked</span>') && blocked.includes('Candidate · not accepted'));
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
  assert.deepEqual(chips, ['|C1|L16|', '|K|p.123|', '|M|p.70–71|', '|A|CP-1A · E2|', '|C1|D1 · D3|']);
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
  assert.ok(rows[0].includes('<strong>6.57</strong>') && rows[0].includes('class="chips"') && rows[0].includes('</span>p.123<span'));
  for (const row of rows) assert.match(row, /<strong>[^<]+<\/strong>/);
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
  assert.ok(/\.panel-card \.chart-open\{display:grid/.test(css));
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

test('the head and the audit summary give the store\'s one section count', () => {
  const sections = [...SECTIONS, sec('Empty', 2, 70, 'audit', []), sec('Also empty', 2, 72, 'audit', [])];
  const html = report({ sections }).moduleReport(OUT);
  assert.equal(sections.length, 12);
  assert.ok(html.includes('<code>CP-1.md</code> · 12 sections'));
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

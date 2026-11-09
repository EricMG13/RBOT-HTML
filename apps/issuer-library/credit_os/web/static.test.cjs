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
const SECTIONS = [
  { heading: 'Reader summary', line: 10, blocks: [
    table(12, ['Bottom line', 'Confidence', 'Main limitation'], [[13, 'Cash up.', 'Medium', 'Synthetic.']]),
    table(15, ['Finding', 'Creditor impact', 'Confidence'], [[16, 'Leverage rose.', 'Higher gross leverage.', 'High'], [17, 'Cash rose.', 'More cushion.', 'Medium']]),
  ] },
  { heading: 'Liquidity table', line: 20, blocks: [
    table(22, ['Measure', 'FY2023', 'FY2024', 'Unit', 'Note', 'Extra1', 'Extra2'], [
      [23, 'Cash', '3,472', '6,261', 'US$m', 'a very long note that is longer than twenty-four characters', 'e1', 'e2'],
      [24, 'Coupons', 'Not supplied', '', 'US$m', 'x', 'e1', 'e2'], [25, 'A', '1', '2', 'US$m', 'x', 'e1', 'e2'], [26, 'B', '1', '2', 'US$m', 'x', 'e1', 'e2'],
      [27, 'C', '1', '2', 'US$m', 'x', 'e1', 'e2'], [28, 'D', '1', '2', 'US$m', 'x', 'e1', 'e2'], [29, 'E', '1', '2', 'US$m', 'x', 'e1', 'e2'], [30, 'F', '1', '2', 'US$m', 'x', 'e1', 'e2'], [31, 'G', '1', '2', 'US$m', 'x', 'e1', 'e2'],
    ]),
  ] },
  { heading: 'Chart data: leverage', line: 40, blocks: [table(42, ['Period', 'Total debt / EBITDA', 'Reporting unit', 'Basis'], [[43, 'FY2024', '6.57', 'x', 'K, page:123'], [44, 'FY2023', '', 'x', 'none']])] },
  { heading: 'Gaps', line: 50, blocks: [{ type: 'text', line: 52, text: 'Coupons are **not supplied**.' }] },
  { heading: 'Sources', line: 60, blocks: [{ type: 'text', line: 62, text: 'K.' }] },
];
const CHIPS = {
  [`${OUT}:16`]: [
    { kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 123, page_end: null, quote: '6.57', quote_found: true, excerpt: 'Debt 6.57 times', reason: null, hash_matches_inventory: true },
    { kind: 'issuer_page', source: 'M', file: 'M.jsonl', page: 70, page_end: 71, hash_matches_inventory: null, quote_found: null, excerpt: null },
    { kind: 'upstream', module: 'CP-1A', codes: ['E2'] },
    { kind: 'upstream', module: null, codes: ['D1', 'D3'] },
  ],
  [`${OUT}:43`]: [{ kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 123, page_end: null }],
  [`${OUT}:52`]: [{ kind: 'gap', label: 'Not supplied', reason: 'the row says so', codes: [] }, { kind: 'gap', label: 'no page', codes: [] }, { kind: 'gap', label: 'p.145 · no key', codes: [] }],
};
function report(overrides = {}, modSections = null) {
  const text = read('views.js');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const plain = v => String(v).replace(/\*\*|`/g, '');
  const rich = v => esc(v).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  const out = { module: 'CP-1', run: 'run-a', source: 'deliveries/d1/CP-1.md', href: '../runs/run-a/deliveries/d1/CP-1.md', label: 'CP-1', sections: SECTIONS,
    summary: { bottomLine: 'Cash up.', confidence: 'Medium', limitation: 'Synthetic.', line: 13 }, charts: [{ title: 'Leverage', unit: 'x', table: 42, columns: [1] }], ...overrides };
  const data = { [OUT]: out };
  const modules = { [OUT]: { sections: modSections || [['liquidity', 'Liquidity table', ['Liquidity table']], ['leverage', 'Chart data', ['Chart data']], ['gaps', 'Gaps & limitations', ['Gaps']], ['sources', 'Sources', ['Sources']], ['audit', 'Technical audit', ['Request']]] } };
  const evidence = new Map();
  for (const s of SECTIONS) for (const b of s.blocks) {
    if (b.type === 'table') for (const r of b.rows) evidence.set(`${OUT}:${r.line}`, { module: 'CP-1', line: r.line });
    else evidence.set(`${OUT}:${b.line}`, { module: 'CP-1', line: b.line });
  }
  const win = { CREDIT_OS_DATA: { chips: CHIPS }, DESIGN_CATALOGUE: { real: [{ id: 'run-a', checklist: null }] }, DESIGN_WORKSPACE: { reports: [] } };
  const sectionData = (id, sid) => out.sections.filter(s => modules[id].sections.find(x => x[0] === sid)[2].some(p => s.heading.startsWith(p)));
  const names = ['window', 'data', 'modules', 'contexts', 'store', 'moduleNames', 'esc', 'plain', 'rich', 'icon', 'pins', 'evidence', 'current', 'isAnalytical', 'sectionData', 'lastFile'];
  const args = [win, data, modules, { 'run-a': { folder: 'run-a', modules: { 'CP-1': { outputs: [OUT], default: OUT } } } }, {}, { 'CP-1': 'Financial foundation' }, esc, plain, rich, n => `<img src="icons/${n}.svg">`, {}, evidence, { context: 'run-a', section: 'head' }, id => !id.startsWith('W-'), sectionData, new Map()];
  return new Function(...names, `${text}; return {moduleReport, chipsMarkup, chipView, keyNumbers, reportLimits, reportAudit, reportBand, outlineMarkup, availability, unavailableView};`)(...args);
}

test('the module report has the six anchors, in order', () => {
  const html = report().moduleReport(OUT);
  const ids = [...html.matchAll(/\bid="(head|bottom-line|numbers|findings|limits|audit)"/g)].map(m => m[1]);
  assert.deepEqual(ids, ['head', 'bottom-line', 'numbers', 'findings', 'limits', 'audit']);
  assert.ok(html.includes('Candidate · not accepted') && html.includes('Current methodology') && html.includes('<code>CP-1.md</code> · 5 sections'));
  assert.ok(html.includes('Quoted from the handoff') && html.includes('CP-1.md · line 13'));
});

test('an empty part keeps its anchor and says so once', () => {
  const html = report({ summary: null, call: null, charts: [], sections: [] }).moduleReport(OUT);
  const ids = [...html.matchAll(/\bid="(head|bottom-line|numbers|findings|limits|audit)"/g)].map(m => m[1]);
  assert.deepEqual(ids, ['head', 'bottom-line', 'numbers', 'findings', 'limits', 'audit']);
  assert.ok(html.includes('No bottom line in this handoff.'));
});

test('chip labels and avatars follow the data, one chip per dict', () => {
  const { chipsMarkup } = report();
  const html = chipsMarkup(`${OUT}:16`);
  const chips = [...html.matchAll(/<button[^>]*class="chip[^"]*"[^>]*>.*?<\/button>/g)].map(m => m[0].replace(/<[^>]+>/g, '|').replace(/\|+/g, '|'));
  assert.deepEqual(chips, ['|C1|L16|', '|K|p.123|', '|M|p.70–71|', '|A|CP-1A · E2|', '|C1|D1 · D3|']);
  assert.ok(html.includes('data-chip="run-a/deliveries/d1/CP-1.md:16" data-index="3"') && html.includes('data-evidence="run-a/deliveries/d1/CP-1.md:16"'));
});

test('gap chips read Not supplied, no page, or the build label, and are dashed', () => {
  const html = report().chipsMarkup(`${OUT}:52`);
  for (const label of ['Not supplied', 'no page', 'p.145 · no key']) assert.ok(html.includes(`</span>${label}<span`), label);
  assert.equal(html.match(/class="chip gap"/g).length, 3);
  assert.ok(html.includes('<span class="av gap">?</span>') && html.includes('title="the row says so"'));
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
  assert.ok(html.includes('1 more rows are under Evidence &amp; audit.'));
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

test('limits come from the Limits group with chips; audit lists the rest by line', () => {
  const r = report();
  const limits = r.reportLimits(OUT);
  assert.ok(limits.includes('Coupons are <strong>not supplied</strong>.') && limits.includes('Not supplied'));
  const audit = r.reportAudit(OUT);
  assert.ok(audit.includes('<span>L20</span>') && audit.includes('<span>L60</span>') && !audit.includes('Gaps &amp; limitations'));
  assert.ok(audit.includes('<details class="audit" id="audit">') && audit.includes('hidden'));
});

test('the outline is the six anchors under On this page', () => {
  const html = report().outlineMarkup(OUT);
  assert.equal(html.match(/class="section-item"/g).length, 6);
  assert.ok(html.includes('aria-label="On this page"') && html.includes('aria-current="location"'));
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

test('key numbers read the analysis group whatever its name (CP-2E: Rates, FX & hedges)', () => {
  // Answer key from the fixture: the T2F section groups under 'Rates, FX & hedges' for CP-2E, its first non-limits group.
  const sections = [{ heading: 'T2F.4 Hedge register', line: 70, blocks: [table(72, ['Instrument', 'Amount', 'Margin / Coupon'], [[73, 'Swap', '500', '3.1'], [74, 'Collar', '250', '2.4']])] }];
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

test('key numbers look past the first analysis group (CP-2E: numeric register in the second group)', () => {
  // Answer key from the fixture: T2G.1 (first group) holds only a text table; the T2F.4 register in the second group is the one shown.
  const sections = [
    { heading: 'T2G.1 ESG notes', line: 60, blocks: [table(62, ['Topic', 'View'], [[63, 'Governance', 'Stable']])] },
    { heading: 'T2F.4 Hedge register', line: 70, blocks: [table(72, ['Instrument', 'Amount', 'Margin / Coupon'], [[73, 'Swap', '500', '3.1']])] },
  ];
  const html = report({ module: 'CP-2E', sections }, [['esg', 'ESG notes', ['T2G.1']], ['hedges', 'Hedge register', ['T2F.4']]]).keyNumbers(OUT);
  assert.ok(html.includes('>Amount<') && html.includes('>500<') && !html.includes('>Governance<'));
});

// ---- The hedge chart: views.js evaluated over a hand-written CP-2E table and a run whose as-of is 2024-09-30.
function hedgeHtml(headers, rows, asOf = '2024-09-30') {
  const text = read('views.js');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const id = 'run-a/deliveries/d1/CP-2E.md';
  const out = { module: 'CP-2E', run: 'run-a', period: '', sections: [{ heading: 'T2F.4', line: 1, blocks: [table(80, headers, rows)] }] };
  const names = ['data', 'contexts', 'esc', 'rich', 'plain', 'evidence', 'modules', 'moduleNames', 'current', 'icon', 'window', 'store', 'pins', 'lastFile', 'isAnalytical', 'sectionData'];
  const fn = new Function(...names, `${text}; return hedgeChart;`)({ [id]: out }, { 'run-a': { asOf } }, esc, esc, esc, new Map(), {}, {}, {}, () => '', { CREDIT_OS_DATA: { chips: {} } }, {}, {}, new Map(), () => true, () => []);
  return fn(id, { kind: 'hedges', table: 80, title: 'Hedges', unit: null });
}
const HEDGE_ROWS = [
  [81, 'Swap', '500', '2022-12-31 to 2025-06-30', 'USDm'],
  [82, 'Cap', '250', '2025-01-31 to 2028-03-31', 'EURm'],
  [83, 'FX forwards', '90', 'Up to 12 months', ''],
];
const leftOf = (html, cls) => [...html.matchAll(new RegExp(`class="${cls}[^"]*" style="left:([\\d.]+)%(?:;width:([\\d.]+)%)?`, 'g'))].map(m => [Number(m[1]), m[2] === undefined ? null : Number(m[2])]);

test('hedge chart axis, base rule, forward flag and units come from the table and the as-of', () => {
  // Hand-computed: start 2022-12-31 (earlier than as-of minus 18 months), end 2028-03-31 (later than as-of plus 36 months); 1917 days.
  // As-of 2024-09-30 is day 639 (1/3); Swap spans days 0-912; Cap starts day 762.
  const html = hedgeHtml(['Instrument', 'Amount', 'Window', 'Unit'], HEDGE_ROWS);
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

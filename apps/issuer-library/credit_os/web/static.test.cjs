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

test('the rail is Start a run, Issuer library, Run activity, Search: no Reports entry (ruling decision 12)', () => {
  const html = read('index.html');
  const rail = html.slice(html.indexOf('<aside class="rail"'), html.indexOf('</aside>'));
  assert.deepEqual([...rail.matchAll(/data-place="([^"]+)"/g)].map(m => m[1]), ['Start a run', 'Issuer library', 'Run activity', 'Search']);
  assert.ok(!/Reports|W-Reports/.test(html));
});

test('the issuer tabs are Report, Overview, Changes, Modules, Forecast, Evidence; no Calendar or Reports tab and no report frame or adapter remains (decisions 1, 12)', () => {
  const views = read('views.js');
  const tabs = views.slice(views.indexOf("querySelector('.workspace-tabs').innerHTML=["), views.indexOf(".map(([id,label])"));
  assert.deepEqual([...tabs.matchAll(/\[(?:'[^']+'|moduleId),'([^']+)'\]/g)].map(m => m[1]), ['Report', 'Overview', 'Changes', 'Modules', 'Forecast', 'Evidence']);
  for (const name of fs.readdirSync(__dirname).filter(f => /\.(js|css|html)$/.test(f))) {
    const text = read(name);
    for (const gone of ['report-adapter', 'report-preview', 'report-workspace', 'report-content', 'cancelReportFrame', 'isReportRoute', 'reportList', 'reportView', 'reportManifest', 'runReports', 'calendarSections']) {
      assert.ok(!text.includes(gone), `${name} still contains ${gone}`);
    }
  }
  // The retired Calendar and Reports hashes are named once, where the old routes are redirected.
  const named = fs.readdirSync(__dirname).filter(f => /\.(js|css|html)$/.test(f) && !f.endsWith('.test.cjs')).filter(f => read(f).includes('W-Calendar') || read(f).includes('W-Reports'));
  assert.deepEqual(named, ['screen.js']);
  assert.ok(!fs.existsSync(path.join(__dirname, 'report-adapter.js')) && !fs.existsSync(path.join(__dirname, 'report-adapter.css')));
});

test('an old Calendar or Reports hash opens the run\'s Report history, or the library when no run is known', () => {
  const screen = read('screen.js');
  assert.ok(screen.includes("if(requestedModule==='W-Calendar'||requestedModule==='W-Reports'){requestedModule='W-Report';requestedSection='history';}"));
  assert.ok(screen.includes("if(!context&&!appDestinations.has(module))module='W-Library';"), 'a run page with no run known is the library');
});

test('the rail opens the run start page first, hidden until the library is served', () => {
  const html = read('index.html');
  const entry = html.match(/<a [^>]*data-place="Start a run"[^>]*>.*?<\/a>/);
  assert.ok(entry, 'the rail has a Start a run entry');
  assert.ok(/\shref="\/"/.test(entry[0]), 'it goes to the service root');
  assert.ok(/\shidden[\s>]/.test(entry[0]), 'it is hidden when the page is opened from disk');
  assert.ok(entry[0].includes('<span class="rail-label">Start a run</span>'));
  assert.ok(html.indexOf('data-place="Start a run"') < html.indexOf('data-place="Issuer library"'), 'it comes first');
  const views = read('views.js');
  assert.ok(/rail\('Start a run'\)\.hidden\s*=\s*!servedOverHttp\(\)/.test(views), 'views.js shows it only when served');
  assert.ok(views.includes(".rail a[data-place]:not([data-place=\"Start a run\"])"), 'the active-place code leaves it alone');
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

test('the Evidence workspace tab lands on the Summary tab; the old sources route stays a deep link', () => {
  const text = read('views.js');
  assert.ok(text.includes("'W-Evidence':['Evidence',[['summary','Evidence',[]]]]") && text.includes("if(module==='W-Evidence')return [['summary','Evidence',[]]];"));
  const {parseHash} = require('./evidence.js');
  assert.equal(parseHash('#W-Evidence/summary?c=r', []).tab, 'summary');
  assert.equal(parseHash('#W-Evidence/sources?c=r', []).tab, 'sources');
});

test('installDestinations keys are exactly the library and issuer pages plus Run activity', () => {
  const text = read('views.js');
  const start = text.indexOf('const destinations={');
  assert.ok(start >= 0, 'destinations table not found');
  const end = text.indexOf('};', start);
  const keys = [...text.slice(start, end).matchAll(/^\s*'([^']+)':\[/gm)].map(m => m[1]);
  assert.deepEqual(keys, ['W-Library', 'W-Report', 'W-Overview', 'W-Changes', 'W-Evidence', 'W-Forecast', 'CP-OS']);
  const row = text.slice(text.indexOf("'CP-OS':["), end);
  assert.deepEqual([...row.matchAll(/\['([^']+)','[^']*',\[\]\]/g)].map(m => m[1]), ['activity']);
});

// Pull the pure activityView and libraryNotShown out of views.js and run them with a stand-in esc and icon.
const esc = v => String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const viewsPart = (from, to, returns) => {
  const text = read('views.js');
  const start = text.indexOf(from), end = text.indexOf(to);
  assert.ok(start >= 0 && end > start, `${from} not found`);
  return new Function('esc', 'icon', 'window', `${text.slice(start, end)}; return ${returns};`)(esc, n => `<img src="icons/${n}.svg">`, { Components: require('./components.js') });
};
const activityView = () => viewsPart('// Run activity (ruling decision 10)', 'function workspaceView(', 'activityView');
const libraryNotShown = () => viewsPart('function libraryNotShown(', 'function libraryView(', 'libraryNotShown');

// The Evidence page: views.js gathers the run's data and evidence.js draws it. The helper runs the real slice of views.js and the real evidence.js
// for one tab (and module filter) of the route.
const evidenceView = (contexts, data = {}) => {
  const text = read('views.js');
  const start = text.indexOf('// ---- Evidence (ruling decisions 9, 10'), end = text.indexOf('function workspaceView(');
  assert.ok(start >= 0 && end > start, 'evidence view not found');
  const names = { 'CP-0': 'Source readiness', 'CP-1': 'Financial foundation', 'CP-1A': 'Business & governance' };
  const route = {}, win = { Evidence: require('./evidence.js'), CREDIT_OS_DATA: { chips: {} } };
  const view = new Function('esc', 'icon', 'moduleTitle', 'handoffLabel', 'contexts', 'data', 'current', 'window', 'ChangesView', 'runModels', 'MODEL_ENTRY', 'SOURCE_ROLES', 'sourceFile', 'modelOptionLabels', `${text.slice(start, end)}; return evidenceView;`)(esc, n => `<i>${n}</i>`, c => names[c] || c, runPage().handoffLabel, contexts, data, route, win, require('./changes.js'), () => [], ['CP-MODEL', 'Cash flow model'], { annual: 'Annual handoff' }, s => (s.output || s.path || '').split('/').at(-1), () => []);
  return (key, tab = 'sources', module = null) => { Object.assign(route, { tab, evidenceModule: module }); return view(key); };
};
const EVIDENCE = {
  sources: [{ name: 'A <report>.pdf', sha256: 'a'.repeat(64), type: 'pdf', documentDate: null, readBy: ['CP-0', 'CP-1'] }],
  unrecorded: [], noSourcesModules: [],
  unused: [{ name: 'C_unread.htm.jsonl', sha256: 'c'.repeat(64), type: 'htm.jsonl', documentDate: null, readBy: [] }],
  handoffs: [{ module: 'CP-0', name: 'CP-0.md', href: '../runs/r/CP-0.md?sha256=1' }, { module: 'CP-1', name: 'CP-1.md', href: '../runs/r/CP-1.md?sha256=2' }],
  zip: 'downloads/r/handoffs.zip',
  downloads: [{ label: 'Model m', href: '/files/m.html' }],
  record: { hashes: [{ name: 'delivery-x.json', sha256: 'd'.repeat(64) }, { name: 'CP-1.md', sha256: '1'.repeat(64) }, { name: 'instructions/CP-0.md', sha256: '2'.repeat(64) }, { name: 'r--deliveries--d--CP-1-a.md', sha256: '3'.repeat(64) }], instructions: [{ module: 'CP-0', href: '../runs/r/instructions/CP-0.md', sha256: 'e'.repeat(64) }],
    calls: [{ module: 'CP-0', attempt: 0, started: '2026-11-09T15:13:51Z', http_status: 200, error_class: null, settled_usd: '0.00941950' }], cap: '12' },
};

const TWO_MODULES = { 'CP-0': { outputs: [], default: null }, 'CP-1': { outputs: [], default: null } };
const evidencePage = (ev, tab, extra = {}) => evidenceView({ r: { evidence: ev, modules: TWO_MODULES, ...extra } })('r', tab);

test('Evidence (library redesign): the Sources tab lists files as cards, then the unused ones; the foot and the Run record tab follow the same four lists', () => {
  const html = evidencePage(EVIDENCE, 'sources');
  const card = /<article class="ev-card ev-src"[^>]*>.*?<\/article>/s.exec(html)[0];
  assert.ok(card.includes('A &lt;report&gt;.pdf') && card.includes('>pdf<') && card.includes('Not recorded'), 'name escaped, type, a date the run does not record');
  assert.deepEqual([...card.matchAll(/aria-label="([^"]+)"/g)].map(m => m[1]).slice(0, 2), ['Source readiness', 'Financial foundation'], 'who read it, by name');
  assert.ok(html.indexOf('Supplied, not used') > html.indexOf('A &lt;report&gt;.pdf') && html.includes('C_unread.htm.jsonl'));
  assert.ok(!html.includes('A &lt;report&gt;.pdf</a>') && !/<a [^>]*>[^<]*(report|unread)/.test(html), 'no link for a source file');
  const at = ['Supplied, not used', 'Original handoffs', 'Calculations and Model'].map(t => html.indexOf(t));
  assert.ok(at.every((n, i) => n >= 0 && (!i || n > at[i - 1])), at.join());
  assert.ok(evidencePage(EVIDENCE, 'record').includes('Input hashes'));
});

test('Evidence: a document date the run records is shown as stored, in the used and the unused list', () => {
  const ev = { ...EVIDENCE, sources: [{ ...EVIDENCE.sources[0], documentDate: '31 March 2025 (audited)' }], unused: [{ ...EVIDENCE.unused[0], documentDate: '2024-12-31' }] };
  const html = evidencePage(ev, 'sources');
  assert.ok(html.includes('31 March 2025 (audited)') && html.includes('2024-12-31'));
  assert.equal(countOf([...html.matchAll(/<article class="ev-card ev-src".*?<\/article>/gs)].join(''), /Not recorded/g), 0, 'both cards have a date');
});

test('Evidence: files whose use no handoff records are "Use not recorded", not "Supplied, not used"', () => {
  const ev = { ...EVIDENCE, sources: [], unused: [], unrecorded: [{ name: 'D_file.pdf', sha256: 'd'.repeat(64), type: 'pdf', documentDate: null, readBy: [] }], noSourcesModules: ['CP-0', 'CP-1'] };
  const html = evidencePage(ev, 'sources');
  assert.ok(html.includes('Use not recorded') && html.includes('has a Sources section') && html.includes('D_file.pdf'));
  assert.ok(!html.includes('Supplied, not used'));
  const some = { ...EVIDENCE, noSourcesModules: ['CP-1'] };
  const part = evidencePage(some, 'sources');
  assert.ok(part.includes('Supplied, not used') && part.includes('No Sources section in the handoff of Financial foundation') && !part.includes('Use not recorded'));
});

test('Evidence: handoffs and calculations are download links; Download all is the zip; the model calls are closed', () => {
  const html = evidencePage(EVIDENCE, 'sources'), record = evidencePage(EVIDENCE, 'record');
  assert.equal(countOf(html, /<a class="ev-dl" href="[^"]*" download/g), 4, 'two handoffs, Download all, one Model');
  assert.equal(countOf(record, /<a class="ev-link" href="[^"]*" download/g), 1, 'one instruction');
  assert.ok(html.includes('href="downloads/r/handoffs.zip" download') && html.includes('<span>Download all</span>'));
  assert.ok(html.includes('href="../runs/r/CP-0.md?sha256=1" download'));
  assert.ok(/<details class="ev-call"/.test(record) && !/<details[^>]* open/.test(record));
  assert.ok(record.includes('Provider cap USD 12') && record.includes('0.00941950') && record.includes('d'.repeat(64)));
  assert.ok(strip(/<details class="ev-call".*?<\/details>/s.exec(record)[0]).includes('Not recorded'), 'a missing error class is not a value');
});

test('Evidence (R3): Read by and the downloads lead with names; the link is named for its handoff; no module code in the Sources tab text', () => {
  const html = evidencePage(EVIDENCE, 'sources');
  assert.ok(!/\bCP-[A-Z0-9]+\b/.test(strip(html)), 'no module code in visible text (an avatar shows the code without its prefix)');
  const named = [...html.matchAll(/\s(?:aria-label|data-tip|title)="([^"]*)"/g)].map(m => m[1]);
  assert.ok(named.length > 5 && named.every(v => !/\bCP-[A-Z0-9]+\b/.test(v)), `no module code in an aria-label, data-tip or title: ${named.filter(v => /\bCP-[A-Z0-9]+\b/.test(v))}`);
  const foot = html.slice(html.indexOf('Original handoffs'));
  assert.ok(foot.includes('<span>Source readiness</span>') && foot.includes('aria-label="Download Source readiness handoff"'), foot);
  assert.ok(foot.includes('aria-label="Download Financial foundation handoff"') && !/>CP-[01]\.md</.test(foot));
});

test('Evidence (R6): the Run record labels a module-named file by its module, keeps other names and every hash', () => {
  const record = evidencePage(EVIDENCE, 'record');
  assert.deepEqual([...record.matchAll(/<div class="ev-nm">([^<]*)<\/div><code>([^<]*)</g)].map(m => [m[1], m[2][0]]),
    [['delivery-x.json', 'd'], ['Financial foundation handoff', '1'], ['Source readiness instructions', '2'], ['Financial foundation handoff (a)', '3']]);
  assert.ok(!/\bCP-[A-Z0-9]+\b/.test(strip(record)));
  assert.equal(runPage().handoffLabel('CP-1.md'), 'Financial foundation handoff');
});

test('Evidence: the Run record lists the methods changed since the run, escaped; a run on today\'s methods lists none', () => {
  const changed = evidencePage(EVIDENCE, 'record', { methodChanges: ['CP-0: methods/cp0.md changed', 'CP-1: <b>x</b> no longer selected'] });
  const record = changed.slice(changed.indexOf('Methods changed since this run'));
  assert.ok(record.includes('<span class="mono">Source readiness: methods/cp0.md changed</span>') && record.includes('<span class="mono">Financial foundation: &lt;b&gt;x&lt;/b&gt; no longer selected</span>'));
  assert.ok(!changed.includes('<b>x</b>'));
  for (const none of [[], undefined]) {
    const html = evidencePage(EVIDENCE, 'record', { methodChanges: none });
    assert.ok(!html.includes('<ul class="ev-mc-list">') && html.includes('None listed'), 'the summary says none are listed and draws no list');
  }
});

test('Evidence (fix round 2): a method change leads with its module name; any other module code is named; file paths stay verbatim', () => {
  const html = evidencePage(EVIDENCE, 'record', { methodChanges: ['CP-0: src/deploy_vii/methods/cp0.md changed', 'CP-1A: src/deploy_vii/methods/cp1a.md, docs/x.md changed', 'CP-0: reads CP-1 and src/deploy_vii/methods/CP-1.md'] });
  const list = /<div class="ev-sub-h">Methods changed since this run<\/div><ul class="ev-mc-list" data-group>.*?<\/ul>/s.exec(html)[0];
  assert.ok(list.includes('<span class="mono">Source readiness: src/deploy_vii/methods/cp0.md changed</span>'), list);
  assert.ok(list.includes('<span class="mono">Business &amp; governance: src/deploy_vii/methods/cp1a.md, docs/x.md changed</span>'), list);
  assert.ok(list.includes('<span class="mono">Source readiness: reads Financial foundation and src/deploy_vii/methods/CP-1.md</span>'), 'a code in the detail is named; a path is not');
  assert.ok(!/\bCP-[A-Z0-9]+\b/.test(strip(list).replace(/src\/deploy_vii\/methods\/CP-1\.md/, '')), list);
});

test('Evidence: a hash row named like a stored source file keeps its name', () => {
  const file = { name: 'Board-CP-1.md', sha256: 'b'.repeat(64), type: 'md', documentDate: null, readBy: [] };
  const ev = { ...EVIDENCE, sources: [file], record: { ...EVIDENCE.record, hashes: [{ name: 'Board-CP-1.md', sha256: 'b'.repeat(64) }] } };
  assert.equal(countOf(evidencePage(ev, 'sources'), />Board-CP-1\.md</g), 1, 'the source card');
  assert.equal(countOf(evidencePage(ev, 'record'), />Board-CP-1\.md</g), 1, 'the hash row');
});

test('Evidence: nothing recorded says so and invents nothing', () => {
  const none = { sources: [], unused: [], unrecorded: [], noSourcesModules: [], handoffs: [], zip: null, downloads: [], record: { hashes: [], instructions: [], calls: [], cap: null } };
  const sources = evidencePage(none, 'sources'), record = evidencePage(none, 'record');
  for (const want of ['The run record lists no supplied files.', 'This run holds no handoff', 'No calculation or Model file was published']) assert.ok(sources.includes(want), want);
  for (const want of ['The run records no hash', 'The run records no instructions', 'The run records no model call', 'Provider cap not recorded']) assert.ok(record.includes(want), want);
  assert.ok(!sources.includes('Download all') && !sources.includes('<table') && !record.includes('<table'));
  assert.ok(!sources.includes('Every supplied file is named') && !sources.includes('Supplied, not used'), 'no supplied file recorded is not "every supplied file used"');
  // Supplied files that a handoff names, with none left over, do say so.
  const all = evidencePage({ ...none, sources: EVIDENCE.sources }, 'sources');
  assert.ok(all.includes('Every supplied file is named in a handoff’s Sources section.') && !all.includes('The run record lists no supplied files.'));
  assert.ok(evidenceView({ r: {} })('r').includes('No evidence record was read'));
});

test('Run activity shows only runs in progress and the queue (ruling decision 10)', () => {
  const html = activityView()({ cap: '20', held: '', runs: [
    { id: 'a', status: 'running', folder: 'f-run', issuer_name: 'Runner' },
    { id: 'b', status: 'queued', folder: 'f-wait', issuer_name: 'Waiter' },
    { id: 'c', status: 'finished', folder: 'f-done', issuer_name: 'Finisher' },
    { id: 'd', status: 'failed', folder: 'f-bad', issuer_name: 'Failer' }] });
  assert.ok(html.includes('Runner') && html.includes('Waiter') && html.includes('Running') && html.includes('Waiting'));
  for (const gone of ['Finisher', 'Failer', 'Ended', 'Run folders not shown', 'Issues']) assert.ok(!html.includes(gone), gone);
  assert.ok(!html.includes('<a '), 'no report link');
});

test('Run activity says so when nothing is running or waiting, and never when its data is missing', () => {
  const none = activityView()({ runs: [{ status: 'finished', issuer_name: 'Finisher' }] });
  assert.ok(none.includes('No run in progress') && !none.includes('Finisher'));
  assert.ok(activityView()({ runs: [] }).includes('No run in progress'));
  const missing = activityView()(undefined);
  assert.ok(missing.includes('could not be read') && !missing.includes('No run in progress'));
  const boot = read('static-boot.js');
  assert.ok(boot.includes('activity=null') && !boot.includes('activity={excluded:[],issues:[]}'));
});

test('the library page lists the folders not shown and the build issues closed, last, with reasons', () => {
  const html = libraryNotShown()({ excluded: [['run-half', 'no <CP-1A> output'], ['legacy', 'not a run']], issues: ['store: bad pin'] });
  for (const want of ['run-half', 'no &lt;CP-1A&gt; output', 'legacy', 'not a run', 'store: bad pin', 'Run folders not shown', 'Issues']) {
    assert.ok(html.includes(want), `missing ${want}`);
  }
  assert.ok(/^<details class="library-not-shown"><summary>/.test(html) && !/<details[^>]* open/.test(html), 'closed by default');
  assert.equal(libraryNotShown()({ excluded: [], issues: [] }), '');
  assert.ok(libraryNotShown()(null).includes('could not be read'));
  const text = read('views.js');
  assert.ok(text.includes('</div>${libraryNotShown(window.DESIGN_ACTIVITY)}`;'), 'drawn after the results and the run detail');
});

test('Forecast for a run with no CP-2G output says no model was published', () => {
  const views = read('views.js');
  assert.ok(views.includes('if(!models.length)return forecastEmpty(context)+forecastCharts(context);'));
  assert.ok(views.includes("data[forecast.output].module==='CP-2G'?'the full forward credit model output':`the ${data[forecast.output].module} output the forecast was built from`"), 'the link names the module it opens');
  assert.ok(views.includes('>Open ${fullName}${icon'), 'the label is not fixed text');
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
const GROUPS = [['Business and evidence', [['CP-0', 'Source readiness'], ['CP-1A', 'Business & governance']]], ['Financial performance', [['CP-1', 'Financial foundation']]], ['Other modules', [['CP-6', 'Unnamed module']]]];
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
  // X2: a control is drawn only where the page's evidence map holds its item. The build keys its chips by the handoff's own lines, so the fixture's chip keys are items of the map too.
  for (const key of Object.keys(CHIPS)) if (!evidence.has(key)) evidence.set(key, { module: 'CP-1', line: Number(key.split(':').pop()) });
  const win = { Components: require('./components.js'), Shapes: require('./shapes.js'), Evidence: require('./evidence.js'), CREDIT_OS_DATA: { chips: CHIPS }, DESIGN_CATALOGUE: { real: [{ id: 'run-a', checklist: null }] }, DESIGN_WORKSPACE: { reports: [] } };
  const sectionData = (id, sid) => out.sections.filter(s => modules[id].sections.find(x => x[0] === sid)[2].some(p => s.heading.startsWith(p)));
  const names = ['window', 'data', 'modules', 'contexts', 'store', 'moduleNames', 'groups', 'esc', 'plain', 'rich', 'icon', 'pins', 'evidence', 'current', 'isAnalytical', 'sectionData', 'lastFile', 'aliases', 'isNewFormat', 'readerPassages', 'blocked', 'splitBasis', 'basisItem', 'chartNumber', 'numericColumn', 'cellView', 'basisButton', 'paragraphView', 'sectionBodyHtml', 'passageControls', 'eventTable', 'eventTimeline'];
  const reader = require('./reader.js');
  const args = [win, data, modules, { 'run-a': { folder: 'run-a', modules: { 'CP-1': { outputs: [OUT], default: OUT } } } }, {}, NAMES, GROUPS, esc, plain, rich, n => `<img src="icons/${n}.svg">`, {}, evidence, { context: 'run-a', section: 'head', module: 'CP-1' }, id => !id.startsWith('W-'), sectionData, new Map(), { 'CP-6A': 'CP-6' }, reader.isNewFormat, reader.readerPassages, reader.blocked, reader.splitBasis, reader.basisItem, ...['chartNumber', 'numericColumn', 'cellView', 'basisButton', 'paragraphView', 'sectionBodyHtml', 'passageControls'].map(name => reader[name]), require('./calendar.js').eventTable, realEventTimeline(esc, rich)];
  return new Function(...names, `${src}; return {fold, moduleReport, reportParts, reportAnalysis, reportReference, reportCalculations, reportHead, chipsMarkup, chipView, keyNumbers, reportLimits, reportAudit, reportBand, outlineMarkup, navigationSections, drawnAnchors, availability, unavailableView, REPORT_PARTS, METHOD_CODE, moduleTitle, handoffLabel};`)(...args);
}
const strip = html => html.replace(/<[^>]+>/g, '');
// screen.js eventTimeline as written, with the page's helpers stood in (the source footer is a plain marker).
function realEventTimeline(esc, rich) {
  const screen = read('screen.js'), calendar = require('./calendar.js');
  return new Function('esc', 'rich', 'eventOrder', 'orderEvents', 'sourceFooter', `${screen.slice(screen.indexOf('function eventTimeline('), screen.indexOf('function businessVisual('))}; return eventTimeline;`)(esc, rich, calendar.eventOrder, calendar.orderEvents, key => `<small class="footer">${esc(key)}</small>`);
}
// The summary as a reader reads it: the title, then the detail the row draws at its right. The row holds the two as two spans with one space between; this joins them with " · ", the form the callers' expected texts use.
const summaryOf = (html, id) => strip(new RegExp(`<details[^>]*id="${id}"[^>]*><summary>(.*?)</summary>`).exec(html)[1].replace('</span> <span class="fold-detail">', ' · '));
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
  assert.ok(html.includes('id="s-56"') && html.includes('Net debt is 1,200 less 3,472.') && !html.includes('data-paragraph='), 'an earlier paragraph with no citation and no chip has no Basis button');
});

test('(g) a leading method code is dropped from a displayed heading and kept nowhere', () => {
  const sections = ['T2F.1 — Macro source gate', 'cp2b.cp_model_catalysts — blocked interface', 'TDR.1 — Research brief', 'Net debt — bridge'].map((h, i) => view(h, 100 + 10 * i, [text(101 + 10 * i, 'x')]));
  const html = report({ sections }).reportAnalysis(OUT);
  assert.ok(html.includes('<h4>Macro source gate</h4>'));
  assert.ok(html.includes('<h4>blocked interface</h4>'));
  assert.ok(html.includes('<h4>Research brief</h4>'));
  assert.ok(!/<h4 title=/.test(html), 'no title keeps the id');
  assert.ok(html.includes('<h4>Net debt — bridge</h4>'));
  assert.equal(report().METHOD_CODE.source, '^(?:[A-Z][A-Z0-9]*\\.[A-Z]?\\d+(?:\\s+—\\s+|\\s+(?=[A-Z]))|[a-z0-9]+(?:\\.[a-z0-9_]+)+\\s+—\\s+)');
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

test('(i2) the head shows the confidence Python computed, or why there is none; no field draws nothing', () => {
  const head = c => report({ confidence: c }).reportHead(OUT);
  assert.ok(head({ value: 58, band: 'Low' }).includes('<span class="output-meta" title="Computed from the inputs the module states">Confidence 58 · Low</span>'));
  assert.ok(head({ value: 0, band: 'Insufficient Information' }).includes('Confidence 0 · Insufficient Information'));
  const missing = head({ missing: 'the table has no row for Source gate' });
  assert.ok(missing.includes('<span class="output-meta" title="Computed from the inputs the module states">Confidence not computed: the table has no row for Source gate</span>'));
  assert.ok(head({ missing: '<b>x</b>' }).includes('Confidence not computed: &lt;b&gt;x&lt;/b&gt;'));
  assert.ok(!report().reportHead(OUT).includes('Confidence'));
  assert.equal(report({ confidence: { value: 58, band: 'Low' } }).reportHead(OUT).match(/class="badge badge-gray"/g).length, 1);
  noCode(head({ value: 58, band: 'Low' }));
});

test('(j) Analysis holds only the view sections, open, in handoff order, each with its line id', () => {
  const html = report().reportAnalysis(OUT);
  // Decisions 7 and 14, H7 (earlier format): no chip is printed in prose; a paragraph with no citation and no chip in the build has no Basis button.
  assert.ok(html.startsWith('<section class="part" id="analysis"><h3>Analysis</h3>') && !html.includes('<details class="fold"'));
  assert.equal(countOf(html, /<button type="button" class="basis-link"/g), 0, 'no citation and no chip in the build: no Basis button');
  assert.ok(!/class="chips"|class="chip/.test(html) && !html.includes('basis-fold'), 'no chip is printed in prose');
  assert.deepEqual([...html.matchAll(/class="analysis-section" id="(s-\d+)"/g)].map(m => m[1]), ['s-34', 's-36']);
  assert.ok(html.includes('Liquidity is <strong>ample</strong> through FY2025.') && !html.includes('data-paragraph='));
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
  assert.deepEqual(chips, ['|K|p.123|', '|M|p.70–71|', '|Business &amp; governance · E2|', '|Financial foundation · D1 · D3|']);
  assert.ok(html.includes('data-chip="run-a/deliveries/d1/CP-1.md:16" data-index="3"') && html.includes('data-evidence="run-a/deliveries/d1/CP-1.md:16"'));
  // The Row chip became the trace icon of the row (no chip class, no "Row" word); it keeps the evidence key.
  assert.ok(/<button type="button" class="basis-link trace-row" data-evidence="run-a\/deliveries\/d1\/CP-1.md:16" title="Table row, line 16" aria-label="Table row, line 16"><svg/.test(html));
});

test('Not supplied renders as a gap chip; other gaps fold into one count', () => {
  const html = report().chipsMarkup(`${OUT}:52`);
  assert.ok(html.includes('</span>Not supplied<span') && html.includes('<span class="av gap">?</span>') && html.includes('title="the row says so"'));
  assert.equal(html.match(/class="chip gap"/g).length, 1);
  assert.equal(html.includes('no page<span') || html.includes('no key<span'), false);
  assert.equal(html.match(/class="chip-count"/g).length, 1);
  assert.ok(html.includes(`data-gaps="${OUT}:52"`) && html.includes('>2 unresolved citations</button>'));
});

test('a key of only unresolved chips has no gap chip and one count; one reads in the singular', () => {
  const { chipsMarkup } = report();
  const two = chipsMarkup(`${OUT}:53`);
  assert.equal(two.includes('class="chip gap"'), false);
  assert.equal(two.match(/class="chip-count"/g).length, 1);
  assert.ok(two.includes('>2 unresolved citations</button>'));
  assert.ok(chipsMarkup(`${OUT}:54`).includes('>1 unresolved citation</button>'));
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
  assert.ok(html.includes('<b>Creditor impact</b>Higher gross leverage.') && html.includes('<span class="conf">Confidence High</span>') && !html.includes('class="pill"'));
});

test('limits come from the limits-placed sections with chips and their line ids; audit lists the rest by line', () => {
  const r = report();
  const limits = r.reportLimits(OUT);
  assert.ok(limits.includes('id="s-50"') && limits.includes('Coupons are <strong>not supplied</strong>.') && limits.includes(`data-paragraph="${OUT}:52"`) && !limits.includes('class="chip'), 'the build holds a chip for this paragraph, so it has a Basis button');
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
  const names = ['data', 'contexts', 'esc', 'rich', 'plain', 'evidence', 'modules', 'moduleNames', 'current', 'icon', 'window', 'store', 'pins', 'lastFile', 'isAnalytical', 'sectionData', 'chartNumber', 'numericColumn', 'cellView'];
  const fn = new Function(...names, `${text}; return ${name};`)({ [id]: out }, { 'run-a': { asOf } }, esc, esc, esc, new Map(), {}, {}, {}, () => '', { CREDIT_OS_DATA: { chips: {} } }, {}, {}, new Map(), () => true, () => [], require('./reader.js').chartNumber, require('./reader.js').numericColumn, require('./reader.js').cellView);
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
    new Function('$', 'current', 'sectionView', 'button', 'keepsCodes', `${text.slice(start, end)}; openAuditSection(button);`)(() => body, { output: 'o' }, () => { throw new Error('boom'); }, button, () => false);
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
  assert.ok(html.includes('<span class="fold-detail">12 sections · unchanged from the handoff</span>'));
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
  for (const line of [75, 77]) assert.ok(html.includes(`aria-label="Table row, line ${line}"`), line); // earlier-format table rows keep their chip column
  assert.ok(!html.includes('data-paragraph='), 'no earlier-format paragraph here has a citation or a chip, so none has a Basis button');
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
  // X1 (re-pointed): the list held Request too (old form: all four names). A section written for another module is listed and drawn nowhere, so Request is gone from it; the others stay.
  for (const name of ['Front matter', 'Alpha register', 'Sources']) assert.ok(audit.includes(name), name);
  assert.ok(!audit.includes('Request') && !audit.includes('data-audit="req"'), 'the Request section is not an item of the list');
  assert.ok(!audit.includes('Beta analysis'));
  for (const name of ['Parent text.', 'asked', 'abc']) assert.ok(!page.replace(audit, '').includes(name), name);
  assert.ok(!page.includes('asked'), 'the Request text is drawn nowhere on the page');
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

test('section rail (Task 4): the first part crossing the top of the canvas is current; the last part is current once wholly in view; the mark is aria-current="location"', () => {
  const src = read('screen.js'), start = src.indexOf('function markRail('), end = src.indexOf('function renderRoute(');
  assert.ok(start >= 0 && end > start);
  const ids = ['bottom-line', 'key-findings', 'limitations'];
  const state = {};
  const links = ids.map(id => ({ dataset: { part: id }, classList: { toggle: (cls, on) => { state[id] = { ...state[id], [cls]: on }; } }, setAttribute: (k, v) => { state[id] = { ...state[id], [k]: v }; }, removeAttribute: k => { state[id] = { ...state[id], [k]: undefined }; } }));
  const rail = { querySelectorAll: () => links };
  const parts = Object.fromEntries(ids.map(id => [id, { id }]));
  const observers = [];
  class FakeObserver { constructor(callback, options) { this.callback = callback; this.options = options; this.targets = []; this.disconnected = false; observers.push(this); } observe(target) { this.targets.push(target); } disconnect() { this.disconnected = true; } }
  const content = { querySelector: sel => (sel === '.sec-rail' ? rail : null) };
  const api = new Function('$', 'document', 'IntersectionObserver', `${src.slice(start, end)}; return {markRail, watchRail};`)(id => (id === 'content' ? content : null), { getElementById: id => parts[id] }, FakeObserver);
  const current = () => ids.filter(id => state[id]?.['aria-current'] === 'location');
  api.markRail(rail, 'key-findings');
  assert.deepEqual(current(), ['key-findings']);
  assert.equal(state['key-findings'].on, true);
  assert.equal(state['bottom-line'].on, false);
  api.watchRail();
  const [band, end_] = observers;
  assert.equal(band.options.rootMargin, '0px 0px -70% 0px');
  assert.deepEqual(band.targets, ids.map(id => parts[id]));
  assert.deepEqual(end_.targets, [parts.limitations], 'only the last part is watched for being wholly in view');
  band.callback([{ target: parts['key-findings'], isIntersecting: true }]);
  assert.deepEqual(current(), ['key-findings']);
  band.callback([{ target: parts['bottom-line'], isIntersecting: true }]);
  assert.deepEqual(current(), ['bottom-line'], 'the first part in page order wins');
  band.callback([{ target: parts['bottom-line'], isIntersecting: false }, { target: parts['key-findings'], isIntersecting: false }]);
  assert.deepEqual(current(), ['bottom-line'], 'with nothing crossing the mark stays where it was');
  end_.callback([{ intersectionRatio: 1 }]);
  assert.deepEqual(current(), ['limitations']);
  end_.callback([{ intersectionRatio: 0.2 }]);
  band.callback([{ target: parts['key-findings'], isIntersecting: true }]);
  assert.deepEqual(current(), ['key-findings']);
  api.watchRail();
  assert.ok(observers[0].disconnected && observers[1].disconnected, 'a new page drops the old observers');
});

test('section rail (Task 4): a page without a rail (earlier format, other pages) starts no observer; without IntersectionObserver the links still work and nothing is marked', () => {
  const src = read('screen.js'), start = src.indexOf('function markRail('), end = src.indexOf('function renderRoute(');
  let made = 0;
  const bare = new Function('$', 'document', 'IntersectionObserver', `${src.slice(start, end)}; return watchRail;`)(() => ({ querySelector: () => null }), {}, class { constructor() { made += 1; } });
  bare();
  assert.equal(made, 0);
  const withRail = { querySelector: () => ({ querySelectorAll: () => [] }) };
  new Function('$', 'document', `${src.slice(start, end)}; watchRail();`)(() => withRail, {});
  assert.equal(made, 0);
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
// The screen's own defaults for every library filter (screen.js holds them; the page tests read the line rather than keep a copy).
const libraryDefaults = () => new Function(`return ${/const LIBRARY_DEFAULTS = (\{[^}]*\});/.exec(read('screen.js'))[1]}`)();
function runPage(mutate = d => d, reports = [], shape = modules => modules, more = {}) {
  const src = read('views.js');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const plain = v => String(v).replace(/\*\*|`/g, '');
  const rich = v => esc(v).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  const data = mutate(runData());
  // The store places each section of an output (data[id].placement, parallel to its sections); the fixtures' own `where` is that placement.
  for (const out of Object.values(data)) out.placement ??= out.sections.map(s => s.where);
  const evidence = new Map();
  for (const [id, out] of Object.entries(data)) for (const s of out.sections) for (const b of s.blocks) {
    for (const r of b.type === 'table' ? b.rows : [b]) evidence.set(`${id}:${r.line}`, { module: out.module, line: r.line });
  }
  const groups = [['Business and evidence', [['CP-0', 'Source readiness']]], ['Financial performance', [['CP-1', 'Financial foundation'], ['CP-1B', 'Cash flow']]], ['Outlook and downside', [['CP-2A', 'Downside']]],
    ['Decision and review', [['CP-6', 'Committee decision']]], ['Other modules', [['CP-X', 'Unnamed module']]], ...(more.names ? [['Names added by the test', Object.entries(more.names)]] : [])];
  const moduleNames = Object.fromEntries(groups.flatMap(g => g[1]));
  const entry = code => ({ outputs: [outId(code)], default: outId(code) });
  const contexts = { [RUN]: { folder: RUN, record: more.record, ...more.runFields, modules: shape({ 'CP-0': { outputs: [], default: null }, ...Object.fromEntries(Object.values(data).map(out => [out.module, entry(out.module)])) }) }, ...more.contexts };
  const win = { Components: require('./components.js'), Shapes: require('./shapes.js'), Evidence: require('./evidence.js'), location: more.location, CREDIT_OS_DATA: { chips: { [`${outId('CP-1')}:16`]: [{ kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 123, page_end: null }], ...more.chips } }, DESIGN_CATALOGUE: { real: more.catalogue || [{ id: RUN, checklist: null }] }, RUN_ACTIVITY: more.activity, DESIGN_WORKSPACE: { reports, models: [], visuals: more.visuals || [], models: more.models || [] } };
  Object.assign(data, more.data || {}); // outputs of other runs, which the run under test's module list must not hold
  const libraryState = { selected: '', sortKey: '', direction: 'asc', hidden: '' };
  const names = ['LIBRARY_DEFAULTS', 'libraryState', 'LibraryLogic', 'libraryFilters', 'window', 'data', 'modules', 'contexts', 'store', 'moduleNames', 'groups', 'esc', 'plain', 'rich', 'icon', 'pins', 'evidence', 'current', 'isAnalytical', 'sectionData', 'lastFile', 'lastSection', 'aliases', 'sourceLink', 'classTag', 'eventTable', 'eventSpan', 'eventAxis', 'eventPlace', 'eventTicks', 'eventAsOf', 'eventStack', 'eventRoom', 'earlierFormatRun', 'blocked', 'historyRows', 'pathwayTitle', 'runModuleCodes', 'matchesHeading', 'readerPassages', 'splitBasis', 'isNewFormat', 'basisItem', 'chartNumber', 'numericColumn', 'cellView', 'basisButton', 'paragraphView', 'sectionBodyHtml', 'passageControls', 'eventTimeline', '$', 'appDestinations', 'document', 'ChangesView'];
  const eventTimeline = realEventTimeline(esc, rich);
  const args = [libraryDefaults(), libraryState, new Function(`${read('screening.js')}; return LibraryLogic;`)(), libraryDefaults(), win, data, Object.fromEntries(Object.keys(data).map(id => [id, { first: 'head', sections: more.sections?.[id] || [] }])), contexts, more.store || {}, moduleNames, groups, esc, plain, rich, n => `<img src="icons/${n}.svg">`, {}, evidence, { context: RUN, section: 'overview' }, id => !id.startsWith('W-'), () => [], new Map(), new Map(), { 'CP-6A': 'CP-6' }, (key, label) => `<button class="source-link" data-evidence="${esc(key)}">${esc(label)}</button>`, () => '', ...['eventTable', 'eventSpan', 'eventAxis', 'eventPlace', 'eventTicks', 'eventAsOf', 'eventStack', 'eventRoom'].map(name => require('./calendar.js')[name]), ...['earlierFormatRun', 'blocked', 'historyRows', 'pathwayTitle', 'runModuleCodes'].map(name => require('./reader.js')[name]), (heading, prefix) => (prefix.startsWith('=') ? heading === prefix.slice(1) : heading.startsWith(prefix)), ...['readerPassages', 'splitBasis', 'isNewFormat', 'basisItem', 'chartNumber', 'numericColumn', 'cellView', 'basisButton', 'paragraphView', 'sectionBodyHtml', 'passageControls'].map(name => require('./reader.js')[name]), eventTimeline, more.dom?.$, new Set(['W-Library', 'CP-OS']), more.dom?.document, require('./changes.js')];
  return new Function(...names, `${src}; return {runTokens, runReport, readerChart, lastPeriodChart, chartCards, cellView, libraryRow, libraryPath, libraryDetail, libraryPanel, libraryResults, libraryState, libraryFilters, libraryChoices, LIBRARY_COLUMNS, libraryView, libraryRows, libraryFacets, libraryCard, libraryCards, libraryLive, libraryChipValue, libraryCount, sameNameWords, libraryRunName, libraryModules, libraryLead, libraryStrip, libraryFiltered, moduleHead, headerChipMarkup, traceHref, drawerFoot, runName, updateWorkspaceChrome, namedText, moduleTitle, handoffLabel, current, modules, eventLanesView, navigationSections, historyView, runLabel, mapLayers, mapsView, moduleReport, reportParts, outlineMarkup, navigatorView, issuerMeta, startRunHref, startRunLink, drawnAnchors, defaultOutput, firstSection, cashflowSection, modelOptionLabels, forecastView, forecastCharts, chartCard, evidenceInput, evidenceHit};`)(...args);
}
const countOf = (html, re) => (html.match(re) || []).length;

// ---- The Overview (ruling H5): selection and ordering only. Expected values below are written by hand from the synthetic fixture's text
// (apps/issuer-library/fixtures/synthetic-new-format) or from the tiny inline handoffs in each test; none is read back from production code.
const readText = html => strip(html).replace(/&#39;/g, "'");
// The fixture's markdown as the store hydrates it: a heading starts a section, a list item starts its own text block (its Basis line stays in it), a pipe table is one table block.
function mdSections(name) {
  const lines = fs.readFileSync(path.join(__dirname, '..', '..', 'fixtures', 'synthetic-new-format', `SYNTHETIC-${name}.md`), 'utf8').split('\n');
  const sections = [];
  let cur = null, block = null;
  const close = () => { if (block && cur) cur.blocks.push(block); block = null; };
  lines.forEach((raw, i) => {
    const n = i + 1, h = /^(#{1,3}) (.*)$/.exec(raw);
    if (h) { close(); cur = { heading: h[2], level: h[1].length, line: n, where: 'view', blocks: [] }; sections.push(cur); return; }
    if (raw.trim() === '') { close(); return; }
    if (raw.startsWith('|')) {
      if (block?.type !== 'table') { close(); block = { type: 'table', line: n, headers: null, rows: [] }; }
      const cells = raw.slice(1, -1).split('|').map(c => c.trim());
      if (!block.headers) block.headers = cells; else if (!/^[-| ]+$/.test(raw)) block.rows.push({ line: n, cells });
      return;
    }
    if (raw.startsWith('- ')) { close(); block = { type: 'text', line: n, text: raw }; return; }
    if (block?.type === 'text') { block.text += `\n${raw}`; return; }
    close(); block = { type: 'text', line: n, text: raw };
  });
  close();
  return sections;
}
// A handoff of the new format from literal passages: lists are the "- " items of each passage.
const passageSections = ({ bottom, key, limits }) => [
  sec('Findings', 2, 1, 'view', []),
  ...(bottom === undefined ? [] : [sec('Bottom line', 3, 2, 'view', [text(3, bottom)])]),
  ...(key === undefined ? [] : [sec('Key findings', 3, 5, 'view', key.map((item, i) => text(6 + i, item)))]),
  ...(limits === undefined ? [] : [sec('Limitations', 3, 20, 'view', limits.map((item, i) => text(21 + i, item)))]),
];
const FIXTURE_NAMES = { 'CP-1A': 'Business and structure', 'CP-2': 'Credit view', 'CP-2D': 'Liquidity' };
const steps = codes => ({ steps: codes.map(module => ({ module, started: null, accepted: null })), edges: [], timed: false });
// Outputs for a run in the new format. `parts` maps a code to sections; `blockedCodes` get established false only for the earlier-format rule.
const overviewData = parts => Object.fromEntries(Object.entries(parts).map(([code, sections]) => [outId(code), runOutput(code, { sections, state: { established: true, declared: null }, summary: null, words: {} })]));
const overviewPage = (parts, { order = Object.keys(parts), asOf = '2025-03-31', ...more } = {}) => runPage(() => overviewData(parts), [], m => m, { record: steps(order), runFields: { asOf }, names: FIXTURE_NAMES, ...more });
const FIXTURE = { 'CP-0': mdSections('CP-0'), 'CP-1': mdSections('CP-1'), 'CP-1A': mdSections('CP-1A'), 'CP-2': mdSections('CP-2'), 'CP-2D': mdSections('CP-2D') };
const withFixtureLanes = d => {
  const cp1a = d[outId('CP-1A')], lane = cp1a.sections.find(s => s.heading === 'Events: issuer calendar');
  cp1a.events = [{ lane: 'issuer calendar', table: lane.blocks.find(b => b.type === 'table').line, gap: null }];
  return d;
};
const fixturePage = (more = {}) => runPage(d => withFixtureLanes(overviewData(FIXTURE)), [], m => m, { record: steps(Object.keys(FIXTURE)), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES, ...more });
const OVERVIEW_CP1 = { visuals: [{ module: 'CP-1', placement: 'Overview; Model' }] };
// The Overview's sections, whole: from the section's opening tag to the next section of the page (the module tiles nest their own groups).
const part = (html, id) => { const open = new RegExp(`<section class="overview-part[^"]*" id="${id}"`).exec(html); if (!open) return undefined; const next = html.indexOf('<section class="overview-part', open.index + 1); return html.slice(open.index, next < 0 ? html.length : next); };
const partIds = html => [...html.matchAll(/<section class="overview-part[^"]*" id="([^"]+)"/g)].map(m => m[1]);
const tileHrefs = html => [...html.matchAll(/<a class="mt-open" href="#([^/"]+)\//g)].map(m => m[1]);
const tileOf = (html, code) => new RegExp(`<details class="mt" name="overview-modules"><summary(?:(?!</details>).)*?<a class="mt-open" href="#${code}/.*?</details>`, 's').exec(html)?.[0];
const sentencesOf = body => body.replace(/\nBasis:.*$/s, '').replace(/^- /, '').replace(/\*\*/g, '').split(/(?<=\.)\s+(?=[A-Z])/);
const CP2_BOTTOM = 'Creditors are exposed to refinancing risk rather than to weak earnings: net debt of USD 1,390 million is 4.2x earnings, and the next maturities fall inside two years.';

test('Overview on the synthetic run: the view, why, the modules and the limits, in that order; no chart, no date list, no navigator content, outline or count line', () => {
  const html = fixturePage().runReport(RUN);
  assert.deepEqual(partIds(html), ['overview-lead', 'overview-why', 'overview-modules', 'overview-limitations']);
  for (const gone of ['data-run-part', 'class="coverage"', 'run-count', 'register', 'class="matrix"', 'chart-index', 'event-lanes', 'status-map', 'overview-dates', 'overview-charts', 'bottom-entry', 'Written by', 'Evidence and audit', 'overview-aside']) assert.ok(!html.includes(gone), gone);
  assert.ok(html.startsWith('<div class="overview-page">'));
});

test('Overview lead: CP-6 absent, so CP-2 leads, as before: its Bottom line is the verdict and its Key findings and What-would-change follow, text as written', () => {
  const html = fixturePage().runReport(RUN), lead = part(html, 'overview-lead'), why = part(html, 'overview-why');
  assert.ok(lead.includes('<h3 class="eyebrow">Bottom line</h3>') && readText(lead).includes(CP2_BOTTOM));
  const items = [
    'Leverage is moderate but not low, at 4.2x net debt to EBITDA, so there is little room for an earnings miss.',
    'A large part of the debt comes due soon: 38% of gross debt matures within 24 months, which makes refinancing access the deciding factor.',
    'Liquidity support rests on an undrawn revolver that steps down, which narrows the cushion over time.',
  ];
  const text = readText(why);
  let at = text.indexOf('Key findings');
  assert.ok(at >= 0);
  for (const item of items) { const next = text.indexOf(item, at); assert.ok(next > at, item); at = next; }
  assert.ok(text.indexOf('What would change the view') > at, 'the callout follows the findings');
  assert.equal(countOf(why, /<li class="feed-item">/g), 3);
  assert.ok(!readText(html).includes('Basis:') && !html.includes('class="basis"'), 'the Basis line is not printed');
  // Hand count: the Bottom line has USD 1,390 million and 4.2x; the findings 4.2x and 38% (24 months is a span of time); one trace icon per paragraph that has a Basis item:
  // the Bottom line 1, the three findings 3, the first What-would-change paragraph 1.
  assert.equal(countOf(lead + why, /<button type="button" class="figure"/g), 4);
  assert.equal(countOf(lead + why, /<button type="button" class="basis-link"/g), 5);
  assert.ok(!readText(why).includes('Peer leverage was not compared'), 'only the lead\'s passages');
});

test('Overview tiles: every module of the run in the catalogue\'s order and groups, the lead among them; first sentence while closed, the whole Bottom line and the link when open', () => {
  const html = fixturePage().runReport(RUN), tiles = part(html, 'overview-modules');
  assert.deepEqual(tileHrefs(tiles), ['CP-0', 'CP-1', 'CP-1A', 'CP-2', 'CP-2D']);
  assert.deepEqual([...tiles.matchAll(/<span class="eyebrow mt-group">([^<]*)<\/span>/g)].map(m => m[1]), ['Business and evidence', 'Financial performance', 'Names added by the test', 'Names added by the test', 'Names added by the test'], 'the group names each tile, in one grid');
  assert.equal(countOf(tiles, /<div class="mt-grid">/g), 1);
  assert.ok(readText(tileOf(tiles, 'CP-0')).includes('The two documents read are enough for a credit snapshot, but no covenant package was read, so creditor protections cannot be confirmed from the file set.'));
  assert.ok(readText(tileOf(tiles, 'CP-1A')).includes("Northbridge is a single-segment services group whose creditors depend on one operating company, so debt service rests on that company's cash generation."));
  const lead = tileOf(tiles, 'CP-2');
  assert.ok(/<span class="mt-lead">Creditors are exposed to refinancing risk rather than to weak earnings: net debt of USD 1,390 million is 4\.2x earnings, and the next maturities fall inside two years\.<\/span>/.test(lead), 'the first sentence, whole');
  assert.ok(lead.includes('<p class="mt-p">') && lead.includes('class="mt-open" href="#CP-2/'));
  assert.ok(!tiles.includes('class="state'), 'no module declares a state here, so no badge');
  const blocked = tileOf(tiles, 'CP-2D');
  assert.ok(readText(blocked).includes('Not assessable: the documents read give no monthly cash forecast and no revolver drawing terms, so cash cover of the maturities cannot be tested.'));
  assert.ok(blocked.includes('<span class="mt-state"><span class="badge badge-gray">Not assessable</span></span>'), 'the mark the module rail shows for a blocked module');
  assert.equal(countOf(html, /Not assessable<\/span>/g), 1, 'only the blocked module is marked');
});

test('Overview tiles: a tile opens one at a time (every tile is a details of the one name), keeps its state in the DOM, and no script is involved', () => {
  const tiles = part(fixturePage().runReport(RUN), 'overview-modules');
  const opens = [...tiles.matchAll(/<details\b([^>]*)>/g)].map(m => m[1]);
  assert.equal(opens.length, 5);
  assert.ok(opens.every(attrs => attrs === ' class="mt" name="overview-modules"'), opens.join('|'));
  assert.ok(!/\sopen[\s>=]/.test(opens.join(' ')), 'all closed on load');
  assert.ok(!/<script|onclick|onclick=/.test(tiles));
  assert.equal(countOf(tiles, /<summary class="mt-head">/g), 5, 'the whole tile head is the control');
  const css = read('screen.css');
  assert.ok(css.includes('.mt[open]{grid-column:1/-1') && css.includes('.mt[open] .mt-lead{display:none}'), 'the open tile takes the row and shows its whole Bottom line in place of the first sentence');
});

test('Overview tiles: a declared state is its word beside its icon, in a status token; a missing state draws none', () => {
  const html = runPage(() => { const d = overviewData(FIXTURE); d[outId('CP-0')].state.declared = 'Restricted'; d[outId('CP-1')].state.declared = 'Draft Only'; return d; }, [], m => m, { record: steps(Object.keys(FIXTURE)), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES }).runReport(RUN);
  const tiles = part(html, 'overview-modules');
  assert.ok(/<span class="state warn"><svg[^>]*>.*?<\/svg><span class="state-w">Restricted<\/span><\/span>/.test(tileOf(tiles, 'CP-0')));
  assert.ok(/<span class="state info"><svg[^>]*>.*?<\/svg><span class="state-w">Draft Only<\/span><\/span>/.test(tileOf(tiles, 'CP-1')));
  assert.equal(countOf(tiles, /class="state /g), 2);
  assert.ok(!tileOf(tiles, 'CP-1A').includes('class="state'));
});

test('Overview order follows the catalogue\'s groups, not the order CP-OS ran the modules', () => {
  const parts = { 'CP-1': FIXTURE['CP-1'], 'CP-0': FIXTURE['CP-0'], 'CP-1A': FIXTURE['CP-1A'] };
  const html = overviewPage(parts, { order: ['CP-1A', 'CP-0'] }).runReport(RUN);
  assert.deepEqual(tileHrefs(html), ['CP-0', 'CP-1', 'CP-1A']);
});

test('Overview lead from CP-6 when it ran and is not blocked; CP-2 is then an ordinary tile', () => {
  const html = overviewPage({
    'CP-6': passageSections({ bottom: 'Committee view: hold the position.', key: ['- Hold, because refinancing is open.'] }),
    'CP-2': passageSections({ bottom: 'Credit view: refinancing risk.', key: ['- Leverage is moderate.'] }),
  }).runReport(RUN);
  const page = readText(part(html, 'overview-lead')) + readText(part(html, 'overview-why'));
  assert.ok(page.includes('Committee view: hold the position.') && page.includes('Hold, because refinancing is open.'));
  assert.ok(!page.includes('Credit view: refinancing risk.') && !page.includes('Leverage is moderate.'));
  assert.deepEqual(tileHrefs(html), ['CP-6', 'CP-2']);
  assert.ok(readText(tileOf(html, 'CP-2')).includes('Credit view: refinancing risk.') && !readText(tileOf(html, 'CP-2')).includes('Leverage is moderate.'), 'a tile is the Bottom line alone');
});

test('Overview lead: a blocked CP-6 falls back to CP-2, and CP-6 keeps its tile with its own words', () => {
  const html = overviewPage({
    'CP-6': passageSections({ bottom: 'Not assessable: no upstream module concluded.', key: ['- Nothing to rank.'] }),
    'CP-2': passageSections({ bottom: 'Credit view: refinancing risk.', key: ['- Leverage is moderate.'] }),
  }).runReport(RUN);
  const page = readText(part(html, 'overview-lead')) + readText(part(html, 'overview-why'));
  assert.ok(page.includes('Credit view: refinancing risk.') && page.includes('Leverage is moderate.') && !page.includes('Nothing to rank.'));
  assert.ok(readText(tileOf(html, 'CP-6')).includes('Not assessable: no upstream module concluded.'));
});

test('Overview lead: an unblocked earlier-format CP-6 has no Bottom line, so the new-format CP-2 leads and CP-6\'s tile reads "No bottom line in this handoff."', () => {
  const earlier = [sec('Findings', 2, 1, 'view', []), sec('Cash is up and leverage is high.', 3, 2, 'view', [text(3, 'Old reader summary text.')])];
  const html = overviewPage({ 'CP-6': earlier, 'CP-2': passageSections({ bottom: 'Credit view: refinancing risk.', key: ['- Leverage is moderate.'] }) }).runReport(RUN);
  assert.ok(readText(part(html, 'overview-lead')).includes('Credit view: refinancing risk.'));
  assert.ok(tileOf(html, 'CP-6').includes('<span class="mt-lead">No bottom line in this handoff.</span>'));
  assert.ok(!html.includes('Old reader summary text.'));
});

test('Overview lead on a short snapshot: CP-L10 leads with its Bottom line and Key findings (amendment 2026-11-11 to H5)', () => {
  const html = overviewPage({
    'CP-0': FIXTURE['CP-0'],
    'CP-1': FIXTURE['CP-1'],
    'CP-L10': passageSections({ bottom: 'Creditors are covered, but only just.', key: ['- Cover is thin.'] }),
  }, { names: { ...FIXTURE_NAMES, 'CP-L10': 'Short credit snapshot' } }).runReport(RUN);
  const page = readText(part(html, 'overview-lead')) + readText(part(html, 'overview-why'));
  assert.ok(page.includes('Creditors are covered, but only just.') && page.includes('Cover is thin.'));
  assert.ok(tileHrefs(html).includes('CP-L10') && readText(tileOf(html, 'CP-L10')).includes('Short credit snapshot'));
});

test('Overview lead: CP-2 still leads over CP-L10 when both ran, and a blocked CP-L10 leaves no lead', () => {
  const both = overviewPage({
    'CP-2': passageSections({ bottom: 'Credit view: refinancing risk.', key: ['- Leverage is moderate.'] }),
    'CP-L10': passageSections({ bottom: 'Short view.', key: ['- Short finding.'] }),
  }).runReport(RUN);
  assert.ok(readText(part(both, 'overview-lead')).includes('Credit view: refinancing risk.') && !readText(part(both, 'overview-lead')).includes('Short view.'));
  const blockedHtml = overviewPage({ 'CP-L10': passageSections({ bottom: 'Not assessable: CP-1 stated no figure.' }) }, { names: { ...FIXTURE_NAMES, 'CP-L10': 'Short credit snapshot' } }).runReport(RUN);
  assert.equal(readText(part(blockedHtml, 'overview-lead')), 'Credit viewNo credit view module completed in this run.');
  assert.deepEqual(partIds(blockedHtml), ['overview-lead', 'overview-modules']);
});

test('Overview lead: neither CP-6 nor CP-2 usable gives the one sentence; both blocked is the same, and every module keeps its tile', () => {
  const none = overviewPage({ 'CP-0': FIXTURE['CP-0'], 'CP-1': FIXTURE['CP-1'] }).runReport(RUN);
  assert.equal(readText(part(none, 'overview-lead')), 'Credit viewNo credit view module completed in this run.');
  const both = overviewPage({ 'CP-6': passageSections({ bottom: 'Not assessable: no input.' }), 'CP-2': passageSections({ bottom: 'Not assessable: no peers.' }) }).runReport(RUN);
  assert.equal(readText(part(both, 'overview-lead')), 'Credit viewNo credit view module completed in this run.');
  assert.deepEqual(tileHrefs(both), ['CP-6', 'CP-2']);
  assert.deepEqual(partIds(both), ['overview-lead', 'overview-modules'], 'nothing else is drawn without a lead');
});

test('Overview limitations: the lead\'s own, as written, with the count of gaps the run lists and the way to them in Evidence; another module\'s limitations are not drawn', () => {
  const html = fixturePage().runReport(RUN), list = part(html, 'overview-limitations');
  const items = [...list.matchAll(/<li>(.*?)<\/li>/gs)].map(m => readText(m[1]));
  assert.deepEqual(items, [
    'The Covenant package was not reviewed,  so covenant headroom is not assessed',
    'Peer leverage was not compared, so the 4.2x reading has no market anchor.',
    'The liquidity assessment is not available, so cash cover of the maturities is unverified.',
  ]);
  assert.ok(!readText(list).includes('Dates after the annual report are scheduled'), 'CP-1A\'s own limitation is not the lead\'s');
  assert.ok(/<div class="gapsig-n" data-count>5<\/div><div class="gapsig-w">gaps recorded<\/div><a class="gapsig-link" href="#W-Evidence\/gaps\?c=run-a">Open in Evidence/.test(list), 'five rows in the run\'s Gaps sections, counted as Evidence lists them');
  assert.ok(list.includes('<h2 class="rd-h"'));
});

test('Overview limitations: a lead with no Limitations passage draws no block; no gaps draws no signal', () => {
  const none = overviewPage({ 'CP-1': passageSections({ bottom: 'B1.' }), 'CP-2': passageSections({ bottom: 'Credit view.', limits: ['- No peer set was supplied.'] }) }).runReport(RUN);
  assert.ok(readText(part(none, 'overview-limitations')).includes('No peer set was supplied.') && !part(none, 'overview-limitations').includes('gapsig'));
  const without = overviewPage({ 'CP-2': passageSections({ bottom: 'Credit view.' }), 'CP-1': passageSections({ bottom: 'B1.', limits: ['- Another module limit.'] }) }).runReport(RUN);
  assert.equal(part(without, 'overview-limitations'), undefined);
  assert.ok(!without.includes('Another module limit.'));
});

// ---- A real-shaped run: CP-1 with its metric table and CP-6 leading with a sided Decision table and an events lane, every audit column and Basis line present.
const FIG = 'CP1-annual-report.pdf', MEMO = 'CP6-memo.pdf';
const REAL_BOTTOM = `Hold the position. Net leverage of 6.01x and interest cover of 2.1x decide it.\nBasis: ${MEMO}, page 1; calculation C05.`;
const REAL_KEY = [`- **Cover is thin.** Interest cover is 2.1x and free cash flow is USD 1,100 million.\nBasis: ${FIG}, page 5`, `- Growth does not change the view.\nBasis: ${FIG}, page 7`];
const REAL_CONTRARY = [`The view would soften if a signed refinancing removed the 2027 maturity.\nBasis: ${MEMO}, page 2`];
const REAL_LIMITS = [`- No holdings file was supplied, so portfolio fit is unscored.\nBasis: ${MEMO}, page 3`, '- The chair left relative value unscored.'];
const METRIC_HEAD = ['Metric', 'FY2024', 'FY2023', 'Definition / identity', 'Source', 'Calculation ID'];
const metricRows = [
  [12, 'Net leverage', '6.01x', '6.40x', 'Net debt over EBITDA', `${FIG}, page 4`, 'C05'],
  [13, 'Interest cover', '2.1x', '2.5x', 'EBITDA over cash interest', `${FIG}, page 5`, 'C06'],
  [14, 'Free cash flow', 'USD 1,100 million', 'USD 900 million', 'Cash from operations less capex', `${FIG}, page 6`, 'C07'],
  [15, 'Revenue growth', '9.0%', '8.0%', 'Year on year', `${FIG}, page 7`, 'C08'],
];
const decisionRows = [[31, 'Leverage after the dividend', '5.55x', 'Bear (weakly)', 'Leverage is high but falling.', `${MEMO}, page 4`], [32, 'Liquidity', 'USD 1,500 million', 'Bull', 'Covers the nearest maturity.', `${MEMO}, page 5`]];
const eventRows = [[42, '2025-07-11', 'Securitization renewal', 'Debt & Capital Structure', 'Funding line ends.', `${MEMO}, page 6`], [43, '2027-09-30', 'Hedge end', 'Macro', 'Rate cover lapses.', `${MEMO}, page 7`]];
const EVENT_HEAD = ['Date/Window', 'Event Description', 'Event Category', 'Credit Relevance Summary', 'Source'];
const realSections = (over = {}) => ({
  'CP-1': [
    sec('Findings', 2, 1, 'view', []),
    sec('Bottom line', 3, 2, 'view', [text(3, `Financial position is in the table below.\nBasis: ${FIG}, page 4`)]),
    ...(over.metric === false ? [] : [sec('Financials and credit metrics', 3, 10, 'view', [table(11, METRIC_HEAD, metricRows)])]),
    sec('Gaps', 2, 90, 'audit', [table(91, ['Gap', 'Severity'], [[92, 'No peer set', 'Low']])]),
  ],
  'CP-6': [
    sec('Findings', 2, 1, 'view', []),
    sec('Bottom line', 3, 2, 'view', [text(3, over.bottom ?? REAL_BOTTOM)]),
    sec('Key findings', 3, 5, 'view', REAL_KEY.map((item, i) => text(6 + i, item))),
    sec('Contrary evidence and what would change the view', 3, 10, 'view', REAL_CONTRARY.map((item, i) => text(11 + i, item))),
    sec('Limitations', 3, 20, 'view', REAL_LIMITS.map((item, i) => text(21 + i, item))),
    ...(over.sided === false ? [] : [sec('Decision', 3, 30, 'view', [table(30, ['Decision driver', 'Figure', 'Side it supports', 'Chair reading', 'Source'], decisionRows)])]),
    ...(over.events === false ? [] : [sec('Events: Decision and watch', 3, 40, 'view', [table(41, EVENT_HEAD, eventRows)])]),
    ...(over.after ?? []),
    sec('Calculations', 2, 70, 'audit', [table(71, ['Calculation ID', 'Result'], [[72, 'C05', '6.01x']])]),
    sec('Gaps', 2, 95, 'audit', [table(96, ['Gap', 'Severity'], [[97, 'No holdings file', 'High'], [98, 'No rating', 'Low']])]),
  ],
});
const realPage = (over = {}) => runPage(() => { const d = overviewData(realSections(over)); if (over.events !== false) d[outId('CP-6')].events = [{ lane: 'Decision and watch', table: 41, gap: over.gap ?? null }]; return d; }, [], m => m, { record: steps(['CP-1', 'CP-6']), runFields: { asOf: '2025-03-31' }, names: { 'CP-1': 'Financial foundation', 'CP-6': 'Committee decision' } });
const realHtml = (over = {}) => realPage(over).runReport(RUN);

test('Overview figure strip: the rows of the run\'s first metric table whose label the Bottom line or Key findings name, in table order, each linked to its module, none when nothing matches', () => {
  const html = realHtml(), strip4 = html.slice(html.indexOf('<div class="strip"'), html.indexOf('</div></div></div></section>', html.indexOf('<div class="strip"')));
  assert.deepEqual([...strip4.matchAll(/<a class="strip-k"[^>]*>(.*?)<\/a>/g)].map(m => m[1]), ['Net leverage', 'Interest cover', 'Free cash flow'], 'Revenue growth is not named: "Growth" alone is not its label');
  assert.deepEqual([...strip4.matchAll(/<p class="strip-v">(.*?)<\/p>/g)].map(m => m[1]), ['6.01x', '2.1x', 'USD 1,100 million']);
  assert.ok(strip4.includes('<p class="strip-b">FY2023 6.40x</p>'));
  assert.ok(/<a class="strip-k" href="#CP-1\/[^"]*"/.test(strip4), 'it links to the module that holds the table');
  assert.ok(html.includes('<div class="c16">') && html.includes('<div class="c8">'));
  const keyOnly = realHtml({ bottom: 'Hold the position, whatever the figures say.' });
  assert.deepEqual([...keyOnly.matchAll(/<a class="strip-k"[^>]*>(.*?)<\/a>/g)].map(m => m[1]), ['Interest cover', 'Free cash flow'], 'the Key findings name rows too');
});

test('Overview figure strip: nothing in the lead\'s text matches a label, or no metric table, and the strip and its column are absent; the first four rows are never picked', () => {
  const html = runPage(() => { const d = overviewData(realSections()); const six = d[outId('CP-6')]; six.sections = six.sections.map(s => (s.heading === 'Key findings' ? { ...s, blocks: [text(6, '- The position is unchanged.')] } : s)); six.sections = six.sections.map(s => (s.heading === 'Bottom line' ? { ...s, blocks: [text(3, 'Hold the position.')] } : s)); six.events = []; return d; }, [], m => m, { record: steps(['CP-1', 'CP-6']), runFields: { asOf: '2025-03-31' }, names: { 'CP-1': 'Financial foundation', 'CP-6': 'Committee decision' } }).runReport(RUN);
  assert.ok(!html.includes('class="strip') && html.includes('<div class="c24"><div class="verdict">'), 'no match: the verdict takes the full width');
  assert.ok(!realHtml({ metric: false }).includes('class="strip'), 'no metric table');
});

test('Overview board: the run\'s first sided table through the sided component, attributed to its module; no sided table, no board and no placeholder', () => {
  const html = realHtml(), board = part(html, 'overview-decides');
  assert.ok(board.startsWith('<section class="overview-part" id="overview-decides"'));
  assert.ok(board.includes('<h2 id="overview-decides-h">What decides it</h2>') && /<p class="from"><a href="#CP-6\/[^"]*">From Committee decision/.test(board));
  assert.ok(board.includes('<div class="sd-board"') && board.includes('Leverage after the dividend') && board.includes('Leverage is high but falling.') && board.includes('Covers the nearest maturity.'));
  assert.ok(html.indexOf('overview-decides') > html.indexOf('overview-lead') && html.indexOf('overview-decides') < html.indexOf('overview-why'));
  const without = realHtml({ sided: false });
  assert.ok(!without.includes('overview-decides') && !without.includes('sd-board') && !without.includes('What decides it'));
  assert.deepEqual(partIds(without), ['overview-lead', 'overview-why', 'overview-watch', 'overview-modules', 'overview-limitations'], 'the lead\'s events still draw');
});

test('Overview watch: the lead\'s own events as the stacked dated timeline, attributed; nothing is windowed, counted or reordered', () => {
  const html = realHtml(), watch = part(html, 'overview-watch');
  assert.ok(watch.includes('<h2 id="overview-watch-h">What to watch</h2>') && /<p class="from"><a href="#CP-6\/[^"]*">From Committee decision/.test(watch));
  assert.ok(watch.includes('class="tl tl-v"') && !watch.includes('tl-h'), 'a narrow column runs the events down the page');
  assert.deepEqual([...watch.matchAll(/<div class="tl-d">(.*?)<\/div>/g)].map(m => m[1]), ['2025-07-11', '2027-09-30']);
  assert.ok(watch.includes('Securitization renewal') && watch.includes('Hedge end') && watch.includes('Funding line ends.'));
  assert.ok(html.indexOf('id="overview-watch"') > html.indexOf('class="callout"'), 'the dates stack under the callout');
});

test('Overview watch: a lead with no events takes the run\'s first dated table of a promoted shape, attributed to the module that holds it; none, no block', () => {
  const register = sec('Event risk register', 3, 50, 'view', [table(51, EVENT_HEAD, [[52, '2026-01-15', 'Rating review', 'Corporate', 'Could move the spread.', `${FIG}, page 9`]])]);
  const page = overviewData(realSections({ events: false }));
  page[outId('CP-1')].sections.splice(3, 0, register);
  const html = runPage(() => page, [], m => m, { record: steps(['CP-1', 'CP-6']), runFields: { asOf: '2025-03-31' }, names: { 'CP-1': 'Financial foundation', 'CP-6': 'Committee decision' } }).runReport(RUN);
  const watch = part(html, 'overview-watch');
  assert.ok(/<p class="from"><a href="#CP-1\/[^"]*">From Financial foundation/.test(watch) && watch.includes('Rating review') && watch.includes('2026-01-15'));
  assert.ok(!part(realHtml({ events: false }), 'overview-watch'), 'no lane and no promoted dated table: nothing is drawn');
  assert.ok(!fixturePage().runReport(RUN).includes('overview-watch'), 'another module\'s lane is not the lead\'s');
});

const absentLane = sections => { const lane = sections['CP-6'].find(s => s.heading === 'Events: Decision and watch'); lane.blocks = [table(41, ['Event date', 'Date precision', 'Published', 'Event', 'Status', 'Source', 'Credit relevance'], [[42, 'Not supplied: no decision date is stated in any supplied source', 'Not supplied: no dated event', 'Not supplied: no dated event', 'Not supplied: owned by other lanes', 'Not supplied: no dated event', 'Not supplied: no dated event', 'Not supplied: the watch conditions are undated triggers']])]; return sections; };
const realNamed = { record: steps(['CP-1', 'CP-6']), runFields: { asOf: '2025-03-31' }, names: { 'CP-1': 'Financial foundation', 'CP-6': 'Committee decision' } };
test('Overview watch: a lead lane that only states an absence is left to the module page: no panel, no empty state, and the callout stands alone in its column', () => {
  const html = runPage(() => { const d = overviewData(absentLane(realSections())); d[outId('CP-6')].events = [{ lane: 'Decision and watch', table: 41, gap: 'no dated decision event is stated' }]; return d; }, [], m => m, realNamed).runReport(RUN);
  assert.ok(!html.includes('overview-watch') && !html.includes('empty-state') && !html.includes('Not supplied') && !html.includes('What to watch'));
  assert.ok(/<div class="c10 ov-side"><div class="callout">.*<\/div><\/div><\/section>/s.test(part(html, 'overview-why') + '</section>'), part(html, 'overview-why'));
});

test('Overview watch: when the lead\'s lane is only an absence, the run\'s first dated table of a module that is not blocked is drawn, attributed to it', () => {
  const register = sec('Event risk register', 3, 50, 'view', [table(51, EVENT_HEAD, [[52, '2026-01-15', 'Rating review', 'Corporate', 'Could move the spread.', `${FIG}, page 9`]])]);
  const page = overviewData(absentLane(realSections()));
  page[outId('CP-6')].events = [{ lane: 'Decision and watch', table: 41, gap: 'no dated decision event is stated' }];
  page[outId('CP-1')].sections.splice(3, 0, register);
  const html = runPage(() => page, [], m => m, realNamed).runReport(RUN), watch = part(html, 'overview-watch');
  assert.ok(/<p class="from"><a href="#CP-1\/[^"]*">From Financial foundation/.test(watch) && watch.includes('Rating review') && !watch.includes('empty-state'));
});

test('Overview: a blocked module\'s tables feed neither What decides it nor What to watch (nor the strip); a usable module\'s still do', () => {
  const blockedBottom = 'Not assessable: no input was supplied.';
  const withBlocked = (code) => { const d = overviewData(realSections()); d[outId(code)].sections = d[outId(code)].sections.map(x => (x.heading === 'Bottom line' ? { ...x, blocks: [text(3, code === 'CP-6' ? 'Hold the position. Net leverage and interest cover decide it.' : blockedBottom)] } : x)); d[outId('CP-6')].events = []; return d; };
  // CP-1 blocked: its metric table gives no strip; CP-6 leads and keeps its own board.
  const noStrip = runPage(() => withBlocked('CP-1'), [], m => m, realNamed).runReport(RUN);
  assert.ok(!noStrip.includes('class="strip') && noStrip.includes('overview-decides'));
  assert.ok(tileOf(noStrip, 'CP-1').includes('Not assessable</span>'));
  // A blocked module holding the only dated table and the only sided table.
  const sections = realSections({ events: false, sided: false });
  const register = sec('Event risk register', 3, 50, 'view', [table(51, EVENT_HEAD, [[52, '2026-01-15', 'Rating review', 'Corporate', 'Could move the spread.', `${FIG}, page 9`]])]);
  const page = overviewData({ ...sections, 'CP-1': [...sections['CP-1'].slice(0, 3), register, sec('Decision', 3, 60, 'view', [table(61, ['Decision driver', 'Figure', 'Side it supports', 'Chair reading'], [[62, 'Cover', '2x', 'Bull', 'ok']])]), ...sections['CP-1'].slice(3)] });
  page[outId('CP-1')].sections = page[outId('CP-1')].sections.map(x => (x.heading === 'Bottom line' ? { ...x, blocks: [text(3, blockedBottom)] } : x));
  const html = runPage(() => page, [], m => m, realNamed).runReport(RUN);
  assert.ok(!html.includes('overview-watch') && !html.includes('overview-decides') && !html.includes('Rating review'));
});

test('Overview gap signal: the count is what the Evidence Gaps tab lists for the run (every saved output of every module), and a module page counts its own module the same way', () => {
  const other = `${RUN}/deliveries/d2/CP-1.md`, gapSec = rows => [sec('Gaps', 2, 90, 'audit', [table(91, ['Gap', 'Severity'], rows.map((r, i) => [92 + i, r, 'Low']))])];
  const page = runPage(() => { const d = overviewData(realSections()); d[outId('CP-6')].events = []; d[outId('CP-1')].sections.splice(2, 0, sec('Limitations', 3, 80, 'view', [text(81, '- A limit.')])); d[other] = runOutput('CP-1', { source: 'deliveries/d2/CP-1.md', sections: gapSec(['Gap A', 'Gap B']), state: { established: true, declared: null }, summary: null, words: {} }); d[other].placement = d[other].sections.map(sx => sx.where); return d; }, [], m => ({ ...m, 'CP-1': { outputs: [outId('CP-1'), other], default: outId('CP-1') } }), realNamed);
  const shown = html => Number(/<div class="gapsig-n" data-count>(\d+)<\/div>/.exec(html)?.[1]);
  assert.equal(shown(page.runReport(RUN)), 5, 'CP-1 default 1 + CP-1 second output 2 + CP-6 2');
  assert.equal(shown(page.moduleReport(outId('CP-1'))), 3, 'the module page counts what Evidence lists with the module filter: both CP-1 outputs');
  assert.equal(shown(page.moduleReport(outId('CP-6'))), 2);
});

test('Overview verdict: a lead sentence over 140 characters is the is-long (text size) headline, not display size', () => {
  const long = 'Watchlist is the action bias that survives the challenge: cash generation and the maturity profile make near-term default remote, but creditors cannot yet tell whether any tranche is paid for an owner policy that recycles earnings. More follows.';
  const html = realHtml({ bottom: long });
  assert.ok(html.includes('<p class="verdict-lead is-long">') && /\.verdict-lead\.is-long\{/.test(read('screen.css')));
});

test('Overview: every sentence of the lead\'s Bottom line, Key findings, What-would-change and Limitations is on the page, in the handoff\'s own characters', () => {
  const html = realHtml(), text = readText(html).replace(/\s+/g, ' ');
  for (const body of [REAL_BOTTOM, ...REAL_KEY, ...REAL_CONTRARY, ...REAL_LIMITS]) for (const sentence of sentencesOf(body)) assert.ok(text.includes(sentence.replace(/\s+/g, ' ')), sentence);
  assert.ok(text.indexOf('Hold the position.') < text.indexOf('Cover is thin.') && text.indexOf('Cover is thin.') < text.indexOf('The view would soften') && text.indexOf('The view would soften') < text.indexOf('No holdings file was supplied'));
});

// The attributes the trace controls carry for the drawer (the paragraph or row key and its Basis items) are their mechanism, shared with the module page; every other attribute is checked.
const pageAttributes = html => [...html.matchAll(/<[a-z][^>]*>/g)].flatMap(tag => [...tag[0].matchAll(/\s([a-z-]+)="([^"]*)"/g)].map(m => [m[1], m[2].replace(/&quot;/g, '"').replace(/&amp;/g, '&')])).filter(([name]) => !['href', 'data-paragraph', 'data-basis', 'data-evidence'].includes(name));
const FORBIDDEN = [['Basis:', t => t.includes('Basis:')], ['a file name', t => /\.(?:pdf|jsonl?|htm|md|xlsx?|csv)\b/.test(t)], ['sha256', t => t.includes('sha256')], ['a calculation ID', t => /\b(?:C\d{2}|[Cc]alculations? [A-Z]\d{2})\b/.test(t)], ['a method code', t => /\bT\d[A-Z]?\.\d/.test(t)], ['the run folder', t => t.includes(RUN) || t.includes('deliveries')], ['markdown', t => t.includes('**')]];
test('Overview of a real-shaped run: no Basis line, file name, hash, calculation ID, method code, run code or markdown in its text or in any attribute but the trace controls\' keys', () => {
  for (const html of [realHtml(), fixturePage().runReport(RUN)]) {
    const text = readText(html), attrs = pageAttributes(html).map(([name, value]) => `${name}=${value}`).join('\n');
    for (const [what, test_] of FORBIDDEN) { assert.ok(!test_(text), `${what} in the page text`); assert.ok(!test_(attrs), `${what} in an attribute`); }
    assert.ok(!/<th scope="col">\s*(?:Source|Evidence|Calculation ID)/.test(html), 'no Source, Evidence or ID column header');
  }
});

test('Overview: the chart index, the Evidence and audit link lists and any records table are gone; a chart or map the catalogue places on Overview is drawn on its module page only', () => {
  const html = runPage(d => withLanes(withMaps(withBridge(d))), [], m => m, OVERVIEW_CP1).runReport(RUN);
  for (const gone of ['Chart index', 'chart-index-link', 'overview-charts', 'panel-card', 'map-card', 'lane-row', 'event-lanes', 'Evidence and audit', 'class="table-scroll"', '<table', 'dates-table', 'Key charts']) assert.ok(!html.includes(gone), gone);
  assert.ok(!realHtml().includes('<table'));
});

test('Overview headings: ordered from h2 with no level skipped, each section labelled as a landmark, one sr-only h2 for the lead', () => {
  for (const html of [realHtml(), fixturePage().runReport(RUN)]) {
    const levels = [...html.matchAll(/<h([1-6])\b/g)].map(m => Number(m[1]));
    assert.ok(levels.length >= 5 && !levels.includes(1), 'the page\'s one h1 is the shell\'s');
    let prev = 1;
    for (const level of levels) { assert.ok(level <= prev + 1, `h${level} after h${prev}: ${levels.join('')}`); prev = level; }
    for (const id of partIds(html)) assert.ok(/aria-label(?:ledby)?=/.test(new RegExp(`<section class="overview-part[^"]*" id="${id}"[^>]*>`).exec(html)[0]), id);
    assert.equal(countOf(html, /<h2 class="sr-only"/g), 1);
  }
});

test('narrow pages (W1): every Evidence table sits in a labelled, focusable scroll region (the Overview has no table left to scroll)', () => {
  const evidenceRegion = label => `<div class="ev-tbl" role="region" aria-label="${label}" tabindex="0" data-group data-head=`;
  const calc = { id: 'o1', placement: ['view'], sections: [{ heading: 'Calculations', level: 2, line: 1, blocks: [{ type: 'table', line: 2, headers: ['Calc ID', 'Result'], rows: [{ line: 3, cells: ['C-1', '2.1x'] }] }] }] };
  const page = tab => evidenceView({ r: { evidence: EVIDENCE, modules: { 'CP-0': { outputs: ['o1'], default: 'o1' } } } }, { o1: calc })('r', tab, 'CP-0');
  const record = page('record'), calculations = page('calculations');
  assert.equal(countOf(record, /<table/g), 1);
  assert.ok(record.includes(evidenceRegion('Model calls of Source readiness')));
  assert.equal(countOf(calculations, /<table/g), 1);
  assert.ok(calculations.includes(evidenceRegion('Source readiness: Calculations')));
  assert.equal(countOf(realHtml(), /<table/g), 0, 'the Overview draws components, never a grid that would need a scroll region');
});

test('Overview: every interpolated passage, strip, board, event and tile cell is escaped, and a passage keeps its own wording (bold only)', () => {
  const hostile = '<b>X</b> & "q" <img src=x onerror=1>';
  const sections = realSections();
  sections['CP-6'][1].blocks = [text(3, `${hostile} **Bold** view of Net leverage.`)];
  sections['CP-6'].find(s => s.heading === 'Limitations').blocks = [text(21, '- <b>L</b> stays text.')];
  sections['CP-1'].find(s => s.heading === 'Financials and credit metrics').blocks[0].rows[0].cells[0] = '<b>Net</b> leverage & "x"';
  sections['CP-6'].find(s => s.heading === 'Decision').blocks[0].rows[1].cells[1] = hostile;
  sections['CP-6'].find(s => s.heading === 'Events: Decision and watch').blocks[0].rows[0].cells[2] = hostile;
  const html = runPage(() => { const d = overviewData(sections); d[outId('CP-6')].events = [{ lane: 'Decision and watch', table: 41, gap: null }]; d[outId('CP-1')].sections[1].blocks = [text(3, hostile)]; return d; }, [], m => m, { record: steps(['CP-1', 'CP-6']), runFields: { asOf: '2025-03-31' }, names: { 'CP-1': 'Financial foundation', 'CP-6': 'Committee decision' } }).runReport(RUN);
  assert.ok(!html.includes('<img src=x') && !html.includes('<b>'), 'no hostile markup survives');
  assert.ok(html.includes('&lt;img src=x onerror=1&gt;') && html.includes('<strong>Bold</strong> view of Net leverage.'));
  assert.ok(html.includes('&lt;b&gt;L&lt;/b&gt; stays text.') && html.includes('&lt;b&gt;X&lt;/b&gt; &amp; &quot;q&quot;'));
  assert.equal(countOf(html, /<img\b/g), 0);
});

test('Overview of an earlier-format run: no lead, no limitations from the old summary; the modules still listed by name, each with "No bottom line in this handoff."', () => {
  const html = runPage(d => d, [], m => m, { record: steps(['CP-1', 'CP-2A', 'CP-6', 'CP-X']), runFields: { asOf: '2025-03-31' } }).runReport(RUN);
  assert.equal(readText(part(html, 'overview-lead')), 'Credit viewThis run is in the earlier format: its handoffs carry no reader passages for Overview to select.');
  assert.deepEqual(partIds(html), ['overview-lead', 'overview-modules']);
  assert.deepEqual(tileHrefs(html), ['CP-1', 'CP-2A', 'CP-6', 'CP-X']);
  assert.equal(countOf(html, /No bottom line in this handoff\./g), 4);
  for (const old of ['Cash is up and leverage is high.', 'No downside is drawn.', 'Synthetic limit one.', 'Leverage rose.']) assert.ok(!html.includes(old), `${old} is the old reader summary, not selectable by H5`);
  assert.ok(!html.includes('Limitations'));
});

test('Overview: a module with saved outputs and no default is a plain tile with a link to choose, never given an output', () => {
  const two = modules => ({ ...modules, 'CP-0': { outputs: [`${RUN}/deliveries/d1/CP-0-a.md`, `${RUN}/deliveries/d1/CP-0-b.md`], default: null } });
  const html = runPage(() => overviewData({ 'CP-1': FIXTURE['CP-1'] }), [], two, { record: steps(['CP-0', 'CP-1']), runFields: { asOf: '2025-03-31' } }).runReport(RUN);
  const list = part(html, 'overview-modules');
  assert.ok(readText(list).includes('Source readiness2 saved outputs, none chosen. Choose one'));
  assert.ok(/<a class="in-ev" href="#CP-0\?c=run-a">Choose one<\/a>/.test(list));
  assert.deepEqual(tileHrefs(list), ['CP-1'], 'the plain tile is not a details');
});

test('Overview: a run with no module output says so and keeps the source inventory link; no part is drawn', () => {
  const html = runPage(() => ({})).runReport(RUN);
  assert.equal(strip(/<div class="missing-state">(.*?)<\/div>/.exec(html)[1]), 'No module output retained for this runThe Overview is selected from module handoffs, and this run holds none.');
  assert.ok(html.includes('href="#W-Evidence/sources?c=run-a"'));
  assert.ok(!html.includes('overview-part') && !html.includes('<table'));
});

test('Overview with no module output returns the missing state with no two-column wrapper', () => {
  const html = runPage(() => ({})).runReport(RUN);
  assert.ok(html.startsWith('<div class="missing-state">'));
  assert.ok(!html.includes('overview-main') && !html.includes('overview-aside'));
});


test('Overview shell: no navigator or Browse modules button, no outline, and the old report parts and their styles are gone', () => {
  const views = read('views.js'), screen = read('screen.js'), css = read('screen.css');
  assert.ok(views.includes("classList.toggle('overview-workspace',!isHome&&module==='W-Overview')"));
  assert.ok(css.includes('.overview-workspace .navigator,.overview-workspace .mobile-modules{display:none}'));
  for (const gone of ['coverageStrip', 'creditStory', 'storyModule', 'storyLine', 'findingsRegister', 'openItems', 'moduleMatrix', 'registerRowShown']) assert.ok(!views.includes(gone) && !screen.includes(gone), gone);
  for (const gone of ['runOutline', 'runPart', 'data-run-part', 'data-register-filter', 'register-all']) assert.ok(!views.includes(gone) && !screen.includes(gone), gone);
  for (const gone of ['.story-module', '.story-group', '.na-line', 'a.cov', '.coverage{', 'table.register', 'table.open-items', 'table.matrix', '.register-tools', '.run-count', '#run-matrix']) assert.ok(!css.includes(gone), gone);
  for (const sel of ['.overview-part', '.passage-list', '.basis{', '.dates-table']) assert.ok(css.includes(sel), sel);
});
// ---- The Modules navigator and the module page (ruling decisions 3, 5, 12; H1, H4). Expected values are written by hand from the synthetic fixture.
const navPage = (more = {}, module = 'CP-2', query = '') => {
  const page = fixturePage({ runFields: { asOf: '2025-03-31', issuerKey: 'nbg' }, ...more });
  page.current.module = module; page.current.output = module === 'CP-MODEL' ? null : outId(module); page.current.section = 'head';
  return { page, ...page.navigatorView(module, query) };
};
const NAV_MODEL = { id: 'model-1', issuerKey: 'nbg', runId: RUN, sources: [] };

test('navigator (decision 5): no details or summary anywhere, plain group headings in order, only groups with a module that ran', () => {
  const { html } = navPage();
  assert.ok(!/<details|<summary/.test(html), 'flat and always open');
  assert.deepEqual([...html.matchAll(/<h2 class="nav-heading">([^<]*)<\/h2>/g)].map(m => m[1]), ['Business and evidence', 'Financial performance', 'Names added by the test']);
});

test('navigator (decision 5): only modules that ran are listed, and the count is that number', () => {
  const { html, count } = navPage();
  assert.equal(count, 5);
  assert.ok(!html.includes('module-code'), 'no module code is drawn');
  assert.deepEqual([...html.matchAll(/<span class="module-label">([^<]*)<\/span>/g)].map(m => m[1]), ['Source readiness', 'Financial foundation', 'Business and structure', 'Credit view', 'Liquidity']);
  assert.ok(!html.includes('CP-1B') && !html.includes('CP-2A') && !html.includes('CP-6'), 'a module the run did not hold is not listed');
});

test('navigator (decision 5): a module with no saved output is not listed even when the run records it', () => {
  const page = runPage(d => withFixtureLanes(overviewData(FIXTURE)), [], m => ({ ...m, 'CP-1B': { outputs: [], default: null } }), { record: steps([...Object.keys(FIXTURE), 'CP-1B']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES });
  page.current.module = 'CP-2'; page.current.output = outId('CP-2');
  const { html, count } = page.navigatorView('CP-2', '');
  assert.equal(count, 5);
  assert.ok(!html.includes('CP-1B'));
});

test('navigator (decision 5, amended 2026-11-12): the plain name only, no code; a blocked module is marked Not assessable, no other is', () => {
  const { html } = navPage();
  assert.ok(html.includes('<span class="module-label">Source readiness</span>'));
  assert.ok(html.includes('<span class="module-label">Credit view</span>'));
  const liquidity = /<a [^>]*><span class="module-label">Liquidity<\/span>.*?<\/a>/s.exec(html)[0];
  assert.ok(!liquidity.replace(/ href="[^"]*"/g, '').includes('CP-2D') && liquidity.includes('<span class="badge badge-gray">Not assessable</span>'));
  assert.equal(countOf(html, /Not assessable<\/span>/g), 1);
});

test('navigator (decision 5): the open entry has aria-current="page"; a new-format module has no outline under it (its page carries the section rail), no other entry has either', () => {
  const { html } = navPage();
  assert.equal(countOf(html, /aria-current="page"/g), 1);
  assert.equal(countOf(html, /<nav class="section-outline"/g), 0, 'the rail on the page replaces the outline of a new-format module');
  const entry = /<li><a [^>]*aria-current="page"[^>]*>.*?<\/a><\/li>/s.exec(html)[0];
  assert.ok(entry.includes('Credit view'));
});

test('navigator (decision 5): the open entry of an earlier-format module keeps its On this page outline, the nine parts in order', () => {
  const r = report();
  const outline = r.outlineMarkup(OUT);
  assert.equal(countOf(outline, /<nav class="section-outline" aria-label="On this page">/g), 1);
  assert.equal(countOf(outline, /class="section-item"/g), 9);
});

test('navigator (decision 5): search filters the same flat list by name, code and section titles', () => {
  assert.equal(navPage({}, 'CP-2', 'liquidity').count, 1);
  assert.equal(navPage({}, 'CP-2', 'cp-2d').count, 1);
  assert.equal(navPage({}, 'CP-2', 'cp-2').count, 2);
  const none = navPage({}, 'CP-2', 'zzz');
  assert.equal(none.count, 0);
  assert.ok(none.html.includes('No match.') && !/<details/.test(none.html));
});

test('navigator (decision 5): the Cash flow model entry (code CP-MODEL) is present exactly when the run has a published model', () => {
  const without = navPage();
  assert.ok(!without.html.includes('CP-MODEL') && !without.html.includes('Cash flow model'));
  const withModel = navPage({ models: [NAV_MODEL] });
  assert.equal(withModel.count, 6);
  assert.ok(withModel.html.includes('<h2 class="nav-heading">Delivered model</h2>'));
  assert.ok(withModel.html.includes('<span class="module-label">Cash flow model</span>'));
  assert.ok(/href="#CP-MODEL\/model-1\?c=run-a"/.test(withModel.html), 'it opens the model view in the Modules workbench, not the Forecast tab');
});

test('module page (H1): the four reader passages come first under their headings, then the other sections in handoff order', () => {
  const page = fixturePage(), id = outId('CP-2'), parts = page.reportParts(id);
  assert.deepEqual(parts.map(p => p[1]), ['Module', 'Bottom line', 'Key findings', 'Limitations']);
  assert.deepEqual(parts.map(p => p[0]), ['head', 'bottom-line', 'key-findings', 'limitations']);
  const html = page.moduleReport(id);
  const at = marker => html.indexOf(marker);
  assert.ok(at('id="bottom-line"') > 0 && at('id="bottom-line"') < at('id="key-findings"') && at('id="key-findings"') < at('id="contrary-evidence"') && at('id="contrary-evidence"') < at('id="limitations"'));
  for (const old of ['id="numbers"', 'id="findings"', 'class="band"', 'Quoted from the handoff', 'id="analysis"', 'id="audit"', 'id="reference"', 'id="calculations"', 'class="fold"']) assert.ok(!html.includes(old), `${old} is the old module page`);
  for (const gone of ['Credit view for Northbridge Synthetic Group', 'CP-2D assesses liquidity', 'Earnings and quarterly cash', 'No peer set supplied', 'Gross debt 1,700 less cash 310']) assert.ok(!html.includes(gone), `${gone} is Request, Next module, Sources, Gaps or Calculations text: Evidence's, not this page's`);
});

test('module page (H1, decision 7): passage text exactly as written, the Basis line not printed, figures and Basis links carry its items', () => {
  const html = fixturePage().moduleReport(outId('CP-2')), text = readText(html);
  for (const kept of [
    'Creditors are exposed to refinancing risk rather than to weak earnings: net debt of USD 1,390 million is 4.2x earnings, and the next maturities fall inside two years.',
    'A large part of the debt comes due soon: 38% of gross debt matures within 24 months, which makes refinancing access the deciding factor.',
    'The strongest evidence against concern is the consistent earnings record over recent quarters. A signed refinancing of the nearest maturity would move the view towards comfort.',
    'The company has not said how it intends to fund the step-down.',
    'The Covenant package was not reviewed,  so covenant headroom is not assessed',
  ]) assert.ok(text.includes(kept), kept);
  assert.ok(!text.includes('Basis:') && !html.includes('class="basis"'), 'the Basis line is not printed');
  const key = `${outId('CP-2')}:17`;
  // Bottom line (line 17) has Basis items and two figures; each figure button wraps its exact text and carries the paragraph key and both items, as written.
  const items = '[&quot;NBG_2025-03-31_annual-report.pdf, page 41&quot;,&quot;calculation K1&quot;]';
  assert.ok(html.includes(`<button type="button" class="figure" data-paragraph="${key}" data-basis="${items}" data-figure="0">USD 1,390 million</button>`));
  assert.ok(html.includes(`<button type="button" class="figure" data-paragraph="${key}" data-basis="${items}" data-figure="1">4.2x</button>`));
  // Hand count of referenced paragraphs: Bottom line 1, Key findings 3, Contrary evidence 1 (its second paragraph has no Basis line), Limitations 2 (items 2 and 3).
  assert.equal(new Set([...html.matchAll(/data-paragraph="([^"]+)"/g)].map(m => m[1])).size, 7);
  assert.equal(countOf(html, /<li class="feed-item">/g), 3, 'the three Key findings are the numbered feed');
  assert.equal(countOf(html, /<li>/g), 3, 'the three limitations, no attribute on them');
  assert.ok(/<p>The company has not said how it intends to fund the step-down\.<\/p>/.test(html), 'a paragraph with no Basis line has no control');
  // Task 4: one trace icon at the end of each referenced paragraph, whether or not it holds a figure: Bottom line 1, Key findings 3, Contrary evidence 1, limitations 2.
  assert.equal(countOf(html, /<button type="button" class="basis-link" data-paragraph="[^"]+" data-basis="[^"]*" aria-label="Basis for paragraph: [^"]+"><svg [^>]*>.*?<\/svg><\/button>/g), 7, 'the trace icon, no Basis word');
  // Hand count of figures in referenced paragraphs: USD 1,390 million and 4.2x (Bottom line), 4.2x and 38% (key findings 1 and 2), 4.2x (limitation 2).
  assert.equal(countOf(html, /class="figure"/g), 5);
});

test('module page (Task 4): a finding section is drawn after the passages, its table as record cards with no Source or ID column and one trace icon per row; Request, Sources, Calculations, Gaps and Next module are not drawn', () => {
  const id = outId('CP-1'), html = fixturePage().moduleReport(id), table = FIXTURE['CP-1'].flatMap(s => s.blocks).find(b => b.type === 'table' && b.headers[1] === 'Item');
  assert.ok(html.indexOf('id="s-19"') > html.indexOf('id="bottom-line"'), 'the section follows the Bottom line');
  assert.ok(html.includes('<h4>Canonical data</h4>'), 'a level-3 section is an h4 under the sr-only Findings h3');
  assert.equal(countOf(html, /<article class="rec-card">/g), 4);
  const text = readText(html);
  for (const [item, value, unit] of [['Gross debt', '1,700', 'USD million'], ['Cash', '310', 'USD million'], ['EBITDA', '331', 'USD million'], ['Debt maturing within 24 months', '646', 'USD million']]) {
    assert.ok(html.includes(`<p class="rec-title">${item}</p>`) && html.includes(`<dt>Value</dt><dd>${value}</dd>`) && html.includes(`<dt>Unit</dt><dd>${unit}</dd>`), item);
  }
  for (const row of table.rows) assert.ok(html.includes(`class="basis-link trace-row" data-evidence="${id}:${row.line}"`), `row ${row.line} has its trace icon`);
  for (const gone of ['NBG_2025-03-31_annual-report.pdf', 'NBG_2024-12-31_Q4-results.pdf', '<dt>Source</dt>', '<dt>ID</dt>', 'Revenue by segment not supplied', 'Canonical data for Northbridge', 'CP-1A reads the calendar', 'Values are as reported']) assert.ok(!text.includes(gone) && !html.includes(gone), gone);
  assert.ok(!html.includes('<table') && !html.includes('source-cell'), 'no raw grid and no Source button');
});

test('module page (Task 4): the page draws only passage, finding and drawing sections: a hidden section, a note paragraph and the register, Sources, Calculations and Gaps tables leave it; handoff order is kept', () => {
  const secs = [
    sec('Request', 2, 3, 'audit', [text(4, 'HIDDEN-REQUEST text')]),
    sec('Sources', 2, 5, 'audit', [table(6, ['Source', 'Use'], [[7, 'SRC-FILE.pdf', 'SOURCES-USE']])]),
    ...passageSections({ bottom: 'Cash is up. Debt is flat.', key: ['**Cash rose.** Operating cash grew.'], limits: ['Peers were not compared.'] }),
    sec('Liquidity position', 3, 30, 'view', [text(31, 'Liquidity is ample.'), text(32, 'Module status: complete.'), text(33, 'Confidence is 0.8 on this view.')]),
    sec('Debt facilities', 3, 40, 'view', [table(42, ['ID', 'Facility', 'Amount', 'Source'], [[43, 'F1', 'Revolver', '300', 'FAC-SOURCE.pdf']])]),
    sec('T2B.4 Source assessment', 3, 50, 'view', [table(52, ['Document', 'Weight'], [[53, 'REGISTER-DOC', 'REGISTER-WEIGHT']])]),
    sec('Module status and QA validation', 2, 60, 'view', [text(61, 'HIDDEN-QA text')]),
    sec('Calculations', 2, 70, 'view', [table(72, ['ID', 'Calculation'], [[73, 'K1', 'CALC-ROW']])]),
    sec('Gaps', 2, 80, 'view', [table(82, ['Gap', 'Effect'], [[83, 'GAP-ROW-ONE', 'e1'], [84, 'GAP-ROW-TWO', 'e2']])]),
    sec('Next module', 2, 90, 'audit', [text(91, 'HIDDEN-NEXT text')]),
  ];
  const parts = runPage(() => overviewData({ 'CP-1': secs }), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES });
  const html = parts.moduleReport(outId('CP-1')), text_ = readText(html);
  for (const hidden of ['HIDDEN-REQUEST', 'SRC-FILE', 'SOURCES-USE', 'FAC-SOURCE', 'REGISTER-DOC', 'REGISTER-WEIGHT', 'HIDDEN-QA', 'CALC-ROW', 'GAP-ROW', 'HIDDEN-NEXT', 'Module status', 'Confidence is 0.8', 'Source assessment', 'F1']) assert.ok(!text_.includes(hidden), `${hidden} is not drawn`);
  for (const shown of ['Liquidity is ample.', 'Revolver', '300', 'Liquidity position', 'Debt facilities', 'Cash is up.', 'Cash rose.', 'Peers were not compared.']) assert.ok(text_.includes(shown), `${shown} is drawn`);
  assert.deepEqual(parts.reportParts(outId('CP-1')).map(p => p[0]), ['head', 'bottom-line', 'key-findings', 's-30', 's-40', 'limitations']);
  assert.ok(html.indexOf('Liquidity position') < html.indexOf('Debt facilities') && html.indexOf('Debt facilities') < html.indexOf('id="limitations"'), 'handoff order, Limitations last');
  assert.deepEqual([...parts.drawnAnchors(outId('CP-1'))].sort(), ['s-30', 's-40'], 'only drawn sections are routable');
  // The gap signal counts the rows of the Gaps tables, links to the module's Evidence gaps tab, and is the last thing on the page.
  assert.ok(html.includes('<div class="gapsig-n" data-count>2</div>') && html.includes('href="#W-Evidence/gaps?c=run-a&amp;m=CP-1"'), html.slice(html.indexOf('lim-row')));
  assert.ok(html.indexOf('gapsig') > html.indexOf('Peers were not compared.'));
});

test('module page (ruling 2026-11-13): a finding paragraph holding an identifier or naming a calculation is not drawn; a passage paragraph always is; a section left with nothing keeps its heading and a link to Evidence', () => {
  const secs = [
    ...passageSections({ bottom: 'Cash holds EV-1 constant. Debt is flat.', key: ['**Cash rose.** See calculation K12 for the bridge.'], limits: ['Peers were not compared (EV-1 only).'] }),
    sec('Liquidity position', 3, 30, 'view', [text(31, 'Liquidity is ample.'), text(32, 'The EV-1 bridge needs review.'), text(33, 'Net debt is shown in calculation D17.'), text(34, 'EV-10 is another event, so this stays.')]),
    sec('Only calculation notes', 3, 40, 'view', [text(41, 'Uses calculation D17 only.')]),
    sec('Only identifier notes', 3, 45, 'view', [text(46, 'EV-1 drives this.')]),
    sec('Event list', 3, 50, 'view', [text(51, 'The list below holds EV-1.'), table(52, ['ID', 'Event'], [[53, 'EV-1', 'Fire']])]),
  ];
  const parts = runPage(() => overviewData({ 'CP-1': secs }), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES });
  const html = parts.moduleReport(outId('CP-1')), text_ = readText(html);
  for (const drawn of ['Liquidity is ample.', 'EV-10 is another event, so this stays.', 'Cash holds EV-1 constant.', 'See calculation K12 for the bridge.', 'Peers were not compared (EV-1 only).', 'Only calculation notes', 'Only identifier notes']) assert.ok(text_.includes(drawn), `${drawn} is drawn`);
  for (const gone of ['The EV-1 bridge needs review', 'calculation D17', 'EV-1 drives this', 'The list below holds EV-1']) assert.ok(!text_.includes(gone), `${gone} is Evidence's`);
  // The Event list keeps its table (a card per row; the ID column is never drawn) and gains no link; the two emptied sections each link to where their paragraphs went.
  const section = line => html.slice(html.indexOf(`id="s-${line}"`)).split('<div class="analysis-section"')[0];
  assert.ok(section(30).includes('Liquidity is ample.') && !section(30).includes('sec-moved'), 'a section with prose left has no link');
  assert.ok(section(40).includes('<p class="sec-moved"><a class="in-ev" href="#W-Evidence/calculations?c=run-a&amp;m=CP-1">In Evidence</a></p>'), 'only calculation notes: the Calculations tab');
  assert.ok(section(45).includes('<p class="sec-moved"><a class="in-ev" href="#W-Evidence/registers?c=run-a&amp;m=CP-1">In Evidence</a></p>'), 'an identifier among them: Registers');
  assert.ok(section(50).includes('Fire') && !section(50).includes('sec-moved'), 'a section that kept a table has no link');
});

test('module page (Task 4): the key findings sit beside "What would change the view" (14 and 10 columns); without a Contrary evidence passage they take the full width; the section rail lists the parts with counts', () => {
  const html = fixturePage().moduleReport(outId('CP-2'));
  assert.ok(html.includes('<section class="part key-row g24" id="key-findings"><div class="c14"><div class="rd-card"><h4 class="rd-h">Key findings</h4>'), 'the findings take 14 columns');
  assert.ok(html.includes('<div class="c10" id="contrary-evidence"><div class="callout"><h4>') && html.includes('What would change the view</h4>'));
  const alone = runPage(() => overviewData({ 'CP-1': passageSections({ bottom: 'Cash is up.', key: ['One finding here.'] }) }), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES }).moduleReport(outId('CP-1'));
  assert.ok(alone.includes('<div class="c24"><div class="rd-card"><h4 class="rd-h">Key findings</h4>') && !alone.includes('callout'));
  // The rail: head first in the page, then 5 of 24 columns for the rail and 19 for the parts; items are the parts after the head, with the number of items listed.
  assert.ok(html.indexOf('class="g24 module-grid"') > html.indexOf('id="head"') && html.includes('<div class="c5 module-rail"><nav class="sec-rail" aria-label="On this page">'));
  assert.deepEqual([...html.matchAll(/<a class="rail-item" data-part="([^"]+)" href="([^"]+)">([^<]*)(?:<span class="rail-count">(\d+)<\/span>)?<\/a>/g)].map(m => [m[1], m[3], m[4]]), [['bottom-line', 'Bottom line', undefined], ['key-findings', 'Key findings', '3'], ['limitations', 'Limitations', '3']]);
  assert.ok(html.includes('href="#CP-2/limitations?c=run-a"') && html.includes('<div class="c19 module-main"><section class="part" id="bottom-line">'));
  assert.equal(countOf(html, /id="section-nav"/g), 0);
});

test('module page (Review Focus 4): an earlier-format handoff keeps today\'s rendering path: the nine parts, the folds and the old outline; the new-format builders are not on its path', () => {
  const r = report(), html = r.moduleReport(OUT);
  assert.deepEqual(r.reportParts(OUT).map(p => p[0]), NINE);
  for (const kept of ['id="reference"', 'id="calculations"', 'id="audit"', 'Statements and registers', 'class="band"']) assert.ok(html.includes(kept), kept);
  for (const gone of ['module-grid', 'sec-rail', 'rec-card', 'class="verdict"', 'class="feed"']) assert.ok(!html.includes(gone), gone);
  assert.equal(html, r.reportParts(OUT).map(p => p[2]).join(''), 'an earlier-format page is its parts in a row');
  const src = read('views.js'), route = src.slice(src.indexOf('function reportParts(id) {'), src.indexOf('// ---- The module page of a new-format handoff'));
  assert.ok(/if\(isNewFormat\(data\[id\]\.sections\)\)return newFormatParts\(id\);/.test(route) && /reportAnalysis\(id\),reference=reportReference\(id\),calculations=reportCalculations\(id\),limits=reportLimits\(id\)/.test(route), 'the earlier-format branch still calls the same builders');
  const moduleReport = src.slice(src.indexOf('function moduleReport(id) {'), src.indexOf('// What the outline and the section list show'));
  assert.ok(/if\(!isNewFormat\(data\[id\]\.sections\)\|\|parts\.length<2\)return parts\.map\(part=>part\[2\]\)\.join\(''\);/.test(moduleReport));
  assert.ok(r.outlineMarkup(OUT).includes('class="section-outline"') && countOf(r.outlineMarkup(OUT), /class="section-item"/g) === 9);
});

test('module page (H4): a blocked new-format module has only its Bottom line and is marked in its head', () => {
  const page = fixturePage(), html = page.moduleReport(outId('CP-2D'));
  assert.deepEqual(page.reportParts(outId('CP-2D')).map(p => p[1]).slice(0, 2), ['Module', 'Bottom line']);
  assert.ok(!html.includes('id="key-findings"') && !html.includes('id="limitations"') && html.includes('Not assessable</span>'));
  assert.ok(readText(html).includes('Not assessable: the documents read give no monthly cash forecast'));
});

test('module page: a module with event lanes draws its own timeline, and one without draws none (the Calendar tab is gone)', () => {
  const page = fixturePage(), cp1a = page.moduleReport(outId('CP-1A')), cp2 = page.moduleReport(outId('CP-2'));
  // Task 7: a new-format page draws each lane as the dated timeline component (C15), one event per row of its table.
  assert.ok(/<section class="part" id="timeline"><div class="tl-lanes"><div class="section-heading"><h3>Timeline<\/h3>/.test(cp1a));
  assert.ok(cp1a.includes('<h4 class="tl-name">issuer calendar</h4>') && countOf(cp1a, /<li class="tl-i">/g) === 9);
  assert.ok(!cp2.includes('id="timeline"') && !cp2.includes('tl-name'));
  assert.ok(page.reportParts(outId('CP-1A')).some(p => p[0] === 'timeline' && p[1] === 'Timeline'));
});

// One CP-1A output of the given sections, placed as the store places an earlier-format handoff's sections (here: all in the view).
const placedPage = sections => runPage(() => { const d = overviewData({ 'CP-1A': sections }); d[outId('CP-1A')].placement = sections.map(s => s.where); return d; }, [], m => m, { record: steps(['CP-1A']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES });
test('module page (W2): an output with an event table and no Events lane draws its timeline from that table; with a lane the lane stands alone', () => {
  const rows = [[12, 'June 6, 2024', 'Notes redeemed', 'K, page 41'], [13, 'May 21 2024', 'Term loan repriced', 'K, page 42'], [14, 'Ongoing', 'Covenant testing', 'K, page 43']];
  const sections = [sec('Findings', 2, 1, 'view', []), sec('Business, structure and governance events', 3, 10, 'view', [table(11, ['Date', 'Event', 'Source'], rows)])];
  const page = placedPage(sections);
  const html = page.moduleReport(outId('CP-1A'));
  assert.ok(/<section class="part" id="timeline"><div class="section-heading"><h3>Issuer events<\/h3>/.test(html), html.slice(0, 300));
  // Rows are ordered by the year and month a date cell names; a row with no year follows. Text as written.
  assert.deepEqual([...html.matchAll(/<div class="event-date"><strong>([^<]*)<\/strong>/g)].map(m => m[1]), ['May 21 2024', 'June 6, 2024', 'Ongoing']);
  assert.ok(html.includes(`<small class="footer">${outId('CP-1A')}:13</small>`), 'each row keeps its source line');
  assert.ok(page.reportParts(outId('CP-1A')).some(p => p[0] === 'timeline' && p[1] === 'Timeline'));
  assert.ok(!html.includes('class="event-lanes'));
  // A table that is not an event table draws no timeline; a lane is drawn as lanes alone.
  const other = placedPage([sec('Findings', 2, 1, 'view', []), sec('Other', 3, 10, 'view', [table(11, ['Item', 'Value'], [[12, 'a', 'b']])])]);
  assert.ok(!other.moduleReport(outId('CP-1A')).includes('id="timeline"'));
  const lane = fixturePage().moduleReport(outId('CP-1A'));
  assert.ok(lane.includes('class="tl-lanes"') && !lane.includes('class="timeline"'));
});

test('module page (H4): an earlier-format handoff keeps its parts and sections, with its chips behind a Basis button, not in the prose', () => {
  const r = report(), parts = r.reportParts(OUT).map(p => p[0]);
  assert.deepEqual(parts, NINE);
  const html = r.moduleReport(OUT);
  assert.ok(html.includes('class="band"') && html.includes('Leverage rose.') && html.includes('Liquidity is <strong>ample</strong> through FY2025.') && html.includes('Debt register'));
  assert.ok(!/class="chips"/.test(r.reportAnalysis(OUT)) && countOf(r.reportAnalysis(OUT), /class="basis-link"/g) === 0, 'no chip in prose; no citation and no chip in the build, so no Basis button');
});

test('module page: s-<line> routes are the finding and drawing sections the page draws; a passage is a part, Request, Sources and Calculations are not routes', () => {
  const page = fixturePage(), cp2 = page.drawnAnchors(outId('CP-2'));
  assert.deepEqual([...cp2], [], 'CP-2 has only passages and Evidence sections (Request line 3, Sources, Calculations line 44, Gaps, Next module)');
  assert.deepEqual([...page.drawnAnchors(outId('CP-1'))], ['s-19'], 'CP-1 draws its Canonical data section (line 19)');
});

test('module page: a chart, map or events section is routable whatever its heading\'s role, including one placed under ## Gaps', () => {
  const chart = (line, heading) => sec(heading, 3, line, 'view', [table(line + 2, ['Period', 'Debt maturing', 'Reporting unit', 'Basis and limitation'], [[line + 3, 'FY2025', '93', 'US$m', 'Schedule.']])]);
  const sections = [...passageSections({ bottom: 'Refinancing decides the view.', key: ['- Debt is due soon.'], limits: ['- None stated.'] }),
    sec('Gaps', 2, 40, 'view', []), chart(44, 'Chart data: maturities under gaps'),
    sec('Calculations', 2, 60, 'view', []), chart(64, 'Chart data: maturities under calculations')];
  const page = runPage(() => {
    const d = overviewData({ 'CP-2': sections });
    d[outId('CP-2')].charts = [{ title: 'Maturities', unit: 'US$m', table: 46, columns: [1] }, { title: 'Maturities again', unit: 'US$m', table: 66, columns: [1] }];
    return d;
  }, [], m => m, { record: steps(['CP-2']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES });
  assert.deepEqual([...page.drawnAnchors(outId('CP-2'))].sort(), ['s-44', 's-64'], 'each drawn chart section has its s-<line> route, under Gaps or Calculations too');
});

test('navigator (decision 5): nothing collapses and nothing persists: no expandedGroups, no details in the navigator code or markup, the Browse modules toggle remains', () => {
  const screen = read('screen.js'), views = read('views.js');
  assert.ok(!screen.includes('expandedGroups') && !screen.includes('module-catalogue') && !screen.includes('nav-group'));
  const navigator = views.slice(views.indexOf('function navigatorGroups'), views.indexOf('const moduleHref='));
  assert.ok(navigator.length > 500 && !/details|summary/.test(navigator));
  assert.ok(!/<details|<summary/.test(read('index.html')) && read('index.html').includes('id="module-toggle"') && screen.includes("$('module-toggle').addEventListener('click'"));
});

// A module with saved outputs and no default (two unnumbered variants): counted, listed as a choose line, never given an output by the page.
const CP0_TWO = modules => ({ ...modules, 'CP-0': { outputs: [`${RUN}/deliveries/d1/CP-0-a.md`, `${RUN}/deliveries/d1/CP-0-b.md`], default: null } });

// Live run activity: pull the live functions (from the Run activity comment to workspaceView) out of views.js.
const liveFns = () => {
  const text = read('views.js');
  const start = text.indexOf('// Run activity (ruling decision 10)'), end = text.indexOf('function workspaceView(');
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const dates = text.slice(0, text.indexOf('// ---- Names, not codes')); // displayDate and its month names, as the page has them
  return new Function('esc', 'icon', 'window', 'pathwayTitle', `${dates}${text.slice(start, end)}; return {liveActivityView, nextActivityReload, swapActivityScript, activityView, activityEnded, refreshElapsed, elapsedLabel, liveStampText};`)(esc, n => `<img src="icons/${n}.svg">`, { Components: require('./components.js') }, require('./reader.js').pathwayTitle);
};
const { liveActivityView, nextActivityReload, swapActivityScript, activityView: activityViewLive, activityEnded, refreshElapsed, elapsedLabel, liveStampText } = liveFns();

// ---- Run activity (library redesign, Task 12): C13 steps and C31 marks per run, a clock on the running module only, C23 when a run ends, C32 states.
const NOW = Date.parse('2026-11-09T14:00:00Z');
const STARTED = '2026-11-09T13:41:00Z'; // 19 minutes before NOW
const running = (extra = {}) => ({ id: 'r1', status: 'running', issuer_name: 'Acme', pathway: 'credit_snapshot', submitted_by: 'Dana', started_at: STARTED, folder: 'acme-2026-11-09-abc', files: ['a.pdf', 'b.pdf', 'c.pdf'], modules: [['CP-0', 'done'], ['CP-1', 'running'], ['CP-2', 'waiting']], ...extra });

test('live run activity draws one card per running run: name, pathway, submitter, start, the run mark, then the steps; escapes names; draws no finished run or link to a report', () => {
  const html = liveActivityView({ runs: [running({ issuer_name: '<img src=x onerror=1>' }), { id: 'b', status: 'finished', issuer_name: 'Initech' }] }, NOW);
  assert.ok(!html.includes('<img') && html.includes('&lt;img'));
  assert.ok(html.includes('Updated') === false, 'no updated stamp when the data has none');
  assert.ok(!html.includes('Initech') && !html.includes('<a '), 'a finished run is not drawn, and no run links to a report');
  assert.strictEqual(countOf(html, /<li class="run-card /g), 1);
  const card = html.slice(html.indexOf('<li class="run-card'));
  assert.ok(card.includes('<span class="run-path">Full credit assessment</span>') && card.includes('<span class="run-by">submitted by Dana</span>') && card.includes('<span class="run-time">started 9 November 2026, 13:41 UTC</span>'));
  assert.ok(card.indexOf('rmark running') < card.indexOf('class="steps-w"'), 'the run mark comes before the steps');
  assert.ok(!card.includes('<progress'), 'C13 steps replace the progress bar');
});
test('the steps are the run modules in the data order; each carries its name and its C31 mark; only the running module carries the loader and the elapsed time', () => {
  const html = liveActivityView({ runs: [running()] }, NOW);
  const items = [...html.matchAll(/<li class="step (\w+)">(.*?)<\/li>/g)];
  assert.deepEqual(items.map(m => m[1]), ['done', 'running', 'waiting']);
  assert.deepEqual(items.map(m => m[2].match(/<span class="st-n">(.*?)<\/span>/)[1]), ['CP-0', 'CP-1', 'CP-2']);
  assert.ok(items[0][2].includes('rmark done') && items[1][2].includes('rmark running') && items[2][2].includes('rmark queued'));
  for (const i of [0, 2]) assert.ok(!items[i][2].includes('lat') && !items[i][2].includes('steps-el'), 'done and waiting modules carry neither a loader nor a clock');
  assert.strictEqual(countOf(html, /class="steps-el"/g), 1, 'one clock');
  assert.strictEqual(countOf(items[1][2], /class="lat"/g), 1, 'the loader is on the running module');
  assert.ok(items[1][2].includes('<span class="steps-el" data-since="2026-11-09T13:41:00Z"> · 19 min into the run</span>'), html);
  assert.ok(html.includes('<span class="steps-n">1 of 3 done</span>'));
  // The loaders on a card are bounded: the run mark and the running step, exactly two; a card with no running module draws none.
  assert.strictEqual(countOf(html, /class="lat"/g), 2, 'a running card: the run mark and the running step, no more');
  const idle = liveActivityView({ runs: [{ id: 'q1', status: 'queued', issuer_name: 'Qone', modules: [['CP-0', 'waiting'], ['CP-1', 'waiting']] }] }, NOW);
  assert.strictEqual(countOf(idle, /class="lat"/g), 0, 'a card with no running module carries no loader');
});
test('each module state is carried as a mark with its word, not by colour alone and not by hover', () => {
  const html = liveActivityView({ runs: [running({ modules: [['A', 'done'], ['B', 'waiting'], ['C', 'done'], ['D', 'running'], ['E', 'odd']] })] }, NOW);
  const items = [...html.matchAll(/<li class="step (\w+)">(.*?)<\/li>/g)];
  assert.strictEqual(items.length, 5);
  for (const [, , inner] of items) assert.ok(/<svg class="i"|class="lat"/.test(inner) && /<span class="state-w">(Done|Running|Waiting)<\/span>/.test(inner), inner);
  assert.ok(!/data-tip|tabindex/.test(html.match(/<ol class="steps.*?<\/ol>/)[0]), 'the state is not a tooltip');
  assert.deepEqual(items.map(m => m[2].match(/state-w">(\w+)</)[1]), ['Done', 'Waiting', 'Done', 'Running', 'Waiting']);
});
test('the library home keeps the unlabelled segments: the labelled form is an option of runSteps', () => {
  const C = require('./components.js');
  const plain = C.runSteps([{ title: 'A', state: 'done' }, { title: 'B', state: 'running' }]);
  assert.ok(plain.includes('<li class="step done" data-tip=') && !plain.includes('st-n') && plain.includes('steps-k'));
  const labelled = C.runSteps([{ title: 'A', state: 'done' }, { title: 'B', state: 'running' }], { labelled: true });
  assert.ok(labelled.includes('<span class="st-n">A</span>') && labelled.includes('rmark done'));
  assert.ok(/libraryLive[\s\S]*window\.Components\.runSteps\(steps\)/.test(read('views.js')), 'the home calls runSteps with no option');
});
test('no start time, or one that is not a dated time with a zone: no elapsed time, and nothing reads NaN, undefined or 0', () => {
  for (const started_at of [undefined, null, '', 'yesterday', '1', 5, {}, '2026-11-09T13:41:00', '2026-11-09T14:30:00Z']) {
    const html = liveActivityView({ runs: [running({ started_at, files: [], folder: undefined })] }, NOW);
    assert.ok(html.includes('class="step running"'), String(started_at));
    assert.ok(!html.includes('steps-el') && !html.includes('data-since'), `${started_at}: no clock`);
    for (const word of ['NaN', 'undefined', 'null', 'Infinity']) assert.ok(!html.includes(word), `${started_at}: ${word}`);
    assert.ok(!/(?<!\d)0(?!\d)/.test(html.replace(/<dl.*?<\/dl>/, '').replace(/\bCP-0\b/g, '').replace(/<[^>]*>/g, ' ')), `${started_at}: a bare 0 outside the counts`);
  }
  assert.strictEqual(elapsedLabel('2026-11-09T13:59:30Z', NOW), 'under a minute');
  assert.strictEqual(elapsedLabel('2026-11-09T12:55:00Z', NOW), '1 h 5 min');
  assert.strictEqual(elapsedLabel('2026-11-09T13:00:00Z', NOW), '1 h');
  assert.strictEqual(elapsedLabel('2026-11-09T13:41:00+00:00', NOW), '19 min');
  assert.strictEqual(elapsedLabel('2026-11-09 13:41:00+00:00', NOW), '19 min');
  assert.strictEqual(elapsedLabel('not a time', NOW), '');
  // Clock skew: a start up to five minutes ahead of this clock reads under a minute; further ahead draws nothing.
  assert.strictEqual(elapsedLabel('2026-11-09T14:03:00Z', NOW), 'under a minute');
  assert.strictEqual(elapsedLabel('2026-11-09T14:05:00Z', NOW), 'under a minute');
  assert.strictEqual(elapsedLabel('2026-11-09T14:05:01Z', NOW), '');
  const skewed = liveActivityView({ runs: [running({ started_at: '2026-11-09T14:03:00Z' })] }, NOW);
  assert.ok(skewed.includes('data-since="2026-11-09T14:03:00Z"> · under a minute into the run'), 'carries data-since so the re-load moves it');
  const el = { textContent: '', getAttribute: () => '2026-11-09T14:03:00Z' };
  refreshElapsed({ querySelectorAll: () => [el] }, NOW + 8 * 60000);
  assert.strictEqual(el.textContent, ' · 5 min into the run');
  assert.strictEqual(liveStampText('2026-11-13T07:56:30Z'), '13 November 2026, 07:56 UTC');
  assert.strictEqual(liveStampText('2026-11-13 07:56:30+01:00'), '13 November 2026, 07:56 +01:00');
  for (const raw of ['2026-11-13T25:70:00Z', '2026-11-13T24:30:00Z', '2026-11-13T07:60:00Z', '2026-11-13T07:56:00+25:99', '2026-11-13T07:56:00+01:60', 'T', 'yesterday', '2026-02-30T07:56:00Z', '2026-11-13T07:56:30', '<b>']) assert.strictEqual(liveStampText(raw), raw);
});
test('a run with no module running draws no clock, and the clock moves on a re-load without drawing the page again', () => {
  assert.ok(!liveActivityView({ runs: [running({ modules: [['CP-0', 'waiting']] })] }, NOW).includes('steps-el'));
  assert.ok(!/data-since/.test(liveActivityView({ runs: [running({ modules: [['CP-0', 'done']] })] }, NOW)));
  const el = { textContent: ' · 19 min into the run', getAttribute: () => STARTED };
  refreshElapsed({ querySelectorAll: sel => (sel === '[data-since]' ? [el] : []) }, NOW + 5 * 60000);
  assert.strictEqual(el.textContent, ' · 24 min into the run');
  assert.ok(!read('views.js').includes('setInterval') && !read('screen.js').includes('setInterval'), 'no per-second timer');
});
test('a stalled running run carries the Stalled mark in words and no loader; a healthy one carries the loader', () => {
  const stalled = liveActivityView({ runs: [running({ stalled: true })] }, NOW);
  assert.ok(stalled.includes('rmark stalled') && stalled.includes('<span class="state-w">Stalled</span>') && !stalled.includes('rmark running') && !stalled.includes('class="lat"'));
  assert.ok(liveActivityView({ runs: [running()] }, NOW).includes('rmark running'));
});
test('the page shows no spend, cap or cost figure for any shape of those fields', () => {
  for (const spent of ['3.10', null, undefined, 3.1, '<b>']) {
    for (const status of ['running', 'queued']) {
      const html = liveActivityView({ cap: '20', cost: '1.2', runs: [running({ status, spent, cost: spent, held: spent })] }, NOW);
      const text = html.replace(/<svg.*?<\/svg>/g, '').replace(/<[^>]*>/g, ' ').toLowerCase();
      for (const word of ['usd', 'spend', 'spent', 'cap', 'cost', '3.10', ' of 20']) assert.ok(!text.includes(word), `${status} ${spent}: ${word}`);
    }
  }
  assert.ok(!read('views.js').includes('liveRunSpend') && !read('screen.css').includes('run-spend'));
});
test('the held reason is a notice above the lists, drawn once with a warning mark and the text; nothing when absent or not a string', () => {
  const HELD = 'the library could not be rebuilt (disk full); ended runs wait for it';
  const html = liveActivityView({ cap: '20', held: HELD, runs: [{ id: 'q', status: 'queued', issuer_name: 'Q' }] }, NOW);
  assert.strictEqual(countOf(html, /class="run-held"/g), 1);
  assert.strictEqual(countOf(html, new RegExp(HELD.replace(/[()]/g, '\\$&'), 'g')), 1);
  assert.ok(/<p class="run-held" role="note"><svg class="i"[^>]*>.*?<\/svg><span>the library could not be rebuilt/.test(html), html);
  assert.ok(html.indexOf('run-held') < html.indexOf('<section'), 'above the lists');
  assert.ok(!html.includes('20'), 'no cap figure');
  assert.ok(liveActivityView({ held: '<b>x</b>', runs: [] }, NOW).includes('&lt;b&gt;x&lt;/b&gt;'), 'escaped');
  for (const held of [undefined, null, '', '  ', 5, {}, [], true]) assert.ok(!liveActivityView({ held, runs: [{ id: 'q', status: 'queued' }] }, NOW).includes('run-held'), JSON.stringify(held));
  assert.ok(activityViewLive({ held: HELD, runs: [] }, NOW).includes('class="run-held"'), 'drawn on the empty page too');
});
test('no run folder, run code, run id or source file name is drawn; the file count is the number of files listed', () => {
  const html = liveActivityView({ runs: [running({ files: ['one.pdf', 'two.xlsx', 'three.pdf', 'four.pdf', 'five.pdf', 'six.pdf', 'seven.pdf', null, { a: 1 }] }), { id: 'q-77', status: 'queued', issuer_name: 'Qone', folder: 'qone-2026-folder', files: ['only.pdf'] }] }, NOW);
  for (const gone of ['acme-2026-11-09-abc', 'qone-2026-folder', 'one.pdf', 'seven.pdf', 'only.pdf', 'q-77', 'r1', 'data-run', '<details', 'class="code"']) assert.ok(!html.includes(gone), gone);
  assert.ok(html.includes('7 source files') && html.includes('1 source file<'), html);
  const bare = liveActivityView({ runs: [running({ files: undefined, issuer_name: undefined })] }, NOW);
  assert.ok(!bare.includes('source file') && !bare.includes('acme-2026') && bare.includes('Issuer not named'));
});
test('waiting runs are a compact list: the queued mark, name, pathway and submitter; a stalled one carries the word Stalled', () => {
  const html = liveActivityView({ runs: [
    { id: 'q1', status: 'queued', pathway: 'credit_snapshot', issuer_name: 'Qone', submitted_by: 'Dana', reason: 'waiting for a slot' },
    { id: 'q2', status: 'queued', pathway: 'earnings_update', issuer_name: 'Qtwo', stalled: true },
    running({ issuer_name: 'Runner' })] }, NOW);
  assert.ok(!html.includes('<table') && !html.includes('<th'), 'a list, not a grid');
  const rows = html.split('<li class="live-run live-queued').slice(1);
  assert.strictEqual(rows.length, 2);
  assert.ok(rows[0].includes('rmark queued') && rows[0].includes('Qone') && rows[0].includes('Full credit assessment') && rows[0].includes('submitted by Dana') && rows[0].includes('waiting for a slot') && !rows[0].includes('Stalled'));
  assert.ok(rows[1].includes('rmark stalled') && rows[1].includes('<span class="state-w">Stalled</span>') && !rows[1].includes('rmark queued'));
  assert.ok(html.indexOf('Runner') < html.indexOf('Qone'), 'Running comes first');
});
test('the counts show running and waiting as numbers under their labels', () => {
  const run = (status, n) => Array.from({ length: n }, (_, i) => ({ id: `${status}${i}`, status, issuer_name: `N${i}` }));
  const html = liveActivityView({ runs: [...run('running', 2), ...run('queued', 3), ...run('finished', 4)] }, NOW);
  assert.ok(html.includes('<dl class="run-tally"><div><dt>Running</dt><dd>2</dd></div><div><dt>Waiting</dt><dd>3</dd></div></dl>'), html);
});
test('nothing running or waiting is the C32 empty state with the one library link; the counts stay', () => {
  const empty = activityViewLive({ runs: [{ status: 'finished', issuer_name: 'Finisher' }] }, NOW);
  assert.ok(empty.includes('<div class="empty-state"') && empty.includes('class="es-t">No run in progress') && !empty.includes('Finisher'));
  assert.ok(empty.includes('<dt>Running</dt><dd>0</dd>') && empty.includes('<dt>Waiting</dt><dd>0</dd>'));
  assert.ok(empty.includes('No run is running or waiting. Finished runs are in the Issuer library.'));
  assert.strictEqual(countOf(empty, /<a /g), 1);
  assert.ok(empty.includes('<a class="primary-action" href="#W-Library/cases">Issuer library</a>'));
});
test('unreadable run activity is the C32 empty state: it says to reload, points at the library, and claims nothing about runs', () => {
  const unread = activityViewLive(null, NOW);
  assert.ok(unread.includes('<div class="empty-state"') && unread.includes('class="es-t">Run activity could not be read</p>'));
  assert.ok(/Reload this page/.test(unread) && unread.includes('Finished runs are in the Issuer library.') && unread.includes('href="#W-Library/cases"'));
  assert.ok(!unread.includes('<dl') && !unread.includes('No run in progress') && !/is running|are running/.test(unread));
  assert.ok(!read('views.js').includes('No live run data was supplied'), 'the old wording is gone');
});
test('a column holding no run is not drawn, and a single column takes the full width', () => {
  const only = status => liveActivityView({ runs: [{ id: 'a', status, issuer_name: 'N' }] }, NOW);
  assert.ok(only('running').includes('class="activity-cols one"') && !only('running').includes('<h2>Waiting</h2>'));
  assert.ok(only('queued').includes('class="activity-cols one"') && !only('queued').includes('<h2>Running</h2>'));
  assert.ok(liveActivityView({ runs: [{ status: 'running' }, { status: 'queued' }] }, NOW).includes('class="activity-cols"'));
});
test('malformed input of each kind throws nothing and draws no invented state', () => {
  const x = '<script>alert(1)</script>';
  for (const bad of [null, undefined, 5, 'x', [], {}, { runs: 'no' }, { runs: {} }, { runs: null }]) {
    assert.doesNotThrow(() => activityViewLive(bad, NOW), String(bad));
    assert.strictEqual(liveActivityView(bad, NOW), '', String(bad));
    const html = activityViewLive(bad, NOW);
    assert.ok(!html.includes('rmark') && !html.includes('run-card') && !html.includes('class="steps"'), `${bad}: no state drawn`);
  }
  const odd = liveActivityView({ updated: x, runs: [null, 3, 'r', [], { status: 'running', issuer_name: x, pathway: x, submitted_by: x, started_at: x, reason: x, name_differs: true, files: [x, { a: 1 }, null],
    modules: [[x, 'done'], [x, x], 'bad', [x], null, [{ a: 1 }, 'running'], [], [7, 'running']] }, { status: 'queued', issuer_name: x, pathway: x, submitted_by: x, reason: x }] }, NOW);
  assert.ok(!odd.includes('<script') && odd.includes('&lt;script&gt;'));
  assert.ok(!odd.includes('NaN') && !odd.includes('undefined') && !odd.includes('[object'));
  for (const status of [undefined, null, 'paused', 'RUNNING', 7, {}, ['running']]) {
    const html = liveActivityView({ runs: [running({ status })] }, NOW);
    assert.ok(!html.includes('<li') && !html.includes('rmark') && !html.includes('steps-w'), `status ${JSON.stringify(status)} is not a live run`);
  }
  assert.ok(liveActivityView({ runs: [running({ modules: 'CP-0' }), running({ modules: [null, 4, 'x'] })] }, NOW).includes('rmark running'), 'a run with no usable module list is its mark alone');
  assert.ok(!liveActivityView({ runs: [running({ modules: [null, 4, 'x'] })] }, NOW).includes('steps-w'));
});
test('a run that was running on the previous load and has ended on this one gives exactly one toast in the words the data supports', () => {
  const was = activityEnded(null, { runs: [running(), running({ id: 'r2', issuer_name: 'Beta' }), running({ id: 'r3', issuer_name: 'Gamma' }), running({ id: 'r4', issuer_name: 'Delta' })] });
  assert.deepEqual(was.toasts, [], 'the first load toasts nothing');
  assert.deepEqual(was.running.map(r => r.id), ['r1', 'r2', 'r3', 'r4']);
  const next = activityEnded(was.running, { runs: [running({ status: 'finished' }), running({ id: 'r2', status: 'failed', issuer_name: 'Beta' }), running({ id: 'r3', issuer_name: 'Gamma' }), running({ id: 'r4', status: 'capped', issuer_name: 'Delta' }), { id: 'q', status: 'queued', issuer_name: 'Zed' }] });
  assert.deepEqual(next.toasts, [
    { text: 'Acme: run finished. Reload to see it in the Issuer library.', action: { label: 'Reload', href: '#W-Library/cases' } },
    { text: 'Beta: run failed.' },
    { text: 'Delta: run did not finish.' }]);
  assert.deepEqual(next.running.map(r => r.id), ['r3'], 'the previous set is replaced by this load\'s');
  assert.deepEqual(activityEnded(next.running, { runs: [running({ id: 'r3', issuer_name: 'Gamma' })] }).toasts, [], 'a run still running gives none');
  assert.deepEqual(activityEnded(next.running, { runs: [{ id: 'r3', status: 'finished', issuer_name: 'Gamma' }, { id: 'r3', status: 'finished', issuer_name: 'Gamma' }] }).toasts.length, 1, 'one toast per run');
  assert.deepEqual(activityEnded(next.running, { runs: [] }).toasts, [], 'a run that left the data is not claimed finished');
  assert.deepEqual(activityEnded([{ id: 'r9', name: '' }], { runs: [{ id: 'r9', status: 'finished' }] }).toasts.map(t => t.text), ['Run finished. Reload to see it in the Issuer library.']);
});
test('malformed data on a re-load keeps the previous running set and toasts nothing', () => {
  const prior = [{ id: 'r1', name: 'Acme' }];
  for (const bad of [null, undefined, [], { runs: 'no' }, 5]) {
    const out = activityEnded(prior, bad);
    assert.deepEqual(out.toasts, []);
    assert.strictEqual(out.running, prior);
  }
  assert.deepEqual(activityEnded(prior, { runs: [null, 3, { status: 'finished' }] }).toasts, [], 'a run with no id is never matched');
});
test('screen.js raises each toast through Components.toast and moves the clock on a re-load', () => {
  const screen = read('screen.js');
  const handler = screen.slice(screen.indexOf('window.onRunActivity='), screen.indexOf("window.addEventListener('hashchange',syncActivityTimer)"));
  assert.ok(handler.includes('activityEnded(previousRunning,live)') && handler.includes('window.Components.toast(') && handler.includes('refreshElapsed('));
  assert.ok(handler.includes('JSON.stringify([live?.runs,live?.held])'), 'a changed held reason redraws the page');
  assert.ok(handler.includes('liveStampText(live.updated)'), 'the snapshot time is written as the page draws it');
  assert.ok(handler.includes('location.reload()') && handler.includes("location.hash=note.action.href"), 'the Reload control sets the hash and reloads');
  assert.ok(screen.includes('let previousRunning=null;'), 'the previous set is in memory only');
  assert.ok(!/localStorage|sessionStorage/.test(handler));
  // The file loaded with the page is the first load: the running set is taken from it at start, so a run that ends before the first re-load is announced.
  const seed = screen.indexOf('previousRunning=activityEnded(null,window.RUN_ACTIVITY).running;');
  assert.ok(seed > 0 && seed < screen.indexOf('syncActivityTimer(true);'), 'the page start seeds the previous set');
});
test('motion: every animation on the page sits inside the reduced-motion no-preference query, and only the running mark and the running step move', () => {
  const css = read('screen.css');
  const blocks = [];
  let outside = '', at = 0;
  for (const open of css.matchAll(/@media\s*\(prefers-reduced-motion:\s*no-preference\)\s*\{/g)) {
    if (open.index < at) continue;
    let depth = 1, i = open.index + open[0].length;
    while (depth && i < css.length) depth += css[i] === '{' ? 1 : css[i] === '}' ? -1 : 0, i++;
    blocks.push(css.slice(open.index + open[0].length, i - 1));
    outside += css.slice(at, open.index);
    at = i;
  }
  outside += css.slice(at);
  assert.ok(blocks.length >= 3, 'the no-preference blocks were found');
  for (const sel of ['.lat', '.step', '.rmark', '.steps', '.run-card', '.run-queue', '.steps-el']) {
    const hit = cssRules(outside).filter(r => r.selector.includes(sel) && /(?:^|[;\s])animation(?:-name)?\s*:\s*(?!none)/.test(r.body));
    assert.deepEqual(hit, [], `${sel} animates outside the no-preference query`);
  }
  const inside = blocks.join('\n');
  assert.ok(/\.rmark\.running \.lat i\{animation:lat-orbit/.test(inside) && /\.step\.running\{animation:step-pulse/.test(inside), 'the loader and the running step animate in the query');
  assert.ok(!/\.(?:run-card|run-queue|run-who|empty-state|steps-el)[^{]*\{[^}]*animation:(?!none)/.test(inside), 'nothing else on the page moves');
  assert.ok(/\.run-card\.stalled \.step\.running\{animation:none\}/.test(inside), 'a stalled run does not pulse');
});
test('the toast control can be hit by a pointer and looks like a control on the navy toast; no dead anchor rule remains', () => {
  const css = read('screen.css'), rules = cssRules(css);
  const hit = rules.filter(r => r.selector.split(',').some(s => s.trim() === '.toast button'));
  assert.ok(hit.some(r => /pointer-events:auto/.test(r.body)), 'the host is pointer-events:none, so the button turns it back on');
  assert.ok(hit.some(r => /(?:^|;)color:/.test(r.body)) && rules.some(r => r.selector.includes('.toast button:focus-visible') && /outline:/.test(r.body)));
  assert.ok(!/\.toast a\b/.test(css), 'the toast draws no anchor');
  assert.ok(!/createElement\('a'\)/.test(read('components.js').slice(read('components.js').indexOf('function toast('), read('components.js').indexOf('function dismissToasts'))));
});
test('long unbroken values wrap in the step caption, the module names and the run notes', () => {
  const rules = cssRules(read('screen.css'));
  for (const sel of ['.steps-t', '.st-n', '.run-reason', '.run-foot-notes', '.run-held']) {
    assert.ok(rules.some(r => r.selector.split(',').map(s => s.trim()).includes(sel) && /overflow-wrap:anywhere/.test(r.body)), sel);
  }
});
test('Run activity styles: a bordered card, a queue of rows, a wrapped line at 390px, a focus ring on the library link', () => {
  const css = read('screen.css');
  const rule = sel => { const m = css.match(new RegExp(`(?:^|\\n)${sel.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&')}\\{([^}]*)\\}`)); assert.ok(m, sel); return m[1]; };
  assert.ok(/border-radius:12px/.test(rule('.run-card')) && rule('.run-card').includes('var(--shadow-xs)') && rule('.run-card').includes('var(--border-secondary)'));
  assert.ok(rule('.run-queue').includes('list-style:none') && /min-width:0/.test(rule('.run-queue li')));
  assert.ok(css.includes('grid-template-columns:minmax(0,1fr) 440px'));
  const who = cssRules(css).filter(r => r.selector.split(',').some(s => ['.run-who', '.run-who strong'].includes(s.trim())));
  assert.ok(who.some(r => r.selector === '.run-who' && /min-width:0/.test(r.body)) && who.some(r => r.selector === '.run-who strong' && /overflow-wrap:anywhere/.test(r.body)), '390px: a long name wraps');
  assert.ok(/@media\(max-width:720px\)\{[^\n]*\.run-queue li\{grid-template-columns:minmax\(0,1fr\)/.test(css), 'a queue row is one column on a phone');
  assert.ok(!/run-(badge|tag|tally|done|primary)[^{]*\{[^}]*Red Hat Display/.test(css), 'Red Hat Text only');
});
test('no live activity adds nothing', () => { assert.strictEqual(liveActivityView(undefined), ''); });

test('malformed live activity shows nothing and does not throw', () => {
  for (const bad of [null, 5, 'x', [], {}, { runs: 'no' }, { runs: {} }]) assert.strictEqual(liveActivityView(bad), '');
  const html = liveActivityView({ runs: [null, 3, [], {}, { status: 'queued' }] });
  assert.ok(html.includes('Waiting'));
});

test('live sections: waiting shows the reason, the held note and the name warning, all escaped; an ended run is not drawn', () => {
  const html = liveActivityView({ cap: '20', held: 'daily limit <b>reached</b>', runs: [
    { id: 'q', status: 'queued', pathway: 'p', folder: 'f', issuer_name: 'Q', reason: '<script>x</script>', name_differs: true, stalled: true },
    { id: 'e', status: 'failed', pathway: 'p', folder: 'f', issuer_name: 'E', ended_at: 'T' }] }, NOW);
  assert.ok(html.includes('daily limit &lt;b&gt;reached') && !html.includes('<b>') && !html.includes('<script>'));
  assert.ok(html.includes('&lt;script&gt;x') && html.includes('issuer name differs from earlier runs') && html.includes('<span class="state-w">Stalled</span>'));
  assert.ok(!html.includes('>E<') && !html.includes('Ended') && !html.includes('run-status'));
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
    assert.doesNotThrow(() => activityViewLive(live));
  }
  assert.ok(activityViewLive({ runs: [{ status: 'running', folder: { toString: 1 }, issuer_name: 'Kept' }] }).includes('Kept'));
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

test('a status adds no class names to the row; only running and queued runs have one', () => {
  const rows = status => [...liveActivityView({ runs: [{ status, folder: 'f' }] }).matchAll(/<(?:li|tr) class="((?:run-card|live-run)[^"]*)"/g)].map(m => m[1]);
  assert.deepEqual(rows('running'), ['run-card live-run live-running']);
  assert.deepEqual(rows('queued'), ['live-run live-queued']);
  for (const other of ['x sr-only skip', '__proto__', 'finished', 'failed', 'capped', 'rejected', 'interrupted']) assert.deepEqual(rows(other), [], other);
});

test('unchanged data is not re-rendered; the clock and the snapshot time still move; a changed run list is drawn again', () => {
  const screen = read('screen.js');
  const handler = screen.slice(screen.indexOf('window.onRunActivity='), screen.indexOf("window.addEventListener('hashchange',syncActivityTimer)"));
  assert.ok(handler.includes('JSON.stringify'));
  assert.ok(!screen.includes('recordActivityView') && !screen.includes('restoreActivityView'), 'no file lists are drawn, so none is restored');
  // Run the real handler against stubs: same runs again => no replacement, only the stamp text and the clock change.
  const content = { scrollTop: 0, writes: 0, stamp: { textContent: '' }, set innerHTML(v) { this.writes++; }, get innerHTML() { return ''; }, querySelector: () => content.stamp, querySelectorAll: () => [] };
  const win = { RUN_ACTIVITY: { updated: 'T1', runs: [{ id: 'a' }] }, Components: { toast: () => {} } };
  const clock = [];
  const fn = new Function('window', 'document', '$', 'moduleBody', 'nameCodes', 'nextActivityReload', 'state', 'keepsCodes', 'activityEnded', 'refreshElapsed', 'Date', 'liveStampText',
    `${screen.slice(screen.indexOf('let lastActivity'), screen.indexOf('window.onRunActivity=')).replace(/\bcurrent\b/g, 'state.current')}${handler.replace(/\bcurrent\b/g, 'state.current')}; return window.onRunActivity;`)(
    win, {}, () => content, () => 'body', () => {}, () => 30000, { current: { module: 'CP-OS' } }, () => false, (previous, live) => ({ toasts: [], running: live.runs }), (root, now) => clock.push(now), { now: () => 99 }, v => v);
  fn(); assert.strictEqual(content.writes, 1);
  win.RUN_ACTIVITY = { updated: 'T2', runs: [{ id: 'a' }] }; fn();
  assert.strictEqual(content.writes, 1, 'unchanged runs: no replacement'); assert.strictEqual(content.stamp.textContent, 'T2'); assert.deepEqual(clock, [99], 'the clock moves on the re-load');
  win.RUN_ACTIVITY = { updated: 'T3', runs: [{ id: 'a', status: 'running' }] }; fn();
  assert.strictEqual(content.writes, 2, 'changed runs: replaced');
});

// Design pass 2026-11-10 (docs/design/2026-11-10-impeccable-pass.md).

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
  assert.equal(runPage().chartCards(['<div class="section-heading"><h2>Leverage</h2><span>x</span></div><h2>kept</h2>']), '<div class="panel-card"><div class="section-heading"><h4>Leverage</h4><span>x</span></div><h2>kept</h2><div class="legend"><span>Chip dot: <i class="dot"></i> issuer page · <i class="dot row"></i> this table row · <i class="dot up"></i> another module · <i class="dot gap"></i> gap</span></div></div>');
});

test('screen.css: the run page tables (status map) run whole', () => {
  const css = read('screen.css');
  assert.ok(css.includes('.run-section .table-scroll{max-height:none;overflow:clip}'));
});

test('hardening: the module report\'s section title is an h2, fold arrows respect reduced motion, the page prints whole', () => {
  const screen = read('screen.js'), css = read('screen.css');
  assert.ok(screen.includes("const level=report?'h2':'h3';"));
  assert.ok(/@media\(prefers-reduced-motion:reduce\)\{[^}]*details\.fold>summary img[^}]*\{transition:none\}/.test(css));
  assert.ok(/@media print\{[^@]*#content\{[^}]*overflow:visible/.test(css));
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

test('screen.css (decision 5): a module-page table box shows a scroll shadow, may wrap its headers and takes the keyboard; a fenced block keeps its lines', () => {
  const css = read('screen.css');
  const box = /\.analysis-section \.table-card\{background:([^}]*)\}/.exec(css);
  assert.ok(box && /local/.test(box[1]) && /scroll/.test(box[1]), 'local covers over scroll shadows');
  assert.ok(css.includes('.analysis-section .table-card:focus-visible{') && css.includes('.analysis-section .table-card thead th{white-space:normal'));
  assert.ok(/\.passage-code\{[^}]*white-space:pre/.test(css));
});

test('library: a row is one item per column; what left the row is the cell title or the selected-run panel', () => {
  const { libraryRow } = runPage();
  const metric = (value, basis) => ({ value, unit: 'x', basis, period: 'FY2024' });
  const run = { id: 'run-z', name: 'Zed & Sons', issuer: 'ZED', title: 'Credit Snapshot', sector: 'Telecoms', date: '2024-09-30', period: 'FY-2024', completion: null, artifacts: [],
    metrics: { leverage: metric('6.5744', 'C9; same "basis"'), net_leverage: metric('0', 'Net of cash'), coverage: null }, ratings: [{ label: 'B+', agency: 'S&P', scope: 'issuer', date: '2024-06-30' }] };
  const cells = [...libraryRow(run, true, false).matchAll(/<td([^>]*)>(.*?)<\/td>/g)].map((m) => [m[1].trim(), m[2]]);
  // Ten columns, in the header's order; a cell holds one value and at most the one control that acts on it.
  assert.deepEqual(cells.map(([, body]) => strip(body)), ['Zed &amp; Sons', '30 September 2024 · Not recorded', 'Telecoms', '30 Sept 2024', '6.5744×', '0×', 'n.a.', 'B+', 'Not assessed', 'Handoffs only']);
  assert.ok(cells.every(([, body]) => countOf(body, /<(?!\/)/g) <= 1));
  assert.ok(/^<button class="library-run-name" type="button" data-library-select="0" aria-expanded="true" aria-controls="run-detail"/.test(cells[0][1]), 'a row is chosen by its place in the list: no run code is written into the page');
  // A run the store does not hold has no link; the Run column names it by its date and workflow, never by its code (the column held the run code before library redesign Task 11).
  assert.deepEqual(cells[1], ['class="run-when"', '30 September 2024 · Not recorded']);
  // A ratio's period stays on the cell (its basis is Evidence's); the rating detail stays; a missing figure reads n.a., a zero is a zero.
  assert.equal(cells[4][0], 'title="FY2024"');
  assert.equal(cells[5][0], 'title="FY2024"');
  assert.equal(cells[6][0], 'class="missing" title="Not available"');
  assert.equal(cells[7][0], 'title="S&amp;P · Issuer · 30 Jun 2024"');
  // A run the store holds opens from its name; a percentage and the not-screened note are single items too.
  const held = libraryRow({ ...run, id: RUN, completion: 75, ratings: [] }, false, true);
  const named = 'Not recorded · Not recorded'; // the held run's own period and pathway, as every run page names it
  assert.ok(held.includes(`<td class="run-when"><a href="#W-Overview/overview?c=${RUN}" aria-label="Open run: Zed &amp; Sons, ${named}">${named}</a></td>`), held);
  assert.ok(held.endsWith(`<td class="missing" title="No rating recorded">n.a.</td><td>75%</td><td><a class="report-link" href="#W-Overview/overview?c=${RUN}" aria-label="Open run: Zed &amp; Sons, ${named}">Open run</a> · <a class="report-link" href="#W-Report/history?c=${RUN}" aria-label="Report history: Zed &amp; Sons, ${named}">History</a></td></tr>`), held);
  assert.ok(!held.includes(RUN.toUpperCase()) && !/aria-label="[^"]*run-a/.test(held.replace(/href="[^"]*"/g, '')), 'no run code or folder in the text or the labels');
  // A run the store does not hold has no run to open; the delivered report is not linked.
  assert.ok(libraryRow({ ...run, completion: 75 }, false, true).endsWith('<td>Not screened</td></tr>'));
  const views = read('views.js'), screen = read('screen.js');
  // The selected-run panel carries the ticker, the run's name and the period the row no longer shows (never the run's code); the issuer is a select in the filter bar.
  assert.ok(views.includes("esc(`${run.issuer} · ${when}`)") && !views.includes("${run.id} / ${run.title}") && views.includes("['Evidence date',libraryDate(run.date),run.period]"));
  assert.ok(views.includes('<select id="library-issuer" data-library-filter="issuer">'));
  // The stylesheet right-aligns columns 5 to 7 by position: they are the three ratios.
  assert.ok(views.includes("[['name','Issuer'],[null,'Run'],[null,'Sector'],['date','Evidence date'],['leverage','Leverage'],['net_leverage','Net leverage'],['coverage','Coverage'],['rating','Rating'],['completion','Completeness'],[null,'Open']]"));
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
  assert.ok(/@media print\{[^@]*\.library-table\{min-width:0\}/.test(css));
});

test('library: a file is linked only in the one form the build writes, a retained workspace file; a presented report copy is not one', () => {
  const { libraryPath } = runPage();
  for (const good of ['../runs/run-a/deliveries/9c5b/CP-1.md', '../runs/a_b-c.d~e/x.md']) {
    assert.strictEqual(libraryPath(good), true, good);
  }
  for (const bad of ['reports/run-a/9c5b/report.html', 'reports/A%20B/x/report.html', '/etc/passwd', '/files/runs/a/x.md', '//evil.example/x', 'https://x/y', 'javascript:alert(1)', 'file:///x', 'C:\\x', 'reports/../../x', '../../x', '../runs/../../x',
    'reports/./x', 'reports/%2e%2e/x', '../runs/%2e%2e/x', '../runs/%2E%2E/x', '..%2fx', '../runs/x%2f..%2fy', '../runs/x/%5c..%5cy', 'reports/a\\b', 'reports//x', 'reports/', '../', 'reports', 'x.html',
    'runs/a/x.md', '../runs/a?b', '../runs/a#b', ' ../runs/a', '../runs/a b', '', null, undefined, 7]) {
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

test('reader charts: nine long step labels wrap word-wise inside their step, at most three lines, an ellipsis where cut, the full text in the title', () => {
  const names = ['Opening: FY2024 EBITDA', 'Acquisition transaction and integration-related expenses', 'Non-cash stock and deferred compensation expense', 'Refinancing costs', 'Other, net', 'Restructuring and impairment charges', 'Foreign currency translation effect', 'Share of equity-method investees', 'Closing: FY2024 EBITDA As Defined'];
  const rows = names.map((n, i) => [63 + i, n, i === 0 ? '3813' : i === 8 ? String(3813 + 70 * 7) : '70', 'US$m', 'Synthetic.']);
  const page = runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: liquidity bridge', 3, 60, 'consumed', [table(62, ['Step', 'Amount', 'Reporting unit', 'Basis and limitation'], rows)])); return d; });
  const html = page.readerChart(outId('CP-1'), BRIDGE_CHART);
  const labels = [...html.matchAll(/<text class="axis-label" x="([\d.]+)"[^>]*>(.*?)<\/text>/g)].map(m => ({ x: Number(m[1]), lines: [...m[2].matchAll(/<tspan[^>]*>(.*?)<\/tspan>/g)].map(t => t[1]) }));
  assert.equal(labels.length, 9);
  const CHAR = 14 * 0.6; // monospace advance of the 14px axis label, in viewBox units
  const boxes = labels.map(l => [l.x - Math.max(...l.lines.map(t => t.length)) * CHAR / 2, l.x + Math.max(...l.lines.map(t => t.length)) * CHAR / 2]);
  for (let i = 1; i < boxes.length; i++) assert.ok(boxes[i - 1][1] < boxes[i][0], `labels ${i - 1} and ${i} overprint: ${boxes[i - 1]} ${boxes[i]}`);
  labels.forEach((l, i) => {
    assert.ok(l.lines.length >= 1 && l.lines.length <= 3, l.lines.join('|'));
    // Every word shown is a whole word of the label, or ends in an ellipsis; a label cut anywhere ends in one.
    const words = names[i].split(' ');
    for (const line of l.lines) for (const w of line.split(' ')) assert.ok(w.endsWith('\u2026') || words.includes(w), `${w} is cut without an ellipsis`);
    const shown = l.lines.join(' ');
    assert.equal(shown === names[i] || shown.endsWith('\u2026') || l.lines.some(t => t.includes('\u2026')), true);
    assert.ok(html.includes(`<title>${names[i].replace(/&/g, '&amp;')}: `), 'the full step name is in the title');
  });
  assert.ok(labels[3].lines.join(' ') === 'Refinancing costs' || labels[3].lines.length <= 3);
});

test('reader charts: the real nine-step bridge labels break only between words, unless one word alone exceeds the line', () => {
  const names = ['Net income (reported, US GAAP) FY2024', 'Interest expense-net', 'Income tax provision', 'Depreciation and amortization expense', 'Non-cash stock and deferred compensation expense', 'Acquisition transaction and integration-related expenses', 'Refinancing costs', 'Other, net', 'Issuer As Defined EBITDA'];
  const rows = names.map((n, i) => [63 + i, n, i === 0 ? '1000' : i === 8 ? '1400' : '50', 'US$m', 'Synthetic.']);
  const page = runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: liquidity bridge', 3, 60, 'consumed', [table(62, ['Step', 'Amount', 'Reporting unit', 'Basis and limitation'], rows)])); return d; });
  const html = page.readerChart(outId('CP-1'), BRIDGE_CHART);
  const labels = [...html.matchAll(/<text class="axis-label" x="([\d.]+)"[^>]*>(.*?)<\/text>/g)].map(m => ({ x: Number(m[1]), lines: [...m[2].matchAll(/<tspan[^>]*>(.*?)<\/tspan>/g)].map(t => t[1]) }));
  const step = Number(/<rect class="[^"]*" x="[\d.]+" y="[\d.]+" width="([\d.]+)"/.exec(html)[1]) + 20;
  const room = Math.floor((step - 6) / 8.4);
  assert.ok(html.includes('vector-chart bridge-wide'), 'a many-step bridge takes the card width');
  labels.forEach((l, i) => {
    const words = names[i].split(' ');
    assert.ok(l.lines.length <= 3, l.lines.join('|'));
    for (const w of l.lines.join(' ').split(' ')) {
      const stem = w.replace(/\u2026$/, '');
      if (words.includes(w)) continue;
      assert.ok(w.endsWith('\u2026') && words.some(o => o.startsWith(stem) && (o.length > room || o === stem)), `${names[i]}: "${w}" is cut inside a word`);
    }
    if (words.every(w => w.length <= room) && l.lines.length < 3) assert.ok(!l.lines.join(' ').includes('\u2026'), l.lines.join('|'));
  });
  for (const n of [1, 2, 3, 6, 7]) assert.equal(labels[n].lines.join(' '), names[n], names[n]);
  const boxes = labels.map(l => { const w = Math.max(...l.lines.map(t => t.length)) * 8.4; return [l.x - w / 2, l.x + w / 2]; });
  for (let i = 1; i < boxes.length; i++) assert.ok(boxes[i - 1][1] < boxes[i][0], `labels ${i - 1} and ${i} overprint`);
  assert.ok(Math.max(...boxes.flat()) <= Number(/viewBox="(-?[\d.]+) -?[\d.]+ ([\d.]+)/.exec(html)[2]), 'inside the viewBox');
});

test('reader charts: a bridge label of three lines stays inside the svg at both label sizes', () => {
  const names = ['Net income (reported, US GAAP) FY2024', 'Depreciation and amortization expense', 'Non-cash stock and deferred compensation expense', 'Other, net'];
  for (const count of [4, 9]) {
    const rows = Array.from({ length: count }, (_, i) => [63 + i, names[i % 4] + (i > 3 ? ` ${i}` : ''), i === 0 ? '1000' : i === count - 1 ? String(1000 + 50 * (count - 2)) : '50', 'US$m', 'Synthetic.']);
    const html = runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: liquidity bridge', 3, 60, 'consumed', [table(62, ['Step', 'Amount', 'Reporting unit', 'Basis and limitation'], rows)])); return d; }).readerChart(outId('CP-1'), BRIDGE_CHART);
    const [, , top, , height] = /viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"/.exec(html).map(Number);
    const bottom = top + height;
    for (const [, y, body] of html.matchAll(/<text class="axis-label" x="[\d.]+" y="([\d.]+)"[^>]*>(.*?)<\/text>/g)) {
      const lines = [...body.matchAll(/<tspan/g)].length;
      for (const px of [11, 14]) assert.ok(Number(y) + (lines - 1) * 1.2 * px + 0.3 * px <= bottom, `${count} steps: ${lines} lines at ${px}px end at ${Number(y) + (lines - 1) * 1.2 * px + 0.3 * px}, past ${bottom}`);
    }
  }
});

test('reader charts: a wide bridge scrolls inside its card as a keyboard-reachable region and is never drawn smaller than before', () => {
  const rows = Array.from({ length: 9 }, (_, i) => [63 + i, `Step ${i}`, i === 0 ? '1000' : i === 8 ? '1350' : '50', 'US$m', 'Synthetic.']);
  const html = runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: liquidity bridge', 3, 60, 'consumed', [table(62, ['Step', 'Amount', 'Reporting unit', 'Basis and limitation'], rows)])); return d; }).readerChart(outId('CP-1'), BRIDGE_CHART);
  assert.match(html, /<div class="vector-chart bridge-wide" role="region" tabindex="0" aria-label="[^"]*Liquidity bridge[^"]*scroll/);
  const min = Number(/<svg [^>]*style="min-width:(\d+)px"/.exec(html)[1]), box = Number(/viewBox="-?[\d.]+ -?[\d.]+ ([\d.]+)/.exec(html)[1]);
  // Before the wide geometry the 11px label was drawn at 368/680 of its size in the 400px overview aside.
  assert.ok(min / box >= 0.7, `drawn at ${min / box} of its size at the narrowest`);
  // A bridge that is not wide is not a scroll region.
  assert.ok(!runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: liquidity bridge', 3, 60, 'consumed', [table(62, ['Step', 'Amount', 'Reporting unit', 'Basis and limitation'], rows.slice(0, 3).map((r, i) => i === 2 ? [r[0], r[1], '1050', r[3], r[4]] : r))])); return d; }).readerChart(outId('CP-1'), BRIDGE_CHART).includes('role="region"'));
});

test('reader charts: a bridge label never exceeds its line budget, a lone word of exactly the budget included', () => {
  const src = require('fs').readFileSync(require('path').join(__dirname, 'views.js'), 'utf8');
  const axisLines = new Function(src.slice(src.indexOf('const AXIS_CHAR'), src.indexOf('function bridgeChart')) + ';return axisLines;')();
  for (const step of [60, 80, 110, 142]) {
    const room = Math.max(4, Math.floor((step - 6) / 8.4));
    for (const label of ['alpha beta gamma delta', 'one two three ' + 'x'.repeat(room), 'one two three ' + 'x'.repeat(room + 3), 'a b ' + 'y'.repeat(room) + ' tail', 'Depreciation amortization and other items', ['a', 'b', 'c'].map(c => c.repeat(room)).join(' ') + ' tail']) for (const line of axisLines(label, step)) assert.ok(line.length <= room, `${step}: "${line}" in ${label}`);
  }
});

test('structure views: five or more ranking and security pairs are told apart by a pattern and the legend swatch matches its segments', () => {
  const html = stackOf([['1', 'Yes', '100'], ['2', 'Yes', '100'], ['3', 'No', '100'], ['4', 'No', '100'], ['5', 'No', '100'], ['1', 'Yes', '100']]);
  const classes = [...html.matchAll(/<a class="stack-seg ([^"]*)"/g)].map(m => m[1]);
  assert.equal(new Set(classes.slice(0, 5)).size, 5);
  assert.equal(classes[5], classes[0]);
  assert.ok(classes[4].includes('hatch') && !classes[0].includes('hatch'));
  const swatches = [...html.matchAll(/<i class="([^"]*)"><\/i>Rank/g)].map(m => m[1]);
  assert.deepEqual(swatches, classes.slice(0, 5));
  assert.deepEqual([...html.matchAll(/<i class="swatch ([^"]*)"/g)].map(m => m[1]), classes);
  const eight = stackOf(Array.from({ length: 8 }, (_, i) => [String(i + 1), 'Yes', '100']));
  assert.equal(new Set([...eight.matchAll(/<a class="stack-seg ([^"]*)"/g)].map(m => m[1])).size, 8);
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
  const zero = Number(/<line x1="0" y1="([^"]*)" x2="660" y2="\1" class="axis"\/>/.exec(html)[1]);
  assert.ok(zero < 210 && Math.abs(rects[0].bottom - zero) < 0.01 && Math.abs(rects[3].bottom - zero) < 0.01);
  assert.ok(Math.abs(rects[1].bottom - 210) < 0.01, 'the outflow ends at the lowest running position');
});

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
  // Ranking 1 secured and ranking 2 unsecured are two pairs, so two series; the widths are unchanged.
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

const stackOf = rows => runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: debt stack', 3, 90, 'consumed', [table(92, ['Facility', 'Ranking', 'Secured', 'Amount', 'Cumulative leverage', ...TAIL], rows.map(([r, s, a], i) => [93 + i, `F${i}`, r, s, a, '1.0', 'US$m', 'Synthetic.']))])); d[outId('CP-1')].charts.push(STACK); return d; }).readerChart(outId('CP-1'), STACK);

test('structure views: debt stack segments of equal ranking and security share a series, others differ, and a legend names each pair', () => {
  const html = stackOf([['1', 'Yes', '100'], ['1', 'Yes', '200'], ['2', 'No', '300'], ['2', 'Yes', '50']]);
  const classes = [...html.matchAll(/<a class="stack-seg series-(\d)"/g)].map(m => m[1]);
  assert.equal(classes[0], classes[1]);
  assert.equal(new Set(classes).size, 3);
  const legend = strip(/<div class="chart-legend stack-legend">(.*?)<\/div>/s.exec(html)[1]);
  assert.equal(legend, 'Rank 1 \u00b7 securedRank 2 \u00b7 unsecuredRank 2 \u00b7 secured');
  // The per-facility swatches use the same classes as the segments.
  assert.deepEqual([...html.matchAll(/<i class="swatch series-(\d)"/g)].map(m => m[1]), classes);
});

test('structure views: a debt stack row with no ranking or an unreadable Secured value keeps a neutral class and the legend says so', () => {
  const html = stackOf([['1', 'Yes', '100'], ['Not supplied: not stated', 'Yes', '100'], ['2', 'Maybe', '100']]);
  assert.equal(countOf(html, /<a class="stack-seg stack-neutral"/g), 2);
  assert.equal(countOf(html, /<i class="swatch stack-neutral"/g), 2);
  const legend = strip(/<div class="chart-legend stack-legend">(.*?)<\/div>/s.exec(html)[1]);
  assert.equal(legend, 'Rank 1 \u00b7 securedRanking not statedRank 2 \u00b7 security not stated');
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

// ---- Package 3 views (2026-11-10): prior and current results, margin and KPI changes, peer ranges and yield against maturity. Every value is synthetic.
const PAIR_HEAD = ['Measure', 'Prior period', 'Prior', 'Current period', 'Current', ...TAIL];
const PEER_HEAD = ['Metric', 'Issuer', 'Peer low', 'Peer median', 'Peer high', 'Peer count', ...TAIL];
const YIELD_HEAD = ['Instrument', 'Maturity date', 'Yield', 'Spread', 'Quote date', 'Source class', ...TAIL];
const GROUPED = { title: 'Prior and current results', unit: 'US$m', table: 132, kind: 'grouped', label: 0, sub: [1, 3], periods: [1, 3], prior: 2, current: 4, columns: [2, 4] };
const DUMBBELL = { title: 'Margin and KPI changes', unit: '', table: 142, kind: 'dumbbell', label: 0, sub: [1, 3], periods: [1, 3], prior: 2, current: 4, columns: [2, 4] };
const RANGE = { title: 'Peer range — percent metrics', unit: '%', table: 152, kind: 'range', label: 0, issuer: 1, low: 2, median: 3, high: 4, count: 5, columns: [1, 2, 3, 4, 5] };
const SCATTER = { title: 'Yield against maturity', unit: '', table: 162, kind: 'scatter', label: 0, date: 1, yield: 2, spread: 3, quoted: 4, source: 5, columns: [2] };
const SYN = 'Synthetic.';
const note = (name, date, yld, unit, spread = '+310 bp') => [name, date, yld, spread, '2024-12-31', 'Dealer quote', unit, SYN];
const withComparison = d => {
  const cp1 = d[outId('CP-1')];
  cp1.sections.push(
    sec('Chart data: prior and current results', 3, 130, 'consumed', [table(132, PAIR_HEAD, [[133, 'Revenue', 'FY2023', '2,100', 'FY2024', '2,250', 'US$m', SYN], [134, 'EBITDA', 'FY2023', 'Not supplied: not stated', 'FY2024', '410', 'US$m', SYN]])]),
    sec('Chart data: margin and KPI changes', 3, 140, 'consumed', [table(142, PAIR_HEAD, [[143, 'EBITDA margin', 'FY2023', '19.5', 'FY2024', '21.0', '%', SYN], [144, 'Subscribers', 'FY2023', '1.2', 'FY2024', '1.4', 'm', SYN], [145, 'Leverage', 'FY2023', '4.0', 'FY2024', 'Not supplied: not stated', 'x', SYN]])]),
    sec('Chart data: peer range — percent metrics', 3, 150, 'consumed', [table(152, PEER_HEAD, [[153, 'EBITDA margin', '21.0', '12.0', '18.5', '26.0', '7', '%', SYN], [154, 'FFO / debt', 'Not supplied: not stated', '8.0', '15.0', '22.0', '6', '%', SYN], [155, 'Misordered', '10.0', '30.0', '18.5', '26.0', '5', '%', SYN]])]),
    sec('Chart data: yield against maturity', 3, 160, 'consumed', [table(162, YIELD_HEAD, [note('2028 note', '2028-06-15', '6.4', '%'), note('2030 note', '2030-06-15', '7.0', '%'), note('2029 note', '2029-06-15', '6.8', '%'), note('No quote', '2031-03-01', 'Not supplied: no quote', '%', 'Not supplied: no quote'), note('Undated', 'June 2029', '6.9', '%'), note('Other measure', '2029-01-01', '250', 'bp')].map((r, i) => [163 + i, ...r]))]));
  cp1.charts.push(GROUPED, DUMBBELL, RANGE, SCATTER);
  return d;
};
const comparison = chart => runPage(withComparison).readerChart(outId('CP-1'), chart);
const FORM = '<details class="chart-table"><summary>Table form</summary>';

test('comparison views: prior and current results are two columns per measure on one zero baseline, the periods under the label', () => {
  const html = comparison(GROUPED);
  assert.ok(html.includes('<span class="chart-label">Revenue<small>FY2023 → FY2024</small></span>'));
  assert.ok(html.includes('<i class="series-0" style="bottom:0%;height:93.33%"></i>') && html.includes('<i class="series-1" style="bottom:0%;height:100%"></i>'));
  const ebitda = html.split('<div class="chart-row"')[2] || html.split('class="chart-row"')[2];
  assert.ok(ebitda.includes('class="col missing"') && !ebitda.includes('series-0'), 'a prior that is not stated has no column');
  assert.ok(strip(html).includes('Prior') && strip(html).includes('Current') && html.includes(FORM) && !/CP-\d/.test(strip(html)));
});

test('comparison views: a dumbbell joins the stated prior and current on a scale shared only within a unit, with no change worked out', () => {
  const html = comparison(DUMBBELL);
  const [margin, subscribers, leverage] = html.split('<div class="dumbbell-row"').slice(1);
  assert.ok(margin.includes('<i class="dumbbell-link" style="left:84.42%;width:6.49%"></i>'));
  assert.ok(margin.includes('<i class="dumbbell-dot series-0" style="left:84.42%"></i>') && margin.includes('<i class="dumbbell-dot series-1" style="left:90.91%"></i>'));
  assert.ok(subscribers.includes('<i class="dumbbell-link" style="left:77.92%;width:12.99%"></i>'), 'its own unit has its own scale');
  assert.ok(strip(margin).includes('Prior FY2023 19.5') && strip(margin).includes('Current FY2024 21.0'));
  assert.ok(leverage.includes('dumbbell-dot series-0') && !leverage.includes('dumbbell-dot series-1') && !leverage.includes('dumbbell-link') && strip(leverage).includes('Current FY2024 n.a.'));
  assert.ok(!/\bchange\b|difference|\bpp\b/i.test(strip(html)), 'no change is stated that the handoff did not state');
  assert.ok(html.includes(FORM));
});

test('comparison views: a peer range is a band from the stated low to high, a median tick and the issuer marker', () => {
  const html = comparison(RANGE);
  const [margin, ffo, misordered] = html.split('<div class="range-row"').slice(1);
  assert.ok(margin.includes('<i class="range-band" style="left:41.96%;width:48.95%"></i>') && margin.includes('<i class="tick" style="left:64.69%"></i>') && margin.includes('<i class="marker" style="left:73.43%"></i>'));
  assert.ok(strip(margin).includes('Issuer 21.0') && strip(margin).includes('Peers 7') && strip(margin).includes('Peer low 12.0'));
  assert.ok(ffo.includes('range-band') && !ffo.includes('class="marker"') && strip(ffo).includes('Issuer n.a.'), 'no marker for an issuer value not stated');
  assert.ok(!misordered.includes('range-band'), 'a band is drawn only for a stated low that does not exceed the high');
  assert.ok(html.includes(FORM));
});

test('comparison views: yield against maturity places each stated date and yield, one panel per unit, and lists what has no point', () => {
  const html = comparison(SCATTER);
  const panels = html.split(/<svg(?! class="i")/).slice(1); // the trace icon of a row is an svg too; only the chart panels are counted
  assert.equal(panels.length, 2, 'yields in another unit are not drawn on the same scale');
  const dots = [...panels[0].matchAll(/<circle class="scatter-dot" cx="([\d.]+)" cy="([\d.]+)"/g)].map(m => [m[1], m[2]]);
  assert.deepEqual(dots, [['60', '166.67'], ['630', '33.33'], ['345', '77.78']]);
  assert.ok(panels[0].includes('>2028-06-15</text>') && panels[0].includes('>2030-06-15</text>'));
  const key = strip(/<ol class="stack-key">(.*?)<\/ol>/s.exec(html)[1]);
  assert.ok(/No quote.*Yield n\.a\./s.test(key) && /Undated.*Maturity June 2029/s.test(key) && key.includes('Dealer quote') && key.includes('+310 bp') && key.includes('2024-12-31'));
  assert.ok(html.includes('An instrument with no stated maturity date or yield has no point.') && html.includes(FORM));
});

test('comparison views: an invalid calendar date has no point and does not break the page; a grouped chart takes the missing-values note', () => {
  const bad = ['2028-13-01', '2028-00-10', '9999-99-99', '2028-02-31'];
  const rows = bad.map((when, i) => [190 + i, ...note(`Bad ${i}`, when, '6.4', '%')]);
  const chart = { ...SCATTER, table: 182 };
  const page = runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: yield against maturity', 3, 180, 'consumed', [table(182, YIELD_HEAD, rows)])); d[outId('CP-1')].charts.push(chart); return d; });
  const html = page.readerChart(outId('CP-1'), chart);
  assert.equal(countOf(html, /scatter-dot/g), 0);
  assert.ok(html.includes('An instrument with no stated maturity date or yield has no point.'));
  assert.equal(page.lastPeriodChart([{ kind: 'dumbbell' }, { kind: 'grouped' }]), 1);
});

test('comparison views: the new view rules use only the series and ink tokens, never amber or red', () => {
  const rules = read('screen.css').split('\n').filter(line => /\.(dumbbell|range|scatter)-/.test(line));
  assert.ok(rules.length >= 3, 'the new rules are found');
  for (const rule of rules) assert.ok(!/amber|--red|#b47812|#b3261e|#8a5300/i.test(rule), rule);
});

// ---- Package 4 views (2026-11-10): recovery by class and the value allocation waterfalls. Every value is synthetic.
const RECOVERY_HEAD = ['Class', 'Scenario', 'Claim', 'Recovery', 'Recovery %', ...TAIL];
const RECOVERY = { title: 'Recovery by class', unit: 'US$m', table: 202, kind: 'recovery', label: 0, scenario: 1, claim: 2, recovery: 3, percent: 4, columns: [2, 3, 4] };
const ALLOCATION = { title: 'Value allocation \u2014 scenario 1', unit: 'US$m', table: 222, kind: 'waterfall', amount: 1, columns: [1] };
const recoveryRow = (line, cls, scenario, claim, recovery, percent) => [line, cls, scenario, claim, recovery, percent, 'US$m', SYN];
const withRecovery = d => {
  const cp1 = d[outId('CP-1')];
  cp1.sections.push(
    sec('Chart data: recovery by class', 3, 200, 'consumed', [table(202, RECOVERY_HEAD, [recoveryRow(203, 'Senior secured', 'Base', '1,200', '1,080', '90'), recoveryRow(204, 'Senior secured', 'Downside', '1,200', '720', '60'), recoveryRow(205, 'Unsecured', 'Base', '800', '120', '15'), recoveryRow(206, 'Unsecured', 'Downside', '800', 'Not supplied: no downside value', 'Not supplied: no downside value')])]),
    sec('Chart data: value allocation \u2014 scenario 1', 3, 220, 'consumed', [table(222, ['Step', 'Amount', ...TAIL], [[223, 'Enterprise value', '2,000', 'US$m', SYN], [224, 'Restructuring costs', '-100', 'US$m', SYN], [225, 'Senior secured distribution', '-1,080', 'US$m', SYN], [226, 'Unsecured distribution', '-120', 'US$m', SYN], [227, 'Value not distributed', '700', 'US$m', SYN]])]));
  cp1.charts.push(RECOVERY, ALLOCATION);
  return d;
};

test('recovery views: recovery is columns by class, one series per scenario on one zero baseline, claim and percent as stated', () => {
  const html = runPage(withRecovery).readerChart(outId('CP-1'), RECOVERY);
  const [senior, unsecured] = html.split('<div class="recovery-group"').slice(1);
  assert.ok(html.includes('<div class="chart-legend"><span><i class="series-0"></i>Base</span><span><i class="series-1"></i>Downside</span></div>'));
  assert.ok(senior.includes('<i class="series-0" style="bottom:0%;height:100%"></i>') && senior.includes('<i class="series-1" style="bottom:0%;height:66.67%"></i>'));
  assert.ok(strip(senior).includes('Base: claim 1,200 US$m · recovery 1,080 · 90%') && strip(senior).includes('Downside: claim 1,200 US$m · recovery 720 · 60%'));
  assert.ok(unsecured.includes('<i class="series-0" style="bottom:0%;height:11.11%"></i>') && unsecured.includes('class="col missing"') && !unsecured.includes('series-1'), 'a recovery not stated has no bar and is never zero');
  assert.ok(strip(unsecured).includes('Downside: claim 800 US$m · recovery n.a. · n.a.'));
  assert.ok(senior.includes(`data-evidence="${outId('CP-1')}:203"`) && html.includes(FORM) && !/CP-\d/.test(strip(html)));
  assert.ok(!/\bcomputed\b|\bshortfall\b/i.test(strip(html)), 'no recovery percentage or shortfall is worked out');
});

test('recovery views: scenarios keep one order in every class; a class with no row for one has an empty not-stated slot, never a zero bar', () => {
  const rows = [recoveryRow(303, 'Senior', 'Base', '100', '90', '90'), recoveryRow(304, 'Senior', 'Downside', '100', '60', '60'), recoveryRow(305, 'Junior', 'Downside', '50', '10', '20')];
  const chart = { ...RECOVERY, table: 302 };
  const page = runPage(d => { d[outId('CP-1')].sections.push(sec('Chart data: recovery by class', 3, 300, 'consumed', [table(302, RECOVERY_HEAD, rows)])); d[outId('CP-1')].charts.push(chart); return d; });
  const junior = page.readerChart(outId('CP-1'), chart).split('<div class="recovery-group"')[2];
  assert.ok(/^[^]*?class="col missing"[^]*?not stated[^]*?series-1/.test(junior.split('<span class="chart-label">')[0]), 'the Base slot is first and empty');
  assert.equal(countOf(junior, /<i class="series-/g), 1);
});

test('recovery views: the figure takes the missing-values note and its rules use no amber or red', () => {
  const page = runPage(withRecovery);
  assert.equal(page.lastPeriodChart([{ kind: 'waterfall' }, { kind: 'recovery' }, { kind: 'bullet' }]), 1);
  const rules = read('screen.css').split('\n').filter(line => /\.recovery-/.test(line));
  assert.ok(rules.length >= 1, 'the new rules are found');
  for (const rule of rules) assert.ok(!/amber|--red|#b47812|#b3261e|#8a5300/i.test(rule), rule);
});

test('recovery views: a value allocation is a waterfall from enterprise value to the value not distributed', () => {
  const html = runPage(withRecovery).readerChart(outId('CP-1'), ALLOCATION);
  assert.equal(countOf(html, /<rect class="total"/g), 2);
  assert.equal(countOf(html, /<rect class="outflow"/g), 3);
  assert.ok(html.includes('aria-label="Value not distributed, 700 US$m. View source"') && html.includes('<h2>Value allocation \u2014 scenario 1</h2>') && html.includes(FORM));
});

// ---- Screens pass (2026-11-10): what a reader acts on is shown; production detail (hashes, file names, word counts) is a title or behind a disclosure.
const HASH = 'f'.repeat(64);
const zedRun = (extra = {}) => ({ id: RUN, name: 'Zed & Sons', issuer: 'ZED', title: 'Credit Snapshot', sector: 'Telecoms', workflow: 'Credit Snapshot', date: '2024-09-30', period: 'FY-2024', completion: null, summary: 'Leverage is high.', gaps: [], ratings: [], currency: 'USD',
  metrics: { leverage: { value: '6.57', unit: 'x', basis: 'Total debt / EBITDA', period: 'FY2024' } },
  artifacts: [{ kind: 'report', label: HASH, state: 'candidate', relationship: 'direct', issue: '', available: true, href: `../runs/${RUN}/deliveries/${HASH}/report.html` }], ...extra });

test('library panel: a delivered report is named, never linked; the run opens from Open run and History; measures the run lacks are one line', () => {
  const page = runPage();
  page.libraryState.selected = RUN;
  const html = page.libraryDetail({ rows: [zedRun()] });
  const list = /<ul class="artifact-list">(.*?)<\/ul>/s.exec(html)[1];
  // The catalogue's report entry is a plain name (its folder hash is not text) with its recorded acceptance; there is no link to the delivered report.
  assert.ok(list.includes('<li><span>Delivered report</span><small>Candidate · not accepted</small></li>'), list);
  assert.ok(!strip(html).includes(HASH) && !html.includes('report.html') && !html.includes('target="_blank"'));
  // Open run and History sit beside each other in the actions; no Open report.
  assert.ok(html.includes(`<a class="secondary-action" href="#W-Overview/overview?c=${RUN}">Open run</a><a class="secondary-action" href="#W-Report/history?c=${RUN}">History</a>`), html);
  assert.ok(!html.includes('Open report') && !html.includes('All reports'));
  // One card for the measure the run has; the seven it lacks are named once, with no empty card.
  assert.equal(countOf(html, /class="metric-item"/g), 1);
  assert.ok(html.includes('<p class="metric-absent">Not established for this run: Revenue, EBITDA, Net leverage, Interest coverage, Closing cash, Undrawn facilities, Cash flow measure.</p>'));
  // A catalogued report keeps its own label when that is not a hash; an accepted one says so. Neither is a link.
  const other = page.libraryDetail({ rows: [zedRun({ artifacts: [{ kind: 'report', label: 'Board pack', state: 'accepted', relationship: 'direct', issue: '', available: true, href: '../runs/elsewhere/pack.html' }] })] });
  assert.ok(other.includes('<li><span>Board pack</span><small>Accepted</small></li>'), other);
});

test('library panel: a measure quoted on the adjusted names draws that label; one with no label draws no extra line', () => {
  const page = runPage();
  page.libraryState.selected = RUN;
  const adjusted = zedRun({ metrics: { leverage: { value: '5.96', unit: 'x', basis: 'Carrying debt over EBITDA.', period: 'FY2024', label: 'Total debt / adjusted EBITDA' } } });
  const html = page.libraryDetail({ rows: [adjusted] });
  assert.ok(html.includes('<p class="metric-named">Total debt / adjusted EBITDA</p>'), html);
  assert.ok(!page.libraryDetail({ rows: [zedRun()] }).includes('metric-named'));
  // The list view says it too, in the cell's title, so an adjusted figure is never read as the reported one.
  const list = run => page.libraryRow(run, false, false);
  assert.ok(list(adjusted).includes('title="Total debt / adjusted EBITDA \u00b7 FY2024"'), list(adjusted));
  assert.ok(list(zedRun()).includes('title="FY2024"') && !list(zedRun()).includes('adjusted'));
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

test('screens pass: one word for a run, in-app actions carry no out-arrow, and the styles the markup needs exist', () => {
  const views = read('views.js'), css = read('screen.css'), screen = read('screen.js');
  assert.ok(!/Change case|another case|for this case|other cases/.test(views));
  assert.ok(views.includes('</svg>Issuer library</a>') && !views.includes('Change run') && !views.includes('View source ↗'));
  for (const sel of ['.metric-absent{', '.library-table td.run-when{overflow-wrap:anywhere']) assert.ok(css.includes(sel), sel);
  // Never assessed is a fact, not an alert: the completeness note no longer uses the amber of states that need action.
  const box = css.slice(css.lastIndexOf('.completion-box{'));
  assert.ok(box.startsWith('.completion-box{border-color:var(--border-secondary);background:var(--gray-50)'));
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

test('names, not codes: module heads and the report head carry no module code in text, title or aria-label', () => {
  const page = runPage(d => { for (const out of Object.values(d)) Object.assign(out, { file: `${RUN}--deliveries--d1--${out.module}.md`, sha256: 'c'.repeat(64) }); return d; }, [], withInputs);
  for (const id of Object.keys(runData())) page.modules[id] = { first: 'head' };
  const head = page.moduleHead({ module: 'CP-1', context: RUN, output: null });
  assert.ok(head.includes('<h2>Financial foundation</h2>') && !head.includes('title='));
  noCode(report().reportHead(OUT));
  assert.equal(page.handoffLabel('deliveries/h/CP-1A.md'), 'Unnamed module handoff', 'a module no group names');
  assert.equal(page.handoffLabel('K.pdf'), 'K.pdf');
});

test('names, not codes: chips name their module, the row control is the trace icon, titles from handoff text are named', () => {
  const r = report(), html = r.chipsMarkup(`${OUT}:16`) + r.chipsMarkup(`${OUT}:777`);
  noCode(html);
  assert.ok(html.includes('title="Table row, line 16" aria-label="Table row, line 16"><svg') && !html.includes('>Row<'), 'the row control is the trace icon');
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
  const inspector = new Function('$', 'document', 'window', 'evidence', 'data', 'classification', 'esc', 'rich', 'icon', 'chipSection', 'unresolvedGap', 'nameCodes', 'moduleTitle', 'handoffLabel', 'returnTrigger', 'drawerFoot', 'setDrawer',
    `${src.slice(start, end)}; return showInspector;`)(() => element, { querySelectorAll: () => [] }, { Components: require('./components.js'), CREDIT_OS_DATA: { chips: {} } }, new Map([['k', item]]), { [OUT]: stored }, () => 'Not classified', v => String(v), v => String(v),
    n => `<i>${n}</i>`, () => '', () => false, (root, output, marks) => named.push([root, output, marks]), r.moduleTitle, r.handoffLabel, null, module => `<footer>${module}</footer>`, open => { element.hidden = !open; });
  inspector('k');
  assert.ok(element.innerHTML.includes('>Financial foundation · Line 54<') && !element.innerHTML.includes('(CP-1)'));
  assert.ok(element.innerHTML.includes('Financial foundation handoff<br>Zed & Sons · RUN-A · saved output') && !element.innerHTML.includes('--CP-1.md'));
  assert.ok(element.innerHTML.includes('<a href="../runs/run-a/deliveries/d1/CP-1.md" download>'), 'the download link is unchanged');
  assert.ok(element.innerHTML.endsWith('<footer>CP-1</footer>'), 'the drawer ends with the footer of the traced module');
  assert.ok(element.innerHTML.includes('id="back-analysis"') && element.innerHTML.includes('aria-label="Close the trace'), 'the drawer has a close button');
  assert.deepEqual(named, [[element, OUT, false]], 'the inspector text is named, its register references left as they are');
  assert.ok(runPage().handoffLabel('runs/x/CP-0.md') === 'Source readiness handoff');
  // The library home no longer draws source quotes (a findings page draws no file or source: they are Evidence's, library redesign Task 11); the handoff names stay with the Evidence sources and the inspector above.
  assert.ok(!read('views.js').includes('librarySources') && !read('views.js').includes('data-library-source') && read('views.js').includes('Sources, definitions and calculations in Evidence'));
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

test('names, not codes: a step heading with no dash, a prefixed register id and a gap cell read as their own words', () => {
  const page = runPage(d => {
    d[outId('CP-1')].sections.push(ref('Steps', 80, [table(81, ['Step', 'Name'], [[82, 'T2.12', 'Gaps ledger'], [83, 'T2.13 Open items', '']])]), sec('T2.14 Ratings view', 3, 90, 'reference', [text(91, 'x')]));
    return d;
  }), id = outId('CP-1'), name = text => page.namedText(text, id);
  assert.equal(name('T2.12'), 'Gaps ledger');
  assert.equal(name('See T2.13'), 'See “Open items”', 'a dashless step row gives its title');
  assert.equal(name('T2.14'), 'Ratings view', 'a dashless step heading gives its title');
  assert.equal(name('T9.9 stands'), 'a method step stands', 'a lowercase word after a dashless id is prose');
  assert.equal(report().METHOD_CODE.test('T2.12 Gaps ledger') && 'T2.12 Gaps ledger'.replace(report().METHOD_CODE, ''), 'Gaps ledger');
  assert.equal('T2.12 — Gaps ledger'.replace(report().METHOD_CODE, ''), 'Gaps ledger');
  assert.equal('T9.9 stands'.replace(report().METHOD_CODE, ''), 'T9.9 stands');
  assert.equal('T2E.3.r01 Row'.replace(report().METHOD_CODE, ''), 'T2E.3.r01 Row');
  page.current.module = 'CP-6';
  assert.equal(name('CP-6-MON-001 and CP-6A-DP-005'), 'MON-001 and DP-005', 'own page: the register id alone, an alias counts as the module');
  assert.equal(name('Gap CP-6-GAP-005'), 'Gap 5');
  page.current.module = 'CP-1';
  assert.equal(name('CP-6-MON-001 and CP-6A-DP-005'), 'Committee decision MON-001 and Committee decision DP-005');
  assert.equal(name('Gap CP-6-GAP-005'), 'Committee decision gap 5');
  assert.equal(name('CP-2R-MON-001'), 'unnamed module MON-001');
  // The real register ids at the start of a heading: METHOD_CODE leaves them (they are not step ids), and the naming shows them without the module code.
  assert.equal('CP-3B-MON-001 Monitoring trigger'.replace(report().METHOD_CODE, ''), 'CP-3B-MON-001 Monitoring trigger');
  page.current.module = 'CP-3B';
  assert.equal(name('CP-3B-MON-001 Monitoring trigger'), 'MON-001 Monitoring trigger');
  page.current.module = 'CP-2A';
  assert.equal(name('CP-2A-DP-005 Decision point'), 'DP-005 Decision point');
  assert.equal(name('CP-3B-MON-001 Monitoring trigger'), 'unnamed module MON-001 Monitoring trigger');
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
  const nodes = texts.map((data, i) => ({ data, previousSibling: i ? { textContent: texts[i - 1] } : null, parentElement: { closest: selector => (selector.includes(zone) && zone ? {} : null) }, replaceWith(fragment) { this.fragment = fragment; } }));
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
  assert.equal(nameCodesIn(['Source readiness', ' (CP-0)'])[1].data, '', 'a parenthesised code after the module name in the node before is dropped');
  assert.ok(screen.includes('Retained fields from this historical run, with module codes and method step ids shown as names.') && !screen.includes('exact retained fields'));
  assert.ok(/function nameCodes[^]*?nameCodes\(\$\('search-results'\),null,false\)/.test(screen), 'search hits borrow no step title');
  assert.ok(screen.includes("tables.map(s=>[id,plain(s.heading.replace(METHOD_CODE,'')),s.heading])"), 'a search hit label loses the heading\'s leading step id');
  assert.ok(/updateLibrary\([^]*?nameCodes\(\$\(id\)\)/.test(read('views.js')), 'a redrawn library is named');
  assert.ok(/function openAuditSection[^]*?body\.innerHTML=sectionView\([^;]*;if\(!keepsCodes\(current\)\)nameCodes\(body\);/.test(screen), 'an audit section is named when it is drawn');
});

test('names, not codes (R4, R6): only the Evidence page escapes nameCodes (its file names stay as stored); module pages and the Overview of either format are named', () => {
  const screen = read('screen.js');
  const keepsCodes = new Function('contexts', 'earlierFormat', 'isAnalytical', 'data', 'isNewFormat', `${screen.slice(screen.indexOf('const keepsCodes='), screen.indexOf('const reportPage='))}; return keepsCodes;`)(
    { r: {} }, () => false, () => true, { o: { sections: [] } }, () => true);
  assert.equal(keepsCodes({ module: 'W-Evidence', context: 'r' }), true);
  assert.equal(keepsCodes({ module: 'W-Forecast', context: 'r' }), false);
  assert.equal(keepsCodes({ module: 'W-Overview', context: 'r' }), false, 'a new-format Overview is named');
  assert.equal(keepsCodes({ module: 'CP-1', output: 'o', context: 'r' }), false, 'a new-format module page is named');
  // Both callers skip a page that keeps its codes.
  assert.ok(screen.includes("if(!keepsCodes(next)){nameCodes($('module-head'));nameCodes($('content'));}") && screen.includes('if(!keepsCodes(current))nameCodes(content);'));
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
  assert.ok(read('screen.js').includes("parent.closest('.ref,.excerpt')") && !read('screen.js').includes('.module-code'), 'a source excerpt is the issuer\'s text, as quoted, and a register reference stays; a Basis line and a navigator entry show names (owner ruling 2026-11-12)');
  // A name already written before its parenthesised code is not said twice; any other parenthesised code becomes its name.
  assert.equal(page.namedText('Source readiness (CP-0) and Foundation (CP-1) and Ghost (CP-9Z)', null), 'Source readiness and Foundation (Financial foundation) and Ghost (unnamed module)');
  assert.equal(page.namedText('the source readiness (CP-0) check', null), 'the source readiness check', 'a name written in other case is not said twice');
});

test('names, not codes: a stored source file name of the run is shown as stored', () => {
  const stored = { names: { 'CP-2D': 'Liquidity' }, runFields: { evidence: { sources: [{ name: 'CP-2025-Info-Memo.pdf' }], unused: [{ name: 'CP-1 Board resolution.pdf' }], unrecorded: [] } } };
  const page = runPage(d => d, [], m => m, stored);
  assert.equal(page.namedText('CP-2025-Info-Memo.pdf, page 3; Liquidity (CP-2D)', null), 'CP-2025-Info-Memo.pdf, page 3; Liquidity');
  assert.equal(page.namedText('CP-1 Board resolution.pdf, page 2; Financial foundation (CP-1) and CP-1', null), 'CP-1 Board resolution.pdf, page 2; Financial foundation and Financial foundation');
  assert.equal(page.namedText('Illiquidity (CP-2D) risk', null), 'Illiquidity (Liquidity) risk');
  assert.equal(page.namedText(' (CP-2D)', null, 'Liquidity'), '');
  assert.equal(page.namedText(' (CP-2D)', null, 'Illiquidity'), ' (Liquidity)');
  assert.equal(runPage().namedText('CP-2025-Info-Memo.pdf, page 3', null), 'unnamed module-Info-Memo.pdf, page 3');
});

// ---- Package 5 views (2026-11-10): calendar lanes and the accessible event table. Every value is synthetic.
const LANE_HEAD = ['Event date', 'Date precision', 'Published', 'Event', 'Status', 'Source', 'Credit relevance'];
const laneRow = (line, date, precision, published, event, status = 'Scheduled — due') => [line, date, precision, published, event, status, 'Synthetic filing', 'Synthetic relevance'];
const LANE_GAP = 'Not supplied: the handoff states no dated event';
const withLanes = d => {
  d[outId('CP-1')].sections.push(sec('Events: Financing', 3, 300, 'consumed', [table(302, LANE_HEAD, [laneRow(303, '2025-03-31', 'day', '—', 'Note matures'), laneRow(304, '2025-06', 'month', '2025-05-01', 'Call window'), laneRow(305, '2025-Q3', 'quarter', '—', 'Rating review', 'Scenario — modelled review'), laneRow(306, '2025', 'year', '—', 'Maturity year')])]));
  d[outId('CP-1')].events = [{ lane: 'Financing', table: 302, gap: null }];
  d[outId('CP-6')].sections.push(sec('Events: Decision and watch', 3, 310, 'consumed', [table(312, LANE_HEAD, [[313, ...Array(7).fill(LANE_GAP)]])]));
  d[outId('CP-6')].events = [{ lane: 'Decision and watch', table: 312, gap: 'the handoff states no dated event' }];
  return d;
};
const markers = html => [...html.matchAll(/class="lane-event (point|span)(?: scenario)?"[^>]*style="left:([\d.]+)%(?:;width:([\d.]+)%)?[;"]/g)].map(m => [m[1], Number(m[2]), m[3] === undefined ? null : Number(m[3])]);

test('calendar lanes: one lane per module that supplied events, placed on one axis at each date precision', () => {
  const html = runPage(withLanes).eventLanesView(RUN);
  assert.equal(countOf(html, /<div class="lane-row">/g), 2);
  assert.ok(strip(html).includes('Financing') && strip(html).includes('Decision and watch') && !/CP-\d/.test(strip(html)), 'lanes carry names, never module codes');
  // Hand-computed: the axis is 2025-01-01 to 2025-12-31, 364 days. Mar 31 is day 89; June is days 151-180; Q3 is days 181-272; the year is the whole axis.
  assert.deepEqual(markers(html), [['point', 24.45, null], ['span', 41.48, 7.97], ['span', 49.73, 25], ['span', 0, 100]]);
});

test('calendar lanes: a table of only Not supplied draws no event and says why', () => {
  const html = runPage(withLanes).eventLanesView(RUN);
  const gap = html.split('<div class="lane-row">')[2];
  assert.ok(strip(gap).includes('Decision and watch') && strip(gap).includes('Not established for this run') && strip(gap).includes('the handoff states no dated event'));
  assert.ok(!gap.includes('lane-event') && !gap.includes('Not supplied'));
});

test('calendar lanes: every event is a keyboard-reachable link naming its lane, date and precision, and the event table follows the lanes', () => {
  const html = runPage(withLanes).eventLanesView(RUN);
  const marker = [...html.matchAll(/<a class="lane-event[^>]*>/g)].map(m => m[0]);
  assert.equal(marker.length, 4);
  assert.ok(marker.every(m => /href="[^"]+"/.test(m) && m.includes('data-evidence=') && m.includes('aria-label=')));
  assert.ok(marker[1].includes('aria-label="Event 3: Financing: Call window, 2025-06 (month). View source"') && marker[1].includes(`data-evidence="${outId('CP-1')}:304"`));
  assert.ok(html.indexOf('class="lane-row"') < html.indexOf('<table class="event-table">'));
  const rows = [...html.split('<tbody>')[1].matchAll(/<tr>(.*?)<\/tr>/gs)].map(m => [...m[1].matchAll(/<t[dh][^>]*>(.*?)<\/t[dh]>/gs)].map(c => strip(c[1])));
  assert.deepEqual([...html.matchAll(/<th scope="col">(.*?)<\/th>/g)].map(m => m[1]), ['Lane', 'Event date', 'Date precision', 'Published', 'Event', 'Status', 'Source', 'Credit relevance']);
  assert.equal(rows.length, 4, 'the lane with no event adds no row');
  assert.deepEqual(rows[1], ['Financing', '2025-06', 'month', '2025-05-01', 'Call window', 'Scheduled — due', 'Synthetic filing', 'Synthetic relevance']);
  assert.deepEqual(rows[2].slice(0, 4), ['Financing', '2025-Q3', 'quarter', '—']);
});

test('calendar lanes: no Calendar page remains; lanes are not drawn on the Overview; the Evidence page is the four lists', () => {
  const page = runPage(withLanes);
  assert.ok(!('calendarSections' in page));
  assert.ok(!read('views.js').includes("eventLanesView(context,{at:'Overview'"), 'the Overview draws no lane: its dated rows feed the nearest dates');
});

test('calendar lanes: the new rules use only existing tokens, no amber or red, and a span is drawn differently from a day', () => {
  const css = read('screen.css').split('\n').filter(line => /\.lane-|\.event-table|\.event-lanes/.test(line));
  assert.ok(css.length >= 3, 'the new rules are found');
  for (const rule of css) assert.ok(!/amber|--red|\bred\b(?! Hat)|#[0-9a-f]{3,8}\b/i.test(rule), rule);  // the font name Red Hat is not a colour
  assert.ok(css.some(rule => /\.lane-event\.point/.test(rule)) && css.some(rule => /\.lane-event\.span/.test(rule)));
});

test('calendar lanes: a Scenario event is drawn with a dashed outline, not by colour alone, and says so in its name and its table row', () => {
  const html = runPage(withLanes).eventLanesView(RUN);
  const marker = [...html.matchAll(/<a class="lane-event[^>]*>/g)].map(m => m[0]);
  assert.deepEqual(marker.map(m => m.includes('scenario')), [false, false, true, false]);
  assert.ok(marker[2].includes('Scenario event') && !marker[1].includes('Scenario event'));
  assert.ok(strip(html).includes('Scenario — modelled review'));
  const rule = read('screen.css').split('\n').find(line => /\.lane-event\.scenario/.test(line));
  assert.ok(rule && /dashed/.test(rule) && !/amber|--red/.test(rule));
});

test('calendar lanes: a module filter draws only that module lane, and the Sources page draws the Sources lane', () => {
  const sources = d => { d[outId('CP-0')] = runOutput('CP-0', { sections: [sec('Events: Sources', 3, 400, 'consumed', [table(402, LANE_HEAD, [laneRow(403, '2025-02-14', 'day', '—', 'Filing published', 'Historical — filed')])])], events: [{ lane: 'Sources', table: 402, gap: null }] }); return withLanes(d); };
  const page = runPage(sources), only = page.eventLanesView(RUN, { only: outId('CP-0'), compact: true });
  assert.equal(countOf(only, /<div class="lane-row">/g), 1);
  assert.ok(strip(only).includes('Sources') && !strip(only).includes('Financing'));
  const text = read('views.js');
  assert.ok(text.includes("if(module==='W-Evidence')return evidenceView(context);") && !/if\(module==='W-Evidence'\)return[^\n]*eventLanesView/.test(text), 'the Evidence page is the four lists, no lanes');
});

// ---- Timeline drawing (2026-11-12 ruling, decision 6): year ticks, an as-of line, stacked points, a numbered key. Every value is synthetic.
const withDense = d => {
  d[outId('CP-0')] = runOutput('CP-0', { sections: [sec('Events: Sources', 3, 400, 'consumed', [table(402, LANE_HEAD, [
    laneRow(403, '2022-03-01', 'day', '—', 'First filing', 'Historical — filed'), laneRow(404, '2024-11', 'month', '—', 'Consent window'),
    laneRow(405, '2024-10-16', 'day', '—', 'Notice issued', 'Historical — filed'), laneRow(406, '2024-10-18', 'day', '—', 'Notice repeated', 'Historical — filed'), laneRow(407, '2025-02-10', 'day', '—', 'Maturity')])])],
  events: [{ lane: 'Sources', table: 402, gap: null }] });
  return d;
};
const denseHtml = asOf => runPage(withDense, [], m => m, { runFields: { asOf } }).eventLanesView(RUN, { only: outId('CP-0'), compact: true });
const styleOf = (html, label) => /style="([^"]*)"/.exec([...html.matchAll(/<a class="lane-event[^>]*>/g)].map(m => m[0]).find(m => m.includes(label)))[1];

test('timeline: a tick at each 1 January on the axis, labelled by year', () => {
  const axis = denseHtml('2024-09-30').split('class="lane-axis"')[1].split('<div role="group"')[0];
  // Hand-computed: the axis is 2022-03-01 to 2025-02-10, 1077 days; 1 January 2023, 2024 and 2025 fall 306, 671 and 1037 days in.
  assert.deepEqual([...axis.matchAll(/class="lane-tick" style="left:([\d.]+)%"/g)].map(m => Number(m[1])), [28.41, 62.3, 96.29]);
  assert.deepEqual([...axis.matchAll(/class="lane-tick-label"[^>]*>(\d{4})</g)].map(m => m[1]), ['2023', '2024', '2025']);
});

test('timeline: the as-of date is a labelled line inside the axis (ends included) and is absent outside it', () => {
  const inside = denseHtml('2024-09-30');
  assert.equal(countOf(inside, /class="lane-asof" style="left:87\.65%"/g), 1, 'hand-computed: 30 September 2024 is day 944 of 1077');
  assert.ok(strip(inside).includes('As of 30 September 2024'));
  assert.ok(/class="lane-asof" style="left:0%"/.test(denseHtml('2022-03-01')) && /class="lane-asof" style="left:100%"/.test(denseHtml('2025-02-10')), 'inclusive at both ends');
  for (const outside of ['2022-02-28', '2025-02-11', null]) assert.ok(!denseHtml(outside).includes('lane-asof') && !strip(denseHtml(outside)).includes('As of'), String(outside));
});

test('timeline: two points closer than a marker are stacked at their own x; a far point and a month span stay on the baseline at full length', () => {
  const html = denseHtml('2024-09-30');
  const issued = styleOf(html, 'Notice issued'), repeated = styleOf(html, 'Notice repeated');
  assert.ok(issued.startsWith('left:89.14%') && repeated.startsWith('left:89.32%'), 'x is the stated day, not moved');
  // Levels are computed on the 402 px narrowest track: the month span (364 to 380 px) holds the baseline, so the point at 358 px goes to row 1 and the one at 359 px to row 2.
  assert.ok(/bottom:24px/.test(issued) && /bottom:44px/.test(repeated), 'each later date sits one row up');
  assert.ok(/bottom:4px/.test(styleOf(html, 'First filing')) && /bottom:4px/.test(styleOf(html, 'Maturity')));
  assert.ok(/^left:90\.62%;width:2\.69%;bottom:4px/.test(styleOf(html, 'Consent window')), 'a month is drawn over its whole length on the baseline');
  assert.ok(html.includes('class="lane-track" style="height:68px"'), 'the lane grows to hold three rows');
});

test('timeline: each marker shows a number and names it; the key lists date and description in date order under the lanes', () => {
  const html = denseHtml('2024-09-30'), tags = [...html.matchAll(/<a class="lane-event[^>]*>.*?<\/a>/g)].map(m => m[0]);
  const numberOf = label => /<span class="lane-no">(\d+)<\/span>/.exec(tags.find(t => t.includes(label)))[1];
  assert.deepEqual(['First filing', 'Notice issued', 'Notice repeated', 'Consent window', 'Maturity'].map(numberOf), ['1', '2', '3', '4', '5']);
  assert.ok(tags.find(t => t.includes('Notice issued')).includes('aria-label="Event 2: Sources: Notice issued, 2024-10-16 (day). View source"'));
  const key = html.split('<ol class="lane-key"')[1].split('</ol>')[0];
  assert.deepEqual([...key.matchAll(/<li>(.*?)<\/li>/g)].map(m => strip(m[1]).replace(/\s+/g, ' ').trim()), ['2022-03-01 First filing', '2024-10-16 Notice issued', '2024-10-18 Notice repeated', '2024-11 Consent window', '2025-02-10 Maturity']);
  assert.ok(html.indexOf('class="lane-key"') > html.indexOf('class="lane-row"'), 'the key follows the lanes');
});

test('timeline: the key numbers run across lanes and a lane with many events still lists every one', () => {
  const many = d => {
    d[outId('CP-0')] = runOutput('CP-0', { sections: [sec('Events: Security', 3, 400, 'consumed', [table(402, LANE_HEAD, Array.from({ length: 14 }, (_, i) => laneRow(403 + i, `2024-05-${String(i + 1).padStart(2, '0')}`, 'day', '—', `Item ${i + 1}`)))])], events: [{ lane: 'Security', table: 402, gap: null }] });
    return withLanes(d);
  };
  const html = runPage(many).eventLanesView(RUN);
  assert.equal(countOf(html, /<span class="lane-no">/g), 18);
  const keys = html.split('<p class="lane-key-name">').slice(1);
  assert.deepEqual(keys.map(k => /^([^<]*)</.exec(k)[1]), ['Security', 'Financing']);
  assert.deepEqual(keys.map(k => /<ol class="lane-key" start="(\d+)"/.exec(k)[1]), ['1', '15']);
  assert.deepEqual(keys.map(k => countOf(k, /<li>/g)), [14, 4]);
});

// ---- Package 6 views (2026-11-10): node/edge maps and the run status map. Every value is synthetic.
const MAP_HEAD = ['From', 'Relationship', 'Edge type', 'To', 'Evidence'];
const edgeRow = (line, from, link, type, to) => [line, from, link, type, to, 'Synthetic p.1'];
const LONG = 'Synthetic holding company with a deliberately very long registered name Limited';
const withMaps = d => {
  const cp1 = d[outId('CP-1')];
  cp1.sections.push(sec('Map: credit-risk transmission', 3, 400, 'consumed', [table(402, MAP_HEAD, [
    edgeRow(403, 'Synthetic driver', 'drives', 'Documentary Fact', 'Synthetic mechanism'),
    edgeRow(404, 'Synthetic mechanism', 'squeezes', 'Management Language', 'Synthetic outcome'),
    edgeRow(405, 'Synthetic driver', 'also hits', 'Analyst Interpretation', 'Synthetic outcome'),
    edgeRow(406, 'Synthetic outcome', 'feeds back', 'Insufficient Information', 'Synthetic driver'),
    edgeRow(407, LONG, 'owns', 'Documentary Fact', 'Synthetic driver'),
  ])]));
  cp1.sections.push(sec('Map: stress scenario', 3, 410, 'consumed', [table(412, MAP_HEAD, [[413, ...Array(5).fill('Not supplied: no scenario stated')]])]));
  cp1.maps = [{ name: 'credit-risk transmission', table: 402, gap: null }, { name: 'stress scenario', table: 412, gap: 'no scenario stated' }];
  return d;
};

test('maps: a layer is the longest path from a node with no incoming edge, and a cycle is cut at its last row', () => {
  const page = runPage();
  const ab = (from, to) => ({ from, to });
  const diamond = page.mapLayers([ab('A', 'B'), ab('B', 'C'), ab('A', 'C')]);
  assert.deepEqual([...diamond.layer], [['A', 0], ['B', 1], ['C', 2]]);
  const loop = page.mapLayers([ab('A', 'B'), ab('B', 'C'), ab('C', 'A'), ab('C', 'C')]);
  assert.deepEqual(loop.cut, [false, false, true, true]);
  assert.deepEqual([...loop.layer], [['A', 0], ['B', 1], ['C', 2]]);
  assert.deepEqual(page.mapLayers([ab('B', 'A'), ab('A', 'B')]).cut, [false, true], 'the first stated row is kept');
});

test('maps: one SVG, a box per node, a word and a line style per edge type, and the edge table beneath with the full text', () => {
  const html = runPage(withMaps).mapsView(outId('CP-1'), 'h3');
  const svg = /<svg.*?<\/svg>/s.exec(html)[0];
  assert.equal(countOf(svg, /<g class="map-node"/g), 4, 'driver, mechanism, outcome and the long holding company: the loop adds no node');
  for (const word of ['Documentary Fact', 'Management Language', 'Analyst Interpretation', 'Insufficient Information']) assert.ok(labelsOf(svg).some(l => l.lines.join(' ') === word), word);
  const dashes = [...svg.matchAll(/<path class="map-edge[^"]*"[^>]*>/g)].map(m => /stroke-dasharray="([^"]*)"/.exec(m[0])?.[1] ?? '');
  assert.equal(dashes.length, 5);
  assert.ok(new Set(dashes).size >= 4, 'each edge type has its own line style');
  assert.ok(!/stroke-width|opacity|weight/.test(svg), 'no weight, thickness or probability is drawn');
  assert.ok(!svg.replace(/<title>.*?<\/title>/g, '').includes(LONG) && svg.includes('…') && svg.includes(`<title>${LONG}</title>`), 'a long name is cut in the box and whole in its title');
  const table = /<table class="map-table".*?<\/table>/s.exec(html)[0];
  assert.ok(html.indexOf('<svg') < html.indexOf('<table class="map-table"'));
  assert.deepEqual([...table.matchAll(/<th scope="col">(.*?)<\/th>/g)].map(m => m[1]), MAP_HEAD);
  assert.equal(countOf(table, /<tr>/g), 6);
  assert.ok(table.includes(LONG) && table.includes('feeds back'));
  assert.ok(/<div class="map-scroll" role="region" aria-label="[^"]+" tabindex="0">/.test(html), 'the diagram scrolls inside its card and can be reached by keyboard');
  assert.ok(!/CP-\d/.test(strip(html)));
});

test('maps: a map of only Not supplied draws no diagram and says why', () => {
  const html = runPage(withMaps).mapsView(outId('CP-1'), 'h3');
  const gap = html.slice(html.indexOf('Stress scenario'));
  assert.ok(gap.includes('Not established for this run') && gap.includes('no scenario stated'));
  assert.ok(!gap.includes('<svg') && !gap.includes('Not supplied'));
});

test('maps: the new rules use only existing tokens, no amber or red', () => {
  const css = read('screen.css').split('\n').filter(line => /\.map-|\.state-shape|\.status-/.test(line));
  assert.ok(css.length >= 4, 'the new rules are found');
  for (const rule of css) assert.ok(!/amber|--red|\bred\b(?! Hat)|#[0-9a-f]{3,8}\b/i.test(rule), rule);
  assert.ok(css.some(rule => /\.map-edge/.test(rule)) && css.some(rule => /shape-open/.test(rule)));
});


test('maps: a wide map keeps its natural width and scrolls inside its card', () => {
  const rule = read('screen.css').split('\n').find(line => /\.map-scroll svg/.test(line));
  assert.ok(rule && !/max-width:\s*100%/.test(rule) && /flex:none|max-width:none/.test(rule), rule);
  const chain = [...Array(12)].map((_, i) => edgeRow(900 + i, `Layer ${i}`, 'next', 'Documentary Fact', `Layer ${i + 1}`));
  const html = runPage(d => { const o = d[outId('CP-1')]; o.sections.push(sec('Map: credit-risk transmission', 3, 890, 'consumed', [table(892, MAP_HEAD, chain)])); o.maps = [{ name: 'credit-risk transmission', table: 892, gap: null }]; return d; }).mapsView(outId('CP-1'), 'h3');
  assert.ok(Number(/<svg[^>]*width="(\d+)"/.exec(html)[1]) > 1440, 'twelve layers are wider than the page');
});

const mapHtml = rowsFor => runPage(d => { const o = d[outId('CP-1')]; o.sections.push(sec('Map: credit-risk transmission', 3, 890, 'consumed', [table(892, MAP_HEAD, rowsFor)])); o.maps = [{ name: 'credit-risk transmission', table: 892, gap: null }]; return d; }).mapsView(outId('CP-1'), 'h3');
const nodeLines = (svg, title) => { const g = [...svg.matchAll(/<g class="map-node"><title>(.*?)<\/title>.*?<\/g>/gs)].find(m => m[1] === title); return [...g[0].matchAll(/<tspan[^>]*>(.*?)<\/tspan>/g)].map(m => m[1]); };

// An edge label is a text whose first baseline is its x, y, one tspan per line (13px apart); its box is its longest line wide (6.6px a character) and 12px tall a line.
const labelsOf = svg => [...svg.matchAll(/<text class="map-edge-label" x="([\d.-]+)" y="([\d.-]+)"[^>]*>(.*?)<\/text>/g)].map(m => {
  const lines = [...m[3].matchAll(/<tspan[^>]*>(.*?)<\/tspan>/g)].map(t => t[1]);
  return { x: +m[1], y: +m[2], lines, w: Math.max(...lines.map(l => l.length)) * 6.6, top: +m[2] - 9, bot: +m[2] + 13 * (lines.length - 1) + 3 };
});
const labelHit = (a, b) => Math.abs(a.x - b.x) < (a.w + b.w) / 2 && a.top < b.bot && b.top < a.bot;

test('maps: node text wraps on whole words and numbers, in at most three lines', () => {
  const name = 'Net leverage 6.01x covenant headroom narrowing sharply';
  const html = mapHtml([edgeRow(900, name, 'drives', 'Documentary Fact', 'Synthetic outcome')]);
  const lines = nodeLines(/<svg.*?<\/svg>/s.exec(html)[0], name);
  assert.ok(lines.length >= 2 && lines.length <= 3, lines.join('|'));
  assert.equal(lines.join(' '), name, 'every word is whole and none is dropped');
  assert.ok(lines.some(line => line.split(' ').includes('6.01x')), '6.01x stays whole');
});

test('maps: node text over three lines ends with an ellipsis and the whole text is in its title', () => {
  const html = mapHtml([edgeRow(900, LONG, 'owns', 'Documentary Fact', 'Synthetic driver')]);
  const svg = /<svg.*?<\/svg>/s.exec(html)[0], lines = nodeLines(svg, LONG);
  assert.equal(lines.length, 3);
  assert.ok(lines[2].endsWith('\u2026') && !lines[0].includes('\u2026'), lines.join('|'));
  for (const line of lines) assert.ok(line.replace('\u2026', '').split(' ').every(word => LONG.split(' ').includes(word)), `no word is cut: ${line}`);
});

test('maps: edge labels do not overlap one another or a node', () => {
  const html = mapHtml([
    edgeRow(901, 'Synthetic driver', 'drives', 'Documentary Fact', 'Synthetic outcome'),
    edgeRow(902, 'Synthetic driver', 'also hits', 'Documentary Fact', 'Synthetic outcome'),
    edgeRow(903, 'Synthetic mechanism', 'squeezes', 'Documentary Fact', 'Synthetic outcome'),
    edgeRow(904, 'Synthetic driver', 'feeds', 'Documentary Fact', 'Synthetic mechanism'),
  ]);
  const svg = /<svg.*?<\/svg>/s.exec(html)[0];
  const labels = labelsOf(svg);
  assert.equal(labels.length, 4);
  for (let i = 0; i < labels.length; i++) for (let j = i + 1; j < labels.length; j++) assert.ok(!labelHit(labels[i], labels[j]), `labels ${i} and ${j}: ${JSON.stringify([labels[i], labels[j]])}`);
  const boxes = [...svg.matchAll(/<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.]+)" height="([\d.]+)"/g)].map(m => m.slice(1).map(Number));
  for (const l of labels) for (const [x, y, w, h] of boxes) assert.ok(!(l.x + l.w / 2 > x && l.x - l.w / 2 < x + w && l.bot > y && l.top < y + h), `a label sits on a node: ${JSON.stringify(l)}`);
});

test('maps: a map wider than its card is a keyboard-reachable scroll region that says so, as the bridge and tables do', () => {
  const chain = [...Array(6)].map((_, i) => edgeRow(900 + i, `Layer ${i}`, 'next', 'Documentary Fact', `Layer ${i + 1}`));
  const html = mapHtml(chain);
  assert.ok(/<div class="map-scroll" role="region" aria-label="[^"]*scroll horizontally[^"]*" tabindex="0">/.test(html), 'the region names the scroll');
  assert.ok(/scroll horizontally/.test(mapHtml([edgeRow(900, 'A', 'next', 'Documentary Fact', 'B')])), 'so does a short map, which may still scroll in a narrow card');
  assert.ok(/\.map-scroll\{[^}]*overflow-x:auto/.test(read('screen.css')));
});

const svgOf = html => /<svg.*?<\/svg>/s.exec(html)[0];
const widthOf = rowsFor => Number(/<svg[^>]*width="(\d+)"/.exec(mapHtml(rowsFor))[1]);
const chainOf = (n, type) => [...Array(n)].map((_, i) => edgeRow(900 + i, `Layer ${i}`, 'next', type, `Layer ${i + 1}`));

test('maps: the column gap follows the longest edge label, never under 120, so short-label maps stay compact', () => {
  // 4 layers, label "Fact" (4*6.6 = 26.4px) + 20 margin fits in the 120 minimum: 2*12 pad + 4*(150 box + 120 gap) - 120 = 984, the width before labels had their own room.
  assert.equal(widthOf(chainOf(3, 'Fact')), 984);
  // A single word wider than a label line stays whole and widens the gap: "Interpretations-and-views" is 25 characters, 25*6.6 = 165px; + 20 margin = 185 gap: 24 + 4*(150+185) - 185 = 1179.
  assert.equal(widthOf(chainOf(3, 'Interpretations-and-views')), 1179);
});

test('maps: an edge label wraps on whole words to two lines, so the gap follows the longest line, not the whole label', () => {
  // Old expectation 1122 (one line of 22 characters, gap 166) is now 984: the longest line is "Interpretation" (14 characters, 92.4px) + 20 margin = 112.4, under the 120 minimum: 24 + 4*(150+120) - 120 = 984.
  assert.equal(widthOf(chainOf(3, 'Analyst Interpretation')), 984);
  const svg = svgOf(mapHtml(chainOf(3, 'Analyst Interpretation')));
  assert.deepEqual(labelsOf(svg).map(l => l.lines), [...Array(3)].map(() => ['Analyst', 'Interpretation']), 'two tspans, whole words, nothing dropped');
  assert.equal(countOf(svg, /<tspan[^>]*>Analyst<\/tspan>/g), 3);
  // "Insufficient Information" (12 and 11 characters) and "Management Language" (19 characters, wraps) fit too.
  assert.equal(widthOf(chainOf(3, 'Insufficient Information')), 984);
  assert.equal(widthOf(chainOf(3, 'Management Language')), 984);
  // More than two lines ends in an ellipsis; the edge table holds the whole text.
  const three = labelsOf(svgOf(mapHtml(chainOf(1, 'one two three four five six seven'))))[0].lines;
  assert.equal(three.length, 2);
  assert.ok(three[1].endsWith('\u2026'), three.join('|'));
});

test('maps: a two-line label is placed by its real box: two of them into one target do not overlap or sit on a node', () => {
  const svg = svgOf(mapHtml([
    edgeRow(901, 'Synthetic driver', 'Analyst Interpretation', 'Documentary Fact', 'Synthetic outcome'),
    edgeRow(902, 'Synthetic mechanism', 'Management Language', 'Documentary Fact', 'Synthetic outcome'),
    edgeRow(903, 'Synthetic driver', 'Analyst Interpretation', 'Documentary Fact', 'Synthetic mechanism'),
  ]));
  const labels = labelsOf(svg);
  assert.equal(labels.length, 3);
  assert.ok(labels.every(l => l.lines.length === 2));
  for (let i = 0; i < 3; i++) for (let j = i + 1; j < 3; j++) assert.ok(!labelHit(labels[i], labels[j]), `labels ${i} and ${j}: ${JSON.stringify([labels[i], labels[j]])}`);
  const boxes = [...svg.matchAll(/<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.]+)" height="([\d.]+)"/g)].map(m => m.slice(1).map(Number));
  for (const l of labels) for (const [x, y, w, h] of boxes) assert.ok(!(l.x + l.w / 2 > x && l.x - l.w / 2 < x + w && l.bot > y && l.top < y + h), `a label sits on a node: ${JSON.stringify(l)}`);
});

test('maps: a node word wider than a line breaks across lines before any ellipsis; the bridge keeps its ellipsis', () => {
  const name = 'https://example.invalid/a/very/long/path/name.html';
  const lines = nodeLines(svgOf(mapHtml([edgeRow(900, name, 'drives', 'Documentary Fact', 'Synthetic outcome')])), name);
  assert.equal(lines.join(''), name, 'every character is shown');
  assert.ok(lines.length === 3 && lines.every(line => line.length <= 20 && !line.includes('\u2026')), lines.join('|'));
  const src = require('fs').readFileSync(require('path').join(__dirname, 'views.js'), 'utf8');
  const axisLines = new Function(src.slice(src.indexOf('const AXIS_CHAR'), src.indexOf('function bridgeChart')) + ';return axisLines;')();
  assert.deepEqual(axisLines('averyveryverylongunbrokenword', 100), ['averyveryv\u2026']);
});

test('maps: with many parallel edges every label still gets a clear spot, and the drawing grows to hold them', () => {
  const rows = [...Array(8)].map((_, i) => edgeRow(900 + i, 'A', 'drives', 'Analyst Interpretation', 'B'));
  const svg = svgOf(mapHtml(rows)), height = Number(/<svg[^>]*height="(\d+)"/.exec(svg)[1]);
  const labels = labelsOf(svg);
  assert.equal(labels.length, 8);
  for (let i = 0; i < 8; i++) for (let j = i + 1; j < 8; j++) assert.ok(!labelHit(labels[i], labels[j]), `labels ${i}, ${j} overlap`);
  assert.ok(Math.max(...labels.map(l => l.bot)) + 1 <= height, 'every label is inside the drawing');
});

test('maps: the region label has no stray punctuation', () => {
  const label = /<div class="map-scroll" role="region" aria-label="([^"]*)"/.exec(mapHtml(chainOf(1, 'Fact')))[1];
  assert.ok(!/[.;]\s*;|\.;/.test(label), label);
  assert.ok(/edges\. The edge table follows; scroll horizontally/.test(label), label);
});

// ---- Package 7 views (2026-11-10): the report manifest and the run/file context bar. Every value is synthetic.

const BAR_STORE = { inputs: { [`${RUN}/inputs/CP-1-input.md`]: { module: 'CP-1', run: RUN, source: 'inputs/CP-1-input.md', href: '../runs/run-a/inputs/CP-1-input.md', sha256: 'c'.repeat(64) } } };
const BAR = {
  runFields: { issuer: 'Synthetic Issuer', issuerKey: 'k1', title: 'Synthetic Issuer', run: 'Run A', asOf: '2025-12-31' },
  contexts: { 'run-b': { folder: 'run-b', issuer: 'Synthetic Issuer', issuerKey: 'k1', run: 'Run B', asOf: '2025-06-30', modules: {} }, 'run-c': { folder: 'run-c', issuer: 'Other', issuerKey: 'k2', run: 'Run C', asOf: '2025-01-31', modules: {} } },
  store: BAR_STORE,
};
const withInput = m => Object.fromEntries(Object.entries(m).map(([code, entry]) => [code, { ...entry, inputs: code === 'CP-1' ? [`${RUN}/inputs/CP-1-input.md`] : [] }]));
const barPage = (reports = [], shape = withInput) => runPage(d => d, reports, shape, BAR);

// ---- Run label and Report history (T2; ruling decisions 4, 12 and H7). Every value is synthetic and written here.
const textBlock = (line, text) => ({ type: 'text', line, end: line, text });
const newFormat = bottom => [sec('Findings', 2, 5, 'x', []), sec('Bottom line', 3, 6, 'x', [textBlock(7, bottom)])];
const entryOf = id => ({ outputs: [id], default: id });
const HIST_B0 = 'run-b/deliveries/d1/CP-0.md', HIST_B2 = 'run-b/deliveries/d1/CP-2A.md', HIST_D0 = 'run-d/deliveries/d1/CP-0.md';
const histOut = (id, code, bottom) => runOutput(code, { run: id.split('/')[0], source: id.split('/').slice(1).join('/'), href: `../runs/${id}`, sections: newFormat(bottom), state: { established: null, declared: null }, summary: null });
const synthetic = { issuer: 'Synthetic Issuer', issuerKey: 'k1', title: 'Synthetic Issuer', pathway: 'credit_snapshot' };
const HIST = {
  runFields: { ...synthetic, run: 'Run A', asOf: '2025-12-31' },
  contexts: {
    'run-b': { folder: 'run-b', ...synthetic, run: 'Run B', asOf: '2025-03-31', record: { steps: [{ module: 'CP-0' }, { module: 'CP-2A' }] }, modules: { 'CP-0': entryOf(HIST_B0), 'CP-2A': entryOf(HIST_B2) } },
    'run-d': { folder: 'run-d', ...synthetic, run: 'Run D', asOf: '2025-03-31', modules: { 'CP-0': entryOf(HIST_D0) } },
    'run-c': { folder: 'run-c', ...synthetic, run: 'Run C', asOf: null, pathway: null, modules: {} },
    'run-x': { folder: 'run-x', issuer: 'Other', issuerKey: 'k2', title: 'Other', run: 'Run X', asOf: '2026-01-01', pathway: 'credit_snapshot', modules: {} },
  },
  data: {
    [HIST_B0]: histOut(HIST_B0, 'CP-0', 'Sources are ready.'),
    [HIST_B2]: histOut(HIST_B2, 'CP-2A', 'Not assessable: no inputs were supplied.'),
    [HIST_D0]: histOut(HIST_D0, 'CP-0', 'Sources are ready.'),
  },
};
const histPage = () => runPage(d => d, [], m => m, HIST);
// The run timeline's entries (library redesign Task 11): each `<li class="tl-i">` with its date, pathway, marks row, module dots and links.
const histRows = html => html.split('<li class="tl-i"').slice(1).map(chunk => {
  const part = re => (re.exec(chunk) || [])[1];
  return { attrs: chunk.slice(0, chunk.indexOf('>')), html: chunk, date: part(/<div class="tl-d">(.*?)<\/div>/s), pathway: part(/<p class="tl-t">(.*?)<\/p>/s), marks: part(/<div class="hist-marks">(.*?)<\/div><div class="hist-dots">/s), dots: part(/<div class="hist-dots">(.*?)<\/div><div class="hist-links">/s), links: part(/<div class="hist-links">(.*?)<\/div><\/div><\/li>|<div class="hist-links">(.*)$/s) };
});
const dotLabels = html => [...(html || '').matchAll(/<span role="img" tabindex="0" data-tip="([^"]*)"/g)].map(m => m[1]);

test('Report history: one entry per run of the issuer, latest as-of date first, a run with no date last; another issuer\'s run is not listed', () => {
  const rows = histRows(histPage().historyView(RUN));
  assert.deepEqual(rows.map(r => /href="(#W-Overview[^"]+)"/.exec(r.links)[1]), ['#W-Overview/overview?c=run-a', '#W-Overview/overview?c=run-b', '#W-Overview/overview?c=run-d', '#W-Overview/overview?c=run-c']);
});

test('Report history: a vertical run timeline with the date as written, the pathway and the modules as dots, never as a text list', () => {
  const html = histPage().historyView(RUN);
  assert.ok(html.includes('<ol class="tl tl-v">') && html.includes('aria-label="Runs of Synthetic Issuer, latest as-of date first"') && !html.includes('<table'));
  assert.ok(html.includes('<span data-count>4</span> runs'));
  const [a, b, d, c] = histRows(html);
  assert.deepEqual([strip(a.date), strip(a.pathway)], ['31 December 2025', 'Full credit assessment']);
  assert.deepEqual([strip(b.date), strip(d.date)], ['31 March 2025', '31 March 2025']);
  assert.deepEqual([strip(c.date), strip(c.pathway)], ['Not recorded', 'Not recorded']);
  const titles = row => dotLabels(row.dots).map(label => label.split(': ')[0]);
  assert.deepEqual(titles(a), ['Financial foundation', 'Downside', 'Committee decision', 'Unnamed module']);
  assert.deepEqual(titles(b), ['Source readiness', 'Downside'], 'in the catalogue\'s order');
  assert.deepEqual(titles(d), ['Source readiness'], 'a partial re-run is its own entry with the modules it ran');
  assert.ok(!/<li>|history-modules/.test(a.dots + b.dots + d.dots), 'no text list of module names');
  assert.ok(c.dots.includes('No module output is retained for this run.') && dotLabels(c.dots).length === 0, 'a run with no modules says so');
  assert.ok(!/CP-/.test(a.html + b.html + d.html + c.html), 'R2: no module code on the page');
});

test('Report history: two runs with one name are told apart by Latest and Earlier, and by nothing else', () => {
  const [a, b, d, c] = histRows(histPage().historyView(RUN));
  assert.ok(!/Latest|Earlier(?! format| methods)/.test(strip(a.marks) + strip(c.marks)), 'a name held once has no word');
  assert.ok(strip(b.marks).includes('Latest') && strip(d.marks).includes('Earlier') && !strip(d.marks).includes('Latest'));
  assert.ok(!/Run [A-D]/.test(a.html + b.html + d.html + c.html), 'no run code to tell them apart');
});

test('Report history: What changed opens the run\'s Changes page, and is absent for a run whose record holds no comparison', () => {
  // Runs A and B record a comparison (a pack); D and C record none.
  const recorded = { first_run: false, pack: { prior: { run: 'x', as_of: '2024-01-01', pathway: 'credit_snapshot' }, measures: [] } };
  const page = runPage(d => d, [], m => m, { ...HIST, runFields: { ...HIST.runFields, changes: recorded }, contexts: { ...HIST.contexts, 'run-b': { ...HIST.contexts['run-b'], changes: recorded } } });
  const [a, b, d, c] = histRows(page.historyView(RUN));
  assert.ok(a.links.includes('<a class="text-action" href="#W-Changes/changes?c=run-a" aria-label="What changed in the run of 31 December 2025, Full credit assessment">What changed'));
  assert.ok(b.links.includes('href="#W-Changes/changes?c=run-b"'), 'run-d is the earlier run of the same pathway');
  assert.ok(!d.links.includes('What changed') && !c.links.includes('What changed'), 'a run whose record holds no comparison, and a run of no pathway, have nothing for the Changes page to show');
  const one = runPage(d => d, [], m => m, { catalogue: [zedRun()], runFields: { ...synthetic, asOf: '2025-01-01' } }).historyView(RUN);
  assert.equal(histRows(one).length, 1, 'an issuer with one run draws one entry, not an empty state');
  assert.ok(!one.includes('What changed') && !one.includes('empty-state'));
});

test('Report history: the status is Completed, plus the count not assessable; Earlier format only where H7 holds; the lead module\'s declared state is the entry\'s mark', () => {
  const [a, b, d, c] = histRows(histPage().historyView(RUN));
  assert.equal(strip(a.marks), 'Completed · 2 not assessable Earlier format Showing', 'earlier format: the store\'s own state decides, and the Reader summary is not a Bottom line');
  assert.equal(strip(b.marks), 'Completed · 1 not assessable Latest', 'new format: the Bottom line says not assessable');
  assert.equal(strip(d.marks), 'Completed Earlier');
  assert.equal(strip(c.marks), 'Completed', 'a run with no handoff is not called earlier format');
});

test('Report history: the lead module\'s declared state is the entry\'s mark, drawn with its icon and word; no declared state, no mark', () => {
  const E6 = 'run-e/deliveries/d1/CP-6.md';
  const withE = declared => runPage(d => d, [], m => m, { ...HIST, contexts: { ...HIST.contexts, 'run-e': { folder: 'run-e', ...synthetic, run: 'Run E', asOf: '2026-06-30', modules: { 'CP-6': entryOf(E6) } } },
    data: { ...HIST.data, [E6]: { ...histOut(E6, 'CP-6', 'Hold the position. Leverage is high.'), state: { established: true, declared } } } }).historyView(RUN);
  const [first] = histRows(withE('Restricted'));
  assert.ok(first.marks.startsWith('<span class="state warn"><svg') && strip(first.marks).startsWith('Restricted Completed'), first.marks);
  assert.ok(!histRows(withE(null))[0].marks.includes('class="state'), 'a run with no declared state has no badge');
});

test('Earlier methods: the badge sits beside Earlier format in the Report history status and the run label, only where methods changed', () => {
  HIST.contexts['run-b'].methodChanges = ['CP-0: methods/cp0.md changed'];
  HIST.runFields.methodChanges = ['CP-0: methods/cp0.md changed'];
  try {
    const page = histPage();
    const [a, b, d] = histRows(page.historyView(RUN));
    assert.equal(strip(a.marks), 'Completed · 2 not assessable Earlier format Earlier methods Showing');
    assert.equal(strip(b.marks), 'Completed · 1 not assessable Earlier methods Latest');
    assert.equal(strip(d.marks), 'Completed Earlier', 'no list, no badge');
    assert.ok(b.marks.includes('<span class="badge badge-gray earlier-methods">Earlier methods</span>'));
    assert.equal(strip(page.runLabel('W-Evidence', RUN).replace(/<a [^>]*>.*?<\/a>/, '')), 'Showing run: 31 December 2025 · Full credit assessment · Run A Earlier format Earlier methods');
    assert.equal(strip(page.runLabel('W-Forecast', 'run-b').replace(/<a [^>]*>.*?<\/a>/, '')), 'Showing run: 31 March 2025 · Full credit assessment Earlier methods');
    assert.equal(strip(page.runLabel('W-Forecast', 'run-d').replace(/<a [^>]*>.*?<\/a>/, '')), 'Showing run: 31 March 2025 · Full credit assessment');
  } finally {
    delete HIST.contexts['run-b'].methodChanges;
    delete HIST.runFields.methodChanges;
  }
});

test('Report history: the selected run\'s entry is marked aria-current and every entry opens a run with a real link named by its date and pathway, never its code', () => {
  const html = histPage().historyView('run-b');
  const rows = histRows(html);
  assert.deepEqual(rows.map(r => r.attrs.includes('aria-current="true"')), [false, true, false, false]);
  for (const row of rows) assert.ok(/<a class="text-action" href="#W-Overview\/overview\?c=run-[a-d]" aria-label="Open run: [^"]+">Open overview/.test(row.links), row.links);
  assert.ok(rows[1].links.includes('aria-label="Open run: 31 March 2025, Full credit assessment"'));
  assert.ok(rows[1].marks.includes('<span class="badge badge-gray">Showing</span>') && !rows[0].marks.includes('Showing'));
});

test('M6: a handoff the build could not read is not an Earlier format; a run with an old-format handoff beside it still is', () => {
  const unread = [{ heading: 'Unstructured handoff', level: 1, line: 1, blocks: [{ type: 'text', line: 1, text: '## Request\nx' }] }];
  const page = swap => runPage(d => d, [], m => m, { ...HIST, data: { ...HIST.data, [HIST_D0]: { ...HIST.data[HIST_D0], sections: swap } } }).runLabel('W-Evidence', 'run-d');
  assert.ok(!page(unread).includes('Earlier format'), 'one unreadable handoff does not make the run an earlier format');
  const old = [{ heading: 'Findings', level: 2, line: 1, blocks: [{ type: 'text', line: 2, text: 'An older handoff.' }] }];
  assert.ok(page(old).includes('Earlier format'), 'an old-format handoff still is');
});

test('run label: the run\'s date, pathway and code, the Earlier format badge only where H7 holds, and the link to the Report history', () => {
  const page = histPage();
  const earlier = page.runLabel('W-Evidence', RUN);
  assert.equal(strip(earlier.replace(/<a [^>]*>.*?<\/a>/, '')), 'Showing run: 31 December 2025 · Full credit assessment · Run A Earlier format');
  assert.ok(earlier.includes('<a class="text-action" href="#W-Report/history?c=run-a">All runs of this issuer</a>'));
  assert.equal(strip(page.runLabel('W-Forecast', 'run-b').replace(/<a [^>]*>.*?<\/a>/, '')), 'Showing run: 31 March 2025 · Full credit assessment', 'the run code is the Evidence page\'s: no code on the Forecast page');
  assert.equal(strip(page.runLabel('W-Overview', 'run-c').replace(/<a [^>]*>.*?<\/a>/, '')), 'Showing run: Not recorded · Not recorded');
  assert.ok(page.runLabel('CP-1', 'run-b').includes('href="#W-Report/history?c=run-b"'));
});

test('run label: a short snapshot run is labelled Short credit snapshot, not the id as words', () => {
  const page = runPage(d => d, [], m => m, { ...HIST, runFields: { ...synthetic, pathway: 'short_snapshot', run: 'Run S', asOf: '2025-12-31' } });
  assert.ok(strip(page.runLabel('W-Overview', RUN)).startsWith('Showing run: 31 December 2025 · Short credit snapshot') && !strip(page.runLabel('W-Overview', RUN)).includes('Run S'));
});

test('run label: no run picker or file pop-over remains, no run chosen draws nothing, and the bar is hidden on the history page itself', () => {
  const html = histPage().runLabel('W-Overview', RUN);
  assert.ok(!/context-pop|context-list|context-role|Other runs of this issuer|Files \(|<summary/.test(html));
  assert.equal(histPage().runLabel('W-Overview', null), '');
  assert.ok(read('index.html').includes('id="context-bar"'));
  assert.ok(read('views.js').includes("$('context-bar').hidden=isHome||module==='W-Report';"));
  assert.ok(!/contextBar/.test(read('views.js') + read('screen.js')));
});

test('run label: a recorded rerun and a recorded supersession are linked or named, and no revision order is claimed when none is recorded', () => {
  assert.ok(!/revision|Rerun|Supersedes/.test(strip(histPage().runLabel('W-Overview', RUN))));
  const page = runPage(d => d, [], m => m, { ...HIST, runFields: { ...HIST.runFields, revisions: [{ word: 'Rerun of', id: 'id-b', run: 'run-b' }, { word: 'Supersedes', id: 'id-x', run: null }] } });
  const text = page.runLabel('W-Overview', RUN);
  assert.ok(/<a href="#W-Overview\/[^"]*c=run-b[^"]*">Rerun of 31 March 2025<\/a>/.test(text), 'a recorded run in the library is a link that keeps that run, named by its date, not its code');
  assert.ok(strip(text).includes('Supersedes id-x') && !/<a[^>]*>Supersedes/.test(text), 'a recorded run the library does not hold is named, not linked');
});

test('Report history: the page is the W-Report destination with one section, the history', () => {
  assert.ok(read('views.js').includes("'W-Report':['Report history',[['history','Report history',[]]]]"));
  assert.ok(read('views.js').includes("if(module==='W-Report')return historyView(context);"));
  assert.ok(read('screen.css').includes('.history-table,.dates-table{') && read('screen.css').includes('.history .tl-d{'));
});

test('package 7: the new rules use only existing tokens, no amber or red', () => {
  const css = read('screen.css').split('\n').filter(line => /\.index-|\.context-|\.history-/.test(line));
  assert.ok(css.length >= 4 && css.some(rule => /\.context-bar/.test(rule)));  // the .index- clause is gone with the dead .index-table rule it kept alive
  for (const rule of css) assert.ok(!/amber|--red|\bred\b(?! Hat)|#[0-9a-f]{3,8}\b|badge-attention/i.test(rule), rule);
});


// ---- The run header's meta line (redesign pass 1): ticker, sector and the run count, each only when the catalogue holds it. Expected text written by hand.
test('the meta line under the issuer title joins ticker, sector and run count with a dot, and leaves out what the catalogue does not hold', () => {
  const all = runPage(d => d, [], m => m, { catalogue: [zedRun()] });
  assert.equal(all.issuerMeta(RUN), 'ZED · Telecoms · 1 run');
  const none = runPage(d => d, [], m => m, { catalogue: [zedRun({ issuer: '', sector: '' })] });
  assert.equal(none.issuerMeta(RUN), '1 run');
  const sectorOnly = runPage(d => d, [], m => m, { catalogue: [zedRun({ issuer: '' })] });
  assert.equal(sectorOnly.issuerMeta(RUN), 'Telecoms · 1 run');
  // Two catalogue runs of the same issuer are counted; a run of another issuer is not.
  const held = (folder, issuerKey) => ({ folder, issuerKey, modules: {} });
  const three = runPage(d => d, [], m => m, {
    runFields: { issuerKey: 'zed' },
    contexts: { 'run-b': held('run-b', 'zed'), 'run-c': held('run-c', 'other') },
    catalogue: [zedRun(), zedRun({ id: 'run-b' }), zedRun({ id: 'run-c', issuer: 'OTH' })],
  });
  assert.equal(three.issuerMeta(RUN), 'ZED · Telecoms · 2 runs');
  // No catalogue row for the run: nothing is guessed, no line.
  assert.equal(runPage(d => d, [], m => m, { catalogue: [] }).issuerMeta(RUN), '');
});

test('the run count in the meta line is the number of rows Report history lists, whatever the catalogue holds', () => {
  const held = (folder, issuerKey) => ({ folder, issuerKey, asOf: '2025-01-01', modules: {} });
  // The catalogue holds three runs of the issuer, the library's contexts hold two: Report history lists two.
  const fewer = runPage(d => d, [], m => m, {
    runFields: { issuerKey: 'zed' }, contexts: { 'run-b': held('run-b', 'zed') },
    catalogue: [zedRun(), zedRun({ id: 'run-b' }), zedRun({ id: 'run-c' })],
  });
  assert.equal(fewer.issuerMeta(RUN), 'ZED · Telecoms · 2 runs');
  assert.equal(histRows(fewer.historyView(RUN)).length, 2);
  // The catalogue holds one run, the contexts three: three.
  const more = runPage(d => d, [], m => m, {
    runFields: { issuerKey: 'zed' }, contexts: { 'run-b': held('run-b', 'zed'), 'run-c': held('run-c', 'zed') },
    catalogue: [zedRun()],
  });
  assert.equal(more.issuerMeta(RUN), 'ZED · Telecoms · 3 runs');
  assert.equal(histRows(more.historyView(RUN)).length, 3);
});

// ---- "Start a run on this issuer" in the run header: the target is the latest run Report history lists, URL-encoded; drawn only over http.
test('the start-run target is the latest run of the issuer by Report history order, its folder URL-encoded', () => {
  const held = (folder, asOf, issuerKey = 'zed') => ({ folder, issuerKey, asOf, modules: {} });
  const page = runPage(d => d, [], m => m, {
    runFields: { issuerKey: 'zed', asOf: '2025-01-01' },
    contexts: { 'run b/2': held('run b/2', '2025-06-30'), 'run-c': held('run-c', '2026-01-31', 'other') },
    catalogue: [zedRun()],
  });
  // The latest as-of date of the issuer's runs is 'run b/2' (the other issuer's later run is not the issuer's).
  assert.equal(page.startRunHref(RUN), '/?from=run%20b%2F2');
  // The first row Report history draws is that same run.
  assert.ok(histRows(page.historyView(RUN))[0].links.includes('c=run+b%2F2'), histRows(page.historyView(RUN))[0].links); // the route's own query encoding
  // With one run, that run.
  assert.equal(runPage(d => d, [], m => m, { catalogue: [zedRun()] }).startRunHref(RUN), '/?from=run-a');
  // No such run in the library: no target.
  assert.equal(page.startRunHref('missing'), '');
});

test('the start-run link is a primary action with a plus icon, drawn only when the library is served over http and the issuer has a run', () => {
  const served = runPage(d => d, [], m => m, { location: { protocol: 'http:' } });
  assert.equal(served.startRunLink(RUN), '<a class="start-run primary-action" href="/?from=run-a"><img src="icons/plus.svg">Start a run on this issuer</a>');
  assert.equal(runPage(d => d, [], m => m, { location: { protocol: 'https:' } }).startRunLink(RUN), served.startRunLink(RUN));
  assert.equal(runPage(d => d, [], m => m, { location: { protocol: 'file:' } }).startRunLink(RUN), '');
  assert.equal(runPage(d => d, [], m => m).startRunLink(RUN), '', 'no location: not served');
  assert.equal(served.startRunLink('missing'), '', 'no run, no link');
  // Report history no longer draws it: the header carries it on every run tab.
  assert.ok(!served.historyView(RUN).includes('start-run'));
  const chrome = read('views.js').slice(read('views.js').indexOf('function updateWorkspaceChrome'));
  // The header's link markup is what startRunLink returns: it is assigned from the call, drawn through that variable in the
  // side group, and nowhere written out by hand in the chrome.
  assert.ok(chrome.includes("const startRun=isHome?'':startRunLink(current.context)"), 'startRun is startRunLink(current.context)');
  assert.ok(chrome.includes("startRun?`<div class=\"issuer-side\">${startRun}</div>`:''"), 'the side group draws ${startRun} and exists only with the link');
  assert.ok(!chrome.includes('start-run'), 'no hand-written link in the header');
  assert.ok(!chrome.includes('/?from='), 'no hand-written target in the header');
});

// ---- The module page (redesign pass 1, task 2). Expected text is written by hand.
test('a fold draws its title and its detail as two spans, the detail at the right', () => {
  const r = report();
  const row = r.fold('reference', 'Statements and registers', '3 tables · 40 rows', '<p>body</p>');
  // The caller's title and detail are the two halves of the old summary text "Statements and registers · 3 tables · 40 rows".
  assert.ok(row.includes('<span class="fold-title">Statements and registers</span> <span class="fold-detail">3 tables · 40 rows</span></summary>'), row);
  // The summary's accessible name reads title, one space, detail.
  assert.equal(strip(row.match(/<summary>(.*?)<\/summary>/)[1]), 'Statements and registers 3 tables · 40 rows');
  assert.match(strip(r.reportAudit(OUT).match(/<summary>(.*?)<\/summary>/)[1]), /^Evidence &amp; audit \d+ sections · unchanged from the handoff$/);
  assert.ok(row.startsWith('<details class="fold" id="reference">') && row.endsWith('<p>body</p></details>'));
  const plainRow = r.fold('handoff-text', 'Full handoff text', '', '');
  assert.ok(plainRow.includes('<span class="fold-title">Full handoff text</span></summary>') && !plainRow.includes('fold-detail'), plainRow);
  // The audit row has the same two parts: its title, then the detail it always had.
  const audit = r.reportAudit(OUT);
  assert.ok(audit.includes('<span class="fold-title">Evidence &amp; audit</span> <span class="fold-detail">10 sections · unchanged from the handoff</span></summary>'), audit); // the fixture's ten sections, counted by hand
});

test('the head names the reading group, and says whether the page has a bottom line', () => {
  const withLine = report().reportHead(OUT);
  assert.ok(/<div class="module-head has-bottom-line" id="head">/.test(withLine), withLine);
  assert.ok(withLine.includes('<span class="head-group">Financial performance</span><h2>Financial foundation</h2>'), withLine);
  const none = report({ summary: null, call: null }).reportHead(OUT);
  assert.ok(!none.includes('has-bottom-line') && none.includes('<span class="head-group">Financial performance</span><h2>'), none);
  const call = report({ summary: null, call: { text: 'A call.', line: 9 } }).reportHead(OUT);
  assert.ok(call.includes('has-bottom-line'), call);
  // The tools keep today's controls.
  assert.ok(withLine.includes('class="head-tools"') && withLine.includes('Candidate · not accepted') && /<a class="btn" href="\.\.\/runs\/run-a\/deliveries\/d1\/CP-1\.md" download>/.test(withLine));
  // A module no reading group names is gathered under the runtime group "Other modules".
  const unnamed = report({ module: 'CP-6' }).reportHead(OUT);
  assert.ok(unnamed.includes('<span class="head-group">Other modules</span><h2>Committee decision</h2>'), unnamed);
});

test('a new-format page has a bottom line when the Bottom line passage exists; a Not assessable module shows its badge in the head tools', () => {
  const text = (body, line) => ({ type: 'text', line, end: line, text: body });
  const sec = (heading, level, line, ...blocks) => ({ heading, level, line, blocks, where: 'view' });
  const sections = bottom => [sec('CP-1 handoff', 1, 1), sec('Request', 2, 2, text('x', 3)), sec('Findings', 2, 5), sec('Bottom line', 3, 6, text(bottom, 7)), sec('Key findings', 3, 9, text('- one', 10))];
  const blockedHead = report({ sections: sections('Not assessable: no cash forecast.'), summary: null }).reportHead(OUT);
  assert.ok(/<div class="head-tools"><span class="badge badge-gray">Not assessable<\/span>/.test(blockedHead) && blockedHead.includes('has-bottom-line'), blockedHead);
  const ordinary = report({ sections: sections('Leverage is moderate.'), summary: null }).reportHead(OUT);
  assert.ok(!ordinary.includes('Not assessable') && ordinary.includes('has-bottom-line'), ordinary);
  const noPassage = report({ sections: sections('x').filter(s => s.heading !== 'Bottom line'), summary: null }).reportHead(OUT);
  assert.ok(!noPassage.includes('has-bottom-line'), noPassage);
});

test('the earlier-format band keeps its words and is not navy; a finding is one item with its confidence as text and a Basis control', () => {
  const r = report();
  const band = r.reportBand(OUT);
  assert.ok(band.includes('<dt>Confidence</dt><dd>Medium</dd>') && band.includes('<dt>Main limitation</dt>') && band.includes('Quoted from the handoff') && band.includes('View source'));
  assert.ok(band.includes('<span class="badge badge-gray">Quoted from the handoff</span>') && !band.includes('on-navy'));
  const article = r.moduleReport(OUT).match(/<article class="finding">.*?<\/article>/s)[0];
  assert.ok(article.includes('<h4>Leverage rose.</h4>') && article.includes('<span class="conf">Confidence High</span>') && article.includes('class="basis-link"'), article);
  const css = read('screen.css'), redesign = css.slice(css.indexOf('/* Redesign pass 1'));
  assert.ok(/\.band\{[^}]*background:none/.test(redesign) && !/\.band\{[^}]*navy/.test(redesign));
});

// ---- Task A1 (ruling 2026-11-12, decisions 1 and 2): a drawing is shown once, routing text sits in an audit fold, a chart with no numbers has a card.
const a1Sections = (extra = []) => [
  sec('Front matter', 2, 90, 'audit', [text(91, 'title: Credit view\nfilename: CP-1-credit.md\nstatus: draft')]),
  sec('Request', 2, 30, 'audit', [text(31, 'Assess the credit.')]),
  ...passageSections({ bottom: 'Cash is up.', key: ['Leverage rose.'], limits: ['Synthetic.'] }),
  sec('Chart data: leverage', 3, 40, 'consumed', [chartTable(42, [[43, 'FY2024', '6.57', 'x', 'K']]), text(44, 'Leverage is the highest in five years.')]),
  sec('Chart data: cover', 3, 50, 'consumed', [chartTable(52, [[53, 'FY2024', '2.1', 'x', 'K']])]),
  sec('Events: Financing', 3, 300, 'consumed', [table(302, LANE_HEAD, [laneRow(303, '2025-03-31', 'day', '—', 'Note matures'), laneRow(304, '2025-06', 'month', '2025-05-01', 'Call window')]), text(305, 'Both dates are scheduled.')]),
  sec('Map: credit-risk transmission', 3, 400, 'consumed', [table(402, MAP_HEAD, [edgeRow(403, 'Driver', 'drives', 'Documentary Fact', 'Outcome')]), text(404, 'The driver is the only one stated.')]),
  sec('Sources', 2, 60, 'audit', [text(62, 'K.')]),
  sec('Next module', 2, 70, 'audit', [text(71, 'Pass to Liquidity.')]),
  ...extra,
];
const a1Set = { charts: [{ title: 'Leverage', unit: 'x', table: 42, columns: [1] }, { title: 'Cover', unit: 'x', table: 52, columns: [1] }], events: [{ lane: 'Financing', table: 302, gap: null }], maps: [{ name: 'credit-risk transmission', table: 402, gap: null }] };
const a1Page = (sections = a1Sections(), set = a1Set) => runPage(() => { const d = overviewData({ 'CP-1': sections }); Object.assign(d[outId('CP-1')], set); return d; }, [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES });
const a1Id = outId('CP-1');

test('module page (A1, decision 1 and 2; Task 4): the outline lists no Chart data, Map, Events, Request, Next module, Front matter or Sources entry; the drawings stand in handoff order and Limitations is last', () => {
  const parts = a1Page().reportParts(a1Id);
  assert.deepEqual(parts.map(p => p[1]), ['Module', 'Bottom line', 'Key findings', 'Charts', 'Timeline', 'Maps', 'Limitations']);
  assert.equal(parts.at(-1)[0], 'limitations');
});

test('module page (Task 4): a drawing stands where its section stood among the finding sections, not before them all', () => {
  const sections = a1Sections();
  sections.splice(sections.findIndex(x => x.heading === 'Chart data: leverage'), 0, sec('Early finding', 3, 20, 'view', [text(21, 'An early finding.')]));
  sections.splice(sections.findIndex(x => x.heading === 'Sources'), 0, sec('Late finding', 3, 500, 'view', [text(501, 'A late finding.')]));
  assert.deepEqual(a1Page(sections).reportParts(a1Id).map(p => p[0]), ['head', 'bottom-line', 'key-findings', 's-20', 'charts', 'timeline', 'maps', 's-500', 'limitations']);
});

test('module page (A1; Task 7): the body has no "Chart data:" heading, and every chart is a card with one trace control, no Table form and no source chip', () => {
  const html = a1Page().moduleReport(a1Id), charts = /<section class="part" id="charts">.*?<\/section>/s.exec(html)[0];
  assert.ok(!html.includes('Chart data:') && !html.includes('Map: ') && !html.includes('Events: '), 'no drawing section is printed again');
  assert.equal(countOf(charts, /<div class="panel-card"/g), 2);
  assert.equal(countOf(charts, /<summary>Table form<\/summary>/g), 0, 'the table as written is in Evidence');
  assert.equal(countOf(charts, /class="chips"/g) + countOf(charts, /data-chip=/g) + countOf(charts, /class="chart-table"/g), 0);
  assert.ok(!charts.includes('.jsonl') && !charts.includes('Chip dot'), 'no file name, no chip key');
  assert.equal(countOf(charts, /<button type="button" class="basis-link trace-row"[^>]*aria-label="(?:Leverage|Cover): where it comes from"/g), 2, 'one trace control a chart, in its heading');
});

test('module page (A1): each chart card, map card and timeline lane carries its section anchor, so s-<line> routes stay', () => {
  const page = a1Page(), html = page.moduleReport(a1Id);
  for (const line of [40, 50]) assert.ok(html.includes(`<div class="panel-card" id="s-${line}">`), `chart ${line}`);
  assert.ok(html.includes('<div class="map-card" id="s-400">') && html.includes('<div class="tl-card" id="s-300">'));
  const anchors = page.drawnAnchors(a1Id);
  for (const line of [40, 50, 300, 400]) assert.ok(anchors.has(`s-${line}`), `s-${line}`);
  for (const line of [30, 60, 70, 90]) assert.ok(!anchors.has(`s-${line}`), `s-${line} (Request, Sources, Next module, Front matter) is not drawn, so it is not a route`);
});

test('module page (A1): prose written under a drawing\'s table is its caption', () => {
  const html = a1Page().moduleReport(a1Id), within = (from, to, needle) => html.slice(html.indexOf(from), html.indexOf(to)).includes(needle);
  assert.ok(within('<div class="panel-card" id="s-40">', '<div class="panel-card" id="s-50">', 'Leverage is the highest in five years.'));
  assert.ok(!within('<div class="panel-card" id="s-50">', 'id="s-300"', 'Leverage is the highest'));
  assert.ok(html.slice(html.indexOf('<div class="tl-card" id="s-300">')).includes('Both dates are scheduled.'));
  assert.ok(html.slice(html.indexOf('<div class="map-card" id="s-400">')).includes('The driver is the only one stated.'));
});

test('module page (A1): a chart with no numbers is a card saying Not established for this run with its reason, in table-line order', () => {
  const sections = a1Sections([sec('Chart data: covenant headroom', 3, 35, 'consumed', [chartTable(37, [[38, 'FY2024', 'Not supplied: no covenant is stated', 'x', 'K']])])]);
  const page = a1Page(sections, { ...a1Set, chartGaps: [{ title: 'Covenant headroom', table: 37 }].map(g => ({ ...g, gap: 'no covenant is stated' })) });
  const html = page.moduleReport(a1Id), charts = /<section class="part" id="charts">.*?<\/section>/s.exec(html)[0];
  const order = [...charts.matchAll(/<div class="panel-card" id="s-(\d+)">/g)].map(m => m[1]);
  assert.deepEqual(order, ['35', '40', '50'], 'the gap card sits where its table is');
  const card = new RegExp('<div class="panel-card" id="s-35">.*?(?=<div class="panel-card" id="s-40">)', 's').exec(charts)[0];
  assert.ok(strip(card).includes('Covenant headroom') && strip(card).includes('Not established for this run') && countOf(strip(card), /Not supplied: no covenant is stated/g) === 1 && !card.includes('<details'), 'the stated cell is the reason, verbatim and once; the table as written is in Evidence (Task 7)');
  assert.ok(!html.includes('Chart data:'));
});

test('module page (A1): a drawing the store could not draw keeps its section in the body', () => {
  const html = a1Page(a1Sections(), { ...a1Set, charts: [a1Set.charts[0]] }).moduleReport(a1Id);
  assert.ok(html.includes('Chart data: cover'), 'no card, no gap entry: the section is still printed');
  assert.ok(!html.includes('Chart data: leverage'));
});

test('module page (A1; Task 7): the timeline draws each event once, as the component, with no Table form fold and no event table', () => {
  const html = a1Page().moduleReport(a1Id), timeline = /<section class="part" id="timeline">.*?<\/section>/s.exec(html)[0];
  assert.ok(!timeline.includes('<details') && !timeline.includes('event-table') && !timeline.includes('Table form'));
  assert.ok(timeline.includes('Note matures') && timeline.includes('Call window') && countOf(timeline, /<li class="tl-i">/g) === 2);
});

test('module page (A1; Task 4): Front matter, Request, Next module and Sources are drawn nowhere on the page: no audit fold, no filename, no routing text', () => {
  const html = a1Page().moduleReport(a1Id), text = readText(html);
  for (const gone of ['title: Credit view', 'status: draft', 'filename', 'CP-1-credit.md', 'Assess the credit.', 'Pass to Liquidity.']) assert.ok(!text.includes(gone), gone);
  assert.ok(!html.includes('id="audit"') && !html.includes('class="fold"') && !html.includes('>Sources<') && !html.includes('front-matter'));
});

test('module page (A1): an earlier-format page draws its charts, maps and lanes as before, without anchors, captions, gap cards or a timeline table form', () => {
  const sections = [sec('Reader summary', 3, 10, 'consumed', []), sec('Chart data: leverage', 3, 40, 'consumed', [chartTable(42, [[43, 'FY2024', '6.57', 'x', 'K']]), text(44, 'Prose.')]), sec('Map: credit-risk transmission', 3, 400, 'consumed', [table(402, MAP_HEAD, [edgeRow(403, 'Driver', 'drives', 'Documentary Fact', 'Outcome')])]), sec('Events: Financing', 3, 300, 'consumed', [table(302, LANE_HEAD, [laneRow(303, '2025-03-31', 'day', '—', 'Note matures')])])];
  const page = a1Page(sections, { ...a1Set, charts: [a1Set.charts[0]], chartGaps: [{ title: 'Gap', table: 9, gap: 'x' }], summary: { bottomLine: 'Cash up.', confidence: 'Medium', limitation: 'x', line: 13, findings: [] } });
  const html = page.moduleReport(a1Id);
  assert.ok(!html.includes('id="s-40"') && !html.includes('<div class="map-card" id=') && !html.includes('<div class="lane-row" id='));
  assert.ok(!html.includes('Not established for this run') && !html.includes('<summary>Table form</summary><div class="table-card"><table class="event-table"'));
  assert.ok(!/<section class="part" id="timeline">.*<summary>Table form<\/summary>.*<table class="event-table">/s.test(html));
});

test('Overview (A1 fix; task 8): a new-format run\'s Overview draws no map card, chart panel or lane even where the catalogue places them; the module page keeps its map card with its s-<line> id', () => {
  const sections = a1Sections(), set = a1Set;
  const page = runPage(() => { const d = overviewData({ 'CP-1': sections }); Object.assign(d[a1Id], set); return d; }, [], m => m, { visuals: [{ module: 'CP-1', placement: 'Overview; Model' }], record: steps(['CP-1']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES });
  const html = page.runReport(RUN);
  assert.ok(!/class="map-card"|class="panel-card"/.test(html) && !/ id="s-\d+"/.test(html) && !html.includes('drawing-caption') && !html.includes('The driver is the only one stated.'), html);
  assert.ok(page.moduleReport(a1Id).includes('<div class="map-card" id="s-400">'));
});

test('module page (A1 fix; Task 4): a level-2 section named Front matter is not drawn wherever it stands (role hidden, rule 7), with its table', () => {
  const later = sec('Front matter', 2, 80, 'consumed', [text(81, 'A body paragraph.'), table(82, ['A', 'B'], [[83, 'FM-CELL-X', 'FM-CELL-Y']])]);
  const html = a1Page(a1Sections([later])).moduleReport(a1Id);
  assert.ok(!html.includes('A body paragraph.') && !html.includes('FM-CELL') && !html.includes('id="s-80"'));
});

test('Overview (A1 fix; task 8): two modules\' maps at the same table line leave no duplicate id on the Overview', () => {
  const two = { 'CP-1': a1Sections(), 'CP-2': a1Sections() };
  const page = runPage(() => { const d = overviewData(two); for (const code of ['CP-1', 'CP-2']) Object.assign(d[outId(code)], a1Set); return d; }, [], m => m, { visuals: [{ module: 'CP-1', placement: 'Overview' }, { module: 'CP-2', placement: 'Overview' }], record: steps(['CP-1', 'CP-2']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES });
  const ids = [...page.runReport(RUN).matchAll(/ id="([^"]+)"/g)].map(m => m[1]);
  assert.ok(ids.length > 0 && new Set(ids).size === ids.length && !ids.some(i => i.startsWith('map-arrow-')), ids.join(' '));
});

test('module page (decision 3; Task 4): a Source column is not drawn on the module page; the row\'s trace icon opens the row, source cells included, in the drawer', () => {
  const FILE = 'NBG_2025-03-31_annual-report.pdf', key = line => `${outId('CP-1')}:${line}`;
  const chips = { [key(23)]: [{ kind: 'upstream', module: 'CP-0', codes: ['D1'] }, { kind: 'issuer_page', source: FILE, file: FILE, page: 41, page_end: null }] };
  const html = fixturePage({ chips }).moduleReport(outId('CP-1'));
  assert.equal(countOf(html, /class="source-cell"/g), 0);
  assert.ok(!readText(html).includes(FILE) && !readText(html).includes('page 41'));
  assert.ok(html.includes(`data-evidence="${key(23)}"`) && html.includes(`data-evidence="${key(24)}"`), 'a trace icon per row, with or without chips');
});

test('timeline: the lanes scroll sideways inside their own region below the width the stacking is computed for; a number chip grows with its digits', () => {
  const html = denseHtml('2024-09-30');
  assert.match(html, /<div class="lane-scroll" role="region" tabindex="0" aria-label="[^"]*scroll[^"]*"><div class="lane-plot">/);
  const css = read('screen.css');
  // 170 px name + 12 px gap + 2 x 8 px track margin + the track width eventStack assumes (EVENT_TRACK_MIN) = 600 px.
  assert.match(css, /\.lane-scroll\{[^}]*overflow-x:auto/);
  assert.match(css, /\.lane-scroll \.lane-plot\{[^}]*min-width:600px/);
  assert.match(css, /\.lane-event\.point\{[^}]*min-width:16px/);
  assert.ok(!/\.lane-event\.point\{[^}]*[^-]width:16px/.test(css), 'the disc is not fixed at 16 px');
});

test('timeline: a three-digit number is stacked against its wider chip', () => {
  const many = d => {
    d[outId('CP-0')] = runOutput('CP-0', { sections: [sec('Events: Sources', 3, 400, 'consumed', [table(402, LANE_HEAD, Array.from({ length: 101 }, (_, i) => laneRow(403 + i, `2024-${String(1 + Math.floor(i / 28)).padStart(2, '0')}-${String(1 + (i % 28)).padStart(2, '0')}`, 'day', '—', `Item ${i + 1}`)))])], events: [{ lane: 'Sources', table: 402, gap: null }] });
    return d;
  };
  const html = runPage(many, [], m => m).eventLanesView(RUN, { only: outId('CP-0'), compact: true });
  assert.equal(countOf(html, /<span class="lane-no">/g), 101);
  const dots = [...html.matchAll(/class="lane-event point"[^>]*style="left:([\d.]+)%;bottom:(\d+)px"><span class="lane-no">(\d+)<\/span>/g)].map(m => ({ left: Number(m[1]), bottom: m[2], chip: Math.max(16, Math.ceil(m[3].length * 7) + 4) }));
  assert.equal(dots.length, 101);
  for (let i = 0; i < dots.length; i++) for (let j = i + 1; j < dots.length; j++) {
    if (dots[i].bottom === dots[j].bottom) assert.ok(Math.abs(dots[i].left - dots[j].left) * 4.02 >= (dots[i].chip + dots[j].chip) / 2, `markers ${i + 1} and ${j + 1} overlap at 402 px`);
  }
});

test('timeline: a span too thin to hold its number at the right end is drawn from its right edge and marked anchored', () => {
  const thin = d => {
    d[outId('CP-0')] = runOutput('CP-0', { sections: [sec('Events: Sources', 3, 400, 'consumed', [table(402, LANE_HEAD, [laneRow(403, '1993', 'year', '—', 'Founded'), laneRow(404, '2024-Q4', 'quarter', '—', 'Last quarter')])])], events: [{ lane: 'Sources', table: 402, gap: null }] });
    return d;
  };
  const html = runPage(thin, [], m => m).eventLanesView(RUN, { only: outId('CP-0'), compact: true });
  const tag = [...html.matchAll(/<a class="lane-event[^>]*>/g)].map(m => m[0]).find(m => m.includes('Last quarter'));
  assert.match(tag, /class="lane-event span anchored"/);
  assert.match(tag, /style="right:0%;width:0\.\d+%;bottom:4px"/);
});

// ---- Whole-branch H1, re-pointed by Task 7: a drawing whose table states none is the empty state (C32) with the module's stated reason; its table as written is Evidence's, not a fold on the page.
const h1Page = (extra, set) => a1Page(a1Sections(extra), { ...a1Set, ...set });
// Every cell of the table at `line` is in the Evidence page (Registers, Tables as written): what the page no longer folds is not lost.
// The a1 sections with `extra` placed under Findings (before the level-2 Sources), where Evidence classifies a drawing as written.
const a1Findings = extra => { const all = a1Sections(); all.splice(all.findIndex(x => x.heading === 'Sources'), 0, ...extra); return all; };
const inEvidence = (sections, line) => {
  const block = sections.flatMap(x => x.blocks).find(b => b.type === 'table' && b.line === line), page = strip(evidenceRegisters(sections));
  // (Evidence's tableView holds a row's cells under the table's headers; a cell beyond them is not in it, a Task 3 matter noted in the Task 7 fix report.)
  for (const cell of [...block.headers, ...block.rows.flatMap(r => r.cells.slice(0, block.headers.length))]) if (String(cell).trim() !== '') assert.ok(page.includes(String(cell).trim()), `Evidence holds the cell: ${cell}`);
};

test('module page (H1; Task 7): a chart card with no numbers is the empty state with every distinct reason, and no Table form fold', () => {
  const page = h1Page([sec('Chart data: covenant headroom', 3, 35, 'consumed', [chartTable(37, [[38, 'FY2024', 'Not supplied: no covenant is stated', 'x (net debt to EBITDA)', 'not established for this run and not a compliance opinion']])])], { chartGaps: [{ title: 'Covenant headroom', table: 37, gap: 'no covenant is stated; no test date is stated' }] });
  const html = page.moduleReport(a1Id), card = new RegExp('<div class="panel-card" id="s-35">.*?(?=<div class="panel-card" id="s-40">)', 's').exec(html)[0];
  assert.ok(card.includes('class="empty-state"') && countOf(strip(card), /Not supplied: no covenant is stated/g) === 1 && !card.includes('<details') && !card.includes('Table form'));
  assert.ok(!strip(card).includes('x (net debt to EBITDA)') && !strip(card).includes('not a compliance opinion'), 'the unit and Basis cells are the table as written, in Evidence');
  inEvidence(a1Findings([sec('Chart data: covenant headroom', 3, 35, 'consumed', [chartTable(37, [[38, 'FY2024', 'Not supplied: no covenant is stated', 'x (net debt to EBITDA)', 'not established for this run and not a compliance opinion']])])]), 37);
});

test('module page (H1; Task 7): an events lane with no event is the empty state with the module\'s reasons, not a timeline and not a fold', () => {
  const row = [313, 'Not supplied: no legal event is settled here', 'Not supplied: none', 'Not supplied: none', 'Not supplied: none', 'Not supplied: none', 'Not supplied: none', 'Not supplied: these are undated triggers recorded in other lanes'];
  const page = h1Page([sec('Events: Legal', 3, 310, 'consumed', [table(312, LANE_HEAD, [row]), text(314, 'Legal lane caption.')])], { events: [{ lane: 'Legal', table: 312, gap: 'no legal event is settled here' }] });
  const html = page.moduleReport(a1Id), lane = /<div class="tl-card" id="s-310">.*?Legal lane caption\./s.exec(html)[0];
  assert.ok(lane.includes('class="empty-state"') && !lane.includes('tl-i') && strip(lane).includes('Not supplied: no legal event is settled here') && strip(lane).includes('Legal lane caption.'));
  assert.ok(strip(lane).includes('Not supplied: these are undated triggers recorded in other lanes') && !lane.includes('<details'), 'the module\'s last-cell reason too');
  inEvidence(a1Findings([sec('Events: Legal', 3, 310, 'consumed', [table(312, LANE_HEAD, [row]), text(314, 'Legal lane caption.')])]), 312);
});

test('module page (H1; Task 7): a map with no edge is the empty state with its reason and one link to the edge table in Evidence; an earlier-format page is unchanged', () => {
  const early = /<section class="part" id="maps">.*?<\/section>/s.exec(runPage(withMaps).moduleReport(outId('CP-1')))[0];
  assert.ok(early.includes('Not established for this run') && !early.includes('<summary>Table form</summary>') && early.includes('<table class="map-table"'), 'earlier format is unchanged');
  const page = h1Page([sec('Map: legal entities', 3, 410, 'consumed', [table(412, MAP_HEAD, [[413, 'Not supplied: no edge is stated', 'Not supplied: x', 'Not supplied: x', 'Not supplied: x', 'Not supplied: no edge with applicable document and jurisdiction can be drawn', 'Not supplied: p']]), text(414, 'Map caption.')])], { maps: [...a1Set.maps, { name: 'legal entities', table: 412, gap: 'no edge is stated' }] });
  const card = /<div class="map-card" id="s-410">.*?Map caption\./s.exec(page.moduleReport(a1Id))[0];
  assert.ok(card.includes('class="empty-state"') && !card.includes('<svg role="group"') && !card.includes('<table') && !card.includes('Table form'));
  assert.ok(strip(card).includes('Not supplied: no edge with applicable document and jurisdiction can be drawn') && card.includes('href="#W-Evidence/registers?c=run-a&amp;m=CP-1"') && countOf(card, /class="in-ev"/g) === 1, card);
  inEvidence(a1Findings([sec('Map: legal entities', 3, 410, 'consumed', [table(412, MAP_HEAD, [[413, 'Not supplied: no edge is stated', 'Not supplied: x', 'Not supplied: x', 'Not supplied: x', 'Not supplied: no edge with applicable document and jurisdiction can be drawn', 'Not supplied: p']]), text(414, 'Map caption.')])]), 412);
});

// ---- Task 7: events, maps and promoted registers on the module page; the audit material of a drawing is Evidence's.
const EvidencePage = require('./evidence.js');
// The Evidence page (Registers tab) of the one output, through the pure builder: the output's sections as the page holds them.
const evidenceRegisters = (sections, module = 'CP-1') => EvidencePage.view({
  run: { context: RUN, code: 'RUN-A', evidence: { sources: [], unused: [], unrecorded: [], noSourcesModules: [], handoffs: [], zip: null, downloads: [], record: { hashes: [], instructions: [], calls: [], cap: null } }, methodChanges: [], steps: [] },
  modules: [{ id: module, outputs: [{ id: a1Id, sections, placement: sections.map(() => 'view') }] }], chips: {},
  deps: { moduleTitle: code => code, hashLabel: name => name, methodChange: line => line },
}, { tab: 'registers', module });
const MATRIX_HEAD = ['Event', 'Description', 'Probability', 'Impact', 'P/I Classification'];
const registerSections = () => a1Sections([
  sec('Analytical appendix', 2, 80, 'view', []),
  sec('T5.4 Probability / Impact Matrix', 3, 82, 'view', [table(84, MATRIX_HEAD, [[85, 'Strike', 'A strike at the plant', 'High', 'High', 'Critical'], [86, 'Flood', 'A flooded warehouse', 'Low', 'High', 'Medium']])]),
  sec('T2F.1 Source register', 3, 90, 'view', [table(92, ['Name', 'Detail'], [[93, 'Alpha', 'Only in Evidence']])]),
]);

test('promoted registers (Task 7): a registers table whose shape is promoted is drawn once on the module page, under its section heading, after the finding sections; the as-written table is in Evidence too', () => {
  const sections = registerSections();
  sections.splice(sections.findIndex(x => x.heading === 'Sources'), 0, sec('Late finding', 3, 500, 'view', [text(501, 'A late finding.')]));
  const page = a1Page(sections), html = page.moduleReport(a1Id);
  assert.deepEqual(page.reportParts(a1Id).map(p => p[0]), ['head', 'bottom-line', 'key-findings', 'charts', 'timeline', 'maps', 's-500', 's-82', 'limitations']);
  assert.equal(page.reportParts(a1Id).find(p => p[0] === 's-82')[1], 'Probability / Impact Matrix', 'the section\'s own heading, its method code dropped');
  assert.equal(countOf(html, /A strike at the plant/g), 1, 'drawn once');
  assert.ok(html.includes('class="shape-block shape-matrix"') && html.includes('<div class="analysis-section" id="s-82">'));
  assert.ok(html.indexOf('A late finding.') < html.indexOf('A strike at the plant'), 'after the finding sections');
  assert.ok(page.drawnAnchors(a1Id).has('s-82') && !page.drawnAnchors(a1Id).has('s-90'));
  const evidence = strip(evidenceRegisters(sections));
  assert.equal(countOf(evidence, /A strike at the plant/g), 1, 'Evidence holds the table as written, once');
  assert.ok(evidence.includes('Only in Evidence') && evidence.includes('A flooded warehouse'));
});
test('promoted registers (Task 7): a registers table of a shape that is not promoted is Evidence only, and so is the prose of a registers section', () => {
  const sections = a1Sections([sec('Analytical appendix', 2, 80, 'view', [text(81, 'Appendix prose, kept in Evidence.')]), sec('T2F.1 Source register', 3, 90, 'view', [table(92, ['Name', 'Detail'], [[93, 'Alpha', 'Only in Evidence']]), text(94, 'Register prose.')])]);
  const html = a1Page(sections).moduleReport(a1Id);
  for (const gone of ['Only in Evidence', 'Appendix prose', 'Register prose', 'Source register']) assert.ok(!html.includes(gone), gone);
  assert.ok(strip(evidenceRegisters(sections)).includes('Only in Evidence'));
});
test('promoted registers (Task 7): an earlier-format handoff draws none, and an inter-module section stays hidden everywhere', () => {
  const sections = [sec('Reader summary', 3, 10, 'consumed', []), ...registerSections().filter(x => x.line >= 80), sec('Downstream owners', 2, 95, 'view', [table(97, MATRIX_HEAD, [[98, 'Hidden event', 'x', 'High', 'High', 'Critical']])])];
  const early = a1Page(sections, { ...a1Set, charts: [], events: [], maps: [], summary: { bottomLine: 'Cash up.', confidence: 'Medium', limitation: 'x', line: 13, findings: [] } }).moduleReport(a1Id);
  assert.ok(!early.includes('shape-matrix') && !early.includes('rm-chip'), 'the earlier-format path draws no component');
  const current = a1Page(a1Sections(sections.filter(x => x.line >= 80))).moduleReport(a1Id);
  assert.ok(!current.includes('Hidden event') && !strip(evidenceRegisters(a1Sections(sections.filter(x => x.line >= 80)))).includes('Hidden event'), 'rule 7: drawn nowhere');
});

test('maps (Task 7): the edge table leaves a new-format page: its Evidence column is nowhere on it, one link opens Evidence, and Evidence holds the table as written', () => {
  const sections = a1Sections(), html = a1Page(sections).moduleReport(a1Id), card = /<div class="map-card" id="s-400">.*?The driver is the only one stated\./s.exec(html)[0];
  assert.ok(!html.includes('Synthetic p.1') && !card.includes('<table') && !card.includes('map-table') && !card.includes('Edges of the map'));
  assert.ok(card.includes('<svg role="group"') && card.includes('class="map-steps"') && countOf(card, /class="in-ev"/g) === 1);
  assert.ok(strip(evidenceRegisters(sections)).includes('Synthetic p.1'), 'the table as written, with its Evidence column, is in Evidence');
});
test('charts (Task 7): a chart\'s source chips and Table form are not on the module page and are in Evidence; the chart keeps one trace control', () => {
  const chips = { [`${a1Id}:43`]: [{ kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 123, page_end: null }] };
  const sections = a1Sections(), page = runPage(() => { const d = overviewData({ 'CP-1': sections }); Object.assign(d[outId('CP-1')], a1Set); return d; }, [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES, chips });
  const html = page.moduleReport(a1Id), charts = /<section class="part" id="charts">.*?<\/section>/s.exec(html)[0];
  assert.ok(!html.includes('K.jsonl') && !html.includes('.jsonl') && !/class="chips"|data-chip=|Table form|class="chart-table"/.test(charts));
  assert.equal(countOf(charts, /class="basis-link trace-row"/g), 2);
  assert.ok(strip(evidenceRegisters(sections)).includes('6.57'), 'the chart\'s table as written is in Evidence');
});
test('timeline (Task 7): an events table with one "Not supplied" row is the empty state with the reason, not a timeline, and a table with events is the timeline', () => {
  const row = [313, ...Array(6).fill('Not supplied: not assessable, no executed governing document available'), 'Not supplied: no legal event is settled here'];
  const gap = h1Page([sec('Events: Legal', 3, 310, 'consumed', [table(312, LANE_HEAD, [row])])], { events: [{ lane: 'Legal', table: 312, gap: 'not assessable' }] }).moduleReport(a1Id);
  const lane = /<div class="tl-card" id="s-310">.*?<\/div><\/div>/s.exec(gap)[0];
  assert.ok(lane.includes('class="empty-state"') && !lane.includes('class="tl ') && strip(lane).includes('Not supplied: not assessable, no executed governing document available'));
  const real = /<div class="tl-card" id="s-300">.*?<\/ol>/s.exec(a1Page().moduleReport(a1Id))[0];
  assert.ok(real.includes('class="tl tl-h"') && !real.includes('empty-state') && !real.includes('K_10') && !real.includes('Synthetic filing'), 'the Source cell stays in the trace control');
});

// ---- The Forecast page (reader check of 2026-11-12): lines with no figure fold away; the model picker names the run, not a hash.
const cell = (status, display, reason = null) => ({ exact: status === 'value' ? display : null, display, reason, status });
const gridColumns = [{ label: 'FY2024', group: 'Fiscal year', start: null, end: null, ytd: false }, { label: 'FY2025E', group: 'Base case', start: null, end: null, ytd: false }];
const gridRow = (band, label, empty, cells) => ({ band, label, kind: 'money', total: false, empty, cells });
// Hand-written grid: Revenue has figures; Capex has none in the main table but one in the Upside table; Closing cash and Gross profit have none anywhere.
const FOLD_GRID = {
  units: 'USD millions', columns: gridColumns, notes: [], limits: [],
  rows: [
    gridRow('Revenue', 'Revenue', false, [cell('value', '1,000'), cell('value', '1,050')]),
    gridRow('Profitability', 'Gross profit', true, [cell('na', 'n.a.', 'not reported'), cell('nm', 'n.m.')]),
    gridRow('Cash and liquidity', 'Capex', false, [cell('na', 'n.a.', 'not reported'), cell('na', 'n.a.', 'not reported')]),
    gridRow('Cash and liquidity', 'Closing cash', true, [cell('na', 'n.a.', 'not reported'), cell('na', 'n.a.', 'not reported')]),
  ],
  other: {
    columns: [{ label: 'FY2025E', group: 'Upside', start: null, end: null, ytd: false }],
    rows: [
      gridRow('Revenue', 'Revenue', false, [cell('value', '1,100')]),
      gridRow('Profitability', 'Gross profit', true, [cell('nm', 'n.m.')]),
      gridRow('Cash and liquidity', 'Capex', false, [cell('value', '40')]),
      gridRow('Cash and liquidity', 'Closing cash', true, [cell('na', 'n.a.', 'not reported')]),
    ],
  },
};
const foldPart = (html, cls) => html.match(new RegExp(`<details class="${cls}">.*?</details>`, 's'))?.[0] ?? null;
const rowLabels = html => [...html.matchAll(/<th scope="row">([^<]*)<\/th>/g)].map(m => m[1]);

test('Forecast: a line with no figure in any column is folded after the main table and before the other cases; its cells stay', () => {
  const html = runPage().cashflowSection({ cashflow: FOLD_GRID });
  const main = html.slice(0, html.indexOf('<details class="cashflow-empty">'));
  const fold = foldPart(html, 'cashflow-empty');
  assert.deepEqual(rowLabels(main), ['Revenue', 'Capex'], 'Capex has a figure only in the Upside table, so it stays in the main table');
  assert.deepEqual(rowLabels(fold), ['Gross profit', 'Closing cash']);
  assert.ok(fold.includes('<summary>Lines with no figure in this run (2)</summary>'));
  assert.ok(!main.includes('Profitability'), 'a heading whose lines are all folded is folded with them');
  assert.ok(fold.includes('<th scope="colgroup" colspan="3">Profitability</th>') && fold.includes('Cash and liquidity'));
  assert.ok(fold.includes('Fiscal year') && fold.includes('Base case') && fold.includes('aria-label="n.a.: not reported"') && fold.includes('aria-label="n.m.: not modelled in the calculation record"'), 'same columns and cells, reasons reachable');
  assert.ok(html.indexOf('class="cashflow-empty"') < html.indexOf('class="cashflow-other"') && html.indexOf('</table>') < html.indexOf('class="cashflow-empty"'));
  assert.ok(html.includes('Why cells show n.a. (3 lines)'), 'the n.a. list still counts every line');
});

test('Forecast: when every line has a figure there is no fold', () => {
  const rows = FOLD_GRID.rows.map(r => ({ ...r, empty: false }));
  assert.ok(!runPage().cashflowSection({ cashflow: { ...FOLD_GRID, rows, other: null } }).includes('cashflow-empty'));
});

test('Forecast: the fold has the other cases\' keyboard and focus styling', () => {
  const css = read('screen.css');
  assert.ok(css.includes('.cashflow-other summary,.cashflow-empty summary{cursor:pointer;font-weight:600;'));
  assert.ok(read('views.js').includes('<details class="cashflow-empty"><summary>'));
});

const PICK_RUNS = { asOf: '2025-03-31', issuerKey: 'k1', pathway: 'credit_snapshot', run: 'Run A' };
const pickPage = models => runPage(d => d, [], m => m, { runFields: PICK_RUNS, models });
const pickModel = (id, extra = {}) => ({ id, issuerKey: 'k1', runId: RUN, runFolder: RUN, sources: [], ...extra });
const HASH_1 = 'a1b2c3d4'.repeat(8), HASH_2 = 'e5f6a7b8'.repeat(8);

test('model picker: one delivery reads the run name (date and pathway), with no hash', () => {
  const models = [pickModel(HASH_1)];
  assert.deepEqual(pickPage(models).modelOptionLabels(models), ['31 March 2025 · Full credit assessment']);
});

test('model picker: two deliveries of one run differ by the first eight characters of the delivery id', () => {
  const models = [pickModel(HASH_1), pickModel(HASH_2)];
  assert.deepEqual(pickPage(models).modelOptionLabels(models), ['31 March 2025 · Full credit assessment · a1b2c3d4', '31 March 2025 · Full credit assessment · e5f6a7b8']);
});

test('model picker: the relationship is appended only when recorded', () => {
  const models = [pickModel(HASH_1, { previous: HASH_2 }), pickModel(HASH_2)];
  const [first, second] = pickPage(models).modelOptionLabels(models);
  assert.equal(first, `31 March 2025 · Full credit assessment · a1b2c3d4 · supersedes 31 March 2025 · Full credit assessment · e5f6a7b8`);
  assert.equal(second, `31 March 2025 · Full credit assessment · e5f6a7b8 · superseded by 31 March 2025 · Full credit assessment · a1b2c3d4`);
  assert.ok(!pickPage([pickModel(HASH_1)]).modelOptionLabels([pickModel(HASH_1)])[0].includes('relationship'));
});

test('model picker: with no run context the run folder is named, then the delivery id', () => {
  const orphan = pickModel(HASH_1, { issuerKey: 'other', runFolder: 'folder-x', runId: 'folder-x' });
  assert.deepEqual(pickPage([orphan]).modelOptionLabels([orphan]), ['folder-x']);
  const bare = pickModel(HASH_2, { issuerKey: 'other', runFolder: null, runId: null });
  assert.deepEqual(pickPage([bare]).modelOptionLabels([bare]), [HASH_2]);
});

test('model picker: a relationship names a listed delivery by its label and an unlisted one by its id', () => {
  const models = [pickModel(HASH_1, { previous: HASH_2 })];
  assert.equal(pickPage(models).modelOptionLabels(models)[0], `31 March 2025 · Full credit assessment · supersedes ${HASH_2}`);
});

test('model picker: ids that share their first eight characters read with the whole id', () => {
  const models = [pickModel('tdg-forecast-005'), pickModel('tdg-forecast-006')];
  assert.deepEqual(pickPage(models).modelOptionLabels(models), ['31 March 2025 · Full credit assessment · tdg-forecast-005', '31 March 2025 · Full credit assessment · tdg-forecast-006']);
});

test('model picker: a delivery for a run the library does not list is named by its own run folder, not the page run', () => {
  const models = [pickModel(HASH_1, { runId: 'run-not-listed', runFolder: 'run-not-listed', sources: [{ run: RUN }] })];
  assert.deepEqual(pickPage(models).modelOptionLabels(models), ['run-not-listed']);
});

test('brand colours: screen.css declares each brand token with the plan value (Rulings 1 and 5)', () => {
  const css = read('screen.css');
  const expected = {
    '--navy': '#000533', '--blue': '#001aff', '--ground': '#f4f4f5', '--rule': '#e8e9eb', '--muted': '#474a4f',
    '--quiet': '#fafafb', '--selection': '#e5e8ff', '--blue-50': '#e5e8ff', '--blue-100': '#c2c9ff', '--blue-700': '#0012b2',
    '--amber': '#806300', '--amber-bg': '#fff4cc', '--amber-border': '#f2dc8c', '--red': '#8e413e', '--green': '#0f8048',
    '--text-primary': '#000533', '--text-secondary': '#383b3f', '--text-tertiary': '#474a4f', '--text-quaternary': '#63676e',
    '--gray-25': '#fcfcfd', '--gray-50': '#fafafb', '--gray-100': '#f4f4f5', '--gray-200': '#e8e9eb', '--gray-300': '#d1d4d8',
    '--ring': '0 0 0 4px rgba(0,26,255,.16)', '--dot-quiet': '#8d939d',
    '--series-1': '#001aff', '--series-2': '#1eff8f', '--series-3': '#eaff00', '--series-4': '#a29aff',
    '--series-1-ln': '#001aff', '--series-2-ln': '#0f8048', '--series-3-ln': '#758000', '--series-4-ln': '#514d80',
  };
  const declared = {};
  for (const block of css.matchAll(/:root\{([^}]*)\}/g)) for (const m of block[1].matchAll(/(--[\w-]+):([^;]+)/g)) declared[m[1]] = m[2].trim();
  for (const [token, value] of Object.entries(expected)) assert.equal(declared[token], value, token);
});

test('brand colours: no rule sets text or a thin line in a bright series fill', () => {
  const css = read('screen.css');
  const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)];
  for (const [, selector, body] of rules) {
    for (const m of body.matchAll(/(?:^|;)\s*(color|stroke)\s*:\s*var\(--series-([234])\)/g)) {
      assert.fail(`${selector.trim()} sets ${m[1]} to the bright fill --series-${m[2]}; use --series-${m[2]}-ln`);
    }
  }
});

test('brand colours: the replaced colour values no longer appear in screen.css', () => {
  const css = read('screen.css');
  for (const old of ['#0017e5', '#0e7a46', '#8a5300', '#b3261e', '#4a5068', '#3a4056', '#0b1030']) assert.ok(!css.includes(old), `${old} is still in screen.css`);
});

function cssRules(css) {
  return [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map((m) => ({ selector: m[1].trim(), body: m[2] }));
}

test('brand colours: a hatched stack segment on a bright fill draws its stripe in that series line value, not white', () => {
  const rules = cssRules(read('screen.css'));
  // B8 (ruling 2026-11-13): rank 2 was --series-2, the status green, so the stack's series are blue, violet, yellow and navy; the stripe of each is its own line value (navy: --blue-100, light on dark, not white).
  for (const [n, stripe] of [[1, '--series-4-ln'], [2, '--series-3-ln'], [3, '--blue-100']]) {
    for (const prefix of ['.stack-seg', '.stack-key', '.stack-legend']) {
      const sel = prefix === '.stack-seg' ? `.stack-seg.series-${n}.hatch` : `${prefix} .series-${n}.hatch`;
      const found = rules.filter((r) => r.selector.split(',').map((s) => s.trim()).includes(sel));
      assert.ok(found.length, `no hatch rule for ${sel}`);
      // The same selector text has the same specificity, so the last rule that sets the stripe is the one that draws it.
      const winner = found.filter((r) => /(?:^|;)\s*background(?:-image)?\s*:/.test(r.body)).at(-1);
      assert.ok(winner, `${sel} sets no stripe`);
      assert.ok(winner.body.includes(`var(${stripe})`), `${sel} stripe is not ${stripe}`);
      assert.ok(!/rgba?\(\s*255\s*,\s*255\s*,\s*255|#fff/i.test(winner.body), `${sel} draws a white stripe`);
    }
  }
});

test('brand colours: no legend or key swatch is filled with a bright series token, and the ledger states keep their tokens', () => {
  const rules = cssRules(read('screen.css'));
  for (const r of rules) {
    if (!/\.(chart-legend|signal-key)\b/.test(r.selector) || !/\.series-\d/.test(r.selector)) continue;
    assert.ok(!/(?:^|;)\s*background(?:-color)?\s*:\s*var\(--series-[234]\)/.test(r.body), `${r.selector} fills a swatch with a bright series token`);
    assert.ok(!/(?:^|;)\s*background(?:-color)?\s*:[^;]*#(?:1eff8f|eaff00|a29aff)\b/i.test(r.body), `${r.selector} fills a swatch with a bright literal`);
  }
  const ledger = { 'ledger-closed': 'var(--green)', 'ledger-remaining': 'var(--navy)', 'ledger-new': 'var(--blue)', 'ledger-no-longer-stated': 'var(--amber)' };
  for (const [cls, value] of Object.entries(ledger)) {
    const rule = rules.find((r) => r.selector.split(',').map((s) => s.trim()).includes(`.${cls}`));
    assert.ok(rule, `no rule for .${cls}`);
    assert.match(rule.body, new RegExp(`(?:^|;)\\s*background\\s*:\\s*${value.replace(/[()]/g, '\\$&')}\\s*(?:;|$)`), `.${cls}`);
  }
});

test('brand colours: the upside path, its points and its key use --series-4-ln; axis and gridline use the brand axis and grid', () => {
  const rules = cssRules(read('screen.css'));
  const last = (sel, prop) => {
    let v = null;
    for (const r of rules) if (r.selector.split(',').map((s) => s.trim()).includes(sel)) for (const m of r.body.matchAll(new RegExp(`(?:^|;)\\s*${prop}\\s*:\\s*([^;]+)`, 'g'))) v = m[1].trim();
    return v;
  };
  assert.equal(last('.path-2', 'stroke'), 'var(--series-4-ln)');
  assert.equal(last('.point-2', 'fill'), 'var(--series-4-ln)');
  assert.equal(last('.path-key-2', 'background'), 'var(--series-4-ln)');
  assert.equal(last('.axis', 'stroke'), 'var(--navy)');
  assert.equal(last('.gridline', 'stroke'), 'var(--gray-200)');
});

test('component look: buttons, text inputs, state badges and the current tab take the component reference box values', () => {
  const css = read('screen.css');
  const rules = cssRules(css);
  const body = (sel) => {
    const r = rules.find((x) => x.selector.split(',').map((s) => s.trim()).join(',') === sel);
    assert.ok(r, `no rule for ${sel}`);
    return r.body;
  };
  assert.match(css, /--radius-control:8px/);
  // Primary and secondary buttons: 8px radius (the control token), weight 600, 40px high.
  const buttons = body('.primary-action,.secondary-action,.tertiary-action');
  assert.match(buttons, /border-radius:var\(--radius-control\)/);
  assert.match(buttons, /font:600 /);
  assert.match(buttons, /height:40px/);
  // Text inputs: 40px high, 8px radius.
  for (const sel of ['.library-search input,.library-filters select,.library-filters input', '.run-field input,.run-field select']) {
    const b = body(sel);
    assert.match(b, /height:40px/, sel);
    assert.match(b, /border-radius:var\(--radius-control\)/, sel);
  }
  // State badges and grades: 6px radius.
  for (const sel of ['.badge', '.grade']) assert.match(body(sel), /border-radius:6px/, sel);
  // The current tab (C1, redesign): a navy pill with white text; once measured the pill is one element that slides (`.has-pill::before`).
  // The last rule of the selector that sets the property is the one that draws it (a later rule in the motion block sets only transitions).
  const tabRule = (sel, prop) => rules.filter((x) => x.selector.split(',').map((t) => t.trim()).includes(sel) && new RegExp(`(?:^|;)${prop}:`).test(x.body)).at(-1);
  assert.match(tabRule('.workspace-tabs>a', 'border-radius').body, /border-radius:999px/);
  assert.match(tabRule('.workspace-tabs>a', 'border').body, /border:0/);
  assert.match(tabRule('.workspace-tabs>a[aria-current]', 'background').body, /background:var\(--navy\);color:#fff/);
  assert.match(tabRule('.workspace-tabs.has-pill::before', 'background').body, /background:var\(--navy\)/);
  assert.match(tabRule('.workspace-tabs.has-pill::before', 'transform').body, /transform:translate\(var\(--pill-x\),var\(--pill-y\)\)/);
  for (const r of rules) {
    if (!r.selector.split(',').some((t) => t.trim().startsWith('.workspace-tabs>a'))) continue;
    for (const m of r.body.matchAll(/border-bottom-width\s*:\s*([^;]+)/g)) assert.equal(m[1].trim(), '2px', r.selector);
  }
});

// ---- The page shell (library redesign, task 2): header chips, no run code outside Evidence, pill tabs, the trace drawer's footer.
const RUN_CODE = 'TDG-PROOF-SNAPSHOT-OPUS-002';
// A DOM stand-in just big enough for updateWorkspaceChrome: the header, the tabs, the context bar and the elements it toggles, each keeping what is written to it.
function chromeDom() {
  const vars = {};
  const node = () => ({ hidden: false, innerHTML: '', textContent: '', vars, style: { setProperty: (k, v) => { vars[k] = v; } }, classList: { toggle() {}, add() {}, remove() {}, contains: () => false }, setAttribute() {}, removeAttribute() {},
    querySelector: () => ({ offsetLeft: 10, offsetWidth: 80, offsetHeight: 36, offsetTop: 10 }) });
  const byId = {}, bySelector = { '.issuer': node(), '.workspace-tabs': node() };
  const $ = id => (byId[id] ||= node());
  const document = { querySelector: sel => bySelector[sel] || (sel.startsWith('.rail') ? node() : null), querySelectorAll: () => [] };
  return { $, document, header: bySelector['.issuer'], tabs: bySelector['.workspace-tabs'], bar: $('context-bar') };
}
function shellPage(runFields = {}) {
  const dom = chromeDom();
  const page = runPage(d => d, [], m => m, { ...HIST, runFields: { ...HIST.runFields, run: RUN_CODE, period: 'FY2025', first: 'CP-0', ...runFields }, dom });
  return { page, dom };
}

test('the issuer header: the name, then chips for the period and the pathway in words; no run code anywhere in the header, tabs or context bar', () => {
  const { page, dom } = shellPage();
  page.current.module = 'W-Overview';
  page.updateWorkspaceChrome('W-Overview');
  const header = dom.header.innerHTML;
  assert.ok(header.includes(`<h1 title="Synthetic Issuer">Synthetic Issuer</h1>`));
  assert.ok(header.includes('<p class="hchips"><span class="hchip">FY2025</span><span class="hchip">Full credit assessment</span></p>'), header);
  assert.ok(!header.includes('Methods changed'), 'no method change, no amber chip');
  for (const [name, markup] of [['header', header], ['tabs', dom.tabs.innerHTML], ['context bar', dom.bar.innerHTML]]) assert.ok(!markup.includes(RUN_CODE), `${name} carries the run code`);
  assert.deepEqual([...dom.tabs.innerHTML.matchAll(/>([^<]+)<\/a>/g)].map(m => m[1]), ['Report', 'Overview', 'Changes', 'Modules', 'Forecast', 'Evidence']);
  assert.deepEqual(dom.tabs.vars, { '--pill-x': '10px', '--pill-w': '80px', '--pill-h': '36px', '--pill-y': '10px' }, 'the pill is placed under the active tab when the tabs are drawn');
});

test('the issuer header: the amber "Methods changed since this run" chip appears only for a non-empty methodChanges and links to the Evidence run record', () => {
  const none = shellPage({ methodChanges: [] });
  none.page.updateWorkspaceChrome('W-Overview');
  assert.ok(!none.dom.header.innerHTML.includes('Methods changed'), 'an empty list draws no chip');
  const changed = shellPage({ methodChanges: ['CP-0: methods/cp0.md changed'] });
  changed.page.updateWorkspaceChrome('W-Overview');
  assert.ok(changed.dom.header.innerHTML.includes('<a class="hchip amber" href="#W-Evidence/record?c=run-a">Methods changed since this run</a>'), changed.dom.header.innerHTML);
});

test('the run code shows only on the Evidence page: the context bar and the section bar', () => {
  const { page, dom } = shellPage();
  for (const module of ['W-Overview', 'W-Changes', 'W-Forecast', 'CP-1']) assert.ok(!page.runLabel(module, RUN).includes(RUN_CODE), `${module} context bar`);
  assert.ok(page.runLabel('W-Evidence', RUN).includes(RUN_CODE), 'the Evidence page names the run by its code');
  assert.ok(!page.moduleHead({ module: 'CP-1', context: RUN, output: null }).includes(RUN_CODE));
  const prefix = read('screen.js').slice(read('screen.js').indexOf('function contextPrefix('), read('screen.js').indexOf('const keepsCodes'));
  assert.ok(prefix.includes("module==='W-Evidence'?`${esc(ctx.run)} · `:''"), 'the section bar names the run only on Evidence');
});

test('the drawer footer links to the Evidence trace of the traced module and the run, encoded like the route\'s own query', () => {
  const { page } = shellPage();
  assert.equal(page.traceHref('CP-2D', RUN), '#W-Evidence/trace?c=run-a&m=CP-2D');
  assert.equal(page.traceHref('CP 2/D?', 'run-b'), '#W-Evidence/trace?c=run-b&m=CP+2%2FD%3F');
  const foot = page.drawerFoot('CP-2D', RUN);
  assert.ok(foot.startsWith('<div class="drawer-foot"><a class="text-action" href="#W-Evidence/trace?c=run-a&amp;m=CP-2D">Open in Evidence'), foot);
});

test('the drawer is the inspector, restyled: close button, Escape and focus return keep their code path, the backdrop closes it', () => {
  const screen = read('screen.js'), html = read('index.html');
  assert.ok(html.includes('<aside class="inspector" id="inspector" role="dialog" aria-modal="true" aria-label="Evidence inspector" hidden></aside><div class="drawer-backdrop" id="drawer-backdrop"'), 'the drawer is a named modal dialog (review L6)');
  assert.ok(screen.includes("event.target.closest('#back-analysis,#drawer-backdrop')"), 'the close button and the backdrop leave the trace');
  assert.ok(screen.includes("if(current.evidence){event.preventDefault();go(current.module,here());return;}"), 'Escape closes the open trace, on the route it was opened on');
  assert.ok(screen.includes("returnTrigger.focus({preventScroll:true})"), 'focus returns to the control that opened it');
  const css = read('screen.css');
  assert.match(css, /\.inspector\{position:fixed;[^}]*width:420px;max-width:100%/);
  assert.match(css, /@media\(max-width:1599\.98px\)\{\.inspector:not\(\[hidden\]\)\+\.drawer-backdrop\{opacity:1;visibility:visible\}\}/);
  assert.match(css, /@media\(max-width:767\.98px\)\{\.inspector\{width:100%\}\}/);
});

test('motion: the pill, the drawer, the backdrop and the toast move only under prefers-reduced-motion: no-preference, and nothing moves in print', () => {
  const css = read('screen.css');
  const shell = css.slice(css.indexOf('/* ---- Library redesign, shell'));
  const outside = shell.replace(/@media\(prefers-reduced-motion:no-preference\)\{[\s\S]*?\n\}\n/g, ''); // every no-preference block, the Evidence page's as well as the shell's
  for (const word of ['transition:transform', 'transition:opacity', 'animation:toast-in']) {
    assert.ok(shell.includes(word), word);
    assert.ok(!outside.includes(word), `${word} sits outside the motion query`);
  }
  assert.ok(shell.includes('@media print{.toast-host,.drawer-backdrop,.basis-link{display:none!important}*{transition:none!important;animation:none!important}}'));
});

test('the tooltip: [data-tip] shows its text after 400ms on hover and focus, with CSS only', () => {
  const css = read('screen.css');
  assert.ok(css.includes('[data-tip]::after{content:attr(data-tip);'));
  assert.ok(css.includes('[data-tip]:is(:hover,:focus-visible)::after{display:block;animation:tip-show 1ms linear .4s both}'));
});

test('components.js is loaded after shapes.js and before reader.js, which calls it', () => {
  const boot = read('static-boot.js');
  const list = boot.slice(boot.indexOf('for(const name of ['), boot.indexOf(']', boot.indexOf('for(const name of [')));
  assert.ok(list.indexOf("'shapes.js'") < list.indexOf("'components.js'") && list.indexOf("'components.js'") < list.indexOf("'reader.js'"), list);
});

// ---- Fix round 1 (review of the shell): the drawer slides, the row trace control's state and focus, no run code on findings pages, toast host, print.
test('S1: the closed drawer stays laid out off-screen so it can slide; the global [hidden] rule is beaten, and it is not readable while closed', () => {
  const css = read('screen.css');
  assert.match(css, /\.inspector\[hidden\]\{display:flex!important;visibility:hidden;transform:translateX\(100%\)\}/);
  assert.ok(css.includes('[hidden]{display:none!important}'), 'the global rule is still there; the drawer rule is more specific');
  const motion = css.slice(css.indexOf('@media(prefers-reduced-motion:no-preference){', css.indexOf('/* ---- Library redesign, shell')));
  assert.match(motion, /\.inspector\{transition:transform \.3s/);
  assert.match(motion, /\.inspector\[hidden\]\{transition:transform \.3s[^}]*visibility 0s linear \.3s\}/);
});

test('Q1 and Q2: the row trace control is cleared when the drawer closes and is the opener of a routed row', () => {
  const screen = read('screen.js');
  assert.ok(screen.includes(".chip[aria-pressed],.trace-row[aria-pressed],[data-paragraph][aria-pressed]"), 'the close branch clears the row control');
  assert.ok(screen.includes('const opener=`.chip[data-evidence="${CSS.escape(next.evidence)}"],.trace-row[data-evidence="${CSS.escape(next.evidence)}"],[data-paragraph="${CSS.escape(next.evidence)}"]`'));
  assert.ok(!screen.includes("$('inspector').scrollIntoView"), 'a fixed drawer does not scroll into view');
});

test('dead has-evidence rules are gone', () => {
  assert.ok(!read('screen.css').includes('has-evidence') && !read('screen.js').includes('has-evidence'));
});

test('Q3: findings pages name a run by date and pathway, never by its code: other-runs links, the model picker and the route announcement', () => {
  const page = histPage();
  const src = read('views.js'), screen = read('screen.js');
  assert.ok(!/unavailableView[\s\S]*?\$\{esc\(run\.run\)\}/.test(src.slice(src.indexOf('function unavailableView('), src.indexOf('function unavailableView(') + 900)), 'the other-runs link text is not the run code');
  assert.ok(src.slice(src.indexOf('function unavailableView(')).includes('esc(runName(run))'));
  assert.equal(page.runName(HIST.contexts['run-b']), '31 March 2025 · Full credit assessment');
  assert.ok(!screen.includes('${contexts[next.context].run}, '), 'the announcement does not read the run code');
  assert.ok(screen.includes('${runName(contexts[next.context])}, '));
});

test('Q4: the toast host is a role=status element that exists before the first message', () => {
  const src = read('components.js');
  assert.ok(src.includes('function toastHost()') && src.includes('toastHost();'), 'the host is made at load');
});

test('Q5: trace icons do not print', () => {
  assert.match(read('screen.css'), /@media print\{[^@]*\.basis-link[^@]*display:none!important/);
});

// ---- fix round 1: a plain-page chart has one trace control, the handoff's own characters, and no raw text in a title attribute.
const plainChart = (mutate, chart) => runPage(mutate).readerChart(outId('CP-1'), chart, false, true, true);
test('plain-page charts (fix round 1): one trace control, no per-row source button, no classification badge', () => {
  for (const [mutate, chart] of [[withStructure, STACK], [withBridge, BRIDGE_CHART], [withStructure, BULLET], [withStructure, LIMITS], [withRecovery, RECOVERY]]) {
    const html = plainChart(mutate, chart);
    assert.equal(countOf(html, /class="basis-link trace-row"/g), 1, `${chart.kind}: one trace control`);
    assert.equal(countOf(html, /class="source-link"/g) + countOf(html, /row-classification/g), 0, `${chart.kind}: no key button, no badge`);
  }
  assert.ok(countOf(runPage(withStructure).readerChart(outId('CP-1'), STACK), /class="source-link"/g) > 0, 'an earlier-format page keeps its key buttons');
});
test('plain-page charts (fix round 1): a cell is drawn as written (no added % or x); a "Not supplied" cell is its own text, never n.a. with the text in a title', () => {
  const rec = plainChart(withRecovery, RECOVERY);
  assert.ok(!/·\s*\d+%/.test(rec) && !rec.includes('90%') && !rec.includes('title="Not supplied') && !rec.includes('>n.a.<'), rec.slice(0, 0));
  assert.ok(strip(rec).includes('Not supplied: no downside value'));
  const stack = plainChart(withStructure, STACK);
  assert.ok(!stack.includes('title="Not supplied') && !stack.includes('>n.a.<') && strip(stack).includes('Not supplied: not stated') && !stack.includes('2.4x'));
  const early = runPage(withRecovery).readerChart(outId('CP-1'), RECOVERY);
  assert.ok(early.includes('90%') && early.includes('title="Not supplied'), 'earlier format unchanged');
});

test('A8: a plain-page chart names its figures in attributes from the same text the visible label draws: no n.a., no raw "Not supplied" cell text', () => {
  const attrs = html => [...html.matchAll(/(?:title|aria-label)="([^"]*)"/g)].map(m => m[1]).concat([...html.matchAll(/<title>(.*?)<\/title>/g)].map(m => m[1]));
  for (const [maker, chart] of [[withStructure, BULLET], [withStructure, LIMITS], [withRecovery, RECOVERY]]) {
    const html = plainChart(maker, chart);
    for (const a of attrs(html)) assert.ok(!/Not supplied|\bn\.a\./.test(a), `${chart.kind}: ${a}`);
  }
  assert.ok(attrs(plainChart(withStructure, BULLET)).includes('Liquidity: threshold 100, Passes at or above'), 'a part with no stated figure is left out of the spoken statement');
});

test('A9: a plain-page chart cell the page holds back for a calculation ID draws the link to Evidence in its place, not nothing', () => {
  const held = d => {
    withStructure(d);
    const block = d[outId('CP-1')].sections.flatMap(section => section.blocks).find(b => b.type === 'table' && b.rows.some(row => row.line === 103));
    block.rows.find(row => row.line === 103).cells[2] = 'Calculation C01 result';
    return d;
  };
  const html = plainChart(held, BULLET);
  assert.ok(/<span class="structure-text">[^<]*Current <a class="in-ev" href="[^"]+">In Evidence<\/a>/.test(html) || html.includes('class="in-ev"'), html.slice(0, 0));
  assert.ok(!html.includes('Calculation C01'), 'the calculation ID itself is not drawn');
});

test('A6: a chart-gap card carries one trace control, as a drawn chart card does', () => {
  const page = h1Page([sec('Chart data: covenant headroom', 3, 35, 'consumed', [chartTable(37, [[38, 'FY2024', 'Not supplied: no covenant is stated', 'x (net debt to EBITDA)', 'not established for this run and not a compliance opinion']])])], {chartGaps: [{title: 'Covenant headroom', table: 37, gap: 'no covenant is stated'}]});
  const html = page.moduleReport(a1Id);
  const card = /<div class="panel-card" id="s-35">.*?(?=<div class="panel-card" id="s-40">)/s.exec(html)[0];
  assert.equal((card.match(/class="basis-link trace-row"/g) || []).length, 1);
});

test('A7: a map card whose edge-table reason was held back draws one "In Evidence" link', () => {
  const page = h1Page([sec('Map: legal entities', 3, 410, 'consumed', [table(412, MAP_HEAD, [[413, 'Not supplied: no edge is stated', 'Not supplied: x', 'Not supplied: x', 'Not supplied: x', 'Not supplied: see CP-0 source readiness register']]), text(414, 'Map caption.')])], {maps: [...a1Set.maps, {name: 'legal entities', table: 412, gap: 'no edge is stated'}]});
  const card = /<div class="map-card" id="s-410">.*?Map caption\./s.exec(page.moduleReport(a1Id))[0];
  assert.equal((card.match(/class="in-ev"/g) || []).length, 1);
  assert.ok(!card.includes('CP-0 source'));
});

// ---- Changes (library redesign, task 9): views.js's changesView gathers the run's CP-8 handoff, its drawer-key output and the Overview link, and gives them to changes.js.
test('changesView hands changes.js the CP-8 output (id, module, run, chip counts) and the Overview route, and draws the page from them', () => {
  const src = read('views.js');
  const body = src.slice(src.indexOf('function changesView(context) {'), src.indexOf('function workspaceView'));
  const cp8 = [sec('Findings', 2, 1, 'view', []), sec('Bottom line', 3, 3, 'view', [text(4, 'About the same. Nothing moved.\nBasis: changes.json')]),
    sec('What changed: the issuer', 3, 10, 'view', [table(11, ['Measure or fact', 'Earlier', 'Current'], [[12, 'Leverage', '6.01x', '6.01x']])])];
  const given = [];
  const run = { folder: 'run-1', issuerKey: 'tdg', pathway: 'credit_snapshot', asOf: '2024-09-30', modules: { 'CP-8': { default: 'out-8' } },
    changes: { lead: 'CP-2', first_run: false, pack: { schema: 'cpos-changes/2', prior: { run: 'r0', as_of: '2024-09-30' }, current: { as_of: '2024-09-30' }, measures: [], modules: [] }, note: null, problem: null, verdicts: { measures: {}, modules: {}, ledger: null } } };
  const win = { CREDIT_OS_DATA: { chips: { 'out-8:4': [{ kind: 'gap' }, { kind: 'gap' }] } }, DESIGN_CATALOGUE: { real: [] } };
  const real = require('./changes.js');
  const spy = { changesHtml: input => { given.push(input); return real.changesHtml(input); }, leadBottom: real.leadBottom };
  const html = new Function('contexts', 'data', 'historyRows', 'sameIssuer', 'window', 'runPathway', 'displayDate', 'routeHref', 'evidenceInput', 'moduleLabel', 'moduleHref', 'ChangesView', `${body}; return changesView;`)(
    { 'run-1': run }, { 'out-8': { id: 'out-8', module: 'CP-8', run: 'run-1', sections: cp8 } }, rows => rows, (a, b) => a === b, win, () => 'Credit snapshot', iso => iso,
    (module, section, key, context) => `#${module}/${section}?c=${context}`, context => ({ run: { context, evidence: null, steps: [], methodChanges: [] }, modules: [{ id: 'CP-8', outputs: [{ id: 'out-8', sections: cp8 }] }], chips: {}, deps: { moduleTitle: x => x } }), code => ({ 'CP-1': 'Financial foundation' })[code] ?? null, code => `#${code}/head`, spy)('run-1');
  assert.equal(given.length, 1);
  const out = given[0].output;
  assert.deepEqual({ id: out.id, module: out.module, run: out.run, chips: out.chips('out-8:4'), none: out.chips('out-8:9') }, { id: 'out-8', module: 'CP-8', run: 'run-1', chips: 2, none: 0 });
  assert.equal(given[0].overviewHref, '#W-Overview/overview?c=run-1');
  assert.equal(given[0].cp8, cp8);
  assert.equal(given[0].modules.name('CP-1'), 'Financial foundation', 'a module is named by its catalogue title');
  assert.equal(given[0].modules.href, undefined, 'the page links to no module page for a bottom line');
  assert.equal(given[0].evidence.modules[0].id, 'CP-8', 'the evidence input the Gaps tab reads');
  assert.ok(html.includes('class="verdict"') && html.includes('data-paragraph="out-8:4"'), 'the drawer key names the CP-8 output and the paragraph line');
  assert.ok(html.includes('href="#W-Evidence/gaps?c=run-1&amp;m=CP-8"') === false, 'no ledger, no link');
  // A run with no CP-8 handoff gives no output and no sections: the page says so and still draws.
  const none = new Function('contexts', 'data', 'historyRows', 'sameIssuer', 'window', 'runPathway', 'displayDate', 'routeHref', 'evidenceInput', 'moduleLabel', 'moduleHref', 'ChangesView', `${body}; return changesView;`)(
    { 'run-1': { ...run, modules: {} } }, {}, rows => rows, (a, b) => a === b, win, () => 'Credit snapshot', iso => iso, () => '#x', () => ({ run: { steps: [], methodChanges: [] }, modules: [], chips: {}, deps: {} }), () => null, () => '#m', spy)('run-1');
  assert.ok(none.includes('The explanation of the changes is not held for this run.') && given[1].output === null && given[1].cp8 === null);
});

// ---- The Forecast page's run charts (Task 10): small multiples, one card per chart contract; form by contract kind and shape; the table, the footnote and ONE trace control per card.
const FC_HEAD = ['Period', 'EBITDA / cash interest', 'Reporting unit', 'Basis and limitation'];
const fcSections = () => [
  sec('Chart data: cover', 3, 10, 'consumed', [table(12, FC_HEAD, [[13, 'FY2023', '2.93', 'x', 'EBITDA over interest; calculation C13'], [14, 'FY2024', '3.60', 'x', 'Over cash interest, net']])]),
  sec('Chart data: revenue', 3, 20, 'consumed', [table(22, ['Period', 'Revenue', 'Adjusted EBITDA', 'Reporting unit', 'Basis and limitation'], [[23, 'FY2023', '6585', '3395', 'US$m', 'Annual; K_10.htm.jsonl, pages 71'], [24, 'FY2024', '7940', '4173', 'US$m', 'Annual <b>&"quoted"']])]),
  sec('Chart data: maturities', 3, 30, 'consumed', [table(32, ['Period', 'Debt maturing', 'Reporting unit', 'Basis and limitation'], [[33, 'FY2025', '93', 'US$m', 'Schedule; downside SC1 case'], [34, 'FY2026', '92', 'US$m', 'Schedule'], [35, 'FY2027', '6637', 'US$m', 'Schedule']])]),
  sec('Chart data: odd', 3, 40, 'consumed', [table(42, ['Item', 'Value', 'Source'], [[43, 'Alpha <b>&"', '12', 'K.jsonl, page 3']])]),
  sec('Chart data: limits', 3, 50, 'consumed', [table(52, ['Period', 'Limit'], [[53, 'FY2024', 'Not supplied: no limit stated in any source']])]),
];
const fcOutput = (extra = {}) => runOutput('CP-1', {
  sections: fcSections(), state: { established: true, declared: null }, summary: null, words: {}, period: 'As of 2025-03-31',
  charts: [{ title: 'Interest cover', unit: 'x', table: 12, columns: [1] }, { title: 'Revenue and EBITDA', unit: 'US$m', table: 22, columns: [1, 2] }, { title: 'Debt maturities', unit: 'US$m', table: 32, columns: [1] }, { title: 'Odd chart', unit: '', table: 42, kind: 'sunburst' }],
  chartGaps: [{ title: 'Portfolio limits', table: 52, gap: 'no limit stated' }], ...extra,
});
const fcPage = (extra, more = {}) => runPage(() => ({ [outId('CP-1')]: fcOutput(extra) }), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' }, ...more });
const fcCards = html => html.split('<article class="fc-card"').slice(1).map(card => `<article class="fc-card"${card.split('</article>')[0]}</article>`);
const cardOf = (html, title) => fcCards(html).find(card => card.includes(`<h3>${title}</h3>`));
const fcAuditText = /\.jsonl|\.htm\b|[Cc]alculations? [A-Z]{1,2}\d{2}\b|\bSC\d\b|sha256/;

test('Forecast charts: one card per contract and gap, in the data\'s order, in the 24-column grid; a two-row single-measure period contract is a prior-value tile, never a line', () => {
  const html = fcPage().forecastCharts(RUN);
  assert.deepEqual([...html.matchAll(/<article class="fc-card"[^>]*aria-label="([^"]*)"/g)].map(m => m[1]), ['Interest cover', 'Revenue and EBITDA', 'Debt maturities', 'Odd chart', 'Portfolio limits']);
  assert.ok(html.includes('class="g24 fc-grid"') && html.includes('id="run-charts"') && html.includes('5 charts, 1 not drawn'));
  const cover = cardOf(html, 'Interest cover');
  const figure = cover.replace(/<svg class="i"[\s\S]*?<\/svg>/g, '');
  assert.ok(cover.includes('class="fc-pair"') && !/<polyline|<path|<svg/.test(figure), 'no line is drawn through two points');
  assert.ok(/<span class="fc-k">FY2023<\/span><strong>2\.93<\/strong><\/p><p class="fc-period"><span class="fc-k">FY2024<\/span><strong>3\.60<\/strong>/.test(cover), 'both periods, the cells as written, in the table\'s order at the same weight (the contract does not say which is later)');
  const revenue = cardOf(html, 'Revenue and EBITDA');
  assert.ok(!revenue.includes('fc-pair') && revenue.includes('class="column-chart"'), 'two measures over two periods are paired columns');
  assert.ok(cardOf(html, 'Debt maturities').includes('class="column-chart"'), 'amounts by period are columns');
});

test('Forecast charts: every non-hidden cell of a contract\'s rows is in the card\'s table; a cell that names an identifier is held back with a link to Evidence', () => {
  const html = fcPage().forecastCharts(RUN);
  const tableOf = card => /<div data-pane="table"[^>]*>(.*?)<\/table>/s.exec(card)[1];
  const cover = tableOf(cardOf(html, 'Interest cover'));
  for (const text of ['FY2023', '2.93', 'FY2024', '3.60', 'Over cash interest, net', 'Period', 'EBITDA / cash interest', 'Reporting unit', 'Basis and limitation']) assert.ok(strip(cover).includes(text), text);
  assert.ok(cover.includes('class="in-ev"') && !strip(cover).includes('calculation C13'));
  const revenue = tableOf(cardOf(html, 'Revenue and EBITDA'));
  for (const text of ['6585', '3395', '7940', '4173', 'US$m']) assert.ok(strip(revenue).includes(text), text);
  assert.ok(!revenue.includes('.jsonl'), 'a file name inside a basis cell is held back');
});

test('Forecast charts: each card has exactly one trace control and no per-period source button', () => {
  const html = fcPage().forecastCharts(RUN);
  for (const card of fcCards(html)) {
    assert.equal(countOf(card, /class="basis-link/g), 1, card.slice(0, 200));
    assert.ok(!/<button[^>]*class="chart-row"/.test(card) && !card.includes('View source'));
  }
});

test('Forecast charts: no file name, calculation ID or scenario id in the text or any attribute of the page (the drawer keys of the trace buttons aside)', () => {
  const html = fcPage().forecastCharts(RUN).replace(/ data-evidence="[^"]*"/g, '');
  assert.ok(!fcAuditText.test(html), (html.match(fcAuditText) || [])[0]);
  assert.ok(!html.includes('SC1') && !html.includes('K_10'));
});

test('Forecast charts: the contract\'s Basis and limitation is a visible footnote, verbatim, and a held-back text is one link to Evidence', () => {
  const html = fcPage().forecastCharts(RUN);
  const cover = cardOf(html, 'Interest cover'), note = /<div class="fc-note">.*?<\/div>/s.exec(cover)[0];
  assert.ok(note.includes('Basis and limitation') && note.includes('Over cash interest, net') && !note.includes('in-ev'), 'drawn lines under the heading');
  assert.ok(/<div class="fc-foot"><a class="in-ev"[^>]*>In Evidence<\/a><a class="text-action"/.test(cover), 'the held-back line is one link in the footer, beside the module link');
  const maturities = /<div class="fc-note">.*?<\/div>/s.exec(cardOf(html, 'Debt maturities'))[0];
  assert.ok(maturities.includes('<b>FY2026, FY2027</b> Schedule') && !maturities.includes('SC1'));
});

test('Forecast charts: a chart gap is the empty state with its stated reason verbatim, in a card of its own, with one trace control', () => {
  const html = fcPage().forecastCharts(RUN), gap = cardOf(html, 'Portfolio limits');
  assert.ok(gap.includes('class="empty-state"') && strip(gap).includes('Not supplied: no limit stated in any source') && !gap.includes('class="column-chart"'));
  assert.equal(countOf(gap, /class="basis-link/g), 1);
  const bare = fcPage({ charts: [], chartGaps: [{ title: 'Portfolio limits', table: 42, gap: 'No holdings report attached' }] }).forecastCharts(RUN);
  assert.ok(strip(cardOf(bare, 'Portfolio limits')).includes('No holdings report attached'), 'the build\'s stated reason stands in when the table states none');
});

test('Forecast charts: the toggle is the shared Chart or Table switch (aria-pressed, the table hidden at first); an unknown contract kind is its table as written, with no toggle', () => {
  const html = fcPage().forecastCharts(RUN), cover = cardOf(html, 'Interest cover');
  assert.ok(cover.includes('data-block') && cover.includes('data-view="chart"') && cover.includes('data-view-pick="chart" aria-pressed="true"') && cover.includes('data-view-pick="table" aria-pressed="false"'));
  assert.ok(cover.includes('<div data-pane="chart">') && cover.includes('<div data-pane="table" hidden>'));
  const odd = cardOf(html, 'Odd chart');
  assert.ok(odd.includes('<div data-pane="table">') && !odd.includes('data-view-pick') && !odd.includes('data-pane="table" hidden') && odd.includes('dtbl'), 'never an empty card');
  assert.ok(odd.includes('Alpha &lt;b&gt;&amp;&quot;') && !odd.includes('K.jsonl'), 'a cell with <b>&" is escaped');
});

test('Forecast charts: a contract that carries markup characters is escaped in the figure and the table', () => {
  const html = fcPage().forecastCharts(RUN), revenue = cardOf(html, 'Revenue and EBITDA');
  assert.ok(!revenue.includes('<b>&"') && revenue.includes('&lt;b&gt;&amp;&quot;'), 'the basis cell');
});

test('Forecast charts: a run with no chart says so (the empty state), and a not-assessable module\'s chart is a card saying why', () => {
  const none = fcPage({ charts: [], chartGaps: [] }).forecastCharts(RUN);
  assert.ok(none.includes('class="empty-state"') && none.includes('No chart in this run') && !none.includes('fc-grid'));
  const only = fcPage({ charts: [] }).forecastCharts(RUN);
  assert.ok(only.includes('1 chart, 1 not drawn') && fcCards(only).length === 1, 'gaps only');
  const hidden = fcPage({ state: { established: false, declared: null }, summary: { limitation: 'No comparable source.' } }).forecastCharts(RUN);
  assert.ok(strip(cardOf(hidden, 'Interest cover')).includes('No comparable source.') && !cardOf(hidden, 'Interest cover').includes('fc-pair'));
});

test('Forecast page: charts but no model show the charts after the no-model statement; the Chart index is no longer on the page', () => {
  const page = fcPage();
  const html = page.forecastView(RUN);
  assert.ok(html.includes('No forecast model was published') && html.indexOf('missing-state') < html.indexOf('run-charts'));
  assert.ok(!html.includes('Chart index') && !html.includes('index-table'));
});

test('Forecast page with a model: the register, the limitations and Built from draw no file name, hash, calculation or scenario id; the model frame gains only a framed header', () => {
  const model = pickModel(HASH_1, {
    mode: 'candidate', qualification: 'partial', download: '../d/model.html', href: '../d/model.html', scope: 'A forecast.',
    register: { heading: 'Assumption register', headers: ['assumption_id', 'driver', 'source', 'rationale'], rows: [['A-01', 'revenue growth', 'K_10.htm.jsonl, page 45', 'Fade from 16.2%'], ['A-02', 'downside shock SC1', 'calculation G06', 'Moderate case']] },
    cashflow: { units: 'USD millions', columns: gridColumns, notes: [], limits: ['Every figure is arithmetic.', 'Downside is scenario SC1: a rate rise.'], rows: [gridRow('Revenue', 'Revenue', false, [cell('value', '1,000'), cell('value', '1,050')])], other: null },
    sources: [{ role: 'annual', run: RUN, path: `runs/${RUN}/x/annual.md`, sha256: HASH_1, changed: false }],
  });
  const html = fcPage(undefined, { models: [model], runFields: PICK_RUNS }).forecastView(RUN, HASH_1);
  const clean = html.replace(/ data-evidence="[^"]*"/g, '').replace(/ (?:value|data-download|data-src|href)="[^"]*"/g, '');
  assert.ok(!fcAuditText.test(clean) && !clean.includes(HASH_1.slice(0, 12)) && !/SHA-256|attempt-/.test(clean), (clean.match(fcAuditText) || [])[0]);
  assert.ok(html.includes('class="frame-head"') && html.includes('id="model-preview"') && html.includes('data-src="../d/model.html"') && html.includes('Open ') === false);
  assert.ok(strip(html).includes('Every figure is arithmetic.') && strip(html).includes('1 further limitation is stated in Evidence'));
  assert.ok(html.indexOf('id="run-charts"') < html.indexOf('id="model-select"') && html.includes('<details class="forecast-register">'));
  assert.ok(!strip(html.slice(html.indexOf('forecast-register'), html.indexOf('</details>', html.indexOf('forecast-register')))).includes('A-01'), 'the id column is Evidence\'s');
});

test('Forecast page: the download link and the model frame say HTML only when the published model is an HTML file', () => {
  const draw = (file) => {
    const model = pickModel(HASH_1, {
      mode: 'candidate', qualification: 'partial', download: file, href: file, scope: 'A forecast.',
      cashflow: { units: 'USD millions', columns: gridColumns, notes: [], limits: [], rows: [gridRow('Revenue', 'Revenue', false, [cell('value', '1,000'), cell('value', '1,050')])], other: null },
      sources: [],
    });
    return fcPage(undefined, { models: [model], runFields: PICK_RUNS }).forecastView(RUN, HASH_1);
  };
  const html = draw('../d/model.html?v=1');
  assert.ok(html.includes('>Download original HTML</a>') && html.includes('<summary>Published model (original HTML)</summary>') && html.includes('class="model-original"'));
  const md = draw('../d/annual.md?v=1');
  assert.ok(md.includes('>Download published model (Markdown)</a>'), 'the Markdown link says Markdown');
  assert.ok(!md.includes('original HTML') && !md.includes('model-original') && !md.includes('model-preview'), 'no HTML frame for a Markdown file');
});

test('Forecast charts: an earlier-format run draws the same cards and links each to its module\'s Key numbers; a new-format run links the Charts part', () => {
  const earlier = fcPage().forecastCharts(RUN);
  assert.equal(fcCards(earlier).length, 5);
  assert.ok(earlier.includes('#CP-1/numbers?') && !earlier.includes('#CP-1/charts?'));
  const newer = fcPage({ sections: [...passageSections({ bottom: 'Cash is up.' }), ...fcSections()] }).forecastCharts(RUN);
  assert.ok(newer.includes('#CP-1/charts?') && !newer.includes('#CP-1/numbers?'));
});

// ---- Task 10 fix round 1.
const allKinds = d => { withBridge(d); withStructure(d); withComparison(d); withRecovery(d); d[outId('CP-1')].sections.flatMap(s => s.blocks).find(b => b.line === 162).rows.forEach(r => { r.cells[5] = 'K_10.htm.jsonl, page 4'; }); return d; };
const MARK_LINKS = /<a [^>]*class="(?:plot-point|stack-seg)|<a [^>]*class="col|<button[^>]*class="(?:chart-open|chart-row)"|View source/;

test('M1: no chart mark is a link or a button on a Forecast card or a new-format module page, whatever the kind; one trace control; no delivery path in an href; no source cell in a key', () => {
  const page = runPage(d => allKinds(d), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' } });
  const cards = fcCards(page.forecastCharts(RUN));
  assert.ok(cards.length >= 12, `every kind has a card (${cards.length})`);
  for (const card of cards) {
    const name = /aria-label="([^"]*)"/.exec(card)[1];
    assert.ok(!MARK_LINKS.test(card), `${name}: a mark is a link or button`);
    assert.ok(countOf(card, /data-evidence="/g) <= 1, `${name}: more than one trace control`);
    assert.ok(![...card.matchAll(/href="([^"]*)"/g)].some(m => /\.md|deliveries/.test(m[1])), `${name}: an href carries the delivery path`);
    assert.ok(!card.includes('jsonl'), `${name}: a source cell is drawn`);
  }
  // The same renderers on a new-format module page (the plain path) draw no mark link either.
  const newer = runPage(d => { allKinds(d); d[outId('CP-1')].sections.unshift(...passageSections({ bottom: 'Cash is up.' })); return d; }, [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' } });
  for (const chart of [BRIDGE_CHART, STACK, BULLET, LIMITS, GROUPED, DUMBBELL, RANGE, SCATTER, RECOVERY]) {
    const html = newer.readerChart(outId('CP-1'), chart, false, true, true);
    assert.ok(!MARK_LINKS.test(html) && countOf(html, /data-evidence="/g) <= 1, chart.title);
  }
  // Earlier-format pages keep their links.
  assert.ok(/<a class="plot-point"/.test(runPage(withBridge).readerChart(outId('CP-1'), BRIDGE_CHART)));
});

test('M2: every text a Forecast card draws is read strictly: a stated absence that names a file or scenario is held back in the figure as in the table', () => {
  const sections = fcSections();
  sections[0].blocks.find(b => b.type === 'table').rows[1].cells[1] = 'Not supplied: no split in K_10.htm.jsonl, scenario SC2';
  sections[2].blocks.find(b => b.type === 'table').rows[1].cells[1] = 'Not supplied: schedule in K_10.htm.jsonl omitted';
  const html = fcPage({ sections }).forecastCharts(RUN);
  for (const title of ['Interest cover', 'Debt maturities']) assert.ok(!/jsonl|SC2/.test(cardOf(html, title)), title);
  // A clean stated absence is still drawn, under the chart, with a marker in the value's own column.
  const clean = fcPage().forecastCharts(RUN);
  assert.ok(!clean.includes('jsonl'));
});

test('F4: a stated absence for one value is a marker in that value\'s column and its sentence sits beneath the chart, not over the bars', () => {
  const sections = fcSections();
  sections[1].blocks.find(b => b.type === 'table').rows[0].cells[2] = 'Not supplied: FY2023 split not read in this pass';
  const revenue = cardOf(fcPage({ sections }).forecastCharts(RUN), 'Revenue and EBITDA');
  const plot = revenue.split('<div class="periods">')[1].split('class="fc-absent"')[0];
  assert.ok(!plot.includes('Not supplied') && plot.includes('absent-mark'), 'the plot holds only the marker');
  assert.ok(/<ul class="fc-absent"><li><span class="absent-mark"[^>]*>†<\/span><b>FY2023<\/b> Adjusted EBITDA: Not supplied: FY2023 split not read in this pass<\/li>/.test(revenue));
});

test('F2: a Forecast bridge prints each step once, in full: bars are numbered and one numbered list names them', () => {
  const page = runPage(d => withBridge(d), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' } });
  const html = page.forecastCharts(RUN), bridge = cardOf(html, 'Liquidity bridge').split('data-pane="table"')[0];
  const labels = SYNTHETIC_BRIDGE.map(row => row[1]);
  const visible = strip(bridge.replace(/<title>.*?<\/title>/g, ''));
  for (const label of labels) assert.equal(countOf(visible, new RegExp(label, 'g')), 1, `${label} once in the page text`);
  assert.ok(bridge.includes('<ol class="bridge-key bridge-numbered">') && /<tspan[^>]*>1<\/tspan>/.test(bridge));
});

test('F5: a Forecast stack row sets rank, security, amount and leverage as label and value pairs', () => {
  const page = runPage(d => withStructure(d), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' } });
  const stack = cardOf(page.forecastCharts(RUN), 'Debt stack');
  assert.ok(stack.includes('<dl class="stack-facts"><div><dt>Rank</dt><dd>1</dd></div><div><dt>Secured</dt><dd>Yes</dd></div><div><dt>Amount</dt><dd>1,200</dd></div><div><dt>Cumulative leverage</dt><dd>2.4</dd></div></dl>'));
  assert.ok(!stack.includes('Rank 1 · Secured Yes'));
});

test('F1: a card whose whole footnote is held back has no heading, only the link in its footer; a card with nothing to say has neither', () => {
  const sections = fcSections();
  const revenue = cardOf(fcPage({ sections }).forecastCharts(RUN), 'Revenue and EBITDA');
  assert.ok(revenue.includes('Annual &lt;b&gt;'), 'one line drawn (the second row)');
  const rows = sections[1].blocks.find(b => b.type === 'table').rows;
  rows[1].cells[4] = 'Annual; K_10.htm.jsonl, pages 71';
  const held = cardOf(fcPage({ sections }).forecastCharts(RUN), 'Revenue and EBITDA');
  assert.ok(!held.includes('fc-note') && !held.includes('Basis and limitation</p>') && /<div class="fc-foot"><a class="in-ev"/.test(held));
  rows.forEach(r => { r.cells[4] = ''; });
  const none = cardOf(fcPage({ sections }).forecastCharts(RUN), 'Revenue and EBITDA');
  assert.ok(!none.includes('fc-note') && !none.includes('in-ev') && none.includes('<div class="fc-foot"><a class="text-action"'));
});

test('M5: a chart the build sent back is a card in its data position with the fixed label, no reason text and a link to Evidence\'s Run record; the message is listed there', () => {
  const extra = sec('Chart data: covenant tests', 3, 45, 'consumed', [table(46, ['Test', 'Odd'], [[47, 'Net leverage', 'x']])]);
  const sections = fcSections(); sections.splice(3, 0, extra);
  const page = fcPage({ sections, issue: 'Chart data: covenant tests is not in its fixed table' });
  const html = page.forecastCharts(RUN);
  assert.deepEqual([...html.matchAll(/<article class="fc-card"[^>]*aria-label="([^"]*)"/g)].map(m => m[1]), ['Interest cover', 'Revenue and EBITDA', 'Debt maturities', 'Odd chart', 'Covenant tests', 'Portfolio limits']);
  const card = cardOf(html, 'Covenant tests');
  assert.ok(card.includes('Sent back by the build') && card.includes('class="empty-state"') && !card.includes('fixed table') && /href="#W-Evidence\/record\?c=run-a&amp;m=CP-1"|href="#W-Evidence\/record\?c=run-a&m=CP-1"/.test(card));
  assert.ok(html.includes('6 charts, 2 not drawn'));
  const record = window_Evidence().view(fcPage({ sections, issue: 'Chart data: covenant tests is not in its fixed table' }, { runFields: { evidence: EVIDENCE } }).evidenceInput(RUN), { tab: 'record', module: null });
  assert.ok(record.includes('Charts the build sent back') && strip(record).includes('Chart data: covenant tests is not in its fixed table'));
});
const window_Evidence = () => require('./evidence.js');

test('M4: the delivered model\'s inputs are in the Run record, its scope limits in the Gaps tab as their own counted group (gapCount unchanged); the page links to the tab that holds them', () => {
  const HASH = 'ab12cd34ef56'.repeat(5);
  const model = pickModel(HASH_1, {
    mode: 'candidate', qualification: 'partial', download: '../d/model.html', href: '../d/model.html',
    cashflow: { units: 'USD millions', columns: gridColumns, notes: [], limits: ['Every figure is arithmetic.', 'Downside is scenario SC1: a rate rise.'], rows: [gridRow('Revenue', 'Revenue', false, [cell('value', '1,000'), cell('value', '1,050')])], other: null },
    sources: [{ role: 'annual', run: RUN, path: `runs/${RUN}/x/CP-1-attempt-2.md`, sha256: HASH, changed: true }, { role: 'forecast', run: RUN, path: `runs/${RUN}/x/CP-2G-attempt-1.md`, sha256: HASH, changed: false }],
  });
  const withModel = fcPage(undefined, { models: [model], runFields: { ...PICK_RUNS, evidence: EVIDENCE } }), without = fcPage(undefined, { runFields: { evidence: EVIDENCE } });
  const E = window_Evidence(), input = withModel.evidenceInput(RUN);
  assert.equal(E.gapCount(input), E.gapCount(without.evidenceInput(RUN)), 'scope limits are not gap rows');
  const gaps = E.view(input, { tab: 'gaps', module: null });
  assert.ok(gaps.includes('Model scope limits') && gaps.includes('<span data-count>2</span> scope limits') && strip(gaps).includes('Downside is scenario SC1: a rate rise.'));
  const badge = (html, tab) => Number(new RegExp(`id="ev-tab-${tab}"[^>]*>.*?data-count>(\\d+)<`, 's').exec(html)[1]);
  // A17 (re-ruled): the badge is the gap count the tile shows; the scope limits are counted by their own group head (asserted above). Old pin: the badge was the panel's counted lines.
  assert.equal(badge(gaps, 'gaps'), E.gapCount(input), 'the Gaps badge is the number of the Gaps tile');
  assert.equal(countOf(gaps.slice(gaps.indexOf('id="ev-panel"')), /data-hay=/g), badge(gaps, 'gaps') + 2, 'the two scope limits are counted by their head, not the badge');
  const record = E.view(input, { tab: 'record', module: null });
  assert.ok(record.includes('Model inputs') && record.includes('CP-1-attempt-2.md') && record.includes(`SHA-256 ${HASH.slice(0, 12)}`) && record.includes('Changed since publication') && record.includes('Matches publication') && strip(record).includes('These files come from different attempts'));
  assert.equal(badge(record, 'record'), countOf(record.slice(record.indexOf('id="ev-panel"')), /data-hay=/g), 'the Run record badge is the counted items');
  const html = withModel.forecastView(RUN, HASH_1);
  assert.ok(/href="#W-Evidence\/gaps[^"]*"[^>]*>In Evidence/.test(html) && html.includes('1 further limitation is stated in Evidence'), 'the held-back limitation links to the Gaps tab');
});

test('Low 8-10, 12: a held-back not-assessable reason shows the fixed label and a link; the model frame names the run only; the register intro is read strictly; the frame heading is a sibling of Built from', () => {
  const hidden = fcPage({ state: { established: false, declared: null }, summary: { limitation: 'No source: K_10.htm.jsonl' } }).forecastCharts(RUN);
  const card = cardOf(hidden, 'Interest cover');
  assert.ok(card.includes('Not established for this run') && /<div class="es-trace"><a class="in-ev"/.test(card) && !card.includes('jsonl'));
  const model = pickModel(HASH_1, { mode: 'candidate', download: '../d/m.html', href: '../d/m.html', previous: HASH_2, register: { heading: 'Register', intro: 'See K_10.htm.jsonl for SC1', headers: ['driver', 'rationale'], rows: [['growth', 'Fade']] }, cashflow: { units: 'USD m', columns: gridColumns, notes: [], limits: [], rows: [gridRow('Revenue', 'Revenue', false, [cell('value', '1'), cell('value', '2')])], other: null } });
  const html = fcPage(undefined, { models: [model], runFields: PICK_RUNS }).forecastView(RUN, HASH_1);
  const frame = html.slice(html.indexOf('class="frame-head"'), html.indexOf('</iframe>'));
  assert.ok(frame.includes('<h2>Published model</h2>') && frame.includes('31 March 2025 · Full credit assessment') && !/supersedes|a1b2c3d4|run-a/.test(frame), frame);
  assert.ok(!html.includes('register-intro') && !html.includes('jsonl'));
});

test('F3 and Low 11: two-series marks use the blue and purple tokens (no green), and the grid keeps the data order', () => {
  const css = read('screen.css');
  assert.ok(/\.series-1\{background:var\(--series-4\)/.test(css) && /\.chart-legend \.series-1[^{]*\{background:var\(--series-4-ln\)/.test(css));
  assert.ok(!css.includes('grid-auto-flow:dense'));
});

test('Forecast grid: each row is filled (a lone narrow card widens, a pair shares the row); no card sits alone beside empty space', () => {
  const spans = html => [...html.matchAll(/<div class="c(\d+)(?: fc-wide)?"><article class="fc-card"/g)].map(m => Number(m[1]));
  assert.deepEqual(spans(fcPage().forecastCharts(RUN)), [8, 8, 8, 12, 12], 'three across, then the last two share the row');
  const only = fcPage({ charts: [fcOutput().charts[0]], chartGaps: [] }).forecastCharts(RUN);
  assert.deepEqual(spans(only), [24], 'one card takes the row');
});

// ---- Changes fix round 2 (N3): views.js builds the Evidence input's `comparison` from the run's pack; the page-level result is on Evidence's Calculations tab for CP-8.
test('Evidence Calculations for CP-8 lists the comparison measure and its computed difference from the run\'s own pack (views.js passes the comparison to Evidence)', () => {
  const side = (value, period) => ({ label: 'm', unit: 'US$m', value, period });
  const pack = { schema: 'cpos-changes/2', prior: { run: 'r0', as_of: '2024-09-30' }, current: { as_of: '2024-09-30' }, modules: [],
    measures: [{ key: 'cash', label: 'Cash', unit: 'US$m', prior: side('6261', '2024-09-30'), current: side('6300', '2024-09-30'), difference: '39' }] };
  const changes = { lead: 'CP-2', pack, note: null, problem: null, verdicts: { measures: { cash: { kind: 'comparable', label: 'Same definition' } }, modules: {}, ledger: null } };
  const cp8 = { id: 'o8', module: 'CP-8', run: 'r', sections: [sec('Findings', 2, 1, 'view', [])], placement: ['view'] };
  const withCp8 = evidenceView({ r: { evidence: EVIDENCE, modules: { 'CP-8': { outputs: ['o8'], default: 'o8' } }, changes } }, { o8: cp8 })('r', 'calculations', 'CP-8');
  assert.ok(withCp8.includes('Difference computed by the comparison') && /<td[^>]*>Cash<\/td>/.test(withCp8) && /<td[^>]*>39 US\$m<\/td>/.test(withCp8) && withCp8.includes('6261 US$m (2024-09-30)'));
  // A run whose changes record holds no pack lists none; one with no CP-8 entry lists them under the run-level group.
  assert.ok(!evidenceView({ r: { evidence: EVIDENCE, modules: { 'CP-8': { outputs: ['o8'], default: 'o8' } }, changes: { ...changes, pack: null } } }, { o8: cp8 })('r', 'calculations', 'CP-8').includes('Difference computed'));
  const orphan = evidenceView({ r: { evidence: EVIDENCE, modules: TWO_MODULES, changes } })('r', 'calculations');
  assert.ok(orphan.includes('>Comparison<') && /<td[^>]*>39 US\$m<\/td>/.test(orphan));
});

// ======== Library home and report history (library redesign, Task 11) ========
// Five issuers, six catalogue runs. ALP is the run RUN (the synthetic "real-shaped" run: a Committee decision lead, a metric table, a calculation ID in its ratio basis, a run code and folder); BET has two runs;
// GAM holds no module and no report; DEL has one module; NOC is in the catalogue only. Expected sets below are written by hand from these rows.
const LIB_CODE = 'ZED-PROOF-SNAPSHOT-OPUS-002', LIB_HASH = 'f'.repeat(64);
const libOut = (folder, code, bottom, declared = null) => { const id = `${folder}/deliveries/d1/${code}.md`; return [id, { ...histOut(id, code, bottom), state: { established: null, declared } }]; };
const libCtx = (folder, issuerKey, issuer, asOf, outs) => ({ folder, issuerKey, issuer, title: issuer, run: `${folder}-code`.toUpperCase(), asOf, pathway: 'credit_snapshot', modules: Object.fromEntries(outs.map(([id, out]) => [out.module, entryOf(id)])) });
const libMetric = (value, unit = 'x', basis = 'Total debt / EBITDA') => ({ value, unit, basis, period: 'FY2024' });
const BASIS_WITH_ID = 'Net figure uses year-end cash (calculation C11); calculations C05, C06';
const libCatalogue = () => [
  zedRun({ id: RUN, issuer: 'ALP', name: 'Alpha Telecom plc', sector: 'Telecoms', workflow: 'Credit Snapshot', date: '2025-03-31', metrics: { leverage: libMetric('5.5', 'x', BASIS_WITH_ID), net_leverage: libMetric('4.5'), coverage: libMetric('2.1') }, ratings: [{ label: 'B+', agency: 'S&P', scope: 'issuer', date: '2025-01-01' }],
    artifacts: [{ kind: 'report', label: LIB_HASH, state: 'candidate', relationship: 'direct', issue: '', available: false, href: '' }, { kind: 'model', label: 'Forecast', state: 'candidate', relationship: 'direct', issue: '', available: true, href: `../runs/${RUN}/deliveries/${LIB_HASH}/annual.md` }] }),
  zedRun({ id: 'run-b', issuer: 'BET', name: 'Beta Aero Inc', sector: 'Aerospace', workflow: 'Credit Snapshot', date: '2025-06-30', metrics: { leverage: libMetric('3.2'), net_leverage: libMetric('2.0'), coverage: libMetric('6.0') }, ratings: [{ label: 'BB', agency: 'S&P', scope: 'issuer', date: '2025-01-01' }] }),
  zedRun({ id: 'run-b0', issuer: 'BET', name: 'Beta Aero Inc', sector: 'Aerospace', workflow: 'Credit Snapshot', date: '2024-06-30', metrics: { leverage: libMetric('4.0') } }),
  zedRun({ id: 'run-g', issuer: 'GAM', name: 'Gamma <b>&"Co"', sector: 'Aerospace', workflow: 'Short <b>&"Snap"', date: '2025-01-31', metrics: { leverage: libMetric('8.0'), net_leverage: libMetric('7.0'), coverage: libMetric('1.0') }, artifacts: [] }),
  zedRun({ id: 'run-d', issuer: 'DEL', name: 'Delta Foods', sector: 'Consumer', workflow: 'Credit Snapshot', date: '2025-05-31', completion: 75, metrics: {}, ratings: [{ label: 'BBB', agency: 'S&P', scope: 'issuer', date: '2025-01-01' }] }),
  zedRun({ id: 'run-n', issuer: 'NOC', name: 'Nocontext Ltd', sector: 'Consumer', workflow: 'Credit Snapshot', date: '2025-02-28', metrics: { leverage: libMetric('6.0'), net_leverage: libMetric('5.0'), coverage: libMetric('3.0') }, ratings: [{ label: 'CCC', agency: 'S&P', scope: 'issuer', date: '2025-01-01' }] }),
];
function libBase() {
  const b = [libOut('run-b', 'CP-0', 'Sources are ready.', 'Ready'), libOut('run-b', 'CP-2A', 'Not assessable: no inputs were supplied.', 'Blocked'), libOut('run-b', 'CP-6', 'Hold the position. Leverage is high.', 'Restricted')];
  const b0 = [libOut('run-b0', 'CP-0', 'Sources are ready.')], d = [libOut('run-d', 'CP-0', 'Sources are ready.')];
  return { b, b0, d, contexts: { 'run-b': libCtx('run-b', 'bet', 'Beta Aero Inc', '2025-06-30', b), 'run-b0': libCtx('run-b0', 'bet', 'Beta Aero Inc', '2024-06-30', b0), 'run-g': libCtx('run-g', 'gam', 'Gamma', '2025-01-31', []), 'run-d': libCtx('run-d', 'del', 'Delta Foods', '2025-05-31', d) }, data: Object.fromEntries([...b, ...b0, ...d]) };
}
function libPage(more = {}) {
  const base = libBase();
  const models = [{ id: LIB_HASH, runId: 'x', runFolder: RUN, href: `../runs/${RUN}/deliveries/${LIB_HASH}/annual.md`, mode: 'candidate' }];
  return runPage(() => overviewData(realSections()), [], m => m, { record: steps(['CP-1', 'CP-6']), catalogue: libCatalogue(), models,
    runFields: { issuerKey: 'alp', issuer: 'Alpha Telecom plc', title: 'Alpha Telecom plc', run: LIB_CODE, asOf: '2025-03-31', pathway: 'credit_snapshot' },
    contexts: base.contexts, data: base.data, ...more });
}
const libIds = page => page.libraryRows().rows.map(r => r.id);
const libIssuers = page => new Set(page.libraryRows().rows.map(r => r.issuer)).size;
const decode = text => text.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
// The screen.js hash functions, run on the page's own filter state with a stand-in location (the node tests have no document).
function libHash(page, hash = '#W-Library/cases') {
  const src = read('screen.js'), loc = { hash };
  const fns = new Function('LIBRARY_DEFAULTS', 'libraryFilters', 'libraryState', 'libraryChoices', 'LibraryLogic', 'LIBRARY_COLUMNS', 'location', 'history', `${src.slice(src.indexOf('const LIBRARY_QUERY_KEYS='), src.indexOf('function resetLibrary()'))}; return {readLibraryHash, writeLibraryHash};`)(
    libraryDefaults(), page.libraryFilters, page.libraryState, page.libraryChoices, new Function(`${read('screening.js')}; return LibraryLogic;`)(), page.LIBRARY_COLUMNS, loc, { replaceState: (a, b, next) => { loc.hash = next; } });
  return { ...fns, loc };
}

// Every existing filter still changes the result set and the hash (one test per filter), and the address round-trips through the new bar.
const FILTER_CASES = [
  ['runs', 'any', ['run-a', 'run-b', 'run-b0', 'run-d', 'run-g', 'run-n']],
  ['issuer', 'BET', ['run-b']],
  ['sector', 'Aerospace', ['run-b', 'run-g']],
  ['workflow', 'Short <b>&"Snap"', ['run-g']],
  ['completion', '75', ['run-d']],
  ['completion', 'unassessed', ['run-a', 'run-b', 'run-g', 'run-n']],
  ['availability', 'report', ['run-a', 'run-b', 'run-d', 'run-n']],
  ['availability', 'handoff', ['run-g']],
  ['search', 'gamma', ['run-g']],
];
const ALL_LATEST = ['run-a', 'run-b', 'run-d', 'run-g', 'run-n'];
for (const [key, value, expected] of FILTER_CASES) {
  test(`library filter ${key}=${value}: the result set changes, the address carries it, and the address reads back to the same set`, () => {
    const page = libPage();
    assert.deepEqual(libIds(page).sort(), ALL_LATEST, 'no filter: the latest run of each issuer');
    page.libraryFilters[key] = value;
    assert.deepEqual(libIds(page).sort(), expected);
    const out = libHash(page);
    out.writeLibraryHash();
    assert.equal(new URLSearchParams(out.loc.hash.split('?')[1]).get(key), value, out.loc.hash);
    assert.ok(out.loc.hash.startsWith('#W-Library/cases?'));
    const again = libPage(), back = libHash(again, out.loc.hash);
    assert.equal(back.readLibraryHash(), true);
    assert.equal(again.libraryFilters[key], value);
    assert.deepEqual(libIds(again).sort(), expected);
  });
}
// Every sort order: the order of the rows and the address. Expected orders are written by hand from the five rows (nulls last in both directions; ties by run id).
const SORT_CASES = [
  ['name', 'asc', ['run-a', 'run-b', 'run-d', 'run-g', 'run-n']], ['name', 'desc', ['run-n', 'run-g', 'run-d', 'run-b', 'run-a']],
  ['date', 'asc', ['run-g', 'run-n', 'run-a', 'run-d', 'run-b']], ['date', 'desc', ['run-b', 'run-d', 'run-a', 'run-n', 'run-g']],
  ['leverage', 'asc', ['run-b', 'run-a', 'run-n', 'run-g', 'run-d']], ['leverage', 'desc', ['run-g', 'run-n', 'run-a', 'run-b', 'run-d']],
  ['net_leverage', 'asc', ['run-b', 'run-a', 'run-n', 'run-g', 'run-d']], ['net_leverage', 'desc', ['run-g', 'run-n', 'run-a', 'run-b', 'run-d']],
  ['coverage', 'asc', ['run-g', 'run-a', 'run-n', 'run-b', 'run-d']], ['coverage', 'desc', ['run-b', 'run-n', 'run-a', 'run-g', 'run-d']],
  ['rating', 'asc', ['run-d', 'run-b', 'run-a', 'run-n', 'run-g']], ['rating', 'desc', ['run-n', 'run-a', 'run-b', 'run-d', 'run-g']],
  ['completion', 'asc', ['run-d', 'run-a', 'run-b', 'run-g', 'run-n']], ['completion', 'desc', ['run-d', 'run-a', 'run-b', 'run-g', 'run-n']],
];
for (const [key, direction, expected] of SORT_CASES) {
  test(`library sort ${key} ${direction}: the rows come in that order and the address carries sort and dir`, () => {
    const page = libPage();
    Object.assign(page.libraryState, { sortKey: key, direction });
    assert.deepEqual(libIds(page), expected);
    const out = libHash(page);
    out.writeLibraryHash();
    const params = new URLSearchParams(out.loc.hash.split('?')[1]);
    assert.deepEqual([params.get('sort'), params.get('dir')], [key, direction]);
    // The sort control offers this order, chosen; the table's column head carries it.
    const html = page.libraryResults(page.libraryRows());
    assert.ok(html.includes(`<option value="${key}:${direction}" selected>`), 'the sort select shows the order');
    assert.ok(html.includes(`aria-sort="${direction === 'asc' ? 'ascending' : 'descending'}"><button type="button" data-library-sort="${key}">`));
    // Read back from the address.
    const again = libPage(), back = libHash(again, out.loc.hash);
    assert.equal(back.readLibraryHash(), true);
    assert.deepEqual(libIds(again), expected);
  });
}
test('library: an address written before the filter bar still reads, and the bar shows it as chosen filters; writing it back changes nothing', () => {
  const old = '#W-Library/cases?sector=Aerospace&runs=any&leverageMin=3.5&sort=leverage&dir=desc';
  const page = libPage(), io = libHash(page, old);
  assert.equal(io.readLibraryHash(), true);
  assert.deepEqual([page.libraryFilters.sector, page.libraryFilters.runs, page.libraryFilters.leverageMin, page.libraryState.sortKey, page.libraryState.direction], ['Aerospace', 'any', '3.5', 'leverage', 'desc']);
  assert.deepEqual(libIds(page), ['run-g', 'run-b0'], 'the Aerospace runs with leverage from 3.5 (run-b is 3.2), by leverage descending');
  const bar = page.libraryFacets();
  assert.ok(bar.includes('data-library-chip="sector" data-value="Aerospace" data-count="2" aria-pressed="true"') && bar.includes('data-library-chip="runs" data-value="any" data-count="2" aria-pressed="true"'));
  assert.deepEqual([...bar.matchAll(/data-library-unset="(\w+)"/g)].map(m => m[1]).sort(), ['leverageMin', 'runs', 'sector', 'sort']);
  io.writeLibraryHash();
  assert.deepEqual([...new URLSearchParams(io.loc.hash.split('?')[1])].sort(), [...new URLSearchParams(old.split('?')[1])].sort(), 'the same keys and values come back');
  // A value the bar does not offer is dropped, as before.
  const odd = libPage(), oddIo = libHash(odd, '#W-Library/cases?sector=Nope&runs=sideways');
  assert.equal(oddIo.readLibraryHash(), false);
});

test('library filter bar: every option shows the number of issuers it selects, the other filters as they stand; the number is what choosing it lists', () => {
  const page = libPage(), bar = page.libraryFacets();
  const chips = [...bar.matchAll(/data-library-chip="(\w+)" data-value="([^"]*)" data-count="(\d+)" aria-pressed="(\w+)"><span class="lf-t">(.*?)<\/span><span class="lf-n">(\d+)<\/span><span class="sr-only"> (issuers?)<\/span>/g)].map(m => ({ key: m[1], value: decode(m[2]), count: Number(m[3]), shown: Number(m[6]), word: m[7] }));
  // Written by hand from the rows: latest-run listing of five issuers.
  assert.deepEqual(chips.map(c => `${c.key}=${c.value}:${c.count}`), ['runs=latest:5', 'runs=any:5', 'sector=Aerospace:2', 'sector=Consumer:2', 'sector=Telecoms:1', 'workflow=Credit Snapshot:4', 'workflow=Short <b>&"Snap":1'.replace('Snap"', 'Snap"'), 'completion=75:1', 'completion=50:1', 'completion=100:0', 'completion=unassessed:4', 'availability=report:4', 'availability=handoff:1'].map(x => x));
  assert.ok(chips.every(c => c.shown === c.count && c.word === (c.count === 1 ? 'issuer' : 'issuers')));
  // And each is what the screen lists when it is chosen: set it, count the issuers.
  for (const c of chips) {
    const other = libPage();
    other.libraryFilters[c.key] = c.value;
    assert.equal(libIssuers(other), c.count, `${c.key}=${c.value}`);
  }
  // The other filters count: with the Aerospace sector chosen the workflow options count Aerospace issuers only.
  const aero = libPage();
  aero.libraryFilters.sector = 'Aerospace';
  const counts = Object.fromEntries([...aero.libraryFacets().matchAll(/data-library-chip="workflow" data-value="([^"]*)" data-count="(\d+)"/g)].map(m => [decode(m[1]), Number(m[2])]));
  assert.deepEqual(counts, { 'Credit Snapshot': 1, 'Short <b>&"Snap"': 1 });
  // The issuer select: one option per issuer, its count in data-count, shown only on All issuers and on an issuer the other filters exclude.
  const select = /<select id="library-issuer" data-library-filter="issuer">(.*?)<\/select>/s.exec(bar)[1];
  assert.deepEqual([...select.matchAll(/<option value="([^"]*)" data-count="(\d+)"[^>]*>(.*?)<\/option>/g)].map(m => [decode(m[1]), Number(m[2]), decode(m[3])]),
    [['', 5, 'All issuers (5)'], ['ALP', 1, 'Alpha Telecom plc'], ['BET', 1, 'Beta Aero Inc'], ['DEL', 1, 'Delta Foods'], ['GAM', 1, 'Gamma <b>&"Co"'], ['NOC', 1, 'Nocontext Ltd']]);
  assert.ok(/<option value="ALP" data-count="0">Alpha Telecom plc \(0\)<\/option>/.test(aero.libraryFacets()), 'an issuer the other filters exclude says none');
});

test('library filter bar: real controls, labelled; options are buttons with aria-pressed; chosen filters repeat in one row, each with its own clear; no filter is lost', () => {
  const page = libPage(), panel = page.libraryPanel();
  assert.ok(panel.includes('<div id="library-facets" class="lf" tabindex="-1">'));
  for (const [key, label] of [['runs', 'Runs'], ['sector', 'Sector'], ['workflow', 'Workflow'], ['availability', 'Deliverables']]) assert.ok(panel.includes(`<div class="lf-group" id="library-${key}" role="group" aria-labelledby="lf-${key}"><span class="lf-lab" id="lf-${key}">${label}</span>`), key);
  assert.ok(panel.includes('<label class="lf-group lf-select"><span class="lf-lab">Issuer</span><select id="library-issuer" data-library-filter="issuer">'));
  assert.ok(!/<select id="library-(runs|sector|workflow|availability|completion)"/.test(panel), 'the five selects are gone');
  assert.ok(!panel.includes('lf-active'), 'nothing chosen, no row of chosen filters');
  // Every option the old selects held is still reachable: through chips, the issuer select or the criteria groups.
  const reachable = key => panel.includes(`id="library-${key}"`) || panel.includes(`data-library-filter="${key}"`);
  for (const key of Object.keys(libraryDefaults())) assert.ok(reachable(key) || key === 'completion' || key === 'workflow' || key === 'availability' || key === 'runs' || key === 'sector', `${key} has a control`);
  assert.ok(panel.includes('data-library-filter="search"') && panel.includes('<button id="library-clear" class="tertiary-action" type="button" hidden>Reset filters</button>'));
  page.libraryFilters.sector = 'Aerospace';
  page.libraryFilters.leverageMin = '3.5';
  Object.assign(page.libraryState, { sortKey: 'date', direction: 'desc' });
  const row = /<div class="lf-active" role="group" aria-label="Active filters">(.*?)<\/div>/s.exec(page.libraryFacets())[1];
  assert.deepEqual([...row.matchAll(/data-library-unset="(\w+)" aria-label="([^"]*)">(.*?)<img/g)].map(m => [m[1], m[2], decode(m[3])]),
    [['sector', 'Remove filter Sector: Aerospace', 'Sector: Aerospace'], ['leverageMin', 'Remove filter Leverage, minimum: 3.5', 'Leverage, minimum: 3.5'], ['sort', 'Remove filter Sort: Evidence date, descending', 'Sort: Evidence date, descending']]);
  // Choosing a chosen option clears it; choosing another sets it; an option the filter does not offer sets nothing.
  assert.equal(page.libraryChipValue('sector', 'Aerospace'), '');
  assert.equal(page.libraryChipValue('sector', 'Consumer'), 'Consumer');
  assert.equal(page.libraryChipValue('runs', 'any'), 'any');
  page.libraryFilters.runs = 'any';
  assert.equal(page.libraryChipValue('runs', 'any'), 'latest', 'a pressed Any run goes back to the filter\'s default');
  assert.equal(page.libraryChipValue('sector', 'Nope'), null);
  assert.equal(page.libraryChipValue('leverageMin', '3'), null, 'only the bar\'s chip filters');
});

test('library: the count line is the status region and says how many issuers are listed; no match says so; nothing to list says so', () => {
  const page = libPage();
  assert.equal(page.libraryCount(page.libraryRows()), '5 issuers · 5 of 6 runs');
  assert.ok(page.libraryView().includes('<p id="library-count" role="status" aria-live="polite">5 issuers · 5 of 6 runs</p>'));
  page.libraryFilters.search = 'nothing matches this';
  assert.equal(page.libraryCount(page.libraryRows()), 'No issuers match these filters. Clear a filter to list them again.');
  const empty = page.libraryResults(page.libraryRows());
  assert.ok(empty.includes('<h2>No issuers match these filters</h2>') && empty.includes('<button id="library-empty-reset" class="primary-action" type="button">Reset filters</button>'));
  const none = runPage(d => d, [], m => m, { catalogue: [] });
  assert.equal(none.libraryCount(none.libraryRows()), 'No issuers to list.');
  const html = none.libraryResults(none.libraryRows());
  assert.ok(html.includes('class="empty-state"') && html.includes('No issuers in this library yet') && html.includes('Start a run on an issuer, then rebuild the library data file to list it here.'), 'an empty library says what to do');
});

test('library cards: one card per issuer, each with its name, ticker and sector, the latest run named by period and pathway, its state mark and first sentence, a dot per module and the links', () => {
  const page = libPage(), view = page.libraryRows(), html = page.libraryResults(view);
  const cards = html.split('<article class="lib-card"').slice(1);
  assert.equal(cards.length, 5);
  const [alpha, beta, gamma, delta, noc] = cards; // the catalogue's order of first appearance
  // Beta: two runs in the library, drawn from the later one; its declared state and first sentence are the Committee decision's.
  assert.ok(beta.includes('<h3 class="lc-name" id="lc-1">Beta Aero Inc</h3><p class="lc-meta">BET · Aerospace</p>'));
  assert.ok(beta.includes('<p class="lc-when">30 June 2025</p><span class="badge badge-gray lc-path">Full credit assessment</span><span class="state warn"><svg') && strip(beta).includes('Restricted'));
  assert.ok(beta.includes('<p class="lc-lead">Hold the position.</p>'));
  assert.deepEqual(dotLabels(beta).map(label => label), ['Source readiness: Ready', 'Downside: Not assessable', 'Committee decision: Restricted']);
  assert.ok(beta.includes('<a class="lc-open" href="#W-Overview/overview?c=run-b" aria-label="Open overview: Beta Aero Inc, 30 June 2025 · Full credit assessment">Open overview<img'));
  assert.ok(beta.includes('<a class="lc-hist" href="#W-Report/history?c=run-b" aria-label="Report history: Beta Aero Inc">2 runs</a>'));
  assert.ok(beta.includes('<button class="secondary-action lc-details" type="button" data-library-select="1" aria-expanded="false" aria-controls="run-detail" aria-label="Details: Beta Aero Inc, 30 June 2025 · Full credit assessment">Details</button>'));
  // Alpha: a lead with no declared state has no badge; its first sentence still shows.
  assert.ok(alpha.includes('<p class="lc-lead">Hold the position.</p>') && !alpha.includes('class="state'), 'a missing declared state draws no badge');
  assert.deepEqual(dotLabels(alpha), ['Financial foundation', 'Committee decision']);
  // Delta: one module, no lead. Gamma: no module. Nocontext: no run page at all, so no overview link and no dots.
  assert.deepEqual(dotLabels(delta), ['Source readiness']);
  assert.ok(gamma.includes('<p class="lc-none">No module output is retained for this run.</p>') && !gamma.includes('mdots'));
  assert.ok(noc.includes('<p class="lc-none">No run page is held for this issuer.</p>') && !noc.includes('lc-open') && !noc.includes('lc-hist'));
  assert.ok(noc.includes('data-library-select="4"'), 'its details are still reachable');
  // The grid is one container; a card is not nested in another.
  assert.equal(countOf(html, /<div class="lib-grid">/g), 1);
});

test('library cards: the module names of a run appear once, as dot labels, and not as a text list', () => {
  const page = libPage(), html = page.libraryView();
  const card = html.split('<article class="lib-card"').slice(1)[1];
  for (const title of ['Source readiness', 'Downside', 'Committee decision']) {
    assert.equal(dotLabels(card).filter(label => label.split(': ')[0] === title).length, 1, `${title} is one dot label`);
    assert.ok(!strip(card).includes(title), `${title} is not text of the card`);
    assert.ok(!html.slice(html.indexOf('data-pane="list"')).includes(`>${title}<`), `${title} is not in the list view either`);
  }
  assert.ok(!/<li>[^<]*(?:Source readiness|Downside|Committee decision)/.test(html), 'no text list of module names');
  const history = libPage().historyView('run-b');
  assert.equal(dotLabels(history).filter(label => label.startsWith('Source readiness')).length, 1 + 1, 'in the history each run\'s dot strip names it once (run-b and run-b0 each hold it)');
});

test('library: the cards and the list are two panes of one block with the shared toggle; List keeps the table, its columns and its sort heads; the Run column is the run name', () => {
  const page = libPage(), html = page.libraryResults(page.libraryRows());
  assert.ok(html.includes('<div class="lib-block" data-block data-view="cards">') && html.includes('<div class="seg" data-i="0" role="group" aria-label="Issuers as cards or as a list">'));
  assert.ok(html.includes('<div data-pane="cards">') && html.includes('<div data-pane="list" hidden>'));
  const list = page.libraryResults(page.libraryRows(), 'list');
  assert.ok(list.includes('data-view="list"') && list.includes('<div data-pane="cards" hidden>') && list.includes('<div data-pane="list">') && list.includes('data-view-pick="list" aria-pressed="true"'));
  assert.deepEqual([...html.matchAll(/<th scope="col"[^>]*>(?:<button[^>]*>)?([^<]*?)(?: <span|<\/)/g)].map(m => m[1].trim()), ['Issuer', 'Run', 'Sector', 'Evidence date', 'Leverage', 'Net leverage', 'Coverage', 'Rating', 'Completeness', 'Open']);
  const rows = [...html.matchAll(/<tr[^>]*>(.*?)<\/tr>/gs)].filter(m => m[1].includes('<td')).map(m => [...m[1].matchAll(/<td[^>]*>(.*?)<\/td>/gs)].map(c => decode(strip(c[1]))));
  assert.equal(rows.length, 5);
  assert.equal(rows[1][1], '30 June 2025 · Full credit assessment', 'the Run column names the run by period and pathway');
  assert.equal(rows[4][1], '28 February 2025 · Credit Snapshot', 'a run the store does not hold keeps its catalogue date and workflow');
  assert.ok(!html.includes('run-id'), 'no run id column');
  // Two runs of one issuer with one name (Any run lists both of Beta\'s: the same period would name both alike) are told apart by a fixed word.
  assert.deepEqual(page.sameNameWords([{ group: 'bet', name: 'A', date: '2025-06-30' }, { group: 'bet', name: 'A', date: '2025-03-31' }, { group: 'bet', name: 'B', date: '2025-01-01' }, { group: 'alp', name: 'A', date: '2025-01-01' }]), ['Latest', 'Earlier', '', '']);
  assert.deepEqual(page.sameNameWords([{ group: 'bet', name: 'A', date: '2025-03-31' }, { group: 'bet', name: 'A', date: '2025-06-30' }]), ['Earlier', 'Latest']);
});

test('library home: no calculation ID, run code, run folder, delivery id, file name, hash or method code in its text or its attributes (every control, options included)', () => {
  const page = libPage({ activity: { updated: 'T', runs: [{ id: 'r1', status: 'running', issuer_name: 'Northbridge', folder: LIB_CODE, pathway: 'credit_snapshot', submitted_by: 'ann', spent: 'USD 3.10', modules: [['CP-0', 'done'], ['CP-1', 'running']] }] } });
  for (const view of ['cards', 'list']) {
    const html = page.libraryView().replace(/<div data-pane="(cards|list)"/g, (m, pane) => (pane === view ? m : `${m} hidden`));
    const withoutBasis = html;
    assert.ok(!html.includes('library-basis'), 'the Leverage basis filter is gone: basis text is calculation material and Evidence\'s');
    const attrs = [...withoutBasis.matchAll(/\s([\w-]+)="([^"]*)"/g)].filter(m => m[1] !== 'href').map(m => decode(m[2]));
    const text = decode(strip(withoutBasis)).replace(/&#39;/g, "'");
    for (const [name, found] of [['text', text], ['attributes', attrs.join('\n')]]) {
      for (const [what, bad] of [['calculation ID', /\b[Cc]alculations? [A-Z]{1,2}\d{2}\b/], ['run code', new RegExp(LIB_CODE, 'i')], ['run folder', /run-[abdgn]0?\b(?!\s*Open)/], ['delivery id', /\b[0-9a-f]{64}\b/], ['file name', /\.(?:jsonl|html?|md|pdf|xlsx?)\b/], ['method code', /\bT\d[A-Z]?\.\d/], ['module code', /\bCP-[0-9A-Z]+\b/], ['Basis:', /Basis:/], ['**', /\*\*/], ['cost', /USD 3\.10/]]) assert.ok(!bad.test(found), `${view} ${name}: ${what}: ${bad.exec(found)?.[0]}`);
    }
  }
  // The detail panel is the other place the old page drew them: the ratio basis (with its calculation ID) is Evidence's, so the panel shows the period and links to Evidence.
  const detail = page.libraryDetail(page.libraryRows());
  assert.ok(!/\(calculation|calculations C|C11/.test(detail) && detail.includes('<p>FY2024</p>') && detail.includes('Sources, definitions and calculations in Evidence'));
  const detailText = decode(strip(detail)) + [...detail.matchAll(/\s([\w-]+)="([^"]*)"/g)].filter(m => m[1] !== 'href').map(m => decode(m[2])).join('\n'); // a route's own address carries the model's key by design
  assert.ok(!detailText.includes(LIB_HASH) && !detailText.includes(LIB_CODE) && !detail.includes('data-library-source') && !detail.includes('metric-sources'), 'the delivery id is never a name');
  assert.ok(detail.includes('>Forecast</a>') || detail.includes('<span>Forecast</span>') || detail.includes('Delivered report'), 'a model is named by its label, not by its delivery folder');
  const cells = page.libraryResults(page.libraryRows());
  assert.ok(!/title="[^"]*(?:calculation|C11)/.test(cells) && cells.includes('title="FY2024"'));
});

test('library home: markup characters in an issuer, sector or workflow name are escaped everywhere they are drawn', () => {
  const page = libPage();
  page.libraryFilters.workflow = 'Short <b>&"Snap"';
  const html = page.libraryView();
  assert.ok(!html.includes('<b>&"') && !/<b>/.test(html.replace(/<b>/g, (m, at) => (html.slice(at - 1, at) === '' ? m : m)).replace(/&lt;b&gt;/g, '')), 'no raw <b> from a name');
  assert.ok(html.includes('Gamma &lt;b&gt;&amp;&quot;Co&quot;') && html.includes('Short &lt;b&gt;&amp;&quot;Snap&quot;'));
  assert.ok(html.includes('data-value="Short &lt;b&gt;&amp;&quot;Snap&quot;"') && html.includes('data-library-unset="workflow" aria-label="Remove filter Workflow: Short &lt;b&gt;&amp;&quot;Snap&quot;"'));
  assert.ok(html.includes('aria-label="Details: Gamma &lt;b&gt;&amp;&quot;Co&quot;, 31 January 2025 · Short snapshot"') || html.includes('aria-label="Details: Gamma &lt;b&gt;&amp;&quot;Co&quot;'), 'the card labels are escaped');
});

// The text of the stylesheet's `@media (prefers-reduced-motion:no-preference){...}` block, found by matching braces.
const reducedMotionBlock = css => {
  const open = css.indexOf('@media (prefers-reduced-motion:no-preference){');
  assert.ok(open >= 0, 'the no-preference media query exists');
  let depth = 0, at = css.indexOf('{', open);
  for (let i = at; i < css.length; i += 1) { if (css[i] === '{') depth += 1; if (css[i] === '}') { depth -= 1; if (depth === 0) return { block: css.slice(open, i + 1), rest: css.slice(0, open) + css.slice(i + 1) }; } }
  throw new Error('unbalanced');
};
const LIVE = { updated: 'T', cap: '20', runs: [
  { id: 'r1', status: 'running', issuer_name: 'Northbridge <Synthetic> & Co', folder: 'nb-run-folder', pathway: 'credit_snapshot', submitted_by: 'ann', spent: 'USD 3.10', modules: [['CP-0', 'done'], ['CP-1', 'running'], ['CP-2A', 'waiting'], ['CP-6', 'waiting']] },
  { id: 'r2', status: 'queued', issuer_name: 'Waiting Ltd', modules: [['CP-0', 'waiting']] }, { id: 'r3', status: 'finished', issuer_name: 'Done Ltd' }, null, 'junk'] };

test('library home: a running run is a row with the C31 mark and the C13 steps: which module is running and how many are done of how many; no cost, no folder, no submitter; a waiting run shows its mark only; finished runs are not drawn', () => {
  const html = libPage({ activity: LIVE }).libraryLive();
  assert.equal(countOf(html, /<li class="live-row">/g), 2, 'the running run and the waiting one');
  assert.ok(html.startsWith('<section class="lib-live" aria-labelledby="lib-live-h"><h2 class="eyebrow lib-eyebrow" id="lib-live-h">Running now</h2>'));
  assert.ok(html.includes('<strong class="lv-name">Northbridge &lt;Synthetic&gt; &amp; Co</strong><span class="lv-pathway">Full credit assessment</span>'));
  assert.ok(html.includes('<span class="state new rmark running"><span class="lat" aria-hidden="true">') && html.includes('<span class="state-w">Running</span>'), 'the mark has its word');
  assert.deepEqual([...html.matchAll(/<li class="step (\w+)" data-tip="([^"]*)"/g)].map(m => [m[1], m[2]]), [['done', 'Source readiness: done'], ['running', 'Financial foundation: running'], ['waiting', 'Downside: waiting'], ['waiting', 'Committee decision: waiting']]);
  assert.ok(html.includes('<span class="steps-k">Running</span> Financial foundation') && html.includes('<span class="steps-n">1 of 4 done</span>'));
  for (const gone of ['USD 3.10', 'nb-run-folder', 'ann', 'Done Ltd', 'CP-']) assert.ok(!html.includes(gone), gone);
  assert.ok(html.includes('Waiting Ltd') && html.includes('<span class="state same rmark queued">'));
  assert.ok(libPage({ activity: { updated: 'T', runs: [{ status: 'running', modules: [['CP-1', 'running']], stalled: true }] } }).libraryLive().includes('<span class="state-w">Stalled</span>'));
  // Nothing running, nothing malformed: nothing drawn. A run with no name or no module list still draws its mark.
  for (const activity of [undefined, null, 'x', [], { runs: 'x' }, { runs: [] }, { runs: [{ status: 'finished' }] }]) assert.equal(libPage({ activity }).libraryLive(), '', JSON.stringify(activity));
  const bare = libPage({ activity: { runs: [{ status: 'running' }] } }).libraryLive();
  assert.ok(bare.includes('Run in progress') && bare.includes('Running</span>') && !bare.includes('steps-w'));
  // The heading says what the row holds: Running now when a run is running, Waiting when only queued runs are.
  const waitingOnly = libPage({ activity: { updated: 'T', runs: [{ id: 'q1', status: 'queued', issuer_name: 'Qone' }] } }).libraryLive();
  assert.ok(waitingOnly.includes('id="lib-live-h">Waiting</h2>') && !waitingOnly.includes('Running now'));
  // It leads the page, before the filter bar.
  const view = libPage({ activity: LIVE }).libraryView();
  assert.ok(view.indexOf('lib-live') > 0 && view.indexOf('lib-live') < view.indexOf('id="library-filters"'));
});

test('A20: the previous-running set is seeded at page start only when the opening route draws live runs (Run activity or the library home)', () => {
  const screen = read('screen.js'), line = /^if\(current\.module==='CP-OS'\|\|current\.module==='W-Library'\)previousRunning=.*$/m.exec(screen);
  assert.ok(line, 'the seed is guarded by the opening route');
  const seed = module => {
    const state = { current: { module }, previousRunning: null };
    new Function('current', 'activityEnded', 'window', 'state', `let previousRunning=state.previousRunning;${line[0]};state.previousRunning=previousRunning;`)(state.current, () => ({ running: [{ id: 'x', name: 'Xray' }] }), { RUN_ACTIVITY: {} }, state);
    return state.previousRunning;
  };
  assert.deepEqual(seed('CP-OS'), [{ id: 'x', name: 'Xray' }]);
  assert.deepEqual(seed('W-Library'), [{ id: 'x', name: 'Xray' }]);
  assert.strictEqual(seed('W-Reports'), null, 'another route draws no run, so none is seeded');
  assert.strictEqual(seed('CP-1'), null);
});

test('library home: the live row moves only in the stylesheet\'s no-preference media query; the state is still clear from icon and word when it does not, and nothing moves in print', () => {
  const css = read('screen.css'), { block, rest } = reducedMotionBlock(css);
  assert.ok(block.includes('.step.running{animation:step-pulse') && block.includes('@keyframes step-pulse') && block.includes('.rmark.running .lat i{animation:lat-orbit') && block.includes('@keyframes lat-orbit'));
  assert.ok(!/step-pulse|lat-orbit/.test(rest), 'no animation of the live row outside the media query');
  assert.ok(/@media print\{[^@]*\.step\.running,\.lat i\{animation:none\}/.test(css), 'print: nothing moves');
  assert.ok(!/animation[^;}]*infinite/.test(rest.slice(rest.indexOf('/* Library home and report history'))), 'no looping animation of the library pages outside the media query');
  assert.ok(css.includes('.step.running{height:12px;background:var(--blue)}') && css.includes('.lat i:nth-child(1){opacity:1}'), 'a static loader and a taller running segment: the state does not depend on motion');
});

test('library detail: the issuer\'s figure strip is the Overview\'s, by the same rule, with the same figures; no trace controls; links to that run; none when the Bottom line names no row', () => {
  const page = libPage(), view = page.libraryRows();
  page.libraryState.selected = RUN;
  const detail = page.libraryDetail(view);
  const strip4 = detail.slice(detail.indexOf('<div class="strip"'), detail.indexOf('</div></div><div class="detail-layout">'));
  assert.deepEqual([...strip4.matchAll(/<a class="strip-k"[^>]*>(.*?)<\/a>/g)].map(m => m[1]), ['Net leverage', 'Interest cover', 'Free cash flow']);
  assert.deepEqual([...strip4.matchAll(/<p class="strip-v">(.*?)<\/p>/g)].map(m => m[1]), ['6.01x', '2.1x', 'USD 1,100 million']);
  assert.ok(strip4.includes('<p class="strip-b">FY2023 6.40x</p>') && /<a class="strip-k" href="#CP-1\/[^"]*c=run-a[^"]*"/.test(strip4), 'it links to the module of this run');
  assert.ok(!strip4.includes('data-basis') && !strip4.includes('trace'), 'no trace control: there is no run page to open it on');
  const overview = realHtml(), overviewStrip = overview.slice(overview.indexOf('<div class="strip"'), overview.indexOf('</div></div></div></section>', overview.indexOf('<div class="strip"')));
  const figures = html => [...html.matchAll(/<p class="strip-(?:v|b)">(.*?)<\/p>/g)].map(m => m[1]);
  assert.deepEqual(figures(strip4), figures(overviewStrip), 'the Overview draws the same figures');
  assert.ok(detail.indexOf('class="lib-strip"') > detail.indexOf('<div class="detail-head">') && detail.indexOf('class="lib-strip"') < detail.indexOf('<div class="detail-layout">'));
  // No match, no strip; a run the store does not hold, none.
  page.libraryState.selected = 'run-b';
  assert.ok(!page.libraryDetail(view).includes('lib-strip'));
  page.libraryState.selected = 'run-n';
  assert.ok(!page.libraryDetail(view).includes('lib-strip') && !page.libraryDetail(view).includes('Sources, definitions and calculations in Evidence'), 'no run page, no Evidence link');
  assert.ok(page.libraryDetail(view).includes('<h2>Nocontext Ltd</h2>'));
});

test('library home: the card view shows the details panel only once an issuer\'s Details was used; the list view always shows it; the cards print and the controls do not', () => {
  const css = read('screen.css');
  assert.ok(css.includes('.library-main:has([data-block][data-view="cards"]) #run-detail:not([data-chosen]){display:none}'));
  assert.ok(/@media print\{[^@]*\.lib-block \[data-pane=list\]\{display:none!important\}\.lib-block \[data-pane=cards\]\[hidden\]\{display:block!important\}/.test(css) && /@media print\{[^@]*\.lf,\.search-row,\.lib-sort,\.lib-block \.seg/.test(css));
  const view = libPage().libraryView();
  assert.ok(view.includes('<section id="run-detail" class="run-detail" aria-label="Selected issuer details" tabindex="-1" >'));
  assert.equal(countOf(view, /<h1/g), 0, 'the page header holds the one h1');
  assert.ok(view.includes('<h2 class="sr-only">Issuers</h2>'));
  assert.deepEqual([...view.matchAll(/<h([1-6])[ >]/g)].map(m => Number(m[1])).filter((n, i, all) => i === 0 || n - all[i - 1] <= 1), [...view.matchAll(/<h([1-6])[ >]/g)].map(m => Number(m[1])), 'headings go down one level at a time');
});

test('library home: markup for a very long name wraps inside its card and a badge never wraps inside; one grid, no side accent, only tokens', () => {
  const css = read('screen.css'), mine = css.slice(css.indexOf('/* Library home and report history')).replace(/\/\*.*?\*\//gs, '');
  assert.ok(/\.lc-name\{[^}]*overflow-wrap:anywhere/.test(mine) && /\.lf-t\{[^}]*overflow-wrap:anywhere/.test(mine) && /\.lf-n\{flex:none/.test(mine) && /\.lib-card\{[^}]*min-width:0/.test(mine));
  assert.ok(/\.lib-grid\{display:grid;grid-template-columns:repeat\(auto-fill,minmax\(min\(100%,300px\),1fr\)\)/.test(mine), 'cards are one continuous responsive grid');
  assert.ok(!/border-left|border-inline-start/.test(mine), 'no side accent');
  assert.ok(!/#[0-9a-fA-F]{3,8}\b/.test(mine.replace(/@media[^{]*\{/g, '')), 'colours are tokens (or system colours), never literals');
  assert.ok(!/class="eyebrow"/.test(read('views.js')) && !/class="eyebrow"/.test(read('screen.js')));
});

test('library home: the page names no run by code in any state: an issuer with no run page, a run with no modules and one with a missing state draw by name', () => {
  const page = libPage();
  const html = page.libraryView();
  const text = decode(strip(html));
  for (const code of [LIB_CODE, 'RUN-B-CODE', 'RUN-B0-CODE', 'RUN-G-CODE', 'RUN-D-CODE']) assert.ok(!text.includes(code), code);
  const attrs = [...html.matchAll(/\s([\w-]+)="([^"]*)"/g)].filter(m => m[1] !== 'href').map(m => m[2]).join('\n');
  for (const code of [LIB_CODE, 'RUN-B-CODE', 'run-b0']) assert.ok(!attrs.includes(code), code);
});

test('report history: no run code, folder, delivery id, calculation ID or module code in its text or its attributes', () => {
  const page = libPage();
  for (const context of [RUN, 'run-b']) {
    const html = page.historyView(context), attrs = [...html.matchAll(/\s([\w-]+)="([^"]*)"/g)].filter(m => m[1] !== 'href').map(m => decode(m[2])).join('\n'), text = decode(strip(html));
    for (const found of [text, attrs]) for (const bad of [new RegExp(LIB_CODE, 'i'), /RUN-B0?-CODE/i, /\b[0-9a-f]{64}\b/, /\b[Cc]alculations? [A-Z]{1,2}\d{2}\b/, /\bCP-[0-9A-Z]+\b/, /\.(?:jsonl|html?|md)\b/]) assert.ok(!bad.test(found), `${context}: ${bad}`);
  }
  // Run B has two runs on the same date and pathway only in name terms: they are 30 June 2025 and 30 June 2024, so no word is needed.
  const [latest, earlier] = histRows(page.historyView('run-b'));
  assert.deepEqual([strip(latest.date), strip(earlier.date)], ['30 June 2025', '30 June 2024']);
  assert.ok(!/Latest|Earlier(?! format| methods)/.test(strip(latest.marks) + strip(earlier.marks)), 'two different names need no word');
  const recorded = { first_run: false, pack: { prior: { run: 'x', as_of: '2024-01-01', pathway: 'credit_snapshot' }, measures: [] } };
  const [withRecord, withoutRecord] = histRows(libPage({ contexts: { ...libBase().contexts, 'run-b': { ...libBase().contexts['run-b'], changes: recorded } } }).historyView('run-b'));
  assert.ok(withRecord.links.includes('What changed') && !withoutRecord.links.includes('What changed'), 'only the run whose record holds a comparison has a What changed link');
  assert.ok(!latest.links.includes('What changed') && !earlier.links.includes('What changed'), 'a run that records no comparison has none, though an earlier run of its pathway is listed');
});

// ---- Task 10 fix round 2.
test('N1: a Forecast card holds back any issuer document name in a footnote (docx, pptx, xml, xhtml)', () => {
  for (const name of ['lender-notes.docx', 'q3_deck.pptx', 'filing.xml', 'annual-report.xhtml']) {
    const sections = fcSections();
    sections[2].blocks.find(b => b.type === 'table').rows[1].cells[3] = `Schedule; ${name}, page 4`;
    assert.ok(!cardOf(fcPage({ sections }).forecastCharts(RUN), 'Debt maturities').includes(name), name);
  }
});

test('L3: the run\'s own id values (every module of the run) are held back in a card; other id-shaped words are drawn', () => {
  const sections = fcSections();
  sections[2].blocks.find(b => b.type === 'table').rows[1].cells[3] = 'EU27 sales and V03 case';
  const other = runOutput('CP-X', { sections: [sec('Scenarios', 3, 10, 'consumed', [table(12, ['Scenario id', 'Name'], [[13, 'V03', 'Base']])])], state: { established: true, declared: null }, summary: null, words: {} });
  const page = runPage(() => ({ [outId('CP-1')]: fcOutput({ sections }), [outId('CP-X')]: other }), [], m => m, { record: steps(['CP-1', 'CP-X']), runFields: { asOf: '2025-03-31' } });
  const maturities = cardOf(page.forecastCharts(RUN), 'Debt maturities');
  const note = /<div class="fc-note">.*?<\/div>/s.exec(maturities);
  assert.ok(!note || !/V03|EU27/.test(note[0]) , 'the whole text is held (it holds the run\'s id V03)');
  sections[2].blocks.find(b => b.type === 'table').rows[1].cells[3] = 'EU27 sales';
  assert.ok(cardOf(fcPage({ sections }).forecastCharts(RUN), 'Debt maturities').includes('EU27 sales'));
});

test('L1: a held-back chart title is not drawn anywhere on its card; the trace control and the card name fall back to "Chart n"', () => {
  for (const t of ['Interest cover per K_10.htm.jsonl', 'Interest cover SC2']) {
    const charts = fcOutput().charts.map((c, i) => (i === 0 ? { ...c, title: t } : c));
    const card = fcCards(fcPage({ charts }).forecastCharts(RUN))[0];
    assert.ok(!/K_10|SC2/.test(card), t);
    assert.ok(/aria-label="Chart 1: where it comes from"/.test(card) && /<article class="fc-card"[^>]*aria-label="Chart 1"/.test(card) && card.includes('<h3>Chart 1</h3>'));
  }
});

test('L2: an absence marker always has its sentence: an empty cell draws none; a held-back absence draws the marker and one In Evidence line', () => {
  const revenueWith = value => { const sections = fcSections(); sections[1].blocks.find(b => b.type === 'table').rows[0].cells[2] = value; const card = cardOf(fcPage({ sections }).forecastCharts(RUN), 'Revenue and EBITDA'); const fig = card.split('data-pane="table"')[0]; return { marks: countOf(fig.split('class="fc-absent"')[0], /class="absent-mark"/g), lines: ((fig.match(/<ul class="fc-absent">[\s\S]*?<\/ul>/) || [''])[0].match(/<li>/g) || []).length, fig }; };
  assert.deepEqual([revenueWith('').marks, revenueWith('').lines], [0, 0]);
  const held = revenueWith('Not supplied: split in K_10.htm.jsonl');
  assert.deepEqual([held.marks, held.lines], [1, 1]);
  assert.ok(held.fig.includes('class="in-ev"') && !held.fig.includes('jsonl'));
  const drawn = revenueWith('Not supplied: split not read');
  assert.deepEqual([drawn.marks, drawn.lines], [1, 1]);
});

test('Info: a held-back bridge label leaves no empty list item; the module-page bridge prints each category once; two models are told apart by run name', () => {
  const sections = [...passageSections({ bottom: 'Cash is up.' })];
  const page = runPage(d => { withBridge(d); d[outId('CP-1')].sections.unshift(...sections); const rows = d[outId('CP-1')].sections.flatMap(s => s.blocks).find(b => b.line === 62).rows; rows[1].cells[0] = 'Free cash flow K_10.htm.jsonl'; return d; }, [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' } });
  const card = cardOf(page.forecastCharts(RUN), 'Liquidity bridge');
  assert.ok(!/<li><span class="bridge-n">\d+<\/span><span><\/span><\/li>/.test(card) && !card.includes('<span></span>'));
  const module = page.readerChart(outId('CP-1'), BRIDGE_CHART, false, true, true), visible = strip(module.replace(/<title>.*?<\/title>/g, ''));
  assert.equal(countOf(visible, /Opening accessible liquidity/g), 1, 'once on the module page');
  const mk = id => pickModel(id, { mode: 'candidate', download: '../d/m.html', href: '../d/m.html', cashflow: { units: 'U', columns: gridColumns, notes: [], limits: ['One limit.'], rows: [gridRow('Revenue', 'Revenue', false, [cell('value', '1'), cell('value', '2')])], other: null } });
  const two = fcPage(undefined, { models: [mk(HASH_1), mk(HASH_2)], runFields: { ...PICK_RUNS, evidence: EVIDENCE } }).evidenceInput(RUN);
  const heads = [...window_Evidence().view(two, { tab: 'gaps', module: null }).matchAll(/<div class="ev-grp-h"><span>([^<]*)<\/span><span class="ev-cd">Model scope limits/g)].map(m => m[1]);
  assert.equal(new Set(heads).size, 2, heads.join(' | '));
  assert.ok(heads.every(h => h.includes('31 March 2025 · Full credit assessment')), heads.join(' | '));
});

test('L3 consequence: calculation ids that are id values of the run (as on every real run) are held in a title and a footnote even without the word "calculation"', () => {
  const sections = fcSections();
  sections[2].blocks.find(b => b.type === 'table').rows[1].cells[3] = 'Calculated as C05';
  const calcs = runOutput('CP-X', { sections: [sec('Calculations', 2, 5, 'consumed', [table(6, ['Calculation ID', 'Result'], [[7, 'C05', '1'], [8, 'C48', '2']])])], state: { established: true, declared: null }, summary: null, words: {} });
  const charts = fcOutput().charts.map((c, i) => (i === 0 ? { ...c, title: 'Interest cover C48' } : c));
  const page = runPage(() => ({ [outId('CP-1')]: fcOutput({ sections, charts }), [outId('CP-X')]: calcs }), [], m => m, { record: steps(['CP-1', 'CP-X']), runFields: { asOf: '2025-03-31' } });
  const html = page.forecastCharts(RUN);
  assert.ok(!html.includes('C48') && !html.includes('C05'));
});

// ---- Task 10 fix round 3: one construction point for the strict context (views.js strictContext), keyed on the run.
const calcsOutput = rows => runOutput('CP-X', { sections: [sec('Calculations', 2, 5, 'consumed', [table(6, ['Calculation ID', 'Result'], rows)])], state: { established: true, declared: null }, summary: null, words: {} });

test('R3-1: the Forecast page register and limitation lines hold back the run\'s id values, with or without a forecast source', () => {
  const sourced = [{ role: 'forecast', output: outId('CP-1'), run: RUN, path: `runs/${RUN}/x/forecast.md`, sha256: HASH_2, changed: false }];
  for (const sources of [[], sourced]) {
    const model = pickModel(HASH_1, {
      mode: 'candidate', download: '../d/m.html', href: '../d/m.html', sources,
      register: { heading: 'Register', intro: null, headers: ['assumption_id', 'driver', 'rationale'], rows: [['A-01', 'margin', 'FY2024 margin carried (C21); upside inherits'], ['A-02', 'margin', 'FY2023 margin (C22)'], ['A-03', 'growth', 'Fade from 16.2%']] },
      cashflow: { units: 'USD m', columns: gridColumns, notes: [], limits: ['Margin held at C22.', 'Every figure is arithmetic.'], rows: [gridRow('Revenue', 'Revenue', false, [cell('value', '1'), cell('value', '2')])], other: null },
    });
    const page = runPage(() => ({ [outId('CP-1')]: fcOutput(), [outId('CP-X')]: calcsOutput([[7, 'C21', '1'], [8, 'C22', '2']]) }), [], m => m, { record: steps(['CP-1', 'CP-X']), runFields: PICK_RUNS, models: [model] });
    const html = page.forecastView(RUN, HASH_1), below = html.slice(html.indexOf('<div class="report-tools'));
    const label = `sources=${sources.length}`;
    assert.ok(!/\bC2[12]\b/.test(strip(below)), `${label}: an id value of the run is drawn`);
    const register = /<details[\s\S]*?<\/details>/.exec(below)?.[0] ?? '';
    assert.ok(strip(register).includes('Fade from 16.2%') && register.includes('class="in-ev"'), label);
    assert.ok(strip(below).includes('Every figure is arithmetic.') && strip(below).includes('1 further limitation is stated in Evidence'), label);
  }
});

test('R3-2: a module code is drawn in a card note even when it is an id value of the run; a scenario id is held', () => {
  const sections = fcSections(), rows = sections[2].blocks.find(b => b.type === 'table').rows;
  rows[1].cells[3] = 'Revenue as CP-1 states it'; rows[2].cells[3] = 'Per the V03 case';
  const other = runOutput('CP-X', { sections: [sec('Modules', 3, 10, 'consumed', [table(12, ['Module id', 'Scenario id', 'Role'], [[13, 'CP-1', 'V03', 'Upstream']])])], state: { established: true, declared: null }, summary: null, words: {} });
  const page = runPage(() => ({ [outId('CP-1')]: fcOutput({ sections }), [outId('CP-X')]: other }), [], m => m, { record: steps(['CP-1', 'CP-X']), runFields: { asOf: '2025-03-31' } });
  const note = /<div class="fc-note">.*?<\/div>/s.exec(cardOf(page.forecastCharts(RUN), 'Debt maturities'))?.[0] ?? '';
  assert.ok(strip(note).includes('Revenue as CP-1 states it'), note);
  assert.ok(!note.includes('V03'), note);
});

test('R3-3: the run\'s id values are the union over every module of the run, whichever module asks; no context of the run is needed', () => {
  const tables = (code, header, id) => runOutput(code, { run: 'run-z', sections: [sec('Ids', 3, 10, 'consumed', [table(12, [header, 'Name'], [[13, id, 'x']])])], state: { established: true, declared: null }, summary: null, words: {} });
  const z = code => `run-z/deliveries/d1/${code}.md`;
  const page = runPage(d => d, [], m => m, { data: { [z('CP-1')]: tables('CP-1', 'Scenario id', 'V03'), [z('CP-2A')]: tables('CP-2A', 'Scenario id', 'W04') } });
  // The second argument is the a19b8d6 signature (the asking output); the function ignores it now.
  for (const code of ['CP-1', 'CP-2A']) assert.deepEqual([...page.runTokens('run-z', z(code))].sort(), ['V03', 'W04'], code);
});

test('R3-4: the strict context has one construction point', () => {
  assert.equal(countOf(read('views.js'), /\bstrict:true\b/g), 1);
});

test('R3-5: the library limitation options read against the run when its context is loaded, and still draw when it is not', () => {
  assert.deepEqual([...runPage().runTokens(null)], [], 'no run: no tokens');
  const catalogue = [
    { id: RUN, checklist: null, gaps: ['Margin held at C22.', 'Every figure is arithmetic.'] },
    { id: 'unloaded-folder', checklist: null, gaps: ['No covenant data supplied.'] },
  ];
  const page = runPage(() => ({ [outId('CP-X')]: calcsOutput([[7, 'C21', '1'], [8, 'C22', '2']]) }), [], m => m, { record: steps(['CP-X']), catalogue });
  const options = page.libraryChoices().limitation.map(([value]) => value);
  assert.ok(options.includes('Every figure is arithmetic.') && options.includes('No covenant data supplied.'), options.join(' | '));
  assert.ok(!options.includes('Margin held at C22.'), options.join(' | '));
});

// ======== Task 11, fix round 1 ========
const startedRecord = at => ({ steps: [{ module: 'CP-0', started: at, accepted: null }], edges: [], timed: true });
const compared = (asOf = '2024-01-01') => ({ lead: 'CP-2', first_run: false, pack: { prior: { run: 'x', as_of: asOf, pathway: 'credit_snapshot' }, measures: [] } });

test('M1 history: What changed is drawn when the run\'s own record holds a comparison (the Changes page\'s condition) and only then; a recorded first run, and a run that records nothing, have none whatever else is listed', () => {
  const base = libBase();
  const page = changes => libPage({ contexts: { ...base.contexts, ...Object.fromEntries(Object.entries(changes).map(([k, c]) => [k, { ...base.contexts[k], changes: c }])) } });
  const links = (p, ctx) => histRows(p.historyView(ctx)).map(r => r.links.includes('What changed'));
  // run-b0 is the oldest run of BET and the only one of its pathway before run-b; its own record says it was compared with a run the library does not list.
  assert.deepEqual(links(page({ 'run-b0': compared() }), 'run-b'), [false, true]); // each run by its own record: run-b records nothing
  // A run whose record says it is a first run has no link, even with an earlier listed run of its pathway.
  assert.deepEqual(links(page({ 'run-b': { first_run: true } }), 'run-b'), [false, false]);
  // A run that records nothing is not a first run (absence is not read as one), but the Changes page would only say "No comparison recorded": no link, with or without an earlier listed run of its pathway (review L7).
  assert.deepEqual(links(page({}), 'run-b'), [false, false]);
  // A pack that could not be read, or a note that none was produced, still say a comparison was meant: the Changes page explains it.
  assert.deepEqual(links(page({ 'run-b0': { first_run: false, note: 'changes: not produced — no prior' } }), 'run-b'), [false, true]);
  assert.deepEqual(links(page({ 'run-b0': { problem: 'unreadable' } }), 'run-b'), [false, true]);
});

test('M2 list: Latest/Earlier is decided by as-of date, then run start, never by row order, and agrees with the history', () => {
  const words = items => libPage().sameNameWords(items);
  const it = (id, date, started) => ({ id, group: 'bet', name: 'N', date, started });
  assert.deepEqual(words([it('a', '2025-06-30', '2025-07-01T09:00:00Z'), it('b', '2025-06-30', '2025-07-05T09:00:00Z')]), ['Earlier', 'Latest'], 'the later start is the later run');
  assert.deepEqual(words([it('b', '2025-06-30', '2025-07-05T09:00:00Z'), it('a', '2025-06-30', '2025-07-01T09:00:00Z')]), ['Latest', 'Earlier'], 'whatever the row order');
  assert.deepEqual(words([it('a', '2025-07-30', null), it('b', '2025-06-30', '2025-07-05T09:00:00Z')]), ['Latest', 'Earlier'], 'the date first');
  assert.deepEqual(words([it('a', '2025-06-30', null), it('b', '2025-06-30', '2025-07-05T09:00:00Z')]), ['Earlier', 'Latest'], 'a run with no start is the older');
  assert.deepEqual(words([it('b', '2025-06-30', null), it('a', '2025-06-30', null)]), ['Earlier', 'Latest'], 'all equal: the folder order the history uses (the smaller folder is listed first, so is Latest)');
  // Through the page: both sort directions give each run the same word, and the history gives the same.
  const base = libBase(), cat = libCatalogue();
  cat.push(zedRun({ id: 'run-b1', issuer: 'BET', name: 'Beta Aero Inc', sector: 'Aerospace', workflow: 'Credit Snapshot', date: '2025-06-30', metrics: { leverage: libMetric('9.9') } }));
  const b1 = [libOut('run-b1', 'CP-0', 'Sources are ready again.', 'Ready')];
  const contexts = { ...base.contexts, 'run-b': { ...base.contexts['run-b'], record: startedRecord('2025-07-01T09:00:00Z') }, 'run-b1': { ...libCtx('run-b1', 'bet', 'Beta Aero Inc', '2025-06-30', b1), record: startedRecord('2025-07-05T09:00:00Z') } };
  const make = direction => { const p = libPage({ catalogue: cat, contexts, data: { ...base.data, ...Object.fromEntries(b1) } }); p.libraryFilters.runs = 'any'; Object.assign(p.libraryState, { sortKey: 'leverage', direction }); return p; };
  const wordOf = (p, id) => { const view = p.libraryRows(), n = view.rows.findIndex(r => r.id === id); return /badge-gray">(Latest|Earlier)</.exec([...p.libraryResults(view, 'list').matchAll(/<td class="run-when">(.*?)<\/td>/g)][n][1])?.[1]; };
  for (const direction of ['asc', 'desc']) assert.deepEqual([wordOf(make(direction), 'run-b'), wordOf(make(direction), 'run-b1')], ['Earlier', 'Latest'], direction);
  const history = histRows(make('asc').historyView('run-b'));
  assert.deepEqual(history.slice(0, 2).map(r => /(Latest|Earlier)</.exec(r.marks)?.[1]), ['Latest', 'Earlier'], 'the history lists the later run first and gives it Latest');
});

const homeOf = activity => libPage({ activity });
test('M3 home: the live row draws running and waiting runs; the reload runs only while one is drawn; an ended run is gone and the loader with it', () => {
  const html = homeOf({ runs: [{ status: 'running', issuer_name: 'Run One', modules: [['CP-1', 'running']] }, { status: 'queued', issuer_name: 'Wait Two' }, { status: 'finished', issuer_name: 'Done' }] }).libraryLive();
  assert.ok(html.includes('Run One') && html.includes('Wait Two') && !html.includes('Done'));
  assert.ok(html.includes('<span class="state same rmark queued">') && html.includes('Waiting'));
  assert.equal(countOf(html, /rmark running/g), 1, 'one moving loader, for the running run only');
  // The re-load rule: the same timer as Run activity, but only while the home has a running or waiting run to follow.
  const text = read('views.js'), start = text.indexOf('// Run activity (ruling decision 10)'), end = text.indexOf('function workspaceView(');
  const rule = live => new Function('esc', 'icon', 'window', `${text.slice(start, end)}; return nextActivityReload;`)(esc, n => n, { Components: require('./components.js'), RUN_ACTIVITY: live });
  assert.equal(rule({ runs: [{ status: 'running' }] })({ module: 'W-Library' }), 30000);
  assert.equal(rule({ runs: [{ status: 'queued' }] })({ module: 'W-Library' }), 30000);
  for (const live of [{ runs: [{ status: 'finished' }] }, { runs: [] }, undefined, null, 'x', { runs: 'x' }]) assert.equal(rule(live)({ module: 'W-Library' }), null, JSON.stringify(live));
  assert.equal(rule({ runs: [{ status: 'running' }] })({ module: 'CP-1A' }), null, 'no other view follows runs');
  assert.equal(rule({ runs: [] })({ module: 'CP-OS' }), 30000);
  // The page: a snapshot that arrives while the home shows refreshes its live row and then lets the timer lapse; no second timer and no new kind of timer.
  const screen = read('screen.js'), handler = screen.slice(screen.indexOf('window.onRunActivity='), screen.indexOf("window.addEventListener('hashchange',syncActivityTimer)"));
  const calls = [];
  const fn = new Function('window', 'state', 'refreshLibraryLive', 'syncActivityTimer', 'nextActivityReload', '$', 'moduleBody', 'activityEnded', 'lastActivity', 'previousRunning', `${handler.replace(/\bcurrent\b/g, 'state.current')}; return window.onRunActivity;`)(
    { RUN_ACTIVITY: { runs: [] } }, { current: { module: 'W-Library' } }, () => calls.push('refresh'), () => calls.push('sync'), () => null, () => { throw new Error('the home is not re-rendered whole'); }, () => { throw new Error('no run page body'); }, () => ({ toasts: [], running: [] }), null, null);
  fn();
  assert.deepEqual(calls, ['refresh', 'sync']);
  assert.ok(!/setInterval\(/.test(screen));
  assert.strictEqual((screen.match(/activityTimer\s*=\s*setTimeout\(/g) || []).length, 1, 'exactly one setTimeout( call sets the activity timer');
  assert.ok(text.includes('function refreshLibraryLive()'), 'the live section is refreshed in place');
});

test('L1 the chip numbers in the Show-them view are the cards that view draws', () => {
  const page = libPage();
  page.libraryFilters.leverageMin = '1';
  const cov = page.libraryRows().coverage, group = Object.keys(cov).find(g => cov[g].hidden > 0);
  assert.ok(group, 'a group hides a run in the fixture');
  page.libraryState.hidden = group;
  const chips = [...page.libraryFacets().matchAll(/data-library-chip="(\w+)" data-value="([^"]*)" data-count="(\d+)"/g)].map(m => ({ key: m[1], value: decode(m[2]), count: Number(m[3]) }));
  for (const c of chips) {
    const p = libPage();
    p.libraryFilters.leverageMin = '1'; p.libraryState.hidden = group; p.libraryFilters[c.key] = c.value;
    assert.equal(countOf(p.libraryResults(p.libraryRows(), 'cards'), /<article class="lib-card"/g), c.count, `${c.key}=${c.value}`);
  }
});

test('L2 the Cards/List choice is library state: kept through an empty result, written by the toggle click, drawn from state', () => {
  const page = libPage();
  page.libraryState.view = 'list';
  const html = page.libraryResults(page.libraryRows());
  assert.ok(html.includes('data-view="list"') && html.includes('data-view-pick="list" aria-pressed="true"'));
  page.libraryFilters.search = 'nothing matches this';
  assert.ok(!page.libraryResults(page.libraryRows()).includes('data-block'));
  page.libraryFilters.search = '';
  assert.ok(page.libraryResults(page.libraryRows()).includes('data-view="list"'), 'List survives the empty result');
  const screen = read('screen.js');
  assert.ok(screen.includes("if(window.Components.handleClick(event.target)){const block=event.target.closest?.('.lib-block');if(block)libraryState.view=block.dataset.view;return;}"));
  assert.ok(screen.includes("view:'cards'") && !read('views.js').includes("querySelector('[data-block]')?.dataset.view"), 'state, not the DOM');
});

test('L3 dots: every dot is the same size with a glyph; completed carries a check, a declared state its icon, not assessable its mark, an unchosen output a hollow ring; each can take focus', () => {
  const html = C0.moduleDots([{ title: 'A', state: null }, { title: 'B', state: 'Ready' }, { title: 'C', state: 'Blocked' }, { title: 'D', blocked: true }, { title: 'E', choose: true }, { title: 'F', state: 'Draft Only' }]);
  const dots = html.split('<li ').slice(1);
  assert.deepEqual(dots.map(d => /class="mdot (\w+)"/.exec(d)[1]), ['done', 'ok', 'bad', 'warn', 'none', 'neutral']);  // the info tone is classed neutral: `.info` is the tooltip-button rule
  assert.ok(dots.slice(0, 4).concat(dots[5]).every(d => d.includes('<svg class="i"')), 'every module that ran has a glyph');
  assert.ok(dots[0].includes('M20 6 9 17l-5-5'), 'completed is a check');
  assert.ok(dots[3].includes('M12 9v4'), 'not assessable is the warning mark');
  assert.ok(!dots[4].includes('<svg'), 'an unchosen output is a hollow ring');
  assert.ok(dots.every(d => d.includes('role="img" tabindex="0"')), 'a dot takes focus so its tooltip shows from the keyboard');
  const css = read('screen.css');
  assert.ok(css.includes('.mdot.neutral>[role=img]{') && !css.includes('.mdot.info') && css.includes('.mdot>[role=img]:focus-visible{outline:2px solid var(--blue)'));
  assert.ok(/\.mdot>\[role=img\]\{[^}]*box-sizing:border-box;[^}]*width:20px;height:20px|\.mdot>\[role=img\]\{[^}]*width:20px;height:20px;[^}]*box-sizing:border-box/.test(css), 'one size');
});
const C0 = require('./components.js');

test('card: the lead sentence is clamped to four lines; Details is a button with aria-expanded that follows the open panel; the pathway is a pill; the catalogue-only date is the long form', () => {
  const css = read('screen.css');
  assert.ok(/\.lc-lead\{[^}]*-webkit-line-clamp:4;line-clamp:4;overflow:hidden/.test(css));
  const page = libPage(), view = page.libraryRows();
  const cards = () => page.libraryResults(page.libraryRows(), 'cards').split('<article class="lib-card"').slice(1);
  assert.ok(cards()[1].includes('<span class="badge badge-gray lc-path">Full credit assessment</span>') && cards()[1].includes('<p class="lc-when">30 June 2025</p>'));
  assert.ok(cards()[1].includes('class="secondary-action lc-details"') && cards()[1].includes('aria-expanded="false"'));
  page.libraryState.selected = 'run-b'; page.libraryState.opened = true;
  assert.ok(cards()[1].includes('aria-expanded="true"') && cards()[0].includes('aria-expanded="false"'));
  assert.equal(page.libraryRunName(view.rows.find(r => r.id === 'run-n')), '28 February 2025 · Credit Snapshot');
  assert.ok(page.libraryView().includes('data-chosen'), 'an opened panel is drawn open');
});

test('basis and limitation filters: the Leverage basis select is gone and an old address carrying it is ignored; a limitation is an option only when it is clean under the strict findings rule', () => {
  const panel = libPage().libraryPanel();
  assert.ok(!panel.includes('library-basis') && !/Leverage basis|definitions differ/.test(panel));
  assert.ok(!('basis' in libraryDefaults()));
  const page = libPage(), io = libHash(page, '#W-Library/cases?basis=Total%20debt%20%2F%20EBITDA&sector=Aerospace');
  assert.doesNotThrow(() => io.readLibraryHash());
  assert.equal(page.libraryFilters.sector, 'Aerospace');
  const dirty = libCatalogue(); dirty[1].gaps = ['No peer set was supplied.', 'See K_10.htm.jsonl for the split', 'Net figure (calculation C11)', 'CP-2A GAP-001'];
  const html = libPage({ catalogue: dirty }).libraryPanel();
  const options = [...html.matchAll(/<select id="library-limitation"[^>]*>(.*?)<\/select>/gs)][0][1];
  assert.deepEqual([...options.matchAll(/<option value="([^"]*)"/g)].map(m => m[1]), ['', 'No peer set was supplied.']);
});

test('history dots follow the catalogue\'s order, not the order the run ran its modules in', () => {
  const ran = { ...HIST.contexts['run-b'], record: { steps: [{ module: 'CP-2A' }, { module: 'CP-0' }] } };
  const page = runPage(d => d, [], m => m, { ...HIST, contexts: { ...HIST.contexts, 'run-b': ran } });
  const [, b] = histRows(page.historyView(RUN));
  assert.deepEqual(dotLabels(b.dots).map(l => l.split(': ')[0]), ['Source readiness', 'Downside'], 'the run ran Downside first; the strip keeps the catalogue order');
  assert.deepEqual(page.libraryModules('run-b').map(m => m.title), ['Source readiness', 'Downside']);
});

test('M3 timer: entering the home with a run to follow starts the timer without an immediate re-load when the file was just loaded with the page; the tick re-loads; a lapsed run stops it', () => {
  const screen = read('screen.js'), block = screen.slice(screen.indexOf('let activityTimer=null;'), screen.indexOf('window.onRunActivity='));
  const timers = new Map(); let id = 1; const swaps = []; const state = { current: { module: 'W-Library' }, wait: 30000 };
  const api = new Function('state', 'nextActivityReload', 'swapActivityScript', 'setTimeout', 'clearTimeout', 'document', 'Date', `${block.replace(/\bcurrent\b/g, 'state.current')}; return {syncActivityTimer};`)(
    state, () => state.wait, (d, now) => swaps.push(now), fn => { timers.set(id, fn); return id++; }, k => timers.delete(k), {}, { now: () => 5 });
  api.syncActivityTimer(true);
  assert.deepEqual(swaps, [], 'the page just loaded the file'); assert.equal(timers.size, 1);
  const [tick] = timers.values(); timers.clear(); tick(); assert.deepEqual(swaps, [5]); assert.equal(timers.size, 1);
  state.wait = null; api.syncActivityTimer(); assert.equal(timers.size, 0, 'no run left to follow: the timer stops');
  state.wait = 30000; api.syncActivityTimer(Object.create(null)); assert.equal(swaps.length, 2, 'a hashchange event is not "fresh": navigating back re-loads at once');
});

test('A14: a closed drawer is not drawn in print: the print hide list holds .inspector[hidden] and the screen-only flex rule cannot win there', () => {
  const css = read('screen.css');
  assert.ok(/@media print\{[^\n]*\.inspector\[hidden\][^\n]*\{display:none!important\}/.test(css), 'the print hide list names the closed drawer');
  assert.ok(css.includes('@media screen{.inspector[hidden]{display:flex!important;'), 'the slide-off rule is for screen only');
  assert.ok(!/(^|\n)\.inspector\[hidden\]\{display:flex!important/.test(css), 'no bare rule that would out-rank the print list');
});

test('B2: the rail count of a section is the number of items the section draws, not the raw blocks', () => {
  const html = runPage(() => overviewData({ 'CP-1': passageSections({ bottom: 'Cash is up.', key: ['One finding here.', '   ', 'Another finding here.'], limits: ['A limit.', '  '] }) }), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' }, names: FIXTURE_NAMES }).moduleReport(outId('CP-1'));
  const rail = Object.fromEntries([...html.matchAll(/<a class="rail-item" data-part="([^"]+)" href="[^"]+">[^<]*<span class="rail-count">(\d+)<\/span><\/a>/g)].map(m => [m[1], Number(m[2])]));
  assert.equal(countOf(html, /<li class="feed-item"/g), 2);
  assert.equal(rail['key-findings'], 2, 'two findings are drawn of three blocks');
  assert.equal(rail.limitations, 1, 'one limitation is drawn of two blocks');
});

test('B3: a search hit on a table the module page does not hold routes to the Evidence tab that holds it, with the hit\'s row; a section the page holds keeps its route', () => {
  const table = (line, rowLine) => [{ type: 'table', line, headers: ['Item', 'Value'], rows: [{ line: rowLine, cells: ['Revolver', '10'] }] }];
  const page = runPage(d => { const out = d[outId('CP-1')]; out.sections = [sec('Findings', 2, 1, 'view', []), sec('Calculations', 2, 10, 'calculations', table(11, 12)), sec('Sources', 2, 20, 'sources', table(21, 22))]; out.placement = out.sections.map(s => s.where); return d; });
  assert.equal(page.evidenceHit(outId('CP-1'), 'Calculations', 12), '#W-Evidence/calculations?c=run-a&m=CP-1&r=12');
  assert.equal(page.evidenceHit(outId('CP-1'), 'Sources', 22), '#W-Evidence/sources?c=run-a&m=CP-1&r=22');
  assert.equal(page.evidenceHit(outId('CP-1'), 'Calculations'), '#W-Evidence/calculations?c=run-a&m=CP-1', 'a table hit has no row');
  assert.equal(page.evidenceHit(outId('CP-1'), 'Findings'), null, 'a section no tab holds keeps the module route');
  assert.equal(require('./evidence.js').parseHash('#W-Evidence/sources?c=run-a&m=CP-1&r=22', ['CP-1']).row, '22');
  assert.equal(require('./evidence.js').parseHash('#W-Evidence/sources?r=x', []).row, undefined);
});

test('B8: no debt-stack series is the status green; the four fills are blue, violet, yellow and navy', () => {
  const rules = cssRules(read('screen.css').replace(/\/\*[^]*?\*\//g, ''));
  const fillOf = n => rules.filter(r => r.selector.split(',').map(s => s.trim()).includes(`.stack-seg.series-${n}`) && /(?:^|;)\s*background\s*:/.test(r.body)).at(-1)?.body.match(/background\s*:\s*([^;]+)/)[1].trim();
  assert.deepEqual([fillOf(1), fillOf(2), fillOf(3)], ['var(--series-4)', 'var(--series-3)', 'var(--navy)']);
  for (const n of [1, 2, 3]) assert.ok(!/series-2|--green/.test(fillOf(n)), `series ${n} is not a green`);
});

test('B6: a Forecast stack says its four field labels once in a header row over the aligned values; each row keeps its labels for a narrow card and assistive technology, and no value disappears', () => {
  const page = runPage(d => withStructure(d), [], m => m, { record: steps(['CP-1']), runFields: { asOf: '2025-03-31' } });
  const stack = cardOf(page.forecastCharts(RUN), 'Debt stack');
  const head = /<div class="stack-head" aria-hidden="true">(.*?)<\/div>/.exec(stack);
  assert.ok(head && countOf(stack, /class="stack-head"/g) === 1, 'one header row');
  assert.deepEqual([...head[1].matchAll(/<span>([^<]*)<\/span>/g)].map(m => m[1]), ['Rank', 'Secured', 'Amount', 'Cumulative leverage']);
  const rows = countOf(stack, /<dl class="stack-facts">/g);
  assert.ok(rows >= 1 && countOf(stack, /<dt>Rank<\/dt>/g) === rows, 'every row still carries its labels');
  for (const value of ['1,200', '2.4']) assert.ok(stack.includes(`<dd>${value}</dd>`), value);
  const css = read('screen.css');
  assert.ok(/@container \(min-width:560px\)\{[^]*\.fc-card \.stack-key \.stack-facts dt\{position:absolute/.test(css), 'the per-row labels are hidden only when the header stands over them');
});

test('L3: a printed Trace tab lists every statement: the rows past the first page are in the DOM, hidden on screen only, and "Show more" is not printed', () => {
  const E = require('./evidence.js'), sec = (heading, level, line, blocks = []) => ({ heading, level, line, blocks });
  const paragraphs = Array.from({ length: 45 }, (_, n) => ({ type: 'text', line: 10 + n, text: `Statement ${n + 1} holds.\nBasis: report.pdf, page ${n + 1}` }));
  const input = { run: { context: 'r', code: 'R', evidence: { sources: [], unused: [], unrecorded: [], noSourcesModules: [], handoffs: [], zip: null, downloads: [], record: { hashes: [], instructions: [], calls: [], cap: null } }, methodChanges: [], steps: [] }, modules: [{ id: 'CP-1', outputs: [{ id: 'o1', sections: [sec('Findings', 2, 1), sec('Key findings', 3, 3, paragraphs)], placement: ['view', 'view'] }] }], chips: {}, deps: { moduleTitle: code => code, hashLabel: n => n, methodChange: l => l } };
  const html = E.view(input, { tab: 'trace', module: null });
  assert.equal((html.match(/class="ev-trow"/g) || []).length, 45, 'every statement is in the DOM');
  assert.equal((html.match(/class="ev-trow" hidden/g) || []).length, 5, 'five are paged on screen');
  const css = read('screen.css'), print = css.split('@media print{').slice(1).map(block => block.slice(0, block.indexOf('}}') + 1)).join('\n');
  assert.ok(/\.ev-more[^{]*\{[^}]*display:none/.test(print) && /\.ev-trow\[hidden\][^{]*\{[^}]*display:block/.test(print), 'print hides the pager and un-hides the paged rows');
});

test('X1: opening an Evidence & audit item draws its sections minus the ones written for another module (screen.js sectionView)', () => {
  const screen = read('screen.js'), src = screen.slice(screen.indexOf('function sectionView('), screen.indexOf('function renderSearch('));
  const request = { heading: 'Request', blocks: [] }, alpha = { heading: 'Alpha register', blocks: [] };
  const sectionView = new Function('callBand', 'pins', 'galleryVisual', 'readerCharts', 'sectionsMarkup', 'sectionData', 'hiddenSections', 'data', 'esc', 'eventTable', `${src}; return sectionView;`)(
    () => '', {}, () => '', () => '', (id, sections) => sections.map(held => held.heading).join('|'), () => [request, alpha], () => new Set([request]), { o: { href: 'h', sha256: 's' } }, v => v);
  assert.equal(sectionView('o', 'req'), 'Alpha register', 'the hidden section is not drawn');
  assert.ok(sectionView('o', 'audit').includes('Alpha register') && !sectionView('o', 'audit').includes('Request'), 'nor under the audit item');
});

test('X2: a chip or trace control whose item is not in the evidence map is not drawn', () => {
  const r = report(), orphan = `${OUT}:888`, held = `${OUT}:16`;
  CHIPS[orphan] = [{ kind: 'issuer_page', source: 'K', file: 'K.jsonl', page: 5, page_end: null, quote_found: null }];
  try {
    assert.equal(r.chipsMarkup(orphan), '', 'chips and the row control of a key with no item');
    assert.ok(r.chipsMarkup(held).includes('data-chip='), 'a key with an item keeps them');
  } finally { delete CHIPS[orphan]; }
  const reader = require('./reader.js');
  const text = 'Debt is 6.57x.\nBasis: K.jsonl, page 5';
  assert.ok(reader.paragraphView(text, held, { held: true }).html.includes('data-paragraph='), 'item present: the control');
  assert.ok(!reader.paragraphView(text, held, { held: false }).html.includes('data-paragraph='), 'no item: no control');
  const texts = [{ text, line: 3 }], has = key => key === 'o:3';
  assert.ok(reader.passageControls(texts, { id: 'o', chips: () => 0, has }).trace(3).includes('data-paragraph="o:3"'));
  assert.equal(reader.passageControls(texts, { id: 'p', chips: () => 0, has }).trace(3), '', 'a passage paragraph with no item has no trace control');
  assert.equal(reader.passageControls(texts, { id: 'p', chips: () => 0, has }).figure(3, 0, '6.57x'), '');
});

// ---- ESG part (module page): the T2G sections of a Rates, FX & hedging handoff are one named part. The fixtures are two complete real handoffs (tests/fixtures/esg);
// the expected headings and cells are written by hand from them, the cells read straight from the Markdown rows by splitting on `|`.
const ESG_DIR = path.join(__dirname, '..', '..', '..', '..', 'tests', 'fixtures', 'esg');
const ESG_LABEL = 'Environmental, social and sustainability (ESG)';
const esgLines = name => fs.readFileSync(path.join(ESG_DIR, `CP-2E-${name}.md`), 'utf8').split('\n');
// The sections as store.parse_source holds them: a heading (levels 1 to 4) opens a section; a pipe table with its separator row is one block; a paragraph runs to a blank line or the next structure.
function esgSections(lines) {
  const sections = [];
  let cur = null;
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i], head = /^(#{1,4}) (.+)$/.exec(line);
    if (head) { cur = { heading: head[2], level: head[1].length, line: i + 1, where: 'view', blocks: [] }; sections.push(cur); continue; }
    if (!line.trim() || /^<!-- table-id: [\w.-]+ -->$/.test(line) || !cur) continue;
    if (line.startsWith('|') && /^\|[\s:|-]+\|$/.test(lines[i + 1] ?? '')) {
      const cells = row => row.trim().replace(/^\||\|$/g, '').split(/(?<!\\)\|/).map(c => c.trim()), block = { type: 'table', line: i + 1, headers: cells(line), rows: [] };
      for (i += 2; i < lines.length && lines[i].startsWith('|'); i += 1) block.rows.push({ line: i + 1, cells: cells(lines[i]) });
      i -= 1; cur.blocks.push(block); continue;
    }
    const start = i;
    while (i + 1 < lines.length && lines[i + 1].trim() && !/^(#|\||- |<!-- table-id:|```)/.test(lines[i + 1]) && !/^\d+\. /.test(lines[i + 1])) i += 1;
    cur.blocks.push({ type: 'text', line: start + 1, text: lines.slice(start, i + 1).join('\n') });
  }
  return sections;
}
const esgPage = (name, sections = esgSections(esgLines(name))) => runPage(() => overviewData({ 'CP-2E': sections }), [], m => m, { record: steps(['CP-2E']), runFields: { asOf: '2025-03-31' }, names: { ...FIXTURE_NAMES, 'CP-2E': 'Rates, FX & hedging' } });
const esgId = outId('CP-2E');
// The first data row of the "Materiality classification" table of a fixture: its first three cells, straight from the Markdown.
const materialityCells = name => {
  const lines = esgLines(name), at = lines.findIndex(line => /^#{3,4} T2G\.4 /.test(line)), row = lines.slice(at).find((line, n, rest) => line.startsWith('|') && rest[n - 2]?.startsWith('|') && /^\|[\s:|-]+\|$/.test(rest[n - 1]));
  return row.split('|').slice(1, 4).map(cell => cell.trim());
};
const ESG_TITLES = {
  h3: ['ESG source inventory', 'Environmental and transition register', 'Social and operational register', 'Materiality classification', 'Sustainability-linked mechanics', 'Refinancing access and cost of capital', 'Credit implication synthesis', 'Environmental and social gaps'],
  h4: ['environmental, social and transition disclosure inventory', 'environmental and transition exposure', 'social and operational exposure', 'materiality classification', 'sustainability-linked debt mechanics', 'refinancing and cost-of-capital linkage', 'credit implications', 'environmental, social and transition gaps'],
};
const partOf = (html, anchor) => { const open = html.indexOf(`<section class="part" id="${anchor}"`); return html.slice(open, html.indexOf('</section>', open)); };

for (const [name, own] of [['h3', 'Macro source gate'], ['h4', 'debt and rate exposure']]) {
  test(`ESG part (${name} fixture): one rail entry, the eight sections under it in handoff order, no T2G code, the rates sections keep their own entries`, () => {
    const page = esgPage(name), html = page.moduleReport(esgId), parts = page.reportParts(esgId);
    const esg = parts.filter(p => p[0] === 'esg');
    assert.equal(esg.length, 1);
    assert.equal(esg[0][1], ESG_LABEL);
    const rail = parts.slice(1).map(p => p[1]);
    assert.equal(rail.filter(label => label === ESG_LABEL).length, 1);
    for (const title of ESG_TITLES[name]) assert.ok(!rail.some(label => label.toLowerCase().startsWith(title.toLowerCase())), `no rail entry of its own: ${title}`);
    assert.ok(rail.some(label => label.toLowerCase().startsWith(own.toLowerCase())), `rates section ${own} keeps its entry`);
    assert.ok(!rail.some(label => label.includes('T2G.')) && !esg[0][2].includes('T2G.'));
    const railLinks = [...html.matchAll(/<a class="rail-item"[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/g)].filter(m => m[1].includes('#CP-2E/esg') && strip(m[2].replace(/<span class="rail-count">.*?<\/span>/g, '')).trim() === 'Environmental, social and sustainability (ESG)');
    assert.equal(railLinks.length, 1, 'the rail has exactly one link to the ESG part, with the ESG label');
    const headings = [...esg[0][2].matchAll(/<h([1-6])[^>]*>(.*?)<\/h\1>/g)].map(m => strip(m[2]).trim());
    assert.equal(headings[0], ESG_LABEL, 'the part is headed with its label');
    assert.deepEqual(headings.slice(1).map(h => h.toLowerCase()), ESG_TITLES[name].map(t => t.toLowerCase()));
    assert.ok(esg[0][3] > 0, 'the rail counts the drawn rows of the part');
  });
  test(`ESG part (${name} fixture): the first data row of the materiality table is drawn in the part, cell for cell`, () => {
    const page = esgPage(name), part = strip(page.reportParts(esgId).find(p => p[0] === 'esg')[2]).replace(/&#39;/g, "'").replace(/&amp;/g, '&');
    for (const cell of materialityCells(name)) assert.ok(cell && part.includes(cell), cell);
  });
}
test('ESG part: the part stands where the first ESG section stood among the body parts, and the other sections keep their order', () => {
  const ids = esgPage('h3').reportParts(esgId).map(p => p[0]), at = ids.indexOf('esg');
  assert.equal(ids[at - 1], 's-209', 'after the last rates section that stood before T2G.1 (line 232)');
  assert.equal(ids[at + 1], 's-301', 'before the section that followed T2G.8');
  assert.ok(!ids.some(id => ['s-232', 's-238', 's-247', 's-256', 's-269', 's-275', 's-282', 's-292'].includes(id)), 'no ESG section is a part of its own');
});
test('ESG part (h3 fixture): a register section of a shape that is not promoted is listed with an In Evidence link and none of its table is drawn; Evidence still lists the tables', () => {
  const sections = esgSections(esgLines('h3')), page = esgPage('h3', sections), parts = page.reportParts(esgId), part = parts.find(p => p[0] === 'esg')[2], html = page.moduleReport(esgId);
  const text = strip(part).replace(/&amp;/g, '&'), evidence = strip(evidenceRegisters(sections, 'CP-2E')).replace(/&amp;/g, '&');
  const lines = esgLines('h3'), firstCell = code => { const at = lines.findIndex(line => line.startsWith(`### ${code} `)), sep = lines.findIndex((line, n) => n > at && /^\|[\s:|-]+\|$/.test(line)); return lines[sep + 1].split('|')[1].trim(); };
  const href = `#W-Evidence/registers?c=${RUN}&amp;m=CP-2E`;
  for (const [code, title] of [['T2G.2', 'Environmental and transition register'], ['T2G.3', 'Social and operational register']]) {
    const cell = firstCell(code), table = sections.find(s => s.heading.startsWith(`${code} `)).blocks.find(b => b.type === 'table');
    assert.ok(cell && table.rows[0].cells[0] === cell);
    assert.ok(!text.includes(cell) && !strip(html).replace(/&amp;/g, '&').includes(cell), `not drawn on the module page: ${cell}`);
    const at = part.indexOf(`>${title}</h`), end = part.indexOf('class="analysis-section"', at), own = part.slice(at, end < 0 ? undefined : end);
    assert.ok(at > 0, title);
    assert.equal(countOf(own, /class="in-ev"/g), 1, `one In Evidence link under ${title}`);
    assert.ok(own.includes(`<p class="sec-moved"><a class="in-ev" href="${href}">In Evidence</a></p>`), own);
    assert.ok(evidence.includes(cell), `still in Evidence: ${cell}`);
  }
});
test('ESG part: a new-format handoff with no ESG heading has no esg part', () => {
  const ids = fixturePage().reportParts(outId('CP-2')).map(p => p[0]);
  assert.ok(!ids.includes('esg'));
  const withoutEsg = esgSections(esgLines('h3')).filter(s => !/^T2G\./.test(s.heading));
  assert.ok(!esgPage('h3', withoutEsg).reportParts(esgId).some(p => p[0] === 'esg'));
});

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
  assert.ok(read('views.js').includes("'Not run in this run'"));
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
  const fn = new Function('window', 'document', '$', 'moduleBody', 'showsCodes', 'nameCodes', 'nextActivityReload', 'state',
    `${screen.slice(screen.indexOf('let lastActivity'), screen.indexOf('window.onRunActivity=')).replace(/\bcurrent\b/g, 'state.current')}${handler.replace(/\bcurrent\b/g, 'state.current')}; return window.onRunActivity;`)(
    win, {}, () => content, () => 'body', () => false, () => {}, () => 30000, { current: { module: 'CP-OS' } });
  fn(); assert.strictEqual(content.writes, 1);
  win.RUN_ACTIVITY = { updated: 'T2', held: '', runs: [{ id: 'a' }] }; fn();
  assert.strictEqual(content.writes, 1, 'unchanged runs: no replacement'); assert.strictEqual(content.stamp.textContent, 'T2');
  win.RUN_ACTIVITY = { updated: 'T3', held: '', runs: [{ id: 'a', status: 'running' }] }; fn();
  assert.strictEqual(content.writes, 2, 'changed runs: replaced');
  win.RUN_ACTIVITY = { updated: 'T4', cap: '20', held: '', runs: [{ id: 'a', status: 'running' }] }; fn();
  assert.strictEqual(content.writes, 3, 'a changed cap with the same runs: replaced');
});

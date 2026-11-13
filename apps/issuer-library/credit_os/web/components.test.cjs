'use strict';
// Components: the icon table, the trace control, header chips, the tab pill, the toast and the tooltip attributes.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const C = require('./components.js');

test('every icon of the table is the markup of its file in icons/, and trace is the layers icon', () => {
  const dir = path.join(__dirname, 'icons');
  const files = fs.readdirSync(dir).filter(name => name.endsWith('.svg'));
  assert.ok(files.length >= 20);
  for (const file of files) {
    const name = file.replace('.svg', '');
    const inner = fs.readFileSync(path.join(dir, file), 'utf8').replace(/^[\s\S]*?>\s*/, '').replace(/<\/svg>\s*$/, '').replace(/\s+/g, ' ').replace(/> </g, '><').trim();
    assert.equal(C.ICON_PATHS[name], inner, name);
  }
  assert.equal(C.ICON_PATHS.trace, C.ICON_PATHS.layers);
  assert.deepEqual(Object.keys(C.ICON_PATHS).sort(), [...files.map(f => f.replace('.svg', '')), 'trace'].sort());
});

test('icon: inline SVG in the text colour, hidden from assistive technology; an unknown name throws', () => {
  const svg = C.icon('check');
  assert.ok(svg.startsWith('<svg ') && svg.includes('stroke="currentColor"') && svg.includes('aria-hidden="true"') && svg.includes('width="16"'));
  assert.ok(svg.includes(C.ICON_PATHS.check));
  assert.throws(() => C.icon('nope'), /no icon named nope/);
});

test('traceButton: a real button with an accessible name, the paragraph key and the Basis items as data attributes', () => {
  const html = C.traceButton('o:9', 'Show the basis of this paragraph', ['Q4.pdf, page 7']);
  assert.ok(html.startsWith('<button type="button" class="basis-link" data-paragraph="o:9" data-basis="[&quot;Q4.pdf, page 7&quot;]" aria-label="Show the basis of this paragraph">'));
  assert.ok(html.includes('<svg') && html.endsWith('</svg></button>'));
  assert.ok(!/>\s*Basis\s*</.test(html), 'the icon is the control; no Basis word');
  assert.ok(C.traceButton('o:9', 'x').includes('data-basis="[]"'));
  assert.ok(C.traceButton('k"><i>', 'a"b').includes('data-paragraph="k&quot;&gt;&lt;i&gt;"') && C.traceButton('k', 'a"b').includes('aria-label="a&quot;b"'));
});

test('traceRow: the same icon for a row opened by evidence key, with the row title and accessible name', () => {
  const html = C.traceRow('o:16', 'Table row, line 16');
  assert.ok(html.includes('data-evidence="o:16"') && html.includes('aria-label="Table row, line 16"') && html.includes('title="Table row, line 16"') && html.includes('<svg'));
});

test('headerChips: a chip per text, a link where there is an href, and nothing when there is nothing', () => {
  assert.equal(C.headerChips([]), '');
  assert.equal(C.headerChips([{text: ''}, null]), '');
  const html = C.headerChips([{text: '31 December 2025'}, {text: 'Credit snapshot'}, {text: 'Methods changed since this run', tone: 'amber', href: '#W-Evidence/record?c=r&x=1&y=2'}]);
  assert.equal(html, '<p class="hchips"><span class="hchip">31 December 2025</span><span class="hchip">Credit snapshot</span><a class="hchip amber" href="#W-Evidence/record?c=r&amp;x=1&amp;y=2">Methods changed since this run</a></p>');
});

test('tipAttributes: the tooltip text is also the accessible name', () => {
  assert.equal(C.tipAttributes('Copy "this"'), 'data-tip="Copy &quot;this&quot;" aria-label="Copy &quot;this&quot;"');
});

function fakeDocument() {
  const made = [];
  const node = tag => {
    const n = {tag, children: [], attrs: {}, id: '', className: '', textContent: '', removed: false,
      setAttribute(k, v) { this.attrs[k] = v; }, append(...kids) { this.children.push(...kids); }, remove() { this.removed = true; }};
    made.push(n);
    return n;
  };
  const body = node('body');
  return {made, body, createElement: node, getElementById: id => body.children.find(c => c.id === id) || null};
}

test('toast: one role=status host; each message is a child that removes itself after 3 seconds', t => {
  const doc = fakeDocument();
  global.document = doc;
  t.after(() => { delete global.document; });
  t.mock.timers.enable({apis: ['setTimeout']});
  C.toast('Copied');
  C.toast('Saved');
  const hosts = doc.body.children;
  assert.equal(hosts.length, 1, 'a single host');
  assert.equal(hosts[0].attrs.role, 'status');
  assert.deepEqual(hosts[0].children.map(c => c.textContent), ['Copied', 'Saved']);
  t.mock.timers.tick(2999);
  assert.ok(hosts[0].children.every(c => !c.removed));
  t.mock.timers.tick(1);
  assert.ok(hosts[0].children.every(c => c.removed));
});

test('toastHost: the role=status host exists, empty, before the first message and is reused', t => {
  const doc = fakeDocument();
  global.document = doc;
  t.after(() => { delete global.document; });
  const host = C.toastHost();
  assert.equal(host.attrs.role, 'status');
  assert.equal(host.children.length, 0);
  assert.equal(C.toastHost(), host);
  assert.equal(doc.body.children.length, 1);
});

test('placePill: the pill follows the active tab through custom properties; no measured tab, no pill', () => {
  const set = {}, classes = new Set();
  const box = active => ({querySelector: () => active, style: {setProperty: (k, v) => { set[k] = v; }}, classList: {add: c => classes.add(c), remove: c => classes.delete(c)}});
  assert.equal(C.placePill(box({offsetLeft: 40, offsetWidth: 90, offsetHeight: 36, offsetTop: 10})), true);
  assert.deepEqual(set, {'--pill-x': '40px', '--pill-w': '90px', '--pill-h': '36px', '--pill-y': '10px'});
  assert.ok(classes.has('has-pill'));
  assert.equal(C.placePill(box(null)), false);
  assert.ok(!classes.has('has-pill'));
  assert.equal(C.placePill(box({offsetLeft: 0, offsetWidth: 0, offsetHeight: 0, offsetTop: 0})), false, 'a hidden tab has no width');
});

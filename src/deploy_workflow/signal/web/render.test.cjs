'use strict';
// Card rendering of the Signal feed page, tested with a small DOM double (no browser).
const test = require('node:test');
const assert = require('node:assert/strict');
const { card, relativeTime, safeLink, emptyState, initials } = require('./render.js');

// A DOM double. textContent is plain text and never parsed as markup, like the real DOM.
class Text {
  constructor(data) { this.data = data; this.parent = null; }
  get textContent() { return this.data; }
}
class El {
  constructor(tag) { this.tagName = tag.toUpperCase(); this.children = []; this.attrs = {}; this.parent = null; this.hidden = false; }
  get className() { return this.attrs.class || ''; }
  set className(v) { this.attrs.class = String(v); }
  get textContent() { return this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this.children = []; if (String(v) !== '') this.appendChild(new Text(String(v))); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; }
  hasAttribute(k) { return k in this.attrs; }
  appendChild(c) { c.parent = this; this.children.push(c); return c; }
  append(...cs) { for (const c of cs) this.appendChild(typeof c === 'string' ? new Text(c) : c); }
  elements() { const out = []; for (const c of this.children) if (c instanceof El) out.push(c, ...c.elements()); return out; }
  querySelectorAll(sel) {
    const tests = sel.split(',').map(s => matcher(s.trim()));
    return this.elements().filter(e => tests.some(t => t(e)));
  }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
}
// Supports: tag, .class, [attr], [attr="value"] and their combinations (no combinators).
function matcher(sel) {
  const re = /^([a-z0-9]*)((?:\.[\w-]+|\[[\w-]+(?:="[^"]*")?\])*)$/i;
  const m = re.exec(sel);
  if (!m) throw new Error('unsupported selector ' + sel);
  const parts = m[2].match(/\.[\w-]+|\[[\w-]+(?:="[^"]*")?\]/g) || [];
  return e => {
    if (m[1] && e.tagName !== m[1].toUpperCase()) return false;
    return parts.every(p => {
      if (p[0] === '.') return e.className.split(/\s+/).includes(p.slice(1));
      const [, k, v] = /^\[([\w-]+)(?:="([^"]*)")?\]$/.exec(p);
      return v === undefined ? e.hasAttribute(k) : e.getAttribute(k) === v;
    });
  };
}
const doc = { createElement: tag => new El(tag), createElementNS: (ns, tag) => new El(tag), createTextNode: s => new Text(s) };

test('the DOM double does not parse markup', () => {
  const e = doc.createElement('div'); e.textContent = '<b>x</b>';
  assert.equal(e.querySelectorAll('b').length, 0);
  assert.equal(e.textContent, '<b>x</b>');
});

test('relativeTime', () => {
  const now = new Date('2026-11-13T12:00:00Z');
  assert.equal(relativeTime('2026-11-13T11:59:40Z', now), 'just now');
  assert.equal(relativeTime('2026-11-13T11:15:00Z', now), '45 min ago');
  assert.equal(relativeTime('2026-11-13T03:00:00Z', now), '9 h ago');
  assert.equal(relativeTime('2026-11-10T12:00:00Z', now), '3 d ago');
  assert.equal(relativeTime('2026-11-01T12:00:00Z', now), '1 Nov 2026');
  assert.equal(relativeTime('2026-11-14T12:00:00Z', now), 'just now');
});
test('safeLink allows only http and https', () => {
  assert.equal(safeLink('https://a.org/x'), 'https://a.org/x');
  for (const bad of ['javascript:alert(1)', 'data:text/html,x', ' JAVASCRIPT:alert(1)', 'file:///etc/passwd', '//a.org/x', ''])
    assert.equal(safeLink(bad), null);
});
test('a card renders hostile text as text', () => {
  const el = card(doc, {id: 1, title: '<img src=x onerror=alert(1)>', summary: '</script><b>x</b>', link: 'javascript:alert(1)',
                        source: '<i>S</i>', kind: 'news', published_at: '2026-11-13T11:00:00Z', other_sources: 2, saved: false,
                        topics: ['<u>T</u>']}, new Date('2026-11-13T12:00:00Z'));
  assert.equal(el.querySelectorAll('img, b, i, u, script').length, 0);
  assert.ok(el.textContent.includes('<img src=x onerror=alert(1)>'));
  assert.equal(el.querySelector('a[href]'), null);                 // no link for a javascript: URL
  assert.ok(el.textContent.includes('Also in 2 other sources'));
});
test('a card links out safely and marks its kind in words', () => {
  const el = card(doc, {id: 2, title: 'T', summary: '', link: 'https://a.org/x', source: 'Authority', kind: 'regulator',
                        published_at: '2026-11-13T11:00:00Z', other_sources: 0, saved: true, topics: []}, new Date('2026-11-13T12:00:00Z'));
  const a = el.querySelector('a[href]');
  assert.equal(a.getAttribute('rel'), 'noopener noreferrer'); assert.equal(a.getAttribute('target'), '_blank');
  assert.ok(el.textContent.includes('Regulator'));
  assert.equal(el.querySelector('[data-action="save"]').getAttribute('aria-pressed'), 'true');
  assert.ok(!el.textContent.includes('other sources'));
});

test('a single other source uses the singular', () => {
  const el = card(doc, {id: 3, title: 'T', summary: 's', link: 'https://a.org/x', source: 'Wire', kind: 'ratings',
                        published_at: '2026-11-13T11:00:00Z', other_sources: 1, saved: false, topics: []}, new Date('2026-11-13T12:00:00Z'));
  assert.ok(el.textContent.includes('Also in 1 other source'));
  assert.ok(!el.textContent.includes('1 other sources'));
  assert.ok(el.textContent.includes('Ratings'));
  assert.equal(el.querySelector('[data-action="save"]').getAttribute('aria-pressed'), 'false');
});

test('empty states say what to do, with the query as text', () => {
  assert.ok(emptyState(doc, 'foryou', '').textContent.includes('Follow a topic to fill this view'));
  assert.ok(emptyState(doc, 'saved', '').textContent.includes('Stories you save appear here'));
  assert.ok(emptyState(doc, 'latest', '', {approved: 0}).textContent.includes('No approved sources yet'));
  const s = emptyState(doc, 'latest', '<b>x</b>');
  assert.ok(s.textContent.includes('No story matches <b>x</b>'));
  assert.equal(s.querySelectorAll('b').length, 0);
});

test('an unknown approved count does not claim there are no approved sources', () => {
  const unknown = emptyState(doc, 'latest', '', {approved: undefined}).textContent;
  assert.ok(unknown.includes('No stories yet'));
  assert.ok(!unknown.includes('approved sources'));
  assert.ok(emptyState(doc, 'latest', '', {approved: 0}).textContent.includes('No approved sources yet'));
  assert.ok(emptyState(doc, 'latest', '', {approved: 3}).textContent.includes('No stories yet'));
});
test('a missing or unparseable time is empty and renders an empty hidden time element', () => {
  const now = new Date('2026-11-13T12:00:00Z');
  for (const bad of [null, undefined, '', 'not a time']) assert.equal(relativeTime(bad, now), '');
  const el = card(doc, {id: 1, title: 'T', kind: 'news', published_at: null}, now);
  const time = el.querySelector('time');
  assert.equal(time.textContent, '');
  assert.ok(time.hasAttribute('hidden'));
  assert.ok(!time.hasAttribute('datetime'));
});
test('initials are letters or digits of the first two words', () => {
  assert.equal(initials('A. Kovac'), 'AK');
  assert.equal(initials('eve'), 'E');
  assert.equal(initials('  '), '?');
  assert.equal(initials('Ünal Çelik'), 'ÜÇ');
  assert.equal(initials('<b>x</b> y'), 'Y');
});

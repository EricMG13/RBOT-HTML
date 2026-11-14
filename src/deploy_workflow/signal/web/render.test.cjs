'use strict';
// Card rendering of the Signal feed page, tested with a small DOM double (no browser).
const test = require('node:test');
const assert = require('node:assert/strict');
const R = require('./render.js');
const { card, relativeTime, safeLink, emptyState, initials } = R;

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
  appendChild(c) {
    if (c instanceof Fragment) { for (const k of c.children) { k.parent = this; this.children.push(k); } c.children = []; return c; }
    c.parent = this; this.children.push(c); return c;
  }
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
class Fragment extends El { constructor() { super('#fragment'); } }
const doc = { createDocumentFragment: () => new Fragment(), createElement: tag => new El(tag), createElementNS: (ns, tag) => new El(tag), createTextNode: s => new Text(s) };

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

// ---- slice 3: threads, comments, groups ----
const NOW = new Date('2026-11-13T12:00:00Z');
const links = f => f.querySelectorAll('a[href]').map(a => a.getAttribute('href'));
const elementsNamed = (f, tag) => f.querySelectorAll(tag);
const byAction = (e, a) => e.querySelectorAll('[data-action="' + a + '"]');
const cm = (o) => Object.assign({id: 1, parent_id: null, author: 'A. Kovac', role: 'writer', text: 'hello', created_at: '2026-11-13T09:12:00Z',
  edited: false, removed: false, reactions: [], mine: false, editable: false}, o);
const tview = (o) => Object.assign({id: 7, group_id: 2, group: 'TMT analysts', story: null, title: 'A note', started_by: 'ak', comments: [], can_post: true}, o);

test('linkify links only http and https and keeps punctuation outside', () => {
  const f = R.linkify(doc, 'see https://a.org/x). and javascript:alert(1) and <b>');
  assert.deepEqual(links(f), ['https://a.org/x']);
  assert.equal(f.textContent, 'see https://a.org/x). and javascript:alert(1) and <b>');
  assert.equal(elementsNamed(f, 'b').length, 0);
});
test('a link opens in a new tab without an opener', () => {
  const a = R.linkify(doc, 'x http://a.org/y').querySelector('a[href]');
  assert.equal(a.getAttribute('target'), '_blank');
  assert.equal(a.getAttribute('rel'), 'noopener noreferrer');
  assert.equal(a.textContent, 'http://a.org/y');
});
test('newlines become line breaks', () => {
  const f = R.linkify(doc, 'a\nb\n\nc');
  assert.equal(elementsNamed(f, 'br').length, 3);
  assert.equal(f.textContent, 'abc');
});
test('a removed comment shows the placeholder and no controls', () => {
  const e = R.comment(doc, cm({removed: true, text: 'secret', mine: true, editable: true, reactions: [{key: 'up', count: 1, mine: false}]}), NOW);
  assert.ok(e.textContent.includes('This comment was removed.'));
  assert.ok(!e.textContent.includes('secret'));
  assert.equal(e.querySelectorAll('button').length, 0);
});
test('edit and delete appear only on my comments, edit only while editable', () => {
  const other = R.comment(doc, cm({}), NOW);
  assert.equal(byAction(other, 'edit-comment').length + byAction(other, 'delete-comment').length, 0);
  const mine = R.comment(doc, cm({mine: true, editable: true}), NOW);
  assert.equal(byAction(mine, 'edit-comment').length, 1);
  assert.equal(byAction(mine, 'delete-comment').length, 1);
  const late = R.comment(doc, cm({mine: true, editable: false}), NOW);
  assert.equal(byAction(late, 'edit-comment').length, 0);
  assert.equal(byAction(late, 'delete-comment').length, 1);
  assert.equal(byAction(late, 'delete-comment')[0].getAttribute('data-id'), '1');
});
test('a reaction chip states its count and pressed state', () => {
  const e = R.comment(doc, cm({reactions: [{key: 'eyes', count: 1, mine: false}, {key: 'up', count: 2, mine: true}, {key: 'check', count: 0, mine: false}]}), NOW);
  const chips = byAction(e, 'react');
  assert.equal(chips.length, 2);
  assert.equal(chips[0].textContent, '👍 2');            // fixed order: up before eyes
  assert.equal(chips[0].getAttribute('aria-pressed'), 'true');
  assert.equal(chips[0].getAttribute('aria-label'), 'Thumbs up, 2');
  assert.equal(chips[0].getAttribute('data-key'), 'up');
  assert.equal(chips[1].textContent, '👀 1');
  assert.equal(chips[1].getAttribute('aria-pressed'), 'false');
  assert.equal(byAction(e, 'add-reaction').length, 2);   // check and question remain
  const reader = R.comment(doc, cm({reactions: [{key: 'up', count: 1, mine: false}]}), NOW, {canPost: false});
  assert.equal(byAction(reader, 'add-reaction').length, 0);
  assert.equal(byAction(reader, 'reply').length, 0);
});
test('comment shows name, role tag, edited tag and time', () => {
  const e = R.comment(doc, cm({edited: true, role: 'owner'}), NOW);
  assert.ok(e.textContent.includes('A. Kovac'));
  assert.ok(e.textContent.includes('Owner'));
  assert.ok(e.textContent.includes('edited'));
  assert.equal(e.querySelector('time').getAttribute('datetime'), '2026-11-13T09:12:00Z');
  assert.ok(!R.comment(doc, cm({role: 'reader'}), NOW).textContent.includes('Reader'));
});
test('replies render under their parent, one level', () => {
  const p = R.threadPanel(doc, tview({comments: [cm({id: 1}), cm({id: 2, parent_id: 1, text: 'reply'}), cm({id: 3, text: 'next'})]}), NOW);
  const top = p.querySelector('ol.comments').children;
  assert.equal(top.length, 2);
  assert.equal(top[0].querySelectorAll('ol.replies').length, 1);
  assert.ok(top[0].querySelector('ol.replies').textContent.includes('reply'));
  assert.equal(top[1].querySelectorAll('ol.replies').length, 0);
  assert.equal(byAction(top[0].querySelector('ol.replies'), 'reply').length, 0);
});
test('a reader gets the note in place of the reply box', () => {
  const r = R.threadPanel(doc, tview({can_post: false}), NOW);
  assert.ok(r.textContent.includes('Readers see this thread but not the reply box.'));
  assert.equal(r.querySelectorAll('textarea').length, 0);
  const w = R.threadPanel(doc, tview({can_post: true}), NOW);
  assert.ok(!w.textContent.includes('Readers see this thread'));
  assert.equal(w.querySelectorAll('textarea').length, 1);
  assert.equal(byAction(w, 'send-comment')[0].getAttribute('data-id'), '7');
});
test('the panel is a labelled aside with a heading, a quote for a story and day dividers', () => {
  const story = {id: 5, title: 'Big deal', link: 'https://a.org/s', source: 'Authority', kind: 'regulator', summary: '', published_at: '', other_sources: 0, saved: false, topics: [], threads: []};
  const p = R.threadPanel(doc, tview({story, title: null, comments: [
    cm({id: 1, created_at: '2026-11-12T09:00:00Z'}), cm({id: 2, created_at: '2026-11-12T10:00:00Z'}), cm({id: 3, created_at: '2026-11-13T08:00:00Z'})]}), NOW);
  assert.equal(p.tagName, 'ASIDE');
  assert.ok(p.hasAttribute('aria-labelledby'));
  assert.equal(p.querySelector('h2').getAttribute('tabindex'), '-1');
  assert.ok(p.querySelector('.quote').textContent.includes('Big deal'));
  const days = p.querySelectorAll('.day').map(d => d.textContent);
  assert.deepEqual(days, ['Today']);
  const p2 = R.threadPanel(doc, tview({comments: [cm({id: 1, created_at: '2026-11-01T09:00:00Z'}), cm({id: 2, created_at: '2026-11-12T10:00:00Z'}),
    cm({id: 3, created_at: '2026-11-13T08:00:00Z'})]}), NOW);
  assert.deepEqual(p2.querySelectorAll('.day').map(d => d.textContent), ['Yesterday', 'Today']);
  const p3 = R.threadPanel(doc, tview({comments: [cm({id: 1, created_at: '2026-11-01T09:00:00Z'}), cm({id: 2, created_at: '2026-11-03T10:00:00Z'})]}), NOW);
  assert.deepEqual(p3.querySelectorAll('.day').map(d => d.textContent), ['3 Nov 2026']);
});
test('a thread without comments says so', () => {
  assert.ok(R.threadPanel(doc, tview({}), NOW).textContent.includes('No comments yet'));
});
test('a card shows who shared it where with the note and a chip per thread', () => {
  const story = {id: 5, title: 'T', link: 'https://a.org/s', source: 'S', kind: 'news', summary: '', published_at: '2026-11-13T11:00:00Z', other_sources: 0, saved: false, topics: [],
    threads: [{id: 9, group: 'TMT analysts', comments: 3, shared_by: 'A. Kovac', note: 'Heavier than assumed.\nSecond line'}, {id: 10, group: 'Credit', comments: 0, shared_by: null, note: null}]};
  const e = card(doc, story, NOW);
  const line = e.querySelector('.shared');
  assert.ok(line.textContent.includes('A. Kovac'));
  assert.ok(line.textContent.includes('shared to'));
  assert.ok(line.textContent.includes('TMT analysts'));
  assert.ok(line.textContent.includes('Heavier than assumed.'));
  assert.ok(!line.textContent.includes('Second line'));
  const chips = byAction(e, 'open-thread');
  assert.equal(chips.length, 2);
  assert.equal(chips[0].getAttribute('data-id'), '9');
  assert.ok(chips[0].textContent.includes('3'));
  assert.equal(byAction(e, 'share')[0].getAttribute('data-id'), '5');
  assert.equal(byAction(card(doc, story, NOW, {canShare: false}), 'share').length, 0);
  assert.equal(card(doc, Object.assign({}, story, {threads: []}), NOW).querySelectorAll('.shared').length, 0);
});
test('markup in a group name, title, note or comment is text', () => {
  const bad = '<img src=x onerror=alert(1)><b>x</b>';
  const story = {id: 5, title: bad, link: 'javascript:1', source: bad, kind: 'news', summary: bad, published_at: '', other_sources: 0, saved: false, topics: [],
    threads: [{id: 9, group: bad, comments: 1, shared_by: bad, note: bad}]};
  const out = [card(doc, story, NOW),
    R.threadPanel(doc, tview({group: bad, title: bad, started_by: bad, story, comments: [cm({author: bad, text: bad})]}), NOW),
    R.threadRow(doc, {id: 1, kind: 'note', title: bad, source: bad, started_by: bad, comments: 2, last_activity_at: '2026-11-13T11:00:00Z', unread: true}, NOW),
    R.groupItem(doc, {id: 1, name: bad, visibility: 'invited', member: true, members: 2, threads: 1, unread: 3})];
  for (const e of out) {
    assert.equal(e.querySelectorAll('img, b, script').length, 0);
    assert.ok(e.textContent.includes(bad));
    for (const x of e.elements()) for (const k of Object.keys(x.attrs)) {
      assert.ok(!k.startsWith('on') && k !== 'style', 'attribute ' + k);
      // slice 2's card puts the title in aria-label (pre-existing, out of this task); the new elements do not.
      if (e !== out[0]) assert.ok(!x.attrs[k].includes('<img'), 'data in attribute ' + k);
    }
  }
});
test('a thread row shows kind, counts, last activity and an unread mark in words', () => {
  const row = {id: 4, kind: 'story', title: 'Deal', source: 'Authority', started_by: 'ak', comments: 1, last_activity_at: '2026-11-13T11:15:00Z', unread: true};
  const e = R.threadRow(doc, row, NOW);
  assert.equal(e.getAttribute('data-action'), 'open-thread');
  assert.equal(e.getAttribute('data-id'), '4');
  assert.ok(e.textContent.includes('Authority') && e.textContent.includes('Deal'));
  assert.ok(e.textContent.includes('1 comment') && !e.textContent.includes('1 comments'));
  assert.ok(e.textContent.includes('45 min ago'));
  assert.ok(e.textContent.includes('Unread'));
  assert.ok(!R.threadRow(doc, Object.assign({}, row, {unread: false, comments: 0}), NOW).textContent.includes('Unread'));
  const note = R.threadRow(doc, Object.assign({}, row, {kind: 'note', source: null, title: 'My note'}), NOW);
  assert.ok(note.textContent.includes('My note') && note.textContent.includes('Note'));
});
test('a group item has its name, a lock when invited and an unread count', () => {
  const g = {id: 3, name: 'TMT', visibility: 'invited', member: true, members: 4, threads: 2, unread: 5};
  const e = R.groupItem(doc, g);
  assert.equal(e.getAttribute('data-action'), 'open-group');
  assert.equal(e.getAttribute('data-id'), '3');
  assert.ok(e.textContent.includes('TMT'));
  assert.ok(e.textContent.includes('Invited group'));
  assert.ok(e.textContent.includes('5'));
  const open = R.groupItem(doc, Object.assign({}, g, {visibility: 'everyone', unread: 0}));
  assert.ok(!open.textContent.includes('Invited group'));
  assert.equal(open.querySelectorAll('.badge').length, 0);
});

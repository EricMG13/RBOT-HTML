'use strict';
// The Signal feed page: state, API calls and event wiring. Card, thread, group and dialog markup comes from
// render.js; this file builds no HTML from data (text goes in with textContent only).
// Sections: feed, topics, groups (channel list, group view, members), address (hash routes), thread panel,
// dialogs (share, new group, note), name, events.
(function () {
  const R = window.SignalRender;
  const POLL_MS = 45000;
  const SEARCH_DEBOUNCE_MS = 300;
  const VIEW_TITLES = {foryou: 'For you', latest: 'Latest', saved: 'Saved'};

  const $ = id => document.getElementById(id);
  const els = {
    channels: $('channels'), channelsToggle: $('channels-toggle'), viewList: $('view-list'), topicList: $('topic-list'),
    title: $('view-title'), feed: $('feed'), cards: $('cards'), skeleton: $('skeleton'), empty: $('empty'), more: $('more'),
    band: $('error-band'), bandText: $('error-text'), retry: $('retry'), pill: $('new-pill'), live: $('live'),
    freshness: $('freshness'), freshnessText: $('freshness-text'), search: $('search'), kindChips: $('kind-chips'),
    chip: $('name-chip'), meName: $('me-name'), meRole: $('me-role'), meInitials: $('me-initials'),
    dialog: $('name-dialog'), form: $('name-form'), input: $('name-input'), nameError: $('name-error'), cancel: $('name-cancel'),
    app: document.querySelector('.app'), rail: document.querySelector('.rail'), railLink: document.querySelector('.rail-link'),
    railBadge: $('rail-badge'), groupList: $('group-list'), newGroup: $('new-group'), feedBar: $('feed-bar'),
    groupHead: $('group-head'), threads: $('threads'), slot: $('thread-slot'),
  };
  const SHARE = {dialog: $('share-dialog'), form: $('share-dialog-form'), error: $('share-dialog-error'), submit: $('share-submit'),
    box: $('share-groups-box'), groups: $('share-groups'), note: $('share-note')};
  const GROUP = {dialog: $('group-dialog'), form: $('group-dialog-form'), error: $('group-dialog-error'), submit: $('group-submit'),
    name: $('group-name'), visibility: $('group-visibility'), topics: $('group-topics')};
  const NOTE = {dialog: $('note-dialog'), form: $('note-dialog-form'), error: $('note-dialog-error'), submit: $('note-submit'),
    title: $('note-title'), text: $('note-text')};
  const NARROW = window.matchMedia('(max-width: 899px)');
  const REPLY_COUNTER_FROM = 3800;
  const REPLY_LIMIT = 4000;

  const state = {
    view: 'foryou', kind: '', q: '', next: null, shown: 0, topics: [], approved: undefined,
    me: null, seq: 0, loading: false, newest: null, retry: null, pollTimer: null, searchTimer: null,
    groups: [], canCreate: false, groupsLoaded: false, groupId: null, group: null, groupSeq: 0, groupNext: null, threadRows: 0,
    threadId: null, thread: null, pendingOpener: null, dialogOpener: null, shareStory: null, noteGroup: null,
  };

  class ApiError extends Error {
    constructor(status, message) { super(message); this.status = status; }
  }

  async function api(method, path, body) {
    const init = {method, headers: {}};
    if (method !== 'GET') {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(body === undefined ? {} : body);
    }
    let res;
    try {
      res = await fetch(path, init);
    } catch (err) {
      throw new ApiError(0, 'Signal could not be reached. Check your connection and try again.');
    }
    let data = null;
    let readable = true;
    try {
      data = await res.json();
    } catch (err) {
      readable = false; // a body that is not JSON is reported below, by status or as unreadable
    }
    if (!res.ok) {
      const message = data && typeof data.error === 'string' ? data.error : 'Signal could not complete that request.';
      throw new ApiError(res.status, message);
    }
    if (!readable) throw new ApiError(res.status, 'The service sent an unreadable answer.');
    return data;
  }

  function announce(text) {
    els.live.textContent = '';
    window.setTimeout(() => { els.live.textContent = text; }, 50);
  }

  function showError(message, retry) {
    els.bandText.textContent = message;
    els.band.hidden = false;
    state.retry = retry;
    announce(message);
  }

  function clearError() {
    els.band.hidden = true;
    state.retry = null;
  }

  function feedParams(before) {
    const p = new URLSearchParams({view: state.view});
    if (state.kind) p.set('kind', state.kind);
    if (state.q) p.set('q', state.q);
    if (before) p.set('before', before);
    return p;
  }

  function setBusy(busy) {
    state.loading = busy;
    els.feed.setAttribute('aria-busy', busy ? 'true' : 'false');
  }

  function renderEmpty() {
    els.empty.textContent = '';
    if (state.shown > 0) { els.empty.hidden = true; return; }
    els.empty.appendChild(R.emptyState(document, state.view, state.q, {approved: state.approved, kind: state.kind}));
    renderTopicChoices();
    els.empty.hidden = false;
  }

  // The topic list inside the For you empty state: the same follow action as the channel list star.
  function renderTopicChoices() {
    const slot = els.empty.querySelector('[data-slot="topics"]');
    if (!slot) return;
    for (const topic of state.topics) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'chip';
      b.setAttribute('data-follow', topic.id);
      b.setAttribute('aria-pressed', topic.following ? 'true' : 'false');
      b.textContent = topic.name;
      slot.appendChild(b);
    }
  }

  function appendCards(list) {
    const now = new Date();
    for (const story of list) els.cards.appendChild(R.card(document, story, now, {canShare: state.canCreate}));
    state.shown += list.length;
  }

  // Loads the current view. reset: replace the list (skeletons while waiting); otherwise append the
  // next page. On failure the last good list stays and the error band offers Retry.
  async function load(reset) {
    const seq = ++state.seq;
    const before = reset ? null : state.next;
    clearError();
    setBusy(true);
    if (reset) { els.skeleton.hidden = false; els.cards.hidden = true; els.empty.hidden = true; els.more.hidden = true; }
    else els.more.disabled = true;
    try {
      const data = await api('GET', '/api/feed?' + feedParams(before));
      if (seq !== state.seq) return false;
      if (reset) { els.cards.textContent = ''; state.shown = 0; }
      const firstNew = els.cards.children.length;
      appendCards(data.cards);
      state.next = data.next_before;
      if (reset) { state.newest = data.newest; hidePill(); }
      renderEmpty();
      announce(state.shown === 0 ? 'No stories' : state.shown + (state.shown === 1 ? ' story' : ' stories') + ' shown');
      if (!reset && els.cards.children[firstNew]) els.cards.children[firstNew].focus();
      return true;
    } catch (err) {
      if (seq !== state.seq) return false;
      // A failed reset leaves the old cards under the new title: they must not be extendable.
      if (reset) state.next = null;
      if (err.status === 401) { askName(); return false; }
      showError(err.message, () => load(reset));
      return false;
    } finally {
      if (seq === state.seq) {
        setBusy(false);
        els.skeleton.hidden = true;
        els.cards.hidden = false;
        els.more.disabled = false;
        els.more.hidden = state.next === null;
      }
    }
  }

  function hidePill() { els.pill.hidden = true; }

  function setView(view) {
    leaveGroupMode();
    state.view = view;
    state.kind = '';
    state.q = '';
    els.search.value = '';
    syncKindChips();
    markCurrentChannel();
    const topic = state.topics.find(t => 'topic:' + t.id === view);
    els.title.textContent = VIEW_TITLES[view] || (topic ? topic.name : 'Topic');
    setChannelsOpen(false);
    return load(true);
  }

  function syncKindChips() {
    for (const b of els.kindChips.querySelectorAll('.chip'))
      b.setAttribute('aria-pressed', b.getAttribute('data-kind') === state.kind ? 'true' : 'false');
  }

  function setChannelsOpen(open) {
    els.channels.classList.toggle('open', open);
    els.channelsToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  // Where focus goes after a follow change rebuilt the list the user was in: the same control for the
  // topic if it still exists, else the other follow control for it, else the view's heading.
  function restoreFollowFocus(id, container) {
    const sel = '[data-follow="' + String(id).replace(/[^\w-]/g, '') + '"]';
    const target = container.querySelector(sel) || els.channels.querySelector(sel) || els.empty.querySelector(sel);
    if (target) target.focus();
    else els.title.focus();
  }

  // ----- topics
  function renderTopics() {
    els.topicList.textContent = '';
    if (state.topics.length === 0) {
      const li = document.createElement('li');
      li.className = 'side-empty';
      li.textContent = 'No topics yet';
      els.topicList.appendChild(li);
      return;
    }
    for (const topic of state.topics) {
      const li = document.createElement('li');
      li.className = 'topic-row';
      const view = document.createElement('button');
      view.type = 'button';
      view.className = 'ch';
      view.setAttribute('data-view', 'topic:' + topic.id);
      if (state.groupId === null && state.view === 'topic:' + topic.id) view.setAttribute('aria-current', 'page');
      const name = document.createElement('span');
      name.className = 'ch-name';
      name.textContent = topic.name;
      const count = document.createElement('span');
      count.className = 'count';
      count.textContent = String(topic.stories);
      count.setAttribute('title', topic.stories + (topic.stories === 1 ? ' story' : ' stories'));
      view.append(R.icon(document, 'hash'), name, count);
      const follow = document.createElement('button');
      follow.type = 'button';
      follow.className = 'follow';
      follow.setAttribute('data-follow', topic.id);
      follow.setAttribute('aria-pressed', topic.following ? 'true' : 'false');
      follow.setAttribute('aria-label', 'Follow ' + topic.name);
      follow.appendChild(R.icon(document, 'star'));
      li.append(view, follow);
      els.topicList.appendChild(li);
    }
  }

  async function loadTopics() {
    try {
      state.topics = await api('GET', '/api/topics');
      renderTopics();
      const topic = state.topics.find(t => 'topic:' + t.id === state.view);
      if (topic) els.title.textContent = topic.name;
    } catch (err) {
      if (err.status !== 401) showError(err.message, loadTopics);
    }
  }

  async function toggleFollow(id) {
    const topic = state.topics.find(t => String(t.id) === String(id));
    if (!topic) return;
    const origin = document.activeElement;
    try {
      const data = await api(topic.following ? 'DELETE' : 'POST', '/api/topics/' + encodeURIComponent(id) + '/follow');
      topic.following = data.following;
      // The pressed state changes in place, so the focused control survives.
      for (const b of document.querySelectorAll('[data-follow]'))
        if (b.getAttribute('data-follow') === String(id)) b.setAttribute('aria-pressed', data.following ? 'true' : 'false');
      announce((data.following ? 'Following ' : 'Unfollowed ') + topic.name);
      if (state.view === 'foryou') {
        // For you is rebuilt from the new follow set; focus returns to the control the user was on.
        const container = origin && els.empty.contains(origin) ? els.empty : els.channels;
        await load(true);
        restoreFollowFocus(id, container);
      }
    } catch (err) {
      if (err.status === 401) askName(); else showError(err.message, () => toggleFollow(id));
    }
  }

  // ----- save
  async function toggleSave(button) {
    const article = button.closest('article');
    const id = article.getAttribute('data-id');
    const saved = button.getAttribute('aria-pressed') === 'true';
    try {
      const data = await api(saved ? 'DELETE' : 'POST', '/api/stories/' + encodeURIComponent(id) + '/save');
      button.setAttribute('aria-pressed', data.saved ? 'true' : 'false');
      announce(data.saved ? 'Saved' : 'Removed from saved');
    } catch (err) {
      if (err.status === 401) askName(); else showError(err.message, () => toggleSave(button));
    }
  }

  // ----- status and freshness
  function describeStatus(status) {
    state.approved = status.sources.approved;
    let text = status.last_pass_at ? 'Sources checked ' + R.relativeTime(status.last_pass_at, new Date()) : 'Sources not checked yet';
    const problems = [];
    if (status.sources.failing > 0) problems.push(status.sources.failing + (status.sources.failing === 1 ? ' source failing' : ' sources failing'));
    if (status.loop_error) problems.push('the check reported an error');
    if (problems.length) text += ' · ' + problems.join(', ');
    els.freshnessText.textContent = text;
    els.freshness.classList.toggle('warn', problems.length > 0);
  }

  async function loadStatus() {
    try {
      describeStatus(await api('GET', '/api/status'));
    } catch (err) {
      els.freshnessText.textContent = 'Source status unavailable';
      els.freshness.classList.add('warn');
    }
  }

  // ----- poll. Fail-open by design: a failed poll only means no pill, no fresh badge and no thread refresh this
  // round (each logs a warning); the next poll tries again, and the views report their own failures in the error band.
  async function pollNewStories() {
    if (state.groupId !== null || state.newest === null || state.loading) return;
    try {
      const snap = {view: state.view, kind: state.kind, q: state.q, newest: state.newest};
      const params = new URLSearchParams({view: snap.view, after: String(snap.newest)});
      const data = await api('GET', '/api/feed/new?' + params);
      const current = state.groupId === null && state.view === snap.view && state.kind === snap.kind && state.q === snap.q && state.newest === snap.newest;
      if (current && data.count > 0) {
        els.pill.textContent = data.count + (data.count === 1 ? ' new story' : ' new stories');
        if (els.pill.hidden) announce(els.pill.textContent);
        els.pill.hidden = false;
      }
    } catch (err) {
      console.warn('new-story poll failed:', err.message);
    }
  }

  function poll() {
    if (document.visibilityState === 'hidden' || !state.me) return;
    loadStatus();
    loadGroups(true);
    refreshUnread();
    refreshOpenThread();
    pollNewStories();
  }

  // ----- groups: channel list, unread badges
  function markCurrentChannel() {
    for (const b of document.querySelectorAll('.ch[data-view]')) {
      if (state.groupId === null && b.getAttribute('data-view') === state.view) b.setAttribute('aria-current', 'page');
      else b.removeAttribute('aria-current');
    }
    for (const b of els.groupList.querySelectorAll('[data-action="open-group"]')) {
      if (b.getAttribute('data-id') === state.groupId) b.setAttribute('aria-current', 'page');
      else b.removeAttribute('aria-current');
    }
  }

  function renderGroupList() {
    els.groupList.textContent = '';
    if (state.groups.length === 0) els.groupList.appendChild(R.groupsEmpty(document));
    for (const g of state.groups) {
      const li = document.createElement('li');
      li.appendChild(R.groupItem(document, g));
      els.groupList.appendChild(li);
    }
    els.newGroup.hidden = !state.canCreate;
    markCurrentChannel();
  }

  async function loadGroups(quiet) {
    if (!quiet) els.groupList.setAttribute('aria-busy', 'true');
    try {
      const data = await api('GET', '/api/groups');
      state.groups = data.groups;
      state.canCreate = Boolean(data.can_create);
      state.groupsLoaded = true;
      renderGroupList();
      return true;
    } catch (err) {
      if (err.status === 401) askName();
      else if (quiet) console.warn('group list refresh failed:', err.message);
      else showError(err.message, () => loadGroups(false));
      return false;
    } finally {
      els.groupList.setAttribute('aria-busy', 'false');
    }
  }

  function setRailBadge(total) {
    els.railBadge.textContent = String(total);
    els.railBadge.hidden = total <= 0;
    els.railLink.setAttribute('aria-label', total > 0 ? 'Signal, ' + R.unreadLabel(total) : 'Signal');
  }

  // The unread object of GET /api/unread and of the read route: {total, by_group: {id: count}}.
  function applyUnread(unread) {
    setRailBadge(unread.total);
    for (const g of state.groups) g.unread = unread.by_group[String(g.id)] || 0;
    renderGroupList();
  }

  async function refreshUnread() {
    try {
      applyUnread(await api('GET', '/api/unread'));
    } catch (err) {
      console.warn('unread refresh failed:', err.message);
    }
  }

  // ----- groups: the group view
  function enterGroupMode() {
    state.seq += 1; // a feed load still in flight must not touch the page
    setBusy(false);
    els.skeleton.hidden = true;
    els.feedBar.hidden = true;
    els.cards.hidden = true;
    els.pill.hidden = true;
    els.empty.hidden = true;
    els.empty.textContent = '';
    els.more.hidden = true;
  }

  function leaveGroupMode() {
    if (state.groupId === null) return;
    state.groupId = null;
    state.group = null;
    state.groupSeq += 1;
    state.threadRows = 0;
    els.feedBar.hidden = false;
    els.groupHead.hidden = true;
    els.groupHead.textContent = '';
    els.threads.hidden = true;
    els.threads.textContent = '';
    markCurrentChannel();
  }

  function showGroupMissing() {
    els.title.textContent = 'Group';
    els.groupHead.hidden = true;
    els.groupHead.textContent = '';
    els.threads.hidden = true;
    els.threads.textContent = '';
    els.more.hidden = true;
    els.empty.textContent = '';
    els.empty.appendChild(R.notFound(document, 'group'));
    els.empty.hidden = false;
    announce('This group does not exist or is not open to you.');
  }

  function renderGroupHead(focusSelector) {
    els.groupHead.textContent = '';
    els.groupHead.appendChild(R.groupHead(document, state.group, state.canCreate));
    els.groupHead.hidden = false;
    if (focusSelector) {
      const target = els.groupHead.querySelector(focusSelector);
      if (target) target.focus();
    }
  }

  function appendThreadRows(rows) {
    const now = new Date();
    for (const row of rows) els.threads.appendChild(R.threadRow(document, row, now));
    state.threadRows += rows.length;
  }

  function renderThreadsEmpty() {
    els.empty.textContent = '';
    if (state.threadRows > 0) { els.empty.hidden = true; return; }
    els.empty.appendChild(R.threadsEmpty(document, state.canCreate));
    els.empty.hidden = false;
  }

  async function openGroup(id) {
    state.groupId = id;
    state.group = null;
    const seq = ++state.groupSeq;
    enterGroupMode();
    clearError();
    setBusy(true);
    els.groupHead.hidden = true;
    els.threads.hidden = true;
    els.skeleton.hidden = false;
    markCurrentChannel();
    setChannelsOpen(false);
    try {
      const [group, page] = await Promise.all([
        api('GET', '/api/groups/' + id), api('GET', '/api/groups/' + id + '/threads')]);
      if (seq !== state.groupSeq) return;
      state.group = group;
      state.groupNext = page.next_before;
      state.threadRows = 0;
      els.title.textContent = group.name;
      els.threads.textContent = '';
      appendThreadRows(page.threads);
      els.threads.hidden = false;
      renderGroupHead();
      renderThreadsEmpty();
      els.more.hidden = state.groupNext === null;
      announce(group.name + ': ' + (state.threadRows === 1 ? '1 thread' : state.threadRows + ' threads'));
    } catch (err) {
      if (seq !== state.groupSeq) return;
      if (err.status === 404) showGroupMissing();
      else if (err.status === 401) askName();
      else showError(err.message, () => openGroup(id));
    } finally {
      if (seq === state.groupSeq) {
        setBusy(false);
        els.skeleton.hidden = true;
      }
    }
  }

  async function moreThreads() {
    const seq = state.groupSeq;
    const id = state.groupId;
    els.more.disabled = true;
    try {
      const page = await api('GET', '/api/groups/' + id + '/threads?' + new URLSearchParams({before: state.groupNext}));
      if (seq !== state.groupSeq) return;
      const first = els.threads.children.length;
      appendThreadRows(page.threads);
      state.groupNext = page.next_before;
      els.more.hidden = state.groupNext === null;
      if (els.threads.children[first]) els.threads.children[first].focus();
    } catch (err) {
      if (seq === state.groupSeq) showError(err.message, moreThreads);
    } finally {
      els.more.disabled = false;
    }
  }

  // The first page again, replacing the rows (after a note was started).
  async function reloadThreads() {
    const seq = state.groupSeq;
    try {
      const page = await api('GET', '/api/groups/' + state.groupId + '/threads');
      if (seq !== state.groupSeq) return;
      els.threads.textContent = '';
      state.threadRows = 0;
      appendThreadRows(page.threads);
      state.groupNext = page.next_before;
      renderThreadsEmpty();
      els.more.hidden = state.groupNext === null;
    } catch (err) {
      if (seq === state.groupSeq) showError(err.message, reloadThreads);
    }
  }

  // ----- groups: members strip
  function membersError(message) {
    const slot = els.groupHead.querySelector('[data-slot="members-error"]');
    if (!slot) return;
    slot.textContent = message;
    slot.hidden = !message;
  }

  async function rereadGroup(focusSelector) {
    const seq = state.groupSeq;
    try {
      const group = await api('GET', '/api/groups/' + state.groupId);
      if (seq !== state.groupSeq) return;
      state.group = group;
      renderGroupHead(focusSelector);
    } catch (err) {
      if (seq !== state.groupSeq) return;
      if (err.status === 404) showGroupMissing(); // for example after leaving an invited group
      else if (err.status === 401) askName();
      else showError(err.message, () => rereadGroup(focusSelector));
    }
  }

  async function changeMembers(method, body, focusSelector) {
    const seq = state.groupSeq;
    try {
      await api(method, '/api/groups/' + state.groupId + '/members', body);
    } catch (err) {
      if (err.status === 401) askName();
      else if (seq === state.groupSeq) { membersError(err.message); announce(err.message); }
      return;
    }
    await rereadGroup(focusSelector);
    loadGroups(true);
  }

  function onGroupHeadClick(event) {
    const b = event.target.closest('[data-action]');
    if (!b || b.tagName === 'FORM') return;
    const action = b.getAttribute('data-action');
    if (action === 'join-group') changeMembers('POST', {}, '[data-action="leave-group"]');
    else if (action === 'leave-group') changeMembers('DELETE', {}, '[data-action="join-group"]');
    else if (action === 'remove-member') changeMembers('DELETE', {name: b.getAttribute('data-name')}, '.member-list .link-btn, #add-member-name');
    else if (action === 'start-note') openNoteDialog(b);
  }

  function onAddMember(event) {
    const form = event.target.closest('form[data-action="add-member"]');
    if (!form) return;
    event.preventDefault();
    const input = form.querySelector('input');
    const name = input.value.trim();
    if (!name) { membersError('Enter a name to add.'); input.focus(); return; }
    changeMembers('POST', {name}, '#add-member-name');
  }

  // ----- address: #group=<id>&thread=<id>, digits only; anything else is ignored
  function parseRoute() {
    const route = {group: null, thread: null};
    for (const part of window.location.hash.replace(/^#/, '').split('&')) {
      const m = /^(group|thread)=([0-9]{1,18})$/.exec(part);
      if (m) route[m[1]] = m[2];
    }
    return route;
  }

  // Moves to a route: one history entry, so Back and Forward restore both the view and the thread.
  function navigate(route, apply) {
    const parts = [];
    if (route.group) parts.push('group=' + route.group);
    if (route.thread) parts.push('thread=' + route.thread);
    const url = window.location.pathname + window.location.search + (parts.length ? '#' + parts.join('&') : '');
    if (url !== window.location.pathname + window.location.search + window.location.hash) window.history.pushState(null, '', url);
    if (apply !== false) applyRoute();
  }

  async function applyRoute() {
    if (!state.me) return;
    const route = parseRoute();
    if (route.group !== state.groupId) {
      if (route.group !== null) openGroup(route.group);
      else setView(state.view);
    }
    if (route.thread !== state.threadId) {
      if (route.thread !== null) openThread(route.thread);
      else closePanel();
    }
  }

  // ----- thread panel
  function setInert() {
    const on = state.threadId !== null && NARROW.matches;
    for (const node of [els.rail, els.channels, els.feed]) node.toggleAttribute('inert', on);
  }

  function showPanel(panel) {
    els.slot.textContent = '';
    els.slot.appendChild(panel);
    els.slot.hidden = false;
    els.app.classList.add('has-thread');
    setInert();
  }

  function selectorFor(node) {
    const clean = value => String(value).replace(/[^\w-]/g, '');
    if (node.classList.contains('reply-text')) return ['.reply-text'];
    if (node.classList.contains('thread-title')) return ['.thread-title'];
    const id = node.getAttribute('data-id');
    if (node.classList.contains('edit-text')) return ['.edit-text[data-id="' + clean(id) + '"]'];
    const action = node.getAttribute('data-action');
    if (!action) return [];
    let base = '[data-action="' + clean(action) + '"]';
    if (id !== null) base += '[data-id="' + clean(id) + '"]';
    const key = node.getAttribute('data-key');
    if (key === null) return [base];
    // A reaction chip and its add control are the same place: a count of zero turns one into the other.
    const keyed = name => '[data-action="' + name + '"][data-id="' + clean(id) + '"][data-key="' + clean(key) + '"]';
    return [keyed('react'), keyed('add-reaction')];
  }

  function focusFirst(panel, selectors) {
    for (const sel of selectors.concat(['.reply-text', '.thread-title'])) {
      const target = panel.querySelector(sel);
      if (target) { target.focus({preventScroll: true}); return target; }
    }
    return null;
  }

  function updateCounter(panel) {
    const ta = panel.querySelector('.reply-text');
    const counter = panel.querySelector('[data-slot="counter"]');
    if (!ta || !counter) return;
    const n = ta.value.length;
    counter.hidden = n < REPLY_COUNTER_FROM;
    counter.textContent = n + ' / ' + REPLY_LIMIT;
  }

  // Puts the reader's unsent work back into a freshly built panel: the reply draft, who it replies to,
  // the refusal line, the sending state and the comment being edited.
  function restoreDraft(panel, t) {
    const comments = t.view.comments;
    const ta = panel.querySelector('.reply-text');
    if (ta) {
      ta.value = t.draft.text;
      const target = t.draft.replyTo && comments.find(c => c.id === t.draft.replyTo.id && !c.removed);
      if (!target) t.draft.replyTo = null;
      const field = panel.querySelector('.reply-field');
      if (t.draft.replyTo) field.parentNode.insertBefore(R.replyingTo(document, t.draft.replyTo.name), field);
      if (t.draft.error) {
        const p = document.createElement('p');
        p.className = 'field-error reply-error';
        p.setAttribute('role', 'alert');
        p.textContent = t.draft.error;
        field.parentNode.insertBefore(p, field.nextSibling);
      }
      const send = panel.querySelector('[data-action="send-comment"]');
      send.disabled = t.sending;
      send.setAttribute('aria-busy', t.sending ? 'true' : 'false');
      send.textContent = t.sending ? 'Sending' : 'Send';
      updateCounter(panel);
    }
    if (t.editing) {
      const c = comments.find(x => x.id === t.editing.id && !x.removed);
      const article = c && panel.querySelector('article.comment[data-id="' + String(c.id) + '"]');
      const body = article && article.querySelector('.comment-text');
      if (!body) {
        t.editing = null;
      } else {
        body.replaceWith(R.editForm(document, c, t.editing.text, t.editing.error));
        const acts = article.querySelector('.comment-acts');
        if (acts) acts.hidden = true;
      }
    }
  }

  // Builds the panel from the thread view. The scroll position and the focused control survive; focus can be
  // given as a list of selectors (the control that was used), else the current one is kept.
  function renderThread(focus) {
    const t = state.thread;
    const old = els.slot.querySelector('.thread');
    const sameThread = old && old.getAttribute('data-id') === String(t.id) && t.view;
    const scroll = sameThread && old.querySelector('.tbody') ? old.querySelector('.tbody').scrollTop : 0;
    const active = document.activeElement;
    const wasFocused = sameThread && old.contains(active) ? selectorFor(active) : [];
    const selection = wasFocused.length && typeof active.selectionStart === 'number' ? [active.selectionStart, active.selectionEnd] : null;
    const panel = R.threadPanel(document, t.view, new Date());
    restoreDraft(panel, t);
    showPanel(panel);
    const body = panel.querySelector('.tbody');
    if (body) body.scrollTop = scroll;
    if (t.first) { t.first = false; panel.querySelector('.thread-title').focus(); return; }
    const target = focus ? focusFirst(panel, focus) : wasFocused.length ? focusFirst(panel, wasFocused) : null;
    if (target && !focus && selection && typeof target.setSelectionRange === 'function') target.setSelectionRange(selection[0], selection[1]);
  }

  function threadFailure(t, err, mode) {
    if (err.status === 401) { askName(); return; }
    if (err.status === 404) {
      showPanel(R.threadMessage(document, t.id, 'missing'));
      if (mode === 'open') els.slot.querySelector('.thread-title').focus();
      return;
    }
    if (mode === 'poll') { console.warn('thread refresh failed:', err.message); return; }
    if (mode === 'open') showPanel(R.threadMessage(document, t.id, 'failed'));
    showError(err.message, () => fetchThread(mode));
  }

  // mode: 'open' (first load), 'write' (after a change) or 'poll' (background; a failure only warns and
  // the next poll tries again).
  async function fetchThread(mode, focus) {
    const t = state.thread;
    if (!t) return;
    const seq = ++t.seq;
    let view;
    try {
      view = await api('GET', '/api/threads/' + t.id);
    } catch (err) {
      if (state.thread === t && seq === t.seq) threadFailure(t, err, mode);
      return;
    }
    if (state.thread !== t || seq !== t.seq) return;
    clearError();
    t.view = view;
    renderThread(focus);
    if (mode === 'open') markRead(t.id);
  }

  function refreshOpenThread() {
    if (state.thread && state.thread.view) fetchThread('poll');
  }

  async function markRead(id) {
    try {
      const data = await api('POST', '/api/threads/' + id + '/read', {});
      applyUnread(data.unread);
      for (const dot of els.threads.querySelectorAll('.thread-row[data-id="' + String(id).replace(/\D/g, '') + '"] .dot')) dot.remove();
    } catch (err) {
      console.warn('marking the thread read failed:', err.message); // the badges are corrected by the next poll
    }
  }

  function openThread(id) {
    if (state.threadId === id) { state.pendingOpener = null; return; }
    state.threadId = id;
    state.thread = {id, view: null, seq: 0, first: true, sending: false, editing: null,
      draft: {text: '', replyTo: null, error: ''}, opener: state.pendingOpener || null};
    state.pendingOpener = null;
    clearError();
    showPanel(R.threadLoading(document, id));
    els.slot.querySelector('.thread-title').focus();
    return fetchThread('open');
  }

  function closePanel() {
    const t = state.thread;
    state.threadId = null;
    state.thread = null;
    els.slot.hidden = true;
    els.slot.textContent = '';
    els.app.classList.remove('has-thread');
    setInert();
    const opener = t && t.opener;
    if (opener && opener.isConnected) opener.focus();
    else els.title.focus();
  }

  // One change in the open thread, then a re-read; focus goes to `focus` (selectors of the control used).
  async function threadWrite(call, focus, onRefusal) {
    const t = state.thread;
    try {
      await call();
    } catch (err) {
      if (err.status === 401) askName();
      else if (state.thread === t && onRefusal) onRefusal(err);
      else if (state.thread === t) showError(err.message, () => threadWrite(call, focus, onRefusal));
      return false;
    }
    if (state.thread === t) await fetchThread('write', focus);
    return true;
  }

  async function sendReply() {
    const t = state.thread;
    const sent = t.draft.text;
    if (t.sending) return;
    if (!sent.trim()) { t.draft.error = 'Write something first.'; renderThread(['.reply-text']); return; }
    t.sending = true;
    t.draft.error = '';
    renderThread(['.reply-text']);
    const body = {text: sent};
    if (t.draft.replyTo) body.parent = t.draft.replyTo.id;
    await threadWrite(
      async () => {
        try {
          await api('POST', '/api/threads/' + t.id + '/comments', body);
        } finally {
          t.sending = false;
        }
        // Sent: the draft goes, unless more was typed while it was sending.
        if (t.draft.text === sent) t.draft = {text: '', replyTo: null, error: ''};
      },
      ['.reply-text'],
      err => { t.draft.error = err.message; renderThread(['.reply-text']); });
  }

  async function saveEdit(id) {
    const t = state.thread;
    if (!t.editing || t.editing.id !== id) return;
    const editButton = '[data-action="edit-comment"][data-id="' + id + '"]';
    await threadWrite(
      async () => {
        await api('POST', '/api/comments/' + id, {text: t.editing.text});
        t.editing = null;
      },
      [editButton],
      err => { t.editing.error = err.message; renderThread(['.edit-text[data-id="' + id + '"]']); });
  }

  function commentById(id) {
    return state.thread.view.comments.find(c => String(c.id) === String(id));
  }

  function onThreadClick(event) {
    const b = event.target.closest('[data-action]');
    const t = state.thread;
    if (!b || !t) return;
    const action = b.getAttribute('data-action');
    const id = b.getAttribute('data-id');
    const used = selectorFor(b);
    if (action === 'close-thread') navigate({group: state.groupId, thread: null});
    else if (!t.view) return;
    else if (action === 'send-comment') sendReply();
    else if (action === 'reply') {
      const c = commentById(id);
      if (c) { t.draft.replyTo = {id: c.id, name: c.author}; renderThread(['.reply-text']); }
    } else if (action === 'cancel-reply') { t.draft.replyTo = null; renderThread(['.reply-text']); }
    else if (action === 'edit-comment') {
      const c = commentById(id);
      if (c) { t.editing = {id: c.id, text: c.text, error: ''}; renderThread(['.edit-text[data-id="' + id + '"]']); }
    } else if (action === 'cancel-edit') { t.editing = null; renderThread(['[data-action="edit-comment"][data-id="' + id + '"]']); }
    else if (action === 'save-edit') saveEdit(Number(id));
    else if (action === 'delete-comment') {
      if (window.confirm('Delete this comment?')) threadWrite(() => api('DELETE', '/api/comments/' + id), []);
    } else if (action === 'react' || action === 'add-reaction') {
      const remove = action === 'react' && b.getAttribute('aria-pressed') === 'true';
      threadWrite(() => api(remove ? 'DELETE' : 'POST', '/api/comments/' + id + '/reactions/' + b.getAttribute('data-key')), used);
    }
  }

  function onThreadInput(event) {
    const t = state.thread;
    const ta = event.target;
    if (!t || !ta.classList) return;
    if (ta.classList.contains('reply-text')) {
      t.draft.text = ta.value;
      if (t.draft.error) {
        t.draft.error = '';
        const err = els.slot.querySelector('.reply-error');
        if (err) err.remove();
      }
      updateCounter(els.slot);
    } else if (ta.classList.contains('edit-text') && t.editing) {
      t.editing.text = ta.value;
    }
  }

  // Enter adds a line; Ctrl or Cmd with Enter sends or saves; Escape leaves an edit.
  function onThreadKey(event) {
    const t = state.thread;
    const ta = event.target;
    if (!t || !ta.classList) return;
    const submit = event.key === 'Enter' && (event.ctrlKey || event.metaKey);
    if (ta.classList.contains('reply-text') && submit) { event.preventDefault(); sendReply(); }
    else if (ta.classList.contains('edit-text') && submit) { event.preventDefault(); saveEdit(t.editing.id); }
    else if (ta.classList.contains('edit-text') && event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      const id = t.editing.id;
      t.editing = null;
      renderThread(['[data-action="edit-comment"][data-id="' + id + '"]']);
    }
  }

  // ----- dialogs: native dialog elements; focus returns to the opener
  function openDialog(parts, opener) {
    state.dialogOpener = opener || document.activeElement;
    parts.error.hidden = true;
    parts.error.textContent = '';
    parts.submit.disabled = false;
    parts.dialog.showModal();
  }

  function dialogError(parts, message) {
    parts.error.textContent = message;
    parts.error.hidden = false;
    parts.submit.disabled = false;
  }

  function wireDialog(parts, id, onSubmit) {
    $(id + '-close').addEventListener('click', () => parts.dialog.close());
    $(id + '-cancel').addEventListener('click', () => parts.dialog.close());
    parts.dialog.addEventListener('close', () => {
      const opener = state.dialogOpener;
      if (opener && opener.isConnected && state.me) opener.focus();
    });
    parts.form.addEventListener('submit', event => {
      event.preventDefault();
      if (!parts.submit.disabled) onSubmit();
    });
  }

  async function submitDialog(parts, call, done) {
    parts.submit.disabled = true;
    parts.error.hidden = true;
    try {
      const data = await call();
      // Focus moves on to what the dialog made (a thread or a group), so it does not return to the opener now;
      // a thread opened from here returns focus to that opener when it closes.
      state.pendingOpener = state.dialogOpener;
      state.dialogOpener = null;
      parts.dialog.close();
      done(data);
    } catch (err) {
      if (err.status === 401) { parts.dialog.close(); askName(); return; }
      dialogError(parts, err.message);
    }
  }

  async function openShare(storyId, opener) {
    state.shareStory = storyId;
    SHARE.note.value = '';
    SHARE.groups.textContent = 'Loading groups';
    SHARE.submit.hidden = false;
    SHARE.box.setAttribute('aria-busy', 'true');
    openDialog(SHARE, opener);
    try {
      const data = await api('GET', '/api/groups');
      state.groups = data.groups;
      state.canCreate = Boolean(data.can_create);
      SHARE.groups.textContent = '';
      SHARE.groups.appendChild(R.groupChoices(document, data.groups, state.canCreate));
      SHARE.submit.hidden = data.groups.length === 0;
      const first = SHARE.groups.querySelector('input, button');
      if (first) first.focus();
    } catch (err) {
      SHARE.groups.textContent = '';
      dialogError(SHARE, err.message);
    } finally {
      SHARE.box.setAttribute('aria-busy', 'false');
    }
  }

  function submitShare() {
    const chosen = SHARE.form.querySelector('input[name="share-group"]:checked');
    if (!chosen) { dialogError(SHARE, 'Choose a group.'); return; }
    const body = {story_id: Number(state.shareStory)};
    const note = SHARE.note.value.trim();
    if (note) body.note = note;
    submitDialog(SHARE, () => api('POST', '/api/groups/' + chosen.value + '/threads', body), data => {
      announce('Shared to the group');
      loadGroups(true);
      navigate({group: state.groupId, thread: String(data.thread_id)});
    });
  }

  function openGroupDialog(opener) {
    GROUP.name.value = '';
    GROUP.visibility.textContent = '';
    GROUP.visibility.appendChild(R.visibilityChoices(document));
    GROUP.topics.textContent = '';
    GROUP.topics.appendChild(R.topicChoices(document, state.topics));
    openDialog(GROUP, opener);
    GROUP.name.focus();
  }

  function submitGroup() {
    const name = GROUP.name.value.trim();
    if (!name) { dialogError(GROUP, 'Enter a name for the group.'); GROUP.name.focus(); return; }
    const visibility = GROUP.form.querySelector('input[name="group-visibility"]:checked').value;
    const topics = Array.from(GROUP.form.querySelectorAll('input[name="group-topic"]:checked')).map(i => Number(i.value));
    submitDialog(GROUP, () => api('POST', '/api/groups', {name, visibility, topics}), data => {
      announce('Group created');
      loadGroups(true);
      state.pendingOpener = null;
      navigate({group: String(data.id), thread: state.threadId});
      els.title.focus();
    });
  }

  function openNoteDialog(opener) {
    state.noteGroup = state.groupId;
    NOTE.title.value = '';
    NOTE.text.value = '';
    openDialog(NOTE, opener);
    NOTE.title.focus();
  }

  function submitNote() {
    const title = NOTE.title.value.trim();
    const text = NOTE.text.value.trim();
    if (!title || !text) { dialogError(NOTE, 'Enter a title and some text.'); return; }
    const gid = state.noteGroup;
    submitDialog(NOTE, () => api('POST', '/api/groups/' + gid + '/threads', {title, text}), data => {
      announce('Note started');
      if (state.groupId === gid) reloadThreads();
      loadGroups(true);
      navigate({group: state.groupId, thread: String(data.thread_id)});
    });
  }

  // New group from the share dialog: the share dialog closes, the group dialog returns focus to the same opener.
  function newGroupFrom(button) {
    let opener = button;
    if (SHARE.dialog.contains(button)) {
      opener = state.dialogOpener;
      SHARE.dialog.close();
    }
    openGroupDialog(opener);
  }

  // ----- name
  function renderMe() {
    const name = state.me ? state.me.name : null;
    els.meName.textContent = name || 'Set your name';
    els.meInitials.textContent = name ? R.initials(name) : '?';
    const role = state.me && state.me.role;
    els.meRole.textContent = role || '';
    els.meRole.hidden = !role;
  }

  function askName() {
    els.cancel.hidden = !state.me;
    els.nameError.hidden = true;
    els.input.value = state.me ? state.me.name : '';
    if (!els.dialog.open) els.dialog.showModal();
    els.input.focus();
  }

  async function refreshMe() {
    const me = await api('GET', '/api/me');
    state.me = me.name ? me : null;
    renderMe();
    return state.me;
  }

  async function start() {
    const statusDone = loadStatus();
    try {
      if (!(await refreshMe())) { askName(); return; }
    } catch (err) {
      showError(err.message, start);
      return;
    }
    await loadTopics();
    await Promise.all([loadGroups(false), refreshUnread()]);
    await statusDone; // the approved count is known (or known to be unavailable) before the first feed message
    const route = parseRoute();
    if (route.group !== null) await openGroup(route.group);
    else await setView(state.view);
    if (route.thread !== null) openThread(route.thread);
  }

  async function submitName(event) {
    event.preventDefault();
    const name = els.input.value.trim();
    if (!name) {
      els.nameError.textContent = 'Enter a name to continue.';
      els.nameError.hidden = false;
      els.input.focus();
      return;
    }
    try {
      await api('POST', '/api/me', {name});
    } catch (err) {
      els.nameError.textContent = err.message;
      els.nameError.hidden = false;
      els.input.focus();
      return;
    }
    try {
      await refreshMe();
    } catch (err) {
      els.nameError.textContent = err.message;
      els.nameError.hidden = false;
      return;
    }
    els.dialog.close();
    announce('Signed in as ' + state.me.name);
    // Saved stories and followed topics belong to the name, so everything is read again.
    await loadTopics();
    await Promise.all([loadGroups(false), refreshUnread()]);
    if (state.groupId !== null) await openGroup(state.groupId);
    else await setView(state.view);
    if (state.thread) fetchThread('write');
  }

  // ----- events
  els.dialog.addEventListener('cancel', event => { if (!state.me) event.preventDefault(); });
  // Some browsers close a modal dialog on a second Escape even when cancel was prevented.
  els.dialog.addEventListener('close', () => { if (!state.me) askName(); });
  els.form.addEventListener('submit', submitName);
  els.cancel.addEventListener('click', () => els.dialog.close());
  els.chip.addEventListener('click', askName);
  els.channelsToggle.addEventListener('click', () => setChannelsOpen(els.channelsToggle.getAttribute('aria-expanded') !== 'true'));
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || document.querySelector('dialog[open]') || els.channelsToggle.getAttribute('aria-expanded') !== 'true') return;
    setChannelsOpen(false);
    els.channelsToggle.focus();
  });
  document.addEventListener('click', event => {
    if (els.channelsToggle.getAttribute('aria-expanded') !== 'true') return;
    if (els.channels.contains(event.target) || els.channelsToggle.contains(event.target)) return;
    setChannelsOpen(false);
  });
  els.retry.addEventListener('click', () => { if (state.retry) state.retry(); });
  els.more.addEventListener('click', () => { if (state.groupId !== null) moreThreads(); else load(false); });
  els.pill.addEventListener('click', async () => {
    if (await load(true) && els.cards.firstElementChild) els.cards.firstElementChild.focus();
  });

  els.channels.addEventListener('click', event => {
    const follow = event.target.closest('[data-follow]');
    if (follow) { toggleFollow(follow.getAttribute('data-follow')); return; }
    const group = event.target.closest('[data-action="open-group"]');
    if (group) { setChannelsOpen(false); navigate({group: group.getAttribute('data-id'), thread: state.threadId}); return; }
    const create = event.target.closest('[data-action="new-group"]');
    if (create) { setChannelsOpen(false); newGroupFrom(create); return; }
    const view = event.target.closest('[data-view]');
    if (!view) return;
    if (state.groupId !== null) navigate({group: null, thread: state.threadId}, false);
    setView(view.getAttribute('data-view'));
  });
  els.empty.addEventListener('click', event => {
    const follow = event.target.closest('[data-follow]');
    if (follow) toggleFollow(follow.getAttribute('data-follow'));
  });
  function openThreadFrom(button) {
    state.pendingOpener = button;
    navigate({group: state.groupId, thread: button.getAttribute('data-id')});
  }
  els.cards.addEventListener('click', event => {
    const save = event.target.closest('[data-action="save"]');
    if (save) { toggleSave(save); return; }
    const share = event.target.closest('[data-action="share"]');
    if (share) { openShare(share.getAttribute('data-id'), share); return; }
    const chip = event.target.closest('[data-action="open-thread"]');
    if (chip) openThreadFrom(chip);
  });
  els.threads.addEventListener('click', event => {
    const row = event.target.closest('[data-action="open-thread"]');
    if (row) openThreadFrom(row);
  });
  els.groupHead.addEventListener('click', onGroupHeadClick);
  els.groupHead.addEventListener('submit', onAddMember);
  els.slot.addEventListener('click', onThreadClick);
  els.slot.addEventListener('input', onThreadInput);
  els.slot.addEventListener('keydown', onThreadKey);
  SHARE.groups.addEventListener('click', event => {
    const create = event.target.closest('[data-action="new-group"]');
    if (create) newGroupFrom(create);
  });
  wireDialog(SHARE, 'share-dialog', submitShare);
  wireDialog(GROUP, 'group-dialog', submitGroup);
  wireDialog(NOTE, 'note-dialog', submitNote);
  window.addEventListener('popstate', applyRoute);
  NARROW.addEventListener('change', setInert);
  // Escape closes the panel when focus is inside it and no dialog is open (an edit takes Escape first).
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || event.defaultPrevented || state.threadId === null || document.querySelector('dialog[open]')) return;
    if (els.slot.contains(document.activeElement)) navigate({group: state.groupId, thread: null});
  });
  els.kindChips.addEventListener('click', event => {
    const chip = event.target.closest('.chip');
    if (!chip) return;
    state.kind = chip.getAttribute('data-kind');
    syncKindChips();
    load(true);
  });

  function runSearch() {
    window.clearTimeout(state.searchTimer);
    const q = els.search.value.trim();
    if (q === state.q) return;
    state.q = q;
    load(true);
  }
  els.search.addEventListener('input', () => {
    window.clearTimeout(state.searchTimer);
    state.searchTimer = window.setTimeout(runSearch, SEARCH_DEBOUNCE_MS);
  });
  els.search.addEventListener('keydown', event => {
    if (event.key === 'Enter') { event.preventDefault(); runSearch(); }
    if (event.key === 'Escape' && els.search.value) { els.search.value = ''; runSearch(); }
  });
  document.addEventListener('keydown', event => {
    if (event.key !== '/' || event.ctrlKey || event.metaKey || event.altKey || document.querySelector('dialog[open]')) return;
    const t = event.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return;
    event.preventDefault();
    els.search.focus();
  });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') poll(); });

  state.pollTimer = window.setInterval(poll, POLL_MS);
  start();
})();

'use strict';
// The Signal feed page: state, API calls and event wiring. Card markup comes from render.js; this file
// builds no HTML from data (text goes in with textContent only).
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
  };

  const state = {
    view: 'foryou', kind: '', q: '', next: null, shown: 0, topics: [], approved: undefined,
    me: null, seq: 0, loading: false, lastLoad: null, retry: null, pollTimer: null, searchTimer: null,
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
    try {
      data = await res.json();
    } catch (err) {
      data = null; // a body that is not JSON is reported below by status
    }
    if (!res.ok) {
      const message = data && typeof data.error === 'string' ? data.error : 'Signal could not complete that request.';
      throw new ApiError(res.status, message);
    }
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
    for (const story of list) els.cards.appendChild(R.card(document, story, now));
    state.shown += list.length;
  }

  // Loads the current view. reset: replace the list (skeletons while waiting); otherwise append the
  // next page. On failure the last good list stays and the error band offers Retry.
  async function load(reset) {
    const seq = ++state.seq;
    const started = new Date();
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
      if (reset) { state.lastLoad = started; hidePill(); }
      renderEmpty();
      announce(state.shown === 0 ? 'No stories' : state.shown + (state.shown === 1 ? ' story' : ' stories') + ' shown');
      if (!reset && els.cards.children[firstNew]) els.cards.children[firstNew].focus();
      return true;
    } catch (err) {
      if (seq !== state.seq) return false;
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
    state.view = view;
    state.kind = '';
    state.q = '';
    els.search.value = '';
    syncKindChips();
    for (const b of document.querySelectorAll('.ch[data-view]')) {
      if (b.getAttribute('data-view') === view) b.setAttribute('aria-current', 'page');
      else b.removeAttribute('aria-current');
    }
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
      if (state.view === 'topic:' + topic.id) view.setAttribute('aria-current', 'page');
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
    try {
      const data = await api(topic.following ? 'DELETE' : 'POST', '/api/topics/' + encodeURIComponent(id) + '/follow');
      topic.following = data.following;
      renderTopics();
      for (const b of els.empty.querySelectorAll('[data-follow]'))
        if (b.getAttribute('data-follow') === String(id)) b.setAttribute('aria-pressed', data.following ? 'true' : 'false');
      announce((data.following ? 'Following ' : 'Unfollowed ') + topic.name);
      if (state.view === 'foryou') await load(true);
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

  // ----- new-stories poll. Fail-open by design: a failed poll only means no pill this round; the next
  // poll tries again, and the feed itself reports its own failures in the error band.
  async function poll() {
    if (document.visibilityState === 'hidden' || !state.me || !state.lastLoad || state.loading) return;
    loadStatus();
    try {
      const params = new URLSearchParams({view: state.view, since: state.lastLoad.toISOString()});
      const data = await api('GET', '/api/feed/new?' + params);
      if (data.count > 0) {
        els.pill.textContent = data.count + (data.count === 1 ? ' new story' : ' new stories');
        if (els.pill.hidden) announce(els.pill.textContent);
        els.pill.hidden = false;
      }
    } catch (err) {
      console.warn('new-story poll failed:', err.message);
    }
  }

  // ----- name
  function renderMe() {
    const name = state.me ? state.me.name : null;
    els.meName.textContent = name || 'Set your name';
    els.meInitials.textContent = name ? name.trim().slice(0, 2).toUpperCase() : '?';
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
    loadStatus();
    try {
      if (!(await refreshMe())) { askName(); return; }
    } catch (err) {
      showError(err.message, start);
      return;
    }
    await loadTopics();
    await setView(state.view);
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
    await setView(state.view);
  }

  // ----- events
  els.dialog.addEventListener('cancel', event => { if (!state.me) event.preventDefault(); });
  // Some browsers close a modal dialog on a second Escape even when cancel was prevented.
  els.dialog.addEventListener('close', () => { if (!state.me) askName(); });
  els.form.addEventListener('submit', submitName);
  els.cancel.addEventListener('click', () => els.dialog.close());
  els.chip.addEventListener('click', askName);
  els.channelsToggle.addEventListener('click', () => setChannelsOpen(els.channelsToggle.getAttribute('aria-expanded') !== 'true'));
  els.retry.addEventListener('click', () => { if (state.retry) state.retry(); });
  els.more.addEventListener('click', () => load(false));
  els.pill.addEventListener('click', async () => {
    if (await load(true) && els.cards.firstElementChild) els.cards.firstElementChild.focus();
  });

  els.channels.addEventListener('click', event => {
    const follow = event.target.closest('[data-follow]');
    if (follow) { toggleFollow(follow.getAttribute('data-follow')); return; }
    const view = event.target.closest('[data-view]');
    if (view) setView(view.getAttribute('data-view'));
  });
  els.empty.addEventListener('click', event => {
    const follow = event.target.closest('[data-follow]');
    if (follow) toggleFollow(follow.getAttribute('data-follow'));
  });
  els.cards.addEventListener('click', event => {
    const save = event.target.closest('[data-action="save"]');
    if (save) toggleSave(save);
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
    if (event.key !== '/' || event.ctrlKey || event.metaKey || event.altKey || els.dialog.open) return;
    const t = event.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return;
    event.preventDefault();
    els.search.focus();
  });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') poll(); });

  state.pollTimer = window.setInterval(poll, POLL_MS);
  start();
})();

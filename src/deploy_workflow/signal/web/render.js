'use strict';
// Rendering of Signal feed cards and empty states. One file for the browser (window.SignalRender) and
// node (module.exports). Every function takes the document as a parameter and touches no global at
// load time. All feed text goes in with textContent or setAttribute, never as markup.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SignalRender = api;
})(typeof self !== 'undefined' ? self : this, function () {
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const KINDS = {regulator: 'Regulator', news: 'News', ratings: 'Ratings', research: 'Research'};
  const REACTIONS = [
    {key: 'up', emoji: '👍', name: 'Thumbs up'},
    {key: 'eyes', emoji: '👀', name: 'Eyes'},
    {key: 'check', emoji: '✅', name: 'Check'},
    {key: 'question', emoji: '❓', name: 'Question'},
  ];
  const EDIT_RULE = 'You can edit a comment for 15 minutes.';
  const IDENTITY_NOTE = 'Names are not checked: anyone on this network can post under any name.';
  const ROLE_TAGS = {writer: 'Writer', owner: 'Owner'};
  const ICONS = {
    bookmark: 'M6 3h12v18l-6-4-6 4z',
    external: 'M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5',
    layers: 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5',
    star: 'M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z',
    hash: 'M5 9h14M5 15h14M10 4L8 20M16 4l-2 16',
    lock: 'M7 11V8a5 5 0 0 1 10 0v3M5 11h14v9H5z',
    share: 'M4 12v7h16v-7M12 3v12M8 7l4-4 4 4',
    message: 'M4 5h16v11H9l-5 4z',
    close: 'M6 6l12 12M18 6L6 18',
    plus: 'M12 5v14M5 12h14',
  };

  function icon(doc, name) {
    const svg = doc.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('class', 'ico');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    const path = doc.createElementNS(SVG_NS, 'path');
    path.setAttribute('d', ICONS[name]);
    svg.appendChild(path);
    return svg;
  }

  function parseTime(iso) {
    if (iso === null || iso === undefined || iso === '') return null;
    const t = new Date(iso);
    return Number.isNaN(t.getTime()) ? null : t;
  }

  function dateText(t) {
    return t.getUTCDate() + ' ' + MONTHS[t.getUTCMonth()] + ' ' + t.getUTCFullYear();
  }

  function relativeTime(iso, now) {
    const t = parseTime(iso);
    if (!t) return '';
    const minutes = Math.floor((now.getTime() - t.getTime()) / 60000);
    if (minutes < 1) return 'just now';
    if (minutes < 60) return minutes + ' min ago';
    if (minutes < 60 * 24) return Math.floor(minutes / 60) + ' h ago';
    if (minutes < 60 * 24 * 7) return Math.floor(minutes / (60 * 24)) + ' d ago';
    return dateText(t);
  }

  function fullTime(iso) {
    const t = parseTime(iso);
    if (!t) return '';
    const pad = n => String(n).padStart(2, '0');
    return dateText(t) + ' ' + pad(t.getUTCHours()) + ':' + pad(t.getUTCMinutes()) + ' UTC';
  }

  function safeLink(url) {
    if (typeof url !== 'string') return null;
    let parsed;
    try {
      parsed = new URL(url); // a URL that needs a base throws and is refused
    } catch (err) {
      return null; // not a URL: the story is shown without a link
    }
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.href : null;
  }

  function el(doc, tag, className, text) {
    const e = doc.createElement(tag);
    if (className) e.setAttribute('class', className);
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }

  // Kind of a story or source: the class key and the label shown in words.
  function kindInfo(kind) {
    const known = Object.prototype.hasOwnProperty.call(KINDS, kind);
    return {key: known ? kind : 'other', label: known ? KINDS[kind] : String(kind || 'Story')};
  }

  // A story title as an external link when its address is safe, else as plain text.
  function titleInto(doc, parent, link, title) {
    const href = safeLink(link);
    if (href) parent.appendChild(externalLink(doc, href, 'headline-link', title));
    else parent.textContent = title;
    return href;
  }

  function monogram(source) {
    const words = String(source || '?').trim().split(/\s+/).filter(Boolean);
    const letters = words.length > 1 ? words[0][0] + words[1][0] : (words[0] || '?').slice(0, 2);
    return letters.toUpperCase();
  }

  // Avatar letters: the first character of up to two words that start with a letter or digit.
  function initials(name) {
    const words = String(name || '').split(/\s+/).filter(w => /^[\p{L}\p{N}]/u.test(w));
    if (words.length === 0) return '?';
    return words.slice(0, 2).map(w => Array.from(w)[0]).join('').toUpperCase();
  }

  function externalLink(doc, href, className, text, label) {
    const a = el(doc, 'a', className, text);
    a.setAttribute('href', href);
    a.setAttribute('target', '_blank');
    a.setAttribute('rel', 'noopener noreferrer');
    if (label) a.setAttribute('aria-label', label);
    return a;
  }

  function card(doc, story, now, opts) {
    const canShare = Boolean(opts && opts.canShare);
    const {key: kind, label: kindLabel} = kindInfo(story.kind);
    const article = el(doc, 'article', 'card card-' + kind);
    article.setAttribute('data-id', String(story.id));
    article.setAttribute('tabindex', '-1');

    const threads = Array.isArray(story.threads) ? story.threads : [];
    const shared = threads.find(t => t.shared_by);
    if (shared) article.appendChild(sharedLine(doc, shared));
    article.appendChild(el(doc, 'span', 'kind', kindLabel));

    const h3 = el(doc, 'h3', 'headline');
    const href = titleInto(doc, h3, story.link, story.title);
    article.appendChild(h3);

    const meta = el(doc, 'p', 'meta');
    const mono = el(doc, 'span', 'src', monogram(story.source));
    mono.setAttribute('aria-hidden', 'true');
    meta.appendChild(mono);
    meta.appendChild(el(doc, 'span', 'src-name', story.source));
    // The frozen card probe expects a time element even when the time is unknown; it is then empty and hidden.
    const when = el(doc, 'time', 'when', relativeTime(story.published_at, now));
    if (parseTime(story.published_at)) {
      when.setAttribute('datetime', String(story.published_at));
      when.setAttribute('title', fullTime(story.published_at));
    } else {
      when.setAttribute('hidden', '');
    }
    meta.appendChild(when);
    article.appendChild(meta);

    if (story.summary) article.appendChild(el(doc, 'p', 'summary', story.summary));

    if (story.topics && story.topics.length) {
      const tags = el(doc, 'ul', 'tags');
      for (const name of story.topics) tags.appendChild(el(doc, 'li', 'tag', name));
      article.appendChild(tags);
    }
    if (story.other_sources > 0) {
      const also = el(doc, 'p', 'also');
      also.appendChild(icon(doc, 'layers'));
      also.appendChild(el(doc, 'span', null,
        'Also in ' + story.other_sources + ' other ' + (story.other_sources === 1 ? 'source' : 'sources')));
      article.appendChild(also);
    }

    if (threads.length) article.appendChild(threadChips(doc, story));

    const acts = el(doc, 'div', 'acts');
    const save = el(doc, 'button', 'act save');
    save.setAttribute('type', 'button');
    save.setAttribute('data-action', 'save');
    save.setAttribute('aria-pressed', story.saved ? 'true' : 'false');
    save.setAttribute('aria-label', 'Save: ' + story.title);
    save.appendChild(icon(doc, 'bookmark'));
    save.appendChild(el(doc, 'span', null, 'Save'));
    acts.appendChild(save);
    if (canShare) {
      const share = el(doc, 'button', 'act share');
      share.setAttribute('type', 'button');
      share.setAttribute('data-action', 'share');
      share.setAttribute('data-id', String(story.id));
      share.appendChild(icon(doc, 'share'));
      share.appendChild(el(doc, 'span', null, 'Share to group'));
      acts.appendChild(share);
    }
    if (href) {
      const open = externalLink(doc, href, 'act open', null, 'Open source: ' + story.title + ' (opens in a new tab)');
      open.appendChild(el(doc, 'span', null, 'Open source'));
      open.appendChild(icon(doc, 'external'));
      acts.appendChild(open);
    }
    article.appendChild(acts);
    return article;
  }

  function plural(n, one, many) {
    return n + ' ' + (n === 1 ? one : many);
  }

  function srOnly(doc, text) {
    return el(doc, 'span', 'sr-only', text);
  }

  // The first line of a note, for the card's shared line.
  function firstLine(text) {
    return String(text || '').split('\n')[0].trim();
  }

  // Who shared a story where, with the first line of the note. Data: {group, shared_by, note}.
  function sharedLine(doc, thread) {
    const line = el(doc, 'p', 'shared');
    const av = el(doc, 'span', 'av', initials(thread.shared_by));
    av.setAttribute('aria-hidden', 'true');
    line.appendChild(av);
    const text = el(doc, 'span', 'shared-text');
    text.appendChild(el(doc, 'strong', null, thread.shared_by));
    text.appendChild(doc.createTextNode(' shared to '));
    text.appendChild(el(doc, 'strong', null, thread.group));
    const note = firstLine(thread.note);
    if (note) text.appendChild(doc.createTextNode(' · “' + note + '”'));
    line.appendChild(text);
    return line;
  }

  // One chip per thread on a card: button[data-action=open-thread][data-id=<thread id>].
  function threadChips(doc, story) {
    const list = el(doc, 'ul', 'thread-chips');
    for (const t of Array.isArray(story.threads) ? story.threads : []) {
      const li = el(doc, 'li');
      const b = el(doc, 'button', 'chip thread-chip');
      b.setAttribute('type', 'button');
      b.setAttribute('data-action', 'open-thread');
      b.setAttribute('data-id', String(t.id));
      b.appendChild(icon(doc, 'message'));
      b.appendChild(el(doc, 'span', null, t.group + ' · ' + plural(t.comments, 'comment', 'comments')));
      li.appendChild(b);
      list.appendChild(li);
    }
    return list;
  }

  // Plain text to a fragment: only http(s) runs that safeLink accepts become links; trailing punctuation
  // stays outside; newlines become br.
  function linkify(doc, text) {
    const frag = doc.createDocumentFragment();
    const lines = String(text === null || text === undefined ? '' : text).split('\n');
    lines.forEach((line, i) => {
      if (i > 0) frag.appendChild(doc.createElement('br'));
      const re = /https?:\/\/[^\s<>"']+/g;
      let last = 0;
      let m;
      while ((m = re.exec(line)) !== null) {
        const url = m[0].replace(/[.,;:!?)]+$/, '');
        const href = safeLink(url);
        if (!href) continue;
        if (m.index > last) frag.appendChild(doc.createTextNode(line.slice(last, m.index)));
        frag.appendChild(externalLink(doc, href, 'text-link', url));
        last = m.index + url.length;
        re.lastIndex = last;
      }
      if (last < line.length) frag.appendChild(doc.createTextNode(line.slice(last)));
    });
    return frag;
  }

  function button(doc, className, label, action, id) {
    const b = el(doc, 'button', className, label);
    b.setAttribute('type', 'button');
    b.setAttribute('data-action', action);
    b.setAttribute('data-id', String(id));
    return b;
  }

  // Reactions: chips for counts above zero (button[data-action=react][data-id=<comment id>][data-key]; pressed
  // means DELETE, else POST), then add controls (data-action=add-reaction, same data) when the viewer can post.
  function reactions(doc, c, canPost) {
    const wrap = el(doc, 'div', 'reactions');
    const counts = new Map((c.reactions || []).map(r => [r.key, r]));
    for (const def of REACTIONS) {
      const r = counts.get(def.key);
      if (!r || !(r.count > 0)) continue;
      const chip = button(doc, 'chip react', def.emoji + ' ' + r.count, 'react', c.id);
      chip.setAttribute('data-key', def.key);
      chip.setAttribute('aria-pressed', r.mine ? 'true' : 'false');
      chip.setAttribute('aria-label', def.name + ', ' + r.count);
      if (!canPost) chip.setAttribute('disabled', '');
      wrap.appendChild(chip);
    }
    if (canPost) {
      for (const def of REACTIONS) {
        const r = counts.get(def.key);
        if (r && r.count > 0) continue;
        const add = button(doc, 'chip react-add', def.emoji, 'add-reaction', c.id);
        add.setAttribute('data-key', def.key);
        add.setAttribute('aria-label', 'Add reaction: ' + def.name);
        wrap.appendChild(add);
      }
    }
    return wrap;
  }

  // A comment. opts.canPost (default false) decides the Reply control and the add-reaction controls.
  // Emits data-action reply | edit-comment | delete-comment | react | add-reaction, data-id = comment id.
  function comment(doc, c, now, opts) {
    const canPost = Boolean(opts && opts.canPost);
    const box = el(doc, 'article', 'comment' + (c.removed ? ' removed' : ''));
    box.setAttribute('data-id', String(c.id));
    if (c.removed) {
      box.appendChild(el(doc, 'p', 'removed-text', 'This comment was removed.'));
      return box;
    }
    const av = el(doc, 'span', 'av', initials(c.author));
    av.setAttribute('aria-hidden', 'true');
    box.appendChild(av);
    const body = el(doc, 'div', 'comment-body');
    const who = el(doc, 'p', 'who');
    const author = el(doc, 'strong', 'author', c.author);
    author.setAttribute('id', 'c' + c.id + '-author');
    who.appendChild(author);
    if (Object.prototype.hasOwnProperty.call(ROLE_TAGS, c.role)) who.appendChild(el(doc, 'span', 'tag role', ROLE_TAGS[c.role]));
    const when = el(doc, 'time', 'when', relativeTime(c.created_at, now));
    if (parseTime(c.created_at)) {
      when.setAttribute('datetime', String(c.created_at));
      when.setAttribute('title', fullTime(c.created_at));
    }
    who.appendChild(when);
    if (c.edited) who.appendChild(el(doc, 'span', 'tag edited', 'edited'));
    body.appendChild(who);
    body.appendChild(el(doc, 'p', 'comment-text')).appendChild(linkify(doc, c.text));
    body.appendChild(reactions(doc, c, canPost));

    const acts = el(doc, 'div', 'comment-acts');
    const named = (cls, label, action) => {
      const b = button(doc, cls, label, action, c.id);
      b.setAttribute('id', 'c' + c.id + '-' + action);
      b.setAttribute('aria-labelledby', 'c' + c.id + '-' + action + ' c' + c.id + '-author');
      acts.appendChild(b);
    };
    if (canPost && c.parent_id === null) named('link-btn', 'Reply', 'reply');
    if (c.mine && c.editable) named('link-btn', 'Edit', 'edit-comment');
    if (c.mine) named('link-btn', 'Delete', 'delete-comment');
    if (acts.children.length) body.appendChild(acts);
    box.appendChild(body);
    return box;
  }

  function dayKey(t) {
    return t.getUTCFullYear() * 10000 + t.getUTCMonth() * 100 + t.getUTCDate();
  }

  // UTC calendar days: Today, Yesterday, else "12 Nov 2026".
  function dayLabel(t, now) {
    const days = Math.round((Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())
      - Date.UTC(t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate())) / 86400000);
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    return dateText(t);
  }

  // A day divider inside the comment list: a separator, not a list item of comments.
  function divider(doc, label) {
    const li = el(doc, 'li', 'day', label);
    li.setAttribute('role', 'separator');
    li.setAttribute('aria-label', label);
    return li;
  }

  function quoteBlock(doc, story) {
    const q = el(doc, 'div', 'quote');
    const {key, label} = kindInfo(story.kind);
    q.appendChild(el(doc, 'span', 'quote-kind card-' + key, label + ' \u00b7 ' + story.source));
    const title = el(doc, 'strong', 'quote-title');
    titleInto(doc, title, story.link, story.title);
    q.appendChild(title);
    return q;
  }

  // The hint inside an empty reply box; replyToName is set while replying to a comment.
  function replyPlaceholder(group, replyToName) {
    return replyToName ? 'Replying to ' + replyToName + '\u2026' : 'Reply to ' + group + '\u2026';
  }

  function replyBox(doc, view) {
    const box = el(doc, 'div', 'reply-box');
    const field = el(doc, 'div', 'reply-field');
    const ta = el(doc, 'textarea', 'reply-text');
    ta.setAttribute('id', 'reply-' + view.id);
    ta.setAttribute('rows', '3');
    ta.setAttribute('maxlength', '4000');
    ta.setAttribute('placeholder', replyPlaceholder(view.group, null));
    ta.setAttribute('aria-labelledby', 'reply-label-' + view.id);
    field.appendChild(ta);
    const foot = el(doc, 'div', 'reply-foot');
    const counter = el(doc, 'span', 'counter');
    counter.setAttribute('data-slot', 'counter');
    counter.setAttribute('hidden', '');
    foot.appendChild(counter);
    foot.appendChild(button(doc, 'send', 'Send', 'send-comment', view.id));
    field.appendChild(foot);
    const label = el(doc, 'label', 'sr-only', 'Reply');
    label.setAttribute('id', 'reply-label-' + view.id);
    label.setAttribute('for', 'reply-' + view.id);
    box.appendChild(label);
    box.appendChild(field);
    box.appendChild(el(doc, 'p', 'identity-note', IDENTITY_NOTE));
    box.appendChild(el(doc, 'p', 'identity-note edit-rule', EDIT_RULE));
    return box;
  }

  // The thread panel. Emits data-action close-thread (header), send-comment (data-id = thread id) and the
  // comment actions. The heading h2.thread-title carries id thread-title-<id> and tabindex -1 for focus.
  function threadPanel(doc, view, now) {
    const panel = el(doc, 'aside', 'thread');
    panel.setAttribute('aria-labelledby', 'thread-title-' + view.id);
    panel.setAttribute('data-id', String(view.id));
    const all = Array.isArray(view.comments) ? view.comments : [];

    const head = el(doc, 'div', 'thead');
    const av = el(doc, 'span', 'av', initials(view.group));
    av.setAttribute('aria-hidden', 'true');
    head.appendChild(av);
    const titles = el(doc, 'div', 'thead-text');
    const h = el(doc, 'h2', 'thread-title', view.group);
    h.setAttribute('id', 'thread-title-' + view.id);
    h.setAttribute('tabindex', '-1');
    titles.appendChild(h);
    titles.appendChild(el(doc, 'p', 'thead-sub', 'Thread · ' + plural(all.filter(c => !c.removed).length, 'comment', 'comments')));
    head.appendChild(titles);
    const close = button(doc, 'icon-btn', null, 'close-thread', view.id);
    close.setAttribute('aria-label', 'Close thread');
    close.appendChild(icon(doc, 'close'));
    head.appendChild(close);
    panel.appendChild(head);

    const body = el(doc, 'div', 'tbody');
    if (view.story) {
      body.appendChild(quoteBlock(doc, view.story));
    } else {
      const note = el(doc, 'div', 'note-head');
      note.appendChild(el(doc, 'span', 'quote-kind', 'Note'));
      note.appendChild(el(doc, 'h3', 'note-title', view.title));
      if (view.started_by) note.appendChild(el(doc, 'p', 'note-by', 'Started by ' + view.started_by));
      body.appendChild(note);
    }

    const ids = new Set(all.map(c => c.id));
    const replies = new Map();
    const tops = [];
    for (const c of all) {
      if (c.parent_id !== null && c.parent_id !== undefined && ids.has(c.parent_id)) {
        if (!replies.has(c.parent_id)) replies.set(c.parent_id, []);
        replies.get(c.parent_id).push(c);
      } else {
        tops.push(c);
      }
    }
    const canPost = Boolean(view.can_post);
    if (tops.length === 0) {
      body.appendChild(el(doc, 'p', 'no-comments', 'No comments yet'));
    } else {
      const list = el(doc, 'ol', 'comments');
      let previous = null;
      for (const c of tops) {
        const t = parseTime(c.created_at);
        if (t && previous !== null && dayKey(t) !== previous) list.appendChild(divider(doc, dayLabel(t, now)));
        if (t) previous = dayKey(t);
        const item = el(doc, 'li', 'comment-item');
        item.appendChild(comment(doc, Object.assign({}, c, {parent_id: null}), now, {canPost}));
        const kids = replies.get(c.id);
        if (kids) {
          const sub = el(doc, 'ol', 'replies');
          for (const r of kids) {
            const ri = el(doc, 'li', 'comment-item');
            ri.appendChild(comment(doc, Object.assign({}, r, {parent_id: c.id}), now, {canPost}));
            sub.appendChild(ri);
          }
          item.appendChild(sub);
        }
        list.appendChild(item);
      }
      body.appendChild(list);
    }
    panel.appendChild(body);

    if (canPost) panel.appendChild(replyBox(doc, view));
    else panel.appendChild(el(doc, 'p', 'reader-note', 'Readers see this thread but not the reply box.'));
    return panel;
  }

  // A row in a group's thread list: button[data-action=open-thread][data-id=<thread id>].
  function threadRow(doc, row, now) {
    const isStory = row.kind === 'story';
    const b = button(doc, 'thread-row ' + (isStory ? 'thread-story' : 'thread-note'), null, 'open-thread', row.id);
    let label = 'Note';
    if (isStory) {
      const source = String(row.source || 'Story');
      label = row.source_kind ? kindInfo(row.source_kind).label + ' \u00b7 ' + source : source;
    }
    b.appendChild(el(doc, 'span', 'quote-kind', label));
    b.appendChild(el(doc, 'strong', 'thread-row-title', row.title));
    const meta = el(doc, 'span', 'thread-row-meta');
    if (row.unread) {
      const dot = el(doc, 'span', 'dot');
      dot.appendChild(srOnly(doc, 'Unread'));
      meta.appendChild(dot);
    }
    meta.appendChild(el(doc, 'span', null, plural(row.comments, 'comment', 'comments')));
    const last = relativeTime(row.last_activity_at, now);
    if (last) meta.appendChild(el(doc, 'span', null, last));
    b.appendChild(meta);
    return b;
  }

  // A group in the channel list: button[data-action=open-group][data-id=<group id>].
  function groupItem(doc, group) {
    const b = button(doc, 'ch group-item', null, 'open-group', group.id);
    if (group.visibility === 'invited') {
      b.appendChild(icon(doc, 'lock'));
      b.appendChild(srOnly(doc, 'Invited group: '));
    } else {
      b.appendChild(icon(doc, 'hash'));
    }
    b.appendChild(el(doc, 'span', 'ch-name', group.name));
    if (group.unread > 0) {
      const badge = el(doc, 'span', 'badge', String(group.unread));
      badge.appendChild(srOnly(doc, ' unread'));
      b.appendChild(badge);
    }
    return b;
  }

  // opts: {approved: number | undefined, kind: string} refine the Latest and filtered messages.
  function emptyState(doc, view, query, opts) {
    const o = opts || {};
    const box = el(doc, 'div', 'empty');
    let title;
    let hint = '';
    if (query) {
      title = 'No story matches ' + query;
      hint = 'Check the spelling or clear the search.';
    } else if (o.kind) {
      title = 'No stories of this kind here';
      hint = 'Choose All to see every kind.';
    } else if (view === 'foryou') {
      title = 'Follow a topic to fill this view';
      hint = 'Stories on the topics you follow appear here.';
    } else if (view === 'saved') {
      title = 'Stories you save appear here';
      hint = 'Use Save on a story to keep it.';
    } else if (view === 'latest') {
      title = o.approved === 0 ? 'No approved sources yet' : 'No stories yet';
      hint = o.approved === 0
        ? 'Stories appear once a source is approved.' : 'New stories appear here as sources are checked.';
    } else {
      title = 'No stories in this topic yet';
    }
    box.appendChild(el(doc, 'h2', 'empty-title', title));
    if (hint) box.appendChild(el(doc, 'p', 'empty-hint', hint));
    if (view === 'foryou' && !query && !o.kind) {
      const slot = el(doc, 'div', 'empty-topics');
      slot.setAttribute('data-slot', 'topics');
      box.appendChild(slot);
    }
    return box;
  }

  // ----- group view, dialogs and messages (page wiring; every function is pure and takes the document)

  function unreadLabel(total) {
    return total + ' unread';
  }

  function groupsEmpty(doc) {
    return el(doc, 'li', 'side-empty', 'No groups yet');
  }

  // A group or thread that is missing or hidden reads the same either way. what: 'group' | 'thread'.
  function notFound(doc, what) {
    const box = el(doc, 'div', 'empty');
    box.appendChild(el(doc, 'h2', 'empty-title', 'This ' + what + ' does not exist or is not open to you.'));
    return box;
  }

  function threadsEmpty(doc, canStart) {
    const box = el(doc, 'div', 'empty');
    box.appendChild(el(doc, 'h2', 'empty-title', 'No threads in this group yet'));
    box.appendChild(el(doc, 'p', 'empty-hint', canStart
      ? 'Share a story from the feed or start a note.'
      : 'Threads appear here when a writer shares a story or starts a note.'));
    return box;
  }

  // The panel shell with a heading and a close control, for the states that have no thread to show.
  function panelShell(doc, threadId, title) {
    const panel = el(doc, 'aside', 'thread');
    panel.setAttribute('aria-labelledby', 'thread-title-' + threadId);
    panel.setAttribute('data-id', String(threadId));
    const head = el(doc, 'div', 'thead');
    const titles = el(doc, 'div', 'thead-text');
    const h = el(doc, 'h2', 'thread-title', title);
    h.setAttribute('id', 'thread-title-' + threadId);
    h.setAttribute('tabindex', '-1');
    titles.appendChild(h);
    head.appendChild(titles);
    const close = button(doc, 'icon-btn', null, 'close-thread', threadId);
    close.setAttribute('aria-label', 'Close thread');
    close.appendChild(icon(doc, 'close'));
    head.appendChild(close);
    panel.appendChild(head);
    return panel;
  }

  function threadLoading(doc, threadId) {
    const panel = panelShell(doc, threadId, 'Loading thread');
    panel.setAttribute('aria-busy', 'true');
    const body = el(doc, 'div', 'tbody');
    for (const w of ['w2', 'w4', 'w3']) body.appendChild(el(doc, 'span', 'bar-s ' + w));
    panel.appendChild(body);
    return panel;
  }

  // what: 'missing' (404) or 'failed' (any other refusal; the page also shows the error band with Retry).
  function threadMessage(doc, threadId, what) {
    const failed = what === 'failed';
    const panel = panelShell(doc, threadId, failed ? 'Thread could not be loaded' : 'Thread not found');
    const body = el(doc, 'div', 'tbody');
    body.appendChild(failed
      ? el(doc, 'p', 'no-comments', 'Try again in a moment.') : notFound(doc, 'thread'));
    panel.appendChild(body);
    return panel;
  }

  // A failure inside the panel, so it is seen at every width; Retry only where trying again can help.
  function threadError(doc, message, canRetry) {
    const box = el(doc, 'div', 'thread-error');
    box.setAttribute('role', 'alert');
    box.appendChild(el(doc, 'p', null, message));
    if (canRetry) box.appendChild(button(doc, 'btn', 'Retry', 'retry-thread', 0));
    return box;
  }

  function tag(doc, text, iconName) {
    const t = el(doc, 'span', 'tag visibility');
    if (iconName) t.appendChild(icon(doc, iconName));
    t.appendChild(doc.createTextNode(text));
    return t;
  }

  // Members of the open group. group: {id, visibility, member, can_manage, members: [name]}.
  // Emits join-group, leave-group (data-id), a form[data-action=add-member] and remove-member (data-name).
  const MEMBERS_SHOWN = 8;
  function membersStrip(doc, group) {
    const names = Array.isArray(group.members) ? group.members : [];
    const invited = group.visibility === 'invited';
    const box = el(doc, 'section', 'members');
    box.setAttribute('aria-label', 'Members');
    const row = el(doc, 'div', 'members-row');
    row.appendChild(tag(doc, invited ? 'Invited only' : 'Open to everyone', invited ? 'lock' : 'hash'));
    const avatars = el(doc, 'ul', 'avatars');
    for (const name of names.slice(0, MEMBERS_SHOWN)) {
      const li = el(doc, 'li');
      const av = el(doc, 'span', 'av', initials(name));
      av.setAttribute('aria-hidden', 'true');
      li.appendChild(av);
      li.appendChild(srOnly(doc, name));
      avatars.appendChild(li);
    }
    if (names.length > MEMBERS_SHOWN) {
      const li = el(doc, 'li');
      li.appendChild(el(doc, 'span', 'av more', '+' + (names.length - MEMBERS_SHOWN)));
      li.appendChild(srOnly(doc, ' more members'));
      avatars.appendChild(li);
    }
    row.appendChild(avatars);
    row.appendChild(el(doc, 'span', 'members-count', plural(names.length, 'member', 'members')));
    if (!invited) {
      row.appendChild(button(doc, 'btn', group.member ? 'Leave' : 'Join',
        group.member ? 'leave-group' : 'join-group', group.id));
    }
    box.appendChild(row);
    if (invited && group.can_manage) {
      const list = el(doc, 'ul', 'member-list');
      names.forEach((name, i) => {
        const li = el(doc, 'li');
        li.appendChild(el(doc, 'span', 'member-name', name)).setAttribute('id', 'member-name-' + i);
        const rm = button(doc, 'link-btn', 'Remove', 'remove-member', group.id);
        rm.setAttribute('data-name', name);
        rm.setAttribute('id', 'member-remove-' + i);
        rm.setAttribute('aria-labelledby', 'member-remove-' + i + ' member-name-' + i);
        li.appendChild(rm);
        list.appendChild(li);
      });
      box.appendChild(list);
      const form = el(doc, 'form', 'add-member');
      form.setAttribute('data-action', 'add-member');
      form.setAttribute('data-id', String(group.id));
      form.setAttribute('novalidate', '');
      const label = el(doc, 'label', 'sr-only', 'Name to add');
      label.setAttribute('for', 'add-member-name');
      const input = el(doc, 'input');
      input.setAttribute('type', 'text');
      input.setAttribute('id', 'add-member-name');
      input.setAttribute('maxlength', '60');
      input.setAttribute('autocomplete', 'off');
      input.setAttribute('placeholder', 'Name to add');
      form.append(label, input, el(doc, 'button', 'btn', 'Add member'));
      form.children[2].setAttribute('type', 'submit');
      box.appendChild(form);
    }
    const err = el(doc, 'p', 'field-error');
    err.setAttribute('data-slot', 'members-error');
    err.setAttribute('role', 'alert');
    err.setAttribute('hidden', '');
    box.appendChild(err);
    return box;
  }

  // The head of a group view: the members strip and, for those who may post, Start a note.
  function groupHead(doc, group, canStart) {
    const head = el(doc, 'div', 'group-head');
    head.appendChild(membersStrip(doc, group));
    if (canStart) {
      const b = button(doc, 'btn pri', null, 'start-note', group.id);
      b.appendChild(icon(doc, 'plus'));
      b.appendChild(el(doc, 'span', null, 'Start a note'));
      head.appendChild(b);
    }
    return head;
  }

  function radioOption(doc, name, value, className) {
    const label = el(doc, 'label', className);
    const input = el(doc, 'input');
    input.setAttribute('type', 'radio');
    input.setAttribute('name', name);
    input.setAttribute('value', value);
    label.appendChild(input);
    return label;
  }

  // Radios for the share dialog. With no groups: a sentence, and New group for those who may create one.
  function groupChoices(doc, groups, canCreate) {
    const frag = doc.createDocumentFragment();
    if (groups.length === 0) {
      frag.appendChild(el(doc, 'p', 'empty-hint', canCreate
        ? 'There are no groups yet. Create one to share this story.' : 'There are no groups open to you yet.'));
      if (canCreate) frag.appendChild(button(doc, 'btn', 'New group', 'new-group', 0));
      return frag;
    }
    const list = el(doc, 'ul', 'choice-list');
    for (const g of groups) {
      const li = el(doc, 'li');
      const label = radioOption(doc, 'share-group', String(g.id), 'choice');
      if (g.visibility === 'invited') {
        label.appendChild(icon(doc, 'lock'));
        label.appendChild(srOnly(doc, 'Invited group: '));
      }
      label.appendChild(el(doc, 'span', 'choice-name', g.name));
      li.appendChild(label);
      list.appendChild(li);
    }
    frag.appendChild(list);
    return frag;
  }

  // The two visibility options of the new group dialog as a joined pair of real radios.
  function visibilityChoices(doc) {
    const wrap = el(doc, 'div', 'seg');
    const defs = [['everyone', 'Open to everyone', 'hash'], ['invited', 'Invited only', 'lock']];
    defs.forEach(([value, text, iconName], i) => {
      const label = radioOption(doc, 'group-visibility', value, 'seg-opt');
      if (i === 0) label.children[0].setAttribute('checked', '');
      label.appendChild(icon(doc, iconName));
      label.appendChild(el(doc, 'span', null, text));
      wrap.appendChild(label);
    });
    return wrap;
  }

  function topicChoices(doc, topics) {
    const frag = doc.createDocumentFragment();
    if (topics.length === 0) {
      frag.appendChild(el(doc, 'p', 'empty-hint', 'No topics yet'));
      return frag;
    }
    const list = el(doc, 'ul', 'choice-list');
    for (const t of topics) {
      const li = el(doc, 'li');
      const label = el(doc, 'label', 'choice');
      const input = el(doc, 'input');
      input.setAttribute('type', 'checkbox');
      input.setAttribute('name', 'group-topic');
      input.setAttribute('value', String(t.id));
      label.appendChild(input);
      label.appendChild(el(doc, 'span', 'choice-name', t.name));
      li.appendChild(label);
      list.appendChild(li);
    }
    frag.appendChild(list);
    return frag;
  }

  // Above the reply box while replying to a top-level comment.
  function replyingTo(doc, name) {
    const bar = el(doc, 'div', 'replying');
    bar.appendChild(el(doc, 'span', null, 'Replying to ' + name));
    bar.appendChild(button(doc, 'link-btn', 'Cancel', 'cancel-reply', 0));
    return bar;
  }

  // A comment's body while it is edited in place; error is the server's line for a refused save.
  function editForm(doc, c, text, error) {
    const form = el(doc, 'div', 'edit-form');
    const ta = el(doc, 'textarea', 'edit-text', text);
    ta.setAttribute('rows', '3');
    ta.setAttribute('maxlength', '4000');
    ta.setAttribute('data-id', String(c.id));
    ta.setAttribute('aria-labelledby', 'c' + c.id + '-author');
    form.appendChild(ta);
    if (error) {
      const p = el(doc, 'p', 'field-error', error);
      p.setAttribute('role', 'alert');
      form.appendChild(p);
    }
    const acts = el(doc, 'div', 'edit-acts');
    acts.appendChild(button(doc, 'btn', 'Cancel', 'cancel-edit', c.id));
    acts.appendChild(button(doc, 'btn pri', 'Save', 'save-edit', c.id));
    form.appendChild(acts);
    return form;
  }

  return {
    IDENTITY_NOTE, EDIT_RULE, threadError, card, emptyState, relativeTime, safeLink, icon, fullTime, initials,
    linkify, comment, threadPanel, threadRow, groupItem, sharedLine, threadChips,
    replyPlaceholder, unreadLabel, groupsEmpty, notFound, threadsEmpty, threadLoading, threadMessage, membersStrip, groupHead,
    groupChoices, visibilityChoices, topicChoices, replyingTo, editForm,
  };
});

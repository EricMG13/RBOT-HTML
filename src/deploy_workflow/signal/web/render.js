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
  const ICONS = {
    bookmark: 'M6 3h12v18l-6-4-6 4z',
    external: 'M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5',
    layers: 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5',
    star: 'M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z',
    hash: 'M5 9h14M5 15h14M10 4L8 20M16 4l-2 16',
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

  function card(doc, story, now) {
    const kind = Object.prototype.hasOwnProperty.call(KINDS, story.kind) ? story.kind : 'other';
    const kindLabel = kind === 'other' ? String(story.kind || 'Story') : KINDS[kind];
    const article = el(doc, 'article', 'card card-' + kind);
    article.setAttribute('data-id', String(story.id));
    article.setAttribute('tabindex', '-1');

    article.appendChild(el(doc, 'span', 'kind', kindLabel));

    const href = safeLink(story.link);
    const h3 = el(doc, 'h3', 'headline');
    if (href) h3.appendChild(externalLink(doc, href, 'headline-link', story.title));
    else h3.textContent = story.title;
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

    const acts = el(doc, 'div', 'acts');
    const save = el(doc, 'button', 'act save');
    save.setAttribute('type', 'button');
    save.setAttribute('data-action', 'save');
    save.setAttribute('aria-pressed', story.saved ? 'true' : 'false');
    save.setAttribute('aria-label', 'Save: ' + story.title);
    save.appendChild(icon(doc, 'bookmark'));
    save.appendChild(el(doc, 'span', null, 'Save'));
    acts.appendChild(save);
    if (href) {
      const open = externalLink(doc, href, 'act open', null, 'Open source: ' + story.title + ' (opens in a new tab)');
      open.appendChild(el(doc, 'span', null, 'Open source'));
      open.appendChild(icon(doc, 'external'));
      acts.appendChild(open);
    }
    article.appendChild(acts);
    return article;
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

  return {card, emptyState, relativeTime, safeLink, icon, fullTime, initials};
});

'use strict';
// Pure reader logic for the 2026-11-11 handoff contract (docs/rulings/2026-11-11-reader-and-issuer-report.md, H1 to H7):
// no DOM, no store, no globals read. Browser: the functions below are globals. Node: module.exports.
// Inputs are the store's shapes: a section is {heading, level, line, blocks[]}; a text block is {type:'text', text}.

const PASSAGE_HEADINGS = {
  bottom: 'Bottom line',
  key: 'Key findings',
  contrary: 'Contrary evidence and what would change the view',
  limits: 'Limitations',
};

// The H3 sections under the first `## Findings` H2, in order; empty when the handoff has none.
function findingsH3(sections) {
  const list = sections || [];
  const start = list.findIndex(s => s.level === 2 && s.heading === 'Findings');
  if (start < 0) return [];
  const found = [];
  for (const section of list.slice(start + 1)) {
    if (section.level === 2) break;
    if (section.level === 3) found.push(section);
  }
  return found;
}

// H1: the four reader passages, each the H3 section with the exact heading under Findings, or null.
function readerPassages(sections) {
  const h3 = findingsH3(sections);
  const out = {};
  for (const [key, heading] of Object.entries(PASSAGE_HEADINGS)) out[key] = h3.find(s => s.heading === heading) || null;
  return out;
}

// H7: new format iff the first H3 after `## Findings` is `Bottom line`.
function isNewFormat(sections) {
  const h3 = findingsH3(sections);
  return h3.length > 0 && h3[0].heading === PASSAGE_HEADINGS.bottom;
}

// H7: a run is "Earlier format" when any of its handoffs (each a sections array) is not new format.
function earlierFormatRun(outputsSections) {
  return (outputsSections || []).some(sections => !isNewFormat(sections));
}

const sectionText = section => (section ? section.blocks.filter(b => b.type === 'text').map(b => b.text).join('\n') : '');

// Not assessable: new format by the engine contract (the launcher makes a blocked module's Bottom line BEGIN exactly `Not assessable: `
// and forbids the phrase in a non-blocked Bottom line); earlier format by the store's own state.established === false.
function blocked(sections, state) {
  if (isNewFormat(sections)) {
    const bottom = readerPassages(sections).bottom;
    const first = bottom && bottom.blocks.find(b => b.type === 'text');
    return !!first && first.text.startsWith('Not assessable:');
  }
  return !!state && state.established === false;
}

// H3: the paragraph's last line, when it starts exactly `Basis: `, is the Basis line. Items split on "; ", one final full stop dropped.
function splitBasis(text) {
  const lines = String(text).split('\n');
  const last = lines[lines.length - 1];
  if (!last.startsWith('Basis: ')) return {body: String(text), items: []};
  const items = last.slice('Basis: '.length).replace(/\.$/, '').split('; ').map(item => item.trim()).filter(item => item !== '');
  return {body: lines.slice(0, -1).join('\n'), items};
}

// H3 item forms. Anything else is kept as text, never dropped.
function basisItem(item) {
  const calculation = /^calculation (\S+)$/.exec(item);
  if (calculation) return {kind: 'calculation', id: calculation[1]};
  const upstream = /^(.+) \((CP-[A-Z0-9]+)\)$/.exec(item);
  if (upstream) return {kind: 'module', name: upstream[1], code: upstream[2]};
  const source = /^(.+?\.[A-Za-z][A-Za-z0-9]{0,4})(?:, page (\d+)|, pages (\d+)–(\d+))?$/.exec(item);
  if (source) {
    const out = {kind: 'source', file: source[1]};
    if (source[2] !== undefined) out.page = Number(source[2]);
    if (source[3] !== undefined) { out.page = Number(source[3]); out.pageEnd = Number(source[4]); }
    return out;
  }
  return {kind: 'text', text: item};
}

// ---- Figures (H6 check 8). A figure is a number with optional thousands commas and decimals, with its currency prefix and unit
// suffix as written. Not figures: a number touching a letter or hyphen-joined to one (10-K, B-1, FY2024, 3rd), a four-digit year
// 1900-2099, a date or a day/year beside a month name, a whole number below 100 that carries no currency, no symbolic unit
// (%, x, bp, bps, pp, basis/percentage points) and no scale word (a count, or a span of time).
const MONTH = '(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\\.?';
const DATE_PATTERNS = [
  /\d{4}-\d{2}-\d{2}/g, /\d{4}-(?:0[1-9]|1[0-2])(?!\d)/g, /\d{4}-Q[1-4]/g,
  new RegExp(`\\b${MONTH}\\s+\\d{1,2}(?:,?\\s+\\d{4})?(?!\\d)`, 'g'),
  new RegExp(`\\b\\d{1,2}\\s+${MONTH}(?:,?\\s+\\d{4})?(?!\\d)`, 'g'),
  new RegExp(`\\b${MONTH}\\s+\\d{4}(?!\\d)`, 'g'),
];
const NUMBER = /\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?/g;
const SYMBOLIC_UNIT = /^(?:%|x(?![A-Za-z])|bps(?![A-Za-z])|bp(?![A-Za-z])|pp(?![A-Za-z])|\s(?:basis points|percentage points)(?![A-Za-z])|\s(?:bps|bp|pp)(?![A-Za-z]))/;
const SCALE_UNIT = /^(?:\s?(?:thousand|million|billion|trillion|bn|k|m)(?![A-Za-z]))/;
const OTHER_UNIT = /^\s(?:times|notches|notch|days|day|weeks|week|months|month|quarters|quarter|years|year)(?![A-Za-z])/;
const SYMBOLS = '$€£¥';
// ISO 4217 codes a credit handoff uses; only these count as a currency prefix (not AGM, IAS, LTM, ECB).
const CURRENCY_CODES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'SEK', 'NOK', 'DKK', 'HKD', 'SGD', 'CNY', 'INR', 'BRL', 'MXN', 'ZAR', 'TRY', 'PLN', 'CZK'];
const CURRENCY_BEFORE = new RegExp(`(?:^|[^A-Za-z])(?:${CURRENCY_CODES.join('|')})$`);

function dateRanges(text) {
  const ranges = [];
  for (const pattern of DATE_PATTERNS) for (const m of text.matchAll(pattern)) ranges.push([m.index, m.index + m[0].length]);
  return ranges;
}

function figureSpans(text) {
  text = String(text);
  const dates = dateRanges(text);
  const spans = [];
  for (const m of text.matchAll(NUMBER)) {
    const start = m.index, end = start + m[0].length, rest = text.slice(end);
    if (dates.some(([from, to]) => start >= from && end <= to)) continue;
    const before = text[start - 1] || '';
    if (/[A-Za-z]/.test(before) || (before === '-' && /[A-Za-z]/.test(text[start - 2] || ''))) continue;
    if (/^-[A-Za-z]/.test(rest)) continue;
    const symbolic = SYMBOLIC_UNIT.exec(rest), scale = SCALE_UNIT.exec(rest), other = OTHER_UNIT.exec(rest);
    const unit = symbolic || scale || other;
    if (!unit && /^[A-Za-z]/.test(rest)) continue;
    let from = start;
    if (SYMBOLS.includes(before)) from = start - 1;
    else if (before === ' ' && CURRENCY_BEFORE.test(text.slice(0, start - 1))) from = start - 4;
    const prefixed = from !== start;
    const plain = !m[0].includes(',') && !m[0].includes('.');
    if (!prefixed && !symbolic && !scale && plain) {
      const value = Number(m[0]);
      if (value < 100) continue;
      if (m[0].length === 4 && value >= 1900 && value <= 2099) continue;
    }
    const to = unit ? end + unit[0].length : end;
    spans.push({start: from, end: to, text: text.slice(from, to)});
  }
  return spans;
}

// H6 check 7: lower case, Basis line dropped, punctuation removed, whitespace collapsed.
function normaliseLimitation(text) {
  return splitBasis(text).body.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, '').replace(/\s+/g, ' ').trim();
}

// ---- Earlier format (H7): a bracket citation or chip that ends a sentence or the paragraph moves, verbatim, to the items.
const CITATION = /\[[^\]]*\]|【[^】]*】/g;
const SENTENCE_END_BEFORE = /[.!?]["')”’]*\s?$/;
const SENTENCE_END_AFTER = /^(?:\s*$|[.!?]+["')”’]*(?:\s|$))/;

function earlierBasis(text) {
  text = String(text);
  const found = [...text.matchAll(CITATION)].map(m => ({start: m.index, end: m.index + m[0].length, text: m[0]}));
  const clusters = [];
  for (const citation of found) {
    const last = clusters[clusters.length - 1];
    if (last && /^\s*$/.test(text.slice(last[last.length - 1].end, citation.start))) last.push(citation);
    else clusters.push([citation]);
  }
  const items = [];
  const cut = [];
  for (const cluster of clusters) {
    const first = cluster[0], tail = text.slice(cluster[cluster.length - 1].end);
    const ends = SENTENCE_END_AFTER.test(tail) || (SENTENCE_END_BEFORE.test(text.slice(0, first.start)) && /^(?:\s|$)/.test(tail));
    if (!ends) continue;
    for (const citation of cluster) {
      items.push(citation.text);
      cut.push([text[citation.start - 1] === ' ' ? citation.start - 1 : citation.start, citation.end]);
    }
  }
  let body = '', at = 0;
  for (const [from, to] of cut) { body += text.slice(at, from); at = to; }
  return {body: body + text.slice(at), items};
}

// ---- Report history (decision 4): as-of date descending, then first start time descending (no time sorts after a time), then folder.
function historyRows(runs) {
  const started = run => (run.record && run.record.steps && run.record.steps[0] && run.record.steps[0].started) || null;
  const compare = (a, b) => (a < b) - (a > b);  // descending
  return [...runs].sort((a, b) => {
    const dates = compare(a.asOf || '', b.asOf || '');
    if (dates) return dates;
    const [sa, sb] = [started(a), started(b)];
    if (sa !== sb) {
      if (sa === null) return 1;
      if (sb === null) return -1;
      return compare(sa, sb);
    }
    return -compare(a.folder, b.folder);
  });
}

// The pathway id as words: "credit_snapshot" is "Credit snapshot"; no id is null (the caller says "Not recorded").
function pathwayTitle(id) {
  const words = String(id || '').split(/[_\s-]+/).filter(word => word !== '').map(word => word.toLowerCase());
  return words.length ? words.join(' ').replace(/^./, first => first.toUpperCase()) : null;
}

// The modules of a run that hold an output, in the run's own order (record.steps), then any the record does not list.
function runModuleCodes(run) {
  const held = Object.entries(run.modules || {}).filter(([, entry]) => entry.outputs && entry.outputs.length).map(([code]) => code);
  const ordered = ((run.record && run.record.steps) || []).map(step => step.module).filter(code => held.includes(code));
  return [...new Set([...ordered, ...held])];
}

// H5: the next n items dated on or after asOf, earliest first; an item without a YYYY-MM-DD date is not dated and is left out.
function nearestDates(items, asOf, n = 5) {
  const dated = items.filter(item => /^\d{4}-\d{2}-\d{2}$/.test(String(item.date)) && item.date >= asOf);
  return dated.map((item, index) => ({item, index}))
    .sort((a, b) => (a.item.date < b.item.date ? -1 : a.item.date > b.item.date ? 1 : a.index - b.index))
    .slice(0, n).map(entry => entry.item);
}

if (typeof module !== 'undefined') module.exports = {readerPassages, isNewFormat, earlierFormatRun, blocked, splitBasis, basisItem, figureSpans, normaliseLimitation, earlierBasis, historyRows, pathwayTitle, runModuleCodes, nearestDates};

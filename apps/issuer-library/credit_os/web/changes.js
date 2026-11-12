'use strict';
// Pure rendering of the Changes tab (docs/rulings/2026-11-11-module-presets-and-changes.md, decision M8): no DOM, no store, no globals written.
// Browser: one global, ChangesView (reader.js is loaded first; nothing else leaks into the page's scope). Node: module.exports.
// Delivery adds no analysis and computes nothing. Every figure shown is text the comparison pack (`changes.json`, schema cpos-changes/2) or CP-8's
// handoff states, with its sign, unit and period: no rounding, no difference worked out here, no direction arrow. A measure that is not comparable
// shows both values and no difference and no joining line. Chart positions are geometry only. All pack and handoff text is model output: it is
// escaped before it reaches the page.
const ChangesView = (() => {
const ChangesReader = typeof module !== 'undefined' ? require('./reader.js') : {escapeHtml, richText, paragraphBody, readerPassages, tableView};

const FIRST_RUN = 'First run of this pathway';
const NOT_COMPARABLE = 'Not comparable';
const NOT_STATED = 'Not stated';
const LEDGER_STATUSES = ['Closed', 'Remaining', 'New', 'No longer stated'];
const TREND_MEASURES = [['leverage', 'Total debt / EBITDA'], ['net_leverage', 'Net debt / EBITDA'], ['coverage', 'EBITDA / cash interest'], ['cash', 'Cash'], ['undrawn', 'Undrawn committed facilities']];
const REASON_PREFIX = /^changes: not produced\s*[—-]\s*/;
const esc = value => ChangesReader.escapeHtml(value);
const rich = value => ChangesReader.richText(value);

// What the run says about its comparison: no pack and no note is a first run of the pathway; a pack that could not be read is neither.
function changesState(changes) {
  if (!changes) return 'first';
  if (changes.problem) return 'unreadable';
  if (changes.note) return 'not_produced';
  return changes.pack ? 'produced' : 'first';
}

// CP-8's handoff (the store's sections) as its reader passages and its three registers; each is null when the handoff has none.
function cp8Parts(sections) {
  const list = sections || [];
  const passages = ChangesReader.readerPassages(list);
  const register = heading => {
    const section = list.find(s => s.level === 3 && s.heading === heading);
    const table = section && section.blocks.find(b => b.type === 'table');
    return table || null;
  };
  return {
    bottom: passages.bottom,
    key: passages.key,
    issuer: register('What changed: the issuer'),
    analysis: register('What changed: the analysis'),
    ledger: register('Limitations ledger'),
  };
}

const column = (table, name) => (table ? table.headers.findIndex(header => header.trim() === name) : -1);
const cell = (row, index) => (index >= 0 && row ? String(row.cells[index] ?? '') : '');
const bare = text => String(text).replace(/\*\*|`/g, '').trim();

// A value with its unit as the pack states them: `x` and `%` follow the figure, any other unit follows after a space.
const withUnit = (value, unit) => (unit == null || unit === '' ? String(value) : /^[x%]$/.test(unit) ? `${value}${unit}` : `${value} ${unit}`);
const sideText = side => (side && side.value != null ? `${withUnit(side.value, side.unit)}${side.period ? ` (${side.period})` : ''}` : NOT_STATED);

// Whether the two values of a measure may be set against each other, and so whether its difference may be shown.
// `comparable` is the pack's: no, yes, or judge (CP-8's row for the measure says Same definition or Not comparable). A row CP-8 marks Not comparable
// is never compared, whatever the pack says. A judge row with no verdict from CP-8 is left unjudged: no difference.
function measureVerdict(measure, issuerTable) {
  const first = column(issuerTable, 'Measure or fact');
  const row = issuerTable ? issuerTable.rows.find(r => bare(cell(r, first < 0 ? 0 : first)) === measure.label) : null;
  const says = pattern => Boolean(row) && row.cells.some(text => pattern.test(bare(text)));
  const note = row ? cell(row, row.cells.length - 1) : null;
  if (measure.comparable === 'no') return {kind: 'not_comparable', label: NOT_COMPARABLE, reason: measure.reason || null};
  if (says(/^Not comparable/i)) return {kind: 'not_comparable', label: NOT_COMPARABLE, reason: note};
  if (measure.comparable === 'yes') return {kind: 'comparable', label: 'Comparable', reason: null};
  if (says(/^Same definition/i)) return {kind: 'comparable', label: 'Same definition', reason: null};
  return {kind: 'unjudged', label: 'Comparability not judged', reason: measure.reason || null};
}

const differenceText = (measure, verdict) => (verdict.kind === 'comparable' && measure.difference != null ? withUnit(measure.difference, measure.unit) : null);

// ---- Part 2: the issuer.
const position = (value, lo, hi) => (hi === lo ? 50 : 8 + ((value - lo) / (hi - lo)) * 84);
function thenAndNowChart(measures, verdicts) {
  const rows = measures.map((measure, i) => {
    const verdict = verdicts[i];
    const values = [measure.prior, measure.current].map(side => (side && side.value != null && Number.isFinite(Number(side.value)) ? Number(side.value) : null));
    const held = values.filter(v => v !== null);
    if (!held.length) return '';
    const lo = Math.min(...held), hi = Math.max(...held);
    const joined = verdict.kind === 'comparable' && values[0] !== null && values[1] !== null;
    const link = joined ? `<i class="dumbbell-link" style="left:${position(Math.min(...values), lo, hi)}%;width:${position(Math.max(...values), lo, hi) - position(Math.min(...values), lo, hi)}%"></i>` : '';
    const dot = (v, series) => (v === null ? '' : `<i class="dumbbell-dot series-${series}" style="left:${position(v, lo, hi)}%"></i>`);
    const text = `Earlier ${sideText(measure.prior)} · Current ${sideText(measure.current)}${verdict.kind === 'comparable' ? '' : ` · ${verdict.label}`}`;
    return `<div class="dumbbell-row changes-row" role="group" aria-label="${esc(measure.label)}"><div class="chart-open"><span class="chart-label">${esc(measure.label)}</span><span class="dumbbell-track" aria-hidden="true">${link}${dot(values[0], 0)}${dot(values[1], 1)}</span><span class="structure-text">${esc(text)}</span></div></div>`;
  }).join('');
  if (!rows) return '';
  return `<div class="chart-legend"><span><i class="series-0"></i>Earlier run</span><span><i class="series-1"></i>Current run</span></div><div class="dumbbell-chart changes-chart" role="group" aria-label="Then and now: each measure on its own scale. The table below gives the same values." tabindex="0">${rows}</div><p class="intro">Each row has its own scale. A measure that is not comparable is shown as two points with no line.</p>`;
}

function measureTable(measures, verdicts) {
  const body = measures.map((measure, i) => {
    const verdict = verdicts[i], difference = differenceText(measure, verdict);
    const change = difference !== null ? esc(difference) : `<strong>${esc(verdict.label)}</strong>${verdict.reason ? `<small>${esc(verdict.reason)}</small>` : ''}`;
    return `<tr><th scope="row">${esc(measure.label)}</th><td>${esc(sideText(measure.prior))}</td><td>${esc(sideText(measure.current))}</td><td>${change}</td></tr>`;
  }).join('');
  return `<div class="table-scroll" role="region" aria-label="Measures, earlier and current" tabindex="0"><table class="history-table"><caption>Measures the pack states, earlier and current</caption><thead><tr><th scope="col">Measure</th><th scope="col">Earlier</th><th scope="col">Current</th><th scope="col">Change</th></tr></thead><tbody>${body}</tbody></table></div>`;
}

function netDebtView(change) {
  if (!change) return '';
  const unit = change.unit, rows = [['Earlier net debt', change.prior_net_debt], ['Change in gross debt', change.change_in_gross_debt], ['Change in cash', change.change_in_cash], ['Current net debt', change.current_net_debt]];
  const item = ([name, value]) => `<div><dt>${esc(name)}</dt><dd>${esc(value == null ? NOT_STATED : withUnit(value, unit))}</dd></div>`;
  return `<h3>Net debt change</h3><dl class="net-debt-change">${rows.map(item).join('')}</dl><p class="intro">${esc(change.convention || '')}</p>`;
}

function maturityView(profile) {
  if (!profile) return '';
  const rows = profile.rows;
  const top = Math.max(0, ...rows.flatMap(r => [r.prior, r.current]).map(Number).filter(Number.isFinite));
  const width = value => (value == null || !Number.isFinite(Number(value)) || top === 0 ? 0 : (Number(value) / top) * 100);
  const bars = rows.map(r => `<div class="maturity-pair" aria-hidden="true"><span>${esc(r.period)}</span><i class="series-0" style="width:${width(r.prior)}%"></i><i class="series-1" style="width:${width(r.current)}%"></i></div>`).join('');
  const body = rows.map(r => `<tr><th scope="row">${esc(r.period)}</th><td>${esc(r.prior == null ? NOT_STATED : r.prior)}</td><td>${esc(r.current == null ? NOT_STATED : r.current)}</td><td>${esc(r.difference == null ? '—' : r.difference)}</td></tr>`).join('');
  return `<h3>Maturity profile, earlier and current</h3><div class="chart-legend"><span><i class="series-0"></i>Earlier run</span><span><i class="series-1"></i>Current run</span></div><div class="maturity-chart">${bars}</div><div class="table-scroll" role="region" aria-label="Maturity profile" tabindex="0"><table class="history-table"><caption>${esc(`Debt maturities, ${profile.unit}`)}</caption><thead><tr><th scope="col">Period</th><th scope="col">Earlier</th><th scope="col">Current</th><th scope="col">Change</th></tr></thead><tbody>${body}</tbody></table></div>`;
}

const omittedNote = omitted => {
  const lines = Object.entries(omitted || {}).map(([name, reason]) => `${name === 'net_debt_change' ? 'Net debt change' : name === 'maturity_profile' ? 'Maturity profile' : name} is not shown: ${reason}.`);
  return lines.length ? `<p class="intro changes-omitted">${lines.map(esc).join(' ')}</p>` : '';
};

const verbatim = (caption, table) => (table ? ChangesReader.tableView(caption, table, {id: 'cp8', chips: () => 0}) : `<p class="empty">${esc(`CP-8's handoff has no ${caption.toLowerCase()} table.`)}</p>`);

function issuerPart(pack, parts) {
  const measures = pack.measures || [];
  const verdicts = measures.map(m => measureVerdict(m, parts && parts.issuer));
  const register = parts ? `<h3>Each change and its cause</h3>${verbatim('What changed: the issuer', parts.issuer)}` : '';
  return `<section class="run-section" id="changes-issuer"><h2>The issuer</h2>${thenAndNowChart(measures, verdicts)}${measures.length ? measureTable(measures, verdicts) : '<p class="empty">The comparison pack states no measure.</p>'}${netDebtView(pack.net_debt_change)}${maturityView(pack.maturity_profile)}${omittedNote(pack.omitted)}${register}</section>`;
}

// ---- Part 1: CP-8's own words, verbatim; a Basis line is shown as the source line it is, never dropped.
function passageView(section) {
  if (!section) return `<p class="empty">${NOT_STATED} in CP-8's handoff.</p>`;
  let html = '', open = false;
  const close = () => { if (open) html += '</ul>'; open = false; };
  for (const block of section.blocks.filter(b => b.type === 'text')) {
    const {item, body, items} = ChangesReader.paragraphBody(block.text);
    const basis = items.length ? `<small class="changes-basis">Basis: ${esc(items.join('; '))}</small>` : '';
    if (item && !open) html += '<ul class="passage-list">';
    if (!item) close();
    open = item;
    html += item ? `<li>${rich(body)}${basis}</li>` : `<p class="passage-text">${rich(body)}${basis}</p>`;
  }
  close();
  return html;
}

function whatChangedPart(parts) {
  return `<section class="run-section" id="changes-what"><h2>What changed</h2><h3>Bottom line</h3>${passageView(parts.bottom)}<h3>Key findings</h3>${passageView(parts.key)}</section>`;
}

// ---- Part 3: one row per module of the pack; CP-8's status and reason read from its register by the module code in the first cell.
const moduleCode = text => { const found = /\(([A-Z0-9][A-Z0-9-]*)\)\s*$/.exec(bare(text)); return found ? found[1] : null; };
function analysisPart(pack, parts) {
  const table = parts && parts.analysis, status = column(table, 'Status'), cause = column(table, 'Cause'), why = column(table, 'Why');
  const rows = (pack.modules || []).map(m => {
    const row = table ? table.rows.find(r => moduleCode(r.cells[0]) === m.module) : null;
    const state = !parts ? 'Explanation not produced' : row ? cell(row, status) || NOT_STATED : `${NOT_STATED} by CP-8`;
    const side = (ran, text) => (text != null ? text : ran ? NOT_STATED : 'Did not run');
    const earlier = side(m.ran_prior, m.prior_bottom_line), current = side(m.ran_current, m.current_bottom_line);
    const reason = row ? [cell(row, cause), cell(row, why)].filter(Boolean) : [];
    return `<details class="change-module"><summary><span class="change-name">${esc(m.title)} <span class="module-code">${esc(m.module)}</span></span><span class="badge badge-gray change-status">${esc(state)}</span><span class="change-then"><small>Earlier</small>${esc(earlier)}</span><span class="change-now"><small>Current</small>${esc(current)}</span></summary><div class="change-pair"><section><h4>Earlier</h4><p>${esc(earlier)}</p></section><section><h4>Current</h4><p>${esc(current)}</p></section></div>${reason.length ? `<p class="change-why">${esc(reason.join(' · '))}</p>` : ''}</details>`;
  }).join('');
  return `<section class="run-section" id="changes-analysis"><h2>The analysis</h2><p class="intro">One row per module. A row opens the earlier and current bottom lines side by side.</p><div class="change-modules">${rows}</div></section>`;
}

// ---- Part 4: counts of each status as one bar (segment sizes are the counts), the ledger itself beneath.
function limitationsPart(parts) {
  const table = parts.ledger, status = column(table, 'Status');
  if (!table) return `<section class="run-section" id="changes-limitations"><h2>Limitations</h2><p class="empty">${NOT_STATED} in CP-8's handoff.</p></section>`;
  const counts = LEDGER_STATUSES.map(name => [name, table.rows.filter(r => bare(cell(r, status)) === name).length]);
  const other = table.rows.length - counts.reduce((sum, [, n]) => sum + n, 0);
  if (other) counts.push(['Other', other]);
  const label = counts.map(([name, n]) => `${name} ${n}`).join(', ');
  const segments = counts.filter(([, n]) => n > 0).map(([name, n]) => `<i class="ledger-${esc(name.toLowerCase().replace(/\W+/g, '-'))}" style="flex-grow:${n}" title="${esc(`${name} ${n}`)}"></i>`).join('');
  const legend = counts.map(([name, n]) => `<span><i class="ledger-${esc(name.toLowerCase().replace(/\W+/g, '-'))}"></i>${esc(name)} <strong>${n}</strong></span>`).join('');
  return `<section class="run-section" id="changes-limitations"><h2>Limitations</h2><div class="ledger-bar" role="img" aria-label="${esc(`Limitations: ${label}`)}">${segments}</div><div class="chart-legend ledger-legend">${legend}</div>${verbatim('Limitations ledger', table)}</section>`;
}

// ---- Part 5: every listed run of the issuer and pathway, earliest first. `runs` is [{key, href, asOf, runId, current, bottom, metrics, changes, cp8}]:
// `metrics` are the library's own quotes ({value, unit, period} per measure), `changes` the run's pack record, `cp8` its CP-8 sections or null.
// A segment joins two neighbouring points only where the later run's own pack compares exactly those two values under one definition.
function joined(runs, i, key, measureOf) {
  const [before, after] = [runs[i - 1], runs[i]];
  const [a, b] = [before.metrics && before.metrics[key], after.metrics && after.metrics[key]];
  const pack = after.changes && after.changes.pack;
  if (!a || !b || !pack || a.unit !== b.unit || !pack.prior || pack.prior.run !== before.runId) return false;
  const measure = (pack.measures || []).find(m => m.key === key);
  if (!measure || !measure.prior || !measure.current || measure.prior.value !== a.value || measure.current.value !== b.value) return false;
  return measureVerdict(measure, cp8Parts(after.cp8).issuer).kind === 'comparable';
}
function trendLine(runs, key, label) {
  const points = runs.map(r => (r.metrics && r.metrics[key] ? r.metrics[key] : null));
  const held = points.filter(Boolean);
  if (!held.length) return `<li><strong>${esc(label)}</strong> <span class="muted">${NOT_STATED} in any listed run.</span></li>`;
  if (new Set(held.map(p => p.unit)).size > 1 || held.some(p => !Number.isFinite(Number(p.value)))) return `<li><strong>${esc(label)}</strong> <span class="muted">Not drawn: the runs state it in different units or without a number.</span></li>`;
  const values = held.map(p => Number(p.value)), lo = Math.min(...values), hi = Math.max(...values);
  const x = i => (runs.length === 1 ? 50 : 8 + (i / (runs.length - 1)) * 84), y = v => (hi === lo ? 20 : 34 - ((v - lo) / (hi - lo)) * 28);
  const lines = runs.map((_, i) => (i > 0 && joined(runs, i, key) ? `<line x1="${x(i - 1)}" y1="${y(Number(points[i - 1].value))}" x2="${x(i)}" y2="${y(Number(points[i].value))}"/>` : '')).join('');
  const dots = points.map((p, i) => (p ? `<circle cx="${x(i)}" cy="${y(Number(p.value))}" r="2.6"/>` : '')).join('');
  return `<li><strong>${esc(label)}</strong><svg class="trend" viewBox="0 0 100 40" width="160" height="40" aria-hidden="true" focusable="false">${lines}${dots}</svg><span class="muted">${esc(withUnit(held[0].value, held[0].unit))} first listed · ${esc(withUnit(held[held.length - 1].value, held[held.length - 1].unit))} latest</span></li>`;
}
function overTimePart(runs, fmtDate) {
  const head = ['Run', ...TREND_MEASURES.map(([, label]) => label), 'Lead module: bottom line'];
  const body = runs.map(r => {
    const metric = key => { const p = r.metrics && r.metrics[key]; return p ? `${esc(withUnit(p.value, p.unit))}${p.period ? `<small>${esc(p.period)}</small>` : ''}` : NOT_STATED; };
    const date = `${esc(fmtDate(r.asOf))}${r.current ? ' <span class="badge badge-gray">Showing</span>' : ''}`;
    return `<tr><th scope="row">${r.href ? `<a href="${esc(r.href)}">${date}</a>` : date}</th>${TREND_MEASURES.map(([key]) => `<td>${metric(key)}</td>`).join('')}<td>${esc(r.bottom == null ? NOT_STATED : r.bottom)}</td></tr>`;
  }).join('');
  const lines = TREND_MEASURES.map(([key, label]) => trendLine(runs, key, label)).join('');
  return `<section class="run-section" id="changes-over-time"><h2>Over time</h2><p class="intro">Every listed run of this issuer and pathway, earliest first, with the figures the library quotes for each. A line joins two runs only where the later run's comparison states that the definitions match; otherwise the points stand alone.</p><ul class="trend-list">${lines}</ul><div class="table-scroll" role="region" aria-label="Over time" tabindex="0"><table class="history-table"><caption>Figures and the lead module's bottom line at each date</caption><thead><tr>${head.map(h => `<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div></section>`;
}

// The lead module's bottom line as its handoff states it: the first paragraph under Bottom line (Basis line dropped), or an earlier-format Reader summary's.
function leadBottom(sections, summary) {
  const bottom = ChangesReader.readerPassages(sections || []).bottom;
  const first = bottom && bottom.blocks.find(b => b.type === 'text');
  if (first) return ChangesReader.paragraphBody(first.text).body;
  return summary && summary.bottomLine != null ? summary.bottomLine : null;
}

// The whole tab. `input`: {changes, cp8 (sections|null), pathway (words), fmtDate(iso), runs}.
function changesHtml(input) {
  const {changes, cp8, pathway, fmtDate, runs} = input;
  const state = changesState(changes);
  if (state === 'first') return `<div class="changes"><p class="changes-first">${FIRST_RUN}</p></div>`;
  const pack = changes.pack || null;
  const parts = state === 'produced' && cp8 ? cp8Parts(cp8) : null;
  const since = pack && pack.prior && pack.prior.as_of ? `Since ${fmtDate(pack.prior.as_of)}` : 'Since the earlier run';
  const heading = `<h2 class="changes-heading">${esc(`${since} · ${pathway}`)}</h2>`;
  let notice = '';
  if (state === 'not_produced') {
    notice = `<div class="caution changes-not-produced" role="note"><strong>The explanation of what changed was not produced for this run.</strong><p>${esc(`Recorded reason: ${changes.note.replace(REASON_PREFIX, '')}`)}</p></div>`;
  } else if (state === 'unreadable') {
    notice = `<div class="caution changes-unreadable" role="note"><strong>The comparison with the earlier run could not be read.</strong><p>${esc(changes.problem)}</p></div>`;
  } else if (!parts) {
    notice = '<div class="caution changes-not-produced" role="note"><strong>CP-8’s explanation is not held for this run.</strong><p>The comparison pack is shown without it.</p></div>';
  }
  const sections = [
    parts ? whatChangedPart(parts) : '',
    pack ? issuerPart(pack, parts) : '',
    pack ? analysisPart(pack, parts) : '',
    parts ? limitationsPart(parts) : '',
    overTimePart(runs, fmtDate),
  ].join('');
  return `<div class="changes">${heading}${notice}${sections}</div>`;
}

return {changesState, cp8Parts, measureVerdict, differenceText, withUnit, thenAndNowChart, measureTable, netDebtView, maturityView, passageView, analysisPart, limitationsPart, overTimePart, leadBottom, changesHtml, FIRST_RUN, NOT_COMPARABLE};
})();

if (typeof module !== 'undefined') module.exports = ChangesView;

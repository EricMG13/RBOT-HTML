'use strict';
// Pure rendering of the Changes tab (docs/rulings/2026-11-11-module-presets-and-changes.md, decision M8): no DOM, no store, no globals written.
// Browser: one global, ChangesView (reader.js is loaded first; nothing else leaks into the page's scope). Node: module.exports.
// The page is the shared components' (components.js) drawing of CP-8's passages and tables, the way a module page draws them: its Bottom line, Key findings and what would
// change the view as C2, C5 and C6, each `change` table as C19, the `moduleState` table as C20, any other finding table by its shape, its Limitations beside the gap signal.
// The ledger (a register of what differs between the two runs) is Evidence's: the Gaps tab lists it as written, and this page keeps the counts and one link to it.
// Delivery adds no analysis and computes nothing. Every figure shown is text the comparison pack (`changes.json`, schema cpos-changes/2 or /3) or CP-8's
// handoff states, with its sign, unit and period: no rounding, no difference worked out here, no direction arrow. This page reads no register for a
// verdict: the library's build derives them once, with CP-8's checker (`changes.verdicts`: measures, modules, ledger), and the page displays them.
// A measure that is not comparable, is not judged, or has no verdict shows both values and no difference and no joining line. Chart positions are geometry only. All pack and handoff text is model output: it is
// escaped before it reaches the page.
const ChangesView = (() => {
const ChangesReader = typeof module !== 'undefined' ? require('./reader.js') : {escapeHtml, richText, plainText, paragraphBody, passageControls, readerPassages, sectionBodyHtml, isNewFormat};
const Shapes = typeof module !== 'undefined' ? require('./shapes.js') : window.Shapes;
const Components = typeof module !== 'undefined' ? require('./components.js') : window.Components;
const Evidence = typeof module !== 'undefined' ? require('./evidence.js') : window.Evidence;

const FIRST_RUN = 'First run of this pathway';
const NO_RECORD = 'No comparison was recorded for this run';
const NOT_COMPARABLE = 'Not comparable';
const NOT_STATED = 'Not stated';
const TREND_MEASURES = [['leverage', 'Total debt / EBITDA'], ['net_leverage', 'Net debt / EBITDA'], ['coverage', 'EBITDA / cash interest'], ['cash', 'Cash'], ['undrawn', 'Undrawn committed facilities']];
const REASON_PREFIX = /^changes: not produced\s*[—-]\s*/;
const esc = value => ChangesReader.escapeHtml(value);

// What the run says about its comparison. A first run is only a run whose own record says it had no prior (`first_run`); a run that records nothing
// (delivered before CP-8 existed, or an earlier format) is 'unrecorded': absence of data is never read as a first run. A pack that could not be read is neither.
function changesState(changes) {
  if (!changes) return 'unrecorded';
  if (changes.problem) return 'unreadable';
  if (changes.note) return 'not_produced';
  if (changes.pack) return 'produced';
  return changes.first_run === true ? 'first' : 'unrecorded';
}

// A value with its unit as the pack states them: `x` and `%` follow the figure, any other unit follows after a space.
const withUnit = (value, unit) => (unit == null || unit === '' ? String(value) : /^[x%]$/.test(unit) ? `${value}${unit}` : `${value} ${unit}`);
const sideText = side => (side && side.value != null ? `${withUnit(side.value, side.unit)}${side.period ? ` (${side.period})` : ''}` : NOT_STATED);

// Whether the two values of a measure may be set against each other, and so whether its difference may be shown: the verdict the build derived
// (`changes.verdicts.measures[key]`: kind comparable | not_comparable | unjudged, label, reason, analysis_change). A measure with no entry, an unknown kind,
// or a run with no verdicts is not judged: no difference, no line.
const NOT_JUDGED = 'Comparability not judged';
function measureVerdict(measure, changes) {
  const found = changes && changes.verdicts && changes.verdicts.measures ? changes.verdicts.measures[measure.key] : null;
  if (!found || !['comparable', 'not_comparable', 'unjudged'].includes(found.kind)) return {kind: 'unjudged', label: NOT_JUDGED, reason: measure.reason || null};
  return {kind: found.kind, label: found.label, reason: found.reason || null, analysisChange: found.analysis_change || null};
}

const differenceText = (measure, verdict) => (verdict.kind === 'comparable' && measure.difference != null ? withUnit(measure.difference, measure.unit) : null);

// A closed fold for a table whose figures a card or a chart already shows (print opens it).
const fold = (label, inner) => `<details class="chg-fold"><summary><span>${esc(label)}</span><span class="chg-fold-ch" aria-hidden="true">${Components.icon('chevron-down')}</span></summary>${inner}</details>`;

// ---- The comparison's own figures. The pack (`changes.json`) holds each measure's two values as the two runs state them and, beside them, differences the BUILD worked out from those values
// (src/deploy_workflow/changes.py). No CP-8 text states them, so they are not findings: this page draws none. They are Evidence's: `comparisonEvidence` is the input the Evidence page lists
// with the calculations of the module that holds the comparison, the difference in a column headed to say who computed it.
const COMPUTED = 'Difference computed by the comparison';
const nonZero = value => value != null && Number(value) !== 0;
const SAME_DATE_NET_DEBT = 'Both runs state net debt for the same date; the difference is between the two analyses, not a change in the issuer.';
const NO_ROW = {line: 0};
const evidenceTable = (headers, rows) => ({line: 0, headers, rows: rows.map(cells => ({...NO_ROW, cells}))});
function netDebtEntry(change) {
  const shown = value => (value == null ? NOT_STATED : withUnit(value, change.unit));
  // Rows of one period with two values and a non-zero difference are the analysis changing, not the issuer: the difference is not listed as a change.
  const analysis = change.same_period === true && [change.change_in_gross_debt, change.change_in_cash].some(nonZero);
  const diff = value => (value == null || analysis ? '—' : shown(value));
  const span = change.prior_period && change.current_period ? ` (${change.prior_period} to ${change.current_period})` : '';
  return {heading: `Net debt${span}`, notes: [...(analysis ? [SAME_DATE_NET_DEBT] : []), ...(change.convention ? [change.convention] : [])],
    tables: [evidenceTable(['Item', 'Earlier', 'Current', COMPUTED], [['Gross debt', shown(change.prior_gross_debt), shown(change.current_gross_debt), diff(change.change_in_gross_debt)],
      ['Cash', shown(change.prior_cash), shown(change.current_cash), diff(change.change_in_cash)], ['Net debt', shown(change.prior_net_debt), shown(change.current_net_debt), '—']])]};
}
function comparisonEvidence(pack, changes, module) {
  if (!pack) return null;
  const entries = [], measures = pack.measures || [];
  if (measures.length) {
    const rows = measures.map(measure => {
      const verdict = measureVerdict(measure, changes), difference = differenceText(measure, verdict);
      const comparable = [...(verdict.reason && verdict.reason.startsWith(verdict.label) ? [verdict.reason] : [verdict.label, verdict.reason]), verdict.analysisChange ? `The analysis changed, not the issuer: ${verdict.analysisChange}` : null].filter(Boolean).join('. ');
      return [measure.label, sideText(measure.prior), sideText(measure.current), difference === null ? '—' : difference, comparable];
    });
    entries.push({heading: 'Comparison measures', notes: [], tables: [evidenceTable(['Measure', 'Earlier', 'Current', COMPUTED, 'Comparability'], rows)]});
  }
  if (pack.net_debt_change) entries.push(netDebtEntry(pack.net_debt_change));
  const profile = pack.maturity_profile;
  if (profile && profile.rows.length) {
    entries.push({heading: `Debt maturities, ${profile.unit}`, notes: [], tables: [evidenceTable(['Period', 'Earlier', 'Current', COMPUTED], profile.rows.map(r => [r.period, r.prior == null ? NOT_STATED : r.prior, r.current == null ? NOT_STATED : r.current, r.difference == null ? '—' : r.difference]))]});
  }
  const omitted = Object.entries(pack.omitted || {}).map(([name, reason]) => `${name === 'net_debt_change' ? 'Net debt change' : name === 'maturity_profile' ? 'Maturity profile' : name} is not listed: ${reason}.`);
  if (omitted.length) entries.push({heading: 'Not listed', notes: omitted, tables: []});
  return entries.length ? {module, entries} : null;
}

// ---- Part 2: the issuer. The maturity profile is each run's stated values as paired bars, in a card with the shared Chart/Table toggle (chart by default; print shows the table too).
// Two series colours that are neither status colours: `.chg-bar.e` (earlier) and `.chg-bar.c` (current).
function maturityView(profile) {
  if (!profile || !profile.rows.length) return '';
  const rows = profile.rows, caption = `Debt maturities, ${profile.unit}`;
  const top = Math.max(0, ...rows.flatMap(r => [r.prior, r.current]).map(Number).filter(Number.isFinite));
  const width = value => (value == null || !Number.isFinite(Number(value)) || top === 0 ? 0 : (Number(value) / top) * 100);
  const bar = (cls, value) => `<span class="chg-bar-row"><i class="chg-bar ${cls}" style="width:${width(value)}%"></i><span class="chg-bv">${esc(value == null ? NOT_STATED : value)}</span></span>`;
  const bars = rows.map(r => `<div class="chg-mat-row"><span class="chg-mat-k">${esc(r.period)}</span><div>${bar('e', r.prior)}${bar('c', r.current)}</div></div>`).join('');
  const legend = '<div class="chg-mat-legend"><span><i class="chg-bar e"></i>Earlier run</span><span><i class="chg-bar c"></i>Current run</span></div>';
  const block = {headers: ['Period', 'Earlier', 'Current'], rows: rows.map((r, at) => ({line: at, cells: [r.period, r.prior == null ? NOT_STATED : r.prior, r.current == null ? NOT_STATED : r.current]}))};
  const toggle = Components.viewToggle(`${caption}: chart or table`, [['chart', 'Chart'], ['table', 'Table']]);
  const figure = `<div class="chg-mat-fig" role="region" aria-label="${esc(`${caption}, chart`)}" tabindex="0">${legend}${bars}</div>`;
  return `<article class="fc-card chg-mat" data-block data-view="chart" aria-label="${esc(caption)}"><div class="fc-head"><div class="fc-title"><h3>Maturity profile</h3><span class="fc-unit">${esc(profile.unit)}</span></div><div class="fc-tools">${toggle}</div></div>${Components.pane('chart', figure, true)}${Components.pane('table', Components.chartTable(block, {caption}), false)}</article>`;
}

// `cards` is CP-8's `change` tables drawn as C19 (empty when the handoff has none or is not held). No cards, no maturity profile and nothing to say: no part.
function issuerPart(pack, parts, cards = '') {
  const missing = parts && !parts.legacy && !cards ? '<p class="intro">The Changes handoff has no table of what changed in the issuer.</p>' : '';
  const inner = `${cards}${missing}${maturityView(pack.maturity_profile)}`;
  return inner ? `<section class="run-section" id="changes-issuer"><h2>The issuer</h2>${inner}</section>` : '';
}

// ---- CP-8's own page, drawn as a module page draws a handoff (the same components and reader functions). `sections` are the store's; `output` is {id, module, run, chips(key)}.
// Passages: Bottom line (C2), Key findings (C5), what would change the view (C6), Limitations (the list and the gap signal). Every finding section is drawn by its tables' shapes:
// a section with a `change` table is the issuer part (C19 cards), one with a `moduleState` table the analysis part (C20 tiles), any other keeps its own heading.
// A section whose role is Evidence's (sources, calculations, gaps, registers) or nobody's (hidden) is not drawn: the ledger is one of them.
const textsOf = section => (section ? section.blocks.filter(b => b.type === 'text').map(b => ({text: b.text, line: b.line})) : []);
const drawsSomething = section => section.blocks.some(b => (b.type === 'table' ? b.rows.length > 0 && Shapes.hiddenColumns(b.headers, 'records').length < b.headers.length : Shapes.blockRole(b.text) !== 'note'));
function cp8Page(sections, output, counts) {
  const out = {id: 'cp8', module: 'CP-8', run: null, chips: () => 0, ...output};
  const passages = ChangesReader.readerPassages(sections), held = new Set(Object.values(passages).filter(Boolean));
  const texts = Object.fromEntries(Object.entries(passages).map(([key, section]) => [key, textsOf(section)]));
  const controls = key => ChangesReader.passageControls(texts[key], {id: out.id, chips: out.chips});
  const tables = sections.flatMap(section => section.blocks.filter(b => b.type === 'table'));
  const tokens = Shapes.idTokens(sections), pairing = Shapes.casePairing(tables), registers = Evidence.href('registers', out.module, out.run);
  const ctxOf = section => ({countNoun: 'modules', tokens, pairing, id: out.id, section, module: out.module, evidenceHref: registers, key: row => `${out.id}:${row.line}`, trace: (row, label) => Components.traceRow(`${out.id}:${row.line}`, label), caption: headingOf(section)});
  const skip = block => block.type === 'text' && (Shapes.blockRole(block.text) === 'note' || (!block.text.startsWith('```') && Shapes.methodNote(Components.paragraphText(block.text), tokens) !== null));
  const bodyOf = section => ChangesReader.sectionBodyHtml(section, {id: out.id, tables: true, chips: out.chips, caption: headingOf, skip, table: (block, at) => Components.render(Shapes.tableShape(block), block, ctxOf(at))});
  const drawn = Evidence.classify(sections).filter(({section, role}) => role === 'finding' && !held.has(section) && section.blocks.length > 0 && drawsSomething(section))
    .map(({section}) => ({section, body: bodyOf(section), shapes: section.blocks.filter(b => b.type === 'table').map(Shapes.tableShape)})).filter(item => item.body.trim() !== '');
  const group = shape => drawn.filter(item => item.shapes.includes(shape));
  const issuer = group('change'), analysis = group('moduleState').filter(item => !issuer.includes(item)), other = drawn.filter(item => !issuer.includes(item) && !analysis.includes(item));
  const joined = items => items.map(item => `${items.length > 1 ? `<h3 class="chg-sec-h">${esc(headingOf(item.section))}</h3>` : ''}${item.body}`).join('');
  const verdict = Components.verdictPanel(texts.bottom, controls('bottom').trace, controls('bottom').figure, 'h3');
  const feed = Components.findingsFeed(texts.key, controls('key').trace, controls('key').figure);
  const contrary = Components.callout('What would change the view', texts.contrary, controls('contrary').trace, controls('contrary').figure, 'h3');
  const why = feed || contrary ? `<div class="g24 chg-why">${feed ? `<div class="${contrary ? 'c14' : 'c24'}"><div class="rd-card"><h3 class="rd-h">Key findings</h3>${feed}</div></div>` : ''}${contrary ? `<div class="${feed ? 'c10' : 'c24'}">${contrary}</div>` : ''}</div>` : '';
  const limits = Components.limitationsBlock(texts.limits, counts.gaps, Evidence.href('gaps', out.module, out.run), controls('limits').trace, controls('limits').figure);
  return {
    lead: verdict || why ? `<section class="run-section chg-lead" id="changes-what"><h2 class="sr-only">What changed</h2>${verdict}${why}</section>` : '',
    issuer: joined(issuer), analysis: joined(analysis),
    other: other.map(item => `<section class="run-section chg-other"><h2>${esc(headingOf(item.section))}</h2>${item.body}</section>`).join(''),
    limits, ledgerRows: counts.ledger, gapsHref: Evidence.href('gaps', out.module, out.run),
  };
}
const headingOf = section => ChangesReader.plainText(section.heading).replace(Shapes.METHOD_CODE, '');

// ---- Part 3: the analysis. `tiles` is CP-8's `moduleState` table as C20 (one counted tile for each state that repeats). Beneath it, one row per module of the pack with each run's own
// bottom line; CP-8's status and reason are the build's (`changes.verdicts.modules[code]`, only a code with exactly one row).
// A run's bottom line for one module as the pack quotes it (the first paragraph of that handoff's Bottom line) is a passage, drawn as a module's page draws its Bottom line:
// the Basis line and list marker dropped, **bold** as emphasis, nothing held back.
function bottomLineHtml(text) {
  return ChangesReader.richText(Components.paragraphText(text)).replace(/(?<![*\w])\*([^*\s](?:[^*]*[^*\s])?)\*(?![*\w])/g, '<em>$1</em>');
}
// `view`: {name(code) -> the module's catalogue title or null}; without it a module keeps the pack's own name.
function analysisPart(pack, parts, changes, tiles = '', view = {}) {
  const modules = (changes && changes.verdicts && changes.verdicts.modules) || {};
  const rows = (pack.modules || []).map(m => {
    const row = Object.prototype.hasOwnProperty.call(modules, m.module) ? modules[m.module] : null;
    const state = !parts ? 'Explanation not produced' : row ? row.status || NOT_STATED : `${NOT_STATED} by Changes since the last run`;
    const paragraph = html => (html.trim() === '' ? '' : `<p>${html}</p>`);  // a bottom line with no words (empty, or only its Basis line) draws no paragraph
    const side = (ran, text) => (text != null ? bottomLineHtml(text) : esc(ran ? NOT_STATED : 'Did not run'));
    const earlier = side(m.ran_prior, m.prior_bottom_line), current = side(m.ran_current, m.current_bottom_line), title = (view.name && view.name(m.module)) || m.title;
    const reason = row ? [row.cause, row.why].filter(Boolean) : [];
    return `<details class="change-module"><summary><span class="change-name">${esc(title)}</span><span class="badge badge-gray change-status">${esc(state)}</span><span class="change-then"><small>Earlier</small>${earlier}</span><span class="change-now"><small>Current</small>${current}</span></summary><div class="change-pair"><section><h4>Earlier</h4>${paragraph(earlier)}</section><section><h4>Current</h4>${paragraph(current)}</section></div>${reason.length ? `<p class="change-why">${esc(reason.join(' · '))}</p>` : ''}</details>`;
  }).join('');
  const missing = parts && !parts.legacy && !tiles ? '<p class="intro">The Changes handoff has no table of what changed in the analysis.</p>' : '';
  return `<section class="run-section" id="changes-analysis"><h2>The analysis</h2>${tiles}${missing}${tiles ? '<h3 class="chg-sec-h">Each module’s bottom line, earlier and current</h3>' : ''}<p class="intro">One row per module. A row opens the earlier and current bottom lines side by side.</p><div class="change-modules">${rows}</div></section>`;
}

// ---- Part 4: the Limitations (CP-8's list beside the gap signal), and under them the ledger's counts of each status as one bar (segment sizes are the counts, the build's:
// `changes.verdicts.ledger`, null when it could not read the ledger) with the one link to the ledger itself, which Evidence lists as written. No ledger and no passage, no part.
function limitationsPart(parts, changes) {
  const counts = changes && changes.verdicts ? changes.verdicts.ledger : null;
  let summary = '';
  if (counts) {
    const label = counts.map(([name, n]) => `${name} ${n}`).join(', ');
    const segments = counts.filter(([, n]) => n > 0).map(([name, n]) => `<i class="ledger-${esc(name.toLowerCase().replace(/\W+/g, '-'))}" style="flex-grow:${n}" title="${esc(`${name} ${n}`)}"></i>`).join('');
    const legend = counts.map(([name, n]) => `<span><i class="ledger-${esc(name.toLowerCase().replace(/\W+/g, '-'))}"></i>${esc(name)} <strong>${n}</strong></span>`).join('');
    summary += `<div class="ledger-bar" role="img" aria-label="${esc(`Limitations: ${label}`)}">${segments}</div><div class="chart-legend ledger-legend">${legend}</div>`;
  }
  if (parts.ledgerRows > 0) summary += `<p class="chg-ledger-link"><a class="text-action" href="${esc(parts.gapsHref)}">Limitations ledger in Evidence<span class="chg-n">${parts.ledgerRows}</span>${Components.icon('arrow-right')}</a></p>`;
  if (!parts.limits && !summary) return '';
  return `<section class="run-section" id="changes-limitations"><div class="rd-card"><h2 class="rd-h">Limitations</h2>${parts.limits}${summary ? `<div class="chg-ledger">${summary}</div>` : ''}</div></section>`;
}

// ---- Part 5: every listed run of the issuer and pathway, earliest first. `runs` is [{key, href, asOf, runId, current, bottom, metrics, changes}], `runId` being the run's folder name (the pack names its prior run by folder):
// `metrics` are the library's own quotes ({value, unit, period} per measure), `changes` the run's record (pack and verdicts).
// A segment joins two neighbouring points only where the later run's own pack compares exactly those two values under one definition.
function joined(runs, i, key) {
  const [before, after] = [runs[i - 1], runs[i]];
  const [a, b] = [before.metrics && before.metrics[key], after.metrics && after.metrics[key]];
  const pack = after.changes && after.changes.pack;
  if (!a || !b || !pack || a.unit !== b.unit || !pack.prior || pack.prior.run !== before.runId) return false;
  const measure = (pack.measures || []).find(m => m.key === key);
  if (!measure || !measure.prior || !measure.current || measure.prior.value !== a.value || measure.current.value !== b.value) return false;
  if (measure.prior.period !== a.period || measure.current.period !== b.period) return false;
  const verdict = measureVerdict(measure, after.changes);
  return verdict.kind === 'comparable' && !verdict.analysisChange;
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
  return `<section class="run-section" id="changes-over-time"><h2>Over time</h2><p class="intro">Every listed run of this issuer and pathway, earliest first, with the figures the library quotes for each. A line joins two runs only where the later run's comparison states that the definitions match; otherwise the points stand alone.</p><ul class="trend-list">${lines}</ul>${fold('The figures and bottom lines as a table', `<div class="table-scroll" role="region" aria-label="Over time" tabindex="0"><table class="history-table"><caption>Figures and the lead module's bottom line at each date</caption><thead><tr>${head.map(h => `<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>`)}</section>`;
}

// The lead module's bottom line as its handoff states it: the first paragraph under Bottom line (Basis line dropped), or an earlier-format Reader summary's.
function leadBottom(sections, summary) {
  const bottom = ChangesReader.readerPassages(sections || []).bottom;
  const first = bottom && bottom.blocks.find(b => b.type === 'text');
  if (first) return ChangesReader.paragraphBody(first.text).body;
  return summary && summary.bottomLine != null ? summary.bottomLine : null;
}

// The whole tab. `input`: {changes, cp8 (sections|null), output ({id, module, run, chips(key)} of the CP-8 handoff), pathway (words), fmtDate(iso), overviewHref, runs}.
const EARLIER_FORMAT = 'It is in the earlier format, which has no bottom line or key findings; the module-by-module comparison is shown on its own.';
function emptyBlock(title, line, overviewHref) {
  return `<section class="run-section chg-empty">${Components.emptyState(title, [esc(line)], `<p class="chg-empty-go"><a class="text-action" href="${esc(overviewHref)}">Open the Overview${Components.icon('arrow-right')}</a></p>`)}</section>`;
}
function changesHtml(input) {
  const {changes, cp8, pathway, fmtDate, runs} = input;
  const state = changesState(changes), overviewHref = input.overviewHref || '#W-Overview/overview';
  if (state === 'first') return `<div class="changes">${emptyBlock('Nothing to compare yet', FIRST_RUN, overviewHref)}</div>`;
  if (state === 'unrecorded') return `<div class="changes">${emptyBlock('No comparison recorded', NO_RECORD, overviewHref)}${runs.length > 1 ? overTimePart(runs, fmtDate) : ''}</div>`;
  const pack = changes.pack || null;
  // `parts` is what CP-8 supplies: its drawn page when the handoff is in the current format, a bare marker when it is held in the earlier one, null when it is not held.
  const held = state === 'produced' && cp8 ? cp8 : null;
  const current = held ? ChangesReader.isNewFormat(held) : false;
  // The gap signal and the ledger's row count are the Evidence page's own enumeration for the module (every saved output), from the evidence input the page gathers.
  const module = (input.output && input.output.module) || 'CP-8';
  const counts = input.evidence ? {gaps: Evidence.gapCount(input.evidence, module), ledger: Evidence.ledgerCount(input.evidence, module)} : {gaps: 0, ledger: 0};
  const parts = held ? (current ? cp8Page(held, input.output, counts) : {legacy: true}) : null;
  // The two runs are named by period and pathway. When both names are the same line, fixed words say which is which.
  const earlierName = pack && pack.prior && pack.prior.as_of ? `${fmtDate(pack.prior.as_of)} · ${pathway}` : null, thisName = pack && pack.current && pack.current.as_of ? `${fmtDate(pack.current.as_of)} · ${pathway}` : null;
  const same = earlierName !== null && earlierName === thisName;
  const title = same ? `${esc(`Earlier run · ${earlierName}`)}<span class="chg-to" aria-hidden="true">${Components.icon('arrow-right')}</span>${esc(`This run · ${thisName}`)}` : esc(`${earlierName === null ? 'Since the earlier run' : `Since ${earlierName.split(' · ')[0]}`} · ${pathway}`);
  const now = !same && thisName ? `<p class="chg-now">This run: ${esc(thisName)}</p>` : '';
  const heading = `<header class="chg-top"><span class="chg-top-i" aria-hidden="true">${Components.icon('git-compare')}</span><div><h2 class="changes-heading">${title}</h2>${now}</div></header>`;
  let notice = '';
  if (state === 'not_produced') {
    notice = `<div class="caution changes-not-produced" role="note"><strong>The explanation of what changed was not produced for this run.</strong><p>${esc(`Recorded reason: ${changes.note.replace(REASON_PREFIX, '')}`)}</p></div>`;
  } else if (state === 'unreadable') {
    notice = `<div class="caution changes-unreadable" role="note"><strong>The comparison with the earlier run could not be read.</strong><p>${esc(changes.problem)}</p></div>`;
  } else if (!parts) {
    notice = '<div class="caution changes-not-produced" role="note"><strong>The explanation of the changes is not held for this run.</strong><p>The module-by-module comparison is shown without it.</p></div>';
  }
  // The comparison's own figures are Evidence's (Calculations tab, the module's filter when the run has that module); one link from every state that has a comparison.
  const evidenceRun = input.evidence ? input.evidence.run.context : input.output && input.output.run;
  const hasModule = Boolean(input.evidence && input.evidence.modules.some(m => m.id === module));
  const figures = pack && comparisonEvidence(pack, changes, module) ? `<p class="chg-figures-link"><a class="text-action" href="${esc(Evidence.href('calculations', hasModule ? module : null, evidenceRun))}">Comparison figures in Evidence${Components.icon('arrow-right')}</a></p>` : '';
  const stated = parts && !parts.legacy;
  const what = !parts ? '' : stated ? (parts.lead || `<section class="run-section" id="changes-what"><h2>What changed</h2><p class="empty">${NOT_STATED} in the Changes handoff.</p></section>`)
    : `<section class="run-section" id="changes-what"><h2>What changed</h2><p class="empty">${NOT_STATED} in the Changes handoff. ${EARLIER_FORMAT}</p></section>`;
  const sections = [
    what,
    pack ? issuerPart(pack, parts, stated ? parts.issuer : '') : '',
    pack ? analysisPart(pack, parts, changes, stated ? parts.analysis : '', input.modules) : '',
    stated ? parts.other : '',
    stated ? limitationsPart(parts, changes) : '',
    overTimePart(runs, fmtDate),
  ].join('');
  return `<div class="changes">${heading}${notice}${figures}${sections}</div>`;
}

return {changesState, measureVerdict, differenceText, withUnit, comparisonEvidence, maturityView, analysisPart, overTimePart, leadBottom, changesHtml, FIRST_RUN, NO_RECORD, NOT_COMPARABLE};
})();

if (typeof module !== 'undefined') module.exports = ChangesView;

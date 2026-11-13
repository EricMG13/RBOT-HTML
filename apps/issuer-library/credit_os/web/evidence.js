'use strict';
// The Evidence page: a governance summary, then tabs by kind (summary, trace, sources, calculations, gaps, registers, run record).
// All audit, tracing and governance material of a run lives here: IDs, hashes, file names, Basis items, calculation rows.
// Roles come from Shapes.sectionRole, columns from Shapes.columnKind; no heading or module id is read here (rule 6).
// Rule 7: a `hidden` section and a column of kind inter-module are drawn nowhere. They stay in the downloadable handoff.
// Pure builders take data and return markup strings; the browser part at the end (click, search) touches the page.
// Browser: window.Evidence. Node: module.exports (the tests).
(() => {
  const shapes = typeof module !== 'undefined' ? require('./shapes.js') : window.Shapes;
  const components = () => (typeof module !== 'undefined' ? require('./components.js') : window.Components);
  // reader.js declares these at the top level of a classic script, so the page reaches them by name once it has loaded.
  const reader = () => (typeof module !== 'undefined' ? require('./reader.js') : {escapeHtml, richText, plainText, splitBasis, basisItem, paragraphBody});
  const esc = value => reader().escapeHtml(value);
  const rich = value => reader().richText(value);
  const plain = value => reader().plainText(value);
  const icon = name => components().icon(name);

  const PAGE = 40; // trace rows shown at first and per "Show more"
  const TABS = [
    ['summary', 'Summary', 'layout-grid', ''],
    ['trace', 'Trace', 'trace', 'Each findings statement with the sources it cites; open one to read the excerpt.'],
    ['sources', 'Sources', 'files', 'The supplied files, which modules read each, and their hashes.'],
    ['calculations', 'Calculations', 'activity', 'The calculation tables of each module.'],
    ['gaps', 'Gaps', 'triangle-alert', 'The gaps each module records, with severity where it gives one.'],
    ['registers', 'Registers', 'folder-open', 'Tables and notes as the handoffs wrote them. Pick a module.'],
    ['record', 'Run record', 'settings-2', 'Steps, input hashes, instructions sent and model calls.'],
  ];
  const TAB_IDS = TABS.map(tab => tab[0]);

  // ---- routes ----
  // `#W-Evidence/<tab>?c=<run>&m=<module>`. An unknown or undecodable tab opens the summary; a module the run lacks is ignored.
  function parseHash(hash, moduleIds = []) {
    const [path, query = ''] = String(hash).replace(/^#/, '').split('?');
    const section = path.split('/')[1];
    let tab = null;
    try { tab = section === undefined ? null : decodeURIComponent(section); } catch (error) { if (!(error instanceof URIError)) throw error; }
    const module = new URLSearchParams(query).get('m');
    return {tab: TAB_IDS.includes(tab) ? tab : 'summary', module: module !== null && moduleIds.includes(module) ? module : null};
  }
  function href(tab, module, context) {
    const params = new URLSearchParams();
    if (context) params.set('c', context);
    if (module) params.set('m', module);
    return `#W-Evidence/${encodeURIComponent(tab)}${params.size ? `?${params}` : ''}`;
  }

  // ---- data: one pass over every handoff of the run, by role ----
  const shownOrNot = value => (value === null || value === undefined || value === '' ? 'Not recorded' : String(value));
  const count = (n, one, many) => `${n} ${n === 1 ? one : many}`;
  // The table as written minus the columns that address another module; no column left (or no row), no table.
  function tableView(block) {
    const keep = block.headers.map((header, at) => at).filter(at => shapes.columnKind(block.headers[at]) !== 'intermodule');
    if (!keep.length || !block.rows.length) return null;
    return {line: block.line, headers: keep.map(at => block.headers[at]), rows: block.rows.map(row => ({line: row.line, cells: keep.map(at => row.cells[at] ?? '')}))};
  }
  // Each section with the chain of headings from its level-2 ancestor down, and its role.
  function classify(sections, placement) {
    const stack = [];
    return sections.map((section, at) => {
      while (stack.length && stack[stack.length - 1].level >= section.level) stack.pop();
      stack.push(section);
      const chain = stack.filter(s => s.level >= 2).map(s => s.heading);
      return {section, chain, role: shapes.sectionRole(chain, placement?.[at])};
    });
  }
  const knownFiles = ev => [...ev.sources, ...ev.unused, ...(ev.unrecorded || [])].map(f => f.name).filter(Boolean);
  // One module's content: trace statements, calculation, gap and register entries, finding tables as written, method notes.
  function moduleContent(mod, input) {
    const known = knownFiles(input.run.evidence);
    const content = {id: mod.id, name: input.deps.moduleTitle(mod.id), trace: [], calcs: [], gaps: [], regs: [], written: [], notes: [], calcNotes: [], regNotes: []};
    for (const output of mod.outputs) {
      const tokens = shapes.idTokens(output.sections);
      for (const {section, chain, role} of classify(output.sections, output.placement)) {
        if (role === 'hidden') continue;
        const texts = section.blocks.filter(b => b.type === 'text'), tables = section.blocks.filter(b => b.type === 'table').map(tableView).filter(Boolean);
        const entry = {heading: section.heading, label: chain.length > 1 ? section.heading : '', notes: texts.map(b => b.text), tables};
        const keep = entry.notes.length || tables.length;
        if (role === 'calculations' && keep) content.calcs.push(entry);
        else if (role === 'gaps' && keep) content.gaps.push(entry);
        else if (role === 'registers' && tables.some(shapes.isLedger)) {
          // A comparison ledger lists what differs between two runs: it is a gap register, drawn as written on the Gaps tab. The section's other tables and its prose stay in Registers.
          const others = {...entry, tables: tables.filter(table => !shapes.isLedger(table))};
          if (others.notes.length || others.tables.length) content.regs.push(others);
          content.gaps.push({heading: section.heading, label: entry.label, notes: [], tables: tables.filter(shapes.isLedger), ledger: true});
        } else if ((role === 'sources' || role === 'registers') && keep) content.regs.push(entry);
        else if (role === 'finding' || role === 'drawing' || role === 'passage') {
          for (const table of tables) content.written.push({heading: section.heading, table});
          for (const block of texts) {
            if (role === 'finding' && shapes.blockRole(block.text) === 'note') { content.notes.push({heading: section.heading, text: block.text}); continue; }
            if (role === 'drawing') continue;
            // Ruling 2026-11-13: a finding paragraph holding an identifier, or naming a calculation, is not on the findings page; it is a method note here.
            const kind = role === 'finding' && !block.text.startsWith('```') ? shapes.methodNote(reader().paragraphBody(block.text).body, tokens) : null;
            if (kind) (kind === 'calculations' ? content.calcNotes : content.regNotes).push({heading: section.heading, text: block.text});
            const split = reader().splitBasis(block.text, known);
            if (split.items.length) content.trace.push({mod: mod.id, name: content.name, key: `${output.id}:${block.line}`, heading: section.heading, body: split.body, items: split.items});
          }
        }
      }
    }
    return content;
  }
  // The rows the Gaps tab lists for one handoff's sections: those of its Gaps sections and of its comparison ledgers. The Overview's and the Changes page's gap signals count the same rows.
  const rowsOf = (sections, placement, wanted, keep) => classify(sections, placement).reduce((total, {section, role}) => (role !== wanted ? total
    : total + section.blocks.filter(b => b.type === 'table').map(tableView).filter(view => view && keep(view)).reduce((n, view) => n + view.rows.length, 0)), 0);
  const ledgerTotal = (sections, placement) => rowsOf(sections, placement, 'registers', shapes.isLedger);
  const gapTotal = (sections, placement) => rowsOf(sections, placement, 'gaps', () => true) + ledgerTotal(sections, placement);
  const contents = input => input.modules.map(mod => moduleContent(mod, input));
  const traceRows = input => contents(input).flatMap(c => c.trace);
  const rowTotal = entries => entries.reduce((n, entry) => n + entry.tables.reduce((k, t) => k + t.rows.length, 0), 0);
  const tableTotal = c => c.regs.reduce((n, e) => n + e.tables.length, 0) + c.written.length;
  const selected = (all, module) => (module ? all.filter(c => c.id === module) : all);

  // ---- small markup helpers ----
  const hay = (...parts) => esc(parts.map(part => plain(part ?? '')).join(' ').toLowerCase());
  const empty = (title, message) => `<div class="ev-empty">${icon('search')}<strong>${esc(title)}</strong><p>${esc(message)}</p></div>`;
  const NUMBER = /^[-−+]?(?:USD )?[\d,]*\.?\d+(?: ?(?:million|billion|x|%|pp))?(?: \(.*\))?$/;
  const numericColumn = cells => { const filled = cells.filter(c => c !== ''); return filled.length > 0 && filled.filter(c => NUMBER.test(c)).length / filled.length >= 0.7; };
  // `counted` is what the tab's badge counts: 'rows' (each row), 'table' (the whole table) or nothing. Counted elements carry data-hay; every other searchable one data-find.
  function tableMarkup(view, caption, name, counted = '') {
    const numeric = view.headers.map((header, at) => numericColumn(view.rows.map(r => r.cells[at])));
    const mono = view.headers.map(header => ['source', 'id'].includes(shapes.columnKind(header)));
    const head = view.headers.map((header, at) => `<th scope="col" class="${numeric[at] ? 'num' : ''}${mono[at] ? ' mono' : ''}">${esc(header)}</th>`).join('');
    const body = view.rows.map(row => `<tr ${counted === 'rows' ? 'data-hay' : 'data-find'}="${hay(name, row.cells.join(' '))}">${row.cells.map((cell, at) => `<td class="${numeric[at] ? 'num ' : ''}${mono[at] ? 'mono ' : ''}${cell.length > 60 ? 'wide' : ''}">${rich(cell)}</td>`).join('')}</tr>`).join('');
    const tableHead = hay(name, caption, view.headers.join(' '));
    return `<div class="ev-tbl" role="region" aria-label="${esc(caption)}" tabindex="0" data-group data-head="${tableHead}"${counted === 'table' ? ` data-hay="${tableHead}"` : ''}><table><caption class="sr-only">${esc(caption)}</caption><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }
  const noteMarkup = (text, name, counted = false) => `<p class="ev-note" ${counted ? 'data-hay' : 'data-find'}="${hay(name, text)}">${rich(text)}</p>`;
  const moduleHead = (c, n, one, many) => `<div class="ev-grp-h"><span>${esc(c.name)}</span><span class="ev-cd">${esc(c.id)}</span><span class="ev-ct"><span data-count>${n}</span> ${n === 1 ? one : many}</span></div>`;
  const subHead = label => (label ? `<h4 class="ev-sub">${esc(label)}</h4>` : '');

  // ---- panels ----
  function tracePanel(all, input) {
    const rows = all.flatMap(c => c.trace);
    if (!rows.length) return empty('Trace', 'No findings statement with a Basis line is listed for this selection.');
    const known = knownFiles(input.run.evidence);
    const html = rows.map((row, at) => `<div class="ev-trow"${at >= PAGE ? ' hidden' : ''} data-k="${at}" data-hay="${hay(row.name, row.heading, row.body, row.items.join(' '))}"><button type="button" aria-expanded="false"><span class="ev-mc"><span class="ev-mm">${esc(row.name)}</span><span class="ev-hh">${esc(row.heading)}</span></span><span class="ev-st-wrap"><span class="ev-st">${rich(row.body)}</span><span class="ev-bchips">${row.items.map(item => basisChip(item, known)).join('')}</span></span><span class="ev-chev">${icon('chevron-down')}</span></button></div>`).join('');
    return `${html}<button class="ev-btn ev-more" type="button" data-more${rows.length > PAGE ? '' : ' hidden'}>Show more (${Math.max(0, rows.length - PAGE)} remaining)</button>`;
  }
  function basisChip(raw, known) {
    const item = reader().basisItem(raw, known);
    const [cls, name] = item.kind === 'calculation' ? ['calc', null] : item.kind === 'source' ? ['', 'file-text'] : item.kind === 'module' ? ['mod', 'files'] : ['', null];
    return `<span class="ev-bc ${cls}" title="${esc(raw)}">${name ? icon(name) : ''}<span>${esc(raw)}</span></span>`;
  }
  function chipExcerpt(chip) {
    if (chip.kind !== 'issuer_page') {
      return `<div class="ev-exc"><div class="ev-exc-h">${chip.kind === 'upstream' ? `Upstream · ${esc([chip.module, ...(chip.codes || [])].filter(Boolean).join(' · '))}` : `Citation gap · ${esc(chip.label || 'no page')}`}</div></div>`;
    }
    const pages = chip.page_end != null && chip.page_end !== chip.page ? `${chip.page} to ${chip.page_end}` : `${chip.page}`;
    const match = chip.hash_matches_inventory === true ? `<span class="ev-ok">${icon('check')}hash matches inventory</span>` : chip.hash_matches_inventory === false ? `<span class="ev-no">${icon('triangle-alert')}hash does not match inventory</span>` : '';
    return `<div class="ev-exc"><div class="ev-exc-h"><span class="mono">${esc(chip.file)}</span><span>page ${esc(pages)}</span>${match}</div>${chip.excerpt ? `<pre>${esc(chip.excerpt)}</pre>` : ''}</div>`;
  }
  // The open row: the whole statement and the excerpts the build holds for its paragraph key.
  function traceBody(row, chips) {
    const found = (chips || {})[row.key] || [];
    return `<div class="ev-trow-b"><p class="ev-full">${rich(row.body)}</p>${found.length ? found.map(chipExcerpt).join('') : '<p class="ev-muted">No excerpt recorded for this statement.</p>'}</div>`;
  }

  const avatar = (code, deps) => `<span class="ev-av" role="img" tabindex="0" ${components().tipAttributes(deps.moduleTitle(code))}>${esc(code.replace(/^CP-/, ''))}</span>`;
  const copyButton = (text, label) => `<button class="ev-cpy" type="button" data-copy="${esc(text)}" data-tip="Copy" aria-label="Copy ${esc(label)}">${icon('copy')}</button>`;
  function fileCard(file, deps, counted = false) {
    const readers = file.readBy.length ? `<div><div class="ev-k">Read by</div><div class="ev-stack">${file.readBy.map(code => avatar(code, deps)).join('')}</div></div>` : '';
    return `<article class="ev-card ev-src" ${counted ? 'data-hay' : 'data-find'}="${hay(file.name, file.type, file.readBy.map(deps.moduleTitle).join(' '))}"><div class="ev-src-top"><span class="ev-src-ic">${icon(file.type === 'pdf' ? 'files' : 'file-text')}</span><div><div class="ev-src-n">${esc(file.name)}</div><span class="ev-src-t">${esc(shownOrNot(file.type))}</span></div></div>` +
      `<div><div class="ev-k">Document date</div><div>${esc(shownOrNot(file.documentDate))}</div></div>${readers}` +
      `<div><div class="ev-k">sha256</div><div class="ev-hash"><code title="${esc(file.sha256)}">${esc(shownOrNot(file.sha256))}</code>${file.sha256 ? copyButton(file.sha256, `hash of ${file.name}`) : ''}</div></div></article>`;
  }
  function sourcesPanel(input, module) {
    const {evidence: ev} = input.run, {deps} = input;
    const unrecorded = ev.unrecorded || [], cards = (files, counted = false) => `<div class="ev-src-g">${files.map(f => fileCard(f, deps, counted)).join('')}</div>`;
    // A run that records no supplied file is not one whose every file was used: missing is not zero.
    if (!ev.sources.length && !ev.unused.length && !unrecorded.length) return empty('Source files', 'The run record lists no supplied files.');
    const used = ev.sources.filter(f => !module || f.readBy.includes(module));
    const usedHtml = used.length ? cards(used, true) : empty('Source files', module ? `No source file is recorded as read by ${deps.moduleTitle(module)}.` : 'No handoff’s Sources section names a supplied file.');
    if (module) return usedHtml;
    const lacking = ev.noSourcesModules && ev.noSourcesModules.length && !unrecorded.length ? `<p class="ev-intro">No Sources section in the handoff of ${ev.noSourcesModules.map(code => esc(deps.moduleTitle(code))).join(', ')}, so a file those modules read may be listed here.</p>` : '';
    const unusedHtml = unrecorded.length && !ev.unused.length ? '' : `<h3 class="ev-sub-h">Supplied, not used <span class="ev-pill"><span data-count>${ev.unused.length}</span></span></h3>${lacking}${ev.unused.length ? cards(ev.unused) : '<p class="ev-intro">Every supplied file is named in a handoff’s Sources section.</p>'}`;
    const unrecordedHtml = unrecorded.length ? `<h3 class="ev-sub-h">Use not recorded <span class="ev-pill"><span data-count>${unrecorded.length}</span></span></h3><p class="ev-intro">None of this run’s handoffs has a Sources section, so the run does not record which supplied files were read.</p>${cards(unrecorded)}` : '';
    return `${usedHtml}${unusedHtml}${unrecordedHtml}`;
  }
  function calculationsPanel(all) {
    const groups = all.filter(c => c.calcs.length || c.calcNotes.length);
    if (!groups.length) return empty('Calculations', 'No calculation table is listed for this selection.');
    const notes = c => (c.calcNotes.length ? `<h4 class="ev-sub">Method notes <span class="ev-cnt"><span data-count>${c.calcNotes.length}</span></span></h4>${c.calcNotes.map(n => `${subHead(n.heading)}${noteMarkup(n.text, c.name, true)}`).join('')}` : '');
    return groups.map(c => `<section class="ev-grp" data-group>${rowTotal(c.calcs) ? moduleHead(c, rowTotal(c.calcs), 'calculation', 'calculations') : moduleHead(c, c.calcNotes.length, 'method note', 'method notes')}${c.calcs.map(e => `${subHead(e.label)}${e.notes.map(n => noteMarkup(n, c.name)).join('')}${e.tables.map(t => tableMarkup(t, `${c.name}: ${e.heading}`, c.name, 'rows')).join('')}`).join('')}${notes(c)}</section>`).join('');
  }
  const SEVERITY = {high: 3, medium: 2, low: 1};
  // A table of a gaps section is a list of gaps: a title, the other cells as fields, and a three-segment meter where the table has a severity column.
  function gapCards(view, c) {
    const severity = view.headers.findIndex(h => /severity/i.test(h)), title = Math.max(0, view.headers.findIndex(h => shapes.columnKind(h) !== 'id'));
    return `<div data-group>${view.rows.map(row => {
      const level = severity < 0 ? 0 : SEVERITY[row.cells[severity].trim().toLowerCase()] || 0;
      const meter = level ? `<span class="ev-meter" aria-hidden="true">${[1, 2, 3].map(n => `<i${n <= level ? ' class="f"' : ''}></i>`).join('')}</span>` : '';
      const fields = view.headers.map((header, at) => (at === title || row.cells[at] === '' ? '' : `<div><div class="ev-l">${esc(header)}</div><div class="ev-v">${at === severity ? meter : ''}${rich(row.cells[at])}</div></div>`)).join('');
      return `<div class="ev-gap" data-hay="${hay(c.name, row.cells.join(' '))}"><div class="ev-gap-t">${icon('triangle-alert')}<span>${rich(row.cells[title])}</span></div><div class="ev-gap-f">${fields}</div></div>`;
    }).join('')}</div>`;
  }
  function gapsPanel(all) {
    const groups = all.filter(c => c.gaps.length);
    if (!groups.length) return empty('Gaps', 'No gap is listed for this selection.');
    // A ledger is a table as written (counted by row); any other gap table is cards.
    const drawn = (e, c) => e.tables.map(t => (e.ledger ? tableMarkup(t, `${c.name}: ${e.heading}`, c.name, 'rows') : gapCards(t, c))).join('');
    return groups.map(c => `<section class="ev-grp" data-group>${moduleHead(c, rowTotal(c.gaps), 'gap', 'gaps')}${c.gaps.map(e => `${subHead(e.label)}${e.notes.map(n => noteMarkup(n, c.name)).join('')}${drawn(e, c)}`).join('')}</section>`).join('');
  }
  function registerGroup(title, n, inner) {
    return `<details class="ev-reg" open data-group><summary>${esc(title)}<span class="ev-cnt"><span data-count>${n}</span></span><span class="ev-ch">${icon('chevron-down')}</span></summary>${inner}</details>`;
  }
  function registersPanel(input, module, all) {
    if (!module) {
      const links = input.modules.map(m => `<a class="ev-fc" href="${esc(href('registers', m.id, input.run.context))}">${esc(input.deps.moduleTitle(m.id))}</a>`).join('');
      return `<div class="ev-empty">${icon('folder-open')}<strong>Pick a module</strong><p>Registers are read one module at a time. Choose a module in the filter bar or here.</p><div class="ev-fchips">${links}</div></div>`;
    }
    const c = all[0];
    if (!c || (!c.regs.length && !c.written.length && !c.notes.length && !c.regNotes.length)) return empty('Registers', 'This module has no register, table or method note to list.');
    const out = c.regs.map(e => registerGroup(e.heading, e.tables.reduce((n, t) => n + t.rows.length, 0), `${e.notes.map(n => noteMarkup(n, c.name)).join('')}${e.tables.map(t => tableMarkup(t, `${c.name}: ${e.heading}`, c.name, 'table')).join('')}`));
    if (c.written.length) out.push(registerGroup('Tables as written', c.written.length, c.written.map(w => `${subHead(w.heading)}${tableMarkup(w.table, `${c.name}: ${w.heading}`, c.name, 'table')}`).join('')));
    if (c.notes.length || c.regNotes.length) out.push(registerGroup('Method notes', c.notes.length + c.regNotes.length, `${c.notes.map(n => `${subHead(n.heading)}${noteMarkup(n.text, c.name)}`).join('')}${c.regNotes.map(n => `${subHead(n.heading)}${noteMarkup(n.text, c.name, true)}`).join('')}`));
    return out.join('');
  }

  // C13: steps per module with the start and accept times as recorded.
  function stepsMarkup(steps, deps) {
    if (!steps.length) return empty('Steps', 'The run record lists no step for this selection.');
    return `<ol class="ev-steps">${steps.map(s => `<li class="ev-step" data-hay="${hay(deps.moduleTitle(s.module), s.module, s.started, s.accepted)}"><span class="ev-sd">${icon('check')}</span><div class="ev-fr">${esc(deps.moduleTitle(s.module))} <span class="ev-cd">${esc(s.module)}</span></div><div class="ev-rl mono">Started ${esc(shownOrNot(s.started))}</div><div class="ev-rl mono">Accepted ${esc(shownOrNot(s.accepted))}</div></li>`).join('')}</ol>`;
  }
  function recordPanel(input, module) {
    const {run, deps} = input, r = run.evidence.record;
    const steps = run.steps.filter(s => !module || s.module === module);
    const changed = run.methodChanges.length ? `<div class="ev-sub-h">Methods changed since this run</div><ul class="ev-mc-list" data-group>${run.methodChanges.map(line => `<li data-find="${hay(deps.methodChange(line))}">${icon('git-compare')}<span class="mono">${esc(deps.methodChange(line))}</span></li>`).join('')}</ul>` : '';
    const hashes = r.hashes.length ? `<ul class="ev-hlist ev-card" data-group>${r.hashes.map(h => `<li data-find="${hay(deps.hashLabel(h.name), h.name, h.sha256)}"><div><div class="ev-nm">${esc(deps.hashLabel(h.name))}</div><code>${esc(shownOrNot(h.sha256))}</code></div>${h.sha256 ? copyButton(h.sha256, `hash of ${deps.hashLabel(h.name)}`) : ''}</li>`).join('')}</ul>` : '<p class="ev-intro">The run records no hash.</p>';
    const sent = r.instructions.filter(i => !module || i.module === module);
    const instructions = !r.instructions.length ? '<p class="ev-intro">The run records no instructions.</p>' : !sent.length ? '<p class="ev-intro">No instructions recorded for this module.</p>' : `<ul class="ev-hlist ev-card" data-group>${sent.map(i => `<li data-find="${hay(deps.moduleTitle(i.module), 'instructions')}"><div><div class="ev-nm">${i.href ? `<a class="ev-link" href="${esc(i.href)}" download aria-label="Download ${esc(deps.moduleTitle(i.module))} instructions">${esc(deps.moduleTitle(i.module))} instructions${icon('download')}</a>` : `${esc(deps.moduleTitle(i.module))} instructions <span class="ev-muted">No link</span>`}</div>${i.sha256 ? `<code>${esc(i.sha256)}</code>` : ''}</div>${i.sha256 ? copyButton(i.sha256, `hash of ${deps.moduleTitle(i.module)} instructions`) : ''}</li>`).join('')}</ul>`;
    const byModule = new Map();
    for (const call of r.calls) { if (!module || call.module === module) byModule.set(call.module, [...(byModule.get(call.module) || []), call]); }
    const calls = !r.calls.length ? '<p class="ev-intro">The run records no model call.</p>' : [...byModule].map(([code, list]) => `<details class="ev-call" data-group><summary>${esc(deps.moduleTitle(code))}<span class="ev-c">${count(list.length, 'call', 'calls')}</span><span class="ev-ch">${icon('chevron-down')}</span></summary>${tableMarkup({headers: ['Attempt', 'Started', 'HTTP status', 'Error', 'Settled (USD)'], rows: list.map(c => ({cells: [c.attempt, c.started, c.http_status, c.error_class, c.settled_usd].map(shownOrNot)}))}, `Model calls of ${deps.moduleTitle(code)}`, deps.moduleTitle(code))}</details>`).join('') || empty('Model calls', 'No model call is listed for this selection.');
    const cap = r.cap === null || r.cap === undefined || r.cap === '' ? 'Provider cap not recorded' : `Provider cap USD ${r.cap}`;
    return `<div class="ev-cols2"><div><div class="ev-sub-h">Steps by module</div>${stepsMarkup(steps, deps)}${changed}</div><div><div class="ev-sub-h">Input hashes</div>${hashes}<div class="ev-sub-h ev-gap-top">Instructions sent</div>${instructions}</div></div><div><div class="ev-sub-h">Model calls <span class="ev-cap-pill">${esc(cap)}</span></div>${calls}</div>`;
  }

  // ---- governance summary: C30 half-ring, tiles with counts, per-module gap bars, method changes, run record ----
  function governance(all, input) {
    const {run, deps} = input, ev = run.evidence;
    const delivered = input.modules.filter(m => m.outputs.length).length, total = input.modules.length, fraction = total ? delivered / total : 0;
    const gaps = all.map(c => rowTotal(c.gaps)), calcs = all.reduce((n, c) => n + rowTotal(c.calcs), 0), gapTotal = gaps.reduce((a, b) => a + b, 0), most = Math.max(1, ...gaps);
    const bars = all.map((c, at) => `<div class="ev-gb${gaps[at] ? '' : ' z'}" tabindex="0" role="img" ${components().tipAttributes(`${c.name}: ${count(gaps[at], 'gap', 'gaps')}`)}><b>${esc(c.id.replace(/^CP-/, ''))}</b><i style="width:${gaps[at] ? `${(gaps[at] / most * 100).toFixed(1)}%` : '2px'}"></i></div>`).join('');
    const arc = 'M12 78 A66 66 0 0 1 144 78';
    const first = run.steps[0], last = run.steps[run.steps.length - 1];
    const methods = run.methodChanges.length ? `<ul class="ev-mc-list">${run.methodChanges.map(line => `<li>${icon('git-compare')}<span class="mono">${esc(deps.methodChange(line))}</span></li>`).join('')}</ul>` : '<div class="ev-cap">None listed</div>';
    const cap = ev.record.cap === null || ev.record.cap === undefined || ev.record.cap === '' ? 'Provider cap not recorded' : `Provider cap USD ${ev.record.cap}`;
    const unusedCaption = !ev.sources.length && !ev.unused.length && (ev.unrecorded || []).length ? `use not recorded for ${count(ev.unrecorded.length, 'file', 'files')}` : `${ev.unused.length} supplied, not used`;
    return `<section class="ev-gov" aria-label="Governance summary">` +
      `<div><div class="ev-lab">Modules delivered</div><div class="ev-ring" role="img" aria-label="${delivered} of ${total} modules delivered"><svg viewBox="0 0 156 84" aria-hidden="true" focusable="false"><path class="rt" d="${arc}" pathLength="100"/><path class="rf" d="${arc}" pathLength="100" stroke-dasharray="100" stroke-dashoffset="${(100 - fraction * 100).toFixed(1)}"/></svg><div class="ev-rn"><span data-count>${delivered}</span><small>of <span data-count>${total}</span></small></div></div></div>` +
      `<div><div class="ev-lab">Source files</div><span class="ev-big" data-count>${ev.sources.length}</span><div class="ev-cap">${esc(unusedCaption)}</div></div>` +
      `<div><div class="ev-lab">Calculations recorded</div><span class="ev-big" data-count>${calcs}</span><div class="ev-cap">rows in the modules’ Calculations tables</div></div>` +
      `<div><div class="ev-lab">Gaps recorded</div><span class="ev-big" data-count>${gapTotal}</span><div class="ev-gbars">${bars}</div></div>` +
      `<div><div class="ev-lab">Methods changed since this run</div><span class="ev-big" data-count>${run.methodChanges.length}</span>${methods}</div>` +
      `<div><div class="ev-lab">Run record</div><div class="ev-rr"><div class="ev-ln"><span class="ev-pt"></span><div><div class="ev-l">Started</div><div class="ev-t">${esc(shownOrNot(first && first.started))}</div></div></div><div class="ev-ln"><span class="ev-bar"></span></div><div class="ev-ln"><span class="ev-pt e"></span><div><div class="ev-l">Accepted</div><div class="ev-t">${esc(shownOrNot(last && last.accepted))}</div></div></div></div><span class="ev-cap-pill">${esc(cap)}</span></div>` +
      `</section>`;
  }

  // ---- tabs, filter bar, the guide, the foot ----
  function tabCounts(all, input, module) {
    const ev = input.run.evidence;
    return {
      trace: all.reduce((n, c) => n + c.trace.length, 0),
      sources: ev.sources.filter(f => !module || f.readBy.includes(module)).length,
      calculations: all.reduce((n, c) => n + rowTotal(c.calcs) + c.calcNotes.length, 0),
      gaps: all.reduce((n, c) => n + rowTotal(c.gaps), 0),
      registers: all.reduce((n, c) => n + tableTotal(c) + c.regNotes.length, 0),
      record: input.run.steps.filter(s => !module || s.module === module).length,
    };
  }
  function filterBar(input, route) {
    const {context} = input.run;
    const chips = [['all', null, 'All'], ...input.modules.map(m => [m.id, m.id, input.deps.moduleTitle(m.id)])].map(([id, code, label]) => `<a class="ev-fc" id="ev-mod-${esc(id)}" href="${esc(href(route.tab, code, context))}"${(code || null) === (route.module || null) ? ' aria-current="true"' : ''}>${esc(label)}</a>`).join('');
    const off = route.tab === 'summary';
    return `<section class="ev-card ev-fbar" aria-label="Filter evidence"><label class="ev-search"><span class="sr-only">Search this tab</span>${icon('search')}<input type="search" id="ev-q" placeholder="${off ? 'Choose a tab to search it' : 'Search this tab'}" autocomplete="off"${off ? ' disabled' : ''}></label><p class="ev-match" role="status"></p><nav class="ev-fchips" aria-label="Module">${chips}</nav></section>`;
  }
  function tabs(input, route, counts) {
    const {context} = input.run;
    return `<nav class="ev-tabs" aria-label="Evidence kinds">${TABS.map(([id, label]) => `<a class="ev-tab" id="ev-tab-${id}" href="${esc(href(id, route.module, context))}"${id === route.tab ? ' aria-current="page"' : ''}><span>${esc(label)}</span>${counts[id] === undefined ? '' : `<span class="ev-cnt" data-count>${counts[id]}</span>`}</a>`).join('')}</nav>`;
  }
  function guide(input, route, counts) {
    return `<div class="ev-guide">${TABS.slice(1).map(([id, label, name, blurb]) => `<a class="ev-card ev-guide-card" href="${esc(href(id, route.module, input.run.context))}"><span class="ev-gi">${icon(name)}</span><span class="ev-gt">${esc(label)}<span class="ev-cnt" data-count>${counts[id]}</span></span><span class="ev-gb-text">${esc(blurb)}</span></a>`).join('')}</div>`;
  }
  const downloadLink = (label, url, named = label) => (url ? `<a class="ev-dl" href="${esc(url)}" download aria-label="Download ${esc(named)}">${icon('download')}<span>${esc(label)}</span></a>` : `<span class="ev-dl off"><span>${esc(label)}</span><span class="ev-muted">No link</span></span>`);
  function foot(input) {
    const {evidence: ev} = input.run, {deps} = input;
    const handoffs = ev.handoffs.map(h => downloadLink(deps.moduleTitle(h.module), h.href, `${deps.moduleTitle(h.module)} handoff`));
    if (ev.zip) handoffs.push(downloadLink('Download all', ev.zip, 'all handoffs (zip)'));
    const files = ev.downloads.map(d => downloadLink(d.label, d.href));
    return `<section class="ev-card ev-foot" aria-labelledby="ev-oh"><h3 id="ev-oh" class="ev-sub-h">Original handoffs</h3>${handoffs.length ? `<div class="ev-dl-g">${handoffs.join('')}</div>` : '<p class="ev-intro">This run holds no handoff.</p>'}<h3 class="ev-sub-h ev-gap-top">Calculations and Model</h3>${files.length ? `<div class="ev-dl-g">${files.join('')}</div>` : '<p class="ev-intro">No calculation or Model file was published from this run.</p>'}</section>`;
  }

  // The whole page for one route: the summary and the filter bar above the tabs on every tab, then the tab's panel and the foot.
  function view(input, route) {
    const ev = input.run.evidence;
    if (!ev) return '<div class="missing-state"><h2>No evidence record was read for this run</h2><p>Rebuild the library and open this page again.</p></div>';
    const tab = TAB_IDS.includes(route.tab) ? route.tab : 'summary', module = route.module || null, here = {tab, module};
    const everyone = contents(input), all = selected(everyone, module);
    const counts = tabCounts(all, input, module);
    const panels = {
      summary: () => guide(input, here, counts),
      trace: () => tracePanel(all, input),
      sources: () => sourcesPanel(input, module),
      calculations: () => calculationsPanel(all),
      gaps: () => gapsPanel(all),
      registers: () => registersPanel(input, module, all),
      record: () => recordPanel(input, module),
    };
    current = {rows: all.flatMap(c => c.trace), chips: input.chips, limit: PAGE};
    const label = TABS.find(t => t[0] === tab)[1];
    return `<div class="ev"><h2 class="ev-title">Audit, tracing and governance</h2>${governance(everyone, input)}${filterBar(input, here)}${tabs(input, here, counts)}<div class="ev-panel" id="ev-panel" role="region" aria-label="${esc(label)}">${panels[tab]()}<div class="ev-empty ev-nomatch" hidden>${icon('search')}<strong>Nothing matches</strong><p>No row of this tab matches the search.</p></div></div>${foot(input)}</div>`;
  }

  // ---- the page: the rows of the open view, search in place, clicks ----
  let current = {rows: [], chips: {}, limit: PAGE};
  const squash = text => String(text).toLowerCase().replace(/\s+/g, ' ').trim();
  // One level of matching. An item is the smallest listed unit and matches when its own text contains the query. A table is shown when one of its
  // rows matches (only those rows) or when its head (caption, module name, headers) matches (every row, counted once). A match never spans two rows.
  // `desc` = {tables: [{head, rows: [text]}], items: [text]}. Items beyond `limit` are held back (trace rows) and counted in `remaining`.
  function searchPlan(desc, query, limit = Infinity) {
    const q = squash(query), hit = text => !q || squash(text).includes(q); // an empty query matches every item: no filtering, paging still applies
    let found = 0;
    const items = desc.items.map(text => { if (!hit(text)) return false; found += 1; return found <= limit; });
    const remaining = Math.max(0, found - limit);
    let matches = Math.min(found, limit);
    const tables = desc.tables.map(table => {
      if (hit(table.head)) { matches += 1; return {show: true, rows: table.rows.map(() => true)}; }
      const rows = table.rows.map(hit);
      const n = rows.filter(Boolean).length;
      matches += n;
      return {show: n > 0, rows};
    });
    return {empty: !q, matches: q ? matches : 0, remaining, items, tables};
  }
  function applyFilter(root) {
    const panel = root.querySelector('.ev-panel'), input = root.querySelector('#ev-q'), query = input ? input.value : '';
    if (!panel) return;
    const tables = [...panel.querySelectorAll('.ev-tbl')].map(el => ({el, rows: [...el.querySelectorAll('tbody tr')]}));
    const items = [...panel.querySelectorAll('[data-hay],[data-find]')].filter(el => !el.closest('.ev-tbl'));
    const text = el => el.dataset.hay ?? el.dataset.find;
    const trace = panel.querySelector('.ev-trow') !== null;
    const plan = searchPlan({tables: tables.map(t => ({head: t.el.dataset.head, rows: t.rows.map(text)})), items: items.map(text)}, query, trace ? current.limit : Infinity);
    items.forEach((el, at) => { el.hidden = !plan.items[at]; });
    tables.forEach((t, at) => { t.el.hidden = !plan.tables[at].show; t.rows.forEach((tr, k) => { tr.hidden = !plan.tables[at].rows[k]; }); });
    const visible = ':is(.ev-tbl,[data-hay],[data-find]):not([hidden])';
    panel.querySelectorAll('[data-group]:not(.ev-tbl)').forEach(group => { group.hidden = group.querySelector(':is(.ev-tbl,[data-hay],[data-find])') !== null && group.querySelector(visible) === null; });
    const more = panel.querySelector('[data-more]');
    if (more) { more.hidden = plan.remaining === 0; more.textContent = `Show more (${plan.remaining} remaining)`; }
    const none = panel.querySelector('.ev-nomatch');
    if (none) none.hidden = plan.empty || plan.matches > 0 || (items.length === 0 && tables.length === 0);
    // The tab badge is the count tabCounts drew and is never rewritten; the matches of a query are their own text beside the search box.
    const label = root.querySelector('.ev-match');
    if (label) label.textContent = plan.empty ? '' : `${plan.matches} matching`;
  }
  function copyHash(button) {
    const text = button.dataset.copy;
    const pending = typeof navigator !== 'undefined' && navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject(new Error('The clipboard is not available'));
    // Documented fail-open: a refused or missing clipboard is shown to the reader as a toast; nothing else depends on the copy.
    pending.then(() => {
      button.innerHTML = icon('check');
      setTimeout(() => { button.innerHTML = icon('copy'); }, 1500);
      components().toast('Hash copied');
    }, error => { console.error('Evidence: copy failed', error); components().toast('Copy failed'); });
  }
  function toggleTrace(button) {
    const row = button.parentElement, open = row.dataset.open !== 'true';
    row.dataset.open = String(open);
    button.setAttribute('aria-expanded', String(open));
    const old = row.querySelector('.ev-trow-b');
    if (old) old.remove();
    if (open) row.insertAdjacentHTML('beforeend', traceBody(current.rows[Number(row.dataset.k)], current.chips));
  }
  // Returns true when the click was the Evidence page's own.
  function handleClick(target) {
    const copy = target.closest('[data-copy]'), more = target.closest('[data-more]'), trace = target.closest('.ev-trow > button');
    if (!copy && !more && !trace) return false;
    const root = target.closest('.ev');
    if (copy) copyHash(copy);
    else if (more) { current.limit += PAGE; applyFilter(root); }
    else toggleTrace(trace);
    return true;
  }
  function handleSearch(input) {
    current.limit = PAGE;
    applyFilter(input.closest('.ev'));
  }

  const api = {TABS, parseHash, href, tableView, classify, gapTotal, ledgerTotal, traceRows, traceBody, view, searchPlan, handleClick, handleSearch};
  if (typeof window !== 'undefined') window.Evidence = api;
  if (typeof module !== 'undefined') module.exports = api;
})();

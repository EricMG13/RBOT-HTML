'use strict';
// Pure classifiers for the library redesign: a handoff section's role, a table's shape, a column's kind, a paragraph's role.
// No DOM, no store, no globals read. Strings in, strings out; nothing here changes a word of the handoff.
// tableShape reads only a table's headers and cell patterns, never the heading of the section that holds it.
// Browser: one global, Shapes. Node: module.exports.
const Shapes = (() => {
  // ---- section roles: named by the heading chain from the level-2 ancestor down to the section ----
  const PASSAGES = ['Bottom line', 'Key findings', 'Contrary evidence and what would change the view', 'Limitations'];
  // A section (or any ancestor) written for another module or the orchestrator: drawn nowhere (rule 7).
  const HIDDEN_HEADING = /^(Request|Next module|Front matter)$|downstream owners|Consumer readiness|command sheet|Readiness for downstream use|Upstream re-anchor|method trace|Module status|QA validation|machine-readable|research brief|Workstream plan|Cross-Module Handoff/i;
  const TOP_ROLE = {Sources: 'sources', Calculations: 'calculations', Gaps: 'gaps'};
  const DRAWING_HEADING = /^(Chart data|Map|Events): /;
  const REGISTER_HEADING = /source assessment|source context|period table|key located evidence|conflicts and duplicates|register|ledger/i;
  // A method code leads a heading: "T2B.3 Name", "T2B.3 — Name", "t2b.calc_x — Name".
  const METHOD_CODE = /^(?:[A-Z][A-Z0-9]*\.[A-Z]?\d+(?:\s+—\s+|\s+(?=[A-Z]))|[a-z0-9]+(?:\.[a-z0-9_]+)+\s+—\s+)/;

  // `placement` is store.py's own label for the section; the role is decided by the chain alone, so the parameter is not read.
  function sectionRole(chain, placement) {
    const own = chain[chain.length - 1] ?? '';
    if (chain.some(h => HIDDEN_HEADING.test(h))) return 'hidden';
    if (TOP_ROLE[chain[0]]) return TOP_ROLE[chain[0]];
    if (chain[0] !== 'Findings') return 'registers';                          // an unknown level-2 heading stays visible, in Evidence
    if (chain.length === 2 && PASSAGES.includes(own)) return 'passage';
    if (DRAWING_HEADING.test(own)) return 'drawing';
    if (chain.some(h => /^Analytical appendix/.test(h)) || REGISTER_HEADING.test(own.replace(METHOD_CODE, ''))) return 'registers';
    return 'finding';
  }

  // ---- columns ----
  const norm = header => String(header ?? '').trim().toLowerCase().replace(/_/g, ' ').replace(/\s+/g, ' ');
  const KIND_RULES = [
    ['id', /^id$|\bid$|^linked pathway row$/],                                  // before source: "Evidence ID" is an id
    ['source', /^(?:(?:sources?|evidence)(?:\s*\/\s*clause|\s+(?:trace|locator|register|document|file|sha|hash|page|reference|ref|link)s?)?|sha256)$/],
    ['intermodule', /^(supplied handoff|use in this module|effect on this module|consumer|downstream module|receiving module|responsible module|command|required consumer action|escalation consequence)$|^consequence for cp-/],
    ['limitation', /limitation/],
    ['consequence', /creditor consequence|effect on the credit view/],
    ['period', /^(?:(?:fy|cy|ltm|pf|[hq][1-4])\s*)?\d{4}[ae]?\b|^(?:fy|cy)\s*\d{2}[ae]?\b/],
    ['case', /\b(scenario|case|downside|upside|base|severe|moderate|stress)\b/],
    ['label', /^(line|metric|item|driver|exposure|from|to|question|gate item|decision driver|security group|rank|break)\b|\bmeasure$/],
  ];
  // The two machine names keep their underscore: "downstream_use" addresses another module, "Downstream Use" (a source register's column) does not.
  const MACHINE_INTERMODULE = /^(?:downstream_use|consumer_module_id)$/i;
  const columnKind = header => (MACHINE_INTERMODULE.test(String(header ?? '').trim()) ? 'intermodule' : (KIND_RULES.find(([, rx]) => rx.test(norm(header))) || ['text'])[0]);
  const HIDDEN_KINDS = new Set(['source', 'id', 'intermodule']);
  // A plain "Module" header says which module a row concerns, so it is not inter-module; `shape` is kept for the interface.
  const hiddenColumns = (headers, shape) => headers
    .map((h, c) => (HIDDEN_KINDS.has(columnKind(h)) ? c : -1))
    .filter(c => c >= 0);

  // ---- table shapes: the first rule that matches wins; the order is the precedence ----
  // Each rule sees the normalised headers `h`. Narrow, named column sets come before the broad period and case rules.
  const has = (h, rx) => h.some(x => rx.test(x));
  const periods = h => h.filter(x => columnKind(x) === 'period').length;
  const SHAPE_RULES = [
    ['matrix', h => has(h, /^probability$/) && has(h, /^impact$/)],            // two graded columns
    ['watch', h => has(h, /leading/)],                                          // "Leading / Lagging"
    ['dated', h => /date|window/.test(h[0]) && has(h, /^event/)],               // date first, an event column
    ['edges', h => h[0] === 'from' && h.includes('to') && has(h, /^relationship/)],
    ['ranked', h => h[0] === 'rank'],
    ['caseRows', h => /^scenario( id)?$/.test(h[0])],                           // rows are the cases
    ['moduleState', h => h[0] === 'module' && has(h, /^status$/)],
    ['qa', h => h[0] === 'question'],
    ['sided', h => has(h, /^side\b/)],
    ['change', h => h.includes('earlier') && h.includes('current')],
    ['facts', h => h.includes('fact') && h.includes('category')],
    ['cases', h => h.filter(x => columnKind(x) === 'case').length >= 2],        // named cases as columns; before status and measure
    ['status', h => has(h, /status$/)],
    ['metric', h => has(h, /definition|identity/) && periods(h) >= 1],
    ['measure', h => /measure$/.test(h[0]) && has(h, /creditor consequence/)],
    ['statement', h => periods(h) >= 2],                                        // lines by two or more periods; after metric and measure, which also carry periods
  ];
  // Where two rules could match: matrix > watch > dated > edges > ranked > caseRows > moduleState > qa > sided > change > facts > cases > status > metric > measure > statement.
  function tableShape(block) {
    const h = (block?.headers ?? []).map(norm);
    if (!h.length || !(block.rows ?? []).length) return 'records';
    return (SHAPE_RULES.find(([, rule]) => rule(h)) || ['records'])[0];
  }

  // ---- paragraphs ----
  const NOTE = /^(?:Module status|Two method texts)\b|^Confidence is \d|qa_status|committee_status/i;
  const SKILL = /\bSKILL\b/;  // the method file's name, upper case only
  const blockRole = text => { const t = String(text ?? '').trim(); return NOTE.test(t) || SKILL.test(t) ? 'note' : 'prose'; };

  const promoted = shape => ['matrix', 'watch', 'dated'].includes(shape);

  // ---- identifiers of a module (Task 5) ----
  const tablesIn = sections => (sections ?? []).flatMap(section => (section.blocks ?? []).filter(block => block.type === 'table'));
  // The distinct cell values of every column of kind `id` in the sections' tables, in first-seen order, that a reader could meet inside a sentence as an
  // identifier: a value holds a digit (so Base and High are words, not tokens) and is not a period label (FY24, FY2024A, 2024, Q3 2024, H1 24) or a bare number.
  // A period label: a year (2024, FY2024-25, FY24E), optionally led by a trailing/half/quarter/nine-month tag (LTM, 1H24, H1 2024, 9M24, Q3 FY24); LTM alone too.
  const PERIOD_LABEL = /^(?:(?:ltm|ttm|ytd|pf)\s*)?(?:(?:[hq][1-4]|[1-4][hq]|\d{1,2}m)\s*)?(?:(?:fy|cy)?\s*\d{2,4}(?:\s*[-/\u2013]\s*\d{2,4})?[ae]?)?$/;
  const isToken = value => /\d/.test(value) && !/^\d+$/.test(value) && !PERIOD_LABEL.test(norm(value));
  function idTokens(sections) {
    const found = new Set();
    for (const block of tablesIn(sections)) {
      block.headers.forEach((header, at) => {
        if (columnKind(header) !== 'id') return;
        for (const row of block.rows) {
          const value = String(row.cells[at] ?? '').trim();
          if (isToken(value)) found.add(value);
        }
      });
    }
    return [...found];
  }

  // The case a table's row stands for. A module with exactly one `cases` table (named cases as columns) and a `caseRows` table with one row per case
  // column and an id column: the i-th row and the i-th case column are the same case, and the case column's header is its name. `ids` are the rows' id
  // cells. `table` is the paired table itself (the one object the names apply to) and `index` its place in `tables`. A `caseRows` table without an id
  // column is never paired, and any other is not named. No match is null: no pairing, no invented names.
  function casePairing(tables) {
    const typed = (tables ?? []).map((block, index) => ({block, index})).filter(({block}) => block && Array.isArray(block.headers) && Array.isArray(block.rows)).map(entry => ({...entry, shape: tableShape(entry.block)}));
    const cases = typed.filter(entry => entry.shape === 'cases');
    if (cases.length !== 1) return null;
    const names = cases[0].block.headers.filter(header => columnKind(header) === 'case').map(header => String(header).trim());
    // The source: exactly one caseRows table with one row per case column whose FIRST column is an id column, and whose ids are all different and non-empty.
    const sources = typed.filter(entry => entry.shape === 'caseRows' && entry.block.rows.length === names.length && columnKind(entry.block.headers[0]) === 'id');
    if (!names.length || sources.length !== 1) return null;
    const ids = sources[0].block.rows.map(row => String(row.cells[0] ?? '').trim());
    if (ids.some(id => id === '') || new Set(ids).size !== ids.length) return null;
    return {names, ids, table: sources[0].block, index: sources[0].index, idColumn: 0};
  }

  // A prose paragraph of a finding section that holds an identifier of the module (an `id` column's value), or that names a calculation, is a method note: the
  // Evidence page's, not the findings page's. `body` is the paragraph without its Basis line. 'calculations' when it names a calculation ID, 'registers' when it
  // holds another identifier, null when it is findings prose. Whole words only, as findingCell reads a cell.
  // The one pattern for a calculation named in text (findingCell reads cells with it too): capital C, a single space, the plural allowed.
  const CALCULATION_ID = /\b[Cc]alculations? (?!(?:FY|CY|PF)\d)[A-Z]{1,2}\d{2}\b/;  // not a period label (calculation FY24 note)
  const tokenPatterns = new WeakMap();
  function methodNote(body, tokens) {
    const text = String(body ?? '');
    if (CALCULATION_ID.test(text)) return 'calculations';
    if (!Array.isArray(tokens) || !tokens.length) return null;
    if (!tokenPatterns.has(tokens)) tokenPatterns.set(tokens, new RegExp(`(?<![A-Za-z0-9_])(?:${[...tokens].sort((a, b) => b.length - a.length).map(token => token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})(?![A-Za-z0-9_])`));
    return tokenPatterns.get(tokens).test(text) ? 'registers' : null;
  }

  return {sectionRole, tableShape, columnKind, hiddenColumns, blockRole, promoted, idTokens, casePairing, methodNote, CALCULATION_ID};
})();

if (typeof window !== 'undefined') window.Shapes = Shapes;
if (typeof module !== 'undefined') module.exports = Shapes;

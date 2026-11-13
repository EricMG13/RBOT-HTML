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

  return {sectionRole, tableShape, columnKind, hiddenColumns, blockRole, promoted};
})();

if (typeof window !== 'undefined') window.Shapes = Shapes;
if (typeof module !== 'undefined') module.exports = Shapes;

(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('library-data').textContent);
  const $ = id => document.getElementById(id);
  const {filterRuns, sortRuns, displayDate, spendText, modelLabel} = LibraryLogic;
  const fields = ['search', 'pathway', 'model', 'latest'];
  const runs = data.runs;
  let issuer = '', selected = runs[0]?.id, sortKey = '', direction = 'asc';
  // Every value from a run is set as text, never parsed as HTML.
  const node = (tag, value, className) => {
    const element = document.createElement(tag);
    if (value != null) element.textContent = value;
    if (className) element.className = className;
    return element;
  };
  const link = (value, href, className) => {
    const element = node('a', value, className);
    element.href = href; element.target = '_blank'; element.rel = 'noopener';
    return element;
  };
  const button = (value, action, className) => {
    const element = node('button', value, className); element.type = 'button';
    element.addEventListener('click', action); return element;
  };
  const fact = (label, value) => {
    const item = node('div', null, 'fact');
    item.append(node('dt', label), node('dd', value));
    return item;
  };
  const filters = () => Object.fromEntries([...fields.map(id => [id, $(id).value]), ['issuer', issuer]]);
  function populateSelect(id, values, placeholder) {
    const options = [...new Set(values.filter(Boolean))].sort();
    $(id).replaceChildren(new Option(placeholder, ''), ...options.map(value => new Option(value, value)));
  }
  function initialise() {
    populateSelect('pathway', runs.map(r => r.pathway), 'All pathways');
    populateSelect('model', runs.flatMap(r => r.execution.models), 'All models');
    $('all-count').textContent = runs.length;
    $('latest-count').textContent = runs.filter(r => r.latest).length;
    const issuers = [...new Set(runs.map(r => r.issuer_id))];
    $('issuer-count').textContent = issuers.length;
    $('issuer-nav').replaceChildren(...issuers.map(id => {
      const matching = runs.filter(r => r.issuer_id === id);
      const choice = button('', () => {issuer = issuer === id ? '' : id; render();}, 'issuer-choice');
      choice.dataset.issuer = id;
      choice.setAttribute('aria-label', 'Filter ' + matching[0].issuer_name);
      choice.append(node('span', id.slice(0, 4).toUpperCase(), 'issuer-monogram'), node('span', matching[0].issuer_name), node('span', matching.length));
      return choice;
    }));
    const hidden = data.not_shown.length;
    $('library-note').replaceChildren(node('strong', `${runs.length} ${runs.length === 1 ? 'run' : 'runs'} on the current methodology. `),
      document.createTextNode(hidden ? `${hidden} other run ${hidden === 1 ? 'folder is' : 'folders are'} in this workspace and not shown; the list at the end says why. ` : ''),
      document.createTextNode('Hashes were checked when this page was built; update the library after new runs.'));
    $('not-shown').hidden = !hidden;
    $('not-shown-summary').textContent = `Not shown · ${hidden} run ${hidden === 1 ? 'folder' : 'folders'}`;
    $('not-shown-rows').replaceChildren(...data.not_shown.map(item => {
      const row = node('tr'); row.append(node('td', item.folder, 'num'), node('td', item.reason)); return row;
    }));
    $('build-date').textContent = `Built ${data.built_at}`;
    $('footer-note').textContent = `Workspace ${data.workspace}`;
  }
  function reset() {
    fields.forEach(id => {$(id).value = '';}); issuer = ''; sortKey = ''; direction = 'asc';
    selected = runs[0]?.id; render();
  }
  function selectRun(id) {
    selected = id; render();
    $('run-detail').focus({preventScroll: true});
    $('run-detail').scrollIntoView({block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  }
  function runRow(run) {
    const row = node('tr'); row.classList.toggle('selected', selected === run.id);
    const identity = node('td');
    const name = button(run.issuer_name, () => selectRun(run.id), 'issuer-title');
    name.setAttribute('aria-label', `View ${run.issuer_name}, run ${run.run_id}`);
    name.setAttribute('aria-expanded', String(selected === run.id)); name.setAttribute('aria-controls', 'run-detail');
    name.append(node('span', run.issuer_id.toUpperCase(), 'ticker'));
    identity.append(name, node('span', run.run_id, 'run-title'));
    if (run.latest) identity.append(node('span', run.latest_shared_with ? `Latest evidence date · shared with ${run.latest_shared_with}` : 'Latest evidence date', 'badge latest-badge'));
    const date = node('td'); date.append(node('span', displayDate(run.as_of) || 'Not recorded', 'cell-primary date-primary'), node('span', run.case_kind || '', 'cell-secondary'));
    const pathway = node('td'); pathway.append(node('span', run.pathway, 'date-primary'), node('span', run.modules.map(m => m.id).join(' · '), 'cell-secondary'));
    const model = node('td'); model.append(node('span', modelLabel(run), 'date-primary'), node('span', run.execution.config || '', 'cell-secondary'));
    const started = node('td', displayDate(run.execution.started_at) || 'Not recorded', 'date-primary');
    const spend = node('td'); spend.append(node('span', spendText(run.execution), 'cell-primary'), node('span', run.cap_usd == null ? '' : `Cap USD ${run.cap_usd}`, 'cell-secondary'));
    const report = node('td'); const anchor = link('Open report ↗', run.report.href, 'report-link');
    anchor.setAttribute('aria-label', `Open report: ${run.issuer_name}, ${run.run_id}`);
    report.append(anchor);
    row.append(identity, date, pathway, model, started, spend, report);
    return row;
  }
  function summaryBlock(summary) {
    const box = node('div', null, 'reader-summary');
    if (!summary) {box.append(node('p', 'This handoff has no reader summary in the expected form. Open the handoff to read it.', 'muted')); return box;}
    box.append(node('p', summary.bottom_line, 'bottom-line'));
    const facts = node('dl', null, 'facts');
    facts.append(fact('Confidence', summary.confidence), fact('Main limitation', summary.limitation));
    box.append(facts);
    if (summary.findings.length) {
      const table = node('table', null, 'findings'); const head = node('tr');
      ['Finding', 'Creditor impact', 'Confidence'].forEach(label => {const th = node('th', label); th.scope = 'col'; head.append(th);});
      const body = node('tbody');
      summary.findings.forEach(item => {const row = node('tr'); row.append(node('td', item.finding), node('td', item.impact), node('td', item.confidence)); body.append(row);});
      const thead = node('thead'); thead.append(head); table.append(thead, body); box.append(table);
    }
    return box;
  }
  function moduleItem(entry) {
    const item = node('li', null, 'module-entry');
    const head = node('div', null, 'module-head');
    const title = node('h4', `${entry.title} (${entry.id})`);
    head.append(title, node('span', entry.execution, 'badge'), link('Open handoff ↗', entry.href, 'source-link'));
    item.append(head, summaryBlock(entry.summary), node('p', `sha256 ${entry.sha256}`, 'hash'));
    return item;
  }
  function renderDetails(run) {
    const root = $('run-detail'); root.hidden = !run; root.replaceChildren();
    if (!run) return;
    const head = node('div', null, 'detail-head'), title = node('div');
    title.append(node('p', 'SELECTED RUN', 'eyebrow'), node('h2', run.issuer_name), node('p', `${run.id} / ${run.run_id}`, 'detail-id'));
    head.append(title, link('Open report ↗', run.report.href, 'primary-button'));
    const layout = node('div', null, 'detail-layout'), left = node('div'), right = node('div');
    left.append(node('h3', 'Scope', 'detail-section-title'), node('p', run.scope, 'detail-description'));
    const facts = node('dl', null, 'facts');
    const execution = run.execution;
    facts.append(fact('Evidence date', displayDate(run.as_of) || 'Not recorded'), fact('Pathway', run.pathway),
      fact('Case', run.case_kind || 'Not recorded'), fact('Requested modules', run.requested_modules.join(', ') || 'Not recorded'),
      fact('Methodology', `Current for every module · ${run.method_version}`), fact('Model', `${modelLabel(run)}${execution.config ? ` (${execution.config})` : ''}`),
      fact('Model calls', String(execution.calls)), fact('Spend', spendText(execution)), fact('Spending cap', run.cap_usd == null ? 'Not recorded' : `USD ${run.cap_usd}`),
      fact('Run on', displayDate(execution.started_at) || 'Not recorded'), fact('Report sha256', run.report.sha256));
    left.append(node('h3', 'Run', 'detail-section-title'), facts);
    right.append(node('h3', 'Module outputs', 'detail-section-title'));
    const list = node('ol', null, 'module-list'); run.modules.forEach(entry => list.append(moduleItem(entry)));
    right.append(list); layout.append(left, right); root.append(head, layout);
  }
  function emptyState() {
    const empty = $('empty-state');
    if (!runs.length) {
      empty.replaceChildren(node('h2', 'No completed runs on the current methodology yet'),
        node('p', 'Start a run with Run workflow, then choose Update library. A run is listed once CP-OS has delivered its report and every module ran on the current methodology.'));
    } else {
      empty.replaceChildren(node('h2', 'No runs match these filters'), button('Reset filters', reset, 'primary-button'));
    }
  }
  function render() {
    const f = filters(), matching = filterRuns(runs, f);
    const rows = sortKey ? sortRuns(matching, sortKey, direction) : matching;
    if (!rows.some(r => r.id === selected)) selected = rows[0]?.id;
    $('run-rows').replaceChildren(...rows.map(runRow));
    $('results-count').textContent = `${rows.length} of ${runs.length} runs · ${new Set(rows.map(r => r.issuer_id)).size} issuers`;
    $('empty-state').hidden = rows.length > 0; emptyState();
    document.querySelectorAll('[data-sort]').forEach(th => th.setAttribute('aria-sort', th.dataset.sort === sortKey ? direction === 'asc' ? 'ascending' : 'descending' : 'none'));
    document.querySelectorAll('[data-issuer]').forEach(el => {const active = el.dataset.issuer === issuer; el.classList.toggle('active', active); el.setAttribute('aria-pressed', String(active));});
    const latest = f.latest === 'latest';
    $('all-runs').classList.toggle('active', !issuer && !latest); $('all-runs').setAttribute('aria-pressed', String(!issuer && !latest));
    $('latest-only').classList.toggle('active', latest); $('latest-only').setAttribute('aria-pressed', String(latest));
    renderDetails(rows.find(r => r.id === selected));
  }
  fields.forEach(id => $(id).addEventListener($(id).tagName === 'SELECT' ? 'change' : 'input', render));
  document.querySelectorAll('[data-sort]').forEach(th => th.querySelector('button').addEventListener('click', () => {
    direction = sortKey === th.dataset.sort && direction === 'asc' ? 'desc' : 'asc'; sortKey = th.dataset.sort; render();
  }));
  $('clear').addEventListener('click', reset);
  $('all-runs').addEventListener('click', reset);
  $('latest-only').addEventListener('click', () => {issuer = ''; $('latest').value = 'latest'; render();});
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !event.metaKey && !event.ctrlKey && !event.altKey && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
      event.preventDefault(); $('search').focus();
    }
  });
  initialise(); render();
})();

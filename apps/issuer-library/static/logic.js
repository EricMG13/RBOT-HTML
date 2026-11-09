/* Pure library operations: filtering, sorting and display text. No analysis or arithmetic on
   analytical values; a spend is compared as the exact decimal the run recorded. */
const LibraryLogic = (() => {
  const text = value => (value == null ? '' : String(value));
  const modelLabel = run => run.execution.models.join(', ') || 'Not recorded';
  // Exact decimal strings compare by their digits: no binary rounding of recorded amounts.
  function compareDecimal(a, b) {
    const parse = value => {
      const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(text(value));
      if (!match) return null;
      return {negative: match[1] === '-', whole: match[2].replace(/^0+(?=\d)/, ''), fraction: (match[3] || '').replace(/0+$/, '')};
    };
    const x = parse(a), y = parse(b);
    if (!x || !y) return 0;
    if (x.negative !== y.negative) return x.negative ? -1 : 1;
    const sign = x.negative ? -1 : 1;
    if (x.whole.length !== y.whole.length) return sign * (x.whole.length - y.whole.length);
    if (x.whole !== y.whole) return sign * (x.whole < y.whole ? -1 : 1);
    const width = Math.max(x.fraction.length, y.fraction.length);
    const fx = x.fraction.padEnd(width, '0'), fy = y.fraction.padEnd(width, '0');
    return fx === fy ? 0 : sign * (fx < fy ? -1 : 1);
  }
  function matches(run, filters) {
    const search = text(filters.search).trim().toLocaleLowerCase();
    const haystack = [run.issuer_name, run.issuer_id, run.id, run.run_id, run.pathway,
      ...run.modules.map(m => `${m.id} ${m.title}`), modelLabel(run)].join(' ').toLocaleLowerCase();
    if (search && !haystack.includes(search)) return false;
    if (filters.issuer && run.issuer_id !== filters.issuer) return false;
    if (filters.pathway && run.pathway !== filters.pathway) return false;
    if (filters.model && !run.execution.models.includes(filters.model)) return false;
    return !(filters.latest === 'latest' && !run.latest);
  }
  const filterRuns = (runs, filters) => runs.filter(run => matches(run, filters));
  const sortValue = (run, key) => key === 'spend' ? run.execution.spend_usd : key === 'started_at' ? run.execution.started_at : run[key];
  function sortRuns(runs, key, direction) {
    return [...runs].sort((left, right) => {
      const a = sortValue(left, key), b = sortValue(right, key);
      if (a == null && b == null) return left.id.localeCompare(right.id);
      if (a == null) return 1; // Missing values stay last in either direction.
      if (b == null) return -1;
      const difference = key === 'spend' ? compareDecimal(a, b) : text(a).localeCompare(text(b));
      return (direction === 'desc' ? -difference : difference) || left.id.localeCompare(right.id);
    });
  }
  function displayDate(value) {
    const day = /^(\d{4})-(\d{2})-(\d{2})/.exec(text(value));
    if (!day) return '';
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const month = months[Number(day[2]) - 1];
    return month ? `${Number(day[3])} ${month} ${day[1]}` : '';
  }
  function spendText(execution) {
    if (execution.spend_usd == null) return 'Not recorded';
    const unknown = execution.unknown_charges;
    return `USD ${execution.spend_usd}${unknown ? ` + ${unknown} unknown ${unknown === 1 ? 'charge' : 'charges'}` : ''}`;
  }
  return {compareDecimal, filterRuns, sortRuns, displayDate, spendText, modelLabel};
})();
if (typeof module !== 'undefined') module.exports = LibraryLogic;

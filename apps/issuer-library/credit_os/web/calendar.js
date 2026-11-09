'use strict';
// Pure calendar logic: no DOM, no store. Browser: the functions below are globals. Node: module.exports.
// An event table is the first table in a CP-1A output whose first header starts with "Date".
function eventTable(sections) {
  for (const section of sections || []) {
    for (const block of section.blocks || []) {
      if (block.type === 'table' && /^date/i.test(block.headers[0] || '')) return {headers: block.headers, rows: block.rows};
    }
  }
  return null;
}

const EVENT_MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];
// Capitalised English month names, full before short so "March" is not read as "Mar"; "may" the verb is not a month.
const EVENT_MONTH = /\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\b/;
const EVENT_YEAR = /(?<!\d)\d{4}(?!\d)/;

// [year, month] for the first 4-digit year in the cell and the first month name anywhere in it (0 when none);
// null when the cell has no year.
function eventOrder(cell) {
  const text = String(cell);
  const year = EVENT_YEAR.exec(text);
  if (!year) return null;
  const month = EVENT_MONTH.exec(text);
  return [Number(year[0]), month ? EVENT_MONTHS.indexOf(month[1].slice(0, 3).toLowerCase()) + 1 : 0];
}

// Stable sort by eventOrder of the first cell; rows without an order go last. Rows are returned as given.
function orderEvents(rows) {
  const keyed = rows.map((row, index) => ({row, index, key: eventOrder(row.cells[0])}));
  keyed.sort((a, b) => {
    if (a.key === null || b.key === null) return (a.key === null) - (b.key === null) || a.index - b.index;
    return a.key[0] - b.key[0] || a.key[1] - b.key[1] || a.index - b.index;
  });
  return keyed.map(item => item.row);
}

if (typeof module !== 'undefined') module.exports = {eventTable, eventOrder, orderEvents};

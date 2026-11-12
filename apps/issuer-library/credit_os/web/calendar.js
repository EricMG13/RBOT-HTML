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

// ---- Lane placement. A lane event is placed from its stated date at its stated precision: a day is a point, a month, quarter or year
// spans its whole length. A date that does not match its precision has no place (it stays in the event table); no day is ever chosen for it.
const DAY_MS = 86400000;
const utcDay = (year, month, day) => Date.UTC(year, month - 1, day) / DAY_MS;
function eventSpan(date, precision) {
  const forms = {day: /^(\d{4})-(\d{2})-(\d{2})$/, month: /^(\d{4})-(\d{2})$/, quarter: /^(\d{4})-Q([1-4])$/, year: /^(\d{4})$/};
  const found = Object.hasOwn(forms, precision) ? forms[precision].exec(String(date)) : null;
  if (!found) return null;
  const [year, part, dayOfMonth] = found.slice(1).map(Number);
  if (precision === 'year') return {from: utcDay(year, 1, 1), to: utcDay(year, 12, 31), point: false};
  if (precision === 'quarter') return {from: utcDay(year, 3 * part - 2, 1), to: utcDay(year, 3 * part + 1, 0), point: false};
  if (part < 1 || part > 12) return null;
  if (precision === 'month') return {from: utcDay(year, part, 1), to: utcDay(year, part + 1, 0), point: false};
  const day = new Date(Date.UTC(year, part - 1, dayOfMonth));
  if (day.getUTCMonth() !== part - 1 || day.getUTCDate() !== dayOfMonth) return null;
  return {from: utcDay(year, part, dayOfMonth), to: utcDay(year, part, dayOfMonth), point: true};
}

// The shared date axis: earliest start to latest end in UTC days (one day wide when everything is a single day), or null with no span.
function eventAxis(spans) {
  if (!spans.length) return null;
  const start = Math.min(...spans.map(s => s.from)), end = Math.max(...spans.map(s => s.to));
  return {start, end: end > start ? end : start + 1};
}

// Left edge and width of a span on the axis, in percent to two decimals; a point has no width.
function eventPlace(span, axis) {
  const percent = days => Math.round(days / (axis.end - axis.start) * 10000) / 100;
  return {left: percent(span.from - axis.start), width: percent(span.to - span.from)};
}

// Where a UTC day sits on the axis, in the same percent as eventPlace.
const eventLeft = (day, axis) => eventPlace({from: day, to: day}, axis).left;

// Axis ticks as {day, left, label}. An axis shorter than a year has a tick at each 1st of a month ("Jan 2025" carries its year; the first tick does too);
// a longer one a tick at each 1 January. Past 12 years only every Nth year (a round N) is labelled; past 40 years only a labelled year has a tick.
function eventTicks(axis) {
  if (!axis) return [];
  const first = new Date(axis.start * DAY_MS), last = new Date(axis.end * DAY_MS);
  const ticks = [];
  if (axis.end - axis.start < 365) {
    for (let at = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth(), 1)); at <= last; at = new Date(Date.UTC(at.getUTCFullYear(), at.getUTCMonth() + 1, 1))) {
      const day = at.getTime() / DAY_MS;
      if (day < axis.start) continue;
      const month = EVENT_MONTHS[at.getUTCMonth()], name = month[0].toUpperCase() + month.slice(1);
      ticks.push({day, left: eventLeft(day, axis), label: !ticks.length || at.getUTCMonth() === 0 ? `${name} ${at.getUTCFullYear()}` : name});
    }
    return ticks;
  }
  const years = [];
  for (let year = first.getUTCFullYear(); year <= last.getUTCFullYear(); year++) if (utcDay(year, 1, 1) >= axis.start && utcDay(year, 1, 1) <= axis.end) years.push(year);
  const every = [1, 2, 5, 10, 20, 25, 50, 100].find(n => Math.ceil(years.length / n) <= 12) ?? 100;
  for (const year of years) {
    const labelled = year % every === 0 || every === 1;
    if (labelled || years.length <= 40) ticks.push({day: utcDay(year, 1, 1), left: eventLeft(utcDay(year, 1, 1), axis), label: labelled ? String(year) : null});
  }
  return ticks;
}

// Percent on the axis of an ISO as-of date, or null when it is not a date or lies outside the axis (the ends count as inside).
function eventAsOf(axis, iso) {
  const found = axis && /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso));
  if (!found) return null;
  const span = eventSpan(iso, 'day');
  return span && span.from >= axis.start && span.from <= axis.end ? eventLeft(span.from, axis) : null;
}

// Rows for the drawn items ({span, left, width} as eventPlace gives them), parallel to the input. Nothing is moved sideways: an item whose marker would overlap one already
// drawn goes up a row instead. Spans are placed first (longest first), so a lone span keeps the baseline and a point over a span sits above it; points follow in date order.
// A marker is `markPx` wide at least; `trackPx` is the lane width the percentages are read against.
function eventStack(items, trackPx = 1032, markPx = 16) {
  const px = percent => percent * trackPx / 100;
  const room = item => item.span.point ? [px(item.left) - markPx / 2, px(item.left) + markPx / 2] : [px(item.left), px(item.left) + Math.max(px(item.width), markPx)];
  const order = items.map((item, index) => index).sort((a, b) => (items[a].span.point - items[b].span.point) || (items[a].span.from - items[b].span.from) || (items[b].span.to - items[a].span.to) || a - b);
  const rows = [], taken = [];
  for (const index of order) {
    const [from, to] = room(items[index]);
    let row = 0;
    while ((taken[row] || []).some(([start, end]) => from < end && start < to)) row++;
    (taken[row] ||= []).push([from, to]);
    rows[index] = row;
  }
  return rows;
}

if (typeof module !== 'undefined') module.exports = {eventTable, eventOrder, orderEvents, eventSpan, eventAxis, eventPlace, eventTicks, eventAsOf, eventStack};

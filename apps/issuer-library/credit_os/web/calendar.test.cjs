'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {eventTable, eventOrder, orderEvents, eventSpan, eventAxis, eventPlace, eventTicks, eventAsOf, eventStack} = require('./calendar.js');

// Block shape is store.py table_block: {type, line, headers, rows: [{line, cells}]}.
const table = (headers, rows) => ({type: 'table', line: 1, headers, rows: rows.map((cells, i) => ({line: i + 3, cells}))});
const section = (heading, ...blocks) => ({heading, line: 1, blocks});

test('eventOrder reads the first year and the first month name', () => {
  assert.deepEqual(eventOrder('May 21 and June 6, 2024'), [2024, 5]);
  assert.deepEqual(eventOrder('1993 inception; history through FY2024'), [1993, 0]);
  assert.deepEqual(eventOrder('October 2024'), [2024, 10]);
  assert.deepEqual(eventOrder('2024 — Sep. refinancing'), [2024, 9]);
  assert.deepEqual(eventOrder('2023 — spring; may continue'), [2023, 0]);
  assert.equal(eventOrder('Subsequent period'), null);
});

test('orderEvents is stable, keeps text and puts rows without a year last', () => {
  const rows = [
    {line: 3, cells: ['Subsequent period', 'x']},
    {line: 4, cells: ['October 2024', 'a']},
    {line: 5, cells: ['1993 — formation', 'b']},
    {line: 6, cells: ['May 8, 2023 — Calspan', 'c']},
    {line: 7, cells: ['October 2024', 'd']},
  ];
  const before = JSON.stringify(rows);
  const ordered = orderEvents(rows);
  assert.deepEqual(ordered.map(r => r.line), [5, 6, 4, 7, 3]);
  assert.equal(JSON.stringify(rows), before);
  assert.equal(ordered[1].cells[0], 'May 8, 2023 — Calspan');
});

test('eventTable finds the Date table under either real CP-1A heading', () => {
  for (const heading of ['Credit-relevant history and event status', 'Dated business history and acquisition register']) {
    const found = table(['Date / period', 'Category'], [['1993', 'Documentary Fact']]);
    const result = eventTable([section('Sources', table(['Source', 'Page'], [['K', '5']])), section(heading, found)]);
    assert.deepEqual(result, {headers: found.headers, rows: found.rows});
  }
  assert.ok(eventTable([section('h', table(['date and event', 'x'], []))]));
});

test('eventTable is null when no table starts with Date', () => {
  assert.equal(eventTable([section('Register', table(['Category', 'Date'], [['a', '2024']]))]), null);
  assert.equal(eventTable([section('Text only', {type: 'text', line: 2, text: 'Date'})]), null);
  assert.equal(eventTable([]), null);
});

// ---- Lane placement (package 5): a date is placed at its stated precision, never on a day it does not state.
const days = (y, m, d) => Date.UTC(y, m - 1, d) / 86400000;

test('eventSpan places a day as a point and a month, quarter or year across its whole span', () => {
  assert.deepEqual(eventSpan('2025-03-31', 'day'), {from: days(2025, 3, 31), to: days(2025, 3, 31), point: true});
  assert.deepEqual(eventSpan('2025-02', 'month'), {from: days(2025, 2, 1), to: days(2025, 2, 28), point: false});
  assert.equal(eventSpan('2024-02', 'month').to, days(2024, 2, 29));
  assert.deepEqual(eventSpan('2025-Q3', 'quarter'), {from: days(2025, 7, 1), to: days(2025, 9, 30), point: false});
  assert.deepEqual(eventSpan('2026', 'year'), {from: days(2026, 1, 1), to: days(2026, 12, 31), point: false});
});

test('eventSpan leaves a date that does not match its precision unplaced', () => {
  for (const [date, precision] of [['2025-06', 'day'], ['2025-03-31', 'month'], ['2025-Q5', 'quarter'], ['2025-02-30', 'day'], ['2025-13', 'month'], ['2025', 'week'], ['', 'day'], ['Not supplied: x', 'year'], ['May 2025', 'month'], ['2025-Q2', 'year']]) {
    assert.equal(eventSpan(date, precision), null, `${date} ${precision}`);
  }
});

test('eventAxis runs from the earliest start to the latest end and eventPlace gives percentages of it', () => {
  assert.equal(eventAxis([]), null);
  const spans = [eventSpan('2025-03-31', 'day'), eventSpan('2025-06', 'month'), eventSpan('2026-Q1', 'quarter')];
  const axis = eventAxis(spans);
  assert.deepEqual(axis, {start: days(2025, 3, 31), end: days(2026, 3, 31)});
  assert.deepEqual(eventPlace(spans[0], axis), {left: 0, width: 0});
  // Hand-computed: 365 days on the axis; June 2025 is days 62 to 91, the first quarter of 2026 days 276 to 365.
  assert.deepEqual(eventPlace(spans[1], axis), {left: 16.99, width: 7.95});
  assert.deepEqual(eventPlace(spans[2], axis), {left: 75.62, width: 24.38});
  assert.deepEqual(eventAxis([spans[0]]), {start: days(2025, 3, 31), end: days(2025, 3, 31) + 1});
});

const day = (y, m, d) => eventSpan(`${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`, 'day');
const label = ticks => ticks.filter(t => t.label).map(t => t.label);

test('eventTicks: a tick at each 1 January inside the axis, labelled by year; the percent is the eventPlace percent', () => {
  const axis = eventAxis([day(2022, 6, 15), day(2025, 3, 1)]);
  const ticks = eventTicks(axis);
  assert.deepEqual(ticks.map(t => t.label), ['2023', '2024', '2025']);
  // Hand-computed: the axis is 990 days wide; 2023-01-01 is 200 days in, 2024-01-01 is 565 and 2025-01-01 is 931.
  assert.deepEqual(ticks.map(t => t.left), [20.2, 57.07, 94.04]);
  assert.ok(ticks.every(t => t.left >= 0 && t.left <= 100));
});

test('eventTicks: an axis starting on 1 January has a tick at 0; over 12 years every Nth year is labelled, every year still has a tick up to 40 years', () => {
  assert.equal(eventTicks(eventAxis([day(2024, 1, 1), day(2024, 12, 31)]))[0].left, 0);
  const wide = eventTicks(eventAxis([day(1993, 1, 1), day(2024, 12, 31)]));
  assert.equal(wide.length, 32, 'a tick per year for 32 years');
  assert.deepEqual(label(wide), ['1995', '2000', '2005', '2010', '2015', '2020']);
  const huge = eventTicks(eventAxis([day(1900, 1, 1), day(2024, 12, 31)]));
  assert.equal(huge.length, label(huge).length, 'beyond 40 years a tick only at a labelled year');
  assert.ok(label(huge).length <= 12);
});

test('eventTicks: an axis shorter than a year gets month ticks at each 1st; none when no 1st falls inside', () => {
  const ticks = eventTicks(eventAxis([day(2024, 10, 16), day(2025, 2, 10)]));
  assert.deepEqual(label(ticks), ['Nov 2024', 'Dec', 'Jan 2025', 'Feb']);
  assert.deepEqual(eventTicks(eventAxis([day(2024, 10, 16), day(2024, 10, 18)])), []);
  assert.deepEqual(eventTicks(null), []);
});

test('eventAsOf: the percent of the as-of date on the axis, inclusive at both ends; null outside or when not a date', () => {
  const axis = eventAxis([day(2024, 1, 1), day(2024, 12, 31)]);
  assert.equal(eventAsOf(axis, '2024-01-01'), 0);
  assert.equal(eventAsOf(axis, '2024-12-31'), 100);
  assert.equal(eventAsOf(axis, '2024-07-01'), eventPlace({from: day(2024, 7, 1).from, to: day(2024, 7, 1).from}, axis).left);
  assert.equal(eventAsOf(axis, '2023-12-31'), null);
  assert.equal(eventAsOf(axis, '2025-01-01'), null);
  for (const bad of [null, undefined, '', '2024-13-01', '30 September 2024']) assert.equal(eventAsOf(axis, bad), null);
  assert.equal(eventAsOf(null, '2024-01-01'), null);
});

test('eventStack: points closer than a marker stack in date order at their own x; points far apart share the baseline', () => {
  const axis = eventAxis([day(2024, 1, 1), day(2024, 12, 31)]);
  const items = [day(2024, 1, 1), day(2024, 1, 2), day(2024, 1, 3), day(2024, 7, 1), day(2024, 12, 31)].map(span => ({span, ...eventPlace(span, axis)}));
  // On 1032 px, one day is 2.8 px: the first three are within one marker of each other.
  assert.deepEqual(eventStack(items, 1032, 16), [0, 1, 2, 0, 0]);
  assert.deepEqual(items.map(i => i.left), items.map(i => eventPlace(i.span, axis).left), 'x is not moved');
  assert.deepEqual(eventStack(items, 1032, 2), [0, 0, 0, 0, 0], 'a marker narrower than the gap needs no stacking');
});

test('eventStack: a span keeps the baseline and a point over it stacks above it; two spans that overlap stack; spans that only touch do not', () => {
  const axis = eventAxis([day(2024, 1, 1), day(2024, 12, 31)]);
  const span = (date, precision) => ({span: eventSpan(date, precision), ...eventPlace(eventSpan(date, precision), axis)});
  const year = span('2024', 'year'), june = span('2024-06', 'month'), may = span('2024-05', 'month');
  const point = {span: day(2024, 6, 10), ...eventPlace(day(2024, 6, 10), axis)};
  assert.deepEqual(eventStack([year, point], 1032, 16), [0, 1]);
  assert.deepEqual(eventStack([may, june], 1032, 16), [0, 0], 'May ends where June starts');
  assert.deepEqual(eventStack([year, june], 1032, 16), [0, 1]);
  assert.deepEqual(eventStack([june, point], 1032, 16), [0, 1]);
  assert.deepEqual(eventStack([], 1032, 16), []);
});

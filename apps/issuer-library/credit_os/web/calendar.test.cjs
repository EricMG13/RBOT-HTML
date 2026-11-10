'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {eventTable, eventOrder, orderEvents, eventSpan, eventAxis, eventPlace} = require('./calendar.js');

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

'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {eventTable, eventOrder, orderEvents} = require('./calendar.js');

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

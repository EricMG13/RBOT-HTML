'use strict';
// Pure page logic. Run: node --test apps/issuer-library/static/logic.test.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const {compareDecimal, filterRuns, sortRuns, displayDate, spendText, modelLabel} = require('./logic.js');

const run = (id, extra = {}) => ({
  id, run_id: `${id}-run`, issuer_id: 'nbg', issuer_name: 'Northbridge', pathway: 'credit_snapshot',
  as_of: '2025-03-31', latest: false, modules: [{id: 'CP-1', title: 'Canonical data foundation'}],
  execution: {models: ['gpt-6.1-sol · medium'], spend_usd: '1', started_at: '2026-11-01T10:00:00Z', unknown_charges: 0},
  ...extra,
});

test('recorded amounts compare by their decimal digits, not as binary floats', () => {
  assert.equal(compareDecimal('0.9', '0.10'), 1);
  assert.equal(compareDecimal('12', '9.5'), 1);
  assert.equal(compareDecimal('0.30', '0.3'), 0);
  assert.equal(compareDecimal('0.1', '0.10000000000000001'), -1); // Equal as floats.
  assert.equal(compareDecimal('-1', '0'), -1);
  assert.equal(compareDecimal('-2', '-1'), -1);
  assert.equal(compareDecimal('007', '7'), 0);
});

test('spend sorts exactly and a missing spend stays last both ways', () => {
  const runs = [run('a', {execution: {...run('a').execution, spend_usd: '0.9'}}),
    run('b', {execution: {...run('b').execution, spend_usd: '0.10'}}),
    run('c', {execution: {...run('c').execution, spend_usd: null}})];
  assert.deepEqual(sortRuns(runs, 'spend', 'asc').map(r => r.id), ['b', 'a', 'c']);
  assert.deepEqual(sortRuns(runs, 'spend', 'desc').map(r => r.id), ['a', 'b', 'c']);
});

test('filters combine search, issuer, pathway, model and latest', () => {
  const runs = [run('a', {latest: true}), run('b', {issuer_id: 'zzz', issuer_name: 'Zeta', pathway: 'earnings_update'}),
    run('c', {execution: {...run('c').execution, models: ['claude-opus-5.5 · medium']}})];
  assert.deepEqual(filterRuns(runs, {search: 'zeta'}).map(r => r.id), ['b']);
  assert.deepEqual(filterRuns(runs, {search: 'canonical data'}).map(r => r.id), ['a', 'b', 'c']);
  assert.deepEqual(filterRuns(runs, {issuer: 'nbg'}).map(r => r.id), ['a', 'c']);
  assert.deepEqual(filterRuns(runs, {pathway: 'earnings_update'}).map(r => r.id), ['b']);
  assert.deepEqual(filterRuns(runs, {model: 'claude-opus-5.5 · medium'}).map(r => r.id), ['c']);
  assert.deepEqual(filterRuns(runs, {latest: 'latest'}).map(r => r.id), ['a']);
});

test('dates show the recorded day and nothing is invented for a missing one', () => {
  assert.equal(displayDate('2024-09-30'), '30 Sep 2024');
  assert.equal(displayDate('2026-11-06T00:16:17.684895Z'), '6 Nov 2026');
  assert.equal(displayDate(null), '');
  assert.equal(displayDate('2024-13-01'), '');
});

test('spend text keeps zero, missing and unknown charges apart', () => {
  assert.equal(spendText({spend_usd: '0', unknown_charges: 0}), 'USD 0');
  assert.equal(spendText({spend_usd: null, unknown_charges: 0}), 'Not recorded');
  assert.equal(spendText({spend_usd: '0.25', unknown_charges: 1}), 'USD 0.25 + 1 unknown charge');
  assert.equal(spendText({spend_usd: '0.25', unknown_charges: 2}), 'USD 0.25 + 2 unknown charges');
  assert.equal(modelLabel(run('a', {execution: {models: []}})), 'Not recorded');
});

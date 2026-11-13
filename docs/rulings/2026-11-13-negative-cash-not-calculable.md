# Ruling: no net debt, net leverage or liquidity is published for a forecast year with negative cash

by: user
date: 2026-11-13

This ruling lifts no pause and authorises no provider call.

Why: on the real run `tdg-full-copilot-sol-high-001-resume` (TransDigm, as of 30 September 2024),
with the Downside of `2026-11-13-downside-follows-forward-model.md` and the shock at 0.3, closing
cash is 1,553.50 in FY2025, -309.77 in FY2026 and -2,165.72 in FY2027. Python published net
leverage of 7.34x and 7.87x and liquidity of 533.23 and -1,322.72 for the two negative years. The
forward credit model's own handoff calls those figures "Not calculable: funded closing cash and
debt not established". Negative cash is an unfunded gap: netting it against debt and adding
undrawn facilities to it states figures the module does not.

The owner's words (2026-11-13): asked in the building session "Should those cells be left empty
with a 'not calculable: cash is negative before funding' reason whenever closing cash is
negative?", "Yes, own PR"; the coordinator session relays the same answer to the same proposal.

Ruled:

1. For a forecast year whose closing cash is known and below zero, net debt, net leverage and
   accessible liquidity are published as missing with the reason
   "Not calculable: cash is negative before funding". Missing stays missing, never zero.
2. Closing cash itself stays published: it is the funding gap.
3. The calculation is not changed. The roll-forward and the break tests read the computed values.
4. It applies to every case and pathway. A year with zero or positive cash, or with cash itself
   missing, is unchanged.

Known limit: a later year whose cash turns positive again after a negative year is published as
calculable, although it rests on an unfunded opening balance.

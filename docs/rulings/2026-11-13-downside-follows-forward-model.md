# Ruling: the Forecast page's Downside follows the forward credit model

by: user
date: 2026-11-13

This ruling lifts no pause and authorises no provider call. It reverses one earlier ruling and
fixes the meaning of one field.

Reverses: the owner ruling of 2026-11-10 recorded in the comment at
`src/deploy_workflow/owners/cpos_forecast.py` ("CP-2G's own cases are computed from their changed
drivers; CP-2A's shock is a separate case on base drivers, never compounded with CP-2G's
downside").

Why: on the real run `tdg-full-copilot-sol-high-001-resume` (TransDigm, as of 30 September 2024)
the Forecast page's Downside showed FY2025 EBITDA 3,739.24, interest 1,553.21, coverage 2.41x and
positive cash in every year, while the forward credit model's own handoff states EBITDA 3,338.61,
interest 1,982.94, coverage 1.68x and a funding gap from FY2026. Two causes:

- The page applied the downside module's shock to the base drivers (12% growth); the forward
  credit model's downside is its own drivers (flat sales) with the same shock.
- The forward credit model put an additive yield change (0.0184) in `rate_increase`, a field the
  code reads as a proportional increase. The downside module had stated 0.30, proportional. On the
  run `tdg-full-copilot-sol-001-resume` the same field carried 0.025, proportional.

The owner's words (2026-11-13, given in the coordinator session and relayed to the building
session): asked which downside the Forecast page shows, "They should be complimentary to the
forward model. It's assumptions are driven by its upstream"; shown options A, B and C, "A".

Ruled (option A):

1. The Downside stress case is the downside module's shock applied to the forward credit model's
   own downside drivers. Where the forward credit model sets no downside drivers, the shock is
   applied to the base drivers, as before.
2. `downside_shock.rate_increase` is the downside module's proportional increase in cash interest
   (0 to 1), copied unchanged. It is never a yield change.
3. The forward credit model's instruction says so, and the launcher sends back for repair a
   forecast block whose shock is not one of the downside module's stated scenarios.
4. A run delivered before this ruling is not changed. It agrees with its forward credit model
   only after it is run again, which is the owner's separate, paid action.

Known limit: the forward credit model of the run above rounded its shocked yield to 0.0797, so its
printed interest (1,982.94) differs from the exact proportional figure (1,982.69) by 0.25; coverage
is 1.68x on both.

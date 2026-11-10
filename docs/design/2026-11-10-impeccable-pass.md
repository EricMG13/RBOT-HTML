# Design pass on the run report and library (`/impeccable`), 2026-11-10

Four passes over `apps/issuer-library/credit_os/web/`: critique, harden, layout, polish. Critique
snapshot (two independent assessments, 25/40): `.impeccable/critique/`. No displayed handoff value,
period, unit, source reference or limitation changed: the page text before and after differs only
by the items marked * below (word-level diff on `cpos-tdg-sol-medium-all-001`, `cpos-tdg-sol-high-001`
and the library table).

## What changed

Run report (Overview)
- Parts carry ids (`run-group-<n>`, `run-register`, `run-open-items`, `run-matrix`,
  `run-deliverables`). The navigator lists them under "On this page"; `#W-Overview/<id>` keeps the
  Overview route and scrolls to the part. The module catalogue starts closed there, as on a module page.
- * Coverage cells show the module code, as the spec says; the name and state are the cell's title.
  Navy for a conclusion, an outline for none.
- Register, open items and matrix run whole (no 70vh box), with headers that stick to the page, in
  Red Hat Text; mono is kept for numbers. Fixed columns, so an unbroken string wraps in its cell.
- A module's name (16px) and bottom line (14px) lead; finding claims are 13px. Groups sit 40px apart.
- * One chip-dot legend per set of charts, under the last card (was one per chart).
- The count of citations without a page is a quiet dotted text button, not a boxed one.
- A run with no module output says so instead of drawing an empty report.

Module page
- * The "Missing values have no bar" note prints once per Key numbers part.
- Chart-card titles are `h4`; the hidden section title is `h2`: no skipped or inverted heading levels.
- Chip sets get a third of a chart row. Analysis prose is capped at 56ch (under 80 characters a line).
- Tables read in the text face; a wholly numeric column is `.num` (mono, right), a number in a
  text column is `.fig` (mono, in place).

Library
- * Each row shows its run id. The table fits 1280px (922px box); closed criteria groups share one line.
- A ratio's basis is clamped to three lines in the row (owner, 2026-11-10). The clamp is CSS only: the
  cell's text and title hold the whole sentence, the selected-run panel prints it in full, and print
  shows it whole. Rows are 145–161px (were 245–485px before the pass).

Everywhere
- Print stylesheet (the canvas prints whole, fills kept), forced-colours rule for coverage, reduced
  motion on fold arrows, 24px minimum on small standalone targets, sideways scroll for the run
  tables at phone widths.

Second hardening pass (same day, CSS only)
- Unbroken strings (a URL, a long identifier) wrap anywhere in the canvas and the inspector; the
  navy band and the selected-run panel no longer widen the page with one.
- The library table has fixed columns and a 900px minimum: a long name, sector or basis wraps in
  its cell, and below 900px of room the table scrolls sideways in its box. Focus inside a row
  (keyboard, tap) shows that row's bases whole; a tooltip alone left keyboard and touch without them.
- The run tables scroll sideways by their own section's width (a container query), so a desktop
  canvas narrowed by the inspector behaves like a phone. The Confidence column is 92px, not 10%.
- On paper the tables drop their minimum widths; the library table sizes to its words and prints
  its header once (Chrome drops the sort buttons from a repeated header).

## Amendments to the specs

- `2026-11-09-module-report-spec.md`, Chips: "Legend line under each chart panel" becomes one legend
  under the last chart panel of a set.
- `2026-11-09-run-report-spec.md`, Coverage strip: sits under the count line, not beside it (twenty
  cells do not fit beside it at 1280px).

## Left as found

- The selected-run panel stays below the table. "Selected run" above its heading, the `—` for a
  missing rating, revenue or EBITDA, and "Open report" as plain text when the file is not linked
  are content or pre-existing behaviour.
- An opened Statements and registers part is long (16,557px on CP-1) with a summary that scrolls
  away; a sticky summary would cover routed section headings.
- The detector's `nested-cards` findings: bordered regions inside the one app frame, not cards in cards.

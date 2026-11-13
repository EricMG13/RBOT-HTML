# Brand application (2026-11-13)

Branch `claude/brand-application`, built on `claude/redesign-run-start` with `main` merged in. Plan,
rulings, reviews and probes are in `.superpowers/sdd/2026-11-12-brand-application/` (git-ignored).
Presentation only: no sentence, request, payload, `build()` or run data changed; fonts did not change.

## What the owner asked

All 2026-11-12: "Yes, build" (the brand colours and component look); "restyle, not rewrite";
"always check live"; "use assets from here: ant.design/components/overview,
untitledui.com/react/components"; "find components for run activity too. and perhaps a redesign of it
too."; "Yes, build it" (the Run activity redesign as drawn); "remove the run spend". On fonts: "Inter
titles", then "Yes, download", then "key old typography", "for headers", "and titles", and finally
"stick to current font" (see Not adopted).

## What was built

Commits: 1fdb343, 014ded8 (library and run start colours); 315931a, 0642fc2 (HTML Model colours);
e1b4a5b (component look); aad5360, 4a94b0d (Run activity); 23a1a3f (whole-branch fixes); 9f9659e
(forced-colours test).

### Issuer library and run start page: tokens (Ruling 1)

Library `screen.css` and `context-form.html` carry the same values (`tests/test_context_form.py`
pins the equality; the run start page alone owns `--ring-error`, `--red-bg`, `--red-border`).

| Token | New |
| --- | --- |
| `--navy` | `#000533` (unchanged) |
| `--blue` | `#001aff` |
| `--ground` | `#f4f4f5` |
| `--rule` | `#e8e9eb` |
| `--muted` | `#474a4f` |
| `--quiet` | `#fafafb` |
| `--selection`, `--blue-50` | `#e5e8ff` |
| `--blue-100` / `--blue-700` | `#c2c9ff` / `#0012b2` |
| `--amber` / `--amber-bg` / `--amber-border` | `#806300` / `#fff4cc` / `#f2dc8c` |
| `--red` / `--red-bg` / `--red-border` | `#8e413e` / `#fdf0f0` / `#f0cfcd` |
| `--green` | `#0f8048` |
| `--text-primary/secondary/tertiary/quaternary` | `#000533` / `#383b3f` / `#474a4f` / `#63676e` |
| `--gray-25` / `--gray-50` / `--gray-100` | `#fcfcfd` / `#fafafb` / `#f4f4f5` |
| `--gray-200` / `--gray-300` | `#e8e9eb` / `#d1d4d8` |
| `--ring` / `--ring-error` | `0 0 0 4px rgba(0,26,255,.16)` / `0 0 0 4px rgba(142,65,62,.14)` |
| `--dot-quiet` | `#8d939d` |

Links use `--blue-700` (Ruling 3). Literal greys outside the token blocks moved to the nearest token
(Ruling 2). Line heights and font sizes were not changed (Ruling 4).

### Chart colours (Rulings 5-7, 10-14)

- Library series 1-4 fill `#001aff`, `#1eff8f`, `#eaff00`, `#a29aff`; each bright fill has a 1px outline
  in its line value `#001aff`, `#0f8048`, `#758000`, `#514d80`; thin lines and series text use the line
  value (Ruling 5). Meaning-bearing colours keep their meaning on the new state values: conditional
  path, "no longer stated" amber; closed green; new blue (Ruling 6).
- HTML Model: `--rb-ch-1..5` fills `#001AFF`, `#1EFF8F`, `#EAFF00`, `#A29AFF`, `#256A80`, with `-ln`
  values `#001AFF`, `#0F8048`, `#758000`, `#514D80`, `#256A80`; waterfall up = series 1, down = series 5,
  total navy (Ruling 7). Series-3 chart text uses ink, because `#758000` is 4.34:1 (Ruling 10); Model
  legend swatches get a 1px inset edge (Ruling 11); hatched bright stack fills draw the stripe in the
  line value (Ruling 12); library comparison path 2 uses `#514d80`, away from both state colours
  (Ruling 13); library chart axis `#000533`, gridline `#e8e9eb` (Ruling 14).

### Component look (Rulings 18-19)

Reference: the live pages of Untitled UI (buttons, badges, inputs, tabs, tables, checkboxes, radio
buttons, progress steps) and Ant Design (alert, tag, descriptions, statistic, table, steps), read in a
browser on 2026-11-12; sizes in `component-reference.md`. Their React code and colours are not used.
Restyled in the pages' own CSS, box properties only (size, padding, radius, border structure), no
type change (Ruling 18). Pinned changes: status pill radius 999px to 6px; review tick 14px to 16px.
The readiness pill is a floating notice, not a state badge, and stays 999px (Ruling 19).

### Run activity (Rulings 9, 20-23)

Redesigned from the mock-up "Run activity" in `views.js` and `screen.css`: running runs as cards with a
progress bar and module chips, waiting runs as a table. Ruling 20: the success tint is the literal
`#e8fff4` on `.run-mods .chip-done`, not a library token. Ruling 21: the empty state keeps its
earlier font declarations. Ruling 22: waiting rows keep their "files read" list. Ruling 23: the empty-state
link is `primary-action`; the two `.run-primary` rules are gone.

Spend is off the page. The writer (`src/deploy_workflow/inbox/activity.py`) still emits `spent` and `cap`;
no script draws them. The USD 20 cap is still shown on the run start page before Submit (the Confirm lead
and the "Cap: USD 20 for this run" row), in `README.md`, and, after a run, on its Evidence page ("Provider
cap" and per-call "Settled (USD)"). READMEs now say Run activity shows no spend.

## Not adopted

- Inter. The owner approved a download, then ruled "stick to current font" (Ruling 17). No file, no
  `@font-face`, no declaration of Inter is in the repo; every family stays Red Hat. `plan.md`,
  `brand-spec.md` and the Task 3 brief in the working folder still say Inter and are superseded.
- The brand 140% body leading (it moves layout that tests pin; Ruling 4).
- Palette colours 5-8 in the library (the static test forbids amber or red series there).

## Sources of the values

The owner's screenshots of the brand guideline (not a file in the repo; the values were read by eye
from them). Two Claude Design mock-ups, "Brand application" and "Run activity", drawn in Inter while
the build keeps Red Hat. Component sizes from the live pages named above.

## Open for the owner

1. M2 (Ruling 24): the Model navigator's module-family edge colours (`report_view.py` `FAMILY_COLORS`,
   `_NEUTRAL_FAMILY_COLOR`) still paint `#0017E5`, `#0E7A46`, `#8A5300`, `#B3261E`, `#9AA0B4`, `#C4410C`,
   `#2B8FD6`, `#7A3DB8`; three have no brand successor and the colour travels in the rendered payload.
2. L5, legend convention: library line charts key the line value, the stack and Model legends key the
   fill with an edge, so "Capex" is an olive key over a yellow bar. One rule for all keys?
3. L6: "Current run" and "Closed" are both `#0f8048`; "Earlier run" and "New" are both `#001aff`.
   Series 2's line value equals the positive-state colour, so "Net debt / EBITDA", "Undrawn facilities"
   and a "Downside" scenario are drawn in it.
4. L7: Run activity redraws when only `spent` changes (`screen.js:709`); harmless, a text selection is
   lost on each settle.
5. Component look for the Model: square panels inside rounded library cards.
6. `#758000` is 4.34:1 on white (lines only; labels use ink). Brand values were read from screenshots.
7. Whether Run activity should say anything when a run's budget cannot be read.
8. Info: weight 500 renders as 400 (Red Hat is declared at 400 and 600); the selected navigator item is
   `--blue` on `--selection` where the brand spec says `#0012b2`; `.chip.verified` keeps `#9fc7ac`.
9. `LIVE_STATUSES` in `views.js` is now read only by a test in `tests/test_context_form.py`; removing
   both together is the owner's call.
10. Size: The branch is over the 800-line convention. `git diff --numstat origin/main...HEAD` after
    the last code commit (9f9659e) is 13 files, 1,051 added and 159 removed, 1,210 changed lines; the
    paths containing `test` account for 839 of them (806 added, 33 removed). The documents of this
    commit are on top of that.

## Pre-existing findings (not from this branch)

1. Changes, "Over time" table: the last column is clipped (identical at `4c0eafa`).
2. Run activity shows the pathway as the stored id and times as raw ISO stamps, as before.
3. A closed "N files read" list stays closed in print.
4. Unused library rules (`.run-mark`, `.activity-log`, `.activity-flow`, `.run-strip`, `.run-field(s)`,
   `.run-stages`, `.run-step`, `.run-advanced`, `.module-steps`, `.chip-*`, `.start-confirm`) and
   `web/brand.css`, linked nowhere.
5. `liveText(run.issuer_name||run.folder||run.id)` renders a truthy non-string name empty.
6. HTML Model line chart: end-of-line value labels overlap when series end close together.
7. Evidence: the "Supplied, not used" heading touches the table above it.

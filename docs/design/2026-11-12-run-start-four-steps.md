# Run start in four steps (2026-11-12)

Owner: "step order - use the design style from the Claude design, but adapate for current state of
code base."

Owner answers to the two questions asked (2026-11-12):

- Step order: "Four steps". Documents → Purpose → Confirm → Start. Today's issuer, agreement,
  market, valuation and assumptions questions are kept and grouped under Confirm, with a More
  context step. This replaces "Stage 1 is pathway selection".
- Prefill: "Today's prefill". Only what the launcher already reads; no new reading of documents.

Source: the Claude Design project's run start screens (R0-R5). Branch `claude/redesign-run-start`,
cut from main f98ff70. Plan and reports are in `.superpowers/sdd/2026-11-12-redesign-run-start/`.

## Built

The eight sections of the page stay as groups. A step map lays over them; no field moved between
sections, so `build()`, `context.json`, the requests and the saved-draft keys are unchanged.

| Step | Today's groups | What it shows |
| --- | --- | --- |
| Documents | Documents | The drop zone ("Choose the issuer's folder, or add files"), the files as rows with state dots, what the launcher recognised. No readiness panel: a pill says it appears once a purpose is chosen. |
| Purpose | Pathway | The pathways as rows (name, question, modules, and the "Needs:" text), level and submitter name side by side, the Advanced module list and turns. |
| Confirm | Issuer and dates; Legal | Issuer name and ID, dates, periods, currency; the agreement file where a module uses it. Stacked under their own headings. |
| More context | Market; Valuation; Assumptions | The groups the level asks, as today. |
| Start | Review | "What Submit does" card with Approve and Submit; the module list as rows; "Your answers" with Edit. Two columns. |

Also built: a numbered stepper (collapses to "Step i of n · name" at 960px and below), a fixed
footer with Back and Next named for the neighbouring step, the readiness column on Purpose, Confirm
and More context, and the "Run started" screen in the same look. Commits 5decc72, a6eec82, 765235d,
47bf7c7, a4408ff.

## Not adopted from the mock-up

| Mock-up | Kept instead | Why |
| --- | --- | --- |
| Drag and drop | The two buttons | None exists in the page (Ruling 7) |
| "Found" tiles, a "from file" source column, "what this folder gives it" lists | Nothing | The code has no such data (Ruling 7) |
| More context only at Standard and Advanced | Shown at Basic for a primary run, a held answer, an error, or "Answer this now" | Today's "never hide an answer" rule wins (Ruling 2) |
| Readiness panel with a "Hide" control | Panel without it; hidden on Documents and Start | Ruling 5 |
| "From file" issuer name and currency | Today's prefill | Owner answer |
| Lightest grey text `#8a90a3` | `--text-quaternary` | Contrast, as in pass 1 |

## Controller rulings

| # | Ruling | Cost if wrong |
| --- | --- | --- |
| 1 | The eight sections stay as groups; a step map lays over them | A rename |
| 2 | A step shows when the level shows any of its groups | A visibility rule |
| 3 | A step stacks its groups under their own headings; "Go to Pathway" becomes "Go to Purpose" | Labels |
| 4 | The Advanced module list stays in Purpose | Moving it later |
| 5 | No readiness panel on Documents (a pill instead); scope line empty until Purpose is visited | A display rule |
| 6 | The page title is "Start a run" | One string |
| 7 | No drag and drop, tiles, source column or folder list | Layout |
| 8 | Next is named for the next step; Skip where today's rule gives it | Labels |
| 9 | The group number is removed; the stepper carries it | Restore |
| 10 | The run and "submission gone" screens keep the page head (title, Start over) as before | A display rule |
| 11 | The Start card sticks by its bottom. With a card taller than the page, Submit is out of view only at the top of the scroll and in view from part-way to the end; before this branch Submit was at the page's very end | A layout rule |

## Verification summary

Synthetic browser tests with a stubbed service. 172 tests passed; quality gate 0 findings. Reviewer
probes: Task 1 re-review 5 passed, Task 2 14 passed, Task 3 re-review 8 passed. On a 12-module
summary Submit first comes into view after 11-20% of the scroll; on the short snapshot, after
66-75%. A focused Approve or Submit is always visible.

Not verified, collected from the reports:

- Look: only three desktop screenshots by eye (Task 2); none of Start or the run screen; no pixel
  comparison with the mock-up.
- Widths 720-960px, print, forced-colors; 375px checked only by a scroll-width probe.
- Keyboard traversal and screen readers (attributes, names and focus asserted only).
- The run screen was driven with literal run data, not a real run reaching each state.
- A pathway or level change while on More context keeps groups the new level would hide until the
  step is left.
- Real-service submit beyond the existing browser tests.

## Open, for the owner

- Pre-existing, found in the Task 2 review: the 960px breakpoint is matched by both the JavaScript
  and the CSS, and the files table keeps a 560px minimum width below 720px.
- The mock-up's library empty state (R0) is not built.

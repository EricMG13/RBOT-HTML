# Run start on an existing issuer: design (2026-11-11)

Adds to `2026-11-11-staged-run-start-design.md`. Status: approved by the owner 2026-11-11; built on branch claude/initiating-runs-existing-issuers-4a8739.

## 1. Intent

A second run on an issuer starts blank today. The analyst uploads every document again and retypes
the issuer ID. The only guard on the ID is help text ("Use the same ID for every run on this
issuer"), so a typo files the run under a new issuer folder and the issuer's history splits.

The new flow: the analyst starts from a run already in the library or in Run activity. The page
keeps that run's issuer identity, carries over its documents and answers, and asks only for what
has changed. Summary and Submit are unchanged.

## 2. Goals, non-goals, anti-goals

**Goals**
- A run started from an existing issuer cannot file under a different issuer ID.
- The analyst adds the new filings without uploading the old ones again.
- A failed run can be started again from its own inputs.

**Non-goals**
- No change to the launcher, the approval digest, the seal, the limits (3 running, 30 a day,
  USD 20 per run) or the library's listing rules.
- No change to `context/1`.
- No CP-8 design. That belongs to the Pause session's plan (section 5).
- No login (staged-run-start spec, section 8).

**Anti-goals** (failure even if it works)
- A carried-over as-of date or period: the stale as-of error of `cpos-tdg-sol-medium-all-001`
  repeated by the page itself.
- A carried-over answer the analyst cannot tell from one they gave in this submission.
- A prior run's files offered for download from the start page.

## 3. Owner decisions (2026-11-11)

1. Gaps other than CP-8 follow the builder's recommendation ("all others your recommendation").
2. CP-8 follows the Pause session, where the owner approved: the comparison with the previous
   same-pathway run, the view over time, and the limitations ledger ("1,2 and 3"); then "approved
   but make cp-8 a section just like forecast, overview and the others", described as "what has
   changed since the last time i looked at this".

## 4. The flow

### Entry

- One link form: `/?from=<run id>`.
- The library's Report history for an issuer has "Start a run"; it passes that issuer's latest run.
- The start page's own progress view offers "Start again from this run" once the run has ended
  as failed, capped, rejected or interrupted. Run activity draws only running and waiting runs
  (library decision 10), so the control is not placed there.
- The existing rail link to `/` stays as the blank start.

### What the service returns

`GET /api/runs/<id>/inputs` returns, for a run whose record and `_engine/drops/<id>/` exist:

- the run's `context.json`;
- the names and sizes of its source files (no content);
- the record's level, module subset and turns per module.

A run with a record but no source folder (started before the service) returns the issuer ID and
name only. An unknown run ID is refused.

### What the page does with it

| Stage | Carried over | Not carried over |
|---|---|---|
| 1 Pathway and level | Pathway, level, module subset and turns per module (each marked beside its input; a subset naming a module the pathway lacks is not applied) | Submitter's name |
| 2 Documents | Every prior file, listed as "carried over from run <id>", each removable | - |
| 3 Issuer and dates | Issuer name and ID (ID locked), currency, identity fields | As-of date, cutoff, current and prior period |
| 4 Legal | - | Which file is the agreement: asked again, so the answer is `none` until a file is chosen |
| 5 to 7 | Every answer | Which file is the bridge, the portfolio workbook or the prior case |
| 8, 9 | Nothing: a new summary, a new approval, a new digest | - |

- The page fills the form with its existing `fill()`; no second loader is added.
- Dates default from the newest document, as on a blank start.
- The locked ID has an "this is a different issuer" control that unlocks it and clears the
  carried-over files and answers. The level stays; a file the analyst uploaded stays.
- When the earlier run's answers cannot be used (no source folder, or unreadable), the only answers
  carried are the issuer name and ID: the level, module subset, turns and anything the analyst typed
  stay. Its documents are still carried when the source folder exists.
- Each carried-over answer is marked "from run <id>" beside its input. The summary lists them in
  one block, the way it lists defaulted inputs, so approval covers them.
- The file questions are not carried over because `context/1` records no per-file choice (staged
  run start spec, stage 4); the prior run's choice exists only in that analyst's browser.
- The service blanks the as-of date, cutoff and both periods in the context it returns, so no
  page can carry them over.

### Carrying the files

- `POST /api/submissions/<sid>/carry` with the prior run ID copies that run's source files into
  the new submission, except `context.json`. The browser never receives them.
- They are copies, not links: the seal, the digest and the launcher reading work unchanged, and a
  later change to one folder cannot reach the other.
- They count toward the upload limits (50 MiB a file, 500 files, 512 MiB in total). A carry that
  would exceed a limit is refused whole, with the limit named.
- A name already stored in the submission is kept, not replaced, and reported as kept.
- The launcher's offline reading runs on carried and new files together. A carried file is
  re-read, not trusted from the prior run.

### Same ID typed on a blank start

- Stage 3 checks the typed ID against the service's run records by exact match
  (`GET /api/issuers/<id>`). A library run the service did not start is not seen.
- On a match it shows "This issuer exists: N runs, latest as-of <date>" and offers "carry over
  from its latest run", which behaves as `/?from=` does.
- When the typed name differs from the filed name, it says so and shows the filed name. The run
  still files under the existing folder (existing rule, `filing.issuer_folder`).
- No near-match search.

## 5. CP-8

The start page asks no CP-8 question. Under the Pause session's plan (its D4, with the owner's
later amendment):

- CP-8 runs last in a run when the issuer has an earlier run of the same pathway dated on or
  before this one. The library shows "First run of this pathway" otherwise.
- Its output is its own library section, beside Overview, Modules, Forecast and Evidence: what
  has changed in the issuer's business and credit profile, and in the modules' findings, since
  the previous run.

What this design owes to it:

- The summary lists the changes section among the sections this run fills, with the run it will
  be compared against (ID and as-of date), or "First run of this pathway".
- Two prior runs can differ and the summary names both: the run the inputs were carried from
  (any pathway) and the run CP-8 compares against (same pathway).
- Both pieces of work change `run_start/submissions.py` and `docs/templates/context-form.html`.
  CP-8 lands first; this build starts from its merged result.

The CP-8 redesign had not merged when this was built, so the two summary lines are not built.
Nothing here depends on it to start a run.

## 6. Trust boundary

- Same audience as the library and no login, as the staged-run-start spec decided.
- `GET /api/runs/<id>/inputs` exposes a prior context to anyone who can reach the service. It
  holds pinned assumptions and deal terms. The owner accepted this with decision 1.
- The run ID is matched against the existing `_RUN` pattern and looked up in the run records;
  it is never joined into a path before that.
- The carry request is state-changing and needs the matching `Origin`, as uploads do.
- Carried files are copied as regular files only; a link in the prior folder is refused.

## 7. Kept, changed

**Kept**
- Stages 8 and 9, the digest, the seal, the scheduler, filing, the launcher and `context.py`.

**Changed**
- `run_start/service.py`: the three routes above.
- `run_start/submissions.py`: the carry (copy within the limits).
- `run_start/prior.py` (new): an earlier run's inputs and an issuer's runs, from the run records.
- `docs/templates/context-form.html`: reading `?from=`, the locked ID, the carried-over marks,
  the carried files in stage 2, the stage 3 existing-issuer notice.
- `apps/issuer-library/credit_os/web/`: "Start a run" on Report history, shown only when the
  service serves the library.
- `apps/issuer-library/README.md`.

## 8. Verification the plan must include

- A run started with `?from=` cannot be submitted under another issuer ID unless the analyst
  chose "this is a different issuer".
- The as-of date and periods of the prior context are absent from the built context unless the
  analyst typed them.
- A carry that exceeds a limit copies nothing. A link in the prior folder is refused.
- The digest of a submission with carried files equals the digest of the same files uploaded.
- A run started with `?from=` a run whose agreement was executed builds `none` until a file is
  chosen.
- An unknown run ID, and a carry without the matching `Origin`, are refused.
- A record with no source folder yields the issuer ID and name only.
- Tests use the existing canned launcher fixtures. No test calls a provider.
- A presentation change needs the reader check `AGENTS.md` names, recorded in VERIFICATION.md.
- A test shows two submissions carrying from one run both end with the run's files. Not proven by
  this build: Windows behaviour of the copy; two analysts carrying from the same run at the same
  moment; that source folders of old runs are never removed
  (no code that deletes them was found; it was not tested).

## 9. Left to the builder

- The wire format of the two routes and the page's internal structure.
- Whether the library's link reads the latest run from the catalogue or asks the service.
- The order of the work, provided the locked ID lands with the first carried-over field.

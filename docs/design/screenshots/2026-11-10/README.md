# Screenshots: Issuer Library, reports and context form (2026-11-10)

Taken in headless Chromium at 1440×900 (2× pixel density) from `main` at `2c83b0b`.

**Synthetic data.** Files 01–09 come from a library that `apps/issuer-library/update_library.py`
built from the browser tests' fixture runs (`tests/library_fixtures.py`): Northbridge Synthetic
Group (`run-a`, `run-b`) and Harbour Lane Synthetic Holdings (`run-c`), with CP-0 and CP-1 only.
The interface, layout and states are real; the analysis text is placeholder ("Source readiness
bottom line.", "Synthetic fixture only"), and the figures are the fixtures' own. Reports are
candidates, not accepted, and nothing here is analytical review.

To list the fixture runs, the build used the tests' stand-in for the current methodology
(`library_fixtures.method`), as `tests/test_library_page_browser.py` does.

| File | View |
|---|---|
| `01-library.png` | Issuer library: the latest run per issuer, with one run selected |
| `02-run-overview.png` | A run's Overview |
| `03-module-findings.png` | A module page (Financial foundation), at its charts and findings |
| `04-calendar.png` | Calendar tab, empty state (the fixtures retain no calendar) |
| `05-forecast.png` | Forecast tab, empty state (no forecast model published) |
| `06-evidence.png` | Evidence library |
| `07-reports.png` | Reports: this run's, the issuer's other runs' and other issuers' |
| `08-report-reader.png` | A delivered report open in the reader |
| `09-run-activity.png` | Run activity, nothing to report |
| `10-context-form-purpose.png` | Context form, Purpose stage, with the run readiness column |
| `11-context-form-sources.png` | Context form, Source files stage, with the folder check run on a test folder |
| `12-context-form-check.png` | Context form, Check & download, for a TDG-like Distressed case |

Files 10–12 are `docs/templates/context-form.html` as it ships. They show the as-of date before
the newest file, legal documents declared executed, and no peer figures. The folder check ran on a
test folder of empty and stub files made for the screenshot.

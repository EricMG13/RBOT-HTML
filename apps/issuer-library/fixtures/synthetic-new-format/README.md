# Synthetic new-format fixture

SYNTHETIC FIXTURE. These files are hand-made to the 2026-11-11 handoff contract
(`docs/rulings/2026-11-11-reader-and-issuer-report.md`, "Handoff contract"). They are not issuer
analysis and not model output. "Northbridge Synthetic Group" (`nbg`) does not exist; every figure is
invented and only consistent across these files.

Case: as of 2025-03-31, pathway credit_snapshot, modules CP-0, CP-1, CP-1A, CP-2 and CP-2D (CP-2D is
blocked, so it is "Not assessable"). Supplied files: `NBG_2025-03-31_annual-report.pdf`,
`NBG_2024-12-31_Q4-results.pdf` and `NBG_2025-02-14_facility-agreement.pdf`; no handoff cites the
facility agreement, so it is "Supplied, not used".

`SYNTHETIC-CP-3C.md` and `SYNTHETIC-CP-6.md` (added 2026-11-15, when CP-3C and CP-6's portfolio
debate joined the full credit assessment) are built into the run only with `--with-cp3c-cp6`. CP-6's
handoff carries the portfolio debate's `### Portfolio posture` section and its registers T6E.4, T6E.6,
T6E.7 and T6E.11; its other producers (security selection, evidence validation) are not in the run.

Purpose: exercise the library's reader code (passages, Basis lines, figures, Overview selection,
nearest dates) on the new format before any real run exists. Build a run folder from these files
with `python apps/issuer-library/fixtures/build_synthetic_run.py --workspace <folder>`.

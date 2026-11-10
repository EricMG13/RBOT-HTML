---
target: "Credit OS issuer library UI: library, run report and module pages"
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 4
target_identity: "file:/Users/ericguei/Documents/RBOT-HTML/.claude/worktrees/impeccable-report-library-595877/apps/issuer-library/credit_os/web/index.html"
target_fingerprint: "sha256:9bca907ca796ab4f1bb1e59a3d559a16eadf4af22d1bbd2b4c2163bebacb8165"
target_path: /Users/ericguei/Documents/RBOT-HTML/.claude/worktrees/impeccable-report-library-595877/apps/issuer-library/credit_os/web/index.html
timestamp: 2026-11-10T07-05-51Z
slug: apps-issuer-library-credit-os-web-index-html
---
Method: dual-agent (A: Fable design review · B: Fable detector and browser evidence). Routes: library, run report (cpos-tdg-sol-medium-all-001), CP-1, CP-6 at 1440 and 1280.

## Design health score: 25/40 (Acceptable)
1 Status 2 · 2 Real world 3 · 3 Control 3 · 4 Consistency 2 · 5 Error prevention 3 · 6 Recognition 2 · 7 Efficiency 2 · 8 Minimalist 2 · 9 Recovery 3 · 10 Help 3

## Design specificity
Authored for the product; run report in spec order. Fails on proportion and typographic role.
Detector (rendered routes): nested-cards 28 (treated as false positive, not adjudicated), tiny-text 11px 22 (committed label size, false positive), tiny-text 10.83px `li > small` 1 (real), skipped-heading h1→h3 on module pages 2 (real), line-length 106–111 chars on `.analysis-text` 7 (real). No page overflow, no unnamed controls, lowest contrast 5.35:1.

## Priority issues
1. [P1] Library rows indistinguishable: run id only in aria-label and the detail panel below the table. Fix: print run id in `libraryRow` identity cell.
2. [P1] Library table 964px in 922px at 1280; Deliverable clipped; rows 245–485px; criteria fill first viewport. Fix: column widths, compact criteria.
3. [P1] Run report has no navigation: register at y=6,353 of 8,465, no section ids. Fix: ids + anchor row under the count line.
4. [P1] Prose in Red Hat Mono in register/open-items/matrix (global td rule screen.css:174); Module column breaks mid-word. Fix: Red Hat Text, mono on .num only.
5. [P2] Nested scroll: `.table-scroll{max-height:70vh}` inside scrolling #content on the run report. Fix: release the cap there.
6. [P2] Story hierarchy inverted (module 12px under 14px findings); coverage strip 20 saturated name pills, spec says codes. Fix: raise module head, codes in cells.
7. [P2] Chip noise: boxed "1 citation without a page" on 33 of 33 findings; legend under each chart. Fix: quiet text button; one legend per group.

## Persona red flags
Alex: no route to the register; 55 tab stops before first library run. Sam: h1→h3 skip; colour-only coverage state on screen; nested scroll regions; two unguarded fold-arrow transitions. Riley: 485px library row; Deliverable clipped at 1280.

## Minor
Deliverables h2 15px vs 19px siblings; opened Reference 16,557px with non-sticky summary; "Evidence & audit33 sections" concatenation; library `—` for missing values left as content; "4 of 4 runs" under Latest run per issuer not investigated.

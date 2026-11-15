# Incoming, not yet registered: method scripts from cp-os b57a344

Staged by the coordinating session on 2026-11-15 for the sub-session that wires the methods'
scripts in as checks. Byte copies of `skills/<skill>/scripts/*.py` from EricMG13/cp-os at commit
b57a344 (2026-11-04), for every skill this archive holds except `cp-os-credit-os`;
`test_confidence_score.py` left out. `SHA256SUMS` lists them.

Compared with EricMG13/Deploy-V at c4d2e35: every script is byte-identical except
`completeness_check.py` (cp-os adds template columns and a bracket-aware `;` split) and
`cp-6-ic-debate-challenge/scripts/confidence_score.py` (cp-os adds a JSON stdin contract).

This folder is temporary. The files here are not in `manifest.json`, so
`tests/test_methodology_selection.py` fails while it exists. Move what is selected into
`skills/<skill>/scripts/` with manifest entries, and delete this folder.

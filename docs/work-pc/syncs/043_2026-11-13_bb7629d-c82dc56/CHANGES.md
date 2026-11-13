# Changes for the work PC

From `bb7629de900f` (the version the work PC last adapted) to `c82dc5605ab6` (2026-11-13T04:17:02Z). 4 file(s) changed. See docs/work-pc/README.md for how to use this.

## Packages and versions

### pyproject.toml requirements

No change.

### uv.lock installed versions (direct and transitive)

No change.

## Changes merged to main (oldest first)

- `57a022b` 2026-11-13 refactor(cp8): delete the reading of numbers in words and list tolerance; one small form check (Merge pull request #89 from EricMG13/claude/redesign-c3-cp8-passages)
- `90613f4` 2026-11-13 docs(work-pc): change pack for bb7629d
- `c82dc56` 2026-11-13 fix(cp8): a Basis item with the listed module name is accepted (Merge pull request #94 from EricMG13/claude/redesign-wb-basis-names)

## Files changed

`Where` gives line ranges in the new version; open those lines first.

### src

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `src/deploy_workflow/changes_check.py` | +60 −249 | L53-56, removed after L65, L71-75, removed after L898, removed after L906, L913, removed after L916, removed after L924, L929-945, L948-955, removed after L972, removed after L1021, L1023-1028, L1042-1045, L1058-1070, L1082-1083 |
| modified | `src/deploy_workflow/credit_os_chips.py` | +30 −0 | L53-82 |
| modified | `src/deploy_workflow/owners/cpos_launch.py` | +1 −30 | L50, removed after L334 |

### tests

| Status | File | +/- | Where |
|---|---|---|---|
| modified | `tests/test_changes.py` | +148 −124 | L2931, L3049, removed after L3071, L3100, removed after L3123, L3126-3128, L3130, removed after L3169, removed after L3172, removed after L3175, removed after L3187, removed after L3225, L3240, removed after L3333, removed after L3345, L3349, L3357, L3362-3363, removed after L3424, removed after L3425, removed after L3433, removed after L3439, L3442, L4073-4111, L4257-4352 |

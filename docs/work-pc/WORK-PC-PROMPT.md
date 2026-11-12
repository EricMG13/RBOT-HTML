# Prompt for the work PC

Paste everything below the line into the work PC's coding assistant. Replace
`<DOWNLOAD>` with the folder extracted from the new ZIP (for a GitHub ZIP, the
`RBOT-HTML-main` folder inside it) and `<ADAPTED>` with the work PC's working copy.

---

Update my adapted copy of this repository from a new download. Do not invent changes:
every edit must come from the download or from an adaptation already in my copy.

- `<DOWNLOAD>`: the new, unchanged download. Read only; never edit it.
- `<ADAPTED>`: my working copy, already adapted to this PC. This is what you update.

`<DOWNLOAD>/docs/work-pc/README.md` explains the change packs and the tool used below.

## 1. Back up and gather

1. Copy `<ADAPTED>` to `<ADAPTED>-backup-<today's date>` before changing anything.
2. New packs: the folders in `<DOWNLOAD>/docs/work-pc/syncs/` that are not in
   `<ADAPTED>/docs/work-pc/syncs/`, in number order. If `<ADAPTED>` has no
   `docs/work-pc/` folder, every pack is new. Read each new pack's `CHANGES.md`.
3. Confirm the packs cover the download:
   `python <DOWNLOAD>/tools/work_pc_delta.py check <DOWNLOAD>`
   If it prints `differs`/`missing`/`extra` lines, the download is newer than the last
   pack: those files have no pack entry, so read them in full in step 4.

## 2. Plan

Run:

```
python <DOWNLOAD>/tools/work_pc_delta.py plan --new <DOWNLOAD> --adapted <ADAPTED>
```

If it says `manifest.json not found` (the first sync only), add
`--base-manifest <DOWNLOAD>/docs/work-pc/baselines/04e7221.json`: my copy was adapted
from commit `04e7221` (the visuals stack, PR #41).

Each line is an action for one file:
- `copy`: changed upstream, never adapted here. Take the download's version.
- `delete`: removed upstream, never adapted here. Delete it.
- `merge`: changed upstream and adapted here. Needs step 5.
- `keep`: adapted here (or a file only this PC has), unchanged upstream. Leave it.

## 3. Packages first

Collect the "Packages and versions" tables from every new pack's `CHANGES.md`. Apply
each version change (latest pack wins) using this PC's usual package source. If a
version cannot be installed here, stop and tell me which package and version.

## 4. Copy and delete

Apply every `copy` and `delete` line exactly. Before deleting, search `<ADAPTED>` for
imports or references to that file from `keep`/`merge` files. If any exist, list them
in the report instead of deleting.

## 5. Merge

For each `merge` file:
1. Find the file in the new packs (`CHANGES.md` gives the `Where` lines;
   `changes.patch` gives the exact hunks, oldest pack first).
2. Work out this PC's adaptation: where `<ADAPTED>` differs from the old upstream text.
   That old text is the `-` and context lines of the hunks.
3. Start from the download's version and re-apply that adaptation, keeping the
   adaptation's intent where the upstream code around it moved or changed.
4. If the upstream change makes the adaptation unnecessary, or the two cannot be
   reconciled, keep the download's version and list the file in the report.

## 6. Adapt new code the same way

From the `keep` and `merge` files, list the kinds of adaptation this PC makes (for
example paths, proxy or network settings, package sources, unavailable tools). Check
the `copy` files, at their `Where` lines and in full for added files, for code that
needs the same adaptation, and apply it the same way.

## 7. Record the sync

Only when steps 3–6 are done, replace `<ADAPTED>/docs/work-pc/` with
`<DOWNLOAD>/docs/work-pc/`. The next sync uses its `manifest.json` as the starting point.

## 8. Verify

1. `python <DOWNLOAD>/tools/work_pc_delta.py check <ADAPTED>` must list only files
   that are `keep`/`merge` in the plan, plus files adapted in step 6. Explain any others.
2. Run this PC's usual fast checks or tests on the changed areas. Do not run anything
   that calls a paid model provider.

## Report

Reply with:
- the packs processed (first and last number) and the counts of copy, delete, merge
  and keep;
- the package changes applied, or not applied and why;
- each merged file: the adaptation re-applied, or why the download's version was kept;
- the files adapted in step 6 and the adaptation used;
- deletions withheld, and anything that failed in step 8;
- the backup folder's path.

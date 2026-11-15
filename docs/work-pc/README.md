# Work-PC change packs

The work PC gets this repository as a ZIP download (no git) and keeps its own adapted
copy. This folder tells it exactly what changed since the version it last adapted, so
it only re-checks those places.

## What is here

| Path | Contents |
|---|---|
| `syncs/<NNN>_<date>_<base>-<head>/CHANGES.md` | Start here. Package/version changes first (`pyproject.toml` requirements and every `uv.lock` version, transitive included), then the PRs merged, then every changed file with its status, `+/−` lines and **`Where`**: the line ranges in the new version to open. |
| `syncs/<NNN>_<date>_<base>-<head>/changes.patch` | The exact unified diff for the same range, for reading hunk by hunk. |
| `syncs/<NNN>_<date>_<base>-<head>/SYNC.json` | `base` and `head` commits of that pack. |
| `manifest.json` | The git blob hash of every file at the newest pack's `head`, that `head`, and `last_pack`, the highest pack number issued so far. |
| `baselines/04e7221.json` | The same for `04e7221`, the version the work PC first adapted (first sync only). |
| `WORK-PC-PROMPT.md` | The prompt for the work PC's assistant. |

Packs chain: each starts at the `head` of the one before it. `NNN` numbers them in order;
a number is issued once and never reused.

## Old packs are removed

Packs dated more than 14 days before today (the date in the folder name, which is the head
commit's own date, against today's date in UTC, so up to a day either way) are removed
from this folder by the same commit that adds a new pack; the newest pack always stays.
So the numbers in `syncs/` can start above `001`, and the removed packs exist only in
git history (`git log -- docs/work-pc/syncs`). Nothing else changes: `check` and `plan`
read `manifest.json`, never old packs.

A work PC that last synced more than 14 days ago is missing packs. It shows as a break in
the chain: the lowest-numbered pack that is new to the work PC has a `base` in its
`SYNC.json` that is not the `head` in the adapted copy's `docs/work-pc/manifest.json`
(first sync: not `04e7221`). `plan` is still complete and correct, because it compares
whole files. What the missing packs would have supplied comes from the old upstream
version instead:

1. Take `head` from `<copy>/docs/work-pc/manifest.json` (first sync: `04e7221`) and
   download that commit's ZIP: `https://github.com/EricMG13/RBOT-HTML/archive/<head>.zip`.
   `check <old download> --manifest <copy>/docs/work-pc/manifest.json` must print
   `identical` (first sync: `--manifest docs/work-pc/baselines/04e7221.json`).
2. Package changes: compare `pyproject.toml` and `uv.lock` in the old and the new download.
3. Merges: the old upstream text of a file is that file in the old download.

With git, the same range is `git diff <head of the copy's manifest> origin/main`.

## On the work PC, after downloading

Give the work PC's coding assistant the prompt in [`WORK-PC-PROMPT.md`](WORK-PC-PROMPT.md).
It backs up the adapted copy, reads the new packs, and then runs:

```
python tools/work_pc_delta.py check <download>                         # packs cover it?
python tools/work_pc_delta.py plan --new <download> --adapted <copy>   # what to do per file
```

`plan` compares both folders with the manifest of the version the copy was adapted
from (`<copy>/docs/work-pc/manifest.json`) and marks each file:
`copy` (changed upstream only), `delete` (removed upstream only), `merge` (changed
upstream and adapted here) or `keep` (adapted here only). The first sync has no
manifest in the copy yet; pass `--base-manifest docs/work-pc/baselines/04e7221.json`
(the visuals stack, PR #41, the version the work PC first adapted).

After the update, copying this folder into the adapted copy records the sync, so the
next `plan` starts from it. `check` and `plan` need only Python 3.11 or later; no git.

## Making a pack

Automatic: after every push to `main`, `.github/workflows/work-pc-pack.yml` runs
`generate`, which starts where the last pack ended, and commits the new pack to `main`
as `github-actions[bot]`. Download a minute after a merge so its pack is included;
`check` reports a `differs` line if a download got ahead of its pack.

By hand (needs git; for example if that workflow cannot push to a protected `main`):

```
python tools/work_pc_delta.py generate                                          # next pack
python tools/work_pc_delta.py generate --base <commit or "YYYY-MM-DD HH:MM">   # pick the start
```

`--head` defaults to `origin/main`. A range with no change outside this folder makes no pack.

```
python tools/work_pc_delta.py prune --dry-run            # list packs past the window
python tools/work_pc_delta.py prune --keep-days 14       # remove them (14 is the default)
```

`prune` never removes the newest pack, and leaves alone and reports anything in `syncs/`
not named `NNN_YYYY-MM-DD_...`. The window is `KEEP_DAYS` in `tools/work_pc_delta.py`; the workflow uses that default.

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
| `manifest.json` | The git blob hash of every file at the newest pack's `head`. |
| `baselines/04e7221.json` | The same for `04e7221`, the version the work PC first adapted (first sync only). |
| `WORK-PC-PROMPT.md` | The prompt for the work PC's assistant. |

Packs chain: each starts at the `head` of the one before it. `NNN` numbers them in order.

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

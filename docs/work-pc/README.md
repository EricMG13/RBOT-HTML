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

Packs chain: each starts at the `head` of the one before it. `NNN` numbers them in order.

## On the work PC, after downloading

1. **Find the new packs.** Compare `docs/work-pc/syncs/` in the new download with the
   same folder in the adapted copy. Every folder the adapted copy lacks is a pack
   to process, oldest first. (If the adapted copy has no `docs/work-pc/`, process all.)
2. **Confirm the packs cover the download.** Before changing anything in the
   downloaded folder (for a GitHub ZIP, the `RBOT-HTML-main` folder inside it):

   ```
   python tools/work_pc_delta.py check <downloaded folder>
   ```

   "identical to the manifest" means the packs describe every change in it. A
   `differs` line means the download is newer than the last pack: the packs miss that
   file, so compare it in full or ask for a fresh pack.
3. **Update packages first.** Apply the version table in each new `CHANGES.md`.
4. **Re-adapt only the listed files**, at the `Where` lines. Read `changes.patch`
   when the summary is not enough.
5. **See where the copy was adapted.** Run the same check on the adapted copy:

   ```
   python tools/work_pc_delta.py check <adapted copy>
   ```

   Its `differs`/`extra` lines are the work PC's own adaptations. A file in both that
   list and a pack's file list needs the most care.

`check` needs only Python 3.11 or later; git is not required.

## Making a pack (before downloading; needs git)

```
python tools/work_pc_delta.py generate --base <commit or "YYYY-MM-DD HH:MM">   # first pack
python tools/work_pc_delta.py generate                                          # every later pack
```

Without `--base` the pack starts at the `head` in `manifest.json`. `--head` defaults to
`origin/main`. Commit the new pack and merge it, then download.

# Migrations

Breaking changes between major versions, newest first. Each entry lists what a
consumer repo has to change when it bumps the version it pins.

Consumers install workflows with `gh aw add`, which copies the workflow and its
`shared/*.md` imports into `.github/workflows/`. Bumping means re-running that
command for the new version, so a renamed workflow is a rename in the consumer
repo too.

## v0.7.0 → v1.0.0

Both `tfs-*-mirrored` workflows are gone. The GitHub-mirror clone they existed
to provide is now a runtime setting on the workflow they were forked from, so
there is one workflow per job instead of two near-identical copies.

### Renames

| Was | Now |
|-----|-----|
| `tfs-implement-mirrored` | `tfs-implement` |
| `tfs-review-pr-mirrored` | `tfs-review-pr` |

`tfs-implement` and `tfs-review-pr` already existed under those names; the
mirrored variants were merged into them rather than the other way round.

### What to do

**If you were on a mirrored variant**, you were using the mirror deliberately,
so set the transport explicitly and keep it:

1. Remove the old workflow: `gh aw remove tfs-implement-mirrored` (likewise
   `tfs-review-pr-mirrored`).
2. Install the replacement: `gh aw add RealPage/agentic-workflows/tfs-implement@v1.0.0`
   (likewise `tfs-review-pr`).
3. Set the repo variable `TFS_USE_MIRROR=true`.
4. Keep `.github/workflows/tfs-mirror.yml` where it is. It is plain GitHub
   Actions YAML that `gh aw add` does not distribute, so it is not touched by
   any of the above.
5. `gh aw compile`.

Step 3 is the one that matters. Leaving `TFS_USE_MIRROR` unset still uses the
mirror when the ref is present, so runs will not break — but a mirror that has
stopped syncing then degrades to a direct clone silently. Setting it to `true`
turns that into a `::warning` instead.

**If you were on a non-mirrored variant**, nothing changes. Re-add at `@v1.0.0`
and compile. Leave `TFS_USE_MIRROR` unset.

### Choosing a transport

`TFS_USE_MIRROR` controls how each workflow obtains a working tree of the target
branch. It is read identically by `tfs-implement` and `tfs-review-pr`.

| Value | Behavior |
|-------|----------|
| unset | Use the mirror ref `tfs-mirror/<target-branch>` when it exists; otherwise clone straight from TFS. Both are supported modes and neither is reported as a problem. |
| `true` `1` `yes` `on` | Same, but warn when the mirror ref is absent. Use this when the mirror is the point. |
| `false` `0` `no` `off` | Never look for the mirror. Always clone from TFS. |

The mirror is transport only. `base_sha` and every ancestry check reference the
freshly fetched TFS tip in both modes, so a mirrored SHA is never authoritative,
and the mirror requires the companion `tfs-mirror.yml` to be installed.

Installing the mirror is worth it when a direct TFS clone dominates run time —
on a large repo that is the difference between minutes and tens of minutes. On a
smaller repo, leave it out and use the direct path.

### Also in this release

`tfs-implement`'s failure path now retries the tag transition to `agent-failed`
when the work item revision moves between the read and the write. Previously a
lost race left the work item stuck in `agent-in-progress` with no signal. No
action needed; the fix is in the workflow.

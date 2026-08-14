# Migrations

Breaking changes between major versions, newest first. Each entry lists what a
consumer repo has to change when it bumps the version it pins.

Consumers install workflows with `gh aw add`, which copies the workflow and its
`shared/*.md` imports into `.github/workflows/`. Bumping means re-running that
command for the new version, so a renamed workflow is a rename in the consumer
repo too.

## v1.0.0 → v2.0.0

`implement-issue` now waits for a human to approve its Implementation Plan
comment (Step 3) before writing any code, by default. Previously it posted
the plan and proceeded straight to implementation in the same run.

### What changed

- After the plan comment, the workflow checks the issue for
  `agent:skip-plan-review`:
  - **Present** — unchanged: proceeds immediately. This is the old default,
    now an explicit, human-set opt-in.
  - **Absent (new default)** — applies `agent:plan-pending-approval`, posts
    a comment asking for `/approve-plan` or feedback, and stops (`noop`).
    No branch or PR is created in that run.
- New trigger: `issue_comment: created`. A comment on an issue labeled
  `agent:plan-pending-approval`:
  - Starting with `/approve-plan` → the label is removed and the workflow
    resumes implementation using the plan already posted.
  - Anything else → treated as feedback: the plan is revised and reposted;
    the issue stays `agent:plan-pending-approval`.
- The workflow never applies `agent:skip-plan-review` itself — a human (or a
  separate automation a team builds) sets it ahead of time. See
  [Plan Approval](workflows/implement-issue.md#plan-approval).
- The PR merge gate is unaffected either way — merging remains entirely
  human-driven, as it always was.

### What to do

Every existing `agent:implement` consumer stops auto-implementing after the
plan comment on upgrade, unless `agent:skip-plan-review` is set before the
plan is posted.

1. `gh aw update RealPage/agentic-workflows/implement-issue` (or
   `gh aw add RealPage/agentic-workflows/implement-issue@v2.0.0` if not
   already installed), then `gh aw compile`.
2. Create the two new labels:
   ```bash
   gh label create agent:plan-pending-approval --description "Implementation plan is waiting on human approval" --color "fbca04"
   gh label create agent:skip-plan-review --description "Skip the plan-approval wait; proceed immediately after posting the plan" --color "0e8a16"
   ```
3. If a repo or team has already earned trust in a class of work and wants
   to keep the previous immediate-implementation behavior, apply
   `agent:skip-plan-review` to those issues (by hand, for now) before
   labeling them `agent:implement`. Building an automated labeler for this
   is a natural next step — see
   [Plan Approval](workflows/implement-issue.md#plan-approval) for the
   intended pattern — but is not part of this release.

Issues that had already progressed past the plan comment before the upgrade
are unaffected; this only changes runs that start fresh after upgrading.

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

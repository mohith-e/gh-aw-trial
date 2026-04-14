# agent-generate-tests

On-demand test writer. Label an open PR `agent:tests` and the agent reads the diff, identifies the new behavior that lacks coverage, writes tests for it, runs the suite, and pushes the new tests back to the PR branch as a commit.

## Getting Started

**From your terminal** (recommended — guided setup for engine, secrets, and PR creation):

```bash
gh aw add-wizard RealPage/agentic-workflows/agent-generate-tests
```

**From Claude Code or any non-interactive shell** (`add-wizard` requires a TTY, so use the non-interactive `add`):

```bash
gh aw add RealPage/agentic-workflows/agent-generate-tests
```

Then label any open PR `agent:tests` and the agent will push tests to that PR's branch.

## Scope and Guarantees

- **Tests only.** Never edits source code. If the agent finds a bug while writing tests, it stops, reverts the test, and comments on the PR with the bug report — it will not silently fix the source.
- **New tests only.** Never modifies existing tests, even if they look wrong. Existing-test cleanup is not this workflow's job.
- **Matches your repo's style.** Reads an adjacent existing test before writing a new one and blends in with the repo's assertion style, fixtures, and naming conventions.
- **One commit per run.** No mega-PRs of tests; 1-10 focused test cases aimed at the highest-value gaps (new public API, new error paths, new branches).
- **Deterministic.** No network, no real clocks, no filesystem escape hatches.

## When to use it

`agent-generate-tests` is the **right tool when a specific PR is missing coverage for specific new behavior**. Typical use:

- A PR adds a new feature and the author forgot to test an error path → label `agent:tests`, agent writes that test.
- A PR adds a new exported function and reviewers want coverage before merging → label `agent:tests`.
- A PR is a refactor but test coverage on the refactored code is thin → label `agent:tests` to bolster before merging the refactor.

It is **not** the right tool for:

- Broad, repo-wide coverage improvement. Use upstream's `daily-test-improver` for that (see below).
- Test quality cleanup (fixing flaky tests, modernizing assertion style). Neither workflow handles this — it is better as a human task.

## Pairing with upstream `daily-test-improver` for continuous coverage

If you want test coverage to improve **incrementally over time across the whole repo** rather than just on demand per PR, pair `agent-generate-tests` with the upstream [`daily-test-improver`](https://github.com/githubnext/agentics/blob/main/workflows/daily-test-improver.md) workflow from `githubnext/agentics`. Together they cover two different shapes of the same problem:

| Workflow | Trigger | Scope | Output | When to reach for it |
|---|---|---|---|---|
| `agent-generate-tests` (this repo) | PR labeled `agent:tests` | **Just the PR's diff** | Commits pushed to the PR branch | Developer wants coverage for a specific PR, right now |
| [`daily-test-improver`](https://github.com/githubnext/agentics/blob/main/workflows/daily-test-improver.md) (upstream) | Daily schedule + `/test-assist` slash command + `reaction: eyes` | **The whole repo** — agent picks the highest-value coverage gaps each run | Up to 4 **draft** PRs per day labeled `[Test Improver]`, each focused on one coverage area | Team wants background coverage improvement without any per-PR developer effort |

### How they complement each other

- **On-PR safety net** — `agent-generate-tests` catches "this PR should have had a test" moments before merge. It is developer-directed and scoped tight to the change under review.
- **Background coverage drift fighter** — `daily-test-improver` runs on its own schedule, picks a different gap each day, and opens a draft PR so humans can decide whether to merge. It prevents coverage from rotting as the codebase grows, and it uses persistent memory to remember which areas it has already tried, so it does not grind on the same spot forever.
- **Non-overlapping triggers** — one is a label on a specific PR, the other is time-based on `main`. They will not fight over the same commit.
- **Non-overlapping outputs** — one pushes to an existing PR branch, the other opens new draft PRs. Reviewers can tell them apart at a glance from the PR title and labels.

### Recommended setup for a repo that wants both

Add both in your repo's `.github/workflows/`:

```yaml
# .github/workflows/agent-generate-tests.md
---
on:
  pull_request:
    types: [labeled]
imports:
  - RealPage/agentic-workflows/workflows/agent-generate-tests.md@<version>
---
```

```yaml
# .github/workflows/daily-test-improver.md
---
on:
  schedule:
    - cron: "0 4 * * *"   # daily at 4am UTC — tune for your timezone
  workflow_dispatch:
imports:
  - githubnext/agentics/workflows/daily-test-improver.md@<version>
---
```

Start conservative:

1. **Enable `agent-generate-tests` first.** It only runs when a developer explicitly labels a PR, so the blast radius is tiny and it is easy to evaluate quality before trusting the agent further.
2. **Add `daily-test-improver` after a week or two.** Once you trust the on-PR shape, layer in the scheduled version. Because `daily-test-improver` opens **draft** PRs, it cannot merge on its own — every improvement still passes through human review before landing.
3. **Watch the first few `[Test Improver]` PRs carefully.** If the agent picks areas that are not worth testing, the upstream workflow supports `/test-assist <instructions>` as a slash command so you can redirect it at a specific module or style of test without waiting for the next scheduled run.

### What `daily-test-improver` will NOT do

- **It will never merge a PR itself** — all output is draft PRs that wait for human review.
- **It will not modify your source code** — it writes tests against what already exists.
- **It will not run if it cannot discover your test and coverage commands** — it bootstraps by probing common manifest files and commands, and stops cleanly if the repo's harness is unconventional (same as `agent-generate-tests`).

See the [upstream source](https://github.com/githubnext/agentics/blob/main/workflows/daily-test-improver.md) for the full list of behaviors, safe-outputs, and configuration options.

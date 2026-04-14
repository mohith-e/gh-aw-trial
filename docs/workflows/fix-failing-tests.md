# fix-failing-tests

Test-failure remediation agent for the **default branch**. When CI breaks on `main`, it reads the failing tests, diagnoses the root cause, fixes the code (or the test), verifies the fix, and opens a PR.

Works alongside two upstream workflows from `githubnext/agentics` that cover adjacent failure cases. This page explains which one to reach for and when.

## Getting Started

```bash
gh aw add RealPage/agentic-workflows/fix-failing-tests
```

After installing, open `.github/workflows/fix-failing-tests.md` and replace `"CI"` in the `workflows:` list with the actual name(s) of your CI/test workflows (e.g., `["CI", "Tests", "Build"]`). Then run `gh aw compile`. The workflow only fires on the default branch (`main`) and only when one of the named workflows completes with a failure.

You can also trigger it manually by labeling an issue `agent:fix-tests` with a link to the failing run, or via `workflow_dispatch`.

## Test-Failure Fix Workflows at a Glance

Three related workflows cover different test-failure scenarios. Pick the one that matches what happened:

| Scenario | Workflow | Source | Action |
|---|---|---|---|
| CI broke on `main` — nobody has a PR open for it | **`fix-failing-tests`** | This repo | Opens a new fix PR |
| CI broke on **your open PR** — you want an agent to unblock it | `pr-fix` | `githubnext/agentics` | Pushes a fix directly to the PR branch |
| CI broke and you want a **diagnosis**, not an auto-fix | `ci-doctor` | `githubnext/agentics` | Opens an issue with root-cause analysis |

You'll typically want more than one of these. `fix-failing-tests` and `pr-fix` are complementary — they cover the two most common "red CI" situations (main vs. PR). `ci-doctor` is useful as a fallback when neither fix agent is confident enough to act, and as a general explainer for flaky or hard-to-diagnose breaks.

## When to Use Which

### Use `fix-failing-tests` when…

- A merge to `main` just turned the default branch red
- A scheduled run (nightly tests, contract tests) failed
- You want an autonomous agent to catch regressions without a human typing anything
- You want a fix PR that a human can review and merge, **not** a direct push

**Trigger:** CI failure on default branch, or manually via issue label `agent:fix-tests` / `workflow_dispatch`.

**Output:** New PR on branch `agent/fix-tests-<run_id>` with Summary, Root Cause, Diagnosis, Fix, Verification, Risks, and a self-review comment.

### Use `pr-fix` when…

- You have an **open PR** and its CI checks are failing
- You want the agent to **push directly to your PR branch**, not open a separate PR
- You're comfortable invoking it via a `/pr-fix` comment on the PR

**Trigger:** `/pr-fix` slash-command comment on a PR.

**Output:** Commits pushed to the PR branch + a comment explaining what was changed.

Add it to your repo:

```bash
gh aw add githubnext/agentics/pr-fix
```

### Use `ci-doctor` when…

- A failure is hard to diagnose and you want an AI investigator, not an auto-fix
- You want every CI failure to automatically generate an issue with analysis
- You're pairing it with one of the fix workflows as a fallback for cases the fix agent can't handle confidently

**Trigger:** `workflow_run` completion (you configure which workflows to monitor).

**Output:** A GitHub issue with root-cause analysis, failure patterns, and remediation steps. Does **not** write code.

Add it to your repo:

```bash
gh aw add githubnext/agentics/ci-doctor
```

## Recommended Pairings

**Minimal setup (single workflow):**
- Just `fix-failing-tests` — autonomous main-branch remediation, fix PRs for review. Good starting point.

**Typical setup (two workflows):**
- `fix-failing-tests` for main-branch breaks
- `pr-fix` for developer-initiated PR unblocking
- Covers both directions of the common "red CI" workflow.

**Full setup (three workflows):**
- `fix-failing-tests` — auto-fix main
- `pr-fix` — on-demand PR unblocker
- `ci-doctor` — diagnosis + issue creation for everything else (including cases `fix-failing-tests` declined to act on)

## Guardrails

`fix-failing-tests` is opinionated about what it will NOT do. These are the hard rules the agent operates under:

- **Never disable, delete, or skip a failing test** to make CI green
- **Never weaken assertions** to avoid an inequality check
- **Never silence errors** with empty `catch` / `except: pass`
- **Never add `sleep()`** to resolve a race condition — fix the actual synchronization point
- **Never revert the commit** that introduced the failure (that's a human decision)
- **No unrelated refactoring** — every line of the diff must be justified by the failure

When the agent can't fix something without breaking these rules, it escalates: either `noop` with a diagnosis comment, or a draft PR with analysis for a human to take over.

## Common Mistakes

### Using `["*"]` for `workflow_run` triggers

The workflow frontmatter defaults to `workflows: ["CI"]`. If you change this to `["*"]`, the workflow fires on **every** workflow completion in your repo — including its own runs, scheduled utility workflows (CodeQL, metrics collectors, triage agents), and maintenance jobs. This causes cascading runs and wastes API credits. Only list the actual CI/test/build workflow names that, when they fail, indicate a test regression the agent should fix.

### Installing on repos without a CI test suite

`fix-failing-tests` is designed to diagnose and fix **test failures**. On repos that have no test suite (documentation repos, tracker repos, config-only repos), the `workflow_run` trigger has no useful target. The only failures it can pick up are from unrelated workflows (PME Triage, CodeQL, scanners), which aren't test failures and aren't something this agent can fix. On such repos, omit the `workflow_run` trigger entirely and use `issues` labeled (`agent:fix-tests`) or `workflow_dispatch` only.

### Listing non-test workflows in the trigger

Even when not using `["*"]`, be selective. Only list workflows whose failures indicate broken tests or broken builds. Don't include:
- **Scheduled utility workflows** (metrics collectors, triage agents, scanners)
- **Code quality tools** (CodeQL, linting-only workflows) — unless lint failures are blocking your CI
- **Documentation or maintenance workflows**

If a workflow isn't something where "the agent should try to fix the code," it doesn't belong in the `workflows:` list.

## Customizing for Your Repo

The shipped workflow discovers the stack at runtime. To tailor it (hardcoded commands, repo-specific test categories, etc.), use the same pattern documented in [`docs/workflows/implement-issue.md`](./implement-issue.md) — run `gh aw init` in your repo, then paste one of the customization prompts into Claude Code and let the gh-aw dispatcher agent drive the edit.

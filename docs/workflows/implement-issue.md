# implement-issue

Generic implementation agent. Label an issue `agent:implement` and it reads the issue, writes the code, adds tests, runs validation, and opens a PR with a self-review.

Works out of the box in any repo because it discovers the project's stack and test commands at runtime.

By default, it stops after posting its Implementation Plan and waits for a human to approve it — see [Plan Approval](#plan-approval) below.

## Requirements

| Requirement | Why |
|---|---|
| WIF auth: vars `ANTHROPIC_FEDERATION_RULE_ID` + `ANTHROPIC_SERVICE_ACCOUNT_ID` | The workflow authenticates to Anthropic via WIF (keyless) — no `ANTHROPIC_API_KEY` secret. RealPage repos inherit the org-default pair; set repo-level vars to override per product. See [Authentication](../wif-auth.md). |
| Labels: `agent:implement`, `agent:needs-review`, `agent:needs-clarification`, `ready-for-decomposition`, `agent:plan-pending-approval`, `agent:skip-plan-review` | The workflow triggers on `agent:implement`, applies the `agent:*` labels for PR handoff and ambiguous issues, applies `ready-for-decomposition` (shared with the `story-decomposition` workflow) when an issue is too large to implement in one pass, and applies/removes `agent:plan-pending-approval` around the plan-approval gate. `agent:skip-plan-review` is only ever read, never applied, by this workflow — see [Plan Approval](#plan-approval). |
| GitHub Actions: "Allow GitHub Actions to create and approve pull requests" | Required by the `create-pull-request` safe output. Settings → Actions → General → Workflow permissions. |
| Recommended: `CLAUDE.md` in the repo root | The agent trusts `CLAUDE.md` over inference when discovering stack, conventions, and commands. |

```bash
# Anthropic auth is via WIF (keyless) — no secret to set. See docs/wif-auth.md.
gh label create agent:implement --description "Triggers implement-issue workflow" --color "1d76db"
gh label create agent:needs-review --description "Implementation PR awaiting review" --color "fbca04"
gh label create agent:needs-clarification --description "Issue needs more detail before implementation" --color "d93f0b"
gh label create ready-for-decomposition --description "Issue is too large; break it into sub-issues" --color "5319e7"
gh label create agent:plan-pending-approval --description "Implementation plan is waiting on human approval" --color "fbca04"
gh label create agent:skip-plan-review --description "Skip the plan-approval wait; proceed immediately after posting the plan" --color "0e8a16"
```

## Getting Started

**From your terminal** (recommended — guided setup for engine, secrets, and PR creation):

```bash
gh aw add-wizard RealPage/agentic-workflows/implement-issue
```

**From Claude Code or any non-interactive shell** (`add-wizard` requires a TTY, so use the non-interactive `add` instead):

```bash
gh aw add RealPage/agentic-workflows/implement-issue
```

Then label any issue `agent:implement` and watch it work.

## Customizing for Your Repo

The shipped workflow is generic — it auto-discovers your stack each run. That's great for trying it out, but once you trust the agent and want faster, more predictable runs, you can tailor it to your specific codebase.

**Don't hand-edit `.github/workflows/implement-issue.md`.** Use Claude Code and let the gh-aw dispatcher agent drive the edit so the workflow stays schema-valid and the lock file stays in sync.

> **Swapping engines:** The workflow body instructs the agent to read `CLAUDE.md` as the authoritative source for stack and conventions. That works with `engine: claude`. If you change the engine, review the `CLAUDE.md` references in the workflow body — other engines may look for a different instructions file or ignore it entirely.

### Prerequisite: `gh aw init`

Both customization paths below use the dispatcher agent that `gh aw init` installs at `.github/agents/agentic-workflows.agent.md`. If that file doesn't exist yet in your repo, run:

```bash
gh aw init
```

Commit the init changes on their own PR first, then proceed with either option below.

### Option 1: Quick customization (~5 minutes)

Swaps the runtime stack-discovery for hardcoded commands specific to your repo. Faster runs, fewer "I guessed at your test command" moments, but no other changes.

Open Claude Code in your repo and paste this prompt:

```
I want to customize .github/workflows/implement-issue.md for this specific repo by hardcoding its commands and paths instead of relying on runtime discovery. Drive the edit through the gh-aw dispatcher agent at .github/agents/agentic-workflows.agent.md — it's the authoritative source for how to update gh-aw workflows correctly.

Steps:
1. Read .github/agents/agentic-workflows.agent.md in full. Follow its dispatch logic: since we are UPDATING an existing workflow, route to its "update" specialized prompt and load whatever instructions it points to.
2. Read this repo's CLAUDE.md, package manifests, and any existing CI config to identify the *actual* test command, lint command, type-check command, and directories where source and test files belong.
3. Make a surgical edit to .github/workflows/implement-issue.md: replace the "Discover the Project Context" section with a concise "Project Context" section that hardcodes those commands and paths. Leave every other section of the workflow unchanged.
4. Run `gh aw compile` after the edit so the `.lock.yml` stays in sync. If the compile fails, fix the workflow file and retry — don't hand-edit the lock file.
5. Open a PR with a clear diff. In the description, list exactly which commands and paths you baked in so I can verify them.

If you're unsure about any command, ask me before guessing. If the dispatcher agent's update prompt asks for information you don't have, ask me for it.
```

### Option 2: Full customization (a deeper rewrite)

Replaces the generic workflow with a fully tailored version shaped by your repo's conventions, testing philosophy, quality gates, and architectural patterns.

Open Claude Code in your repo and paste this prompt:

```
I want a fully tailored implementation workflow for this repo, not a generic one. Drive the rewrite through the gh-aw dispatcher agent at .github/agents/agentic-workflows.agent.md — it's the authoritative source for how to author gh-aw workflows correctly.

Steps:
1. Read .github/agents/agentic-workflows.agent.md in full. Follow its dispatch logic: since we are UPDATING an existing workflow, route to its "update" specialized prompt and load whatever instructions it points to.
2. Read this repo's CLAUDE.md, all relevant package manifests, the existing test suite, the lint/format config, any ADRs under docs/, and the existing .github/workflows/ directory to build a complete picture of the stack, conventions, architectural patterns, and quality gates.
3. Rewrite .github/workflows/implement-issue.md following the dispatcher agent's update guidance. Bake in the real test and lint commands, the conventional directories for source and test files, naming conventions, the project's testing philosophy (unit vs. integration vs. e2e), and any mandatory quality gates (coverage thresholds, type checking, security scans).
4. Preserve the existing trigger (issue labeled `agent:implement`) and the existing PR output structure (Summary / What Changed / Test Coverage / Risks / Assumptions / Out of Scope / self-review) unless the dispatcher agent's instructions say otherwise.
5. Run `gh aw compile` after the rewrite so the `.lock.yml` stays in sync. If the compile fails, fix the workflow file and retry — don't hand-edit the lock file.
6. Open a PR with the rewrite. In the PR description, list (a) the top assumptions you made about this repo's conventions so I can verify them, and (b) a short note on which dispatcher-agent prompt you routed through and why.

Ask me clarifying questions before writing anything if the repo's conventions aren't clear from the code, or if the dispatcher agent's update prompt asks for information you don't have.
```

## Plan Approval

By default, the workflow stops after posting its Implementation Plan comment (Step 3) and waits for a human to approve it before writing any code. Think of it as a cloud-hosted, asynchronous version of "a dev reviews the plan before the agent proceeds" — the same trust boundary a local interactive session gives you by default, just running unattended in Actions.

**What happens on a normal `agent:implement` run:**

1. The plan comment is posted, as before.
2. The workflow checks the issue for `agent:skip-plan-review`:
   - **Present** — proceeds immediately to implementation. This is the pre-v2 behavior, preserved as an explicit, human-set opt-in.
   - **Absent (the default)** — applies `agent:plan-pending-approval`, posts a short comment explaining how to respond, and stops. No branch or PR is created in that run.

**Responding to a pending plan**, via a comment on the issue:

- Comment **`/approve-plan`** (as the first word) to accept the plan as posted. The label is removed and the workflow resumes implementation using that plan — it does not regenerate it.
- Comment anything else — a question, a requested change, a redirect — and the workflow treats it as feedback: it revises the plan, posts the revised version, and stays `agent:plan-pending-approval`. There's no limit on revision rounds; keep commenting until the plan looks right, then approve it.

**`agent:skip-plan-review` is only ever read by this workflow, never applied by it.** A human sets it, per issue or ahead of time via automation you build, before the issue is labeled `agent:implement` (or before the plan is posted, for a re-run). Setting it up front is the only way to get the old always-proceed behavior.

**Building an auto-labeler.** Once a team has run enough `agent:implement` issues through manual approval to trust a *class* of work, the natural next step is a separate workflow that applies `agent:skip-plan-review` automatically based on mechanical, low-risk signals — bounded blast radius or file count, explicit acceptance criteria present, no open questions in the thread, no CODEOWNERS-flagged paths touched, and so on. Model it on a label-gated eligibility check with cited evidence and explicit exclusion rules, not a holistic judgment call — the same shape as this workflow's own scope check, just running as a pre-check before `agent:implement` is applied rather than inside this workflow. That detector is out of scope here; this workflow only defines the gate it reads.

## Outputs

Every run of the workflow produces one of these, depending on the trigger and the plan-approval gate:

- **Plan pending approval (the default path):** Implementation plan comment → `agent:plan-pending-approval` label → approval-request comment. No branch or PR yet.
- **Approved (`/approve-plan` comment, or `agent:skip-plan-review` was already present):** **A branch** named `agent/implement-issue-<issue_number>` → **a pull request** with sections for Summary, What Changed, Test Coverage, Risks, Assumptions, and Out of Scope → **a self-review** posted as a separate PR comment with "things I'm confident about" and "things reviewers should double-check" → **`agent:needs-review`** label on the PR.
- **Feedback comment while pending approval:** A revised plan comment, replacing the previous plan. `agent:plan-pending-approval` stays applied.

If the issue is unclear, the workflow posts a clarification comment and applies `agent:needs-clarification` instead of guessing.

If tests fail three times, the workflow opens a **draft** PR with failure details so a human can take over.

**Why the self-review is a comment, not a first-class PR review.** It would be, if `submit-pull-request-review` could target the PR the run just created — that's what it used to do, and it's the better outcome when it works. But this workflow's triggers are `issues:labeled` and `workflow_dispatch`, never `pull_request`, so `submit-pull-request-review`'s default `target: "triggering"` has nothing to resolve. The documented workaround — `target: "*"` plus the `temporary_id` from `create-pull-request` — doesn't help either: as of gh-aw v0.83.4, `submit_pr_review.cjs` never calls the temporary-ID resolver that sibling handlers (`merge_pull_request.cjs`, `close_discussion.cjs`, `update_discussion.cjs`) do use, so it can't resolve a same-run PR at all (confirmed via job logs; this is a gap in gh-aw itself, not a workflow config issue — not yet reported upstream). `add-comment`'s handler resolves temporary IDs correctly, so that's what Step 7 uses instead. Revisit this once gh-aw closes that gap.

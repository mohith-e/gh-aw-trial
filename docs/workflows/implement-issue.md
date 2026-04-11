# implement-issue

Generic implementation agent. Label an issue `agent:implement` and it reads the issue, writes the code, adds tests, runs validation, and opens a PR with a self-review.

Works out of the box in any repo because it discovers the project's stack and test commands at runtime.

## Getting Started

```bash
gh aw add RealPage/agentics/implement-issue
```

Then label any issue `agent:implement` and watch it work.

## Customizing for Your Repo

The shipped workflow is generic — it auto-discovers your stack each run. That's great for trying it out, but once you trust the agent and want faster, more predictable runs, you can tailor it to your specific codebase.

**Don't hand-edit `.github/workflows/implement-issue.md`.** Use Claude Code and let the gh-aw dispatcher agent drive the edit so the workflow stays schema-valid and the lock file stays in sync.

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

## Outputs

Every run of the workflow produces:

- **Implementation plan** posted as a comment on the issue before any code is written
- **A branch** named `agent/implement-issue-<issue_number>`
- **A pull request** with sections for Summary, What Changed, Test Coverage, Risks, Assumptions, and Out of Scope
- **A self-review** posted as a separate PR comment with "things I'm confident about" and "things reviewers should double-check"
- **`agent:needs-review`** label on the PR

If the issue is unclear, the workflow posts a clarification comment and applies `agent:needs-clarification` instead of guessing.

If tests fail three times, the workflow opens a **draft** PR with failure details so a human can take over.

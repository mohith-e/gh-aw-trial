# agent-review-pr

Automated AI code reviewer. When a PR is opened or reopened, the agent analyzes the diff for correctness, security, and alignment with the repo's patterns, then leaves up to 8 inline comments on specific lines and submits one summary review with per-dimension scores.

## Getting Started

**From your terminal** (recommended — guided setup for engine, secrets, and PR creation):

```bash
gh aw add-wizard RealPage/agentics/agent-review-pr
```

**From Claude Code or any non-interactive shell** (`add-wizard` requires a TTY, so use the non-interactive `add`):

```bash
gh aw add RealPage/agentics/agent-review-pr
```

Once installed, every new PR will automatically receive a review. No label needed — the workflow fires on `opened` and `reopened`.

## Scope and Guarantees

- **Comments only.** Cannot modify code, push commits, or request changes. Always submits as `COMMENT`, never `REQUEST_CHANGES`.
- **One review per open.** Fires on `opened` and `reopened` only — no `synchronize`, so it does not re-review on every push. Developers who want a re-review can close and reopen the PR.
- **Skips bots, drafts, and agent PRs.** Will not review Dependabot, Renovate, Copilot, or agent-authored PRs (branch names starting with `agent/`).
- **Size limit.** PRs over ~1500 changed lines / ~40 files get a comment suggesting a split instead of a review.
- **8-comment cap.** Inline comments are capped at 8; additional findings go into the summary review under "Lower-priority observations." This prevents review-bomb noise.
- **Opt-out.** Label a PR `skip-ai-review` and the agent will not run.

## Review Dimensions

The agent evaluates three dimensions and gives each a 1–5 score:

| Dimension | What it checks |
|-----------|---------------|
| **Correctness** | Off-by-one errors, logic bugs, error handling, concurrency, resource leaks, API contract violations, test coverage gaps |
| **Security** | Injection, XSS, secrets in code, auth/authz gaps, unsafe deserialization, SSRF, logging sensitive data |
| **Patterns** | Consistency with adjacent code, `CLAUDE.md` conventions, reinvented utilities, architectural leakage, missing cross-cutting concerns |

## The "What I Couldn't Judge" Section

Every review includes a "What I Couldn't Judge" section that explicitly surfaces the agent's blind spots — business logic correctness, intended UX behavior, migration safety for production data, and similar. This forces the human reviewer to focus on the things only a human can evaluate.

## Copilot Alternative

Teams whose users have a GitHub Copilot license enabling them to use GitHub Copilot Cloud Coding Agent and Code Reviewer may prefer the native Copilot code review. This workflow is for teams that want Claude-specific review graded against `CLAUDE.md`, or that value the "What I Couldn't Judge" pattern and structured per-dimension scoring — features Copilot's reviewer does not offer.

Both can coexist: this workflow skips bot-authored PRs, including Copilot's.

## Requirements

| Requirement | Why |
|---|---|
| `CLAUDE.md` in the repo (recommended) | The agent grades patterns against it — without it, reviews default to universal conventions |
| Label: `skip-ai-review` (optional) | Developer opt-out mechanism |

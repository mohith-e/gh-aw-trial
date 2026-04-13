# RealPage Agentic Workflows

**Label a pull request. An agent does the work. Close the tab.**

This is RealPage's library of ready-made [GitHub Agentic Workflows](https://github.github.com/gh-aw/). They're pre-built AI agents that live in your repo as GitHub Actions and fire when you label an issue or PR. No Python glue, no laptop scripts, no MCP servers to host. You `gh aw add` a workflow and you're done.

If you've been hand-rolling agents on your laptop, this is where that work becomes shared infrastructure.

---

## Pick Your Path

There are two ways to start, depending on how much trust you're extending on day one.

### Path A — "I'm skeptical, just show me" (zero risk)

Install **one** workflow that cannot change any code. It reviews every PR you open and leaves inline comments plus a summary score. If you hate it, delete it. If you like it, you've earned the first data point on whether agents are actually useful on your repo.

```bash
cd your-repo
git checkout main

# From your terminal (guided setup)
gh aw add-wizard RealPage/agentics/workflows/agent-review-pr.md@v0.3.0

# From Claude Code or any non-interactive shell
gh aw add RealPage/agentics/workflows/agent-review-pr.md@v0.3.0
```

> **Caution:** `add-wizard` has been observed to push commits directly to the current branch on repos without branch protection. Run it from a feature branch or ensure branch protection is enabled. Use `gh aw add` for a non-interactive alternative that generates files locally without pushing. For repos with the gh-aw dispatcher agent already set up (`.github/agents/agentic-workflows.agent.md`), you can also ask the agent directly in Claude Code or Copilot to install the workflow — no CLI command needed.

Merge the PR the wizard opens. Then open any pull request. Within a minute or two you'll see inline comments on specific lines plus a summary review with 1-5 scores across **correctness**, **security**, and **repo patterns**. It never requests changes; humans still decide whether to merge.

**Why this first:** `agent-review-pr` can only *comment*. It cannot push code. It cannot modify files. It cannot break a build. The blast radius is literally zero. If an agent is going to be wrong, this is the cheapest place to find out.

### Path B — "I'm in, show me something useful" (real work)

Install the workflow that **writes tests for your new code**. Open a PR, label it `agent:tests`, and the agent reads your diff, figures out what behavior is new, writes test cases for it, runs the suite to make sure they pass, and pushes the tests back to your PR branch as one commit.

```bash
cd your-repo
git checkout main
gh aw add-wizard RealPage/agentics/workflows/agent-generate-tests.md@v0.3.0
```

Open any PR with new behavior, slap on the `agent:tests` label, and watch commits appear on your branch. The agent writes tests only — it never touches your source code, and if it finds a bug while trying to write a test, it comments on the PR and refuses to "fix" the source on its own.

**Why this is the bigger step:** `agent-generate-tests` actually writes code. It is tightly scoped (tests, not source), self-sandboxing (one commit per run), and paranoid about drift (refuses to run on a red baseline). You're extending real trust — it ends up with commit rights to a PR branch. Start here when you want to see an agent produce something shippable.

**You can install both.** They don't conflict: one only comments, the other only writes tests. Together they form a practical first stack.

---

## The Five Golden Workflows

Once Path A or Path B has proven the shape works, here's the full set we recommend for developer-facing day-to-day work. Each one is label-triggered, scoped to one specific job, and designed to be safe to retry.

| # | Workflow | Trigger | What it does | Blast radius |
|---|---|---|---|---|
| 1 | [`agent-review-pr`](workflows/agent-review-pr.md) | PR opened | Inline review comments + 1-5 scores on correctness, security, patterns | **Comments only** — cannot modify code |
| 2 | [`agent-generate-tests`](workflows/agent-generate-tests.md) | PR labeled `agent:tests` | Writes tests for the PR's new behavior; pushes commits back to the branch | Tests only — never edits source |
| 3 | [`agent-refactor`](workflows/agent-refactor.md) | Issue or PR labeled `agent:refactor` | Behavior-preserving refactor of one area per run | Opens a PR; no API changes, no deps changes |
| 4 | [`implement-issue`](workflows/implement-issue.md) | Issue labeled `agent:implement` | Reads an issue, writes code + tests, opens a PR with self-review | Opens a PR; human reviews before merge |
| 5 | [`fix-failing-tests`](workflows/fix-failing-tests.md) | CI failure on `main`, or issue labeled `agent:fix-tests` | Diagnoses the failing test, fixes code or test, opens a fix PR | Opens a PR; human reviews before merge |

These are ordered **from least to most trust**. A sensible adoption path:

1. Start with #1. Let it run for a week on real PRs. Calibrate how often it's helpful.
2. Add #2. See an agent contribute actual commits for the first time, in a tightly scoped way.
3. Add #3 or #5 next — they're both incremental (one area, one test failure at a time).
4. Add #4 last, once you trust the earlier ones. This is the one where an agent writes a feature from an issue, and it is the biggest trust extension in the set.

> **Copilot overlap:** Teams whose users have a GitHub Copilot license enabling them to use GitHub Copilot Cloud Coding Agent and Code Reviewer may prefer the native Copilot equivalent for #1 (code review) and #4 (implement-issue). The other three — tests, refactor, fix-failing-tests — fill gaps where Copilot has no equivalent. Both can coexist.

> See [`docs/workflows.md`](docs/workflows.md) for the full reference, including pipeline workflows like PRD generation, auto-remediation, and Fortify triage.

---

## There's a Whole Library Upstream Too

These five are ours. They work alongside the broader library at [`githubnext/agentics`](https://github.com/githubnext/agentics) — dozens of agents maintained by GitHub's agentics team. They install the same way:

```bash
gh aw add-wizard githubnext/agentics/daily-test-improver    # incremental coverage across the whole repo
gh aw add-wizard githubnext/agentics/ci-doctor              # diagnoses flaky CI failures
gh aw add-wizard githubnext/agentics/pr-fix                 # opens focused fix PRs for review comments
```

A few especially useful combinations:

- **On-PR tests + incremental coverage** — `agent-generate-tests` (this repo) for per-PR gaps, plus `daily-test-improver` (upstream) for background coverage improvement across the whole codebase. See [`docs/workflows/agent-generate-tests.md`](docs/workflows/agent-generate-tests.md) for a recommended phased rollout.
- **Fix-failing-tests + ci-doctor + pr-fix** — layered incident response for flaky or broken CI. Explained in [`docs/workflows/fix-failing-tests.md`](docs/workflows/fix-failing-tests.md).

Pin everything to a tagged version (`@v0.3.0`), never `@main`, in any repo where real code lives.

---

## "I Already Built Agents on My Laptop — Why Would I Switch?"

If you've written a Python or Node script that calls the Claude API to review PRs, generate docs, or summarize issues, **gh-aw is the same prompt engineering, wrapped in a GitHub-native harness**. You're not throwing away your work — you're lifting it out of `~/scripts/` and into the repo itself, where the whole team benefits.

The side-by-side:

| Your laptop script | The gh-aw equivalent |
|---|---|
| Python/Node file with hardcoded `anthropic` calls | A markdown file with frontmatter + natural-language prompt |
| `gh pr comment`, `gh issue create`, `git push` called directly | Safe-outputs (`add-comment`, `create-issue`, `push-to-pull-request-branch`) — the harness does the writes |
| Cron job on your laptop, or `launchd`, or a VM nobody owns | GitHub Actions schedule / label / PR trigger |
| Secrets in your shell env (`ANTHROPIC_API_KEY=...`) | Repo secret, injected by the harness at run time |
| "It works on my machine" | Runs identically for every team member |

The **single biggest unlock** is safe-outputs: instead of your script holding raw write credentials, gh-aw's harness accepts structured instructions from the agent (*"post this comment"*, *"open this PR"*) and performs them with scoped permissions. You keep the prompt, you drop the boilerplate, and you get reviewability — because your agent is now just a markdown file in your repo, tracked in git.

**Porting path:**

1. **Read one of our workflows.** Any file under [`workflows/`](workflows/) is the full agent. The frontmatter declares the trigger and what it's allowed to write; the body is the prompt.
2. **Copy the shape.** Take your existing prompt. Put it in a new markdown file with gh-aw frontmatter. Replace your `anthropic.messages.create(...)` glue with the matching `safe-outputs:` declaration.
3. **Test it in a throwaway repo first.** Create an empty sandbox repo you don't mind breaking, point a consumer stub at your branch (`@my-branch`), and iterate there before touching anything real.
4. **Move it to a shared repo** once it works. Either add it here in `RealPage/agentics` (PRs welcome — see **Contributing** below) or keep it in your own team's repo and import it the same way.

If your homegrown agent depends on a tool gh-aw doesn't expose yet, the escape hatch is [MCP servers](https://github.github.com/gh-aw/reference/tools/#mcp-servers) — declare them in the workflow frontmatter and the agent gets access. Most of what a laptop script does (git, file reads, bash, HTTP) is already built into gh-aw.

---

## On TFS Today? You Don't Have to Wait for Migration

**[Coming soon]** We're exploring a path for repos still hosted on TFS (Azure DevOps / TFVC) to use gh-aw workflows *now*, without waiting for a full GitHub migration. The likely shape is a small staging repo on GitHub that mirrors your TFS code, runs gh-aw workflows against it, and syncs agent-generated PRs back to TFS for review.

If you're on TFS and this would unblock your team, please file an issue against this repo (or reach out to the Agentic Workflows team directly) — concrete demand is what moves this from "exploring" to "building." Tracking will land in a dedicated issue; watch this section for a link.

---

## Try It Without Installing

Not ready to touch a real repo yet? Open any file under [`workflows/`](workflows/) — they're plain markdown. The frontmatter declares the trigger and safe-outputs; the body is the natural-language prompt the agent follows. [`agent-review-pr.md`](workflows/agent-review-pr.md) is a good starting read because it shows the full shape of a PR-review agent in under 300 lines.

When you're ready to try one for real, go back to **Pick Your Path** at the top of this README — Path A (`agent-review-pr`) has zero blast radius and is the safest first install.

---

## Learn More

- [gh-aw documentation](https://github.github.com/gh-aw/) — the official GitHub Agentic Workflows docs
- [gh-aw imports reference](https://github.github.com/gh-aw/reference/imports/#remote-repository-imports) — how remote imports and version pinning work
- [Agent Factory blog series](https://github.github.com/gh-aw/blog/) — 100+ production workflows with real metrics
- [Workflow reference](docs/workflows.md) — detailed docs on every workflow in this repo, including pipeline diagrams
- [CLI cheatsheet](docs/cli-cheatsheet.md) — common `gh aw` commands for managing and debugging

---

## Full Workflow Reference

The five golden workflows above are the recommended on-ramp. The full set — including PRD pipelines, auto-remediation, Fortify triage, and documentation workflows — is:

| Workflow | What it does | How to trigger |
|----------|-------------|----------------|
| `agent-generate-tests` | Writes tests for a PR's new behavior; pushes them to the PR branch | PR labeled `agent:tests` |
| `agent-refactor` | Behavior-preserving refactor of one area per run | Issue or PR labeled `agent:refactor` |
| `agent-review-pr` | Auto AI code review with inline comments and a summary score | PR opened |
| `auto-remediation` | Finds errors in logs, opens fix PRs | Every 2 hours or manual |
| `fix-failing-tests` | Diagnoses a failing test, fixes code or test, opens a fix PR | CI failure on `main` or issue labeled `agent:fix-tests` |
| `fortify-fix` | Reads a Fortify issue and opens a focused fix PR | Issue labeled `fortify-fix` |
| `fortify-triage` | Pulls Fortify SAST findings, opens one issue per vuln | After Fortify scan or weekly |
| `implement-issue` | Reads an issue, writes code + tests, opens a PR with self-review | Issue labeled `agent:implement` |
| `mcp-selection` | Configures data sources for agents | PRD PR merged to main |
| `pme-triage` | Fetches PMEs from Salesforce, surfaces untracked ones as issues | Every 6 hours or manual |
| `prd-decomposition` | Breaks a PRD into epic + stories | PRD PR merged to main |
| `prd-generation` | Writes a PRD from a feature idea | Issue labeled `feature-idea` |
| `skill-selection` | Pulls coding skills for your stack | PRD PR merged to main |
| `story-decomposition` | Breaks a story into implementation sub-issues | Issue labeled `ready-for-decomposition` |
| `validation` | Checks code against PRD acceptance criteria | PR labeled `needs-validation` |

Install any of them the same way:

```bash
gh aw add-wizard RealPage/agentics/workflows/<workflow-name>.md@v0.3.0
```

### Adding auto-remediation

The auto-remediation workflow needs a few extra inputs (Elastic endpoints, Kibana config). The wizard walks you through them:

```bash
gh aw add-wizard RealPage/agentics/workflows/auto-remediation.md@v0.3.0
```

> **Important:** GitHub Actions does not populate `inputs.*` on scheduled runs — `workflow_dispatch` input defaults are UI-only and have no runtime effect. This workflow uses a workflow-level `env:` block instead. After import, open `.github/workflows/auto-remediation.md` and fill in `SERVICE_NAME`, `KIBANA_BASE_URL`, `KIBANA_DATA_VIEW_ID`, and `TITLE_PREFIX` in the `env:` section at the top. Then run `gh aw compile`. Because `gh aw update` does a 3-way merge, your values will be preserved across updates.

---

## Contributing

Want to improve these workflows for everyone?

1. Create a branch in this repo
2. Edit the workflow under `workflows/`
3. Test by pointing a consumer repo's stub at your branch: `@my-branch`
4. Open a PR — once merged and tagged, all consumers can bump their version ref

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard. A CI check enforces this on every PR.

### Development Tooling

This repo is set up for authoring workflows with GitHub Copilot Agent and VS Code:

- **Copilot Agent dispatcher** — `.github/agents/agentic-workflows.agent.md` routes requests to the right gh-aw prompt (create, update, debug, upgrade). Open the repo in VS Code or GitHub Copilot and ask it to "create a new workflow" or "debug workflow X".
- **VS Code MCP server** — `.vscode/mcp.json` connects the `gh aw mcp-server` so Copilot can call gh-aw tools directly.
- **Copilot setup steps** — `.github/workflows/copilot-setup-steps.yml` installs the gh-aw CLI in Copilot Agent's environment.

To set up a new repo for workflow authoring in the same way, run:

```bash
gh aw init
```

### Automated Documentation

A `daily-doc-updater` workflow runs on this repo every day. It scans merged pull requests from the last 24 hours, identifies undocumented features, and opens documentation PRs automatically. You don't need to manually update `README.md` or `docs/workflows.md` for every change — the agent handles routine doc updates.

### Versioning and Releases

This repo uses [release-please](https://github.com/googleapis/release-please) to automate releases. When a PR is merged to `main`, release-please opens a release PR that bumps the version and updates the changelog based on your commit messages. Merge that PR to cut a new GitHub release and tag.

Semver rules for commit types:
- **Patch** (`fix:`) — bug fixes to workflow instructions
- **Minor** (`feat:`) — new workflows or non-breaking enhancements
- **Major** (`feat!:` or `BREAKING CHANGE:` footer) — breaking changes

Pin to a specific version in production (e.g., `@v0.3.0`). Use `@main` only during development.

### Updating workflows in your repo

Use `gh aw update` to pull the latest version and update the pinned SHA:

```bash
gh aw update auto-remediation
```

To target a specific tag:

```bash
gh aw update auto-remediation --ref v0.3.0
```

By default, `update` does a 3-way merge — your local changes are preserved and merged with upstream changes. So your customizations won't be overwritten.

If you ever want to discard local changes and take the upstream version exactly:

```bash
gh aw update auto-remediation --no-merge
```

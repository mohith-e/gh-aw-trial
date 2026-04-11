# Agentics

RealPage's shared library of [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/). Add AI-powered automation to your repo — PRD generation, task decomposition, code validation, auto-remediation, and more.

Workflows run as GitHub Actions, triggered by labels, PR events, or schedules. You add them to your repo with one command.

## Quick Start

### Prerequisites

1. Install the [gh-aw CLI](https://github.github.com/gh-aw/)
2. Make sure your repo has a `CLAUDE.md` describing your project's tech stack, conventions, and key paths

### Add a workflow

```bash
cd your-repo

# Make sure your checkout is clean and on main
git checkout main

# Add any workflow from this library — the wizard walks you through setup
# and creates a PR for review
gh aw add-wizard RealPage/agentics/workflows/prd-generation.md@v0.2.0
```

That's it. Label an issue `feature-idea` and the agent writes a PRD and opens a PR.

### Available workflows

| Workflow | What it does | How to trigger |
|----------|-------------|----------------|
| `prd-generation` | Writes a PRD from a feature idea | Label an issue `feature-idea` |
| `prd-decomposition` | Breaks a PRD into epic + stories | Merge a PRD PR to main |
| `story-decomposition` | Breaks a story into implementation sub-issues | Label an issue `ready-for-decomposition` |
| `skill-selection` | Pulls coding skills for your stack | Merge a PRD PR to main |
| `mcp-selection` | Configures data sources for agents | Merge a PRD PR to main |
| `validation` | Checks code against PRD criteria | Label a PR `needs-validation` |
| `auto-remediation` | Finds errors in logs, opens fix PRs | Every 2 hours (looks back 2 hrs) or manual |
| `fortify-triage` | Pulls Fortify SAST findings, opens one issue per critical/high vuln | After Fortify scan completes, weekly, or manual |
| `fortify-fix` | Reads a Fortify issue and opens a focused fix PR | Issue labeled `fortify-fix` |

Pick and choose. You don't need all of them — add only what's useful for your project.

```bash
# Add several at once
gh aw add-wizard RealPage/agentics/workflows/prd-generation.md@v0.2.0
gh aw add-wizard RealPage/agentics/workflows/prd-decomposition.md@v0.2.0
gh aw add-wizard RealPage/agentics/workflows/validation.md@v0.2.0
```

### Adding auto-remediation

The auto-remediation workflow requires several inputs (Elastic endpoints, Kibana config, etc.). Use the `add-wizard` command to walk through setup interactively. Pass the tag ref so it locks to a specific version instead of a commit hash:

```bash
# Make sure your checkout is clean and on main
git status
git checkout main

# Run the wizard — it will add the workflow and create a PR for review
gh aw add-wizard RealPage/agentics/workflows/auto-remediation.md@v0.2.0
```

The wizard will prompt for your service name, Kibana base URL, data view ID, and other inputs. Once complete, it creates a PR that can be reviewed and merged.

> **Important:** GitHub Actions does not populate `inputs.*` on scheduled runs — `workflow_dispatch` input defaults are UI-only and have no runtime effect. This workflow uses a workflow-level `env:` block instead, which applies to both schedule and manual dispatch. After import, open `.github/workflows/auto-remediation.md` and fill in `SERVICE_NAME`, `KIBANA_BASE_URL`, `KIBANA_DATA_VIEW_ID`, and `TITLE_PREFIX` in the `env:` section at the top. Then run `gh aw compile`. Since `gh aw update` does a 3-way merge, your values will be preserved on future updates.

> See [docs/workflows.md](docs/workflows.md) for detailed documentation, pipeline diagrams, and how workflows chain together.

## Try It Without Installing

Not ready to add workflows to your repo? You can explore how they work first:

1. **Read a workflow** — open any file in [`workflows/`](workflows/) to see the full agent instructions. They're just markdown.

2. **Look at the examples** — the [`examples/`](examples/) directory shows the thin stubs that go in your repo's `.github/workflows/`. Most are under 15 lines.

3. **Try the template** — spin up a throwaway repo with everything pre-configured:
   ```bash
   gh repo create RealPage/my-sandbox --template RealPage/agentic-workflow-template --private
   cd my-sandbox
   gh aw compile
   ```

4. **Watch the pipeline** — file an issue with the `feature-idea` label on the template repo and watch the agents work through PRD → stories → implementation.

## Learn More

- [gh-aw documentation](https://github.github.com/gh-aw/) — the official docs for GitHub Agentic Workflows
- [gh-aw imports reference](https://github.github.com/gh-aw/reference/imports/#remote-repository-imports) — how remote imports work
- [Agent Factory blog series](https://github.github.com/gh-aw/blog/) — 100+ production workflows with real metrics
- [Workflow reference](docs/workflows.md) — detailed docs on each workflow in this repo, including pipeline diagrams
- [CLI cheatsheet](docs/cli-cheatsheet.md) — common `gh aw` commands for managing and debugging workflows

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

Pin to a specific version in production (e.g., `@v0.1.0`). Use `@main` only during development.

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



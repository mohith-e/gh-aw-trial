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

# Add any workflow from this library
gh aw add RealPage/agentics/prd-generation

# Compile and push
gh aw compile
git add .github/
git commit -m "Add PRD generation workflow"
git push
```

That's it. Label an issue `feature-idea` and the agent writes a PRD and opens a PR.

### Available workflows

| Workflow | What it does | How to trigger |
|----------|-------------|----------------|
| `prd-generation` | Writes a PRD from a feature idea | Label an issue `feature-idea` |
| `decomposition` | Breaks a PRD into epic + stories | Merge a PRD PR to main |
| `skill-selection` | Pulls coding skills for your stack | Merge a PRD PR to main |
| `mcp-selection` | Configures data sources for agents | Merge a PRD PR to main |
| `validation` | Checks code against PRD criteria | Label a PR `needs-validation` |
| `auto-remediation` | Finds errors in logs, opens fix PRs | Hourly schedule or manual |

Pick and choose. You don't need all of them — add only what's useful for your project.

```bash
# Add several at once
gh aw add RealPage/agentics/prd-generation
gh aw add RealPage/agentics/decomposition
gh aw add RealPage/agentics/validation
```

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

## Contributing

Want to improve these workflows for everyone?

1. Create a branch in this repo
2. Edit the workflow under `workflows/`
3. Test by pointing a consumer repo's stub at your branch: `@my-branch`
4. Open a PR — once merged and tagged, all consumers can bump their version ref

### Versioning

This repo uses semver tags. Pin to a specific version in production (e.g., `@v0.1.0`). Use `@main` only during development.

- **Patch** (`v0.1.1`) — bug fixes to workflow instructions
- **Minor** (`v0.2.0`) — new workflows or non-breaking enhancements
- **Major** (`v1.0.0`) — breaking changes

### Updating workflows in your repo

Bump the version ref in your stubs and recompile:

```yaml
imports:
  - RealPage/agentics/workflows/prd-generation.md@v0.2.0
```

```bash
gh aw compile
git add .github/
git commit -m "Update agentic workflows to v0.2.0"
```

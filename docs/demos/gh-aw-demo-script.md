# gh-aw Demo Script — 1 Hour, Rehearsable

**Audience:** Senior engineers who built RADD (AI-powered SDLC automation on Azure DevOps)
**Tone:** Non-competitive, complimentary. RADD is impressive. gh-aw is complementary.
**Format:** Live demo with talking points. Show, don't tell.

---

## Pre-Demo Setup Checklist

- [ ] `gh aw` CLI installed and authenticated (`gh aw --version`)
- [ ] `lumina-agents-mcp` repo cloned, workflows compiled, GitHub Actions enabled
- [ ] `ANTHROPIC_API_KEY` secret configured on `lumina-agents-mcp`
- [ ] `gh-aw-shared-workflows` repo up to date on `main`
- [ ] Draft feature idea ready to file (title: "Add agent response caching with configurable TTL")
- [ ] Pre-completed pipeline run available on `lumina-agents-mcp` as backup (PRD PR, decomposed issues, implementation PR, validation comment)
- [ ] Elastic MCP endpoint configured (if showing auto-remediation live)
- [ ] Browser tabs pre-loaded:
  1. [gh-aw docs — Overview](https://github.github.com/gh-aw/introduction/overview/)
  2. [gh-aw blog / Agent Factory](https://github.github.com/gh-aw/blog/2026-01-12-welcome-to-pelis-agent-factory/)
  3. [gh-aw-shared-workflows README](https://github.com/RealPage/gh-aw-shared-workflows)
  4. [lumina-agents-mcp repo](https://github.com/RealPage/lumina-agents-mcp)
  5. [github/gh-aw repo](https://github.com/github/gh-aw) — for Related Projects
  6. [Patterns page](https://github.github.com/gh-aw/patterns/issue-ops/)
  7. [Engines reference](https://github.github.com/gh-aw/reference/engines/)
- [ ] Terminal open with `gh-aw-shared-workflows` and `lumina-agents-mcp` repos

---

## Segment 1: Opening & Framing (5 min)

### Talking Points

> "Before I start — I want to acknowledge the elephant in the room. You've already built this. RADD is a production agentic development platform. You have the wizard, the Slack notifications, the observability dashboard, the Azure DevOps integration. That's real engineering and real value being delivered today.
>
> So why am I showing you something else?
>
> The answer isn't 'this replaces RADD.' It's: 'what if the teams that already live in GitHub could get similar capabilities natively — with no custom platform to build or maintain?'
>
> GitHub Agentic Workflows — gh-aw — is GitHub's answer to that question. It's being built by GitHub Next and Microsoft Research. Peli de Halleux, Don Syme, and their team are actively developing it. It entered technical preview in February 2026.
>
> Here's what's happening in the community right now: Peli's Agent Factory runs 100+ workflows in production on the gh-aw repo itself. There's a 19-part blog series documenting the results. The repo has 3,700+ stars and 275 releases. This is moving fast.
>
> The pitch today is simple: **RADD handles your Azure DevOps teams. gh-aw handles your GitHub teams. Together, you cover your entire engineering org.** Let me show you how."

### Live Demo Steps

1. *No screen action needed — this is a verbal opening.*
2. Optionally show the [GitHub blog announcement](https://github.blog/changelog/2026-02-13-github-agentic-workflows-are-now-in-technical-preview/) briefly — one sentence: "Entered tech preview last month."

### Transition

> "Let me start by walking you through the docs so you can see what gh-aw actually is architecturally."

---

## Segment 2: gh-aw Overview — Review the Docs (10 min)

### Talking Points

This segment establishes credibility with the architecture. This audience builds platforms — they want to see the engineering underneath.

### Live Demo Steps

**Step 1: Overview page** (2 min)
- Open [https://github.github.com/gh-aw/introduction/overview/](https://github.github.com/gh-aw/introduction/overview/)

> "Workflows are markdown files with YAML frontmatter. Not complex YAML pipelines — natural language instructions that compile down to hardened GitHub Actions. You write what you want the agent to do in plain English, and `gh aw compile` generates a lockfile — the actual Actions YAML."

- Scroll to show the markdown-to-YAML compilation concept.

**Step 2: gh-aw repo README — Related Projects** (1 min)
- Switch to the [github/gh-aw repo](https://github.com/github/gh-aw)
- Scroll to Related Projects section

> "This isn't one tool — it's an ecosystem. The Agent Workflow Firewall handles network egress control. The MCP Gateway centralizes tool access. The Agentics sample pack has 50+ ready-to-use workflows. This is GitHub investing in an open platform, not a closed product."

**Step 3: Engine flexibility** (2 min)
- Open [https://github.github.com/gh-aw/reference/engines/](https://github.github.com/gh-aw/reference/engines/)

> "Engine flexibility. Copilot is the default, but swapping to Claude, Codex, or Gemini is one line in your frontmatter."

- Show the engine configuration table:

| Engine | Frontmatter | Secret |
|--------|------------|--------|
| Copilot | `engine: copilot` | `COPILOT_GITHUB_TOKEN` |
| Claude | `engine: claude` | `ANTHROPIC_API_KEY` |
| Codex | `engine: codex` | `OPENAI_API_KEY` |
| Gemini | `engine: gemini` | `GEMINI_API_KEY` |

> "No vendor lock-in. If a better model comes out next month, you change one line and recompile."

**Step 4: Safe outputs and security** (2 min)
- Open [https://github.github.com/gh-aw/introduction/architecture/](https://github.github.com/gh-aw/introduction/architecture/)

> "Security is defense-in-depth, three layers. At the substrate level — runner VM isolation, container boundaries. At the configuration level — schema validation, action pinning, static analysis with actionlint and zizmor. At the plan level — agents run read-only and request actions through structured output. A separate permission-controlled job actually executes those requests.
>
> The agent never directly touches your repo. It proposes. A validated, rate-limited job acts. Every operation is logged. You can set max operations per run, required labels, blocked patterns, auto-expiration on created items.
>
> For public repos, there's lockdown mode — XPIA protection that sanitizes content, filters URIs, detects prompt injection attempts, and isolates tokens outside the agent container. This is the kind of security engineering you'd expect from GitHub."

**Step 5: Design patterns** (3 min)
- Open [https://github.github.com/gh-aw/patterns/issue-ops/](https://github.github.com/gh-aw/patterns/issue-ops/)
- Click through 2-3 pattern pages to show the variety

> "Here's where it gets interesting for how you'd adopt this. gh-aw defines named operational patterns — think of them as lego blocks."

Show the pattern list:

| Pattern | What it does |
|---------|-------------|
| **IssueOps** | Issues as automation triggers |
| **LabelOps** | Label changes trigger workflows |
| **DailyOps** | Scheduled cron automation |
| **ChatOps** | Slash commands in comments (`/plan`, `/review`, `/q`) |
| **DispatchOps** | Manual and API-triggered workflows |
| **TaskOps** | Research → review → implement task chains |
| **MemoryOps** | Stateful agents that learn across runs |
| **MultiRepoOps** | Cross-repository workflows |
| **SideRepoOps** | Side-repository operations |
| **ProjectOps** | GitHub Projects v2 integration |

> "These are composable building blocks. Your team picks the patterns that match how they already work. gh-aw doesn't force a prescribed process. Team A might use IssueOps and LabelOps. Team B might use the full TaskOps chain. Team C might only use DailyOps for automated monitoring. It's their choice."

### Transition

> "So that's the architecture. But does it actually work at scale? Let me show you production results."

---

## Segment 3: Peli's Agent Factory — Proof at Scale (5 min)

### Talking Points

This segment answers the skeptic's question: "Cool architecture, but does it ship real code?"

### Live Demo Steps

**Step 1: Agent Factory overview** (1 min)
- Open [https://github.github.com/gh-aw/blog/2026-01-12-welcome-to-pelis-agent-factory/](https://github.github.com/gh-aw/blog/2026-01-12-welcome-to-pelis-agent-factory/)

> "Peli de Halleux from Microsoft Research runs what he calls the Agent Factory. It's 100+ agentic workflows running on the gh-aw repository itself. He wrote a 19-part blog series documenting every workflow category — triage, documentation, refactoring, security, testing, release, analytics. Each one with real metrics."

**Step 2: Production metrics** (3 min)
- Navigate to the Project Coordination blog post (Plan Command metrics)
- Show key numbers:

> "Let me give you the headline numbers."

| Workflow | Merged PRs | Merge Rate |
|----------|-----------|------------|
| **Plan Command** | 514 | 67% |
| **Documentation Updater** | 57 | 96% |
| **Documentation Unbloat** | 88 | 85% |
| **Semantic Function Refactor** | 112 | 79% |
| **Duplicate Code Detector** | 76 | 79% |
| **CLI Consistency Checker** | 80 | 78% |

> "514 merged PRs from the Plan Command alone — that's the `/plan` ChatOps command that decomposes issues into implementation plans and drives them through to PRs. 67% merge rate means two-thirds of AI-generated PRs were accepted by human reviewers.
>
> Documentation Updater: 96% merge rate. It keeps docs in sync with code changes — almost never wrong.
>
> Semantic Function Refactor: 112 merged PRs at 79%. This is non-trivial refactoring — renaming for consistency, restructuring function signatures.
>
> These aren't demos. These are production workflows that have been running for months on an active codebase."

**Step 3: Workflow chaining** (1 min)
- Show blog post that demonstrates the chain: analysis → discussion → `/plan` decomposition → implementation → PR

> "The workflows chain together. A DailyOps workflow discovers an issue. A ChatOps workflow decomposes it. A TaskOps workflow implements it. A validation workflow checks it. Each step is a separate, composable workflow. You can use any subset."

### Transition

> "So it works at scale. Now let me show you how easy it is to create your own workflows."

---

## Segment 4: How Easy It Is to Create Workflows (10 min)

### Talking Points

This is where the audience starts thinking "I could do this." Show the simplicity.

### Live Demo Steps

**Step 1: Show the shared workflows repo** (2 min)
- Switch to [gh-aw-shared-workflows README](https://github.com/RealPage/gh-aw-shared-workflows)
- Show the two pipeline diagrams:
  - Feature Development Pipeline flow
  - Auto-Remediation Pipeline flow

> "This is our shared workflows repo. It contains six reusable workflows organized into two pipelines. Feature development — from idea to validated PR. And auto-remediation — from error log to fix PR. Consumer repos import these, they don't copy them."

**Step 2: Anatomy of a shared workflow** (3 min)
- Open `shared/prd-generation.md` in the terminal or editor

> "Let's look at what a workflow actually is."

Walk through the structure:

```
---                                    ← YAML frontmatter starts
engine: claude                         ← Which AI engine to use
on:                                    ← GitHub event triggers
  workflow_dispatch:
  issues:
    types: [opened, labeled]
safe-outputs:                          ← Allowed operations (defense-in-depth)
  - create-pull-request
  - add-comment:
      max: 3
---                                    ← Frontmatter ends

# PRD Generation                       ← Natural language instructions begin

You are a product requirements analyst...
```

> "That's it. YAML frontmatter declares triggers, engine, permissions, and safety constraints. The body is natural language instructions. No complex pipeline DSL. No scripting language. You tell the agent what to do in plain English, and `gh aw compile` generates the Actions YAML.
>
> Compare this to writing a GitHub Actions workflow from scratch — or building a custom platform. This is a markdown file."

**Step 3: `gh aw add-wizard` — the interactive way** (3 min)
- In terminal, inside a consumer repo (e.g., `lumina-agents-mcp`), run:

```bash
gh aw add-wizard
```

> "RADD has a great 3-step wizard — choose trigger, configure actions, review and activate. gh-aw has its own version. Let me show you."

- Walk through the interactive prompts as they appear:
  - **Workflow name** — give it a name (e.g., "code-review")
  - **Trigger selection** — pick from issues, PRs, schedule, dispatch, etc.
  - **Engine** — choose Claude, Copilot, Codex, Gemini
  - **Safe outputs** — select which operations the agent can perform
  - **Instructions** — the wizard scaffolds the markdown file with your choices

> "It walks you through every decision — trigger, engine, permissions, safe outputs — and generates the workflow markdown file for you. For someone who's never written a gh-aw workflow before, this is the fastest path. You answer a few questions, it writes the file, you run `gh aw compile`, and you're live.
>
> Same outcome as RADD's wizard — different interface. RADD gives you a web UI. gh-aw gives you a CLI. Both get you to a working workflow in under 5 minutes."

- Show the generated `.md` file in `.github/workflows/` after the wizard completes

**Step 4: Adding a shared workflow from RealPage's library** (2 min)
- Stay in the consumer repo terminal
- Run:

```bash
gh aw add RealPage/gh-aw-shared-workflows/auto-remediation
```

> "Now let me show you the other path — pulling from a shared workflow library. We've built a set of production-ready workflows in our gh-aw-shared-workflows repo. Instead of writing from scratch, a team can pull a ready-made workflow with one command."

- Show the generated file in `.github/workflows/auto-remediation.md`

> "One command. It pulled a consumer stub with triggers, permissions, and an import pointing to our shared logic. Let me show you what it generated."

- Open the generated file — point out the structure:

```yaml
---
on:
  schedule:
    - cron: "0 * * * *"
  workflow_dispatch:
    inputs:
      service_name:
        description: "Service name to search errors for"
        required: false
      # ... more inputs

permissions:
  contents: read
  issues: read

imports:
  - RealPage/gh-aw-shared-workflows/shared/auto-remediation.md@v0.1.0
---
```

> "Triggers are included — hourly schedule and manual dispatch with configurable inputs. The `imports:` line pulls the shared logic from our org's repo, pinned to a version. The team doesn't need to understand the 150 lines of workflow logic. They configure their secrets, compile, and they're live.
>
> If we improve the shared workflow upstream — better error classification, smarter triage — every consumer gets the update when they bump the version tag."

**Step 5: The compile step** (1 min)
- In terminal, show:

```bash
gh aw compile
```

> "One command. This reads all your `.md` workflow files, resolves imports, validates safe outputs, and generates `.lock.yml` files — the actual GitHub Actions workflows. Commit those, push, and you're live."

**Step 6: Show all example stubs** (1 min)
- Open the [workflows/ directory on GitHub](https://github.com/RealPage/gh-aw-shared-workflows/tree/main/workflows)
- Quickly show that each file is the same pattern, 8-15 lines each

> "Here's our full library of consumer stubs — PRD generation, decomposition, skill selection, MCP selection, validation, auto-remediation. Each one is 8-26 lines. A team can pull any combination of these into their repo with `gh aw add` and have a working pipeline in minutes."

### Transition

> "Okay, enough showing files. Let me show you this running end-to-end."

---

## Segment 5: End-to-End SDLC Demo with lumina-agents-mcp (20 min)

### Talking Points

This is the centerpiece. Mirror what RADD demoed (bug → AI fix → PR in ~4.5 min) but show the full feature lifecycle: idea → PRD → stories → implementation → validation.

### Live Demo Steps

**Step 1: Setup — show the repo** (2 min)
- Open `lumina-agents-mcp` repo in browser
- Navigate to `.github/workflows/` directory
- Show the workflow stubs

> "This is lumina-agents-mcp — a real project, not a demo scaffold. Let me show you its workflow directory."

- Click through 2-3 workflow stubs

> "Each of these is a thin stub that imports from gh-aw-shared-workflows. The shared logic lives upstream. The consumer just declares triggers and imports."

- Open the `CLAUDE.md` file in the repo root

> "This is how the agent understands the project. Tech stack, conventions, architecture, key file paths — all in a markdown file in the repo root. No database config, no web UI. The agent reads this before every workflow run. If you want to change how the agent behaves, you edit this file."

**Step 2: File a feature idea** (2 min)
- Go to Issues → New Issue on `lumina-agents-mcp`
- Title: **"Add agent response caching with configurable TTL"**
- Body:

> ```
> ## Feature Idea
>
> Add a caching layer for agent responses to reduce latency and API costs
> for repeated or similar queries. Cache should support:
>
> - Configurable TTL per agent type
> - Cache invalidation on agent configuration changes
> - Redis backend for distributed deployments
> - In-memory fallback for single-node setups
> - Cache hit/miss metrics exposed via existing observability
> ```

- Add the `feature-idea` label
- Submit

> "I'm filing a feature idea — just like a PM or tech lead would. The `feature-idea` label is the trigger. Watch what happens."

**Step 3: Show PRD Generation running + `gh aw status`** (3 min)
- Navigate to Actions tab → show the PRD Generation workflow running
- Click into the running workflow

> "The workflow triggered automatically. The agent is reading the issue, reading the project's CLAUDE.md for architectural context, reading the PRD template, and generating a comprehensive PRD."

- **Switch to terminal** and run:

```bash
gh aw status
```

> "Instead of watching the Actions UI, I can check status from my terminal. `gh aw status` shows every active and recent workflow run — which workflows are running, which are queued, which just finished. This is your quick pulse check without leaving the command line."

- While waiting, explain what's happening:

> "It's filling in the PRD template — problem statement, user stories, functional requirements prioritized as P0/P1/P2, technical considerations, acceptance criteria, test strategy. The same structured thinking a senior engineer would do, but automated.
>
> You showed bug → AI fix → PR in about 4.5 minutes with RADD. Here's the first stage of feature idea → PRD → stories → implementation → validation. Same velocity, broader scope."

- **If the run completes in time:** Show the generated PR with the PRD document. Walk through the sections.
- **If it's still running:** Switch to the pre-completed backup. "Here's one I prepared earlier — let me show you the output."

Show the generated PRD:
> "Look at this — problem statement, four user stories, P0/P1/P2 requirements, technical considerations calling out Redis integration and cache invalidation strategies, acceptance criteria checklist, test strategy. This is a real PRD. A human PM would review and refine this, but the heavy lifting is done."

**Step 4: Merge and fan-out** (3 min)
- Merge the PRD PR (or show the pre-completed merge)
- Navigate to Actions tab — show three workflows triggering simultaneously:
  1. **Decomposition** — creating epic + stories
  2. **Skill Selection** — fetching relevant coding skills
  3. **MCP Selection** — configuring data sources

> "Merging the PRD triggers three workflows in parallel. This is the fan-out. Decomposition breaks the PRD into an epic and prioritized stories. Skill selection fetches relevant coding skills from our ai-coding-toolkit — things like `python-project`, `api-design`, `elk-logging`. MCP selection configures which external tools the implementation agent will have access to — maybe BigQuery for schema validation, Brave Search for API docs."

- Show the Issues tab with the created epic and stories
- Show story issues with priority labels (`priority:critical`, `priority:high`, `priority:low`)

> "The decomposition created an epic issue and individual story issues, each prioritized based on the PRD requirements. P0 items are labeled `priority:critical` and `ready-for-implementation`. The agent understood the dependency graph — it only marks stories as ready when their dependencies are met."

**Step 5: Implementation** (5 min)
- Show a story issue that has the `ready-for-implementation` label
- Navigate to Actions → show the implementation workflow running (or show pre-completed)

> "When a story is labeled `ready-for-implementation`, the implementation agent picks it up. It reads the story, reads the PRD for full context, reads the CLAUDE.md for project conventions, and has access to whatever MCP tools were configured — maybe BigQuery for checking schemas, maybe Brave Search for looking up Redis client library docs."

- Show the implementation PR

> "Here's the PR. Code changes, tests, the whole thing. The agent wrote implementation code following the project's existing patterns, added unit tests, and opened a PR referencing the story issue."

- **Switch to terminal** and run:

```bash
gh aw logs
```

> "Now let me show you what the agent actually did. `gh aw logs` streams the agent's reasoning and actions from the most recent run. You can see every file it read, every decision it made, every tool it called. This is your debugging and review tool — if a PR looks wrong, you come here to understand why."

- Scroll through briefly to show the agent's reasoning steps

> "This is full transparency. No black box. The agent's entire thought process is logged and accessible from your terminal."

**Step 6: Validation** (3 min)
- Add the `needs-validation` label to the implementation PR
- Navigate to Actions → show validation workflow running (or show pre-completed)

> "Now I add the `needs-validation` label. A separate validation agent — completely independent from the one that wrote the code — reads the PR, traces back to the story and the original PRD, and validates the implementation against the acceptance criteria."

- Show the validation comment on the PR:

> "Look at this validation report. It's a checklist — each acceptance criterion from the PRD with a pass/fail. Summary, gaps identified, overall recommendation. This is your automated code review against the spec.
>
> The full pipeline: feature idea → PRD → decomposed stories → implementation → validated PR. All through GitHub-native triggers — issues, labels, PR events. No external platform, no webhook infrastructure, no custom UI."

**Step 7: Recap the pipeline** (2 min)

> "Let me zoom out. You showed bug → AI fix → PR in 4.5 minutes. Here's what gh-aw does for the full feature lifecycle:"

Draw the flow verbally:

```
Feature idea (issue + label)
    → PRD Generation (agent writes PRD, opens PR)
        → [merge PRD]
            → Decomposition (epic + prioritized stories)
            → Skill Selection (coding skills for the agent)
            → MCP Selection (data sources for the agent)
                → Implementation (agent writes code + tests, opens PR)
                    → Validation (separate agent checks against PRD)
```

> "Every artifact is visible in GitHub. PRD is a PR. Stories are issues. Implementation is a PR. Validation is a comment. Your entire audit trail is native GitHub. No external system to check, no dashboard to maintain."

### Transition

> "That covers new feature development. But what about the ops side — what about when things break in production? You showed this beautifully with RADD's Sentry integration. Let me show you how gh-aw handles it."

---

## Segment 6: Converting Auto-Remediation to gh-aw (5 min)

### Talking Points

Bridge directly from RADD's Sentry pipeline. Be explicit about the parallel.

### Live Demo Steps

**Step 1: Open the auto-remediation workflow** (2 min)
- Open `shared/auto-remediation.md` in terminal or editor
- Walk through the five stages:

> "You built a custom pipeline to go from Sentry alert to AI fix to PR. Here's gh-aw's equivalent."

Walk through each stage:

> "**Stage 1: Error Discovery.** The agent queries Elastic via MCP — `log.level == 'ERROR'` for the configured service, grouped by error type, deduplicated, sorted by frequency. Top 5 by default.
>
> **Stage 2: Triage & Root Cause Analysis.** Each error gets classified — category, severity, confidence level, suggested fix, code location. The agent does the same analysis a senior engineer would do when triaging a production issue.
>
> **Stage 3: Issue Creation.** Deduplication check first — if an issue already exists, it adds a comment instead of creating a duplicate. New issues get severity labels, error category labels, and the full analysis in the body.
>
> **Stage 4: Implementation.** Here's where the confidence gating matters. Only high and medium confidence fixes get auto-implemented. Low confidence? Issue only — flagged for a human. Security-sensitive code? Issue only — flagged for a human. The agent reads your CLAUDE.md, reads the source file, implements a minimal fix, adds tests if a test file exists, and opens a PR.
>
> **Stage 5: Summary.** A workflow summary with everything that happened — errors discovered, issues created, PRs opened, duplicates skipped."

**Step 2: Show the consumer stub** (1 min)
- Open `workflows/auto-remediation.md`

> "Here's all a team needs to add to their repo — 26 lines. Declares the hourly schedule trigger, the manual dispatch inputs for overrides and dry-run mode, and the import. That's it. Add this file, set three secrets — `SERVICE_NAME`, `ELASTIC_MCP_URL`, `ELASTIC_MCP_API_KEY` — run `gh aw compile`, and your repo has automated error remediation."

**Step 3: Swapping Elastic for Sentry** (1 min)

> "You use Sentry. This workflow uses Elastic. The swap is straightforward — you'd replace the Elastic MCP server with a Sentry MCP server in the `mcp-servers:` block and adjust the query instructions. The pattern is identical: discover errors, triage, fix, PR. The data source is pluggable."

- Point to the `mcp-servers:` section in the frontmatter

> "MCP servers are configured right here in the frontmatter. Swap Elastic for Sentry, recompile, done. You could even run both — Elastic for infrastructure logs, Sentry for application errors."

**Step 4: `gh aw audit` — the audit trail** (1 min)
- In terminal, run:

```bash
gh aw audit
```

> "This is the one your security and governance teams will love. `gh aw audit` shows every action every agent has taken across your repo — issues created, PRs opened, labels applied, comments posted. Every safe output execution, timestamped, with the workflow that triggered it.
>
> RADD gives you this through your dashboard. gh-aw gives you this from the CLI, backed by GitHub's own audit infrastructure. For compliance, you have a complete record of what agents changed, when, and why — all queryable from the terminal."

- Show the output briefly — point out the structured format (action type, timestamp, workflow name)

**Step 5: The key comparison** (1 min)

> "You built a custom platform to do this — and it works great. With gh-aw, a team gets the same capability by dropping a 26-line markdown file into their repo, pointing it at their observability stack, and running `gh aw compile`. The pattern is the same. The trade-off is: custom platform with full control versus zero-infrastructure GitHub-native with community momentum."

### Transition

> "This brings me to the bigger point about how teams would actually adopt this."

---

## Segment 7: Flexibility & Non-Prescribed Process (3 min)

### Talking Points

Reinforce the lego-block philosophy. Show this audience they wouldn't be locked into one way of working.

### Live Demo Steps

**Step 1: Recap the pattern catalog** (1 min)
- No new screen — reference the patterns page from Segment 2

> "Remember those design patterns — IssueOps, LabelOps, DailyOps, ChatOps, TaskOps? Those are the building blocks. Here's how different teams might compose them."

**Step 2: Show team composition examples** (2 min)

> "**Team A** — small, fast-moving. They use PRD generation and implementation only. Idea → PRD → code. Lightweight, minimal ceremony.
>
> **Team B** — regulated, quality-focused. They use the full pipeline with validation. Idea → PRD → stories → implementation → validation. Every change traced back to requirements.
>
> **Team C** — ops-focused. They don't care about feature development workflows. They only use auto-remediation. Production errors get automatically triaged and fixed.
>
> **Team D** — domain specialists. They build custom workflows using the same patterns for their specific needs. Maybe a DailyOps workflow that scans for dependency vulnerabilities. Maybe a ChatOps workflow that lets developers type `/deploy staging` in a PR comment.
>
> gh-aw doesn't tell you how to develop software. It gives you building blocks. Your teams compose what fits their process. And because it's all markdown files in Git, it's auditable, reviewable, and version-controlled. Your governance team can review workflow changes the same way they review code changes — through PRs."

### Transition

> "Let me wrap up with how I see these two platforms fitting together."

---

## Segment 8: Q&A and Closing (2 min)

### Talking Points

> "To bring it home: **RADD is great for your Azure DevOps teams. gh-aw is great for your GitHub teams. Together, you cover your entire engineering org.**
>
> For any team on GitHub today, the starting point is one workflow. Maybe auto-remediation — drop in a markdown file, point it at Elastic or Sentry, and let it run. Maybe PRD generation — turn messy feature requests into structured requirements automatically. Start small, grow from there. No platform to deploy, no infrastructure to maintain.
>
> The community behind this is moving fast. 3,700+ stars on the gh-aw repo. 275 releases. Peli's Agent Factory with 100+ workflows and real production metrics. A 19-part blog series documenting everything. GitHub is investing heavily in this as a core platform capability.
>
> Here are the resources:"

**Share links:**
- [gh-aw Documentation](https://github.github.com/gh-aw/)
- [github/gh-aw Repository](https://github.com/github/gh-aw) (3.7k stars, MIT license)
- [gh-aw-shared-workflows](https://github.com/RealPage/gh-aw-shared-workflows) (our shared workflows)
- [Agentics Template](https://github.com/githubnext/agentics-template) (starter template)
- [Agentics Sample Pack](https://github.com/githubnext/agentics) (50+ workflows)
- [Agent Factory Blog Series](https://github.github.com/gh-aw/blog/2026-01-12-welcome-to-pelis-agent-factory/)
- [GitHub Blog Announcement](https://github.blog/changelog/2026-02-13-github-agentic-workflows-are-now-in-technical-preview/)

> "I'm happy to take questions."

---

## Anticipated Q&A

### "How does this compare to RADD's observability?"

> "RADD has a purpose-built dashboard — run status, metrics, MCP server health. That's a real advantage of a custom platform. gh-aw uses GitHub Actions as its observability layer — run logs, workflow summaries, PR comments. It's not as rich as a dedicated dashboard, but it's zero additional infrastructure. For deeper observability, you'd use the Metrics Collector pattern — there's a DailyOps workflow in Peli's factory that aggregates metrics into discussions. You could also pipe data into DataDog or your existing observability stack via MCP."

### "What about Slack notifications?"

> "gh-aw supports Slack via MCP server. You'd add a Slack MCP server to your workflow frontmatter and include an instruction like 'post a summary to #engineering-alerts when the workflow completes.' RADD has this built in with IoT-maton. In gh-aw it's a configuration addition, not a built-in feature — the trade-off of composability over opinionated defaults."

### "What's the cost model?"

> "gh-aw runs on GitHub Actions — you're using your existing Actions minutes. The AI engine cost depends on which engine you choose. Claude, Codex, Gemini — you bring your own API key. Copilot uses your existing GitHub Copilot license. There's no separate gh-aw licensing cost."

### "How do we handle secrets and sensitive operations?"

> "Three layers. First, safe outputs constrain what the agent can do — rate-limited, allowlisted operations only. Second, the agent never holds tokens directly — API-proxy holds authentication outside the agent container. Third, all files are scanned for secrets before artifact upload. For security-sensitive code paths, the auto-remediation workflow explicitly creates an issue instead of auto-fixing — flagged for human implementation."

### "Can we use this with Azure DevOps?"

> "gh-aw is GitHub-native. It needs GitHub Actions as the execution substrate and GitHub issues/PRs as the collaboration layer. For Azure DevOps workflows, RADD is the right tool. The complementary model is: RADD for Azure DevOps repos, gh-aw for GitHub repos. If teams migrate to GitHub, they get gh-aw capability natively."

### "What about XPIA / prompt injection on public repos?"

> "Lockdown mode. For public repos, the GitHub MCP server only surfaces items from users with push access — blocks untrusted content from reaching the agent. Pre-activation sanitization neutralizes @mentions, converts HTML/XML tags, filters URIs. There's a separate threat detection pipeline that analyzes buffered artifacts for suspicious content. Token isolation keeps API keys outside the agent container entirely."

### "How mature is this? Can we bet on it?"

> "Tech preview since February 2026. 275 releases — that's roughly daily releases. 3,700+ stars. GitHub Next and Microsoft Research are backing it. Peli's Agent Factory has been running 100+ workflows in production for months with measurable results. Is it GA? No. But the velocity of development and the investment from GitHub suggest this is going to be a core platform capability, not a side project."

---

## Timing Guide

| Segment | Duration | Cumulative |
|---------|----------|------------|
| 1. Opening & Framing | 5 min | 0:05 |
| 2. gh-aw Overview | 10 min | 0:15 |
| 3. Agent Factory | 5 min | 0:20 |
| 4. Creating Workflows | 10 min | 0:30 |
| 5. End-to-End SDLC Demo | 20 min | 0:50 |
| 6. Auto-Remediation | 5 min | 0:55 |
| 7. Flexibility | 3 min | 0:58 |
| 8. Q&A and Closing | 2 min | 1:00 |

**Buffer:** Segments 2-4 can each be trimmed by 2 min if the live demo in Segment 5 runs long. Segment 5 has a built-in backup plan (pre-completed run).

---

## Backup Plan: If Live Demos Take Too Long

Agent runs typically take 2-5 minutes each. The full pipeline in Segment 5 involves multiple runs.

**Strategy:**
1. **Trigger the feature idea live** — file the issue, show the workflow start. This takes seconds.
2. **Switch to pre-completed run** — "Here's one I prepared earlier." Walk through the artifacts: PRD PR, decomposed issues with priority labels, implementation PR, validation comment.
3. **Check back on the live run** — if it finishes during a later segment, show it briefly: "And our live run just completed — same results."

**Pre-complete before the demo:**
- Run the full pipeline on `lumina-agents-mcp` with a test feature idea
- Screenshot or bookmark: PRD PR, epic issue, story issues, implementation PR, validation comment
- Keep the browser tabs open for quick switching

---

## Key Phrases to Rehearse

These are the sound bites that stick. Practice saying them naturally.

1. "You've already proven this model works. gh-aw is GitHub's answer for teams living in the GitHub ecosystem."
2. "What if your GitHub repos could do this natively, with no custom platform to build or maintain?"
3. "Workflows are markdown files, not complex YAML pipelines."
4. "One line to swap engines. No vendor lock-in."
5. "The agent never directly touches your repo. It proposes. A validated, rate-limited job acts."
6. "514 merged PRs. 96% merge rate on docs. This isn't a proof of concept."
7. "You have a great wizard. gh-aw's equivalent is a markdown file and `gh aw compile`."
8. "26 lines. That's all a team needs to add automated error remediation."
9. "RADD for Azure DevOps. gh-aw for GitHub. Together, full coverage."
10. "gh-aw doesn't tell you how to develop software. It gives you building blocks."

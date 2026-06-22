# Claude Code Prompt: gh-aw Demo Preparation (1 Hour)

Copy everything below the line into a new Claude Code session.

---

## Context

I'm preparing a **1-hour demo** of [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/) for an audience of **senior engineers who have built their own agentic development platform** called STRATIS BORG. STRATIS BORG is an AI-powered SDLC automation platform that orchestrates Azure DevOps work items through AI coding agents to generate PRs, with Slack notifications and full observability. It's a polished, production system — this audience knows agentic development deeply.

**The tone must be non-competitive and complimentary.** STRATIS BORG is impressive engineering. gh-aw is not a replacement — it is a **complementary platform that is optimal for teams already on GitHub**. The pitch is:
- Teams already on GitHub get agentic workflows with zero custom infrastructure
- Teams NOT on GitHub have an incentive to migrate because gh-aw gives them this capability natively
- STRATIS BORG and gh-aw can coexist — STRATIS BORG handles Azure DevOps workflows, gh-aw handles GitHub-native workflows
- gh-aw's open ecosystem and GitHub backing mean fast community growth and long-term investment

## What I Need

Help me build a structured, rehearsable **1-hour demo** with the following segments. For each segment, provide:
1. **Talking points** — what to say, framed for this audience
2. **Live demo steps** — exact actions to perform on screen
3. **Transition script** — how to bridge to the next segment naturally

## Demo Segments

### Segment 1: Opening & Framing (5 min)

- Acknowledge STRATIS BORG as strong prior art — "you've already proven this model works"
- Frame gh-aw as GitHub's answer for teams living in the GitHub ecosystem
- Key message: "What if your GitHub repos could do this natively, with no custom platform to build or maintain?"
- Briefly mention gh-aw is built by **GitHub Next & Microsoft Research** (Peli de Halleux, Don Syme, et al.)
- Note the **fast community growth**: 100+ workflows in Peli's Agent Factory, 19-part blog series, active open-source development

### Segment 2: gh-aw Overview — Review the Docs (10 min)

- Walk through the [gh-aw documentation site](https://github.github.com/gh-aw/) live
- Review the **README** and highlight the **Related Projects** section showing the ecosystem
- Show how workflows are just **markdown files with YAML frontmatter** — not complex YAML pipelines
- Highlight key architectural concepts:
  - **Engine flexibility**: Copilot, Claude, Codex, Gemini — swap with one line
  - **MCP tool integration**: GitHub tools, Elastic, Brave Search, custom MCP servers
  - **Safe outputs**: rate-limited, allowlisted operations (defense-in-depth security)
  - **Lockdown mode**: XPIA protection for public repos
- Show the **design patterns as lego blocks** — the named operational patterns that let teams compose without being prescribed a process:
  - IssueOps, LabelOps, DailyOps, ChatOps, DispatchOps
  - TaskOps (research → review → implement), MemoryOps (stateful agents)
  - MultiRepoOps, SideRepoOps, ProjectOps
  - Emphasize: "These are composable building blocks. Your team picks the patterns that match how they already work. gh-aw doesn't force a prescribed process."

### Segment 3: Peli's Agent Factory — Proof at Scale (5 min)

- Show the [Agent Factory blog series](https://github.github.com/gh-aw/blog/) and results
- Highlight production metrics: Plan Command (514 merged PRs, 67% merge rate), Documentation Updater (96% merge rate), Semantic Refactor (79% merge rate)
- Frame these as **agent workflows you can drop right into your environment** — not demos, production-proven patterns
- Show how workflows chain: analysis → discussion → `/plan` decomposition → implementation → PR
- Key message: "This isn't a proof of concept. This is 100+ workflows running in production with measurable results."

### Segment 4: How Easy It Is to Create Workflows (10 min)

- Live demo using the [agentics](https://github.com/RealPage/agentic-workflows) repo
- Show the repo README with the Feature Development Pipeline and Auto-Remediation Pipeline diagrams
- Walk through creating a workflow from scratch:
  1. Create a markdown file in `.github/workflows/`
  2. Add YAML frontmatter (trigger, permissions, engine, tools, safe-outputs)
  3. Write natural language instructions in the body
  4. Run `gh aw compile` to generate the lockfile
  5. Commit and push — it's live
- Show the **import/composition model**: how consumer repos create thin stubs that import shared logic:
  ```yaml
  imports:
    - RealPage/agentic-workflows/workflows/prd-generation.md@v0.1.0
  ```
- Compare to STRATIS BORG's 3-step wizard: "You have a great wizard. gh-aw's equivalent is a markdown file and `gh aw compile`. Different approach, same outcome — making it dead simple to stand up a workflow."
- Run `gh aw add-wizard RealPage/agentic-workflows/workflows/prd-generation.md` live — show the wizard generating the consumer stub automatically

### Segment 5: End-to-End SDLC Demo with lumina-agents-mcp (20 min)

This is the centerpiece. Use the [lumina-agents-mcp](https://github.com/RealPage/lumina-agents-mcp) project to show a full product requirement to PR pipeline — mirroring what STRATIS BORG demoed with their Azure DevOps bug-fix flow, but driven entirely through GitHub.

**Setup**: Have the lumina-agents-mcp repo open. Show its `.github/workflows/` directory with the workflow stubs that import from agentics.

**Live demo flow**:
1. **Create a feature idea** — file a GitHub issue on lumina-agents-mcp with the `feature-idea` label (e.g., "Add agent response caching with configurable TTL")
2. **PRD Generation triggers** — show the workflow running in GitHub Actions. Walk through the agent reading the issue, filling the PRD template, and opening a PR with a full PRD document
3. **Merge the PRD** — merge the PRD PR to trigger the parallel fan-out:
   - **Decomposition** creates an epic + prioritized stories as GitHub Issues
   - **Skill Selection** fetches relevant coding skills from ai-coding-toolkit
   - **MCP Selection** configures data sources for the implementation agent
4. **Implementation** — label a story `ready-for-implementation` and show the agent writing code, running tests, and opening a PR
5. **Validation** — label the PR `needs-validation` and show the validation agent checking code against PRD acceptance criteria

**Talking points during the demo**:
- Draw parallel to STRATIS BORG: "You showed bug → AI fix → PR in ~4.5 minutes. Here's feature idea → PRD → stories → implementation → validation, all through GitHub native triggers."
- Point out the PRs and issues generated by the pipeline as visible artifacts
- Show the CLAUDE.md file — "This is how the agent understands your project. No database config, no web UI — it's a markdown file in your repo."
- Show the workflow stubs — "Each of these is 10-15 lines. The shared logic lives in agentics and gets imported."

### Segment 6: Converting Auto-Remediation to gh-aw (5 min)

- Bridge from STRATIS BORG's Sentry-triggered bug fix pipeline to gh-aw's auto-remediation workflow
- Open `workflows/auto-remediation.md` from agentics and walk through the 5 stages:
  1. Error Discovery (queries Elastic via MCP)
  2. Triage & Root Cause Analysis
  3. Issue Creation (deduplication, severity labels)
  4. Implementation (confidence-gated — only fixes high/medium confidence)
  5. Summary
- Describe the consumer stub: "All a team adds to their repo is a ~20-line markdown file that declares the schedule trigger and imports the shared workflow. The `gh aw add-wizard` command generates it for them. The shared workflow handles the logic."
- Key message: "You built a custom platform to do this with Sentry. With gh-aw, a team can add this capability to any GitHub repo by dropping in a 26-line markdown file, pointing it at their Elastic instance, and running `gh aw compile`. The pattern is the same — discover errors, triage, fix, PR — but it runs on GitHub Actions with no custom infrastructure."
- Show how easy it would be to swap Elastic for Sentry by adding a Sentry MCP server in the `mcp-servers:` block

### Segment 7: Flexibility & Non-Prescribed Process (3 min)

- Recap the lego-block design philosophy
- Show concrete examples of flexibility:
  - Team A uses only PRD generation + implementation (lightweight)
  - Team B uses the full pipeline with validation (rigorous)
  - Team C only uses auto-remediation (ops-focused)
  - Team D builds custom workflows for their domain using the same patterns
- "gh-aw doesn't tell you how to develop software. It gives you building blocks. Your teams compose what fits their process."

### Segment 8: Q&A and Closing (2 min)

- Reiterate complementary positioning: "STRATIS BORG is great for your Azure DevOps teams. gh-aw is great for your GitHub teams. Together, you cover your entire engineering org."
- Call to action: "For any team on GitHub today, they can start with one workflow — maybe auto-remediation or PRD generation — and grow from there. No platform to deploy, no infrastructure to maintain."
- Share resources: gh-aw docs, RealPage/agentic-workflows repo, githubnext/agentics upstream library, Agent Factory blog series

## Key Constraints

- **Never disparage STRATIS BORG.** Always acknowledge it as proven, impressive engineering.
- **Focus on GitHub-native advantage**, not feature comparison. The value prop is: "If you're on GitHub, this is built for you."
- **Show, don't tell.** Every claim should have a live demo backing it up.
- **Keep it practical.** This audience builds production systems — they want to see real workflows, real PRs, real pipeline runs, not slides.
- **Respect the time.** 1 hour including Q&A. Each segment should be tight and rehearsable.

## Preparation Checklist

Before the demo, ensure:
- [ ] `gh aw` CLI is installed and authenticated
- [ ] lumina-agents-mcp repo is accessible and has workflows compiled
- [ ] agentics repo is up to date
- [ ] A draft feature idea issue is ready to file on lumina-agents-mcp
- [ ] GitHub Actions is enabled and WIF auth is configured on lumina-agents-mcp (`ANTHROPIC_FEDERATION_RULE_ID` + `ANTHROPIC_SERVICE_ACCOUNT_ID` vars; RealPage org default inherited — see docs/wif-auth.md)
- [ ] Browser tabs pre-loaded: gh-aw docs site, gh-aw blog, agentics README, lumina-agents-mcp repo
- [ ] Elastic MCP endpoint is configured (for auto-remediation segment if showing live)
- [ ] Have a pre-recorded or pre-completed run as backup for the live SDLC demo (agent runs take minutes — have one ready to show results while the live one runs)

## Backup Plan

If live demo timing is tight (agent runs take 2-5 minutes each):
- Have a **pre-completed run** on lumina-agents-mcp showing the full pipeline artifacts (PRD PR, decomposed issues, implementation PR, validation comment)
- Show the live trigger, then switch to "here's one I prepared earlier" to walk through results
- The auto-remediation segment can use the workflow file walkthrough without a live run — the architecture speaks for itself

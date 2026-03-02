# gh-aw Demo — Backup Slides for Q&A

Pull these up when the audience pushes back. Each slide is self-contained.
Designed for a senior engineering audience that builds production platforms.

---

## Slide 1: "But It's Technical Preview..."

### The Label vs. The Reality

| What "tech preview" implies | What's actually happening |
|-----------------------------|--------------------------|
| Might disappear | 275 releases (~daily shipping) |
| Unstable / broken | 100+ workflows running in prod on gh-aw's own repo |
| Small experiment | 3,700+ stars, 268 forks, MIT licensed |
| Unknown team | Peli de Halleux (Microsoft Research), Don Syme (F# creator), GitHub Next |
| No production use | 514 merged PRs from Plan Command alone (67% merge rate) |

### What "tech preview" actually means here

- API surface may evolve (frontmatter schema, CLI flags)
- Not yet covered by GitHub's SLA/support contracts
- Feature set still expanding

### Why that's acceptable risk

- **Version pinning** — imports lock to `@v0.1.0`. Breaking changes don't propagate until you choose to upgrade.
- **No proprietary runtime** — workflows compile to standard GitHub Actions YAML. Worst case: stop compiling, keep running what you have.
- **MIT licensed** — you own the code. No vendor can pull it away.
- **Markdown files in Git** — your workflows are just files in your repo. Nothing to migrate off of.

### The honest line

> "Tech preview means the API might change. It doesn't mean this might disappear. GitHub is dogfooding this on their own codebase with 100+ workflows. When was the last time you saw a 'tech preview' with 275 releases and daily production use?"

---

## Slide 2: "What's Your Rollback Story?"

### If gh-aw disappears tomorrow

1. Your `.lock.yml` files are standard GitHub Actions YAML — they keep running
2. Your workflow `.md` files are documentation of what the agent does — still useful
3. Your CLAUDE.md, PRD templates, skills — all plain files in your repo, engine-agnostic
4. Zero infrastructure to decommission (no servers, no databases, no SaaS to cancel)

### If a breaking change lands

1. Imports are version-pinned: `@v0.1.0` — nothing changes until you bump
2. `gh aw compile` runs locally — you see the diff before pushing
3. Lockfiles are committed to Git — you can `git diff` any compilation change
4. Standard PR review process applies to workflow changes

### The sound bite

> "The rollback story is: stop running `gh aw compile`. Your existing compiled workflows keep running as normal GitHub Actions. There's nothing to unwind."

---

## Slide 3: "How Do We Know GitHub Is Serious About This?"

### Investment signals

| Signal | Evidence |
|--------|----------|
| **Team** | GitHub Next + Microsoft Research (not a hackathon project) |
| **People** | Peli de Halleux (GenAI research lead), Don Syme (created F#) |
| **Velocity** | 275 releases in ~2 months |
| **Dogfooding** | 100+ workflows on their own repo, 19-part blog series documenting results |
| **Ecosystem** | Firewall (AWF), MCP Gateway, Agentics sample pack (50+ workflows), starter template |
| **Blog coverage** | Official GitHub blog announcement, GitHub Changelog entry |
| **Community** | 3,700+ stars, 268 forks, active open-source development |
| **Architecture** | Built on GitHub Actions — extending a core platform, not bolting on a side feature |

### Strategic context

- GitHub Copilot moved from code completion → Workspace → Agents. gh-aw is the workflow automation layer.
- Microsoft is betting on AI-native development. gh-aw is how that bet manifests in CI/CD.
- Built on Actions — GitHub's most widely adopted automation platform. They're extending it, not replacing it.

### The sound bite

> "When the person who created F# and the head of GenAI research at Microsoft are shipping daily releases, this isn't a tech preview that's going to quietly sunset."

---

## Slide 4: "Why Not Just Wait for GA?"

### What you lose by waiting

- **Time** — teams on GitHub today have no agentic workflow capability. Every month without it is manual work that could be automated.
- **Learning curve** — early adoption means your teams build muscle memory before it becomes table stakes.
- **Influence** — tech preview is when feedback shapes the product. GA means the decisions are made.

### What you risk by starting now

- **Minimal** — a markdown file and a compiled YAML file per workflow. If you need to stop, you delete two files.
- **No infrastructure** — nothing to decommission, no contracts to cancel.
- **No migration** — workflows are in your repo. There's nothing external to manage.

### Suggested adoption path

```
Month 1:  One team, one workflow (auto-remediation or PRD generation)
Month 2:  Evaluate results, expand to 2-3 teams
Month 3:  Build shared workflows for your org's patterns
Ongoing:  Track gh-aw releases, bump versions as the platform matures
```

### The sound bite

> "The cost of trying is a markdown file. The cost of waiting is your GitHub teams not having what your Azure DevOps teams already have with RADD."

---

## Slide 5: "How Does Security Compare to RADD?"

### gh-aw's defense-in-depth model

```
┌─────────────────────────────────────────┐
│  Layer 1: Substrate                     │
│  GitHub Actions runner VM isolation     │
│  Container runtime boundaries           │
│  CPU/memory controls                    │
├─────────────────────────────────────────┤
│  Layer 2: Configuration                 │
│  Schema validation, action pinning      │
│  Static analysis (actionlint, zizmor)   │
│  Expression allowlisting                │
├─────────────────────────────────────────┤
│  Layer 3: Plan (Agent Boundary)         │
│  Agents run READ-ONLY                   │
│  Actions requested via structured JSON  │
│  Separate permission-controlled job     │
│  Rate-limited, allowlisted operations   │
└─────────────────────────────────────────┘
```

### Key security features

| Feature | What it does |
|---------|-------------|
| **Safe outputs** | Agent proposes, validated job acts. Max ops per run, blocked patterns, required labels. |
| **Token isolation** | API-proxy holds tokens outside agent container — agent can't exfiltrate credentials |
| **Secret scanning** | All files scanned before artifact upload, secrets redacted |
| **Lockdown mode** | Public repos: only surfaces content from users with push access |
| **XPIA protection** | Pre-activation sanitization: @mentions, HTML tags, URIs neutralized |
| **Threat detection** | Separate job analyzes artifacts for prompt injection / secret leakage |
| **Network firewall** | Agent Workflow Firewall — domain allowlists via iptables/Squid proxy |

### RADD comparison (complimentary framing)

> "RADD controls security through your custom platform — you own the entire stack. gh-aw controls security through GitHub's platform — defense-in-depth baked into the runtime. Different trust models, both valid. The question is where your team's security boundary sits."

---

## Slide 6: "What About Observability? RADD Has a Dashboard."

### What gh-aw gives you natively

| Need | gh-aw approach |
|------|---------------|
| Run status | `gh aw status` — real-time view of active/recent runs from the terminal |
| Agent reasoning | `gh aw logs` — stream the agent's full thought process, file reads, tool calls |
| Audit trail | `gh aw audit` — every agent action across the repo, timestamped, queryable |
| Workflow history | Actions tab — filterable, searchable |
| Artifacts | PRs, issues, comments — all in GitHub |
| Metrics | Workflow summary comments (auto-generated) |

### CLI observability tools (demo these live)

```bash
gh aw status    # What's running right now? What just finished?
gh aw logs      # What did the agent do? Full reasoning trace.
gh aw audit     # What has every agent changed in this repo? Complete history.
```

### What you'd add for parity with RADD

| Need | How to add it |
|------|--------------|
| Custom dashboard | DailyOps workflow → Metrics Collector (Peli's factory uses this) |
| Slack notifications | Add Slack MCP server to workflow frontmatter |
| DataDog integration | Add DataDog MCP server |
| Centralized metrics | Pipe workflow summaries to your existing observability stack |

### The honest take

> "RADD has a purpose-built dashboard — that's a real advantage of owning the full stack. gh-aw gives you `gh aw status`, `gh aw logs`, and `gh aw audit` from the CLI, plus the GitHub Actions UI. It's not a custom dashboard, but it's zero-infrastructure observability with a complete audit trail. For most teams, that plus Slack notifications covers 90% of what they need. For the other 10%, you compose in a metrics workflow."

---

## Slide 7: "We Already Have RADD. Why Do We Need This?"

### You probably don't — for Azure DevOps teams

RADD works. It's production. It's proven. Don't replace what works.

### You do — for GitHub teams

| Question | Answer |
|----------|--------|
| Do you have teams on GitHub? | gh-aw gives them agentic workflows natively |
| Are teams migrating to GitHub? | gh-aw is an incentive — they get this capability on day one |
| Do you want one platform per ecosystem? | RADD = Azure DevOps, gh-aw = GitHub |
| Do you want community momentum? | 3,700+ stars, 50+ sample workflows, active OSS development |

### Coexistence model

```
Azure DevOps repos  ──→  RADD  ──→  ADO work items, PRs, Slack
GitHub repos        ──→  gh-aw         ──→  Issues, PRs, Actions
                              ↕
                    Same patterns, different platforms
```

### The sound bite

> "This isn't 'replace RADD.' This is 'cover your GitHub teams with the same class of automation RADD gives your Azure DevOps teams.' One org, full coverage."

---

## Slide 8: "What's the Learning Curve?"

### For workflow consumers (most teams)

```bash
# Path A: Interactive wizard — answers prompts, generates the workflow file
gh aw add-wizard

# Path B: Import from shared library — one command, pulls from org's shared repo
gh aw add RealPage/gh-aw-shared-workflows/auto-remediation

# Then compile and push
gh aw compile && git push
```

**Time to first workflow:** 5 minutes.
**Skills required:** Git. That's it.

### For workflow authors (platform team)

```
1. Write markdown with YAML frontmatter          (new skill)
2. Understand safe outputs model                  (security layer)
3. Configure MCP servers                          (tool integration)
4. Design instructions for agents                 (prompt engineering)
```

**Time to proficiency:** 1-2 days with the docs and examples.
**Skills required:** Markdown, YAML, prompt engineering basics.

### For workflow architects (you)

```
1. Design shared workflow libraries               (this repo)
2. Define org-wide patterns and standards         (governance)
3. Build import/composition model                 (reuse strategy)
4. Configure per-team overrides and extensions    (flexibility)
```

**Comparable to:** What you already did building RADD's workflow creation wizard. Same thinking, different medium.

---

## Slide 9: "What Engines Do You Recommend?"

### Engine comparison for this audience

| Engine | Best for | Trade-off |
|--------|----------|-----------|
| **Copilot** | Teams already paying for GitHub Copilot. Default choice. | Tied to GitHub's model selection |
| **Claude** | Complex reasoning, long-context workflows (PRD gen, decomposition) | Separate API cost (Anthropic) |
| **Codex** | Code-heavy implementation tasks | Separate API cost (OpenAI) |
| **Gemini** | Teams with Google Cloud investment | Separate API cost (Google) |

### Our choice

> "We use Claude for all workflows in gh-aw-shared-workflows. It handles long-context tasks like PRD generation and multi-step analysis well. But the point is: **it's one line to change.** If a better model ships next quarter, you swap and recompile. No code changes, no migration."

### Swap demo

```yaml
# Before
engine: claude

# After — that's it
engine: copilot
```

---

## Quick Reference: Key Numbers

Keep these ready to cite during Q&A.

| Metric | Value |
|--------|-------|
| gh-aw GitHub stars | 3,700+ |
| gh-aw releases | 275 |
| gh-aw forks | 268 |
| Agent Factory workflows | 100+ |
| Plan Command merged PRs | 514 (67% merge rate) |
| Documentation Updater merge rate | 96% |
| Semantic Refactor merged PRs | 112 (79% merge rate) |
| Duplicate Code Detector merged PRs | 76 (79% merge rate) |
| Blog series posts | 19 |
| Agentics sample pack workflows | 50+ |
| gh-aw license | MIT |
| Tech preview date | February 2026 |
| Consumer workflow stub size | 8-26 lines |
| Time to first workflow | ~5 minutes |

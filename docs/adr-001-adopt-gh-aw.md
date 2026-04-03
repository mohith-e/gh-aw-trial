# ADR-001: Adopt GitHub Agentic Workflows for SDLC Automation

**Status:** Proposed
**Date:** 2026-03-13
**Context:** [Issue #19](https://github.com/RealPage/agentic-workflows/issues/19)

## Decision

Use GitHub Agentic Workflows (gh aw) as the shared platform for AI-powered SDLC automation rather than building or maintaining standalone tools.

## Why

1. **Zero new infrastructure.** Runs on existing GitHub Actions runners. No servers to provision or maintain.
2. **GitHub is the strategic direction.** IT has identified GitHub as the preferred platform. Microsoft's investment (Copilot, Actions, gh CLI) is clearly focused on GitHub, while TFS/Azure DevOps is in maintenance mode.
3. **Purpose-built agentic security.** gh aw provides a [three-layer security architecture](https://github.github.com/gh-aw/introduction/architecture/) designed specifically for AI agents: network-isolated containers with domain allowlists, permission separation (agents never get write access — all writes go through validated SafeOutput jobs), content sanitization, secret redaction, and an independent threat detection pipeline that blocks output if it finds malicious patches or leaked credentials. Building this ourselves would be a massive undertaking; extending gh aw's model over time is far safer.
4. **Free improvements.** Building on a shared platform means we automatically benefit from gh aw enhancements without additional investment.
5. **Shared workflow library.** Reusable markdown-based workflow definitions that any repo can import. One improvement benefits every consumer.
6. **Low barrier to entry.** Users interact through issue forms and PR reviews — no prompt engineering, CLI, or IDE setup required.

## Risks

- **TFS migration dependency.** Teams still on TFS need a migration path before they can fully adopt gh aw.
- **Coverage gaps.** Current workflows focus on code-level automation. Test environment orchestration, test data management, and non-functional testing need future workflow definitions.
- **Framework diversity.** Teams use varied frameworks and languages. Workflow instructions must be configurable per project.

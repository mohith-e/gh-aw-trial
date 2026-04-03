# FAQ: GitHub Agentic Workflows Adoption

## Why GitHub when most of our repos are on TFS?

IT has identified GitHub as the preferred platform going forward. TFS (Azure DevOps) and GitHub are both Microsoft, but Microsoft's investment is clearly on GitHub — Copilot, Actions, and the gh CLI all live there. TFS is in maintenance mode. Migration was already planned; gh aw strengthens the case. We're working with teams on transition planning.

## How does a workflow agent understand the codebase?

Agentic workflows run as GitHub Actions with a full repo checkout. The agent has complete access to the codebase plus project context from `CLAUDE.md`. This is different from Copilot Chat, which has lighter repo access. Both tools are complementary: Chat for discovery, Actions workflows for heavy processing.

## Won't less technical team members struggle without a UI?

Users interact through GitHub issue forms (fill in a form, submit) and PR reviews (read and approve). No prompt engineering or CLI needed. Issue templates and label-driven automation act as guardrails — users fill forms, agents do the work, humans review output.

## Do we need new infrastructure?

No. gh aw runs on existing GitHub Actions runners. No servers to stand up or maintain.

## What about security?

gh aw has a [purpose-built security architecture](https://github.github.com/gh-aw/introduction/architecture/) for AI agents. Agents run in network-isolated containers with domain allowlists. They never get write permissions — all writes (creating issues, opening PRs) go through separate validated jobs via SafeOutputs. Content is sanitized before agents see it, secrets are automatically redacted from output, and an independent threat detection pipeline blocks results if it finds anything malicious. This is far beyond what we could reasonably build and maintain ourselves.

## How does this handle test environments and test data?

Current workflows focus on code-level automation. Test environment orchestration and test data management are areas to explore. Agents can be extended with MCP servers for environment management.

## What about non-functional testing?

Current workflows cover functional validation and code-level checks. The platform is extensible — new workflow definitions can target performance, security, or accessibility testing.

## What about existing test frameworks?

Agentic workflows complement existing frameworks, they don't replace them. Implementation agents generate tests using whatever framework the project specifies in its `CLAUDE.md`.

## How do we track quality metrics and reporting?

GitHub provides native reporting via PR checks and Actions summaries. The validation workflow posts structured checklists on PRs. There's room for a dedicated reporting workflow.

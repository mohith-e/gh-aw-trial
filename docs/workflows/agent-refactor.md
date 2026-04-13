# agent-refactor

Developer-directed, behavior-preserving refactor agent. One run, one area, one PR. Three modes dictate the scope:

- **Targeted** — label an issue whose body names a path, module, or symbol → the agent refactors that area.
- **Sweep** — label an issue with no named area → the agent picks the single highest-value area based on smell-to-risk ratio.
- **PR** — label an open PR `agent:refactor` → the agent refactors code touched by the PR's diff.

## Getting Started

**From your terminal** (recommended — guided setup for engine, secrets, and PR creation):

```bash
gh aw add-wizard RealPage/agentics/agent-refactor
```

**From Claude Code or any non-interactive shell** (`add-wizard` requires a TTY, so use the non-interactive `add`):

```bash
gh aw add RealPage/agentics/agent-refactor
```

Then label an issue or PR `agent:refactor` and the agent will start a run.

## Scope Limits

| Mode | File cap | Line-change guideline |
|------|----------|----------------------|
| Targeted | 1–3 files or a single module | ~500 changed lines |
| Sweep | Same as Targeted | ~500 changed lines |
| PR | Files the PR touches (max ~5 files) | ~300 changed lines |

If the area exceeds these limits, the agent narrows to the most-changed or most-smelly slice and documents what it excluded in the plan comment.

## Guarantees

- **Behavior preservation is the primary invariant.** Tests run after every incremental step. No API changes, no dependency changes, no new features.
- **No drive-by edits.** Only the scoped area is touched. Unrelated code, untouched lines, and files outside scope are off-limits.
- **Incremental commits.** One refactor step per commit, so reviewers can follow the history.
- **Red-baseline gate.** If the test suite is already failing before the agent starts, it aborts and comments explaining that the baseline must be green first.

## Limitations

- **Fail-stops on first test failure.** If one step fails, the remaining steps are abandoned even if they are independent. This is deliberate — a failed step may indicate an incorrect mental model of the code. The PR description documents which steps were skipped.
- **Does not cross module boundaries in a single run.** Each run refactors one area. If you want multiple areas refactored, trigger multiple runs.
- **Ambiguous scope blocks the run.** In Targeted mode, if the named area is ambiguous (e.g., "the auth code" maps to four modules), the agent asks for clarification rather than guessing.

## When to Use Which Mode

| Situation | Mode | How to trigger |
|-----------|------|---------------|
| "Clean up the billing validators" | Targeted | Open an issue naming the area, label `agent:refactor` |
| "Find something worth refactoring" | Sweep | Open an issue with no specific area named, label `agent:refactor` |
| "While this PR is open, clean up what it touches" | PR | Label the open PR `agent:refactor` |

## Requirements

| Requirement | Why |
|---|---|
| Labels: `agent:refactor`, `agent:needs-clarification` | Trigger and clarification flow |
| Test command discoverable | Agent must be able to verify behavior preservation after each step |
| Green baseline | Agent aborts if the test suite is already red |

---
on: issues

permissions:
  contents: read
  issues: read
  id-token: write   # required for WIF keyless auth

engine:
  id: claude
  auth:
    type: github-oidc
    provider: anthropic
    federation-rule-id: ${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}
    # organization-id is the RealPage Anthropic org UUID — same for every GitHub org
    organization-id: cb16d48f-b95b-4b2c-9e86-a09f46eccb90
    service-account-id: ${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}
    workspace-id: wrkspc_011kuRkDngP7B49bQc5AZLVJ

safe-outputs:
  create-issue:
    max: 30
  add-labels:

---

# Story Decomposition

When a user story issue is labeled `ready-for-decomposition`, decompose it into implementation sub-issues as GitHub Issues.

## Instructions

1. Read the user story issue title, body, and acceptance criteria
2. Read the project's `CLAUDE.md` for architectural context, tech stack, and conventions
3. Analyze the story to identify the discrete implementation tasks needed:
   - What code changes are required (new files, modified files, new endpoints, etc.)
   - What tests need to be written
   - What configuration or infrastructure changes are needed
   - What documentation updates are needed
4. Create sub-issues under the parent story issue:
   - Each sub-issue should represent a single, independently implementable unit of work
   - Each sub-issue should have a clear title, description, and acceptance criteria
   - Each sub-issue should reference the parent story issue
   - Use task list syntax in the parent story body to link all sub-issues
5. Label each sub-issue:
   - `sub-issue` label on all
   - `type:code` for implementation tasks
   - `type:test` for test-only tasks
   - `type:config` for configuration or infrastructure changes
   - `type:docs` for documentation updates
6. Order sub-issues by dependency — if sub-issue B depends on sub-issue A, note the dependency in B's description
7. Add label `ready-for-implementation` to sub-issues that have no dependencies on other sub-issues

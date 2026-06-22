---
permissions:
  contents: read
  id-token: write   # required for WIF keyless auth

imports:
  - shared/wif-engine.md

safe-outputs:
  create-pull-request:
  add-comment:
    max: 3

---

# PRD Generation

When a new issue is labeled `feature-idea`, generate a Product Requirements Document (PRD) from the feature description.

## Instructions

1. Check that the issue has the `feature-idea` label. If not, skip this workflow.
2. Read the issue title and body to understand the feature request
3. Use the PRD template at `docs/prds/templates/prd-template.md` as the base structure
4. Read the project's `CLAUDE.md` for architectural context and technology stack
5. Generate a comprehensive PRD draft by filling in:
   - Problem statement derived from the issue description
   - User stories for the relevant personas
   - Functional requirements categorized by priority (P0/P1/P2)
   - Technical considerations aligned with the project's stack and architecture
   - Acceptance criteria based on the requirements
   - Test strategy covering unit and integration tests
6. Create the PRD as `docs/prds/{issue-number}-{slugified-title}.md`
7. Open a pull request with the generated PRD
8. Comment on the original issue linking to the PR and requesting review

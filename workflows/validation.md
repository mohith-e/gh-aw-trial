---
on: pull_request

permissions:
  contents: read
  pull-requests: read
  issues: read
  id-token: write   # required for WIF keyless auth

imports:
  - shared/wif-engine.md

safe-outputs:
  add-comment:
    max: 5
  update-issue:

---

# Value Validation

When an implementation PR is labeled `needs-validation`, validate the implementation against the PRD acceptance criteria.

## Instructions

1. Check that the pull request has the `needs-validation` label. If not, skip this workflow.
2. Read the pull request description and linked story issue
3. Find the associated PRD in `docs/prds/`
4. Review the code changes in the pull request
5. Validate against each acceptance criterion in the PRD:
   - Check that functional requirements are addressed
   - Verify test coverage exists for the acceptance criteria
   - Confirm the implementation matches the technical considerations
6. Post a validation report as a PR comment with:
   - Checklist of each acceptance criterion and pass/fail status
   - Summary of what was validated
   - Any gaps or concerns found
   - Overall recommendation: approve, request changes, or needs discussion
7. If all criteria pass, comment recommending the PR for merge
8. If criteria are missing, comment on the linked story issue describing the gaps

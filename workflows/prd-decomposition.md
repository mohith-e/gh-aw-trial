---
permissions:
  contents: read
  id-token: write   # required for WIF keyless auth

imports:
  - shared/wif-engine.md

safe-outputs:
  create-issue:
    max: 20
  add-labels:

---

# PRD Decomposition

When a PRD pull request is merged to main, decompose the PRD into epics and stories as GitHub Issues.

## Instructions

1. Identify the merged PRD file from the pull request changes
2. Read and analyze the full PRD document
3. Decompose the PRD into an epic and individual stories:
   - Create one epic issue with label `epic` summarizing the full feature
   - Create story issues with label `story` for each functional requirement
   - Each story should have a clear title, description, and acceptance criteria from the PRD
   - Link all stories to the epic using task list syntax in the epic body
4. Prioritize stories based on the PRD's P0/P1/P2 classification:
   - P0 stories get label `priority:critical`
   - P1 stories get label `priority:high`
   - P2 stories get label `priority:low`
5. Add label `ready-for-implementation` to P0 stories that have no dependencies

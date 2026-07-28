---
on:
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

imports:
  - shared/wif-engine.md

network: defaults

tools:
  bash: true

safe-outputs:
  noop:

timeout-minutes: 5
---

# WIF auth check

Use bash to read the `GITHUB_RUN_ID` and `GITHUB_REPOSITORY` environment variables. Print a confirmation that WIF authentication succeeded, including those values. Then call `noop`.

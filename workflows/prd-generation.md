---
on:
  workflow_dispatch:
  issues:
    types: [opened, labeled]

permissions:
  contents: read
  issues: read

imports:
  - RealPage/gh-aw-shared-workflows/shared/prd-generation.md@v0.1.0
---

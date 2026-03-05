---
on:
  workflow_dispatch:
  issues:
    types: [opened, labeled]

permissions:
  contents: read
  issues: read

imports:
  - RealPage/agentics/workflows/prd-generation.md@v0.1.0
---

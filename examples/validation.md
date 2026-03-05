---
on:
  workflow_dispatch:
  pull_request:
    types: [labeled]

permissions:
  contents: read
  issues: read
  pull-requests: read

imports:
  - RealPage/agentics/workflows/validation.md@v0.1.0
---

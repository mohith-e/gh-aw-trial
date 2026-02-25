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
  - RealPage/gh-aw-shared-workflows/workflows/validation.md@v0.1.0
---

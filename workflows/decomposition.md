---
on:
  workflow_dispatch:
  pull_request:
    types: [closed]
    branches: [main]
    paths: ["docs/prds/*.md"]

permissions:
  contents: read
  issues: read

imports:
  - RealPage/gh-aw-shared-workflows/shared/decomposition.md@v0.1.0
---

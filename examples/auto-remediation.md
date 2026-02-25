---
on:
  schedule:
    - cron: "0 * * * *"
  workflow_dispatch:
    inputs:
      service_name:
        description: "Service name to search errors for (overrides SERVICE_NAME env var)"
        required: false
      time_range_minutes:
        description: "How far back to search for errors (default: 60)"
        required: false
      max_issues:
        description: "Maximum number of errors to process (default: 5)"
        required: false
      dry_run:
        description: "Preview mode — analyze errors but don't create issues or PRs (true/false)"
        required: false

permissions:
  contents: read
  issues: read

imports:
  - RealPage/gh-aw-shared-workflows/workflows/auto-remediation.md@v0.1.0
---

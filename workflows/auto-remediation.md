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

engine: claude

mcp-servers:
  elastic:
    url: ${{ vars.ELASTIC_MCP_URL }}
    headers:
      Authorization: "ApiKey ${{ secrets.ELASTIC_MCP_API_KEY }}"

safe-outputs:
  create-issue:
    max: 5
  add-labels:
  create-pull-request:
    max: 5
  add-comment:
    max: 10

---

# Auto-Remediation

Discover errors from Elastic logs, triage them, create GitHub issues with root cause analysis, implement fixes, and open pull requests for human review.

## Context

This workflow runs on a schedule (hourly) or manually. It queries Elastic APM logs for a target service, analyzes errors with AI, and produces actionable pull requests with fixes. Humans review the PRs — they can approve, request changes, or discuss the proposed fix before merging.

The target service is configured via the `SERVICE_NAME` repository variable. The Elastic MCP server provides access to query logs via ES|QL.

## Stage 1: Error Discovery

1. Read the repository's `CLAUDE.md` for project context, tech stack, and key file locations
2. Determine the service name:
   - Use the `service_name` workflow input if provided
   - Otherwise use the `SERVICE_NAME` repository variable
   - If neither is set, skip with a comment explaining the configuration needed
3. Determine the time range:
   - Use the `time_range_minutes` input if provided, otherwise default to 60 minutes
4. Query the Elastic MCP server to discover errors:
   - Use the ES|QL query tool to search for ERROR-level logs in the time range
   - Query pattern: search for logs where `log.level == "ERROR"` and `service.name == "{service_name}"` within the last N minutes
   - Group errors by error type (exception class name or error message pattern)
   - For each unique error, capture: error type, error message, file path, function name, line number, occurrence count, and a sample stack trace
5. Deduplicate errors by error type — keep the entry with the highest occurrence count
   - AI-generated file paths in stack traces can be inconsistent, so deduplication should be by error type only
6. Sort by occurrence count (descending) and take the top N errors (use `max_issues` input or default to 5)
7. If no errors are found, log that the service is healthy and stop

## Stage 2: Triage and Root Cause Analysis

For each discovered error, perform triage and root cause analysis:

### Triage

Classify the error into:
- **Category**: One of: syntax, runtime, type, reference, network, database, authentication, authorization, validation, configuration, dependency, memory, timeout, logic, unknown
- **Severity**:
  - `critical` — Service outage, data loss, security breach
  - `high` — Major feature broken, significant user impact
  - `medium` — Degraded functionality, workaround available
  - `low` — Minor issue, cosmetic, or edge case
- **Summary**: One-sentence description of the problem
- **Root cause**: What is causing this error
- **Suggested fixes**: Ordered list of potential fixes, most likely first

### Root Cause Analysis

Analyze deeper to identify:
- **Code location**: The exact file, function, and line where the fix should be applied
- **Root cause explanation**: Why this error occurs (not just what it is)
- **Suggested fix**: Specific code change needed
- **Fix complexity**: trivial / simple / moderate / complex
- **Confidence**: high / medium / low

## Stage 3: Issue Creation

For each triaged error:

1. **Check for duplicates**: Search existing issues for the error type with the `auto-remediation` label. If a matching open issue exists, skip creating a new one and add a comment on the existing issue noting the continued occurrences
2. If `dry_run` is true, log the analysis results but do not create issues — skip to the summary
3. Create a GitHub issue with:
   - **Title**: `[{SEVERITY}] Fix {errorType} in {codeLocation}`
   - **Labels**: `auto-remediation`, `bug`
     - Add `priority:critical` or `priority:high` if severity warrants it
     - Add `type:{category}` (e.g., `type:network`, `type:database`)
   - **Body** containing:
     - Error summary and occurrence count
     - Root cause analysis
     - Suggested fix with code location
     - Fix complexity and confidence level
     - Sample stack trace in a collapsed `<details>` block
     - The time window searched

## Stage 4: Implementation

For each created issue, implement a fix:

1. Read the project's `CLAUDE.md` for coding standards, conventions, and key file locations
2. Read the source file identified in the root cause analysis
3. Understand the surrounding code context — read related files, imports, and tests
4. Implement the fix:
   - Make the minimal code change needed to resolve the error
   - Follow the project's existing patterns and conventions
   - Do NOT refactor surrounding code or make unrelated changes
   - Add or update tests to cover the error scenario if a test file exists for the affected code
5. Open a pull request with:
   - **Title**: `Fix {errorType} in {codeLocation} (auto-remediation)`
   - **Body** containing:
     - Link to the created issue (`Fixes #N`)
     - Summary of what was changed and why
     - Root cause analysis
     - The error occurrence count and severity
     - What to look for during review
   - **Labels**: `auto-remediation`
6. Comment on the issue linking to the PR

## Stage 5: Summary

After processing all errors, add a summary comment on the workflow run:

- Total errors discovered
- Errors processed (with breakdown by severity)
- Issues created (with links)
- PRs opened (with links)
- Duplicates skipped
- Any errors that failed to process and why

## Important Guidelines

- **Minimal fixes only**: Each PR should fix exactly one error. Do not bundle fixes or refactor.
- **Safety first**: If an error is in a security-sensitive area (authentication, authorization, cryptography), create the issue but flag it as needing human implementation — do NOT attempt an automated fix.
- **Protected paths**: Do not modify CI/CD configs, deployment manifests, or infrastructure files. Create an issue describing the needed fix instead.
- **Confidence threshold**: Only implement fixes where root cause confidence is `high` or `medium`. For `low` confidence, create the issue but skip implementation and note that manual investigation is needed.
- **Test preservation**: Never delete or weaken existing tests. Only add or strengthen test coverage.

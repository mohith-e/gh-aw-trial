---
description: |
  Security vulnerability triage agent. Pulls scan results from the Fortify on Demand
  API, categorizes findings by severity, and creates one GitHub issue per critical/high
  vulnerability with full remediation guidance. Also creates a summary tracking issue.

on:
  workflow_run:
    workflows: ["Fortify AST Scan"]
    types: [completed]
    branches: [master]
  schedule: weekly
  workflow_dispatch:
    inputs:
      fod_release_id:
        description: "Fortify on Demand release ID to triage"
        required: true
        type: string

engine: claude

permissions: read-all

network: defaults

tools:
  github:
    toolsets: [issues, repos]
  bash: true

safe-outputs:
  create-issue:
  add-labels:
    max: 5
  add-comment:
  update-issue:
  noop:

steps:
  - name: Fetch Fortify vulnerabilities
    env:
      FOD_PAT: ${{ secrets.FOD_PAT }}
      FOD_USERNAME: ${{ secrets.FOD_USERNAME }}
      FOD_RELEASE_ID: ${{ inputs.fod_release_id || secrets.FOD_RELEASE_ID }}
    run: |
      if [ -z "$FOD_USERNAME" ]; then
        echo '{"error": "FOD_USERNAME secret is not set. Configure in repo settings."}' > fortify-data.json
        exit 0
      fi
      if [ -z "$FOD_RELEASE_ID" ]; then
        echo '{"error": "FOD_RELEASE_ID is not set. Provide via workflow_dispatch input or set the FOD_RELEASE_ID repository variable."}' > fortify-data.json
        exit 0
      fi
      echo "Authenticating to Fortify API as $FOD_USERNAME..."
      FOD_TOKEN=$(curl --silent --request POST 'https://api.ams.fortify.com/oauth/token' \
        --form 'scope="api-tenant"' \
        --form 'grant_type="password"' \
        --form "username=\"$FOD_USERNAME\"" \
        --form "password=\"$FOD_PAT\"" | jq -r '.access_token')

      if [ -z "$FOD_TOKEN" ] || [ "$FOD_TOKEN" = "null" ]; then
        echo '{"error": "Failed to authenticate to Fortify API. Check FOD_PAT secret."}' > fortify-data.json
        exit 0
      fi
      echo "Authenticated successfully."

      echo "Fetching release summary for release $FOD_RELEASE_ID..."
      curl --silent "https://api.ams.fortify.com/api/v3/releases/$FOD_RELEASE_ID" \
        --header "Authorization: Bearer $FOD_TOKEN" \
        --header 'Accept: application/json' | jq '{
          releaseId: .releaseId,
          releaseName: .releaseName,
          critical: .critical,
          high: .high,
          medium: .medium,
          low: .low,
          issueCount: .issueCount,
          rating: .rating,
          isPassed: .isPassed,
          staticScanDate: .staticScanDate
        }' > fortify-summary.json

      echo "Release summary:"
      cat fortify-summary.json

      ISSUE_COUNT=$(jq '.issueCount' fortify-summary.json)
      if [ "$ISSUE_COUNT" = "0" ] || [ "$ISSUE_COUNT" = "null" ]; then
        echo '{"items": [], "totalCount": 0}' > fortify-vulns.json
        echo "No vulnerabilities found."
      else
        echo "Fetching $ISSUE_COUNT vulnerabilities (paginated)..."
        echo '{"items":[],"totalCount":0}' > fortify-vulns.json
        OFFSET=0
        while true; do
          PAGE=$(curl --silent "https://api.ams.fortify.com/api/v3/releases/$FOD_RELEASE_ID/vulnerabilities?limit=50&offset=$OFFSET&orderBy=severityString&orderByDirection=DESC" \
            --header "Authorization: Bearer $FOD_TOKEN" \
            --header 'Accept: application/json')
          PAGE_COUNT=$(echo "$PAGE" | jq '.items | length')
          TOTAL=$(echo "$PAGE" | jq '.totalCount')
          if [ "$OFFSET" = "0" ]; then
            echo "$PAGE" > fortify-vulns.json
          else
            jq --argjson new "$(echo "$PAGE" | jq '.items')" '.items += $new' fortify-vulns.json > fortify-vulns-tmp.json && mv fortify-vulns-tmp.json fortify-vulns.json
          fi
          echo "  Fetched $PAGE_COUNT vulns (offset $OFFSET, total $TOTAL)"
          OFFSET=$((OFFSET + 50))
          [ "$PAGE_COUNT" -lt 50 ] && break
          sleep 0.5
        done

        echo "Fetching details for critical and high vulnerabilities..."
        mkdir -p fortify-details
        for VULN_ID in $(jq -r '.items[] | select(.severityString == "Critical" or .severityString == "High") | .vulnId' fortify-vulns.json); do
          echo "  Fetching details for vuln $VULN_ID..."
          curl --silent "https://api.ams.fortify.com/api/v3/releases/$FOD_RELEASE_ID/vulnerabilities/$VULN_ID/details" \
            --header "Authorization: Bearer $FOD_TOKEN" \
            --header 'Accept: application/json' > "fortify-details/$VULN_ID.json"
          sleep 0.5
        done
        echo "Done fetching vulnerability details."
      fi

      echo "Fortify data collection complete."

---

# Fortify Security Triage

You are a security triage agent for the `${{ github.repository }}` repository. Your mission is to read pre-fetched Fortify vulnerability data, understand each finding, and create one GitHub issue per critical/high vulnerability with full remediation guidance. You also create a summary tracking issue.

## Context

- **Repository**: ${{ github.repository }}
- **Scanner**: Fortify on Demand (SAST)
- **Fortify Release ID**: Read from `fortify-summary.json` (`.releaseId` field)
- **Triage Date**: $(date +%Y-%m-%d)

## Data Files

The pre-step has already authenticated to the Fortify API and saved the results locally:

- `fortify-summary.json` — Release-level summary with severity counts
- `fortify-vulns.json` — Full list of vulnerabilities with metadata
- `fortify-details/<vulnId>.json` — Detailed info per critical/high vulnerability

## Workflow

### Step 1: Read Fortify Data

```bash
cat fortify-summary.json
```

```bash
cat fortify-vulns.json | jq '.totalCount as $total | {totalCount: $total, items: [.items[] | {vulnId: .vulnId, category: .category, subCategory: .subCategory, severity: .severityString, status: .status, isSuppressed: .isSuppressed, primaryLocation: .primaryLocationFull, lineNumber: .lineNumber, kingdom: .kingdom, cweId: .cweId, introducedDate: .introducedDate, removedDate: .removedDate}]}'
```

If `fortify-summary.json` contains an `error` field, call the `noop` tool reporting the auth failure and exit.

If `totalCount` is 0, call the `noop` tool with a message indicating no findings and exit.

### Step 2: Filter Findings

Skip entirely:
- Suppressed vulnerabilities (`isSuppressed: true`)
- Already removed vulnerabilities (`removedDate` is not null)

Group remaining:
1. **Critical** — will get individual issues
2. **High** — will get individual issues
3. **Medium/Low** — logged in summary only

### Step 3: Read Vulnerability Details

For each critical and high vulnerability, read the detailed remediation guidance:

```bash
cat fortify-details/<vulnId>.json | jq '{summary: .summary, explanation: .explanation, recommendations: .recommendations, tips: .tips}'
```

### Step 4: Create One Issue Per Critical/High Vulnerability

For each critical and high vulnerability, check if an issue already exists (search for `[Fortify-<vulnId>]` in issue titles). If not, create an issue:

**Title**: `[Fortify-<vulnId>] <Category>: <subCategory> in <fileName> (<severity>)`

**Body**:
```markdown
## Fortify Finding: <Category>

**Severity**: <severity>
**CWE**: [CWE-<cweId>](https://cwe.mitre.org/data/definitions/<cweId>.html)
**Kingdom**: <kingdom>
**File**: `<primaryLocationFull>`
**Line**: <lineNumber>
**Fortify Vuln ID**: <vulnId>
**Introduced**: <introducedDate>

### Summary
<summary from details>

### Explanation
<explanation from details>

### Recommended Fix
<recommendations from details>

### Tips
<tips from details>

---
*Created by Fortify Triage Agent on $(date +%Y-%m-%d)*
```

**Labels**: Add these labels to each issue:
- `fortify`
- `security`
- Severity label: `critical` or `high`
- `fortify-fix` (this triggers the remediation workflow)

### Step 5: Create Summary Tracking Issue

Create a summary issue titled `[Fortify Triage] Scan Results - $(date +%Y-%m-%d)` with:

```markdown
## Fortify SAST Triage Summary

**Scan Date**: $(date +%Y-%m-%d)
**Fortify Release**: {releaseId from fortify-summary.json}
**Star Rating**: {rating}/5
**Total Vulnerabilities**: N

| Severity | Count | Issues Created | Status |
|----------|-------|---------------|--------|
| Critical | X     | X             | Issues created |
| High     | X     | X             | Issues created |
| Medium   | X     | —             | Logged only |
| Low      | X     | —             | Logged only |

### Critical/High Issues Created

- #<issue_number> — [Fortify-<vulnId>] <Category> in <file>
- #<issue_number> — [Fortify-<vulnId>] <Category> in <file>

### Medium/Low Findings (not triaged)

- Medium: <category> in <file>:<line> (CWE-<cweId>)

### Suppressed (excluded)

- <count> suppressed findings skipped

---
*Generated by Fortify Triage Agent*
```

Label the summary issue with `fortify` and `triage-summary`.

## Important Guidelines

- **Read files, don't call APIs**: All Fortify data is pre-fetched in local JSON files. Do NOT attempt to call the Fortify API directly.
- **One issue per vulnerability**: Each critical/high finding gets its own issue for targeted remediation.
- **No duplicates**: Search existing issues before creating. If `[Fortify-<vulnId>]` already exists, skip it.
- **Always add `fortify-fix` label**: This triggers the separate remediation workflow.
- **Skip suppressed**: Do not create issues for suppressed vulnerabilities.
- **Noop when clean**: If no fixable vulnerabilities exist, call the `noop` tool and exit gracefully.

## Output Requirements

1. **If fixable findings exist**: Create individual issues + summary issue
2. **If no findings**: Call the `noop` tool:
   ```json
   {
     "noop": {
       "message": "Fortify triage complete. No open vulnerabilities found for the configured release."
     }
   }
   ```

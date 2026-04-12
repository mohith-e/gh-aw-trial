---
description: |
  PME triage workflow. Authenticates to Salesforce, fetches open Problem
  Management Escalations via SOQL, cross-references against GitHub Issues
  to find untracked PMEs, ranks by priority/age/impact, and creates
  GitHub issues for follow-up.

on:
  schedule: "every 6 hours"
  workflow_dispatch:
    inputs:
      product_filter:
        description: "SOQL LIKE pattern for Support_Product_Name__c (e.g. '%Knock%'). Leave empty for all products."
        default: ""
      pme_limit:
        description: "Max PMEs to fetch from Salesforce"
        default: "25"
      lookback_days:
        description: "How far back to search for new/updated PMEs (days)"
        default: "30"
      title_prefix:
        description: "Optional prefix for created issue titles"
        default: "PME "

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: claude

network:
  allowed:
    - defaults
    - "realpage.my.salesforce.com"
    # tfs.realpage.com: listed to prevent AWF from redacting TFS URLs in safe
    # outputs (e.g., Azure_DevOps_URL__c links). On GitHub-hosted runners this
    # host is unreachable; on self-hosted runners with VPN access it will also
    # enable future TFS REST API cross-referencing (v2).
    - "tfs.realpage.com"

tools:
  github:
    toolsets: [default]

mcp-scripts:
  sf-query:
    description: "Authenticate to Salesforce via OAuth client_credentials and execute a SOQL query. Returns results as JSON."
    inputs:
      query:
        type: string
        required: true
        description: "The SOQL query to execute"
    run: |
      AUTH=$(curl -s -X POST "https://realpage.my.salesforce.com/services/oauth2/token" \
        -d "grant_type=client_credentials" \
        -d "client_id=$SF_CLIENT_ID" \
        -d "client_secret=$SF_CLIENT_SECRET")
      TOKEN=$(echo "$AUTH" | jq -r '.access_token')
      if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "$AUTH"
        exit 1
      fi
      curl -s -G "https://realpage.my.salesforce.com/services/data/v62.0/query" \
        -H "Authorization: Bearer $TOKEN" \
        --data-urlencode "q=$INPUT_QUERY"
    env:
      SF_CLIENT_ID: "${{ vars.SF_OAUTH_CLIENT_ID }}"
      SF_CLIENT_SECRET: "${{ secrets.SF_OAUTH_SECRET }}"
    timeout: 30

safe-outputs:
  create-issue:
    title-prefix: ${{ inputs.title_prefix }}
    labels: [pme-triage]
    max: 10
  add-labels:
    max: 20
    allowed:
      - "pme-triage"
      - "priority:critical"
      - "priority:high"
      - "priority:medium"
      - "priority:low"
  add-comment:
    max: 5

timeout-minutes: 10
---

# PME Triage

You are a PME triage agent. Your job is to fetch open Problem Management Escalations (PMEs) from Salesforce, cross-reference them against this repository's GitHub Issues, and create tracking issues for any PMEs that are not yet being tracked.

Execute the following pipeline in order. If any step finds zero results, stop early and report.

> **Note:** The field API names for `Problem_Management_Escalation__c` below were validated against the production Salesforce org on 2026-04-12.

## Step 0: Salesforce Connectivity Check

Before querying for PMEs, verify that Salesforce authentication and the PME object are accessible.

Call `sf-query` with this query:

```
SELECT Id FROM Problem_Management_Escalation__c LIMIT 1
```

Inspect the response:

- If the response contains a `records` array (even if empty), authentication is working and the object exists. Proceed to Step 1.
- If the response contains an `error` or `errorCode` field, Salesforce is not accessible. Create a GitHub issue using the `create-issue` safe output with the following content, then **stop the pipeline** — do not continue to Step 1.

**Title:** `[SETUP] Salesforce authentication failed for PME triage`

**Body:**

````markdown
## Action Required — Configure Salesforce OAuth Credentials

The PME triage workflow could not authenticate to Salesforce. This usually means the OAuth client credentials are missing or misconfigured.

### Error Response

{paste the full error response JSON here}

### Steps to Fix

1. Ensure the following secrets are configured in this repository's GitHub Actions settings:
   - `SF_OAUTH_CLIENT_ID` (variable) — the Connected App client ID for `pmeautomation@realpage.com`
   - `SF_OAUTH_SECRET` (secret) — the corresponding client secret

2. Verify the Connected App in Salesforce:
   - The app must have the `client_credentials` OAuth flow enabled
   - The running user must be `pmeautomation@realpage.com`
   - The app must have access to the `Problem_Management_Escalation__c` object

3. Test authentication manually:
   ```bash
   curl -s -X POST "https://realpage.my.salesforce.com/services/oauth2/token" \
     -d "grant_type=client_credentials" \
     -d "client_id=$SF_OAUTH_CLIENT_ID" \
     -d "client_secret=$SF_OAUTH_SECRET"
   ```

### After Fixing

Close this issue and re-run the PME triage workflow. It will detect successful authentication and proceed normally.
````

Add the labels `pme-triage` to this issue using the `add-labels` safe output.

## Step 1: Fetch Open PMEs

Construct a SOQL query to fetch open PMEs from the last ${{ inputs.lookback_days }} days. Call `sf-query` with this query:

```
SELECT Name, Summary__c, Description__c, Priority__c, Escalation_Status__c, Accountable_Team__c, Responsible_Team__c, Impacted_Products__c, Azure_DevOps_ID__c, Azure_DevOps_URL__c, CreatedDate, LastModifiedDate FROM Problem_Management_Escalation__c WHERE Escalation_Status__c NOT IN ('Closed', 'Resolved') AND CreatedDate >= LAST_N_DAYS:${{ inputs.lookback_days }} ORDER BY Priority__c ASC, CreatedDate ASC LIMIT ${{ inputs.pme_limit }}
```

If `${{ inputs.product_filter }}` is not empty, add this condition to the WHERE clause before the ORDER BY:

```
AND Support_Product_Name__c LIKE '${{ inputs.product_filter }}'
```

After retrieving results:

- If the `records` array is empty or `totalSize` is 0, stop and report: "No open PMEs found in the last ${{ inputs.lookback_days }} days."
- Otherwise, note the total count and proceed.

## Step 2: Cross-Reference Against GitHub Issues

For each PME returned from Salesforce, search for existing open GitHub Issues in this repository that:
- Have the `pme-triage` label
- Contain the PME `Name` (e.g., `PME-00001`) in the issue title or body

Build three lists:

1. **Already tracked** — PMEs that have a matching open GitHub issue and the issue is up to date (the PME's `LastModifiedDate` is not significantly newer than the issue creation date)
2. **Untracked** — PMEs with no matching open GitHub issue
3. **Stale** — PMEs that have a matching open GitHub issue, but the PME's `LastModifiedDate` is more than 24 hours after the issue was created (indicating the PME has been updated since the issue was filed)

If all PMEs are already tracked and none are stale, stop and report: "All $N PMEs are already tracked. No action needed."

> **TODO (future):** When a PME matches an existing GitHub issue, post the issue link back to the PME record in Salesforce. The current `pmeautomation@realpage.com` Connected App may not have write permissions — verify before implementing.

## Step 3: Group and Rank Untracked PMEs

### 3a: Group related PMEs

Analyze the untracked PMEs and group ones that likely refer to the same underlying issue. Compare `Summary__c`, `Description__c`, `Impacted_Products__c`, and `Accountable_Team__c` across the untracked set. PMEs should be grouped together when they share:

- Substantially similar summaries or descriptions (e.g., same error message, same symptom described differently)
- The same impacted product AND similar symptoms
- Explicit cross-references to each other

PMEs that are clearly distinct problems should remain as singleton groups. When in doubt, do **not** group — it is better to create separate issues than to conflate unrelated problems.

### 3b: Score each group

Score each group using this formula:

**Score = priority_weight × (1 + age_days / 30) × (1 + 0.25 × (group_size - 1))**

Where:
- `priority_weight` based on the highest `Priority__c` prefix in the group:
  - `P1` = 4 (e.g., `P1 - Critical`)
  - `P2` = 3 (e.g., `P2 - Critical`, `P2 - High`)
  - `P3` = 2 (e.g., `P3 - Medium`, `P3 - Major`)
  - `P4` = 1 (e.g., `P4 - Enhancement`, `P4 - Feature Request`)
  - `null` or unrecognized = 2 (default to medium)
- `age_days`: days since the oldest `CreatedDate` in the group
- `group_size`: number of PMEs in the group (groups with more PMEs score higher, indicating a wider-impact issue)

Sort groups by score descending (highest score = most urgent).

Output the grouped and ranked list as a table before proceeding:

```markdown
| Rank | Group | PME Names | Priority | Oldest (days) | Size | Score | Summary |
|------|-------|-----------|----------|---------------|------|-------|---------|
```

## Step 4: Create GitHub Issues

For each group of untracked PMEs (up to 10 issues), create **one GitHub issue per group** using the `create-issue` safe output.

### Single-PME groups

**Title format:** `[{Priority__c}] {Name}: {Summary__c}`

Use the first 80 characters of `Summary__c` if it is longer.

### Multi-PME groups

**Title format:** `[{highest Priority__c}] {Name1}, {Name2}, ...: {common summary}`

Where `{common summary}` is a brief description of the shared symptom or root cause (not a concatenation of all summaries). Use the first 80 characters.

**Body template (for all issues):**

```markdown
## Summary

{For single-PME groups: Summary__c — full text}
{For multi-PME groups: description of the common issue, noting how many PMEs are grouped and why}

## PMEs in this Issue

{For each PME in the group, include a row in the table below}

| PME ID | Priority | Status | Created | Age | SF Link |
|--------|----------|--------|---------|-----|---------|
| {Name} | {Priority__c} | {Escalation_Status__c} | {CreatedDate} | {age_days} days | [View](https://realpage.my.salesforce.com/{Id}) |

## Details

{For single-PME groups: the PME's Description__c, or "No description provided." if empty}
{For multi-PME groups: include each PME's description under a sub-heading}

### {Name}: {Summary__c}

{Description__c}

## Existing Work Items

{For each PME with Azure_DevOps_ID__c populated: "- {Name}: TFS [{Azure_DevOps_ID__c}]({Azure_DevOps_URL__c})"}
{If no PMEs have work items: "No existing TFS work items linked in Salesforce."}

## Triage

| Field | Value |
|-------|-------|
| **Accountable Team** | {Accountable_Team__c — from highest-priority PME, or most common across group} |
| **Responsible Team** | {Responsible_Team__c} |
| **Impacted Products** | {union of Impacted_Products__c across group} |
| **Group Score** | {score} |

## Next Steps

- [ ] Review PME details and confirm priority
- [ ] Assign to the appropriate team
- [ ] Link to implementation issue or PR once work begins
- [ ] Close this issue when the PME(s) are resolved in Salesforce
```

### Apply Labels (if available)

Before applying labels, check whether each label exists in this repository by searching for it. Only apply labels that already exist.

Attempt to add the following labels to each created issue using the `add-labels` safe output:

- `pme-triage`
- `priority:{level}` based on the highest `Priority__c` prefix in the group: `P1` → `priority:critical`, `P2` → `priority:high`, `P3` → `priority:medium`, `P4` → `priority:low`. If all `Priority__c` values are null or unrecognized, use `priority:medium`.

If a label does not exist in the repository, **do not attempt to add it**. Instead, append the priority level to the issue title as a suffix: `[priority:high]`. For example:

- Label exists: title is `PME [P2 - High] PME-500128: ...` with `priority:high` label applied
- Label missing: title is `PME [P2 - High] PME-500128: ... [priority:high]`

## Step 5: Update Stale Tracking Issues

For each PME in the **stale** list (from Step 2), add a comment to the existing GitHub issue using the `add-comment` safe output:

```markdown
## PME Updated in Salesforce

This PME was last modified on **{LastModifiedDate}**, which is after this tracking issue was created.

### Current Salesforce State

| Field | Value |
|-------|-------|
| **Status** | {Escalation_Status__c} |
| **Priority** | {Priority__c} |
| **Accountable Team** | {Accountable_Team__c} |
| **Last Modified** | {LastModifiedDate} |

Please review the [PME in Salesforce](https://realpage.my.salesforce.com/{Id}) for the latest details.
```

## Final Summary

After completing all steps, output a summary table:

```markdown
## PME Triage Run Summary

**Run parameters:** product_filter=`${{ inputs.product_filter }}`, lookback_days=${{ inputs.lookback_days }}, pme_limit=${{ inputs.pme_limit }}

| # | PME Name(s) | Group | Priority | Age | Action | Issue |
|---|-------------|-------|----------|-----|--------|-------|
| 1 | {Name} | — / Group A | {Priority__c} | {age} days | Created / Already tracked / Stale — commented on #N | #N |
```

**Totals:**
- PMEs fetched from Salesforce: {count}
- Already tracked: {count}
- Untracked PMEs grouped into {N} issues: {count} PMEs → {N} issues
- Stale issues updated: {count}

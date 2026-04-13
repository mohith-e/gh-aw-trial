---
description: |
  PME triage workflow. Authenticates to Salesforce, fetches open Problem
  Management Escalations via SOQL, cross-references against GitHub Issues
  to find untracked PMEs, ranks by priority/age/impact, creates GitHub
  issues for follow-up, and writes triage results back to Salesforce.
  Detects enhancement clusters and works-as-designed customer pain.

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
      priority_filter:
        description: "SOQL LIKE pattern for Priority__c (e.g. 'P4%'). Leave empty for all priorities."
        default: ""
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
  repo-memory:
    branch-name: memory/pme-triage
    description: "PME tracking state — cross-reference cache and issue-number backfill"
    allowed-extensions: [".json"]
    max-file-size: 1048576
    max-file-count: 5

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
    max: 5
  add-labels:
    max: 25
    allowed:
      - "pme-triage"
      - "priority:critical"
      - "priority:high"
      - "priority:medium"
      - "priority:low"
      - "enhancement-backlog"
      - "wad:customer-impact"
  add-comment:
    max: 5
  jobs:
    sf-comment:
      description: "Post Chatter comments on Salesforce PME records. Pass a JSON array of {record_id, comment} objects. Called once per run with all comments batched."
      runs-on: ubuntu-latest
      output: "Comments posted to Salesforce PME records."
      inputs:
        comments_json:
          description: 'JSON array of objects, each with "record_id" (SF 18-char ID) and "comment" (text to post). Example: [{"record_id":"a4PQU...","comment":"GitHub Tracking: #42"}]'
          required: true
          type: string
      steps:
        - name: Post Chatter comments to Salesforce
          uses: actions/github-script@v8
          env:
            SF_CLIENT_ID: "${{ vars.SF_OAUTH_CLIENT_ID }}"
            SF_CLIENT_SECRET: "${{ secrets.SF_OAUTH_SECRET }}"
          with:
            script: |
              const fs = require('fs');
              const outputFile = process.env.GH_AW_AGENT_OUTPUT;
              if (!outputFile) { core.info('No agent output'); return; }

              const clientId = process.env.SF_CLIENT_ID;
              const clientSecret = process.env.SF_CLIENT_SECRET;
              if (!clientId || !clientSecret) {
                core.setFailed('SF_OAUTH_CLIENT_ID or SF_OAUTH_SECRET not configured');
                return;
              }

              // Authenticate via client_credentials
              const authResp = await fetch('https://realpage.my.salesforce.com/services/oauth2/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `grant_type=client_credentials&client_id=${encodeURIComponent(clientId)}&client_secret=${encodeURIComponent(clientSecret)}`
              });
              const authData = await authResp.json();
              if (!authData.access_token) {
                core.setFailed(`SF auth failed: ${JSON.stringify(authData)}`);
                return;
              }

              // Read the batched comments from agent output
              const agentOutput = JSON.parse(fs.readFileSync(outputFile, 'utf8'));
              const item = agentOutput.items.find(i => i.type === 'sf_comment');
              if (!item || !item.comments_json) {
                core.info('No sf_comment items found');
                return;
              }

              const comments = JSON.parse(item.comments_json);
              core.info(`Processing ${comments.length} SF comment(s)`);

              let posted = 0;
              for (const entry of comments) {
                core.info(`Posting comment to PME ${entry.record_id}`);
                try {
                  const resp = await fetch('https://realpage.my.salesforce.com/services/data/v62.0/sobjects/FeedItem', {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${authData.access_token}`,
                      'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ ParentId: entry.record_id, Body: entry.comment })
                  });
                  if (!resp.ok) {
                    const err = await resp.text();
                    core.warning(`SF API error for ${entry.record_id} (${resp.status}): ${err}`);
                    continue;
                  }
                  posted++;
                  core.info('Comment posted successfully');
                } catch (error) {
                  core.warning(`Request failed for ${entry.record_id}: ${error.message}`);
                  continue;
                }
              }
              core.info(`Posted ${posted}/${comments.length} comments`);
              if (posted === 0) {
                core.setFailed('All SF comment posts failed');
              }

timeout-minutes: 10
---

# PME Triage

You are a PME triage agent. Your job is to fetch open Problem Management Escalations (PMEs) from Salesforce, cross-reference them against this repository's GitHub Issues, and create tracking issues for any PMEs that are not yet being tracked.

Execute the following pipeline in order. If any step finds zero results, stop early and report.

> **Note:** The field API names for `Problem_Management_Escalation__c` below were validated against the production Salesforce org on 2026-04-12.

> **Write constraint — Salesforce comments:** The `sf-comment` safe output job posts permanent Chatter comments to Salesforce records. FeedItem deletion is disabled org-wide — every comment is permanent and visible to all PME stakeholders. Keep comments concise and factual. Do not post duplicate comments; always check for existing GitHub-linked comments before writing.
>
> **Batching:** Custom safe output jobs can only be called once per run. Collect ALL SF comments throughout the pipeline and call `sf-comment` exactly once at the end of Step 5 with a single `comments_json` array containing every comment to post.
>
> **Safe output timing:** All safe output items (`create-issue`, `add-labels`, `add-comment`, `sf-comment`) are processed **after your session ends**, not during it. You will never be able to see or look up issues you create via safe outputs — they do not exist yet. Do not search for newly created issues to obtain their numbers. Use PME names (not issue numbers) when referencing newly created issues in SF write-back comments.

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

If `${{ inputs.priority_filter }}` is not empty, add this condition to the WHERE clause before the ORDER BY:

```
AND Priority__c LIKE '${{ inputs.priority_filter }}'
```

After retrieving results:

- If the `records` array is empty or `totalSize` is 0, stop and report: "No open PMEs found in the last ${{ inputs.lookback_days }} days."
- Otherwise, note the total count and proceed.

## Step 2: Cross-Reference Against State File and GitHub Issues

### 2a: Load state file

Read `/tmp/gh-aw/repo-memory-default/pme-state.json` from repo memory. If the file does not exist (first run), start with an empty object `{}`.

The state file maps PME names to their tracking status:

```json
{
  "PME-493502": {"status": "tracked", "issue": 135, "sf_writeback": true},
  "PME-497398": {"status": "issue_pending", "title": "[Enhancement] AIM: ..."},
  "PME-500128": {"status": "tracked", "issue": 102, "sf_writeback": false}
}
```

### 2b: Backfill pending issues

For any PME in the state file with `"status": "issue_pending"`, search GitHub Issues for an open issue with the `pme-triage` label whose title contains the PME `Name`. If found, update the state entry to `"status": "tracked"` with the issue number. If not found, leave as `"issue_pending"` — it may still be processing.

### 2c: Classify fetched PMEs

For each PME returned from Salesforce in Step 1, check the state file first:

- **In state file with `"status": "tracked"`** — already tracked. Check if the PME's `LastModifiedDate` is more than 24 hours after the issue was created to detect staleness.
- **In state file with `"status": "issue_pending"`** — issue creation was submitted on a prior run but not yet confirmed. Treat as already tracked (do not create a duplicate).
- **Not in state file** — search GitHub Issues for an open issue with the `pme-triage` label containing the PME `Name` in the title or body. If found, add to the state file as `"tracked"`. If not found, classify as untracked.

Build three lists:

1. **Already tracked** — PMEs with a matching issue that is up to date
2. **Untracked** — PMEs with no matching issue
3. **Stale** — PMEs with a matching issue where `LastModifiedDate` is more than 24 hours after issue creation

If all PMEs are already tracked and none are stale, save the state file and stop: "All $N PMEs are already tracked. No action needed."

### 2d: Write back issue links to Salesforce

For each PME in the **already tracked** list where the state file has `"sf_writeback": false` (or the field is missing), post the GitHub issue link back to the PME record in Salesforce.

To avoid duplicate comments, also check whether the GitHub issue body contains the string `SF write-back: done`. If present, set `"sf_writeback": true` in the state file and skip.

If not yet written back, add an entry to the SF comments batch:

- `record_id`: the PME's Salesforce `Id`
- `comment`: `"GitHub Tracking: #{issue_number} — {issue_title}\nhttps://github.com/{owner}/{repo}/issues/{issue_number}"`

Then set `"sf_writeback": true` in the state entry.

> **Note:** FeedItem cannot be queried by ParentId via SOQL (Salesforce platform restriction). Use the GitHub issue body and the state file as dedup sources, not Salesforce.

## Step 3: Group and Rank Untracked PMEs

### 3a: Group related PMEs

Analyze the untracked PMEs and group ones that likely refer to the same underlying issue. Compare `Summary__c`, `Description__c`, `Impacted_Products__c`, and `Accountable_Team__c` across the untracked set. PMEs should be grouped together when they share:

- Substantially similar summaries or descriptions (e.g., same error message, same symptom described differently)
- The same impacted product AND similar symptoms
- Explicit cross-references to each other

PMEs that are clearly distinct problems should remain as singleton groups. When in doubt, do **not** group — it is better to create separate issues than to conflate unrelated problems.

After grouping, classify each group as either a **bug group** or an **enhancement group**:

- **Enhancement group**: ALL PMEs in the group have `Priority__c` starting with `P4` (e.g., `P4 - Enhancement`, `P4 - Feature Request`), AND the summaries/descriptions indicate a feature request, improvement suggestion, or enhancement rather than a defect. Common signals: "would be nice", "feature request", "enhancement", "ability to", "support for", "option to".
- **Bug group**: Any group that contains at least one PME with priority P1–P3, OR where the descriptions clearly describe a defect, error, or regression — even if all PMEs are P4.

When in doubt, classify as a bug group. It is better to over-surface a potential bug than to bury it in the enhancement backlog.

For enhancement groups, perform an additional clustering step: look across all enhancement groups for clusters that share the same product area (`Impacted_Products__c`) or accountable team (`Accountable_Team__c`). Merge enhancement groups that target the same product area into larger "enhancement opportunity" groups. Bug groups should NOT be merged in this step — only enhancement groups.

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

Sort bug groups by score descending (highest score = most urgent).

For **enhancement groups**, use a modified scoring formula:

**Enhancement Score = cluster_size × (1 + age_days / 60) × product_area_weight**

Where:
- `cluster_size`: number of PMEs in the enhancement group (dominant factor — more requests = more demand)
- `age_days`: days since the oldest `CreatedDate` in the group
- `product_area_weight`: 1.5 if all PMEs share the same `Impacted_Products__c` (focused demand), 1.0 otherwise

Sort enhancement groups separately by enhancement score descending.

Output the grouped and ranked list as a table before proceeding. List all bug groups first, then all enhancement groups, with a separator row:

```markdown
| Rank | Type | Group | PME Names | Priority | Oldest (days) | Size | Score | Summary |
|------|------|-------|-----------|----------|---------------|------|-------|---------|
```

### 3c: WAD (Works As Designed) detection

Before creating issues, analyze each group (both bug and enhancement) for "works as designed" signals — behavior that is technically correct per the system's design but causes customer pain.

**WAD signals** (one or more indicates possible WAD):
- The description mentions the system is "working as expected" or "by design" but the behavior causes customer frustration or confusion
- The description references documentation or help text that confirms the current behavior
- The escalation was filed because the customer expected different behavior, not because of an error or crash
- Keywords: "works as designed", "by design", "expected behavior", "not a bug", "confusing", "unintuitive", "misleading"
- The PME status or notes indicate that support confirmed the behavior is correct but the customer is still impacted
- The `Priority__c` is P3 or P4 and the description focuses on user experience or workflow friction rather than a technical defect

**WAD classification:**
- If a group has strong WAD signals AND the behavior causes measurable customer impact (repeated escalations, customer churn risk, workflow blockers), flag it as `wad: true`.
- If a group has WAD signals but the impact is low or cosmetic, note it but do not flag it.
- If in doubt, do NOT flag as WAD — it is better to treat something as a bug than to dismiss customer pain.

For each WAD-flagged group, record:
- **WAD behavior**: what the system does (correctly, per its design)
- **Customer expectation**: what the customer expected instead
- **Impact**: why this matters (frequency, severity, workaround difficulty)

## Step 4: Create GitHub Issues

For each group of untracked PMEs (up to 10 issues), create **one GitHub issue per group** using the `create-issue` safe output. Use the bug group template for bug groups and the enhancement group template for enhancement groups.

### Single-PME bug groups

**Title format:** `[{Priority__c}] {Name}: {Summary__c}`

Use the first 80 characters of `Summary__c` if it is longer.

### Multi-PME bug groups

**Title format:** `[{highest Priority__c}] {Name1}, {Name2}, ...: {common summary}`

Where `{common summary}` is a brief description of the shared symptom or root cause (not a concatenation of all summaries). Use the first 80 characters.

**Body template (for bug group issues):**

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

### Enhancement group issues

For groups classified as `enhancement`, use a different title and body template.

**Title format:** `[Enhancement] {product_area}: {common theme} ({N} PMEs)`

Where `{product_area}` is the shared `Impacted_Products__c` (or "Multiple Products" if mixed), and `{common theme}` is a brief description of the enhancement area (first 80 characters).

**Body template for enhancement groups:**

```markdown
## Enhancement Opportunity

{Description of the common enhancement theme across the grouped PMEs. What capability are customers requesting? What product area does this affect?}

**Cluster size:** {N} PMEs requesting similar functionality
**Product area:** {Impacted_Products__c}
**Demand signal:** {N} independent escalations over {age_range} days

## PMEs in this Enhancement Cluster

| PME ID | Summary | Created | Age | SF Link |
|--------|---------|---------|-----|---------|
| {Name} | {Summary__c} | {CreatedDate} | {age_days} days | [View](https://realpage.my.salesforce.com/{Id}) |

## Individual Requests

{For each PME, include their specific request under a sub-heading}

### {Name}: {Summary__c}

{Description__c}

## Existing Work Items

{Same as bug template}

## Product Review

| Field | Value |
|-------|-------|
| **Accountable Team** | {Accountable_Team__c} |
| **Impacted Products** | {union of Impacted_Products__c} |
| **Enhancement Score** | {score} |
| **Cluster Size** | {N} PMEs |
| **Oldest Request** | {oldest CreatedDate} ({age} days ago) |

## Next Steps

- [ ] Review enhancement requests and assess product fit
- [ ] Prioritize against current roadmap
- [ ] If accepted, create implementation stories
- [ ] If declined, update PME records with rationale
- [ ] Close this issue when a decision is made
```

Apply the `enhancement-backlog` label (in addition to `pme-triage`) to enhancement group issues using the `add-labels` safe output, if the label exists in the repository. If it does not exist, prepend `[Enhancement]` to the issue title instead. Do **not** apply a `priority:*` label to enhancement group issues — the priority is implicitly low (P4) and the demand signal (cluster size) is the relevant metric.

### WAD-flagged issues

For any group (bug or enhancement) flagged as `wad: true` in Step 3c, add a **Product Opportunity** section to the issue body. Insert it between the "Details" / "Individual Requests" section and the "Existing Work Items" section:

```markdown
## Product Opportunity — Works As Designed

> **This behavior appears to be working as designed, but is causing customer pain.**

| Aspect | Description |
|--------|-------------|
| **Current behavior** | {what the system does correctly per its design} |
| **Customer expectation** | {what customers expect instead} |
| **Impact** | {why this matters — frequency, workaround difficulty, customer sentiment} |

This PME may not represent a bug in the traditional sense, but the gap between designed behavior and customer expectation represents a product improvement opportunity.
```

Apply the `wad:customer-impact` label to these issues using the `add-labels` safe output, if the label exists in the repository. If it does not exist, prepend `[WAD]` to the issue title instead. This label can coexist with other labels (`pme-triage`, `priority:*`, `enhancement-backlog`).

### Apply Labels (if available)

Before applying labels, check whether each label exists in this repository by searching for it. Only apply labels that already exist.

Attempt to add the following labels to each created issue using the `add-labels` safe output:

- `pme-triage`
- `priority:{level}` based on the highest `Priority__c` prefix in the group: `P1` → `priority:critical`, `P2` → `priority:high`, `P3` → `priority:medium`, `P4` → `priority:low`. If all `Priority__c` values are null or unrecognized, use `priority:medium`.

If a label does not exist in the repository, **do not attempt to add it**. Instead, append the priority level to the issue title as a suffix: `[priority:high]`. For example:

- Label exists: title is `PME [P2 - High] PME-500128: ...` with `priority:high` label applied
- Label missing: title is `PME [P2 - High] PME-500128: ... [priority:high]`

### Post issue link back to Salesforce

For each PME included in a newly created GitHub issue, add an entry to the SF comments batch:

- `record_id`: the PME's Salesforce `Id`
- `comment`: `"GitHub Issue Created: {issue_title}\nRepository: {owner}/{repo}"`

Since issue numbers are not available at this point (safe outputs are processed after your session ends), reference the issue by title. The next scheduled run will backfill the issue number via Step 2b.

### Update state file

For each PME included in a newly created issue, add or update its entry in the state file:

```json
{"status": "issue_pending", "title": "{issue_title}", "sf_writeback": false}
```

The next run's Step 2b will backfill the issue number once the safe output has been processed.

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

After posting the GitHub comment, also add an entry to the SF comments batch:

- `record_id`: the PME's Salesforce `Id`
- `comment`: `"GitHub Issue updated with latest Salesforce state.\nRepository: {owner}/{repo}"`

### Post all SF comments

After completing Steps 2b, 4, and 5, call the `sf-comment` safe output job exactly **once** with all collected comments:

- `comments_json`: a JSON array of `{"record_id": "...", "comment": "..."}` objects

If no comments were collected (e.g., all PMEs already had write-back markers), skip this call.

### Save state file

Write the updated state file to `/tmp/gh-aw/repo-memory-default/pme-state.json`. This file is automatically committed and pushed to the `memory/pme-triage` branch after the run completes. Include all PMEs processed during this run — both newly added entries and updated existing entries.

## Final Summary

After completing all steps, output a summary table:

```markdown
## PME Triage Run Summary

**Run parameters:** product_filter=`${{ inputs.product_filter }}`, priority_filter=`${{ inputs.priority_filter }}`, lookback_days=${{ inputs.lookback_days }}, pme_limit=${{ inputs.pme_limit }}

| # | PME Name(s) | Type | WAD | Group | Priority | Age | Action | SF Write-Back | Issue |
|---|-------------|------|-----|-------|----------|-----|--------|---------------|-------|
| 1 | {Name} | Bug / Enhancement | — / WAD | — / Group A | {Priority__c} | {age} days | Created / Already tracked / Stale | ✓ / — | #N |
```

**Totals:**
- PMEs fetched from Salesforce: {count}
- Already tracked: {count} ({count} with SF write-back)
- Bug groups created: {count} issues ({count} PMEs)
- Enhancement groups created: {count} issues ({count} PMEs)
- WAD-flagged issues: {count}
- Stale issues updated: {count}
- SF comments posted: {count}

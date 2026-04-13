---
description: |
  PME triage workflow. Pre-step authenticates to Salesforce and fetches open
  Problem Management Escalations via SOQL, lists existing GitHub tracking issues,
  and checks label availability — all deterministically in pre-activation.
  The agent reads the pre-computed context, groups/scores/classifies PMEs,
  creates GitHub issues for untracked PMEs, and writes triage results back
  to Salesforce. Detects enhancement clusters and works-as-designed customer pain.

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
  steps:
    - name: Fetch PME context (SF + GitHub + state)
      env:
        SF_CLIENT_ID: "${{ vars.SF_OAUTH_CLIENT_ID }}"
        SF_CLIENT_SECRET: "${{ secrets.SF_OAUTH_SECRET }}"
        GH_TOKEN: "${{ github.token }}"
        PRODUCT_FILTER: "${{ inputs.product_filter }}"
        PRIORITY_FILTER: "${{ inputs.priority_filter }}"
        LOOKBACK_DAYS: "${{ inputs.lookback_days || '30' }}"
        PME_LIMIT: "${{ inputs.pme_limit || '25' }}"
        REPO: "${{ github.repository }}"
      run: |
        set -euo pipefail
        mkdir -p /tmp/gh-aw/agent

        #──────────────────────────────────────────────
        # 1. Salesforce authentication
        #──────────────────────────────────────────────
        echo "::group::Salesforce authentication"
        if [ -z "${SF_CLIENT_ID:-}" ] || [ -z "${SF_CLIENT_SECRET:-}" ]; then
          echo '{"sf_auth_error": "SF_OAUTH_CLIENT_ID or SF_OAUTH_SECRET not configured"}' > /tmp/gh-aw/agent/pme-context.json
          echo "::error::Salesforce credentials not configured"
          echo "::endgroup::"
          exit 0
        fi
        AUTH=$(curl -s -X POST "https://realpage.my.salesforce.com/services/oauth2/token" \
          -d "grant_type=client_credentials" \
          -d "client_id=$SF_CLIENT_ID" \
          -d "client_secret=$SF_CLIENT_SECRET")
        TOKEN=$(echo "$AUTH" | jq -r '.access_token')
        if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
          echo "{\"sf_auth_error\": $(echo "$AUTH" | jq -c .)}" > /tmp/gh-aw/agent/pme-context.json
          echo "::error::Salesforce authentication failed"
          echo "::endgroup::"
          exit 0
        fi
        echo "Authenticated to Salesforce successfully."
        echo "::endgroup::"

        #──────────────────────────────────────────────
        # 2. SOQL query — fetch open PMEs
        #──────────────────────────────────────────────
        echo "::group::SOQL query"
        QUERY="SELECT Id, Name, Summary__c, Description__c, Priority__c, Escalation_Status__c, Accountable_Team__c, Responsible_Team__c, Impacted_Products__c, Azure_DevOps_ID__c, Azure_DevOps_URL__c, CreatedDate, LastModifiedDate FROM Problem_Management_Escalation__c WHERE Escalation_Status__c NOT IN ('Closed', 'Resolved') AND CreatedDate >= LAST_N_DAYS:${LOOKBACK_DAYS}"
        if [ -n "${PRODUCT_FILTER:-}" ]; then
          QUERY="${QUERY} AND Support_Product_Name__c LIKE '${PRODUCT_FILTER}'"
        fi
        if [ -n "${PRIORITY_FILTER:-}" ]; then
          QUERY="${QUERY} AND Priority__c LIKE '${PRIORITY_FILTER}'"
        fi
        QUERY="${QUERY} ORDER BY Priority__c ASC, CreatedDate ASC LIMIT ${PME_LIMIT}"
        echo "Query: $QUERY"
        SF_RESULT=$(curl -s -G "https://realpage.my.salesforce.com/services/data/v62.0/query" \
          -H "Authorization: Bearer $TOKEN" \
          --data-urlencode "q=$QUERY")
        PME_COUNT=$(echo "$SF_RESULT" | jq '.totalSize // 0')
        echo "Fetched $PME_COUNT PME(s) from Salesforce."
        echo "::endgroup::"

        #──────────────────────────────────────────────
        # 3. GitHub issues with pme-triage label
        #──────────────────────────────────────────────
        echo "::group::GitHub issues"
        GH_ISSUES=$(gh issue list --repo "$REPO" --label pme-triage --state open --limit 200 \
          --json number,title,body,createdAt,labels 2>/dev/null || echo '[]')
        GH_ISSUE_COUNT=$(echo "$GH_ISSUES" | jq 'length')
        echo "Found $GH_ISSUE_COUNT existing pme-triage issue(s)."
        echo "::endgroup::"

        #──────────────────────────────────────────────
        # 4. Label existence check
        #──────────────────────────────────────────────
        echo "::group::Label check"
        LABELS_TO_CHECK='["pme-triage","priority:critical","priority:high","priority:medium","priority:low","enhancement-backlog","wad:customer-impact"]'
        LABELS_EXIST='{}'
        for LABEL in $(echo "$LABELS_TO_CHECK" | jq -r '.[]'); do
          if gh label list --repo "$REPO" --search "$LABEL" --limit 1 --json name 2>/dev/null | jq -e --arg l "$LABEL" 'any(.[]; .name == $l)' > /dev/null 2>&1; then
            LABELS_EXIST=$(echo "$LABELS_EXIST" | jq --arg l "$LABEL" '. + {($l): true}')
          else
            LABELS_EXIST=$(echo "$LABELS_EXIST" | jq --arg l "$LABEL" '. + {($l): false}')
          fi
        done
        echo "Labels: $LABELS_EXIST"
        echo "::endgroup::"

        #──────────────────────────────────────────────
        # 5. State file from repo-memory
        #──────────────────────────────────────────────
        echo "::group::State file"
        STATE='{}'
        # No git checkout in pre_activation, so use the GitHub API to check
        # for the memory branch and fetch the state file via raw content.
        MEMORY_BRANCH_REF=$(gh api "repos/$REPO/git/ref/heads/memory/pme-triage" --jq '.ref' 2>/dev/null || echo '')
        if [ -n "$MEMORY_BRANCH_REF" ]; then
          # File is at the root of the memory branch (not under a subdirectory)
          STATE_CONTENT=$(gh api "repos/$REPO/contents/pme-state.json?ref=memory/pme-triage" --jq '.content' 2>/dev/null | base64 -d 2>/dev/null || echo '{}')
          if echo "$STATE_CONTENT" | jq . > /dev/null 2>&1; then
            STATE="$STATE_CONTENT"
          fi
        fi
        STATE_KEYS=$(echo "$STATE" | jq 'keys | length')
        echo "Loaded state file with $STATE_KEYS tracked PME(s)."
        echo "::endgroup::"

        #──────────────────────────────────────────────
        # 6. Assemble context file
        #──────────────────────────────────────────────
        jq -n \
          --argjson sf_pmes "$SF_RESULT" \
          --argjson gh_issues "$GH_ISSUES" \
          --argjson labels "$LABELS_EXIST" \
          --argjson state "$STATE" \
          --arg product_filter "${PRODUCT_FILTER:-}" \
          --arg priority_filter "${PRIORITY_FILTER:-}" \
          --arg lookback_days "$LOOKBACK_DAYS" \
          --arg pme_limit "$PME_LIMIT" \
          --arg repo "$REPO" \
          '{
            run_params: {
              product_filter: $product_filter,
              priority_filter: $priority_filter,
              lookback_days: ($lookback_days | tonumber),
              pme_limit: ($pme_limit | tonumber),
              repo: $repo
            },
            sf_pmes: $sf_pmes,
            gh_issues: $gh_issues,
            labels: $labels,
            state: $state
          }' > /tmp/gh-aw/agent/pme-context.json

        echo "Context file written: $(wc -c < /tmp/gh-aw/agent/pme-context.json) bytes"
        echo "  PMEs from SF: $PME_COUNT"
        echo "  Existing issues: $GH_ISSUE_COUNT"
        echo "  State entries: $STATE_KEYS"
    - name: Upload context artifact
      uses: actions/upload-artifact@v4
      with:
        name: pme-context
        path: /tmp/gh-aw/agent/pme-context.json
        # Artifact only needs to survive until the agent job downloads it
        # (seconds, not days). If the schedule frequency is reduced (e.g.
        # weekly), this does NOT need to change — it's cross-job within a
        # single run, not cross-run. Only increase if the workflow itself
        # takes >1 day to complete.
        retention-days: 1

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: claude

network:
  allowed:
    - defaults
    # tfs.realpage.com: listed to prevent AWF from redacting TFS URLs in safe
    # outputs (e.g., Azure_DevOps_URL__c links). On GitHub-hosted runners this
    # host is unreachable; on self-hosted runners with VPN access it will also
    # enable future TFS REST API cross-referencing (v2).
    - "tfs.realpage.com"

tools:
  github:
    toolsets: [issues, repos]
  repo-memory:
    branch-name: memory/pme-triage
    description: "PME tracking state — cross-reference cache and issue-number backfill"
    allowed-extensions: [".json"]
    max-file-size: 1048576
    max-file-count: 5

steps:
  - name: Download context artifact
    uses: actions/download-artifact@v4
    with:
      name: pme-context
      path: /tmp/gh-aw/agent/

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

You are a PME triage agent. A deterministic pre-step has already fetched all data you need. Your job is to classify, group, and score PMEs, then create GitHub issues for untracked ones.

> **Write constraint — Salesforce comments:** The `sf-comment` safe output job posts permanent Chatter comments to Salesforce records. FeedItem deletion is disabled org-wide — every comment is permanent and visible to all PME stakeholders. Keep comments concise and factual. Do not post duplicate comments.
>
> **Batching:** Custom safe output jobs can only be called once per run. Collect ALL SF comments throughout the pipeline and call `sf-comment` exactly once at the end with a single `comments_json` array containing every comment to post.
>
> **Safe output timing:** All safe output items (`create-issue`, `add-labels`, `add-comment`, `sf-comment`) are processed **after your session ends**, not during it. You will never be able to see or look up issues you create via safe outputs — they do not exist yet. Do not search for newly created issues to obtain their numbers. Use PME names (not issue numbers) when referencing newly created issues in SF write-back comments.

## Step 1: Read Pre-Computed Context

Read `/tmp/gh-aw/agent/pme-context.json`. This file was assembled by the pre-step and contains:

```json
{
  "run_params": { "product_filter": "...", "priority_filter": "...", "lookback_days": 30, "pme_limit": 25, "repo": "owner/repo" },
  "sf_pmes": { "totalSize": N, "records": [ ... ] },
  "gh_issues": [ { "number": 102, "title": "...", "body": "...", "createdAt": "...", "labels": [...] } ],
  "labels": { "pme-triage": true, "priority:high": true, "enhancement-backlog": false, ... },
  "state": { "PME-500128": { "status": "tracked", "issue": 102, "sf_writeback": true }, ... }
}
```

**If the file contains `sf_auth_error`**, Salesforce authentication failed. Create a GitHub issue using the `create-issue` safe output:

- **Title:** `[SETUP] Salesforce authentication failed for PME triage`
- **Body:** Include the error from the context file, instructions to configure `SF_OAUTH_CLIENT_ID` (variable) and `SF_OAUTH_SECRET` (secret) for the Connected App (`pmeautomation@realpage.com`), and a manual test curl command. Then **stop** — do not continue.

**If `sf_pmes.totalSize` is 0**, stop and report: "No open PMEs found."

## Step 2: Cross-Reference PMEs Against State and GitHub Issues

### 2a: Backfill pending issues

For any PME in the state file with `"status": "issue_pending"`, search the `gh_issues` array for an open issue whose title contains the PME `Name`. If found, update the state entry to `"status": "tracked"` with the issue number. If not found, leave as `"issue_pending"`.

### 2b: Classify fetched PMEs

For each PME in `sf_pmes.records`, check the state file first:

- **In state with `"status": "tracked"`** — already tracked. Check if `LastModifiedDate` is more than 24 hours after the matching issue's `createdAt` to detect staleness.
- **In state with `"status": "issue_pending"`** — treat as already tracked (do not create a duplicate).
- **Not in state** — search `gh_issues` for an issue whose title or body contains the PME `Name`. If found, add to state as `"tracked"`. If not found, classify as **untracked**.

Build three lists: **already tracked**, **untracked**, **stale**.

If all PMEs are already tracked and none are stale, save the state file and stop: "All $N PMEs are already tracked. No action needed."

### 2c: Write back issue links to Salesforce

For each PME in the **already tracked** list where the state has `"sf_writeback": false` (or missing), check whether the matching GitHub issue body contains `SF write-back: done`. If present, set `"sf_writeback": true` and skip. Otherwise, add an SF comment entry:
- `record_id`: the PME's Salesforce `Id`
- `comment`: `"GitHub Tracking: #{issue_number} — {issue_title}\nhttps://github.com/{repo}/issues/{issue_number}"`

Then set `"sf_writeback": true` in the state entry.

## Step 3: Group and Rank Untracked PMEs

### 3a: Group related PMEs

Group untracked PMEs that likely refer to the same underlying issue by comparing `Summary__c`, `Description__c`, `Impacted_Products__c`, and `Accountable_Team__c`. When in doubt, do **not** group.

Classify each group:
- **Enhancement group**: ALL PMEs have `Priority__c` starting with `P4` AND descriptions indicate feature requests (signals: "would be nice", "feature request", "enhancement", "ability to", "support for", "option to").
- **Bug group**: Any group with P1–P3 priority, or descriptions clearly describe defects. When in doubt, classify as bug.

For enhancement groups, merge clusters sharing the same `Impacted_Products__c` or `Accountable_Team__c`.

### 3b: Score each group

**Bug score** = `priority_weight × (1 + age_days / 30) × (1 + 0.25 × (group_size - 1))`

Priority weights: P1=4, P2=3, P3=2, P4=1, null/unknown=2.

**Enhancement score** = `cluster_size × (1 + age_days / 60) × product_area_weight`

Where `product_area_weight` = 1.5 if all PMEs share the same `Impacted_Products__c`, else 1.0.

Output a ranked table before proceeding:

```markdown
| Rank | Type | PME Names | Priority | Age (days) | Size | Score | Summary |
```

### 3c: WAD (Works As Designed) detection

Check each group for WAD signals: "works as designed", "by design", "expected behavior", "not a bug", "confusing", "unintuitive" — or when support confirmed behavior is correct but customer is still impacted.

Flag as `wad: true` only when there are strong WAD signals AND measurable customer impact. Record the current behavior, customer expectation, and impact.

## Step 4: Create GitHub Issues

For each group of untracked PMEs, create **one issue per group** using `create-issue`.

### Title formats

- **Single-PME bug:** `[{Priority__c}] {Name}: {Summary__c}` (first 80 chars of summary)
- **Multi-PME bug:** `[{highest Priority}] {Name1}, {Name2}: {common summary}`
- **Enhancement:** `[Enhancement] {product_area}: {common theme} ({N} PMEs)`

### Bug issue body

```markdown
## Summary
{Summary__c or description of common issue for multi-PME groups}

## PMEs in this Issue
| PME ID | Priority | Status | Created | Age | SF Link |
|--------|----------|--------|---------|-----|---------|
| {Name} | {Priority__c} | {Escalation_Status__c} | {CreatedDate} | {age} days | [View](https://realpage.my.salesforce.com/{Id}) |

## Details
{Description__c, or per-PME sub-headings for multi-PME groups}

## Existing Work Items
{TFS links from Azure_DevOps_ID__c/Azure_DevOps_URL__c, or "No existing TFS work items linked."}

## Triage
| Field | Value |
|-------|-------|
| **Accountable Team** | {Accountable_Team__c} |
| **Responsible Team** | {Responsible_Team__c} |
| **Impacted Products** | {Impacted_Products__c} |
| **Group Score** | {score} |

## Next Steps
- [ ] Review PME details and confirm priority
- [ ] Assign to the appropriate team
- [ ] Link to implementation issue or PR once work begins
- [ ] Close this issue when the PME(s) are resolved in Salesforce
```

### Enhancement issue body

```markdown
## Enhancement Opportunity
{Description of the common enhancement theme}

**Cluster size:** {N} PMEs | **Product area:** {Impacted_Products__c} | **Demand signal:** {N} escalations over {age_range} days

## PMEs in this Enhancement Cluster
| PME ID | Summary | Created | Age | SF Link |
|--------|---------|---------|-----|---------|

## Individual Requests
{Per-PME sub-headings with Description__c}

## Existing Work Items
{TFS links or "No existing TFS work items linked."}

## Product Review
| Field | Value |
|-------|-------|
| **Accountable Team** | {Accountable_Team__c} |
| **Impacted Products** | {Impacted_Products__c} |
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

### WAD-flagged issues

For any `wad: true` group, insert this section between "Details"/"Individual Requests" and "Existing Work Items":

```markdown
## Product Opportunity — Works As Designed
> **This behavior appears to be working as designed, but is causing customer pain.**

| Aspect | Description |
|--------|-------------|
| **Current behavior** | {what the system does} |
| **Customer expectation** | {what customers expect} |
| **Impact** | {frequency, workaround difficulty, sentiment} |
```

### Labels

Use the `labels` object from the context file to know which labels exist. Only apply labels that exist.

- Bug issues: apply `priority:{level}` label (P1→critical, P2→high, P3→medium, P4→low)
- Enhancement issues: apply `enhancement-backlog` label (no priority label)
- WAD issues: apply `wad:customer-impact` label

If a label does not exist, append it to the title instead: `[priority:high]`.

### SF write-back for new issues

For each PME in a newly created issue, add an entry to the SF comments batch:
- `record_id`: the PME's Salesforce `Id`
- `comment`: `"GitHub Issue Created: {issue_title}\nRepository: {repo}"`

Issue numbers are not available (safe outputs process after your session), so reference by title. The next run backfills via Step 2a.

### Update state file

For each PME in a new issue, add to state:
```json
{"status": "issue_pending", "title": "{issue_title}", "sf_writeback": false}
```

## Step 5: Update Stale Tracking Issues

For each **stale** PME, add a comment to its existing issue using `add-comment`:

```markdown
## PME Updated in Salesforce
This PME was last modified on **{LastModifiedDate}**, after this tracking issue was created.

| Field | Value |
|-------|-------|
| **Status** | {Escalation_Status__c} |
| **Priority** | {Priority__c} |
| **Accountable Team** | {Accountable_Team__c} |
| **Last Modified** | {LastModifiedDate} |

Please review the [PME in Salesforce](https://realpage.my.salesforce.com/{Id}).
```

Also add an SF comment entry: `"GitHub Issue updated with latest Salesforce state.\nRepository: {repo}"`

## Step 6: Finalize

### Post all SF comments

Call `sf-comment` exactly **once** with all collected comments as a `comments_json` array. Skip if no comments were collected.

### Save state file

Write the updated state to `/tmp/gh-aw/repo-memory/default/pme-state.json`. The framework automatically pushes this file to the `memory/pme-triage` branch after your session ends.

### Summary

Output a summary table:

```markdown
## PME Triage Run Summary
**Run parameters:** product_filter=`{filter}`, priority_filter=`{filter}`, lookback_days={N}, pme_limit={N}

| # | PME Name(s) | Type | WAD | Priority | Age | Action | SF Write-Back | Issue |
|---|-------------|------|-----|----------|-----|--------|---------------|-------|
```

**Totals:** PMEs fetched, already tracked, bug groups created, enhancement groups created, WAD-flagged, stale updated, SF comments posted.

---
# Safe-output handler for the failure path of a TFS work-item run: comment on
# the work item and transition its tag to agent-failed. Imported by the TFS
# implementer workflow; the job holds its own TFS_PAT scope so the agent step
# never sees the credential.

safe-outputs:
  jobs:
    tfs-record-failure:
      description: |
        Post a comment on the work item explaining what went wrong and
        transition the tag agent-in-progress -> agent-failed. Do NOT include
        any secret value (PAT, raw stderr that may contain credentials) in
        `reason`. Call this when you have claimed a work item but cannot
        complete it: build broken, work item too ambiguous, push rejected.
        Mutually exclusive with tfs_finalize_pull_request.
      inputs:
        work_item_id:
          type: number
          required: true
          description: "TFS work item ID to mark as failed."
        reason:
          type: string
          required: true
          description: "Short, secret-free explanation of what went wrong."
      runs-on: ubuntu-latest
      env:
        TFS_PAT: ${{ secrets.TFS_PAT }}
        TFS_BASE: ${{ vars.TFS_BASE }}
      steps:
        # See the matching guard in tfs-finalize-pull-request for the why.
        - name: Gate on threat-detection success
          if: needs.detection.result != 'success'
          env:
            DETECTION_RESULT: ${{ needs.detection.result }}
          run: |
            echo "ERROR: threat-detection did not succeed (result=${DETECTION_RESULT})." >&2
            echo "Refusing to write to TFS." >&2
            exit 1
        - name: Post comment and transition tag to agent-failed
          run: |
            set -euo pipefail
            TFS_B64="$(printf ':%s' "$TFS_PAT" | base64 -w0)"
            TFS_AUTH="Authorization: Basic $TFS_B64"

            # Enforce "exactly one" — see comment in tfs-finalize-pull-request.
            COUNT=$(jq -c '[.items[] | select(.type == "tfs_record_failure")] | length' "$GH_AW_AGENT_OUTPUT")
            if [ "$COUNT" -eq 0 ]; then
              echo "No tfs_record_failure intent emitted; nothing to do."
              exit 0
            fi
            if [ "$COUNT" -gt 1 ]; then
              echo "ERROR: agent emitted tfs_record_failure $COUNT times; expected exactly 1." >&2
              exit 1
            fi
            INTENT=$(jq -c '.items[] | select(.type == "tfs_record_failure")' "$GH_AW_AGENT_OUTPUT")

            WI_ID=$(echo "$INTENT"  | jq -r '.work_item_id // empty')
            REASON=$(echo "$INTENT" | jq -r '.reason // empty')

            # Defensive validation — see comment in tfs-finalize-pull-request.
            missing=""
            for var in WI_ID REASON; do
              if [ -z "${!var}" ]; then
                missing="$missing $var"
              fi
            done
            if [ -n "$missing" ]; then
              echo "ERROR: tfs_record_failure intent is missing required input(s):$missing" >&2
              echo "Raw intent payload: $INTENT" >&2
              echo "Work item will remain in agent-in-progress and require manual cleanup." >&2
              exit 1
            fi

            COMMENT=$(jq -n --arg t "$REASON" '{text: $t}')
            curl -fsS -X POST -H "$TFS_AUTH" -H "Content-Type: application/json" \
              --data "$COMMENT" \
              "$TFS_BASE/_apis/wit/workitems/$WI_ID/comments?api-version=6.0-preview.3" > /dev/null

            # Retry loop for the tag transition — same rev-mismatch race as in
            # tfs-finalize-pull-request (see the comment there). Less likely
            # on this path (no PR creation triggering async auto-linking), but
            # the comment POST above bumps System.CommentCount and a
            # concurrent human edit can bump the rev between our GET and
            # PATCH; without a retry the WI would be left stuck in
            # agent-in-progress. Rev mismatch is 412 on Azure DevOps cloud,
            # 409 + TF26071 on on-prem TFS.
            WI_PATCH_HTTP_CODE=""
            WI_PATCH_RESPONSE=$(mktemp)
            for attempt in 1 2 3 4 5 6 7 8; do
              WI=$(curl -fsS -H "$TFS_AUTH" "$TFS_BASE/_apis/wit/workitems/$WI_ID?api-version=6.0")
              REV=$(echo "$WI"  | jq -r '.rev')
              TAGS=$(echo "$WI" | jq -r '.fields["System.Tags"] // ""')
              NEW_TAGS=$(echo "$TAGS" | sed 's/agent-in-progress/agent-failed/g')
              PATCH=$(jq -n --argjson rev "$REV" --arg tags "$NEW_TAGS" \
                '[{"op":"test","path":"/rev","value":$rev},{"op":"replace","path":"/fields/System.Tags","value":$tags}]')
              WI_PATCH_HTTP_CODE=$(curl -sS -o "$WI_PATCH_RESPONSE" -w "%{http_code}" \
                -X PATCH -H "$TFS_AUTH" -H "Content-Type: application/json-patch+json" \
                --data "$PATCH" "$TFS_BASE/_apis/wit/workitems/$WI_ID?api-version=6.0")
              if [ "$WI_PATCH_HTTP_CODE" = "200" ]; then
                break
              fi
              if [ "$WI_PATCH_HTTP_CODE" = "412" ] || \
                 { [ "$WI_PATCH_HTTP_CODE" = "409" ] && \
                   grep -qE "TF26071|WorkItemRevisionMismatchException" "$WI_PATCH_RESPONSE"; }; then
                echo "WI rev moved between GET and PATCH (attempt $attempt, rev was $REV, HTTP $WI_PATCH_HTTP_CODE) — refetching and retrying."
                sleep 1
                continue
              fi
              break
            done
            if [ "$WI_PATCH_HTTP_CODE" != "200" ]; then
              echo "ERROR: tag transition to agent-failed failed (HTTP $WI_PATCH_HTTP_CODE) on WI #$WI_ID after retries." >&2
              echo "TFS response:" >&2
              cat "$WI_PATCH_RESPONSE" >&2
              echo "The failure comment was posted; flip the tag to agent-failed manually." >&2
              rm -f "$WI_PATCH_RESPONSE"
              exit 1
            fi
            rm -f "$WI_PATCH_RESPONSE"

            echo "Recorded failure on work item #$WI_ID"
---

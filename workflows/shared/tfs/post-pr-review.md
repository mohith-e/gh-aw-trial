---
# Safe-output handler that writes an AI review back to a TFS pull request:
# one summary thread carrying the reviewed-SHA marker, an optional reply on
# the /review-ai command thread, and up to eight inline findings. Imported by
# the TFS PR-review workflow; the job holds its own PAT scope so the agent
# step never sees the credential.

safe-outputs:
  jobs:
    tfs-post-pr-review:
      description: |
        Post the AI code review onto the TFS pull request as comment thread(s):
        one summary thread (carrying the reviewed-SHA marker) plus up to 8
        inline threads anchored to specific lines. Call exactly once per run,
        after you have finished analyzing the diff. This is advisory only — it
        posts comments, it never votes on or completes the PR.
      inputs:
        pr_id:
          type: number
          required: true
          description: "TFS pull request ID being reviewed (from the workspace JSON)."
        source_commit_sha:
          type: string
          required: true
          description: "The PR's source_commit_sha from the workspace JSON (40-char hex). Recorded in the summary comment as the idempotency marker and a human-readable 'reviewed at commit' line. Do NOT invent or alter it."
        summary_markdown:
          type: string
          required: true
          description: "The summary review body (markdown): verdict, per-dimension score table, and prioritized findings. Posted as one PR-level comment thread."
        inline_findings_json:
          type: string
          required: true
          description: "A JSON array (as a string) of up to 8 inline findings, each an object {\"path\": \"/repo/relative/path\", \"line\": <int>, \"severity\": \"high|medium|low\", \"summary\": \"<one paragraph>\"}. `path` is repo-relative with a leading slash; `line` is a line in the new (post-change) file. Pass \"[]\" if there are no inline findings. Inline posting is best-effort; every finding also appears in summary_markdown."
        command_thread_id:
          type: string
          required: false
          description: "The command_thread_id from the workspace JSON, passed through unchanged. Non-empty only when this run was triggered by a /review-ai comment; the handler then tags the review served for that command and replies on the command thread. Leave empty (or omit) for scheduled reviews."
      runs-on: ubuntu-latest
      # This handler's own TFS writes go via TFS_REVIEW_PAT, never
      # GITHUB_TOKEN — but gh-aw's injected agent-artifact download step
      # (which fetches $GH_AW_AGENT_OUTPUT) still runs in this job and needs
      # read scope, so `contents: read` is kept rather than `permissions: {}`
      # (matching tfs-implement.md's handler, which keeps it for the same
      # reason).
      permissions:
        contents: read
      env:
        # Same TFS_REVIEW_PAT-preferred, TFS_PAT-fallback precedence as the
        # select step — both must resolve to the same identity for a given
        # run, which `||` guarantees since it's evaluated the same way here.
        TFS_REVIEW_PAT: ${{ secrets.TFS_REVIEW_PAT || secrets.TFS_PAT }}
        TFS_BASE: ${{ vars.TFS_BASE }}
        TFS_REPO: ${{ vars.TFS_REPO }}
      steps:
        # gh-aw v0.76.x emits `if: (!cancelled()) && ...` on custom safe-output
        # jobs, which overrides GitHub Actions' default needs-success gating.
        # Guard explicitly so a failed threat-detection blocks the TFS write.
        # Delete when upstream lands native gating on custom safe-output jobs.
        - name: Gate on threat-detection success
          if: needs.detection.result != 'success'
          env:
            DETECTION_RESULT: ${{ needs.detection.result }}
          run: |
            echo "ERROR: threat-detection did not succeed (result=${DETECTION_RESULT})." >&2
            echo "Refusing to write to TFS." >&2
            exit 1
        - name: Post review thread(s) to the TFS PR
          run: |
            set -euo pipefail
            TFS_B64="$(printf ':%s' "$TFS_REVIEW_PAT" | base64 -w0)"
            TFS_AUTH="Authorization: Basic $TFS_B64"

            # Enforce "exactly one" — gh-aw's safe-outputs.jobs.* schema does
            # not accept `max: 1`, so count here.
            COUNT=$(jq -c '[.items[] | select(.type == "tfs_post_pr_review")] | length' "$GH_AW_AGENT_OUTPUT")
            if [ "$COUNT" -eq 0 ]; then echo "No tfs_post_pr_review intent emitted; nothing to do."; exit 0; fi
            if [ "$COUNT" -gt 1 ]; then echo "ERROR: expected exactly 1 tfs_post_pr_review intent, got $COUNT." >&2; exit 1; fi
            INTENT=$(jq -c '.items[] | select(.type == "tfs_post_pr_review")' "$GH_AW_AGENT_OUTPUT")

            PR_ID=$(echo "$INTENT" | jq -r '.pr_id // empty')
            SRC_SHA=$(echo "$INTENT" | jq -r '.source_commit_sha // empty')
            SUMMARY=$(echo "$INTENT" | jq -r '.summary_markdown // empty')
            INLINE=$(echo "$INTENT" | jq -c '.inline_findings_json // "[]" | fromjson? // []')
            CMD_THREAD=$(echo "$INTENT" | jq -r '.command_thread_id // empty')

            # Idempotency and /review-ai dedup key off the marker patterns
            # below found in *existing* comment content. Strip any
            # look-alike text the agent itself put in summary_markdown so
            # prompt-injected output cannot spoof a marker for an arbitrary
            # SHA/thread and suppress a future review. The handler-generated
            # FOOTER below is the only place these markers are allowed to
            # come from.
            SUMMARY=$(printf '%s' "$SUMMARY" | sed -E \
              -e 's/<!--[[:space:]]*agent-(reviewed-sha|review-command)[[:space:]]*:[^>]*-->//g' \
              -e 's/agent-(reviewed-sha|review-command)[[:space:]]*:[^[:space:]]*//g')

            # Defensive validation of agent-supplied fields.
            for pair in "PR_ID=$PR_ID" "SRC_SHA=$SRC_SHA" "SUMMARY=$SUMMARY"; do
              name="${pair%%=*}"; val="${pair#*=}"
              [ -n "$val" ] || { echo "ERROR: missing required field $name." >&2; exit 1; }
            done
            case "$PR_ID" in *[!0-9]*) echo "ERROR: pr_id '$PR_ID' is not numeric." >&2; exit 1;; esac
            if ! printf '%s' "$SRC_SHA" | grep -Eq '^[0-9a-f]{40}$'; then
              echo "ERROR: source_commit_sha '$SRC_SHA' is not a 40-char hex SHA." >&2; exit 1
            fi
            case "$CMD_THREAD" in *[!0-9]*) CMD_THREAD="";; esac  # ignore anything non-numeric

            # Read-only retry options — same rationale as the select step's
            # CURL_READ (see there). Applied ONLY to the two GETs below. The
            # thread-creating POSTs further down stay deliberately un-retried:
            # one that times out after TFS already accepted it would post the
            # review twice.
            CURL_READ=(--connect-timeout 20 --retry 3 --retry-delay 5 --retry-all-errors)

            REPO_ID=$(curl -fsS "${CURL_READ[@]}" -H "$TFS_AUTH" \
              "$TFS_BASE/_apis/git/repositories/$TFS_REPO?api-version=6.0" | jq -r '.id')
            THREADS_URL="$TFS_BASE/_apis/git/repositories/$REPO_ID/pullRequests/$PR_ID/threads?api-version=6.0"

            # Idempotency re-check at write time (guards overlapping runs racing
            # the same PR before either posted). A command-triggered review is
            # deduped by its command thread id; a scheduled one by the SHA.
            SHA_MARKER="agent-reviewed-sha: $SRC_SHA"
            EXISTING=$(curl -fsS "${CURL_READ[@]}" -H "$TFS_AUTH" "$THREADS_URL")
            if [ -n "$CMD_THREAD" ]; then
              CMD_MARKER="agent-review-command: $CMD_THREAD"
              if echo "$EXISTING" | jq -e --arg m "$CMD_MARKER" \
                   '[.value[]?.comments[]?.content // ""] | any(contains($m))' > /dev/null; then
                echo "PR $PR_ID: /review-ai command (thread $CMD_THREAD) already served — skipping duplicate post."
                exit 0
              fi
            else
              if echo "$EXISTING" | jq -e --arg m "$SHA_MARKER" \
                   '[.value[]?.comments[]?.content // ""] | any(contains($m))' > /dev/null; then
                echo "PR $PR_ID already has a review for ${SRC_SHA:0:8} — skipping duplicate post."
                exit 0
              fi
            fi

            # ---------- Post the summary thread (carries the marker[s]) ----------
            # The SHA marker is always present (machine dedup key + human "reviewed
            # at commit" context). A command-triggered review also carries the
            # command marker so that /review-ai request is not served twice.
            if [ -n "$CMD_THREAD" ]; then
              TRIGGER_NOTE="Requested via \`/review-ai\`. "
              CMD_MARKER_LINE=$(printf '\n<!-- agent-review-command: %s -->' "$CMD_THREAD")
            else
              TRIGGER_NOTE=""
              CMD_MARKER_LINE=""
            fi
            FOOTER=$(printf '\n\n---\n_🤖 Automated review by `tfs-review-pr`. %sReviewed at source commit `%s`. This is a second set of eyes, not a gate — a human review is still required. To opt out of scheduled reviews, label the PR `skip-ai-review`; comment `/review-ai` for an on-demand re-review._\n<!-- %s -->%s' "$TRIGGER_NOTE" "${SRC_SHA:0:8}" "$SHA_MARKER" "$CMD_MARKER_LINE")
            BODY="${SUMMARY}${FOOTER}"
            THREAD=$(jq -n --arg body "$BODY" \
              '{comments:[{parentCommentId:0, content:$body, commentType:1}], status:1}')
            HTTP=$(curl -sS -o /tmp/thread.json -w "%{http_code}" \
              -X POST -H "$TFS_AUTH" -H "Content-Type: application/json" \
              --data "$THREAD" "$THREADS_URL")
            if [ "$HTTP" != "200" ] && [ "$HTTP" != "201" ]; then
              echo "ERROR: summary thread POST returned HTTP $HTTP" >&2; cat /tmp/thread.json >&2; exit 1
            fi
            echo "Posted summary review thread on PR $PR_ID."

            # If a /review-ai command triggered this run, reply on that command
            # thread so the requester is notified. Best-effort — a failure here
            # does not undo the review that was already posted above.
            if [ -n "$CMD_THREAD" ]; then
              REPLY=$(jq -n '{content: "✅ AI review posted — see the summary thread on this PR.", parentCommentId: 1, commentType: 1}')
              RHTTP=$(curl -sS -o /dev/null -w "%{http_code}" \
                -X POST -H "$TFS_AUTH" -H "Content-Type: application/json" \
                --data "$REPLY" \
                "$TFS_BASE/_apis/git/repositories/$REPO_ID/pullRequests/$PR_ID/threads/$CMD_THREAD/comments?api-version=6.0")
              if [ "$RHTTP" = "200" ] || [ "$RHTTP" = "201" ]; then
                echo "Replied on /review-ai command thread $CMD_THREAD."
              else
                echo "::warning title=Command reply failed::Could not reply on /review-ai thread $CMD_THREAD (HTTP $RHTTP). The review itself was posted."
              fi
            fi

            # ---------- Post inline threads (best-effort) ----------
            # TFS anchors a thread to a line via threadContext (filePath +
            # rightFileStart/End). A malformed line/path yields an HTTP 4xx we
            # surface as a warning rather than failing the whole review — the
            # finding is already in the summary above.
            N=$(echo "$INLINE" | jq 'length')
            echo "Inline findings: $N"
            if [ "$N" -gt 8 ]; then
              echo "::warning title=Too many inline findings::Agent emitted $N inline findings; contract caps at 8. Posting only the first 8 — all findings remain in the summary review."
              N=8
            fi
            j=0
            while [ "$j" -lt "$N" ]; do
              F=$(echo "$INLINE" | jq -c ".[$j]")
              j=$((j + 1))
              FPATH=$(echo "$F" | jq -r '.path // empty')
              LINE=$(echo "$F" | jq -r '.line // empty')
              SEV=$(echo "$F" | jq -r '.severity // "low"')
              FSUM=$(echo "$F" | jq -r '.summary // empty')
              [ -n "$FPATH" ] && [ -n "$FSUM" ] || { echo "  finding $j: missing path/summary — skip."; continue; }
              case "$LINE" in ''|*[!0-9]*) echo "  finding $j: non-numeric line — skip."; continue;; esac
              case "$FPATH" in /*) ;; *) FPATH="/$FPATH";; esac
              CBODY="[$SEV] $FSUM"
              ITHREAD=$(jq -n --arg body "$CBODY" --arg path "$FPATH" --argjson line "$LINE" \
                '{comments:[{parentCommentId:0, content:$body, commentType:1}], status:1,
                  threadContext:{filePath:$path,
                    rightFileStart:{line:$line, offset:1},
                    rightFileEnd:{line:$line, offset:1}}}')
              IHTTP=$(curl -sS -o /tmp/ithread.json -w "%{http_code}" \
                -X POST -H "$TFS_AUTH" -H "Content-Type: application/json" \
                --data "$ITHREAD" "$THREADS_URL")
              if [ "$IHTTP" = "200" ] || [ "$IHTTP" = "201" ]; then
                echo "  posted inline thread on ${FPATH}:${LINE}"
              else
                echo "::warning title=Inline comment failed::Could not post inline thread on ${FPATH}:${LINE} (HTTP $IHTTP). The finding is included in the summary review."
              fi
            done
            echo "Review posting complete for PR $PR_ID."
---

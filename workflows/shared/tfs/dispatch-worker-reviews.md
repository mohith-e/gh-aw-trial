---
# Safe-output handler that fans a coordinator run out into per-PR worker runs.
# It lives in a handler job rather than a pre-agent step because gh-aw rejects
# any write permission (including actions: write) on the agent job. Imported by
# the TFS PR-review workflow.

safe-outputs:
  jobs:
    tfs-dispatch-worker-reviews:
      description: |
        COORDINATOR path only. Scan TFS for up to TFS_REVIEW_BATCH_SIZE
        distinct eligible PRs (same rules as a worker's own schedule-path
        scan: /review-ai commands first, then non-draft/non-skip-labeled/
        not-yet-reviewed PRs, oldest first) and dispatch each as its own
        isolated workflow_dispatch worker run. Call exactly once per
        coordinator run — this job does its own TFS scan rather than
        trusting a list from the agent, since the scan is fully
        deterministic and doesn't benefit from being round-tripped through
        the model; `acknowledged` exists only because a safe-output needs at
        least one field, not because its value matters.
      inputs:
        acknowledged:
          type: boolean
          required: true
          description: "Always pass true. This job ignores the value — it performs its own TFS scan rather than trusting anything from the agent — but the tool call needs at least one declared field."
      # Deterministic coordinator-only gate — gh-aw already restricts this job
      # to runs where the agent emitted a matching tfs_dispatch_worker_reviews
      # intent, but that alone trusts the model's self-reported mode. A
      # worker run (inputs.pr_id set) could still emit that same intent if
      # mis-prompted or compromised, which would fire an unwanted scan+dispatch
      # from a worker context. inputs.pr_id is set by the trigger itself, not
      # the agent, so this can't be spoofed by anything the model emits.
      # Written WITHOUT ${{ }} deliberately: gh-aw ANDs this onto its own
      # bare-expression base gate ((!cancelled()) && ... && contains(...)) —
      # wrapping this in ${{ }} would mix bare and wrapped expression syntax
      # in the same if:, which GitHub Actions rejects.
      if: inputs.pr_id == ''
      runs-on: ubuntu-latest
      # actions: write is what lets this job dispatch worker runs — safe here
      # specifically because this is NOT the agent job (see the permissions
      # block's comment). contents: read is kept for the same reason as
      # tfs-post-pr-review's handler: gh-aw's injected agent-artifact
      # download step still runs in this job.
      permissions:
        contents: read
        actions: write
      env:
        TFS_REVIEW_PAT: ${{ secrets.TFS_REVIEW_PAT || secrets.TFS_PAT }}
        TFS_BASE: ${{ vars.TFS_BASE }}
        TFS_REPO: ${{ vars.TFS_REPO }}
        TFS_REVIEW_SCHEDULE_ENABLED: ${{ vars.TFS_REVIEW_SCHEDULE_ENABLED }}
        TFS_REVIEW_MAX_AGE_DAYS: ${{ vars.TFS_REVIEW_MAX_AGE_DAYS }}
        # OPTIONAL fan-out width (positive integer), read only here — this is
        # the job that actually scans and dispatches. Instead of reviewing the
        # first eligible match itself, a coordinator run dispatches up to this
        # many eligible PRs as separate, isolated workflow_dispatch WORKER runs
        # (each with pr_id set), so multiple PRs get reviewed from one tick
        # instead of one. Unset or invalid = 5. Start modest and raise it while
        # watching worker queue times — a large batch concentrates dispatch
        # demand instantly, and Anthropic/TFS/runner capacity may bite before
        # the batch size does.
        TFS_REVIEW_BATCH_SIZE: ${{ vars.TFS_REVIEW_BATCH_SIZE }}
        # workflow_dispatch is an explicit, documented exception to
        # GITHUB_TOKEN's no-recursive-triggers rule (see
        # https://github.blog/changelog/2022-09-08-github-actions-use-github_token-with-workflow_dispatch-and-repository_dispatch/),
        # so this reliably creates new runs rather than silently no-opping.
        GH_TOKEN: ${{ github.token }}
      steps:
        # Same rationale as tfs-post-pr-review's identical gate — see there.
        - name: Gate on threat-detection success
          if: needs.detection.result != 'success'
          env:
            DETECTION_RESULT: ${{ needs.detection.result }}
          run: |
            echo "ERROR: threat-detection did not succeed (result=${DETECTION_RESULT})." >&2
            echo "Refusing to scan/dispatch." >&2
            exit 1
        - name: Scan TFS and dispatch worker runs
          run: |
            set -euo pipefail
            COUNT_INTENT=$(jq -c '[.items[] | select(.type == "tfs_dispatch_worker_reviews")] | length' "$GH_AW_AGENT_OUTPUT")
            if [ "$COUNT_INTENT" -eq 0 ]; then echo "No tfs_dispatch_worker_reviews intent emitted; nothing to do."; exit 0; fi
            if [ "$COUNT_INTENT" -gt 1 ]; then echo "ERROR: expected exactly 1 tfs_dispatch_worker_reviews intent, got $COUNT_INTENT." >&2; exit 1; fi

            TFS_B64="$(printf ':%s' "$TFS_REVIEW_PAT" | base64 -w0)"
            TFS_AUTH="Authorization: Basic $TFS_B64"

            # Read-only retry options — same rationale as the select step's
            # CURL_READ (see there). This job is where the observed
            # `curl: (28)` coordinator failures actually happened: every call
            # it makes to TFS is a GET, so all of them are retried, and this
            # job posts nothing to TFS at all.
            CURL_READ=(--connect-timeout 20 --retry 3 --retry-delay 5 --retry-all-errors)

            # ---------- 1. Resolve repo id ----------
            REPO_ID=$(curl -fsS "${CURL_READ[@]}" -H "$TFS_AUTH" \
              "$TFS_BASE/_apis/git/repositories/$TFS_REPO?api-version=6.0" | jq -r '.id')
            if [ -z "$REPO_ID" ] || [ "$REPO_ID" = "null" ]; then
              echo "::error::Could not resolve TFS repo id for '$TFS_REPO'." >&2; exit 1
            fi

            # ---------- 2. Build the candidate PR list (oldest first) ----------
            # Same scan a worker's own schedule path uses — see that step's
            # comment for why $top=100 and oldest-first draining are the
            # intended scope controls.
            CANDIDATES=$(curl -fsS "${CURL_READ[@]}" -H "$TFS_AUTH" -G \
              --data-urlencode "searchCriteria.status=active" \
              --data-urlencode "\$top=100" \
              "$TFS_BASE/_apis/git/repositories/$REPO_ID/pullrequests?api-version=6.0" \
              | jq -c '[.value[]] | sort_by(.creationDate)')
            COUNT=$(echo "$CANDIDATES" | jq 'length')
            echo "Active PR candidates: $COUNT"

            # ---------- 3. Fan-out width ----------
            BATCH_SIZE=5
            if [ -n "${TFS_REVIEW_BATCH_SIZE:-}" ]; then
              case "$TFS_REVIEW_BATCH_SIZE" in
                ''|*[!0-9]*|0) echo "::warning::TFS_REVIEW_BATCH_SIZE='${TFS_REVIEW_BATCH_SIZE}' is not a positive integer — using default of $BATCH_SIZE." ;;
                *) BATCH_SIZE="$TFS_REVIEW_BATCH_SIZE" ;;
              esac
            fi
            echo "Fan-out width: up to $BATCH_SIZE worker run(s) this tick."

            # ---------- 4. Collect up to BATCH_SIZE distinct eligible PRs ----------
            # Identical eligibility rules to a worker's own schedule-path scan
            # (COMMAND path first, then SCHEDULE path with its two admin
            # knobs) — the only difference is COLLECTING matches instead of
            # stopping at the first one. Kept as a literal copy (not a shared
            # function) so the two scans can't silently drift apart without
            # the duplication catching a reviewer's eye; if you change one,
            # change the other.
            SCHEDULE_ENABLED="true"
            case "$(printf '%s' "${TFS_REVIEW_SCHEDULE_ENABLED:-}" | tr '[:upper:]' '[:lower:]')" in
              false|0|no|off) SCHEDULE_ENABLED="false" ;;
            esac
            CUTOFF=""
            if [ -n "${TFS_REVIEW_MAX_AGE_DAYS:-}" ]; then
              case "$TFS_REVIEW_MAX_AGE_DAYS" in
                ''|*[!0-9]*) echo "::warning::TFS_REVIEW_MAX_AGE_DAYS='${TFS_REVIEW_MAX_AGE_DAYS}' is not a positive integer — ignoring (no age filter)." ;;
                *) CUTOFF=$(date -u -d "${TFS_REVIEW_MAX_AGE_DAYS} days ago" +%Y-%m-%dT%H:%M:%SZ)
                   echo "Schedule age filter: only PRs created on/after $CUTOFF (last ${TFS_REVIEW_MAX_AGE_DAYS}d)." ;;
              esac
            fi
            [ "$SCHEDULE_ENABLED" = "true" ] || echo "Scheduled scan DISABLED (TFS_REVIEW_SCHEDULE_ENABLED=false); only /review-ai PRs are collected this tick."

            TO_DISPATCH=()
            i=0
            while [ "$i" -lt "$COUNT" ] && [ "${#TO_DISPATCH[@]}" -lt "$BATCH_SIZE" ]; do
              PR=$(echo "$CANDIDATES" | jq -c ".[$i]")
              i=$((i + 1))
              PR_ID=$(echo "$PR" | jq -r '.pullRequestId')
              IS_DRAFT=$(echo "$PR" | jq -r '.isDraft // false')
              SRC_SHA=$(echo "$PR" | jq -r '.lastMergeSourceCommit.commitId // ""')
              HAS_SKIP_LABEL=$(echo "$PR" | jq -r '[.labels[]?.name // empty] | any(. == "skip-ai-review")')

              THREADS=$(curl -fsS "${CURL_READ[@]}" -H "$TFS_AUTH" \
                "$TFS_BASE/_apis/git/repositories/$REPO_ID/pullRequests/$PR_ID/threads?api-version=6.0")

              # COMMAND path — identical matching/dedup rules to a worker run.
              SERVED_CMDS=$(echo "$THREADS" | jq -r '[.value[]?.comments[]?.content // ""] | join("\n")' \
                | grep -oE 'agent-review-command: [0-9]+' | grep -oE '[0-9]+$' | sort -u || true)
              CMD_IDS=$(echo "$THREADS" | jq -r '.value[]?
                | select((.comments[0].content // "")
                    | test("(^|[^a-zA-Z0-9/])/review-ai([^a-zA-Z0-9]|$)"; "i"))
                | select([.comments[]?.content // ""] | join("\n")
                    | test("agent-reviewed-sha:|agent-review-command:") | not)
                | .id')
              CMD_THREAD=""
              for cid in $CMD_IDS; do
                if ! echo "$SERVED_CMDS" | grep -qx "$cid"; then CMD_THREAD="$cid"; break; fi
              done
              if [ -n "$CMD_THREAD" ]; then
                if [ -z "$SRC_SHA" ]; then
                  echo "PR $PR_ID: /review-ai requested but no lastMergeSourceCommit yet — skip this tick."; continue
                fi
                echo "PR $PR_ID: /review-ai command (thread $CMD_THREAD) — queuing for dispatch (bypasses draft/label/dedup)."
                TO_DISPATCH+=("$PR_ID")
                continue
              fi

              # SCHEDULE path.
              if [ "$SCHEDULE_ENABLED" != "true" ]; then
                echo "PR $PR_ID: scheduled scan disabled — skip (comment /review-ai to force a review)."; continue
              fi
              if [ -n "$CUTOFF" ]; then
                PR_CREATED=$(echo "$PR" | jq -r '.creationDate // ""')
                if [ "$(echo "$PR" | jq -r --arg c "$CUTOFF" '((.creationDate // "") | sub("\\.[0-9]+Z$"; "Z")) < $c')" = "true" ]; then
                  echo "PR $PR_ID: created $PR_CREATED is older than the ${TFS_REVIEW_MAX_AGE_DAYS}d cutoff — skip (comment /review-ai to force)."; continue
                fi
              fi
              [ "$IS_DRAFT" = "true" ] && { echo "PR $PR_ID: draft (no /review-ai) — skip."; continue; }
              [ "$HAS_SKIP_LABEL" = "true" ] && { echo "PR $PR_ID: labeled skip-ai-review — skip."; continue; }
              if [ -z "$SRC_SHA" ]; then
                echo "PR $PR_ID: no lastMergeSourceCommit yet (merge not computed) — skip this tick."; continue
              fi
              if echo "$THREADS" | jq -e --arg m "agent-reviewed-sha: $SRC_SHA" \
                   '[.value[]?.comments[]?.content // ""] | any(contains($m))' > /dev/null; then
                echo "PR $PR_ID: already reviewed at source commit ${SRC_SHA:0:8} — skip."
                continue
              fi

              echo "PR $PR_ID: eligible at ${SRC_SHA:0:8} — queuing for dispatch."
              TO_DISPATCH+=("$PR_ID")
            done

            echo "Collected ${#TO_DISPATCH[@]} PR(s) to dispatch: ${TO_DISPATCH[*]:-<none>}"

            # ---------- 5. Dispatch one isolated workflow_dispatch run per PR ----------
            # Self-discover this workflow's own file path from
            # GITHUB_WORKFLOW_REF (format:
            # owner/repo/.github/workflows/<file>@ref, a default GitHub
            # Actions env var) rather than hardcoding a filename, since
            # consumers may name their compiled stub differently.
            WORKFLOW_FILE=$(printf '%s' "$GITHUB_WORKFLOW_REF" | sed -E 's#^[^/]+/[^/]+/\.github/workflows/##; s#@.*$##')
            DISPATCHED=0
            # --ref pins workers to the SAME ref this coordinator run used.
            # Without it, `gh workflow run` dispatches on the repo's default
            # branch regardless of what triggered the coordinator — harmless
            # for a real schedule/dispatch tick (which only ever fires off
            # the default branch anyway), but it silently sends worker runs
            # to the wrong branch for a manual coordinator dispatch on a
            # non-default ref (e.g. testing this workflow itself before
            # merge). GITHUB_REF_NAME is a default Actions env var.
            for pr_id in ${TO_DISPATCH[@]+"${TO_DISPATCH[@]}"}; do
              if gh workflow run "$WORKFLOW_FILE" --repo "$GITHUB_REPOSITORY" --ref "$GITHUB_REF_NAME" -f "pr_id=$pr_id"; then
                DISPATCHED=$((DISPATCHED + 1))
              else
                echo "::warning title=Dispatch failed::Could not dispatch a worker run for PR $pr_id; it remains eligible and will be retried next tick."
              fi
            done
            echo "Dispatched $DISPATCHED worker run(s)."
---

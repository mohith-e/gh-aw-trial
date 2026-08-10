---
# Safe-output handler for the happy path of a TFS work-item run: push the
# agent's format-patch to TFS, open the PR, post the review-notes thread, link
# the work item, and transition its tag. Imported by the TFS implementer
# workflow; the job holds its own TFS_PAT scope so the agent step never sees
# the credential.

safe-outputs:
  jobs:
    tfs-finalize-pull-request:
      description: |
        Open the PR in TFS, post the PR review-notes thread, link the work
        item to the PR via an ArtifactLink relation, and transition the work
        item tag agent-in-progress -> agent-pr-opened. Call exactly once per
        run on the happy path, after the branch has been pushed to TFS.
        Mutually exclusive with tfs_record_failure.
      inputs:
        work_item_id:
          type: number
          required: true
          description: "TFS work item ID being closed out."
        branch:
          type: string
          required: true
          description: "Branch name already pushed to TFS, e.g. agent/wi-12345-fix-foo."
        base_sha:
          type: string
          required: true
          description: "Target-branch SHA the pre-agent step snapshotted before the agent ran. The handler branches from this exact commit so the patch always applies cleanly, even if the target branch moved during the run. Must be a 40-char hex SHA reachable from the target branch."
        title:
          type: string
          required: true
          description: "PR title. The handler truncates to 100 chars."
        description:
          type: string
          required: true
          description: "PR description body (markdown)."
        pr_review_notes_markdown:
          type: string
          required: true
          description: "Body of the PR review-notes thread (markdown). Posted as a comment thread on the TFS PR for the human reviewer — explains what changed, what was tested, confidence, and what to double-check."
      runs-on: ubuntu-latest
      # gh-aw safe-output handler jobs default to `permissions: {}` (no scopes).
      # `contents: read` covers two things here: gh-aw's agent-artifact download
      # (which carries the format-patch this job consumes) and the mirror clone
      # below when TFS_USE_MIRROR selects it. The TFS write goes via TFS_PAT,
      # never this token.
      permissions:
        contents: read
      env:
        TFS_PAT: ${{ secrets.TFS_PAT }}
        GITHUB_TOKEN: ${{ github.token }}
        TFS_BASE: ${{ vars.TFS_BASE }}
        TFS_TARGET_BRANCH: ${{ vars.TFS_TARGET_BRANCH }}
        TFS_REPO: ${{ vars.TFS_REPO }}
        TFS_USE_MIRROR: ${{ vars.TFS_USE_MIRROR }}
      steps:
        # gh-aw v0.76.x emits `if: (!cancelled()) && ...` on custom safe-output
        # jobs, which overrides GitHub Actions' default needs-success gating.
        # Built-in handlers add `&& needs.detection.result == 'success'`; the
        # compiler does not do that for custom jobs. Guard explicitly so a
        # failed threat-detection blocks TFS writes. Delete when upstream
        # lands native gating on custom safe-output jobs.
        - name: Gate on threat-detection success
          if: needs.detection.result != 'success'
          env:
            DETECTION_RESULT: ${{ needs.detection.result }}
          run: |
            echo "ERROR: threat-detection did not succeed (result=${DETECTION_RESULT})." >&2
            echo "Refusing to write to TFS." >&2
            exit 1
        - name: Push branch to TFS, open PR, post PR review-notes thread, link WI, transition tag
          run: |
            set -euo pipefail
            TFS_B64="$(printf ':%s' "$TFS_PAT" | base64 -w0)"
            TFS_AUTH="Authorization: Basic $TFS_B64"

            # Enforce "exactly one" — gh-aw's safe-outputs.jobs.* schema does
            # not accept `max: 1`, so we count here instead.
            COUNT=$(jq -c '[.items[] | select(.type == "tfs_finalize_pull_request")] | length' "$GH_AW_AGENT_OUTPUT")
            if [ "$COUNT" -eq 0 ]; then
              echo "No tfs_finalize_pull_request intent emitted; nothing to do."
              exit 0
            fi
            if [ "$COUNT" -gt 1 ]; then
              echo "ERROR: agent emitted tfs_finalize_pull_request $COUNT times; expected exactly 1." >&2
              echo "Each run must end in exactly one of {finalize, record-failure, noop}." >&2
              exit 1
            fi
            INTENT=$(jq -c '.items[] | select(.type == "tfs_finalize_pull_request")' "$GH_AW_AGENT_OUTPUT")

            WI_ID=$(echo "$INTENT"   | jq -r '.work_item_id // empty')
            BRANCH=$(echo "$INTENT"  | jq -r '.branch // empty')
            BASE_SHA=$(echo "$INTENT" | jq -r '.base_sha // empty')
            TITLE=$(echo "$INTENT"   | jq -r '.title // empty' | cut -c1-100)
            PR_DESC=$(echo "$INTENT" | jq -r '.description // empty')
            REVIEW_NOTES=$(echo "$INTENT" | jq -r '.pr_review_notes_markdown // empty')

            # Defensive validation. The MCP SDK enforces the inputs schema's
            # `required:` fields at the tool boundary, so under normal operation
            # every field below is non-empty. This block exists so the handler
            # fails loudly rather than POSTing garbage to TFS if some future
            # gh-aw change relaxes that enforcement.
            missing=""
            for var in WI_ID BRANCH BASE_SHA TITLE PR_DESC REVIEW_NOTES; do
              if [ -z "${!var}" ]; then
                missing="$missing $var"
              fi
            done
            if [ -n "$missing" ]; then
              echo "ERROR: tfs_finalize_pull_request intent is missing required input(s):$missing" >&2
              echo "Raw intent payload (no secrets here — these are agent-emitted values):" >&2
              echo "$INTENT" >&2
              echo "Work item will remain in agent-in-progress and require manual cleanup." >&2
              exit 1
            fi

            # base_sha format check. The pre-agent step writes a full 40-char
            # hex SHA from `git rev-parse`; reject anything else before we
            # use it in `git checkout`. Ancestry against the target branch is
            # verified after clone, below.
            if ! [[ "$BASE_SHA" =~ ^[0-9a-f]{40}$ ]]; then
              echo "ERROR: base_sha is not a 40-char hex SHA: '$BASE_SHA'" >&2
              exit 1
            fi

            # ---------- Push the agent's commit to TFS ----------
            # The agent ran without TFS credentials; its commit lives only as a
            # format-patch file in its artifact. gh-aw bundles the agent's
            # /tmp/gh-aw/agent/ tree into the artifact, so the patch the agent
            # wrote to /tmp/gh-aw/agent/aw-tfs-wi-<id>.patch lands at
            # safe-jobs/agent/aw-tfs-wi-<id>.patch after download. We clone the
            # target branch fresh, git-am the patch on top of the snapshotted
            # base, and push the branch back to TFS.
            PATCH_FILE="$RUNNER_TEMP/gh-aw/safe-jobs/agent/aw-tfs-wi-${WI_ID}.patch"
            if [ ! -f "$PATCH_FILE" ]; then
              echo "ERROR: expected patch file at $PATCH_FILE was not in the agent artifact." >&2
              echo "The agent must write /tmp/gh-aw/agent/aw-tfs-wi-<id>.patch in Step 5." >&2
              ls -la "$RUNNER_TEMP/gh-aw/safe-jobs/" "$RUNNER_TEMP/gh-aw/safe-jobs/agent/" 2>&1 | sed 's/^/  /' >&2
              exit 1
            fi

            PUSH_STAGING="$RUNNER_TEMP/push-staging"
            TFS_HOST="${TFS_BASE#*://}"; TFS_HOST="${TFS_HOST%%/*}"

            # Clone the target branch. Transport is selected by TFS_USE_MIRROR
            # exactly as in the claim step — see the comment on that variable
            # in shared/tfs/core.md. Unlike the claim step this side keeps FULL
            # history in both modes: we branch from base_sha, the tip the agent
            # snapshotted, and a shallow copy could miss it if the target moved
            # during the run. base_sha is an ancestor of the current target tip
            # (the branch only advances under branch protection), so a full
            # fetch of the target branch is guaranteed to contain it.
            MIRROR_MODE=auto
            case "$(printf '%s' "${TFS_USE_MIRROR:-}" | tr '[:upper:]' '[:lower:]')" in
              "")              MIRROR_MODE=auto ;;
              true|1|yes|on)   MIRROR_MODE=on ;;
              false|0|no|off)  MIRROR_MODE=off ;;
              *) echo "::warning title=Unrecognized TFS_USE_MIRROR::'${TFS_USE_MIRROR}' is not one of true/false — treating it as unset (probe for the mirror)." ;;
            esac

            MIRROR_PRESENT=false
            if [ "$MIRROR_MODE" != "off" ]; then
              GH_REPO_URL="https://github.com/${GITHUB_REPOSITORY}.git"
              MIRROR_BRANCH="tfs-mirror/${TFS_TARGET_BRANCH}"
              # See the claim step for why Basic auth (not Bearer) is required.
              GH_B64="$(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 -w0)"
              GH_AUTH="Authorization: Basic $GH_B64"
              if git -c "http.https://github.com/.extraheader=$GH_AUTH" \
                     ls-remote --exit-code --heads "$GH_REPO_URL" "$MIRROR_BRANCH" > /dev/null; then
                MIRROR_PRESENT=true
                git -c "http.https://github.com/.extraheader=$GH_AUTH" \
                    clone --branch "$MIRROR_BRANCH" --single-branch "$GH_REPO_URL" "$PUSH_STAGING"
              elif [ "$MIRROR_MODE" = "on" ]; then
                echo "::warning title=TFS mirror missing::refs/heads/$MIRROR_BRANCH not present on GitHub, but TFS_USE_MIRROR asks for it — falling back to a direct TFS fetch. Install/dispatch the 'TFS Mirror Sync' workflow (tfs-mirror.yml), or set TFS_USE_MIRROR=false to silence this."
              fi
            fi

            if [ "$MIRROR_PRESENT" = "false" ]; then
              git init "$PUSH_STAGING"
            fi
            git -C "$PUSH_STAGING" config user.email "agent-bot@noreply.local"
            git -C "$PUSH_STAGING" config user.name  "tfs-implement"

            # Add TFS as a remote and fetch the target branch. The extraheader
            # is persisted (not `-c` one-shot) because the final `git push tfs`
            # below needs it too. Explicit refspec so the ancestry check
            # against `tfs/$TFS_TARGET_BRANCH` below works without relying on
            # the remote's configured fetch refspec.
            git -C "$PUSH_STAGING" remote add tfs "$TFS_BASE/_git/$TFS_REPO"
            git -C "$PUSH_STAGING" config --local "http.https://${TFS_HOST}/.extraheader" "$TFS_AUTH"
            git -C "$PUSH_STAGING" fetch tfs "+refs/heads/${TFS_TARGET_BRANCH}:refs/remotes/tfs/${TFS_TARGET_BRANCH}"

            # Verify base_sha is reachable from the target branch. Defense
            # against an intent that supplies an arbitrary commit not part of
            # the project's history — e.g., from a different branch. The TFS
            # tip lives at `tfs/$TFS_TARGET_BRANCH` after the fetch above;
            # `origin/*` would be the GitHub mirror, which can lag and is not
            # authoritative here.
            if ! git -C "$PUSH_STAGING" cat-file -e "$BASE_SHA^{commit}" 2>/dev/null; then
              echo "ERROR: base_sha $BASE_SHA is not present in the cloned $TFS_TARGET_BRANCH history." >&2
              exit 1
            fi
            if ! git -C "$PUSH_STAGING" merge-base --is-ancestor "$BASE_SHA" "tfs/$TFS_TARGET_BRANCH"; then
              echo "ERROR: base_sha $BASE_SHA is not an ancestor of tfs/$TFS_TARGET_BRANCH." >&2
              echo "Refusing to push a branch whose base is outside the target branch's history." >&2
              exit 1
            fi

            # Branch from the snapshotted base, not the target-branch tip.
            # If the target branch moved during the run, the PR will show as
            # "behind main" — same UX as a stale human PR — instead of `git am`
            # failing and leaving the work item stuck in agent-in-progress.
            git -C "$PUSH_STAGING" checkout -B "$BRANCH" "$BASE_SHA"

            # git am preserves the agent's commit author + message from the patch.
            # --keep-cr is REQUIRED: this repo is mixed-EOL (some files stored
            # CRLF, some LF) and the agent's format-patch faithfully carries each
            # file's endings. git am parses the patch as an email (mailsplit /
            # mailinfo) and by default STRIPS the trailing CR from every line
            # before applying — which de-CRs the context of CRLF files so they no
            # longer match the CRLF working tree at base_sha, and `git am` rejects
            # them with "patch does not apply" (LF files are unaffected). Keeping
            # the CR makes the strict apply match end-to-end and, crucially,
            # leaves the agent's already-correct line endings intact — no EOL
            # drift introduced into the PR. (`--3way` would NOT fix this: the CR
            # stripping happens in the mail-parse stage before apply, and a 3-way
            # merge could even succeed while leaving an added line as LF inside a
            # CRLF file.)
            if ! git -C "$PUSH_STAGING" am --keep-cr < "$PATCH_FILE"; then
              echo "ERROR: git am failed — the agent's patch does not apply cleanly to base_sha $BASE_SHA." >&2
              echo "This indicates the patch was produced against a different base than was snapshotted." >&2
              git -C "$PUSH_STAGING" am --abort || true
              exit 1
            fi

            # The push goes to TFS only — never to GitHub. Drop the GitHub
            # header defensively before pushing; it was `-c` one-shot on the
            # mirror clone, so nothing should be persisted.
            git -C "$PUSH_STAGING" config --local --unset "http.https://github.com/.extraheader" || true

            # Try a regular push first. When the branch is new on TFS this
            # succeeds. If it already exists from a prior attempt of this WI
            # the push is rejected non-fast-forward — handled below.
            PUSH_ERR=$(mktemp)
            if git -C "$PUSH_STAGING" push tfs "$BRANCH" 2>"$PUSH_ERR"; then
              echo "Pushed branch $BRANCH to TFS."
              rm -f "$PUSH_ERR"
            else
              cat "$PUSH_ERR" >&2
              if ! grep -qE "non-fast-forward|fetch first|\[rejected\]" "$PUSH_ERR"; then
                echo "ERROR: push to TFS failed for a reason other than non-fast-forward." >&2
                rm -f "$PUSH_ERR"
                exit 1
              fi
              rm -f "$PUSH_ERR"
              echo "Branch $BRANCH already exists on TFS — reconciling with our work."
              # Fetch the existing remote branch so we can compare trees and
              # use --force-with-lease (which gates on the just-fetched tip).
              # Explicit refspec so the `rev-parse refs/remotes/tfs/$BRANCH`
              # below works without relying on the remote's configured fetch
              # refspec.
              git -C "$PUSH_STAGING" fetch tfs "+refs/heads/${BRANCH}:refs/remotes/tfs/${BRANCH}"
              LOCAL_TREE=$(git -C "$PUSH_STAGING" rev-parse "HEAD^{tree}")
              REMOTE_TREE=$(git -C "$PUSH_STAGING" rev-parse "refs/remotes/tfs/$BRANCH^{tree}")
              if [ "$LOCAL_TREE" = "$REMOTE_TREE" ]; then
                echo "TFS branch already contains the same tree as our patch (different commit SHA from prior attempt). Skipping push."
              else
                echo "TFS branch tree differs from our patch — force-pushing the updated work."
                git -C "$PUSH_STAGING" push --force-with-lease tfs "$BRANCH"
                echo "Force-pushed branch $BRANCH to TFS."
              fi
            fi

            # ---------- Open the PR ----------
            # Grab both repo id and project id from the same call — the
            # artifact URI for the PR-to-WI link below needs project id.
            REPO_INFO=$(curl -fsS -H "$TFS_AUTH" \
              "$TFS_BASE/_apis/git/repositories/$TFS_REPO?api-version=6.0")
            REPO_ID=$(echo "$REPO_INFO"    | jq -r '.id')
            PROJECT_ID=$(echo "$REPO_INFO" | jq -r '.project.id')

            # `workItemRefs` in the initial POST is unreliable in Azure DevOps
            # — the PR is created but the structured WI association is not set,
            # which makes the "Work items must be linked" branch policy fail
            # and leaves the right-side "Work items" panel empty. The reliable
            # mechanism is the work-item PATCH below, which adds an
            # ArtifactLink relation pointing at the PR's vstfs:// URI.
            PR_BODY=$(jq -n \
              --arg branch "$BRANCH" --arg target "$TFS_TARGET_BRANCH" \
              --arg title "$TITLE" --arg desc "$PR_DESC" \
              '{sourceRefName: ("refs/heads/" + $branch),
                targetRefName: ("refs/heads/" + $target),
                title: $title, description: $desc}')
            # Capture HTTP status separately so we can recover from 409
            # ("active PR already exists for source/target"). Happens when a
            # previous run pushed the branch and opened a PR but failed
            # before finalizing — or when the same WI is re-dispatched.
            # Reusing the existing PR keeps the workflow idempotent on retry.
            PR_RESPONSE=$(mktemp)
            PR_HTTP_CODE=$(curl -sS -o "$PR_RESPONSE" -w "%{http_code}" \
              -X POST -H "$TFS_AUTH" -H "Content-Type: application/json" \
              --data "$PR_BODY" \
              "$TFS_BASE/_apis/git/repositories/$REPO_ID/pullrequests?api-version=6.0")
            if [ "$PR_HTTP_CODE" = "201" ]; then
              PR_ID=$(jq -r '.pullRequestId' "$PR_RESPONSE")
              echo "Created PR #$PR_ID"
            elif [ "$PR_HTTP_CODE" = "409" ]; then
              echo "PR already exists for refs/heads/$BRANCH -> refs/heads/$TFS_TARGET_BRANCH; looking it up to reuse."
              EXISTING=$(curl -fsS -H "$TFS_AUTH" -G \
                --data-urlencode "searchCriteria.sourceRefName=refs/heads/$BRANCH" \
                --data-urlencode "searchCriteria.targetRefName=refs/heads/$TFS_TARGET_BRANCH" \
                --data-urlencode "searchCriteria.status=active" \
                --data-urlencode "api-version=6.0" \
                "$TFS_BASE/_apis/git/repositories/$REPO_ID/pullrequests")
              PR_ID=$(echo "$EXISTING" | jq -r '.value[0].pullRequestId // empty')
              if [ -z "$PR_ID" ]; then
                echo "ERROR: TFS returned 409 but no matching active PR was found. PR creation response:" >&2
                cat "$PR_RESPONSE" >&2
                rm -f "$PR_RESPONSE"
                exit 1
              fi
              echo "Reusing existing PR #$PR_ID"
            else
              echo "ERROR: PR creation failed with HTTP $PR_HTTP_CODE. Response body:" >&2
              cat "$PR_RESPONSE" >&2
              rm -f "$PR_RESPONSE"
              exit 1
            fi
            rm -f "$PR_RESPONSE"

            # Always attempt to post the review-notes thread. If a prior
            # attempt of the same WI already posted an equivalent thread,
            # TFS returns 409 — log and continue rather than fail, so we
            # don't lose the thread in the (rare) case where the prior
            # attempt created the PR but died before the thread POST.
            # Anything else still fails loudly with the response body.
            THREAD=$(jq -n --arg body "$REVIEW_NOTES" \
              '{comments:[{parentCommentId:0, content:$body, commentType:1}], status:1}')
            THREAD_RESPONSE=$(mktemp)
            THREAD_HTTP_CODE=$(curl -sS -o "$THREAD_RESPONSE" -w "%{http_code}" \
              -X POST -H "$TFS_AUTH" -H "Content-Type: application/json" \
              --data "$THREAD" \
              "$TFS_BASE/_apis/git/repositories/$REPO_ID/pullRequests/$PR_ID/threads?api-version=6.0")
            case "$THREAD_HTTP_CODE" in
              200|201)
                echo "Posted review-notes thread to PR #$PR_ID."
                ;;
              409)
                echo "Review-notes thread already present on PR #$PR_ID — skipping (likely from a prior attempt)."
                ;;
              *)
                echo "ERROR: Failed to post review-notes thread (HTTP $THREAD_HTTP_CODE). Response:" >&2
                cat "$THREAD_RESPONSE" >&2
                rm -f "$THREAD_RESPONSE"
                exit 1
                ;;
            esac
            rm -f "$THREAD_RESPONSE"

            # Atomic WI patch: rev guard + tag transition + (conditional) PR
            # link. The artifact URI uses URL-encoded slashes (%2F) as Azure
            # DevOps expects in the vstfs:///Git/PullRequestId/<proj>/<repo>/<pr>
            # identifier. Adding the relation here (not via the PR POST) is
            # what populates the WI's right-side "Work items" / "Pull
            # Requests" panel and clears the "Work items must be linked"
            # branch policy gate.
            #
            # Wrapped in a retry loop because TFS's PR creation triggers an
            # asynchronous WI auto-linking pass (the PR description + branch
            # name reference #<wi-id>), which bumps the WI rev in the
            # ~milliseconds between our GET and PATCH and makes the rev test
            # op fail 412. The PATCH still has to GUARD against concurrent
            # human edits, so we re-test against the just-fetched rev rather
            # than dropping the guard. `$expand=relations` lets us dedupe the
            # ArtifactLink add — TFS returns 409 RelationAlreadyExistsException
            # if we POST a duplicate (happens on retried WIs whose prior
            # attempt got this far).
            PR_ARTIFACT="vstfs:///Git/PullRequestId/${PROJECT_ID}%2F${REPO_ID}%2F${PR_ID}"
            WI_PATCH_HTTP_CODE=""
            WI_PATCH_RESPONSE=$(mktemp)
            for attempt in 1 2 3 4 5 6 7 8; do
              WI=$(curl -fsS -H "$TFS_AUTH" "$TFS_BASE/_apis/wit/workitems/$WI_ID?\$expand=relations&api-version=6.0")
              REV=$(echo "$WI"  | jq -r '.rev')
              TAGS=$(echo "$WI" | jq -r '.fields["System.Tags"] // ""')
              NEW_TAGS=$(echo "$TAGS" | sed 's/agent-in-progress/agent-pr-opened/g')
              ARTIFACT_EXISTS=$(echo "$WI" | jq --arg link "$PR_ARTIFACT" \
                '[(.relations // [])[] | select(.rel == "ArtifactLink" and .url == $link)] | length')
              if [ "$ARTIFACT_EXISTS" -eq 0 ]; then
                PATCH=$(jq -n --argjson rev "$REV" --arg tags "$NEW_TAGS" --arg link "$PR_ARTIFACT" \
                  '[{"op":"test","path":"/rev","value":$rev},
                    {"op":"replace","path":"/fields/System.Tags","value":$tags},
                    {"op":"add","path":"/relations/-","value":{
                       "rel":"ArtifactLink",
                       "url":$link,
                       "attributes":{"name":"Pull Request"}
                     }}]')
              else
                [ "$attempt" -eq 1 ] && echo "ArtifactLink for PR #$PR_ID already present on WI #$WI_ID — skipping relation add."
                PATCH=$(jq -n --argjson rev "$REV" --arg tags "$NEW_TAGS" \
                  '[{"op":"test","path":"/rev","value":$rev},
                    {"op":"replace","path":"/fields/System.Tags","value":$tags}]')
              fi
              WI_PATCH_HTTP_CODE=$(curl -sS -o "$WI_PATCH_RESPONSE" -w "%{http_code}" \
                -X PATCH -H "$TFS_AUTH" -H "Content-Type: application/json-patch+json" \
                --data "$PATCH" "$TFS_BASE/_apis/wit/workitems/$WI_ID?api-version=6.0")
              if [ "$WI_PATCH_HTTP_CODE" = "200" ]; then
                break
              fi
              # Rev mismatch comes back as 412 on Azure DevOps cloud but 409
              # on on-prem TFS (TF26071 / WorkItemRevisionMismatchException).
              # Only retry the 409 case when the body confirms it's a rev
              # mismatch, so we don't mask other 409s (e.g., a future
              # RelationAlreadyExists that escapes the dedupe check).
              if [ "$WI_PATCH_HTTP_CODE" = "412" ] || \
                 { [ "$WI_PATCH_HTTP_CODE" = "409" ] && \
                   grep -qE "TF26071|WorkItemRevisionMismatchException" "$WI_PATCH_RESPONSE"; }; then
                echo "WI rev moved between GET and PATCH (attempt $attempt, rev was $REV, HTTP $WI_PATCH_HTTP_CODE) — refetching and retrying."
                sleep 1
                continue
              fi
              # Any other status: surface immediately, no retry.
              break
            done
            if [ "$WI_PATCH_HTTP_CODE" = "200" ]; then
              rm -f "$WI_PATCH_RESPONSE"
            else
              echo "ERROR: WI patch failed (HTTP $WI_PATCH_HTTP_CODE) on WI #$WI_ID after retries." >&2
              echo "Last patch body sent:" >&2
              echo "$PATCH" >&2
              echo "TFS response:" >&2
              cat "$WI_PATCH_RESPONSE" >&2
              echo "" >&2
              echo "PR #$PR_ID was created and the review-notes thread was posted," >&2
              echo "but the work item link / tag transition did not complete." >&2
              echo "A human can add the WI link via the TFS UI and flip the tag manually." >&2
              rm -f "$WI_PATCH_RESPONSE"
              exit 1
            fi

            echo "Finalized PR #$PR_ID for work item #$WI_ID"
---

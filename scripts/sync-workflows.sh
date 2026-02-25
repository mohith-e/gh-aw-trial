#!/usr/bin/env bash
set -euo pipefail

# Sync shared gh-aw workflows from RealPage/gh-aw-shared-workflows
# into the current project's .github/workflows/ directory.
#
# Usage: ./scripts/sync-workflows.sh
#
# Requires: gh CLI authenticated with access to RealPage org

SHARED_REPO="RealPage/gh-aw-shared-workflows"
WORKFLOWS_DIR=".github/workflows"
SHARED_WORKFLOWS=(
  prd-generation
  decomposition
  skill-selection
  mcp-selection
  validation
)

echo "Syncing shared workflows from ${SHARED_REPO}..."

mkdir -p "${WORKFLOWS_DIR}"

changed=0
for workflow in "${SHARED_WORKFLOWS[@]}"; do
  echo "  Fetching ${workflow}.md..."
  content=$(gh api "repos/${SHARED_REPO}/contents/workflows/${workflow}.md" --jq '.content' | base64 -d)
  target="${WORKFLOWS_DIR}/${workflow}.md"

  if [ -f "${target}" ]; then
    existing=$(cat "${target}")
    if [ "${content}" = "${existing}" ]; then
      echo "    ✓ ${workflow}.md is up to date"
      continue
    fi
  fi

  echo "${content}" > "${target}"
  echo "    ✓ ${workflow}.md updated"
  changed=$((changed + 1))
done

if [ "${changed}" -gt 0 ]; then
  echo ""
  echo "${changed} workflow(s) updated. Next steps:"
  echo "  1. Run 'gh aw compile' to regenerate lock files"
  echo "  2. Review changes and commit"
else
  echo ""
  echo "All workflows are up to date."
fi

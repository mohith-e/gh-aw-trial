---
# Configuration shared by every workflow that talks to the RealPage TFS
# instance: the network allow-list and the two repo variables that identify
# the TFS project and repo.
#
# This file is the single source of workflow-level `env:` for the TFS family.
# gh-aw fails compilation when two imports define the same workflow-level env
# key, so a TFS variable read by more than one workflow belongs here and
# nowhere else. Variables specific to one workflow stay in that workflow.

# ── Network allow-list ────────────────────────────────────────────────────────
#
# The default below covers all RealPage teams on the corporate TFS instance.
#
# If your team is on a different TFS / Azure DevOps host (e.g. dev.azure.com,
# a self-hosted Azure DevOps Server, or a different on-prem TFS), override
# this list in your consumer stub. Example for dev.azure.com:
#
#   network:
#     allowed:
#       - defaults
#       - dev.azure.com
#
# gh-aw resolves frontmatter at compile time, so `${{ vars.X }}` does not work
# here. The hostname listed must match the host portion of vars.TFS_BASE — if
# you point this workflow at a different TFS instance, update both. The verify
# step cross-checks them at runtime.
#
# Keep the allow-list as narrow as possible — it is the primary exfiltration
# guard for a workflow that handles a TFS PAT.
# ──────────────────────────────────────────────────────────────────────────────
network:
  allowed:
    - defaults
    - tfs.realpage.com

env:
  TFS_BASE: ${{ vars.TFS_BASE }}
  TFS_REPO: ${{ vars.TFS_REPO }}
  # Clone transport. Every TFS workflow needs a working tree of the target
  # branch, and there are two ways to get one:
  #
  #   mirror — clone refs/heads/tfs-mirror/<branch> from this GitHub repo,
  #            then fetch only the delta from TFS. Requires the companion
  #            tfs-mirror.yml. Worth it when a direct TFS clone dominates
  #            run time; on a large repo that is the difference between
  #            minutes and tens of minutes.
  #   direct — fetch the target branch straight from TFS. No companion
  #            workflow, no mirror refs.
  #
  # Accepted values, matched case-insensitively:
  #   unset            probe for the mirror ref; use it if present, otherwise
  #                    go direct without comment. Both are supported modes.
  #   true 1 yes on    probe as above, but warn when the mirror ref is absent
  #                    so a mirror that has stopped syncing is visible.
  #   false 0 no off   never probe; always go direct.
  #
  # The mirror is transport only. base_sha and every ancestry check reference
  # the freshly fetched TFS tip, so a mirror SHA is never authoritative.
  TFS_USE_MIRROR: ${{ vars.TFS_USE_MIRROR }}
---

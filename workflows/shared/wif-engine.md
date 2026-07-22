---
# DEPRECATED — NO LONGER IMPORTED (retained for reference only).
#
# gh-aw v0.82.10 (2026-07-16) introduced a behavior-defined engine model whose
# imported `auth:` is parsed as a sequence of OAuth secret-bindings and cannot
# express Anthropic WIF fields. Importing this shared engine therefore fails to
# compile ("mapping was used where sequence is expected"). The WIF auth block is
# now INLINED into each workflow's own `engine:` frontmatter instead.
#
# Last worked on gh-aw v0.82.9. Upstream regression: github/gh-aw#47294.
# The inline object auth below still works on any gh-aw version that supports
# Anthropic WIF (≥ v0.79.6) — copy the `engine:` block below (NOT the `---`
# delimiters) into a workflow's own frontmatter rather than importing this file.
#
# Originally: shared Claude engine + WIF auth, imported so the auth config lived
# in exactly one place (engine defined ONCE across the workflow and its imports).
engine:
  id: claude
  auth:
    type: github-oidc
    provider: anthropic
    federation-rule-id: ${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}
    # organization-id is the RealPage Anthropic org UUID — same for every GitHub org in this org
    organization-id: cb16d48f-b95b-4b2c-9e86-a09f46eccb90
    service-account-id: ${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}
    workspace-id: wrkspc_011kuRkDngP7B49bQc5AZLVJ           # github-actions workspace
---

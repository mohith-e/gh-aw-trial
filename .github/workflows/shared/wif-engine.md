---
# Shared Claude engine + WIF auth for this repo's OWN gh-aw workflows under
# .github/workflows/. gh-aw resolves imports relative to the importing file and
# requires them to live within .github/, so the canonical workflows/shared/
# wif-engine.md (distributed to consumers) cannot be imported from here — this
# is an in-.github mirror of it. Keep the two in sync.
#
# gh-aw requires the engine to be defined only ONCE across the main workflow and
# all imports, so importing workflows must NOT declare their own `engine:` line.
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

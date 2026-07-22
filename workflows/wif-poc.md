---
on:
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

engine:
  id: claude
  auth:
    type: github-oidc
    provider: anthropic
    federation-rule-id: ${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}
    # organization-id is the RealPage Anthropic org UUID — same for every GitHub org
    organization-id: cb16d48f-b95b-4b2c-9e86-a09f46eccb90
    service-account-id: ${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}
    workspace-id: wrkspc_011kuRkDngP7B49bQc5AZLVJ

network: defaults

tools:
  bash: true

safe-outputs:
  noop:

timeout-minutes: 5
---

# WIF auth check

Use bash to read the `GITHUB_RUN_ID` and `GITHUB_REPOSITORY` environment variables. Print a confirmation that WIF authentication succeeded, including those values. Then call `noop`.

---
# Shared Claude engine + WIF auth — imported by every workflow so the auth
# config lives in exactly one place. gh-aw requires the engine to be defined
# only ONCE across the main workflow and all imports, so importing workflows
# must NOT declare their own `engine:` line.
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
  env:
    # Routing signal for awf — required until gh-aw-firewall#4117 ships.
    # awf sets ANTHROPIC_BASE_URL in the agent container only when ANTHROPIC_API_KEY
    # is present. Without it the agent bypasses the api-proxy and fails auth.
    # This is NOT a real key; the proxy uses WIF. When #4117 ships, remove this block.
    ANTHROPIC_API_KEY: "sk-ant-placeholder-key-for-credential-isolation"
---

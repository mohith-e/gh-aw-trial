---
# Shared Claude engine + WIF auth, imported so the auth config lives in exactly
# one place (engine defined ONCE across the workflow and all its imports). An
# importing workflow must NOT declare its own `engine:` block — not even a
# partial one.
#
# Requires gh-aw >= v0.83.2. v0.82.10 through v0.83.1 rejected an imported WIF
# `auth:` mapping ("mapping was used where sequence is expected") because
# `EngineDefinition.Auth` is a sequence; github/gh-aw#47294, fixed by #47572.
# During that window this block was inlined into each workflow instead.
#
# `gh aw add` fetches this file alongside the workflow, so consumers get it
# automatically — verified on v0.83.4 against a scratch repo.
#
# A workflow needing engine-level extras cannot import this file:
#   - `max-turns` — move it to the ROOT level and the import works.
#   - `engine.env` — no import-compatible equivalent; `sandbox.agent.env` is
#     refused by strict mode as an internal implementation detail, so such a
#     workflow must keep the whole `engine:` block inline.
#
# This is the in-.github mirror of the canonical workflows/shared/wif-engine.md,
# needed because gh-aw resolves imports relative to the importing file within
# .github/. Keep the two in sync.
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

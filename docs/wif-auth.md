# Authentication: Keyless Anthropic Auth for gh-aw

Workflows that use an `ANTHROPIC_API_KEY` repo secret attribute API usage to the key owner's personal account — automated runs look like individual usage in billing reports. Workload Identity Federation (WIF) lets each workflow run mint a short-lived token automatically, attributed to a service account. Nothing to store, nothing to rotate, and cost shows up under the right product in the Anthropic console.

## How it works

When a workflow runs, the GitHub Actions runner mints a short-lived OpenID Connect (OIDC) JWT (`id-token: write` permission required). The gh-aw api-proxy exchanges that JWT with Anthropic for a short-lived bearer token, then forwards requests to the Anthropic API. Your workflow never touches a real key.

## Prerequisites

**gh-aw ≥ v0.79.4.** Check your version:

```bash
gh aw --version
```

Update if behind:

```bash
gh extension upgrade aw
```

---

## Add WIF to a workflow

### Step 1: Use the shared engine import

Replace `engine: claude` with an import. The shared config in this repo (`shared/wif-engine.md`) contains the full WIF auth block — you just import it:

```yaml
imports:
  - shared/wif-engine.md

permissions:
  contents: read
  id-token: write
```

Add any toolset-required read permissions your workflow needs (e.g., `issues: read`, `pull-requests: read`). The five golden workflows already have the right permissions set.

> **Do not add a separate `engine:` block.** The import provides it. Adding your own causes a compilation error.

> **Write permissions (`contents: write`, `pull-requests: write`, etc.) are blocked by strict mode.** gh-aw routes all writes through safe-outputs rather than direct `GITHUB_TOKEN` write access — explicit write permissions on the token are neither needed nor allowed.

### Step 2: Compile

```bash
gh aw compile workflows/<your-workflow>.md
```

Compilation should exit 0. The only expected warning is the OIDC advisory:

```
This workflow grants id-token: write permission
OIDC tokens can authenticate to cloud providers (AWS, Azure, GCP).
Ensure proper audience validation and trust policies are configured.
```

That warning is informational — the trust policy is already configured on the Anthropic side.

### Step 3: Verify the lock

Check that the WIF env vars made it into the compiled lock:

```bash
grep "AWF_AUTH" .github/workflows/<your-workflow>.lock.yml
```

Expected: `AWF_AUTH_TYPE`, `AWF_AUTH_PROVIDER`, `AWF_AUTH_ANTHROPIC_FEDERATION_RULE_ID`, `AWF_AUTH_ANTHROPIC_ORGANIZATION_ID`, `AWF_AUTH_ANTHROPIC_SERVICE_ACCOUNT_ID` — all present as env vars on the agent step.

---

## Variables

Two Actions variables are required. Set them at the repo level (Settings → Secrets and variables → Actions → Variables), or at the GitHub org level to share across repos in that org.

| Variable | Who sets it | Notes |
|---|---|---|
| `ANTHROPIC_FEDERATION_RULE_ID` | Already set at org level for `RealPage` GitHub org | If your repo is under a different GitHub org, set this at that org level after requesting a federation rule (see below) |
| `ANTHROPIC_SERVICE_ACCOUNT_ID` | **You** — set this per repo or per org | Provisioned when you request a service account; one per product area |

The shared import references both via `${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}` and `${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}`.

---

## Request a service account

Each product needs its own service account so spend is attributable. Request via the issue template in `RealPage/ai-internal-enablement`:

→ [New Anthropic service account request](https://github.com/RealPage/ai-internal-enablement/issues/new?template=anthropic-service-account.yml)

One service account per product area. If your repo is under a GitHub org other than `RealPage`, note the org name in the form — admins create the federation rule for that org before provisioning the service account.

Once provisioned, set `ANTHROPIC_SERVICE_ACCOUNT_ID` as an Actions variable on your repo (or org level to share across repos). `ANTHROPIC_FEDERATION_RULE_ID` is already set at the `RealPage` org level; if your repo is under a different GitHub org, the admins will provide the rule ID to set at that org level.

---

## Troubleshooting

**HTTP 401 on every run:** Most common cause — the service account is not a member of the target workspace. The exchange returns 401 with no message identifying the cause. Check workspace membership in the Anthropic Console before investigating further. Ping the admins with your service account ID if you need help.

**Auth events dashboard:** [platform.claude.com/settings/workload-identity-federation?tab=history&range=7d](https://platform.claude.com/settings/workload-identity-federation?tab=history&range=7d) — shows recent token exchange attempts, which federation rule matched, and the subject claim from the OIDC JWT. Requires org-admin access to the Anthropic Console.

---

## See also

- [`workflows/wif-poc.md`](../workflows/wif-poc.md) — minimal dispatch workflow to verify WIF auth end-to-end
- [`docs/wif-administration.md`](wif-administration.md) — operator guide: new GitHub orgs, federation rule setup, service account provisioning, cost attribution
- [Anthropic WIF docs](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation) — issuer and federation rule reference

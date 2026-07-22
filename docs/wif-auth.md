# Authentication: Keyless Anthropic Auth for gh-aw

Workflows that use an `ANTHROPIC_API_KEY` repo secret attribute API usage to the key owner's personal account — automated runs look like individual usage in billing reports. Workload Identity Federation (WIF) lets each workflow run mint a short-lived token automatically, attributed to a service account. Nothing to store, nothing to rotate, and cost shows up under the right product in the Anthropic console.

## How it works

When a workflow runs, the GitHub Actions runner mints a short-lived OpenID Connect (OIDC) JWT (`id-token: write` permission required). The gh-aw api-proxy exchanges that JWT with Anthropic for a short-lived bearer token, then forwards requests to the Anthropic API. Your workflow never touches a real key.

## Prerequisites

**gh-aw ≥ v0.79.6** (when Anthropic WIF support landed). Check your version:

```bash
gh aw --version
```

Update if behind:

```bash
gh extension upgrade aw
```

> **Inline the WIF block — do not import a shared engine.** Earlier revisions of this
> doc pointed you at a shared `shared/wif-engine.md` you would `import`. That no longer
> works: **gh-aw v0.82.10** (2026-07-16) changed imported engine definitions to a
> behavior-defined model whose `auth:` is a sequence of OAuth secret-bindings and cannot
> express Anthropic WIF fields — importing the shared engine now fails to compile
> (`mapping was used where sequence is expected`). The import pattern worked only up to
> **v0.82.9**; on v0.82.10+ the engine + WIF auth must be **inlined** per workflow (as
> below). Inline object auth compiles on every WIF-capable gh-aw version (≥ v0.79.6). Upstream regression:
> [github/gh-aw#47294](https://github.com/github/gh-aw/issues/47294).

---

## Add WIF to a workflow

### Step 1: Inline the WIF engine block

Replace `engine: claude` with the full inline engine + WIF auth block:

```yaml
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

permissions:
  contents: read
  id-token: write
```

Add any toolset-required read permissions your workflow needs (e.g., `issues: read`, `pull-requests: read`). The five golden workflows already have the right permissions set.

> **Define `engine:` exactly once.** Put this block in the workflow's own frontmatter. `shared/wif-engine.md` is retained for reference only and must not be imported.

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

WIF auth needs **two** Actions variables, and they are a **matched pair**: a federation rule targets exactly one service account, so the rule ID and the service account ID must correspond. **Always set both together** — never one without the other.

| Variable | What it is |
|---|---|
| `ANTHROPIC_FEDERATION_RULE_ID` | The federation rule that targets *your* service account (`fdrl_...`) |
| `ANTHROPIC_SERVICE_ACCOUNT_ID` | *Your* service account (`svac_...`) — the rule's target |

Set them at the **repo level** (Settings → Secrets and variables → Actions → Variables), or at the **GitHub org level** to share a default across repos in that org. A repo-level value overrides the org-level one — but override **both**, or the rule and account won't correspond and the token exchange fails.

Provisioning hands you both values together (see below). The `RealPage` GitHub org has an org-level default pair — the `realpage-org` rule targeting the `realpage-gh` account — for repos that use the shared account; a product with its own service account sets its own pair (its rule + its account) at the repo level.

The inline engine block references both via `${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}` and `${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}`.

---

## Request a service account

Each product gets its own service account (so spend is attributable) **and its own federation rule that targets it** — the two are provisioned together. Request via the issue template in `RealPage/ai-internal-enablement`:

→ [New Anthropic service account request](https://github.com/RealPage/ai-internal-enablement/issues/new?template=anthropic-service-account.yml)

Filing the request runs the `wif-admin` automation (after admin approval). It creates the service account, a federation rule targeting it (subject `repo:<org>/*`), and the workspace membership — then prints the **pair** of values to set: `ANTHROPIC_FEDERATION_RULE_ID` + `ANTHROPIC_SERVICE_ACCOUNT_ID`. Set **both** as Actions variables on your repo (or org level to share). Works the same whether your repo is under `RealPage` or another GitHub org (note the org in the form).

Multiple products under one GitHub org each get their own pair — several rules can share the `repo:<org>/*` subject, each targeting a different service account; your repo's variable pair selects which one your workflows use.

---

## Troubleshooting

**HTTP 401 on every run:** Most common cause — the service account is not a member of the target workspace. The exchange returns 401 with no message identifying the cause. Check workspace membership in the Anthropic Console before investigating further. Ping the admins with your service account ID if you need help.

**Auth events dashboard:** [platform.claude.com/settings/workload-identity-federation?tab=history&range=7d](https://platform.claude.com/settings/workload-identity-federation?tab=history&range=7d) — shows recent token exchange attempts, which federation rule matched, and the subject claim from the OIDC JWT. Requires org-admin access to the Anthropic Console.

---

## See also

- [`workflows/wif-poc.md`](../workflows/wif-poc.md) — minimal dispatch workflow to verify WIF auth end-to-end
- [`docs/wif-administration.md`](wif-administration.md) — operator guide: new GitHub orgs, federation rule setup, service account provisioning, cost attribution
- [Anthropic WIF docs](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation) — issuer and federation rule reference

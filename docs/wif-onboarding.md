# WIF Onboarding: Keyless Anthropic Auth for gh-aw

**Status: preview for early adopters — requires gh-aw v0.77.5+**

> **Known limitation:** A placeholder `ANTHROPIC_API_KEY` is still required in `engine.env` as a routing signal (see [Workflow frontmatter](#workflow-frontmatter)). This is a dummy value — the proxy uses WIF, not the key. The requirement will be removed when [gh-aw-firewall#4117](https://github.com/github/gh-aw-firewall/issues/4117) ships in a new firewall release.

This guide covers setting up Workload Identity Federation (WIF) so gh-aw workflows authenticate to Anthropic via short-lived OIDC tokens rather than a static API key. No real `ANTHROPIC_API_KEY` to rotate or leak.

## How it works

When a workflow runs, the GitHub Actions runner mints a short-lived OIDC JWT (`id-token: write` permission required). The gh-aw api-proxy exchanges that JWT with Anthropic's token endpoint for a short-lived `sk-ant-oat01-...` bearer token, then forwards requests to the Anthropic API. Your workflow never touches a real key.

## Prerequisites

### 1. gh-aw version

**v0.77.5 or later** (stable). v0.77.5 removed the compiler's requirement that `ANTHROPIC_API_KEY` be registered as a secret — so WIF workflows no longer fail secret validation. A placeholder value is still required in `engine.env` (see [Workflow frontmatter](#workflow-frontmatter)) until a firewall fix ships.

Check your installed version:

```bash
gh aw --version
```

Update if needed:

```bash
gh extension upgrade aw
```

### 2. Anthropic Console access

You need org-admin access to [console.anthropic.com](https://console.anthropic.com) to create the issuer, service account, and federation rule.

---

## Anthropic Console setup

> **For RealPage teams:** the COE maintains shared org-level resources. If you are onboarding a repo under the `RealPage` GitHub org, skip to [GitHub variables](#github-variables) — the issuer, service account, and federation rule are already configured. Contact the COE if you need a repo-scoped override.

### Step 1: Create the federation issuer

In the Anthropic Console, navigate to **Settings → Workload Identity Federation → Issuers → Add issuer**.

| Field | Value |
|---|---|
| Name | `GitHub Actions` (or any label) |
| Issuer URL | `https://token.actions.githubusercontent.com` |
| Discovery method | JWKS discovery (auto-populated from the URL) |

Save. The issuer gets an `fdis_...` ID.

### Step 2: Create a service account

Navigate to **Settings → Service accounts → Create service account**.

Naming convention: `<product>-ghaw` (e.g., `payments-ghaw`, `knock-ghaw`). One service account per product area.

Assign it to the appropriate workspace. If you are using the Default workspace, leave workspace selection empty.

Save. The service account gets an `svac_...` ID.

### Step 3: Create a federation rule

Navigate to the issuer you created → **Federation rules → Add rule**.

For an org-wide rule (all repos in a GitHub org):

| Field | Value |
|---|---|
| Service account | Select the service account from step 2 |
| Subject prefix | `repo:<github-org>/*` |
| Additional claims | `repository_owner: <github-org>`, `enterprise: realpage` |
| Audience | `https://api.anthropic.com` |
| Scope | `workspace:developer` |
| Token lifetime | `600` (seconds) |

`enterprise: realpage` pins the rule to the RealPage GitHub Enterprise, preventing JWT reuse from a typosquatted org with the same name. The value is the slug from `https://github.com/enterprises/realpage` — visible to enterprise owners under **GitHub → Your enterprises → Settings**.

For a repo-scoped rule (tighter, recommended for production):

| Field | Subject prefix |
|---|---|
| Single branch | `repo:<github-org>/<repo>:ref:refs/heads/main` |
| Any branch | `repo:<github-org>/<repo>:*` |

For production repo-scoped rules, also add `ref_protected: "true"` to Additional claims — this requires main to be a protected branch and blocks exchange if branch protection is accidentally removed.

Save. The rule gets an `fdrl_...` ID.

---

## GitHub variables

Set two Actions variables at the GitHub org level (Settings → Secrets and variables → Actions → Variables). Repo-level variables override org-level when set.

| Variable | Value | Scope |
|---|---|---|
| `ANTHROPIC_FEDERATION_RULE_ID` | `fdrl_...` from step 3 | Org (or repo) |
| `ANTHROPIC_SERVICE_ACCOUNT_ID` | `svac_...` from step 2 | Org (or repo) |

The `organization-id` (Anthropic org UUID) is hardcoded in workflow sources — it is the same for every GitHub org under the same Anthropic workspace and never needs to vary.

---

## Workflow frontmatter

Add an `engine.auth` block to any Claude workflow:

```yaml
permissions:
  contents: read
  id-token: write        # required — grants runner the ability to mint OIDC JWTs

engine:
  id: claude
  auth:
    type: github-oidc
    provider: anthropic
    federation-rule-id: ${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}
    organization-id: cb16d48f-b95b-4b2c-9e86-a09f46eccb90   # RealPage Anthropic org
    service-account-id: ${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}
  env:
    # Routing signal for awf — required until gh-aw-firewall#4117 ships.
    # awf only sets ANTHROPIC_BASE_URL in the agent container when ANTHROPIC_API_KEY
    # is present. This is NOT a real key; the proxy uses WIF for all actual requests.
    # Remove this block once the firewall fix is released.
    ANTHROPIC_API_KEY: "sk-ant-placeholder-key-for-credential-isolation"
```

`workspace-id` is optional — omit it when the federation rule targets the Default workspace (which has no `wrkspc_` ID).

See [`workflows/wif-poc.md`](../workflows/wif-poc.md) for a complete minimal workflow you can dispatch to verify auth end-to-end.

---

## Compile and install

After adding `engine.auth` to a workflow source, recompile its lock:

```bash
gh aw compile <workflow-name>
```

Verify the lock is correct:

```bash
grep -E "AWF_AUTH|ANTHROPIC_API_KEY" .github/workflows/<workflow-name>.lock.yml
```

Expected output:
- `AWF_AUTH_TYPE`, `AWF_AUTH_PROVIDER`, `AWF_AUTH_ANTHROPIC_FEDERATION_RULE_ID`, `AWF_AUTH_ANTHROPIC_ORGANIZATION_ID`, `AWF_AUTH_ANTHROPIC_SERVICE_ACCOUNT_ID` — all present as env vars on the agent step
- `ANTHROPIC_API_KEY` — appears **only** in `--exclude-env ANTHROPIC_API_KEY` on the `awf` command line; this is expected and means the key is actively blocked from the agent container. It should **not** appear as a set env var.

If `ANTHROPIC_API_KEY` appears as a set env var (e.g. `ANTHROPIC_API_KEY: sk-ant-...`), the workflow was compiled without WIF auth — check that `engine.auth` is present in the source and recompile.

---

## Cost attribution

WIF requests are tagged with the service account ID in Anthropic's usage data. You can attribute spend per service account **without separate workspaces** using the messages usage report:

```
GET /v1/organizations/usage_report/messages?group_by[]=service_account_id
```

To filter to a specific service account:

```
GET /v1/organizations/usage_report/messages?service_account_ids[]=svac_...&group_by[]=service_account_id
```

Both endpoints require an Admin API key (`sk-ant-admin-...`). See the [usage report API reference](https://platform.claude.com/docs/en/api/admin/usage_report/retrieve_messages) for the full parameter list including time range, model, and service tier filters.

---

## Known limitations

| Limitation | Detail |
|---|---|
| Requires gh-aw ≥ v0.77.5 | Earlier stable releases lack WIF support |
| Long-running jobs (>10 min) | Untested — the 600s JWT lifetime may expire before the workflow completes. The api-proxy inherits `BaseOidcTokenProvider` refresh logic (auto-refresh at 75% of lifetime), but this has not been validated for long runs |
| Default workspace | Has no `wrkspc_` ID in the Console — omit `workspace-id` from frontmatter |
| Workbench usage | Calls made via the Console Workbench show `api_key_id: null` in the usage API — not attributable to a service account |

---

## Related

- [`workflows/wif-poc.md`](../workflows/wif-poc.md) — minimal dispatch workflow to verify WIF auth
- [Anthropic WIF docs](https://platform.claude.com/docs/en/manage-claude/workload-identity-federation) — issuer and federation rule reference
- [GitHub Actions WIF example](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions) — plain GHA YAML reference (no gh-aw)
- [ai-internal-enablement#571](https://github.com/RealPage/ai-internal-enablement/issues/571) — RealPage COE POC tracking issue

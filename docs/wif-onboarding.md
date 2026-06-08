# WIF Onboarding: Keyless Anthropic Auth for gh-aw

**Status: preview — not ready for dev rollout**

> **Rollout blocker:** The auto-generated threat-detection job fails with HTTP 401 under WIF auth — the gh-aw compiler omits `id-token: write` from the detection job's permissions, so the api-proxy can't mint the OIDC JWT. Detection annotations appear on every run but the workflow still passes. Fix is pending in [github/gh-aw#36460](https://github.com/github/gh-aw/issues/36460). Rollout to teams is paused until a gh-aw release that includes that fix ships and workflows are recompiled. See [agentic-workflows#80](https://github.com/RealPage/agentic-workflows/issues/80).

> **Known limitation:** A placeholder `ANTHROPIC_API_KEY` is still required in `engine.env` as a routing signal (see [Workflow frontmatter](#workflow-frontmatter)). This is a dummy value — the proxy uses WIF, not the key. The requirement will be removed when [gh-aw-firewall#4117](https://github.com/github/gh-aw-firewall/issues/4117) ships in a new firewall release.

Instead of storing a long-lived `ANTHROPIC_API_KEY` in GitHub Secrets — which can leak and must be manually rotated — Workload Identity Federation (WIF) lets each workflow run mint a short-lived token automatically. Nothing to store, nothing to rotate. Usage is also attributed to a service account in billing reports, rather than to an individual developer's key — which otherwise makes automated runs look like personal usage.

## How it works

When a workflow runs, the GitHub Actions runner mints a short-lived OpenID Connect (OIDC) JSON Web Token (JWT) (`id-token: write` permission required). The gh-aw api-proxy exchanges that JWT with Anthropic's token endpoint for a short-lived `sk-ant-oat01-...` bearer token, then forwards requests to the Anthropic API. Your workflow never touches a real key.

## Prerequisites

**gh-aw ≥ v0.77.5** (stable). v0.77.5 removed the compiler's requirement that `ANTHROPIC_API_KEY` be registered as a secret — so WIF workflows no longer fail secret validation. A placeholder value is still required in `engine.env` (see [Workflow frontmatter](#workflow-frontmatter)) until a firewall fix ships.

Check your installed version:

```bash
gh aw --version
```

Update if needed:

```bash
gh extension upgrade aw
```

---

## GitHub variables

> **For repos under the `RealPage` GitHub org:** The federation issuer, service account, and federation rule are already configured. Set these two variables and then jump to [Workflow frontmatter](#workflow-frontmatter).
>
> If you're setting up WIF for a **different GitHub org** (e.g. `modernmsg`), complete [Operator setup](#operator-setup-new-org-only) first to create the required resources, then come back here.

Set two Actions variables at the GitHub org level (Settings → Secrets and variables → Actions → Variables). Repo-level variables override org-level when set.

| Variable | Value | Scope |
|---|---|---|
| `ANTHROPIC_FEDERATION_RULE_ID` | `fdrl_...` from your federation rule | Org (or repo) |
| `ANTHROPIC_SERVICE_ACCOUNT_ID` | `svac_...` from your service account | Org (or repo) |

For the `RealPage` org, the COE has already set these at the org level. The underlying resource IDs for reference:

| Resource | Name | ID |
|---|---|---|
| Issuer | GitHub Actions | `fdis_01RPUmB9gNG4qojQ96FWSEDi` |
| Federation rule | `realpage-org` (`repo:RealPage/*`) | `fdrl_01UrTuTXEcPdS3ckapB7re3y` |
| Workspace | `github-actions` | `wrkspc_011kuRkDngP7B49bQc5AZLVJ` |

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
    workspace-id: wrkspc_011kuRkDngP7B49bQc5AZLVJ           # github-actions workspace
  env:
    # Routing signal for awf — required until gh-aw-firewall#4117 ships.
    # awf only sets ANTHROPIC_BASE_URL in the agent container when ANTHROPIC_API_KEY
    # is present. This is NOT a real key; the proxy uses WIF for all actual requests.
    # Remove this block once the firewall fix is released.
    ANTHROPIC_API_KEY: "sk-ant-placeholder-key-for-credential-isolation"
```

`workspace-id` is required when the federation rule targets a named workspace. Omit it only when using the Default workspace (which has no `wrkspc_` ID). For the `RealPage` org, `wrkspc_011kuRkDngP7B49bQc5AZLVJ` (`github-actions`) is hardcoded above — it is the same for every repo in the org.

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

## Operator setup (new org only)

> **Skip this section if you're adding WIF to a repo in the `RealPage` GitHub org.** The required resources are already configured. Start at [GitHub variables](#github-variables).
>
> You only need these steps when onboarding a **new GitHub org** (e.g. `modernmsg`, `joedean`) for the first time.

You need org-admin access to [console.anthropic.com](https://console.anthropic.com) to create the resources below.

### The shared federation issuer

All GitHub Actions workflows — across every GitHub org — use the same federation issuer. You do not need to create a new one.

| Field | Value |
|---|---|
| Name | `GitHub Actions` |
| Issuer URL | `https://token.actions.githubusercontent.com` |
| ID | `fdis_01RPUmB9gNG4qojQ96FWSEDi` |

Create a federation rule under this existing issuer (Step 2 below) that targets your org.

### Step 1: Create a service account

Navigate to **Settings → Service accounts → Create service account**.

Naming convention: `<product>-gh` (e.g. `payments-gh`, `knock-gh`). One service account per product area.

Save. The service account gets an `svac_...` ID.

> **Auth will fail without this step.** After creating the service account, add it as a member of the target workspace. Open the service account's full detail page (**Settings → Service accounts → click the row → Open full page**) and add it to each workspace the federation rule will target. Tokens minted for a workspace the service account is not a member of are rejected with HTTP 401 at exchange time — with no error message pointing to this as the cause.

### Step 2: Create a federation rule

Navigate to **Settings → Workload Identity Federation → Issuers → GitHub Actions → Federation rules → Add rule**.

For an org-wide rule (all repos in a GitHub org):

| Field | Value |
|---|---|
| Service account | Select the service account from Step 1 |
| Subject prefix | `repo:<github-org>/*` |
| Additional claims | See below |
| Audience | `https://api.anthropic.com` |
| Scope | `workspace:developer` |
| Token lifetime | `600` (seconds) |

**Additional claims:**

| Claim | Value | Varies? |
|---|---|---|
| `repository_owner` | The GitHub org (e.g. `RealPage`, `modernmsg`, `joedean`) | **Yes** — one rule per org |
| `enterprise` | `realpage` | **No** — always `realpage` for all RealPage-managed GitHub orgs |

`enterprise: realpage` pins the rule to the RealPage GitHub Enterprise, preventing JWT reuse from a same-named org elsewhere. The value is the slug from `https://github.com/enterprises/realpage`.

For a repo-scoped rule (tighter, recommended for production):

| Scope | Subject prefix |
|---|---|
| Single branch | `repo:<github-org>/<repo>:ref:refs/heads/main` |
| Any branch | `repo:<github-org>/<repo>:*` |

For production repo-scoped rules, also add `ref_protected: "true"` to Additional claims — this requires main to be a protected branch and blocks exchange if branch protection is accidentally removed.

Save. The rule gets an `fdrl_...` ID — use this as `ANTHROPIC_FEDERATION_RULE_ID`.

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

## Troubleshooting

**Authentication events dashboard:** [platform.claude.com/settings/workload-identity-federation?tab=history&range=7d](https://platform.claude.com/settings/workload-identity-federation?tab=history&range=7d)

Shows recent token exchange attempts — check here first when a workflow run returns HTTP 401. Each entry shows whether the exchange succeeded, which federation rule matched, and the subject claim from the OIDC JWT. Requires org-admin access to the Anthropic Console.

**Most common silent failure:** The service account is not a member of the target workspace. The exchange returns HTTP 401 with no message identifying this as the cause. Check workspace membership in the Console before investigating further (see [Step 1](#step-1-create-a-service-account)).

---

## Known limitations

| Limitation | Detail |
|---|---|
| **Detection job fails with HTTP 401** | The gh-aw compiler omits `id-token: write` from the auto-generated threat-detection job's permissions block under WIF auth. The detection model never runs and three annotations appear on every run. Fix pending in [github/gh-aw#36460](https://github.com/github/gh-aw/issues/36460). This is the current rollout blocker. |
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

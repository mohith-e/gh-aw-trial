# WIF Administration: Federation Rules, Service Accounts, and Cost Attribution

This doc covers the back-office side of Workload Identity Federation for gh-aw at RealPage. Primary audience: COE. Future audience: IT, once Anthropic ships an admin API that would let us automate provisioning via Terraform or similar.

For the dev-facing guide (how to add WIF to a workflow), see [`docs/wif-auth.md`](wif-auth.md).

---

## RealPage shared resources

The following resources are already provisioned for the `RealPage` GitHub org and shared by all workflows in it.

| Resource | Name | ID |
|---|---|---|
| Federation issuer | GitHub Actions | `fdis_01RPUmB9gNG4qojQ96FWSEDi` |
| Federation rule | `realpage-org` (`repo:RealPage/*`) | `fdrl_01UrTuTXEcPdS3ckapB7re3y` |
| Workspace | `github-actions` | `wrkspc_011kuRkDngP7B49bQc5AZLVJ` |

The `organization-id` (Anthropic org UUID) is `cb16d48f-b95b-4b2c-9e86-a09f46eccb90` — the same for every GitHub org under the same Anthropic organization.

These IDs are hardcoded in `workflows/shared/wif-engine.md` and referenced from `ANTHROPIC_FEDERATION_RULE_ID` / `ANTHROPIC_SERVICE_ACCOUNT_ID` org-level Actions variables. Repos under other GitHub orgs need their own federation rule (see below) but share this workspace and org ID.

---

## Setting up a new GitHub org

You need org-admin access to [console.anthropic.com](https://console.anthropic.com) to create the resources below. Only needed when onboarding a GitHub org for the first time.

### The shared federation issuer

All GitHub Actions workflows — across every GitHub org — use the same federation issuer. You do not need to create a new one.

| Field | Value |
|---|---|
| Name | `GitHub Actions` |
| Issuer URL | `https://token.actions.githubusercontent.com` |
| ID | `fdis_01RPUmB9gNG4qojQ96FWSEDi` |

### Step 1: Create a service account

Navigate to **Settings → Service accounts → Create service account**.

Naming convention: `<github-org>-gh` for org-wide accounts (e.g., `knockrentals-gh`), or `<product>-gh` for product-scoped accounts (e.g., `knock-gh`, `payments-gh`). One service account per product area.

Save — the service account gets an `svac_...` ID.

> **Critical — workspace membership:** After creating the service account, add it as a member of the target workspace. Open the full service account page (**Settings → Service accounts → click the row → Open full page**) and add it to each workspace the federation rule will target. Tokens minted for a workspace the service account is not a member of return HTTP 401 at exchange time with no error message pointing to this cause. This is the most common setup mistake.

### Step 2: Create a federation rule

Navigate to **Settings → Workload Identity Federation → Issuers → GitHub Actions → Federation rules → Add rule**.

For an org-wide rule (all repos in a GitHub org):

| Field | Value |
|---|---|
| Service account | Service account from Step 1 |
| Subject prefix | `repo:<github-org>/*` |
| Audience | `https://api.anthropic.com` |
| Scope | `workspace:developer` |
| Token lifetime | `600` (seconds) |

**Additional claims:**

| Claim | Value | Varies? |
|---|---|---|
| `repository_owner` | The GitHub org (e.g., `RealPage`, `knockrentals`) | **Yes** — one rule per org |
| `enterprise` | `realpage` | **No** — always `realpage` for all RealPage-managed GitHub orgs |

`enterprise: realpage` pins the rule to the RealPage GitHub Enterprise, preventing JWT reuse from a same-named org elsewhere. The value is the slug from `https://github.com/enterprises/realpage`.

For repo-scoped rules (tighter; recommended for production):

| Scope | Subject prefix |
|---|---|
| Single branch | `repo:<github-org>/<repo>:ref:refs/heads/main` |
| Any branch | `repo:<github-org>/<repo>:*` |

For production repo-scoped rules, also add `ref_protected: "true"` to Additional claims — this requires main to be a protected branch and blocks token exchange if branch protection is removed.

Save. The rule gets an `fdrl_...` ID.

### Step 3: Set Actions variables

Set these two variables at the GitHub org level (Settings → Secrets and variables → Actions → Variables), or at the repo level to override the org default:

| Variable | Value |
|---|---|
| `ANTHROPIC_FEDERATION_RULE_ID` | `fdrl_...` from Step 2 |
| `ANTHROPIC_SERVICE_ACCOUNT_ID` | `svac_...` from Step 1 |

---

## Cost attribution

WIF requests are tagged with the service account ID in Anthropic's usage data. Attribute spend per service account using the messages usage report:

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

**Auth events dashboard:** [platform.claude.com/settings/workload-identity-federation?tab=history&range=7d](https://platform.claude.com/settings/workload-identity-federation?tab=history&range=7d)

Shows recent token exchange attempts — check here first when a workflow run returns HTTP 401. Each entry shows whether the exchange succeeded, which federation rule matched, and the subject claim from the OIDC JWT. Requires org-admin access to the Anthropic Console.

---

## Known limitations

| Limitation | Detail |
|---|---|
| Default workspace | Has no `wrkspc_` ID in the Console — omit `workspace-id` from `shared/wif-engine.md` if targeting the default workspace. |

---

## Future: automation via Anthropic admin API

Provisioning today is manual (Console UI + org-level variables). Once Anthropic ships a stable admin API covering service accounts and federation rules, the intent is to automate this via Terraform or a gh-aw workflow — driven by the issue template in `ai-internal-enablement`. Until then, provisioning is a manual admin step by the COE.

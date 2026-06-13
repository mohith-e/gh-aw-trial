# WIF Administration: Federation Rules, Service Accounts, and Cost Attribution

This doc covers the back-office side of Workload Identity Federation for gh-aw at RealPage. Primary audience: COE. Provisioning is now **automated** by the `wif-admin` workflow in `RealPage/ai-internal-enablement` (see [Automated onboarding](#automated-onboarding-recommended)); the manual Console steps remain as a fallback and for the one-time bootstrap.

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

## Automated onboarding (recommended)

The `wif-admin` workflow in [`RealPage/ai-internal-enablement`](https://github.com/RealPage/ai-internal-enablement) provisions WIF resources via the [Anthropic WIF Admin API](https://platform.claude.com/docs/en/manage-claude/wif-admin-api), so you no longer click through the Console for the common cases. It mints a short-lived `org:admin` token at runtime (WIF) and runs idempotent, list-then-create CRUD. Full runbook: [`docs/wif-admin-runbook.md`](https://github.com/RealPage/ai-internal-enablement/blob/main/docs/wif-admin-runbook.md).

**To onboard a service account:** file the **Anthropic service account request** issue form in `ai-internal-enablement` (or run the workflow manually with `action=create-service-account`, inputs `github_org` + `product_name`). The run pauses at a **team-approval gate**; a member of `@RealPage/anthropic-service-account-admins` approves the `wif-provisioning` deployment. On approval the workflow:

- ensures the `github-actions` workspace and the GitHub Actions issuer exist;
- creates the service account (`organization_role: developer`) and adds it to the workspace with role `workspace_developer`;
- creates the federation rule for `repo:<org>/*` targeting that service account;
- prints the `ANTHROPIC_FEDERATION_RULE_ID` + `ANTHROPIC_SERVICE_ACCOUNT_ID` to set (output-only — a human sets the org/repo Actions variables; the workflow can't write them).

**Actions:** `create-service-account`, `archive-service-account`, `create-rule` (targets an existing SA), `archive-rule`, `create-workspace`, `describe-rule`.

**Model — one rule per service account.** A federation rule targets exactly one SA (the minted token acts as that target). Service accounts are per product; a GitHub org can have several. All of an org's rules share subject `repo:<org>/*` + claims (`repository_owner`, `repository_owner_id`), and each targets its own SA. So `ANTHROPIC_FEDERATION_RULE_ID` and `ANTHROPIC_SERVICE_ACCOUNT_ID` are **both per product, set together**.

**Authorization.** Anyone can file/dispatch, but only the `anthropic-service-account-admins` team can approve the gated deployment — that, not who can file or label, is the control. (There is no approval label; the GitHub Environment `wif-provisioning` with required reviewers is the gate.)

**One-time bootstrap (manual, Console).** The `org:admin` federation rule that lets the workflow call the Admin API must be created once in the Console — Anthropic blocks automation from self-granting `org:admin`. See the runbook's bootstrap section. After that, everything below is automated.

---

## Manual provisioning (fallback / bootstrap)

Prefer the automated flow above. These manual Console steps are the fallback and the way to perform the one-time bootstrap. You need org-admin access to [console.anthropic.com](https://console.anthropic.com).

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
| `repository_owner` | The GitHub org, GitHub-canonical case (e.g., `RealPage`, `knockrentals`) | **Yes** — per org |
| `repository_owner_id` | The org's numeric id (`gh api orgs/<org> --jq .id`) | **Yes** — per org |
| `enterprise` | `realpage` | **No** — optional; always `realpage` for RealPage-managed orgs |

A rule targets exactly **one** service account, so an org with multiple product SAs has multiple rules — all sharing the `repo:<org>/*` subject and claims above, each targeting its own SA. The automated workflow pins `repository_owner` + `repository_owner_id` (immutable; survives org renames). `enterprise: realpage` is an alternative/additional pin (the slug from `https://github.com/enterprises/realpage`); the case-sensitive `repository_owner` match is why the canonical org case matters.

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

## Automation status

**Shipped (2026-06): the `wif-admin` workflow** in `ai-internal-enablement` automates provisioning via the Anthropic WIF Admin API — see [Automated onboarding](#automated-onboarding-recommended). Conventional (non-gh-aw) GitHub Actions; deterministic, idempotent, team-gated.

A Terraform/IaC alternative was evaluated and deferred to a backlog spike ([`ai-internal-enablement#827`](https://github.com/RealPage/ai-internal-enablement/issues/827)) — pursue only if a maintained community/Anthropic provider appears.

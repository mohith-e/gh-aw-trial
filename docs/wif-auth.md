# Authentication: Keyless Anthropic Auth for gh-aw

Workflows that use an `ANTHROPIC_API_KEY` repo secret attribute API usage to the key owner's personal account — automated runs look like individual usage in billing reports. Workload Identity Federation (WIF) lets each workflow run mint a short-lived token automatically, attributed to a service account. Nothing to store, nothing to rotate, and cost shows up under the right product in the Anthropic console.

## How it works

When a workflow runs, the GitHub Actions runner mints a short-lived OpenID Connect (OIDC) JWT (`id-token: write` permission required). The gh-aw api-proxy exchanges that JWT with Anthropic for a short-lived bearer token, then forwards requests to the Anthropic API. Your workflow never touches a real key.

## Prerequisites

**gh-aw ≥ v0.83.2** — that release restored WIF auth support for *imported* engine
definitions, which is the pattern below. Check your version:

```bash
gh aw --version
```

Update if behind:

```bash
gh extension upgrade aw
```

> **Version history.** Anthropic WIF landed in **v0.79.6**. From **v0.82.10** through
> **v0.83.1**, importing a shared engine failed to compile
> (`mapping was used where sequence is expected`) because `EngineDefinition.Auth` is a
> sequence and could not express a WIF `auth:` mapping — during that window this doc told
> you to inline the block instead. Fixed in **v0.83.2**
> ([github/gh-aw#47294](https://github.com/github/gh-aw/issues/47294), fixed by
> [#47572](https://github.com/github/gh-aw/pull/47572)). If you are pinned below v0.83.2,
> inline the `engine:` block from `shared/wif-engine.md` instead of importing it.

---

## Add WIF to a workflow

### Step 1: Import the shared WIF engine

Replace `engine: claude` with an import of the shared engine, so the auth config lives in
exactly one place:

```yaml
imports:
  - shared/wif-engine.md

permissions:
  contents: read
  id-token: write
```

`gh aw add` fetches `shared/wif-engine.md` alongside the workflow, so consumers get it
automatically — no extra step.

Add any toolset-required read permissions your workflow needs (e.g., `issues: read`, `pull-requests: read`). The five golden workflows already have the right permissions set.

> **Define `engine:` exactly once.** The imported file supplies it, so an importing
> workflow must **not** declare its own `engine:` block — not even a partial one. Two
> consequences worth knowing:
> - `max-turns` belongs at the **root** level, not under `engine:`; there it coexists with the import.
> - `engine.env` has no import-compatible equivalent (`sandbox.agent.env` is refused by
>   strict mode as an internal implementation detail). A workflow that needs it must keep
>   the whole `engine:` block inline, copied from `shared/wif-engine.md`.

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

The shared engine block references both via `${{ vars.ANTHROPIC_FEDERATION_RULE_ID }}` and `${{ vars.ANTHROPIC_SERVICE_ACCOUNT_ID }}`.

---

## Pin the model: set `GH_AW_DEFAULT_MODEL_CLAUDE`, then override per step

**Never leave a step unpinned.** On the `RealPage` org:

| Variable | Value | Why |
|---|---|---|
| `GH_AW_DEFAULT_MODEL_CLAUDE` | `claude-sonnet-4-6` | catch-all floor, so no step can inherit the CLI default |
| `GH_AW_MODEL_AGENT_CLAUDE` | `claude-sonnet-4-6` | agent work — Sonnet handles it and is ~5× cheaper than Opus |
| `GH_AW_MODEL_DETECTION_CLAUDE` | `claude-opus-4-8` | threat detection is a **security** control; deliberately the stronger model |

**Best practice: use the cheapest agent model that gets the job done, and at least `claude-opus-4-8` for detection.** Those pull in opposite directions on purpose. Agent work is high-volume and Sonnet handles it, so that is where cost discipline belongs. Detection is the prompt-injection and malicious-output guard — a security control — so it is pinned *up*, and it runs on a short prompt, so the delta is small. Do not let detection drift below Opus 4.8 to save money.

Keep `GH_AW_DEFAULT_MODEL_CLAUDE` set as well, even with both per-step variables in place. It is the floor: if gh-aw adds a step later, or a per-step variable is removed, the floor catches it instead of the step silently inheriting whatever the bundled CLI defaults to.

A gh-aw run invokes the Claude CLI more than once — the **agent** step and the **threat-detection** step are separate invocations reading separate variables, each falling back to the same shared default:

| Step | Variable it reads | Falls back to |
|---|---|---|
| agent | `GH_AW_MODEL_AGENT_CLAUDE` | `GH_AW_DEFAULT_MODEL_CLAUDE` |
| threat detection | `GH_AW_MODEL_DETECTION_CLAUDE` | `GH_AW_DEFAULT_MODEL_CLAUDE` |

`GH_AW_MODEL_AGENT_CLAUDE` pins **only the agent**. Detection never reads it. If no variable resolves for a step, no `--model` flag is passed and that step inherits whatever the pinned Claude CLI defaults to — which changes between gh-aw releases.

> **Why this changed.** Setting only `GH_AW_MODEL_AGENT_CLAUDE` left threat detection
> unpinned. That was harmless until gh-aw **v0.83.4** bumped the bundled Claude CLI from
> 2.1.214 to 2.1.220, moving the unpinned default from `claude-opus-4-8` to
> `claude-opus-5`. Detection then failed on **every run** while the job still reported
> **success** — a green run was not actually being scanned:
>
> ```
> API Error: 400 Model "claude-opus-5" has no AI credits pricing and no default
> pricing is configured. Set apiProxy.defaultAiCreditsPricing in the AWF config
> ... or add the model to the pricing catalog.
> ```
>
> **"AI credits" is the AWF api-proxy's own metering unit, not an Anthropic entitlement.**
> The proxy meters each run against a credit budget (`GH_AW_MAX_AI_CREDITS`, default 1000
> for the agent step / 400 for detection) and needs a per-model input/output rate from its
> pricing catalog to do the conversion. `claude-opus-5` is absent from AWF v0.27.42's
> catalog, so the proxy rejects the request with a 400 **before it reaches Anthropic**.
> Nothing to do with your Anthropic spend or entitlements.
>
> This is a version skew in gh-aw itself — the bundled CLI defaults to a model the bundled
> proxy cannot price — and upstream is hitting it too (several open
> `has no AI credits pricing for model (claude-opus-5)` issues in `github/gh-aw`).
>
> Measured: 6 failures per run in 8/8 runs on v0.83.4, 0 in 4 runs on v0.82.14. Details in
> [ai-internal-enablement#1139](https://github.com/RealPage/ai-internal-enablement/issues/1139).
>
> **Two ways out.** Pin a model that *is* in the catalog (what the table above does —
> `claude-opus-4-8` and `claude-sonnet-4-6` both are), or set
> `sandbox.agent.default-ai-credits-pricing` in frontmatter to supply a fallback rate
> (added in v0.83.0 for exactly this). Pinning is preferred: it is explicit about which
> model runs, rather than letting an unpriced default through at a guessed rate.

Precedence is `per-workflow model:` → per-step variable → `GH_AW_DEFAULT_MODEL_CLAUDE` → CLI default. The `RealPage` setup above uses exactly that: the floor nothing falls through, plus a per-step override raising detection to Opus. Verified live in [run 30337740916](https://github.com/RealPage/ai-internal-enablement/actions/runs/30337740916) — `agent -> claude-sonnet-4-6`, `detection -> claude-opus-4-8`, zero credit errors.

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

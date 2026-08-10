# Self-hosted runners

Two examples for teams running agentic workflows on self-hosted runner pools:

| File | What it is |
|------|-----------|
| [`hello-self-hosted.md`](../../workflows/hello-self-hosted.md) | Minimal working example. A gh-aw workflow pinned to a self-hosted pool that proves it can reach an internal-only host. |
| [`netcheck-self-hosted.yml`](../../workflows/netcheck-self-hosted.yml) | Diagnostic. Plain GitHub Actions — no agent — that names which network layer broke when the example doesn't work. |

Networking is the main thing that goes wrong with self-hosted adoption. Pointing
a workflow at an internal pool looks like a one-line `runs-on:` change, and it is
— right up until the runner can't reach something, at which point a gh-aw run
fails with an agent-shaped error a long way from the actual cause. The split
above exists so you can answer "is the network the problem?" in about 30 seconds
without running an agent at all.

## Installing them

```bash
gh aw add RealPage/agentic-workflows/workflows/hello-self-hosted.md
```

`netcheck-self-hosted.yml` is plain GitHub Actions, and `gh aw add` only
distributes gh-aw markdown workflows. Copy it into `.github/workflows/`
manually — same as [`tfs-mirror.yml`](../../workflows/tfs-mirror.yml).

Both files pin `enterprise-global-runners`, RealPage's long-lived VM pool. Change
the group to whatever your pool is called.

## Why the hello example checks an internal host

Reaching `api.anthropic.com` proves nothing about self-hosting — a
GitHub-hosted runner needs that too. The example checks
`artifacts.realpage.com`, which resolves to an RFC1918 address and answers only
from inside the corporate network, so a completed TLS handshake is real evidence
the job landed on an internal runner.

It's a TLS handshake rather than an HTTP request on purpose: the result then
doesn't depend on whether the host wants credentials.

Swap in whatever internal host your workflows actually depend on, and put the
same host in the diagnostic's `TARGET_HOSTS`.

## Only the agent job runs on your pool

gh-aw compiles a workflow into several jobs. A root-level `runs-on:` applies to
the **agent job**; the activation and safe-output jobs around it stay on
GitHub-hosted runners. This is usually what you want — those jobs talk to the
GitHub API, not to your internal network — but it does mean pinning a pool is
not the same as running everything inside the network. If a safe output (or
another framework job) needs to reach the internal network too, see
[Configuring the framework job runner](https://github.github.com/gh-aw/reference/self-hosted-runners/#configuring-the-framework-job-runner)
for `runs-on-slim:` and `safe-outputs.runs-on:`.

## Pool topology: plain VM vs. GKE/ARC

The examples target a long-lived VM pool: native Docker daemon, corporate DNS,
one filesystem. Pools backed by GKE/ARC pods are a different architecture and
need more configuration:

```yaml
runner:
  topology: arc-dind
```

That setting handles the runner/daemon filesystem split, staging a sysroot and
daemon-visible mounts. Don't set it on a VM pool — there's no split to bridge,
and it adds machinery for a problem you don't have.

Two things only bite on `arc-dind`:

- **DNS.** ARC pods often have a link-local resolver as their only nameserver.
  See the AWF DNS fallback below.
- **Copilot copy step.** Under `arc-dind` with the firewall enabled, gh-aw emits
  a "Copy Copilot CLI to daemon-visible path" step regardless of which engine the
  workflow declares. On a `claude` workflow no Copilot binary exists, so
  `cp "$(command -v copilot)"` fails on an empty source path. The workaround is a
  stub `copilot` on `PATH`. Make the stub **exit non-zero** — the copy step only
  runs `command -v` / `cp` / `chmod` and never executes it, so a failing stub
  satisfies the step, while a stub that exits 0 would let anything actually
  invoking Copilot fail silently while reporting green.

## Known failure classes

**SNI-based egress filtering.** TCP to port 443 connects, but the TLS handshake
is reset specifically when SNI names the blocked host. The tell is
`[B] fails, [C] passes` — same IP, different SNI works. This is a firewall
allowlist question for whoever owns the subnet, not something a workflow can fix.

**AWF discards a working resolver.** AWF treats link-local and cloud-metadata
nameservers (`169.254.*`, `168.63.129.16`, `100.100.100.100`) as non-portable and
substitutes `8.8.8.8`/`8.8.4.4`. On a GKE/ARC pool the discarded address is often
the pod's only resolver, and clusters that block egress to public DNS then leave
squid unable to resolve anything — every request dies as
`CONNECT 503 TCP_TUNNEL:HIER_NONE`, on all hosts alike. It reads like a total
outage rather than a DNS fault. Filed upstream as
[github/gh-aw-firewall#7185](https://github.com/github/gh-aw-firewall/issues/7185).
Workaround: give the runner a routable resolver (a kube-dns ClusterIP or
corporate DNS) that AWF doesn't filter.

**Copilot engine on a runner without sudo.** `install_copilot_cli.sh` calls plain
`sudo` with no fallback and hard-aborts if the runner can't escalate. Nothing
here uses `engine: copilot`, so this is unexercised — but it's a trap if you
adapt these examples to that engine. Prior art:
[github/gh-aw#18188](https://github.com/github/gh-aw/issues/18188) (closed
won't-fix).

## Reading the diagnostic

Per host, it resolves DNS, probes TCP/443, then runs three TLS handshakes:

| Test | What it does |
|---|---|
| `[A]` | By hostname, SNI = host — couples DNS and TLS |
| `[B]` | IP-pinned, SNI = host — TLS only, no DNS |
| `[C]` | IP-pinned, SNI = `example.com` — SNI-fronting control |

| Result | Verdict |
|---|---|
| `[B]` passes | Host is fine |
| `[B]` fails, `[C]` passes | SNI-based egress block |
| `[B]` and `[C]` fail, TCP open | TLS blocked, not SNI-selective |
| TCP/443 blocked | Routing or firewall, not TLS |
| `[A]` fails, `[B]` passes | DNS is the fault, not TLS |
| Nothing resolves | DNS is the fault; TLS tests are skipped |

All hosts failing identically usually means DNS rather than per-host blocking.
The job exits non-zero if any host is not `OK`, and writes a summary table to the
run's step summary.

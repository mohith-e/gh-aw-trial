---
name: "Hello — self-hosted runner"
on:
  workflow_dispatch:

# Long-lived VM pool with corporate DNS and a native Docker daemon. Pools built
# on GKE/ARC pods need `runner: topology: arc-dind` as well — see
# docs/workflows/self-hosted-runners.md.
runs-on:
  group: enterprise-global-runners

timeout-minutes: 5

imports:
  - shared/wif-engine.md

permissions:
  contents: read
  id-token: write

network:
  allowed:
    - github
    - artifacts.realpage.com

# Without this the agent is handed the default safe outputs and files an issue
# on every run. An example that litters the repo is worse than no example.
safe-outputs:
  noop:

steps:
  - name: Checkout repository
    uses: actions/checkout@v7.0.1
    with:
      persist-credentials: false
  # The point of this example. This step runs in the compiled `agent` job, the
  # one job gh-aw pins to `runs-on:` above, so a passing handshake here is
  # actual proof of where that job landed — reaching Anthropic alone proves
  # nothing, since a GitHub-hosted runner does that too. artifacts.realpage.com
  # resolves and answers only from inside the corporate network. A TLS
  # handshake rather than an HTTP request, so the result does not depend on the
  # host's auth behaviour.
  # If this fails, run netcheck-self-hosted.yml — it tells you which layer broke.
  - name: Verify internal-only host is reachable
    run: |
      echo | timeout 12 openssl s_client \
        -connect artifacts.realpage.com:443 \
        -servername artifacts.realpage.com 2>&1 | grep -q 'Certificate chain'
      echo "artifacts.realpage.com reachable — this job is running inside the network."

---

# Hello from a self-hosted runner

Write a haiku about GitHub Actions running on a self-hosted enterprise runner.
Print the haiku and then say "Done!"

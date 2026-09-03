# Changelog

## 1.0.0 (2026-09-03)


### ⚠ BREAKING CHANGES

* **implement-issue:** implement-issue's default behavior changes for every existing agent:implement consumer — runs stop after the plan comment unless agent:skip-plan-review is set beforehand. See docs/migrations.md for the upgrade steps and new required labels.
* **tfs:** workflows/tfs-review-pr-mirrored.md is removed. Consumer stubs importing it must import workflows/tfs-review-pr.md instead and set the repo variable TFS_USE_MIRROR=true to keep the mirror transport. See docs/migrations.md.
* **tfs:** workflows/tfs-implement-mirrored.md is removed. Consumer stubs importing it must import workflows/tfs-implement.md instead and set the repo variable TFS_USE_MIRROR=true to keep the mirror transport.

### Features

* add agent-generate-tests workflow ([4ca7ac4](https://github.com/mohith-e/gh-aw-trial/commit/4ca7ac45ed0127ab8ba1feb37a02adde072a491b))
* add agent-refactor workflow ([229d92e](https://github.com/mohith-e/gh-aw-trial/commit/229d92e7cda24d481a09657c377435c533ec1a96))
* add agent-review-pr workflow ([e2dc2f8](https://github.com/mohith-e/gh-aw-trial/commit/e2dc2f86f1c07b2e9bbe06f29aeeed2b98ce09aa))
* add fix-failing-tests workflow ([0be6e80](https://github.com/mohith-e/gh-aw-trial/commit/0be6e802cde176e7215ce1eda8e850bef98ac291))
* add Fortify SAST triage and remediation workflows ([62c8cce](https://github.com/mohith-e/gh-aw-trial/commit/62c8ccee2bb7ba21a12cb50b14eed011bf46c0d2))
* Add Fortify SAST triage and remediation workflows ([37ff928](https://github.com/mohith-e/gh-aw-trial/commit/37ff928696658f6f2ebcea796a8454cae2f77148))
* add implement-issue workflow ([aa689c2](https://github.com/mohith-e/gh-aw-trial/commit/aa689c2c772802da453af24a9e27e2c8f7fff80e))
* add implement-issue workflow ([671d4f4](https://github.com/mohith-e/gh-aw-trial/commit/671d4f41ccb1ccfd771592fd654f200410aa5b67))
* add PME triage workflow ([16ce312](https://github.com/mohith-e/gh-aw-trial/commit/16ce312e951b62d5567058e9dba60758b532fd31))
* add PME triage workflow ([dad065d](https://github.com/mohith-e/gh-aw-trial/commit/dad065de42ca6d9fbfeeb52df7b23860b04649fa)), closes [#36](https://github.com/mohith-e/gh-aw-trial/issues/36)
* add priority_filter dispatch input to pme-triage ([dac83e4](https://github.com/mohith-e/gh-aw-trial/commit/dac83e4b7971e73e3c8859a7b8b92040c239a872))
* add release-please and conventional commits workflows ([920549e](https://github.com/mohith-e/gh-aw-trial/commit/920549e6978aa3a06c924874bc7ebd3039d701a7))
* add repo memory for PME cross-reference state caching ([e7d4f1c](https://github.com/mohith-e/gh-aw-trial/commit/e7d4f1c209570dfbbc4946c0442cfd68329a2256))
* add rollout gate + age filter to tfs-review-pr-mirrored ([f94669b](https://github.com/mohith-e/gh-aw-trial/commit/f94669b9b17b05010e28be3252aa2fe2985b4fee))
* add test-improver workflow (Claude via WIF, adapted from githubnext/agentics) ([#130](https://github.com/mohith-e/gh-aw-trial/issues/130)) ([c210484](https://github.com/mohith-e/gh-aw-trial/commit/c21048423d1165ab47ce16114de55571926ba3c5))
* add tfs-review-pr-mirrored workflow ([c719177](https://github.com/mohith-e/gh-aw-trial/commit/c71917710bf3ea0d6c89b589737e33ecce1e7b1e))
* add tfs-review-pr-mirrored workflow ([6076651](https://github.com/mohith-e/gh-aw-trial/commit/6076651324e66042bc50109974839451f7cd2592))
* group related PMEs into single issues and add SF write-back TODO ([05b0b5c](https://github.com/mohith-e/gh-aw-trial/commit/05b0b5c0075258237c260e95c7733dff17b0edb8))
* **implement-issue:** address PR [#28](https://github.com/mohith-e/gh-aw-trial/issues/28) review feedback ([bd108ca](https://github.com/mohith-e/gh-aw-trial/commit/bd108ca95a2a199e5e5505e8e30b7a1794cb533b))
* **implement-issue:** require human plan approval by default, skippable via label ([#145](https://github.com/mohith-e/gh-aw-trial/issues/145)) ([c017714](https://github.com/mohith-e/gh-aw-trial/commit/c0177148a04520b680e22138a770b99c0da40c25))
* incremental re-review + /review-ai scoping instructions ([c952043](https://github.com/mohith-e/gh-aw-trial/commit/c9520430c28bb49a8632f51fc2db3ffcb70a61eb))
* pme-triage v2 — SF write-back, enhancement grouping, WAD detection ([e0fa9a5](https://github.com/mohith-e/gh-aw-trial/commit/e0fa9a51eb9d862acc9dafd648b8bcf685fc9202))
* pme-triage v2 — SF write-back, enhancement grouping, WAD detection ([e95a6ee](https://github.com/mohith-e/gh-aw-trial/commit/e95a6ee0d589ca23af896d60550a6af325530894))
* **pme-triage:** expand SF context with Chatter, comment fields, and fix issue quality ([#55](https://github.com/mohith-e/gh-aw-trial/issues/55)) ([fe58de4](https://github.com/mohith-e/gh-aw-trial/commit/fe58de45b510a61e7bb0141665b7c2840f04e038)), closes [#53](https://github.com/mohith-e/gh-aw-trial/issues/53)
* review AI-authored PRs + add /review-ai on-demand trigger ([45fe417](https://github.com/mohith-e/gh-aw-trial/commit/45fe4171d699302498183c658e8a1eed652284f4))
* standardise releases with release-please and conventional commits enforcement ([ee83e4f](https://github.com/mohith-e/gh-aw-trial/commit/ee83e4fc8d591b2ba1ac07cb07e7c88f5f5e8efb))
* **tfs-implement:** add mirrored variant for large repos ([1340040](https://github.com/mohith-e/gh-aw-trial/commit/13400407330523b87667d374fa636085947800b7))
* **tfs-implement:** add mirrored variant for large repos ([e6b2421](https://github.com/mohith-e/gh-aw-trial/commit/e6b2421134f85cb114eda95b602a45c27d380d69))
* **tfs-implement:** add reusable TFS work item implementer ([#73](https://github.com/mohith-e/gh-aw-trial/issues/73)) ([9c1f21f](https://github.com/mohith-e/gh-aw-trial/commit/9c1f21f56075b651a69bfbcd9c338f6525c02659))
* **tfs-implement:** add tfs-mirror companion and optimize the clone path ([252ffa7](https://github.com/mohith-e/gh-aw-trial/commit/252ffa71740d2b1e105c734275e9d546762f2698))
* **tfs-implement:** clone target branch directly from TFS ([401f95d](https://github.com/mohith-e/gh-aw-trial/commit/401f95da8e5e0e26b12e9e6070b492270aa81d38))
* **tfs-mirror:** make chunked bootstrap truly resumable + robust to transient errors ([4239f31](https://github.com/mohith-e/gh-aw-trial/commit/4239f316abb5777b657a3eeacc86f4e41bfdb3a2))
* **tfs-mirror:** support chunked bootstrap for large branches ([34c0caf](https://github.com/mohith-e/gh-aw-trial/commit/34c0caf12cdc96e5387657454046cb49a1021cb4))
* **tfs-mirror:** support chunked bootstrap for large branches ([535ccb5](https://github.com/mohith-e/gh-aw-trial/commit/535ccb54372f5bb53357d100f2f0c4d330a8c3a3))
* **tfs-review-pr-mirrored:** coordinator/worker fan-out ([1f7a8f3](https://github.com/mohith-e/gh-aw-trial/commit/1f7a8f39d86a11cea780af718b7dc43758bb2ecf))
* **wif:** extract shared engine config + untrack workflows/*.lock.yml ([#89](https://github.com/mohith-e/gh-aw-trial/issues/89)) ([684054f](https://github.com/mohith-e/gh-aw-trial/commit/684054f3dec89e22eb63f2d2083e8b272fdfcd75))
* **wif:** migrate all 5 golden workflows to WIF auth ([#93](https://github.com/mohith-e/gh-aw-trial/issues/93)) ([16d267c](https://github.com/mohith-e/gh-aw-trial/commit/16d267c6031b96b342e1efd75d08a3275ec4d633))
* **workflows:** coordinator/worker fan-out for tfs-review-pr-mirrored ([2294210](https://github.com/mohith-e/gh-aw-trial/commit/22942103a63ff6465b6ccb5fa5708e115ba8b122))
* **workflows:** raise tfs-review-pr-mirrored to a 5-min poll cadence ([b24ff17](https://github.com/mohith-e/gh-aw-trial/commit/b24ff171979212ff3161b9f30eb05478dc3ab93f))
* **workflows:** self-hosted runner example + network diagnostic ([#137](https://github.com/mohith-e/gh-aw-trial/issues/137)) ([c5c1aee](https://github.com/mohith-e/gh-aw-trial/commit/c5c1aeee038eb49618f302e85b20145bf5502898))
* **workflows:** use a dedicated TFS_REVIEW_PAT for tfs-review-pr-mirrored ([1aaab90](https://github.com/mohith-e/gh-aw-trial/commit/1aaab900366971b9c2162807521adc5c86872f89))


### Bug Fixes

* add contents:read to pre-activation, correct push_repo_memory doc ([7c96ec2](https://github.com/mohith-e/gh-aw-trial/commit/7c96ec28277eb7cc6f0ed20b1f3ed7d3ba6f20c5))
* add label-missing fallbacks for enhancement-backlog and wad:customer-impact ([309a9c6](https://github.com/mohith-e/gh-aw-trial/commit/309a9c6fd07aa7ea7c7a4345f26f16e3873aadeb))
* add tfs.realpage.com to network allowlist to prevent URL redaction ([b80726e](https://github.com/mohith-e/gh-aw-trial/commit/b80726eb90ad21714ea2c981ba97adf3a0796bf7))
* address Copilot review findings on tfs-review-pr-mirrored ([c75b20f](https://github.com/mohith-e/gh-aw-trial/commit/c75b20f1ea7918036c809e8f2449f21fb909a334))
* **auto-remediation:** rename safe-inputs → mcp-scripts ([#106](https://github.com/mohith-e/gh-aw-trial/issues/106)) ([5713947](https://github.com/mohith-e/gh-aw-trial/commit/5713947fbbab7943a69ca4456dfbbcf706e99859)), closes [#104](https://github.com/mohith-e/gh-aw-trial/issues/104)
* batch sf-comment into single call (custom jobs are max 1) ([95f31bb](https://github.com/mohith-e/gh-aw-trial/commit/95f31bbe5395120e46ef14e1affbfcc64a4afcac))
* bump artifact actions to v7/v8 (Node.js 20 deprecation) ([2507281](https://github.com/mohith-e/gh-aw-trial/commit/25072816f9b8dec5a63100f8a5f5526fd07465a2))
* correct repo memory path and push instruction ([62ada36](https://github.com/mohith-e/gh-aw-trial/commit/62ada364d5049426e0276224af697997e12e4918))
* correct state file path on memory branch (root, not subdir) ([8298b82](https://github.com/mohith-e/gh-aw-trial/commit/8298b82de9d0275a5af6c3a405883fcbad95bb3d))
* drop Claude API mention from README intro ([#49](https://github.com/mohith-e/gh-aw-trial/issues/49)) ([3cc979a](https://github.com/mohith-e/gh-aw-trial/commit/3cc979a454cf329ffd1b9d76f5963b53d852f874))
* drop TFS_TARGET_BRANCH from tfs-review-pr-mirrored (var-name collision) ([8bbfa1b](https://github.com/mohith-e/gh-aw-trial/commit/8bbfa1b8ca181a0b159a2908078690562bcd4356))
* eliminate post-creation issue search loop, lower create-issue max to 5 ([a8f64a8](https://github.com/mohith-e/gh-aw-trial/commit/a8f64a82b8a4aa6f333c4b385977362033e4f603))
* fix nested code fence rendering in pme-triage body template ([1ed5485](https://github.com/mohith-e/gh-aw-trial/commit/1ed548531860e707408918a6995ea649aa7b7bc9))
* **fortify-triage:** extract username and release ID from secrets ([d6465d9](https://github.com/mohith-e/gh-aw-trial/commit/d6465d9d7f717a72860a680932b036a5300d66b3))
* hybrid pre-step — agent-level steps for GH, mcp-scripts for SF ([609eddb](https://github.com/mohith-e/gh-aw-trial/commit/609eddb40b5ca044cdfbd6206aa2127e64fb2ba1))
* inline release-type simple and remove release-please-config.json ([f3b47d7](https://github.com/mohith-e/gh-aw-trial/commit/f3b47d71db802cb5f16a45cb61ea3a8348a56c5a))
* only apply labels if they exist, fall back to title suffix ([d35ee63](https://github.com/mohith-e/gh-aw-trial/commit/d35ee63c69aa3d3592476779703d67f6f9b1caa9))
* pass GITHUB_TOKEN env var to action-semantic-pull-request ([0eaadf1](https://github.com/mohith-e/gh-aw-trial/commit/0eaadf1220a2f1edd01fd819eeee8990f1db5340))
* pass pre-step context via artifact (on.steps → agent) ([4fa1631](https://github.com/mohith-e/gh-aw-trial/commit/4fa163181ba2a6501a22deda7e826f2fa43331d3))
* **pme-triage:** handle SF error array in Chatter response validation ([#57](https://github.com/mohith-e/gh-aw-trial/issues/57)) ([9f1c3cd](https://github.com/mohith-e/gh-aw-trial/commit/9f1c3cd4f1820e5e05103ccefe3e455fed270326))
* **pme-triage:** include nested comment replies in Chatter extraction ([#59](https://github.com/mohith-e/gh-aw-trial/issues/59)) ([ab061a3](https://github.com/mohith-e/gh-aw-trial/commit/ab061a317b2e1b9aeda0d382629a65b0f8a409b5))
* **pme-triage:** inline Chatter via Feeds subquery, eliminate N+1 API calls ([#61](https://github.com/mohith-e/gh-aw-trial/issues/61)) ([fa12868](https://github.com/mohith-e/gh-aw-trial/commit/fa1286872cbad13dd06107df2e9376949d0ad154))
* **pme-triage:** use Composite + Chatter REST API instead of SOQL on FeedItem ([#58](https://github.com/mohith-e/gh-aw-trial/issues/58)) ([10f39a5](https://github.com/mohith-e/gh-aw-trial/commit/10f39a5369c32d916cbb0d1b96a8bc9883e9368f))
* **pme-triage:** use per-PME Chatter Connect REST API for feed fetch ([#60](https://github.com/mohith-e/gh-aw-trial/issues/60)) ([ceef119](https://github.com/mohith-e/gh-aw-trial/commit/ceef1190204161b22297986b5328f04f5127c276))
* remove stray wif-poc test artifact from .github/workflows ([#96](https://github.com/mohith-e/gh-aw-trial/issues/96)) ([8e059f9](https://github.com/mohith-e/gh-aw-trial/commit/8e059f9dae3d0141430e431d0961c96e04a6a0d5)), closes [#95](https://github.com/mohith-e/gh-aw-trial/issues/95)
* remove token from release-please, switch to action-semantic-pull-request pinned to SHA ([e15a505](https://github.com/mohith-e/gh-aw-trial/commit/e15a50523a8057f36129d38d77ec7ef6fcc5e36f))
* replace FeedItem SOQL dedup with GitHub issue body marker ([ce12b38](https://github.com/mohith-e/gh-aw-trial/commit/ce12b384160909912d8e65b16de65cac102f9216))
* replace workflow_dispatch inputs with env section for schedule compatibility ([f3fbb3e](https://github.com/mohith-e/gh-aw-trial/commit/f3fbb3e4ce72ffaae6650c34d3997ed2a193e165))
* replace workflow_dispatch inputs with env section for schedule compatibility ([98ab7d5](https://github.com/mohith-e/gh-aw-trial/commit/98ab7d5d8ee702e6f0ba901cb044ed9bfbe02322))
* restructure SOQL query construction to ensure filters are applied ([6c8d59b](https://github.com/mohith-e/gh-aw-trial/commit/6c8d59b9abf7fa510e8767d32a1b7e6ba68b7ab0))
* revert contents:write — repo memory handles its own permissions ([2baaf1e](https://github.com/mohith-e/gh-aw-trial/commit/2baaf1ef53ed588497d08d6c3aaca5b2d4d2d8c8))
* safer defaults for fix-failing-tests trigger ([#50](https://github.com/mohith-e/gh-aw-trial/issues/50)) ([7e18444](https://github.com/mohith-e/gh-aw-trial/commit/7e184447682fc323010680367f61d4f124a0e5e2))
* set max: 15 on sf-comment custom safe output job ([2e3936e](https://github.com/mohith-e/gh-aw-trial/commit/2e3936e9452521cbe90b3fdaefe7c4494524e85b))
* soften add-wizard safety note to reflect observed behavior ([#48](https://github.com/mohith-e/gh-aw-trial/issues/48)) ([2ac47e0](https://github.com/mohith-e/gh-aw-trial/commit/2ac47e01ac399123f17011d6f3e73f67b8460687))
* stop tfs-review-pr-mirrored re-posting its own review as a /review-ai command ([680324f](https://github.com/mohith-e/gh-aw-trial/commit/680324fa70adf6f8c594769da17d660cd0a23b4e))
* surface pre-step errors instead of silently falling back ([977acd0](https://github.com/mohith-e/gh-aw-trial/commit/977acd08dc36e07a6279f0d221065ac9a18ac6e6))
* **tfs-implement-mirrored:** apply review findings from loft-core validation ([c83f276](https://github.com/mohith-e/gh-aw-trial/commit/c83f276ee8d207e0ab94fa2fbc8e092e26195a8b))
* **tfs-implement:** git am --keep-cr so CRLF files apply cleanly ([#87](https://github.com/mohith-e/gh-aw-trial/issues/87)) ([30ea76f](https://github.com/mohith-e/gh-aw-trial/commit/30ea76f7b94915f3b18ce60dcb682a5e9ca56a8c))
* **tfs-review-pr-mirrored:** gate dispatch job to coordinator runs, fix worker ref ([72820c2](https://github.com/mohith-e/gh-aw-trial/commit/72820c2334a9e3e024c99c3b0de0f30ae97c4bd8))
* **tfs-review-pr-mirrored:** retry read-only TFS calls, never the writes ([bb94cd3](https://github.com/mohith-e/gh-aw-trial/commit/bb94cd3fe98e6614547ec507aaceb6c472d381b4))
* update auto-remediation onboarding note to reflect env: pattern ([f446c7a](https://github.com/mohith-e/gh-aw-trial/commit/f446c7a5bb06899b3ae46cbf95ea9cd288313199))
* use GitHub API for state file in pre-step (no git checkout) ([29d2f87](https://github.com/mohith-e/gh-aw-trial/commit/29d2f8715b3aa03de15e7fa2af0db39d0dc73bbd))
* use on.steps for pre-step (runs in pre-activation job, not agent) ([0750ffd](https://github.com/mohith-e/gh-aw-trial/commit/0750ffd94c48b6219eca5aabb294d3002d86912a))
* use repository variable for SF_OAUTH_CLIENT_ID instead of secret ([2ae3957](https://github.com/mohith-e/gh-aw-trial/commit/2ae395713cd3857575ec88ef2ad38e4e97359f7c))
* **wif:** add workspace-id, remove placeholder ANTHROPIC_API_KEY ([#98](https://github.com/mohith-e/gh-aw-trial/issues/98)) ([d9ad7ca](https://github.com/mohith-e/gh-aw-trial/commit/d9ad7ca1f387ed75e2595145cf80c3bee0ff7d00)), closes [#95](https://github.com/mohith-e/gh-aw-trial/issues/95)
* **wif:** restore placeholder ANTHROPIC_API_KEY in shared engine ([#94](https://github.com/mohith-e/gh-aw-trial/issues/94)) ([9cbcdcf](https://github.com/mohith-e/gh-aw-trial/commit/9cbcdcf425e1117314c873f8e99965f03984ee6b))
* **workflows:** inline WIF engine auth — gh-aw v0.82.10 breaks shared import ([#120](https://github.com/mohith-e/gh-aw-trial/issues/120)) ([f41758f](https://github.com/mohith-e/gh-aw-trial/commit/f41758f735bd3d4a411e129da817488c4fbb38c6))
* **workflows:** inline WIF engine auth in tfs-review-pr-mirrored ([#123](https://github.com/mohith-e/gh-aw-trial/issues/123)) ([d2f69f5](https://github.com/mohith-e/gh-aw-trial/commit/d2f69f58bb8a493d5f38077720c1598e1bf63566))
* **workflows:** restore shared/wif-engine.md import on gh-aw v0.83.4 ([#128](https://github.com/mohith-e/gh-aw-trial/issues/128)) ([2685bb1](https://github.com/mohith-e/gh-aw-trial/commit/2685bb19eface2b77f0d1147616be77d9027f43b))
* **workflows:** un-scope tfs-review-pr-mirrored's concurrency group by pr_id ([45f3231](https://github.com/mohith-e/gh-aw-trial/commit/45f323108c1c436ab541dca73c757c6ef85e8ffe))


### Performance Improvements

* move data fetching to deterministic pre-step ([19dd825](https://github.com/mohith-e/gh-aw-trial/commit/19dd825439268ed01f51ce3820453ac8edf539ec))


### Reverts

* **workflows:** revert tfs-review-pr-mirrored to 15-min cadence ([6fd3b90](https://github.com/mohith-e/gh-aw-trial/commit/6fd3b90e034fa405af4e7bdb3f4d2541906ea3e6))


### Documentation

* **tfs:** add consumer migration notes for the v1.0.0 renames ([#139](https://github.com/mohith-e/gh-aw-trial/issues/139)) ([bd41559](https://github.com/mohith-e/gh-aw-trial/commit/bd415595f0bb935208ef801e294e0c506cfcdea6))


### Code Refactoring

* **tfs:** shared import modules, collapse the mirrored variants, add tfs-review-pr ([#138](https://github.com/mohith-e/gh-aw-trial/issues/138)) ([9f26296](https://github.com/mohith-e/gh-aw-trial/commit/9f26296e60b4270721600fa806d86abf795f9de4))

## [2.0.0](https://github.com/RealPage/agentic-workflows/compare/v1.0.0...v2.0.0) (2026-08-14)


### ⚠ BREAKING CHANGES

* **implement-issue:** implement-issue's default behavior changes for every existing agent:implement consumer — runs stop after the plan comment unless agent:skip-plan-review is set beforehand. See docs/migrations.md for the upgrade steps and new required labels.

### Features

* **implement-issue:** require human plan approval by default, skippable via label ([#145](https://github.com/RealPage/agentic-workflows/issues/145)) ([c017714](https://github.com/RealPage/agentic-workflows/commit/c0177148a04520b680e22138a770b99c0da40c25))

## [1.0.0](https://github.com/RealPage/agentic-workflows/compare/v0.7.0...v1.0.0) (2026-08-10)


### ⚠ BREAKING CHANGES

* **tfs:** workflows/tfs-review-pr-mirrored.md is removed. Consumer stubs importing it must import workflows/tfs-review-pr.md instead and set the repo variable TFS_USE_MIRROR=true to keep the mirror transport. See docs/migrations.md.
* **tfs:** workflows/tfs-implement-mirrored.md is removed. Consumer stubs importing it must import workflows/tfs-implement.md instead and set the repo variable TFS_USE_MIRROR=true to keep the mirror transport.

### Features

* add test-improver workflow (Claude via WIF, adapted from githubnext/agentics) ([#130](https://github.com/RealPage/agentic-workflows/issues/130)) ([c210484](https://github.com/RealPage/agentic-workflows/commit/c21048423d1165ab47ce16114de55571926ba3c5))
* add tfs-review-pr-mirrored workflow ([c719177](https://github.com/RealPage/agentic-workflows/commit/c71917710bf3ea0d6c89b589737e33ecce1e7b1e))
* **tfs-review-pr-mirrored:** coordinator/worker fan-out ([1f7a8f3](https://github.com/RealPage/agentic-workflows/commit/1f7a8f39d86a11cea780af718b7dc43758bb2ecf))
* **workflows:** coordinator/worker fan-out for tfs-review-pr-mirrored ([2294210](https://github.com/RealPage/agentic-workflows/commit/22942103a63ff6465b6ccb5fa5708e115ba8b122))
* **workflows:** raise tfs-review-pr-mirrored to a 5-min poll cadence ([b24ff17](https://github.com/RealPage/agentic-workflows/commit/b24ff171979212ff3161b9f30eb05478dc3ab93f))
* **workflows:** self-hosted runner example + network diagnostic ([#137](https://github.com/RealPage/agentic-workflows/issues/137)) ([c5c1aee](https://github.com/RealPage/agentic-workflows/commit/c5c1aeee038eb49618f302e85b20145bf5502898))
* **workflows:** use a dedicated TFS_REVIEW_PAT for tfs-review-pr-mirrored ([1aaab90](https://github.com/RealPage/agentic-workflows/commit/1aaab900366971b9c2162807521adc5c86872f89))


### Bug Fixes

* address Copilot review findings on tfs-review-pr-mirrored ([c75b20f](https://github.com/RealPage/agentic-workflows/commit/c75b20f1ea7918036c809e8f2449f21fb909a334))
* **tfs-review-pr-mirrored:** gate dispatch job to coordinator runs, fix worker ref ([72820c2](https://github.com/RealPage/agentic-workflows/commit/72820c2334a9e3e024c99c3b0de0f30ae97c4bd8))
* **tfs-review-pr-mirrored:** retry read-only TFS calls, never the writes ([bb94cd3](https://github.com/RealPage/agentic-workflows/commit/bb94cd3fe98e6614547ec507aaceb6c472d381b4))
* **workflows:** inline WIF engine auth in tfs-review-pr-mirrored ([#123](https://github.com/RealPage/agentic-workflows/issues/123)) ([d2f69f5](https://github.com/RealPage/agentic-workflows/commit/d2f69f58bb8a493d5f38077720c1598e1bf63566))
* **workflows:** restore shared/wif-engine.md import on gh-aw v0.83.4 ([#128](https://github.com/RealPage/agentic-workflows/issues/128)) ([2685bb1](https://github.com/RealPage/agentic-workflows/commit/2685bb19eface2b77f0d1147616be77d9027f43b))
* **workflows:** un-scope tfs-review-pr-mirrored's concurrency group by pr_id ([45f3231](https://github.com/RealPage/agentic-workflows/commit/45f323108c1c436ab541dca73c757c6ef85e8ffe))


### Reverts

* **workflows:** revert tfs-review-pr-mirrored to 15-min cadence ([6fd3b90](https://github.com/RealPage/agentic-workflows/commit/6fd3b90e034fa405af4e7bdb3f4d2541906ea3e6))


### Documentation

* **tfs:** add consumer migration notes for the v1.0.0 renames ([#139](https://github.com/RealPage/agentic-workflows/issues/139)) ([bd41559](https://github.com/RealPage/agentic-workflows/commit/bd415595f0bb935208ef801e294e0c506cfcdea6))


### Code Refactoring

* **tfs:** shared import modules, collapse the mirrored variants, add tfs-review-pr ([#138](https://github.com/RealPage/agentic-workflows/issues/138)) ([9f26296](https://github.com/RealPage/agentic-workflows/commit/9f26296e60b4270721600fa806d86abf795f9de4))

## [0.7.0](https://github.com/RealPage/agentic-workflows/compare/v0.6.0...v0.7.0) (2026-07-22)


### Features

* **tfs-mirror:** make chunked bootstrap truly resumable + robust to transient errors ([4239f31](https://github.com/RealPage/agentic-workflows/commit/4239f316abb5777b657a3eeacc86f4e41bfdb3a2))
* **tfs-mirror:** support chunked bootstrap for large branches ([34c0caf](https://github.com/RealPage/agentic-workflows/commit/34c0caf12cdc96e5387657454046cb49a1021cb4))
* **tfs-mirror:** support chunked bootstrap for large branches ([535ccb5](https://github.com/RealPage/agentic-workflows/commit/535ccb54372f5bb53357d100f2f0c4d330a8c3a3))


### Bug Fixes

* **workflows:** inline WIF engine auth — gh-aw v0.82.10 breaks shared import ([#120](https://github.com/RealPage/agentic-workflows/issues/120)) ([f41758f](https://github.com/RealPage/agentic-workflows/commit/f41758f735bd3d4a411e129da817488c4fbb38c6))

## [0.6.0](https://github.com/RealPage/agentic-workflows/compare/v0.5.0...v0.6.0) (2026-07-06)


### Features

* **tfs-implement:** add mirrored variant for large repos ([1340040](https://github.com/RealPage/agentic-workflows/commit/13400407330523b87667d374fa636085947800b7))
* **tfs-implement:** add mirrored variant for large repos ([e6b2421](https://github.com/RealPage/agentic-workflows/commit/e6b2421134f85cb114eda95b602a45c27d380d69))


### Bug Fixes

* **tfs-implement-mirrored:** apply review findings from loft-core validation ([c83f276](https://github.com/RealPage/agentic-workflows/commit/c83f276ee8d207e0ab94fa2fbc8e092e26195a8b))

## [0.5.0](https://github.com/RealPage/agentic-workflows/compare/v0.4.0...v0.5.0) (2026-06-22)


### Features

* **tfs-implement:** add reusable TFS work item implementer ([#73](https://github.com/RealPage/agentic-workflows/issues/73)) ([9c1f21f](https://github.com/RealPage/agentic-workflows/commit/9c1f21f56075b651a69bfbcd9c338f6525c02659))
* **tfs-implement:** add tfs-mirror companion and optimize the clone path ([252ffa7](https://github.com/RealPage/agentic-workflows/commit/252ffa71740d2b1e105c734275e9d546762f2698))
* **tfs-implement:** clone target branch directly from TFS ([401f95d](https://github.com/RealPage/agentic-workflows/commit/401f95da8e5e0e26b12e9e6070b492270aa81d38))
* **wif:** extract shared engine config + untrack workflows/*.lock.yml ([#89](https://github.com/RealPage/agentic-workflows/issues/89)) ([684054f](https://github.com/RealPage/agentic-workflows/commit/684054f3dec89e22eb63f2d2083e8b272fdfcd75))
* **wif:** migrate all 5 golden workflows to WIF auth ([#93](https://github.com/RealPage/agentic-workflows/issues/93)) ([16d267c](https://github.com/RealPage/agentic-workflows/commit/16d267c6031b96b342e1efd75d08a3275ec4d633))


### Bug Fixes

* **auto-remediation:** rename safe-inputs → mcp-scripts ([#106](https://github.com/RealPage/agentic-workflows/issues/106)) ([5713947](https://github.com/RealPage/agentic-workflows/commit/5713947fbbab7943a69ca4456dfbbcf706e99859)), closes [#104](https://github.com/RealPage/agentic-workflows/issues/104)
* remove stray wif-poc test artifact from .github/workflows ([#96](https://github.com/RealPage/agentic-workflows/issues/96)) ([8e059f9](https://github.com/RealPage/agentic-workflows/commit/8e059f9dae3d0141430e431d0961c96e04a6a0d5)), closes [#95](https://github.com/RealPage/agentic-workflows/issues/95)
* **tfs-implement:** git am --keep-cr so CRLF files apply cleanly ([#87](https://github.com/RealPage/agentic-workflows/issues/87)) ([30ea76f](https://github.com/RealPage/agentic-workflows/commit/30ea76f7b94915f3b18ce60dcb682a5e9ca56a8c))
* **wif:** add workspace-id, remove placeholder ANTHROPIC_API_KEY ([#98](https://github.com/RealPage/agentic-workflows/issues/98)) ([d9ad7ca](https://github.com/RealPage/agentic-workflows/commit/d9ad7ca1f387ed75e2595145cf80c3bee0ff7d00)), closes [#95](https://github.com/RealPage/agentic-workflows/issues/95)
* **wif:** restore placeholder ANTHROPIC_API_KEY in shared engine ([#94](https://github.com/RealPage/agentic-workflows/issues/94)) ([9cbcdcf](https://github.com/RealPage/agentic-workflows/commit/9cbcdcf425e1117314c873f8e99965f03984ee6b))

## [0.4.0](https://github.com/RealPage/agentic-workflows/compare/v0.3.1...v0.4.0) (2026-04-29)


### Features

* **pme-triage:** expand SF context with Chatter, comment fields, and fix issue quality ([#55](https://github.com/RealPage/agentic-workflows/issues/55)) ([fe58de4](https://github.com/RealPage/agentic-workflows/commit/fe58de45b510a61e7bb0141665b7c2840f04e038)), closes [#53](https://github.com/RealPage/agentic-workflows/issues/53)


### Bug Fixes

* **pme-triage:** handle SF error array in Chatter response validation ([#57](https://github.com/RealPage/agentic-workflows/issues/57)) ([9f1c3cd](https://github.com/RealPage/agentic-workflows/commit/9f1c3cd4f1820e5e05103ccefe3e455fed270326))
* **pme-triage:** include nested comment replies in Chatter extraction ([#59](https://github.com/RealPage/agentic-workflows/issues/59)) ([ab061a3](https://github.com/RealPage/agentic-workflows/commit/ab061a317b2e1b9aeda0d382629a65b0f8a409b5))
* **pme-triage:** inline Chatter via Feeds subquery, eliminate N+1 API calls ([#61](https://github.com/RealPage/agentic-workflows/issues/61)) ([fa12868](https://github.com/RealPage/agentic-workflows/commit/fa1286872cbad13dd06107df2e9376949d0ad154))
* **pme-triage:** use Composite + Chatter REST API instead of SOQL on FeedItem ([#58](https://github.com/RealPage/agentic-workflows/issues/58)) ([10f39a5](https://github.com/RealPage/agentic-workflows/commit/10f39a5369c32d916cbb0d1b96a8bc9883e9368f))
* **pme-triage:** use per-PME Chatter Connect REST API for feed fetch ([#60](https://github.com/RealPage/agentic-workflows/issues/60)) ([ceef119](https://github.com/RealPage/agentic-workflows/commit/ceef1190204161b22297986b5328f04f5127c276))

## [0.3.1](https://github.com/RealPage/agentic-workflows/compare/v0.3.0...v0.3.1) (2026-04-14)


### Bug Fixes

* drop Claude API mention from README intro ([#49](https://github.com/RealPage/agentic-workflows/issues/49)) ([3cc979a](https://github.com/RealPage/agentic-workflows/commit/3cc979a454cf329ffd1b9d76f5963b53d852f874))
* safer defaults for fix-failing-tests trigger ([#50](https://github.com/RealPage/agentic-workflows/issues/50)) ([7e18444](https://github.com/RealPage/agentic-workflows/commit/7e184447682fc323010680367f61d4f124a0e5e2))
* soften add-wizard safety note to reflect observed behavior ([#48](https://github.com/RealPage/agentic-workflows/issues/48)) ([2ac47e0](https://github.com/RealPage/agentic-workflows/commit/2ac47e01ac399123f17011d6f3e73f67b8460687))

## [0.3.0](https://github.com/RealPage/agentic-workflows/compare/v0.2.0...v0.3.0) (2026-04-13)


### Features

* add agent-generate-tests workflow ([4ca7ac4](https://github.com/RealPage/agentic-workflows/commit/4ca7ac45ed0127ab8ba1feb37a02adde072a491b))
* add agent-refactor workflow ([229d92e](https://github.com/RealPage/agentic-workflows/commit/229d92e7cda24d481a09657c377435c533ec1a96))
* add agent-review-pr workflow ([e2dc2f8](https://github.com/RealPage/agentic-workflows/commit/e2dc2f86f1c07b2e9bbe06f29aeeed2b98ce09aa))
* add fix-failing-tests workflow ([0be6e80](https://github.com/RealPage/agentic-workflows/commit/0be6e802cde176e7215ce1eda8e850bef98ac291))
* add Fortify SAST triage and remediation workflows ([62c8cce](https://github.com/RealPage/agentic-workflows/commit/62c8ccee2bb7ba21a12cb50b14eed011bf46c0d2))
* Add Fortify SAST triage and remediation workflows ([37ff928](https://github.com/RealPage/agentic-workflows/commit/37ff928696658f6f2ebcea796a8454cae2f77148))
* add implement-issue workflow ([aa689c2](https://github.com/RealPage/agentic-workflows/commit/aa689c2c772802da453af24a9e27e2c8f7fff80e))
* add implement-issue workflow ([671d4f4](https://github.com/RealPage/agentic-workflows/commit/671d4f41ccb1ccfd771592fd654f200410aa5b67))
* add PME triage workflow ([16ce312](https://github.com/RealPage/agentic-workflows/commit/16ce312e951b62d5567058e9dba60758b532fd31))
* add PME triage workflow ([dad065d](https://github.com/RealPage/agentic-workflows/commit/dad065de42ca6d9fbfeeb52df7b23860b04649fa)), closes [#36](https://github.com/RealPage/agentic-workflows/issues/36)
* add priority_filter dispatch input to pme-triage ([dac83e4](https://github.com/RealPage/agentic-workflows/commit/dac83e4b7971e73e3c8859a7b8b92040c239a872))
* add release-please and conventional commits workflows ([920549e](https://github.com/RealPage/agentic-workflows/commit/920549e6978aa3a06c924874bc7ebd3039d701a7))
* add repo memory for PME cross-reference state caching ([e7d4f1c](https://github.com/RealPage/agentic-workflows/commit/e7d4f1c209570dfbbc4946c0442cfd68329a2256))
* group related PMEs into single issues and add SF write-back TODO ([05b0b5c](https://github.com/RealPage/agentic-workflows/commit/05b0b5c0075258237c260e95c7733dff17b0edb8))
* **implement-issue:** address PR [#28](https://github.com/RealPage/agentic-workflows/issues/28) review feedback ([bd108ca](https://github.com/RealPage/agentic-workflows/commit/bd108ca95a2a199e5e5505e8e30b7a1794cb533b))
* pme-triage v2 — SF write-back, enhancement grouping, WAD detection ([e0fa9a5](https://github.com/RealPage/agentic-workflows/commit/e0fa9a51eb9d862acc9dafd648b8bcf685fc9202))
* pme-triage v2 — SF write-back, enhancement grouping, WAD detection ([e95a6ee](https://github.com/RealPage/agentic-workflows/commit/e95a6ee0d589ca23af896d60550a6af325530894))
* standardise releases with release-please and conventional commits enforcement ([ee83e4f](https://github.com/RealPage/agentic-workflows/commit/ee83e4fc8d591b2ba1ac07cb07e7c88f5f5e8efb))


### Bug Fixes

* add contents:read to pre-activation, correct push_repo_memory doc ([7c96ec2](https://github.com/RealPage/agentic-workflows/commit/7c96ec28277eb7cc6f0ed20b1f3ed7d3ba6f20c5))
* add label-missing fallbacks for enhancement-backlog and wad:customer-impact ([309a9c6](https://github.com/RealPage/agentic-workflows/commit/309a9c6fd07aa7ea7c7a4345f26f16e3873aadeb))
* add tfs.realpage.com to network allowlist to prevent URL redaction ([b80726e](https://github.com/RealPage/agentic-workflows/commit/b80726eb90ad21714ea2c981ba97adf3a0796bf7))
* batch sf-comment into single call (custom jobs are max 1) ([95f31bb](https://github.com/RealPage/agentic-workflows/commit/95f31bbe5395120e46ef14e1affbfcc64a4afcac))
* bump artifact actions to v7/v8 (Node.js 20 deprecation) ([2507281](https://github.com/RealPage/agentic-workflows/commit/25072816f9b8dec5a63100f8a5f5526fd07465a2))
* correct repo memory path and push instruction ([62ada36](https://github.com/RealPage/agentic-workflows/commit/62ada364d5049426e0276224af697997e12e4918))
* correct state file path on memory branch (root, not subdir) ([8298b82](https://github.com/RealPage/agentic-workflows/commit/8298b82de9d0275a5af6c3a405883fcbad95bb3d))
* eliminate post-creation issue search loop, lower create-issue max to 5 ([a8f64a8](https://github.com/RealPage/agentic-workflows/commit/a8f64a82b8a4aa6f333c4b385977362033e4f603))
* fix nested code fence rendering in pme-triage body template ([1ed5485](https://github.com/RealPage/agentic-workflows/commit/1ed548531860e707408918a6995ea649aa7b7bc9))
* **fortify-triage:** extract username and release ID from secrets ([d6465d9](https://github.com/RealPage/agentic-workflows/commit/d6465d9d7f717a72860a680932b036a5300d66b3))
* hybrid pre-step — agent-level steps for GH, mcp-scripts for SF ([609eddb](https://github.com/RealPage/agentic-workflows/commit/609eddb40b5ca044cdfbd6206aa2127e64fb2ba1))
* inline release-type simple and remove release-please-config.json ([f3b47d7](https://github.com/RealPage/agentic-workflows/commit/f3b47d71db802cb5f16a45cb61ea3a8348a56c5a))
* only apply labels if they exist, fall back to title suffix ([d35ee63](https://github.com/RealPage/agentic-workflows/commit/d35ee63c69aa3d3592476779703d67f6f9b1caa9))
* pass GITHUB_TOKEN env var to action-semantic-pull-request ([0eaadf1](https://github.com/RealPage/agentic-workflows/commit/0eaadf1220a2f1edd01fd819eeee8990f1db5340))
* pass pre-step context via artifact (on.steps → agent) ([4fa1631](https://github.com/RealPage/agentic-workflows/commit/4fa163181ba2a6501a22deda7e826f2fa43331d3))
* remove token from release-please, switch to action-semantic-pull-request pinned to SHA ([e15a505](https://github.com/RealPage/agentic-workflows/commit/e15a50523a8057f36129d38d77ec7ef6fcc5e36f))
* replace FeedItem SOQL dedup with GitHub issue body marker ([ce12b38](https://github.com/RealPage/agentic-workflows/commit/ce12b384160909912d8e65b16de65cac102f9216))
* replace workflow_dispatch inputs with env section for schedule compatibility ([f3fbb3e](https://github.com/RealPage/agentic-workflows/commit/f3fbb3e4ce72ffaae6650c34d3997ed2a193e165))
* replace workflow_dispatch inputs with env section for schedule compatibility ([98ab7d5](https://github.com/RealPage/agentic-workflows/commit/98ab7d5d8ee702e6f0ba901cb044ed9bfbe02322))
* restructure SOQL query construction to ensure filters are applied ([6c8d59b](https://github.com/RealPage/agentic-workflows/commit/6c8d59b9abf7fa510e8767d32a1b7e6ba68b7ab0))
* revert contents:write — repo memory handles its own permissions ([2baaf1e](https://github.com/RealPage/agentic-workflows/commit/2baaf1ef53ed588497d08d6c3aaca5b2d4d2d8c8))
* set max: 15 on sf-comment custom safe output job ([2e3936e](https://github.com/RealPage/agentic-workflows/commit/2e3936e9452521cbe90b3fdaefe7c4494524e85b))
* surface pre-step errors instead of silently falling back ([977acd0](https://github.com/RealPage/agentic-workflows/commit/977acd08dc36e07a6279f0d221065ac9a18ac6e6))
* update auto-remediation onboarding note to reflect env: pattern ([f446c7a](https://github.com/RealPage/agentic-workflows/commit/f446c7a5bb06899b3ae46cbf95ea9cd288313199))
* use GitHub API for state file in pre-step (no git checkout) ([29d2f87](https://github.com/RealPage/agentic-workflows/commit/29d2f8715b3aa03de15e7fa2af0db39d0dc73bbd))
* use on.steps for pre-step (runs in pre-activation job, not agent) ([0750ffd](https://github.com/RealPage/agentic-workflows/commit/0750ffd94c48b6219eca5aabb294d3002d86912a))
* use repository variable for SF_OAUTH_CLIENT_ID instead of secret ([2ae3957](https://github.com/RealPage/agentic-workflows/commit/2ae395713cd3857575ec88ef2ad38e4e97359f7c))


### Performance Improvements

* move data fetching to deterministic pre-step ([19dd825](https://github.com/RealPage/agentic-workflows/commit/19dd825439268ed01f51ce3820453ac8edf539ec))

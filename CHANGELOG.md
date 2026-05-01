# Changelog

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

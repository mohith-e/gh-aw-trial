---
permissions:
  contents: read
  id-token: write   # required for WIF keyless auth

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

safe-outputs:
  create-pull-request:
  add-comment:
    max: 3

---

# MCP Server Selection

When a PRD is merged to main, analyze its technical requirements and configure MCP servers for the implementation workflow so agents have access to the right data sources and tools during development.

## Context

gh-aw workflows support MCP servers declared in the YAML frontmatter under `mcp-servers:`. When implementation agents run, they can use these MCP servers to access external systems — databases, APIs, documentation — which helps them write better, more informed code.

The implementation workflow is at `.github/workflows/implementation.md`. An `mcp-servers:` block can be added to its YAML frontmatter to give agents access to external tools.

## Available MCP Servers

The following MCP servers are available. For each, the key is the server name and the value contains its transport config. Environment variables referencing secrets use the format `secrets.SECRET_NAME` wrapped in GitHub Actions expression syntax.

### Data & Analytics

**BigQuery** — Query BigQuery tables for schema exploration, sample data, and validation.
- command: `npx`
- args: `["-y", "@anthropic/bigquery-mcp-server"]`
- env keys: GCP_PROJECT (from secrets), GCP_LOCATION (from secrets), GOOGLE_APPLICATION_CREDENTIALS (from secrets)
- allowed: all tools
- Required secrets: GCP_PROJECT, GCP_LOCATION, GCP_SA_KEY_PATH

### Documentation & Search

**Brave Search** — Web search for documentation, API references, and examples.
- command: `npx`
- args: `["-y", "@anthropic/brave-search-mcp-server"]`
- env keys: BRAVE_API_KEY (from secrets)
- allowed: all tools
- Required secrets: BRAVE_API_KEY

**Markitdown** — Convert documents (PDF, DOCX, XLSX) to markdown for analysis.
- registry: `https://api.mcp.github.com/v0/servers/microsoft/markitdown`
- container: `ghcr.io/microsoft/markitdown`
- allowed: all tools
- Required secrets: none

### Development Tools

**Sequential Thinking** — Multi-step reasoning for complex implementation decisions.
- command: `npx`
- args: `["-y", "@modelcontextprotocol/server-sequential-thinking"]`
- allowed: all tools
- Required secrets: none

**Jupyter** — Execute Python code, run tests, and validate implementations.
- import: `workflows/mcp/jupyter.md`
- Required secrets: none

### Infrastructure & Observability

**DataDog** — Query monitoring data for observability implementations.
- command: `npx`
- args: `["-y", "@anthropic/datadog-mcp-server"]`
- env keys: DD_API_KEY (from secrets), DD_APP_KEY (from secrets)
- allowed: all tools
- Required secrets: DD_API_KEY, DD_APP_KEY

### Collaboration

**Notion** — Access project documentation and design specs.
- container: `mcp/notion`
- env keys: NOTION_TOKEN (from secrets)
- allowed: search_pages, get_page
- Required secrets: NOTION_TOKEN

**Slack** — Post implementation updates or read channel context.
- container: `mcp/slack`
- env keys: SLACK_TOKEN (from secrets)
- allowed: search_messages, read_channel
- Required secrets: SLACK_TOKEN

## Instructions

1. Identify the merged PRD file from the pull request changes
2. Read the full PRD, focusing on:
   - Section 5 (Technical Considerations) — APIs, databases, external services
   - Section 4 (Functional Requirements) — what the implementation needs access to
   - Section 6 (Acceptance Criteria) — what the agent needs to validate
   - The project's `CLAUDE.md` for architectural context
3. Read the current `.github/workflows/implementation.md` to see if `mcp-servers:` is already configured
4. Determine which MCP servers would help implementation agents:
   - **BigQuery** — if the PRD involves querying, schema exploration, or data validation against BigQuery
   - **Brave Search** — if the PRD references external APIs or libraries the agent may need docs for
   - **Sequential Thinking** — if the PRD involves complex multi-step logic or architectural decisions
   - **Jupyter** — if the PRD requires running Python code to validate implementations
   - **DataDog** — if the PRD involves observability, metrics, or monitoring
   - **Notion** — if the PRD references design specs or documentation in Notion
   - **Do NOT add** servers that require secrets the repo doesn't have configured
   - **Do NOT add** servers irrelevant to the PRD's technical scope
5. Update `.github/workflows/implementation.md` by adding the `mcp-servers:` block to the YAML frontmatter, right before the closing `---`. Use the standard gh-aw frontmatter syntax for MCP servers with secrets referenced as GitHub Actions expressions
6. IMPORTANT: Also check if the required secrets exist. If an MCP server needs a secret, note in the PR which secrets need to be configured before the implementation workflow can use that server
7. Open a pull request with:
   - Title: "Configure MCP servers for implementation agents (PRD #N)"
   - Body explaining which MCP servers were added, why each was selected based on the PRD, and any secrets that need to be configured
   - Include a reminder that `gh aw compile` must be run locally after merge to regenerate the lock file
8. Comment on the original PRD PR explaining what MCP servers were configured for implementation

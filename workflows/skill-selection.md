---
permissions:
  contents: read
  id-token: write   # required for WIF keyless auth

imports:
  - shared/wif-engine.md

safe-outputs:
  create-pull-request:
  add-comment:
    max: 3

---

# Skill Selection

When a PRD is merged to main, analyze its technical requirements and pull relevant coding skills from the RealPage ai-coding-toolkit into this repo.

## Context

The RealPage/ai-coding-toolkit repo contains reusable coding skills at `skills/<skill-name>/SKILL.md`. Each skill has YAML frontmatter with `name`, `description`, and optional `stack` fields, followed by markdown instructions covering patterns, templates, and best practices.

Skills are installed to `.claude/skills/<skill-name>/SKILL.md` where Claude Code agents automatically discover and use them during implementation.

## Available Skills

The following skills exist in `RealPage/ai-coding-toolkit/skills/`:

| Skill | Stack | Description |
|-------|-------|-------------|
| api-design | - | REST API design standards, pagination, error handling, versioning |
| auto-remediator | - | Auto-remediation patterns |
| avro-schemas | - | Avro schema design and evolution |
| confluent-kafka | - | Confluent Kafka producer/consumer patterns |
| dotnet-project | dotnet | .NET project standards and templates |
| elk-logging | - | ELK stack logging patterns |
| git-conventions | - | Git commit, branching, and PR conventions |
| java-project | java | Java project standards and templates |
| kong-gateway | - | Kong API gateway configuration |
| langsmith-evals | - | LangSmith evaluation patterns |
| launchdarkly | - | LaunchDarkly feature flag patterns |
| openai-agents | - | OpenAI agents SDK patterns |
| python-project | python | Python project standards (pyproject.toml, testing, linting, CI/CD) |
| spring-boot | java | Spring Boot application patterns |
| spring-cache | java | Spring caching patterns |
| spring-data | java | Spring Data JPA/repository patterns |
| spring-framework | java | Spring Framework core patterns |
| spring-observability | java | Spring observability and metrics |
| spring-resilience | java | Spring resilience (retry, circuit breaker) |
| spring-security | java | Spring Security configuration |
| temporal-onboarding | - | Temporal workflow onboarding |
| temporal-workflows | - | Temporal workflow and activity patterns |
| unified-login | - | Unified login integration |

## Instructions

1. Identify the merged PRD file from the pull request changes
2. Read the PRD document, focusing on:
   - Section 5 (Technical Considerations) — technologies, frameworks, dependencies
   - Section 4 (Functional Requirements) — what needs to be built
   - The project's existing `CLAUDE.md` and `pyproject.toml` (or `pom.xml`, `build.gradle`, `package.json`) for current stack context
3. Check which skills already exist in `.claude/skills/` — do not re-add skills that are already installed
4. Match PRD requirements to available skills. Selection criteria:
   - **Always include** `git-conventions` if not already present (applies to all repos)
   - **Include stack skills** matching the project's language (e.g., `python-project` for Python repos, `java-project` for Java)
   - **Include domain skills** that match PRD technical requirements (e.g., `api-design` for API work, `elk-logging` for observability, `confluent-kafka` for event streaming)
   - **Exclude** skills for stacks not used in this project (e.g., skip all Spring/Java/.NET skills for a Python project)
   - **Exclude** skills for technologies not mentioned in the PRD or existing codebase
5. For each selected skill, fetch its content from `RealPage/ai-coding-toolkit` using the GitHub API:
   - Read `https://api.github.com/repos/RealPage/ai-coding-toolkit/contents/skills/{skill-name}/SKILL.md`
   - The content is base64-encoded in the response — decode it
6. Write each selected skill to `.claude/skills/{skill-name}/SKILL.md` in this repo
7. Open a pull request with:
   - Title: "Add coding skills from ai-coding-toolkit for PRD #{prd-number}"
   - Body listing which skills were added and why each was selected based on the PRD
8. Comment on the original PRD PR explaining which skills were added and how they'll help the implementation agents

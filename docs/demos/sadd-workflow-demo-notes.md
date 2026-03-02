# STRATIS BORG - AI SDLC Pipeline Demo Notes

## Application Overview

**STRATIS BORG** is an AI-powered Software Development Lifecycle (SDLC) automation platform at `ai-sdlc.dev.stratisiot.net`. It orchestrates automated bug-fix workflows by connecting Azure DevOps work items to AI coding agents that generate pull requests.

---

## Demo Walkthrough

### 1. Dashboard (0:00)

- Shows the main monitoring dashboard with key metrics: 23 active runs, 5 completed today, 7 failed today, 33 Sentry issues queued, 1 resolved by AI
- MCP Servers section: 1 healthy, 1 unhealthy, 2 servers configured with 6 tools
- "Top Error Patterns" panel on the right (resource/workspace, git/checkout, validation errors)
- Recent Runs list showing repeated "Matter Gateway Timeout" runs with "Success" status

### 2. Team Configuration (~0:06-0:08)

- Navigates to the **stratis-iot-codex** team page (tagged "Active")
- Team starts with 1/1 Agents, 0 Repositories, 0 Recent Runs
- After some setup: 2 Repositories, 3 Recent Runs, 100% Success Rate
- Tabs available: Overview, AI Config, Infrastructure, Repositories, Tools, Triggers, Workflows

### 3. Workflow Creation Wizard (~0:18-0:50)

The demo walks through a 3-step workflow creation wizard:

#### Step 1 - Choose a Trigger

- Options: Azure DevOps, GitHub, Sentry, Manual, Schedule
- **Azure DevOps** is selected
- Configures connection to "IoT Test", work item type filter = "Bug", tag filter = "iot-bug"
- Three Azure DevOps connections are shown (IoT Test, test-ado, architecture-board) — all healthy

#### Step 2 - Configure Actions

- **Create Pull Request** — enabled, branch naming pattern: `aisdlc-{{run_id}}`, reviewers: `@username, @team`
- **Auto-resolve Source** — enabled, resolve state on success = "Resolved", fail state on failure = "Active"
- **Notifications** — enabled, channel = "Stratis-Borg", notify on success + failure
- **Failure Handling** — toggle available for auto-retry of failed runs

#### Step 3 - Review & Activate

- Workflow named **"IoT Bug Fix Pipeline"**
- Pipeline summary visualization: TRIGGER (Azure DevOps) → TEAM (stratis-iot-codex) → ACTIONS (3 actions)
- Shows trigger details, team details, and actions summary
- Option to "Activate immediately" or "Start paused"
- Clicks **Activate Workflow**

### 4. Workflow Deployed (~0:56-1:06)

- Back on team page showing the new **"IoT Bug Fix Workflow"** listed under Workflows (1)
- Visual pipeline: Azure DevOps ADO work items → 1 Agent & 2 repos → Create PR pipeline actions
- Navigates into the workflow detail page showing the full pipeline diagram and action configuration

### 5. Creating a Bug in Azure DevOps (~1:16-1:22)

- Switches to Azure DevOps (dev.azure.com) in the STRATIS-Chirp project
- Creates a new Bug work item: **"Matter Gateway Timeout sometimes when retiring device"**
- Tags it with `iot-bug` (the trigger tag)
- Includes repro steps, a Sentry link, and "504 Error returned"
- Saves the bug

### 6. Automated Run Triggered (~1:30-2:10)

- Returns to STRATIS BORG → Runs page (1,186 total runs)
- A new run appears immediately with status **"Running"** — triggered by Azure DevOps Work Item #65486
- Run details show:
  - Run ID: `bb7290fc-8e38-43d7-8538-f548299561ad`
  - Team: stratis-iot-codex
  - Duration progresses from 4s → 14s → 19s → 29s (running)
  - Instructions are parsed from the bug: repro steps, Sentry link, 504 error
  - Work item metadata: Bug, Priority 0, Project stratis-Chirp
- **CLI Output tab** shows the AI agent (codex) actively working — importing modules, analyzing gateway/metrics selectors and components in `NetworkDeviceExclusionResult.tsx`
- Pull Request instruction visible: "Make sure the PR description clearly explains what changed and why"

### 7. Run Completes Successfully (~2:12-2:24)

- Run status changes to **"Success"** after ~4m 28s
- Work item #65486 is now linked
- **Primary Output** shows the AI's solution:
  - Handles gateway timeout responses during retire by continuing to poll for `promise_id`
  - Shows a "timeout but still running" message instead of leaving UI in a failure-only state
  - Changes to `NetworkDeviceExclusionResult.tsx` across success and error payload shapes
  - Polls promise status using the resolved `promise_id`
- "View PR" link is available

### 8. Slack Notification (~2:28)

- Switches to Slack, **#iot-dev-alerts** channel in STRATIS workspace
- **IoT-maton** bot posts: "AI-SDLC Run bb7290fc completed"
  - Repo: realpage-smartbuilding/stratis-cs-portal
  - Team: stratis-iot-codex
  - "codex cli changes applied"
  - PR: **View PR** link

### 9. GitHub Pull Request (~2:30-2:40)

- Opens GitHub PR **#855** on `stratis-cs-portal`: "Matter Gateway Timeout sometimes when retiring device - AISDLC run bb7290fc..."
- PR is in **Draft** status, from branch `aisdlc/run-bb7290fc8e38` into `main`
- PR body includes:
  - AISDLC automated change metadata (RunId, Team, Trigger, Branch, Tests: SKIPPED)
  - Full bug instructions and repro steps
  - AI SDLC Run Notes with detailed metadata
- **Files changed (1):** `NetworkDeviceExclusionResult.tsx` — +27 insertions, -11 deletions
- The diff shows the AI added:
  - Logic to extract `promise_id` from multiple response paths
  - A timeout message: "We received a timeout from the gateway, but the operation may still be running. We'll keep checking the promise status."
  - Error handling with `<ObjectDisplay>` for failure cases
  - Promise status polling via `responsePromiseId`

### 10. Final State (~2:46)

- Returns to STRATIS BORG showing the run as successful
- Workflows page shows all workflows including the new **"IoT Bug Fix Workflow"** with status Healthy, 1 run, 100% success rate

---

## Key Takeaways

1. **End-to-end automation**: Bug filed in Azure DevOps → AI agent analyzes the bug + Sentry error → generates a code fix → creates a GitHub PR → notifies via Slack — all automated
2. **~4.5 minutes** from bug creation to a working PR with code changes
3. The AI agent understood the gateway timeout issue and implemented a real fix (promise polling + timeout UX message)
4. The workflow wizard is straightforward: pick trigger → configure actions → review → activate
5. Full observability: run logs, CLI output, cost tracking, and audit trail

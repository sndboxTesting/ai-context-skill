# START HERE - Suneel Local AI Current Setup

This is the authoritative current setup profile for Suneel's local AI system.

## Current Installed Setup

Suneel's local AI system is already installed and running under:

`/Users/MAC/SuneelWorkSpace`

The current installed services are:

1. Ollama
   - Purpose: local AI model runner
   - Main model: `adwi:latest` (Qwen3 MoE 30.5B, 131K context, Q4_K_M quantization)
   - Also installed: `llama3.1:8b` (fast 4.9GB fallback), `nomic-embed-text` (embeddings)
   - Optimizations: Flash Attention ON, KV cache q8_0, num_parallel=1 (all 64GB dedicated)
   - API: `http://127.0.0.1:11434`

2. Open WebUI
   - Purpose: local ChatGPT-style browser interface
   - URL: `http://localhost:3000`
   - Docker container: `suneel-open-webui`

3. n8n
   - Purpose: local workflow automation engine
   - URL: `http://localhost:5678`
   - Docker container: `suneel-n8n`
   - Community license has been activated

4. SearXNG
   - Purpose: local web search provider for Open WebUI
   - URL: `http://localhost:8888`
   - Docker container: `suneel-searxng`

5. VS Code Terminal
   - Purpose: main place where Suneel runs commands
   - User prefers one command at a time

## Current Working Local Commands

These commands already exist in:

`/Users/MAC/SuneelWorkSpace/bin`

Commands:

- `status-ai`
- `start-ai`
- `stop-ai`
- `logs-ai`
- `check-github-latest-release`
- `summarize-url`
- `summarize-youtube`
- `save-youtube-summary`
- `daily-ai-status-report`
- `index-ai-notes`


## Profile and Command API Helper Commands

Suneel also has these helper commands:

- `ask-ai-profile`
  - Asks questions using the full authoritative START HERE profile file
  - More reliable than RAG for setup/status questions

- `start-command-api`
  - Starts the Safe Local Command API

- `stop-command-api`
  - Stops the Safe Local Command API

- `status-command-api`
  - Checks whether the Safe Local Command API is running and responding


## All Current Commands

This is the authoritative complete list of Suneel's current commands in `/Users/MAC/SuneelWorkSpace/bin`.

Core stack commands:
- `status-ai`
- `start-ai`
- `stop-ai`
- `logs-ai`
- `show-ai-tree`

Research and summarization commands:
- `check-github-latest-release`
- `summarize-url`
- `summarize-youtube`
- `save-youtube-summary`

Memory, profile, and planning commands:
- `daily-ai-status-report`
- `index-ai-notes`
- `ask-ai-profile`
- `plan-local-task`

Safe Command API commands:
- `start-command-api`
- `stop-command-api`
- `status-command-api`
- `suneel-command-api`

Maintenance automation commands:
- `auto-ai-maintenance`

Important:
- `plan-local-task` creates task plans only. It does not execute commands automatically.
- `show-ai-tree` is read-only. It shows the local AI workspace folder structure without modifying files.
- `auto-ai-maintenance` performs safe upkeep through approved commands and logs the result.


## Current Knowledge and Memory

Suneel's local notes are stored in:

`/Users/MAC/SuneelWorkSpace/notes`

Important note files include:

- `local-ai-learning-journal.md`
- `reliable-web-research-prompt.md`
- `suneel-local-ai-profile.md`
- YouTube summaries under `youtube-summaries`


## Daily Learning and Operations Commands

Suneel also has these commands:

- `daily-ai-status-report`
  - Creates a Markdown status report under `/Users/MAC/SuneelWorkSpace/notes/daily-status`
  - Captures the output of `status-ai`
  - Helps build an operations history for the local AI system

- `index-ai-notes`
  - Creates or refreshes `/Users/MAC/SuneelWorkSpace/notes/AI-NOTES-INDEX.md`
  - Lists Markdown and text notes in the local AI notes folder
  - Helps Suneel and the local AI understand what memory files exist


## Completed Milestones

- Ollama installed and running with `adwi:latest` (Qwen3 MoE 30.5B, 131K context, Q4_K_M).
- `llama3.1:8b` available as fast fallback. `nomic-embed-text` for embeddings.
- Ollama optimized: Flash Attention, q8_0 KV cache, num_parallel=1.
- Open WebUI running at `http://localhost:3000`.
- n8n running at `http://localhost:5678`.
- SearXNG running at `http://localhost:8888`.
- Webpage summarization: `summarize-url` (now uses adwi:latest).
- YouTube summarization: `summarize-youtube` and `save-youtube-summary` (now uses adwi:latest).
- Notes indexed with `index-ai-notes`.
- Daily AI status reports: `daily-ai-status-report`.
- Safe Local Command API working at `http://127.0.0.1:5055`.
- n8n Daily Heartbeat and Auto Maintenance workflows tested.
- Adwi Phase 1 complete: multiline input, streaming, image analysis, YouTube auto-detect,
  capability registry, learning journal, daily-improve, reasoning commands, natural routing.

## What to Build Next (Phase 2)

See `/Users/MAC/SuneelWorkSpace/notes/adwi-capability-roadmap.md` for the full roadmap.
Run `/what-next` inside adwi for an AI-driven recommendation.

Top Phase 2 priorities:
1. Conversation memory — persist multi-turn chat history between adwi sessions
2. RAG over notes — inject relevant local notes into every prompt automatically
3. Implement-from-video flow — paste video → extract ideas → build plan → apply safely
4. Gmail read-only integration with approved scope
5. n8n trigger from adwi — kick off n8n workflows from adwi commands



## Workspace Inspection Command

Suneel has a read-only workspace inspection command:

- `show-ai-tree`
  - Shows the local AI workspace folder structure
  - Uses `/Users/MAC/SuneelWorkSpace` as the root
  - Skips noisy internal data folders where practical
  - Does not modify files

## Safe Local Task Planning

Suneel has a safe task planning command:

- `plan-local-task`
  - Takes a task description from Suneel
  - Uses the authoritative START HERE profile and notes index
  - Creates a Markdown task plan under `/Users/MAC/SuneelWorkSpace/notes/task-plans`
  - Does not execute commands automatically
  - Helps Suneel review risk, commands, verification, rollback, and logging before approving anything

Preferred safe automation pattern:

1. AI plans.
2. Suneel reviews.
3. Suneel approves.
4. A safe command is created or allowlisted.
5. n8n or the Safe Command API runs only approved actions.
6. Results are logged.


## Adwi Safe Self-Healing

Suneel has a safe self-healing command:

- `adwi-self-heal`
  - Starts/checks Ollama
  - Starts/checks Docker AI stack
  - Starts/checks Safe Command API
  - Refreshes the notes index
  - Creates a daily status report
  - Saves a self-heal log under `/Users/MAC/SuneelWorkSpace/notes/self-heal-logs`

Safety boundary:

`adwi-self-heal` does not give Adwi unrestricted Mac access. It does not delete files, install unknown packages, access secrets, send email, change passwords, modify money-related accounts, or run arbitrary AI-generated commands.

This is the approved pattern for auto-fixing the local AI setup.


## Adwi Local Secrets Vault

Suneel has a local secrets vault folder:

`/Users/MAC/SuneelWorkSpace/secrets`

Purpose:

- Store API keys, tokens, and secret configuration for approved local AI tools.
- Keep secrets separate from notes, Knowledge/RAG, and chat history.
- Allow future approved tools to load secrets safely without printing them.

Important files:

- `secrets.local.env`
  - Real local secret values
  - Private file
  - Permission should be `600`

- `secrets.example.env`
  - Example placeholder file
  - Safe to inspect

- `secrets.manifest.json`
  - Lists allowed secret names only
  - Does not contain secret values

Commands:

- `adwi-secrets-status`
  - Shows which secret names are configured
  - Does not print secret values

- `adwi-secrets-edit`
  - Opens the local secrets file in VS Code

Safety boundary:

- Adwi should not print secret values.
- Adwi should not upload secrets to Open WebUI Knowledge.
- Adwi should not scan the whole Mac for secrets.
- Approved helper commands may load specific secrets for specific tasks.


## Secrets Vault Integration for Open WebUI Sync

Open WebUI sync commands now use the Adwi local secrets vault.

Secrets source:

`/Users/MAC/SuneelWorkSpace/secrets/secrets.local.env`

Commands that should use this secrets file:

- `sync-openwebui-knowledge`
- `watch-openwebui-knowledge`
- `start-openwebui-knowledge-watcher`

Required secret names:

- `OPENWEBUI_URL`
- `OPENWEBUI_API_KEY`
- `OPENWEBUI_KNOWLEDGE_ID`

Safety rule:

These commands should read secrets only from the local secrets vault and should not print secret values.


## Clipboard Command Runner

Suneel has a command-output clipboard helper:

- `cliprun`
- alias: `cr`

Usage:

`cr 'command here'`

What it does:

1. Runs the command.
2. Shows the output in the terminal.
3. Redacts obvious API keys, JWTs, and bearer tokens.
4. Saves a Markdown log under `/Users/MAC/SuneelWorkSpace/notes/clipboard-command-logs`.
5. Copies the command and output to the Mac clipboard with `pbcopy`.

Safety note:

This is safer than auto-copying every terminal command because it avoids accidentally copying secrets from unrelated commands.

## Safety Rules

The AI should not have unlimited access to:

- files
- email accounts
- credentials
- money
- system settings
- destructive commands

Safe workflow:

1. AI suggests.
2. Suneel reviews.
3. Suneel approves.
4. Tool runs.
5. Result is logged.

## Important Correction

Do not say Suneel only has a basic setup.

Suneel already has a working local AI foundation with Ollama, Open WebUI, n8n, SearXNG, webpage summarization, YouTube summarization, saved notes, and helper commands.

Do not recommend OpenClaw or Claude Co-work as if they are already installed.

They may be considered later, but they are not part of the current installed setup.

## Working n8n Heartbeat Automation

Suneel has created and tested a safe n8n heartbeat workflow.

Workflow name:

`Suneel Daily AI Status Heartbeat`

Workflow file:

`/Users/MAC/SuneelWorkSpace/n8n/workflows/daily-ai-status-heartbeat.json`

What it does:

1. n8n calls the Safe Local Command API.
2. The API route `/daily-ai-status-report` runs the allowlisted command `daily-ai-status-report`.
3. A Markdown status report is saved under `/Users/MAC/SuneelWorkSpace/notes/daily-status`.

Safe Command API details:

- Local Mac URL: `http://127.0.0.1:5055`
- n8n Docker URL: `http://host.docker.internal:5055`
- Allowed routes:
  - `/status-ai`
  - `/daily-ai-status-report`
  - `/index-ai-notes`

Command API helper commands:

- `start-command-api`
- `stop-command-api`
- `status-command-api`

Important safety design:

n8n does not have unrestricted shell access. It can only call allowlisted Safe Command API routes.

## Working n8n Auto AI Maintenance Automation

Suneel has created and tested a fuller n8n automation workflow.

Workflow name:

`Suneel Auto AI Maintenance`

Workflow file:

`/Users/MAC/SuneelWorkSpace/n8n/workflows/auto-ai-maintenance.json`

What it does:

1. n8n calls the Safe Local Command API.
2. The API route `/auto-ai-maintenance` runs the allowlisted command `auto-ai-maintenance`.
3. `auto-ai-maintenance` starts/checks the local AI stack.
4. It confirms the Safe Command API behavior.
5. It creates a daily AI status report.
6. It refreshes the notes index.
7. It asks the authoritative local profile what is completed and what should be built next.
8. It saves a Markdown maintenance log under `/Users/MAC/SuneelWorkSpace/notes/maintenance-logs`.

Latest confirmed maintenance log example:

`/Users/MAC/SuneelWorkSpace/notes/maintenance-logs/20260613-195944-auto-ai-maintenance.md`

Important safety design:

This automation still does not give unrestricted Mac access. It runs only through the Safe Local Command API allowlist.


## Safe Command API Self-Heal Route

The Safe Local Command API includes an approved route:

- `/adwi-self-heal`
  - Runs the allowlisted `adwi-self-heal` command
  - Performs safe repairs/checks only
  - Logs results under `/Users/MAC/SuneelWorkSpace/notes/self-heal-logs`

This route does not provide unrestricted Mac access.

## Working n8n Adwi Self-Heal Automation

Suneel has created and tested an n8n workflow named:

`Adwi Safe Self-Heal`

Workflow file:

`/Users/MAC/SuneelWorkSpace/n8n/workflows/adwi-self-heal.json`

What it does:

1. n8n calls the Safe Local Command API route `/adwi-self-heal`.
2. The API runs the allowlisted command `adwi-self-heal`.
3. `adwi-self-heal` performs safe setup repair/check actions only.
4. It refreshes the notes index.
5. It creates a daily AI status report.
6. It saves a self-heal log under `/Users/MAC/SuneelWorkSpace/notes/self-heal-logs`.

Latest confirmed self-heal log example:

`/Users/MAC/SuneelWorkSpace/notes/self-heal-logs/20260613-211501-adwi-self-heal.md`

Important safety design:

This workflow does not give unrestricted Mac access. It only runs through the Safe Command API allowlist.

## Working Automatic Open WebUI Knowledge Sync

Suneel has working automatic Open WebUI Knowledge sync.

Watched folder:

`/Users/MAC/SuneelWorkSpace/open-webui-knowledge-upload`

Knowledge collection:

`Suneel Local AI Knowledge`

Main commands:

- `sync-openwebui-knowledge`
  - Manually syncs new or changed `.md` and `.txt` files to Open WebUI Knowledge

- `watch-openwebui-knowledge`
  - Watches the upload folder and repeatedly runs sync

- `start-openwebui-knowledge-watcher`
  - Starts the watcher manually in the background

- `stop-openwebui-knowledge-watcher`
  - Stops the manual watcher

- `status-openwebui-knowledge-watcher`
  - Shows LaunchAgent/manual watcher status and upload state summary

Persistence:

A macOS LaunchAgent keeps the watcher running:

`com.suneel.openwebui-knowledge-watcher`

LaunchAgent file:

`/Users/MAC/Library/LaunchAgents/com.suneel.openwebui-knowledge-watcher.plist`

State file:

`/Users/MAC/SuneelWorkSpace/watchers/open-webui-knowledge/uploaded-state.json`

Logs:

`/Users/MAC/SuneelWorkSpace/notes/open-webui-sync-logs`

Safety boundary:

- Only watches `/Users/MAC/SuneelWorkSpace/open-webui-knowledge-upload`
- Only uploads `.md` and `.txt` files
- Uses secrets from `/Users/MAC/SuneelWorkSpace/secrets/secrets.local.env`
- Does not upload the secrets folder
- Does not scan the whole Mac

Confirmed working test files:

- `ADWI-AUTO-SYNC-TEST.md`
- `ADWI-WATCHER-AUTO-TEST.md`
- `ADWI-LAUNCHAGENT-AUTO-TEST.md`
- `ADWI-QUIET-WATCHER-TEST.md`


## Current Adwi Model and Integrated Action Confirmation

Current Adwi command:

`adwi`

Current Adwi Ollama model:

`adwi:latest`

Current Adwi base model:

`qwen3:30b`

Adwi is now an integrated local terminal assistant with both natural chat and built-in slash actions.

Important current facts:

- `adwi:latest` is based on `qwen3:30b`, not `llama3.1:8b`.
- `llama3.1:8b` remains installed as a smaller fallback model.
- Adwi suppresses visible thinking output for normal chat.
- Adwi supports `/status`, `/self-heal`, `/sync-knowledge`, `/watcher-status`, `/secrets-status`, `/search`, `/read`, `/url`, `/youtube`, and `/save-youtube`.
- Adwi excludes the secrets folder from read/search.
- Adwi blocks destructive and money/payment/banking/crypto actions.

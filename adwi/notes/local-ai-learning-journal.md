# Suneel Local AI Learning Journal

This journal tracks useful ideas learned from web pages, YouTube videos, experiments, and local setup work.

## Current Local AI Setup

- Workspace: `/Users/MAC/SuneelWorkSpace`
- Local model runner: Ollama
- Current model: `llama3.1:8b`
- Chat UI: Open WebUI at `http://localhost:3000`
- Automation engine: n8n at `http://localhost:5678`
- Web search: SearXNG at `http://localhost:8888`
- Notes folder: `/Users/MAC/SuneelWorkSpace/notes`
- Helper commands folder: `/Users/MAC/SuneelWorkSpace/bin`

## Working Commands

- `status-ai` — check the local AI stack
- `start-ai` — start Ollama and Docker services
- `stop-ai` — stop Docker services and Ollama
- `logs-ai` — view Docker logs
- `check-github-latest-release owner/repo` — check official GitHub latest release
- `summarize-url URL` — summarize a webpage with local AI
- `summarize-youtube URL` — summarize a YouTube video from captions
- `save-youtube-summary URL` — summarize and save a YouTube video note

## Lessons Learned

### Local AI Agents In 26 Minutes — Tina Huang

Saved summary:
`/Users/MAC/SuneelWorkSpace/notes/youtube-summaries/20260613-174715-local-ai-agents-in-26-minutes.md`

Useful idea:
- A local AI agent can be thought of as:
  - Brain = local model
  - Memory = local notes/files
  - Tools = controlled scripts/commands
  - Heartbeat = scheduled workflows
  - Interface = chat app or automation dashboard

How this applies locally:
- Brain: Ollama + local model
- Memory: notes under `SuneelWorkSpace/notes`
- Tools: helper commands under `SuneelWorkSpace/bin`
- Heartbeat: n8n workflows
- Interface: Open WebUI

Safety rule:
- Do not give any AI agent unlimited access to files, email, credentials, money, or system settings.
- Build small approved tools first.
- Review outputs before applying changes.

## Next Build Ideas

1. Create a local note index.
2. Connect saved notes to Open WebUI/RAG.
3. Create n8n workflow to run daily local AI status.
4. Add Gmail integration carefully with approval.
5. Add MCP servers after the core setup is stable.
6. Add a safe “apply locally” workflow that suggests changes before executing anything.


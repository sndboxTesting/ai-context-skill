# Suneel Local AI Profile

## Current Setup Summary

Suneel's local AI workspace is located at:

`/Users/MAC/SuneelWorkSpace`

The current local AI setup includes:

- Ollama as the local model runner
- Local model: `llama3.1:8b`
- Open WebUI as the browser chat interface at `http://localhost:3000`
- n8n as the local automation and workflow engine at `http://localhost:5678`
- SearXNG as the local web search service at `http://localhost:8888`
- VS Code terminal as the main place to run commands
- Notes and learning memory stored under `/Users/MAC/SuneelWorkSpace/notes`
- Helper commands stored under `/Users/MAC/SuneelWorkSpace/bin`

## Working Helper Commands

- `status-ai` checks the health of the local AI stack
- `start-ai` starts Ollama and Docker services
- `stop-ai` stops Docker services and Ollama
- `logs-ai` shows Docker logs
- `check-github-latest-release owner/repo` checks official GitHub release data
- `summarize-url URL` summarizes a webpage using local AI
- `summarize-youtube URL` summarizes a YouTube video using captions/transcripts
- `save-youtube-summary URL` summarizes and saves a YouTube video note

## Local AI Agent Architecture

Suneel's local AI agent architecture should be built safely using these parts:

- Brain: Ollama local models
- Memory: Markdown notes in `SuneelWorkSpace/notes`
- Tools: controlled scripts in `SuneelWorkSpace/bin`
- Heartbeat: n8n workflows and scheduled automations
- Interface: Open WebUI
- Search: SearXNG
- Learning library: saved webpage summaries and YouTube summaries

## Safety Rules

The local AI should not be given unlimited access to files, email, credentials, money, or system settings.

Safe approach:

1. Build small tools first.
2. Let AI suggest actions.
3. Review actions before execution.
4. Keep credentials private.
5. Avoid destructive file actions unless explicitly approved.
6. Log important summaries and changes into the notes folder.

## Recommended Next Build Steps

1. Improve Open WebUI Knowledge/RAG retrieval using focused profile notes.
2. Add more saved summaries to the notes folder.
3. Create a daily n8n workflow that runs `status-ai`.
4. Create a safe local task suggestion workflow.
5. Add Gmail/email integration carefully, only after defining permissions.
6. Add MCP servers after the core system is stable.
7. Build an “apply locally” workflow that proposes commands first and only runs them after approval.


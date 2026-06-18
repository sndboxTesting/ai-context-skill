# ADWI AUTO SYNC TEST

This file verifies that Suneel's local Open WebUI Knowledge sync automation works.

Important facts:

- Adwi is Suneel's local terminal AI assistant.
- Adwi runs locally through Ollama.
- Adwi currently uses `adwi:latest`, based on `qwen3:30b`.
- The Open WebUI Knowledge collection is named `Suneel Local AI Knowledge`.
- The local sync command is `sync-openwebui-knowledge`.
- The local watcher command is `start-openwebui-knowledge-watcher`.
- The secrets are stored under `/Users/MAC/SuneelWorkSpace/secrets`.
- Secret values should never be printed in chat or logs.

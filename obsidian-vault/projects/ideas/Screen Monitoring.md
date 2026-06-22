---
type: idea
status: planned
tags: [idea, roadmap, vision, monitoring]
updated: 2026-06-21
---

# Screen Monitoring

#idea #roadmap #vision

## Status
🔵 Planned — not started

## Why It Matters
Adwi can know what you're working on without you having to explain it. Periodic screenshots let it offer relevant suggestions, track context switches, and improve `/daily-brief` with actual work context instead of just inbox + priorities.

## Existing Related Files

| File | Relevance |
|------|-----------|
| `adwi/voice.py` | Has `record_screen()` stub concept |
| `adwi/adwi_cli.py` | `/screenshot-analyze` → `minicpm-v:latest` already wired |
| `adwi/bin/adwi-nightly-status` | Example of periodic shell script |

## Implementation Sketch

1. Add `adwi/screen_monitor.py` — periodic screencapture via `screencapture -x /tmp/adwi-screen.png`
2. Feed screenshot to `/screenshot-analyze` → `minicpm-v:latest` (5.5 GB, already loaded)
3. Extract: current app, window title, what user is doing
4. Write summary to memory.db via `AdwiMemory.ingest()`
5. Add a LaunchAgent to run every 10-15 min when on AC power and not idle
6. Surface in `/daily-brief` as "Context from your screen"

## Risks

- Privacy: screenshots captured locally only, never sent to cloud — must be documented
- Battery: only run on AC (same gate as SimLab)
- Noise: many screenshots will be identical (same window) — deduplicate by perceptual hash
- Storage: compress or delete after ingestion

## Next Action

Prototype `screencapture -x /tmp/test.png && adwi /screenshot-analyze /tmp/test.png` to validate the vision pipeline works end-to-end.

## Related Notes

- [[projects/ideas/Voice Input]]
- [[knowledge/Memory and Knowledge Map]]
- [[knowledge/Ideas Index]]

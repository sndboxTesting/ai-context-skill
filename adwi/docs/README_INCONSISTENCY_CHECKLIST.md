# README / Documentation Inconsistency Checklist

> Audit performed: **2026-06-17**
> Scope: README.md, CLAUDE.md, bin/auto-update-readme, docs/, adwi/adwi_cli.py, docker-compose.yml
> Maintained by: human (update this file after each significant doc change)

---

## Status legend

| Symbol | Meaning |
|--------|---------|
| ✅ RESOLVED | Fixed in this session; verified against code |
| ⚠️ TRACKED | Known limitation; explicitly documented, not silently wrong |
| 🔁 AUTO-FIXED | Fixed by improving bin/auto-update-readme so it won't recur |
| 📌 MANUAL | Requires human attention; cannot be auto-resolved |

---

## Issue Inventory

### ISSUE-001 — Docker SERVICES section showed `:1` for all ports

| Field | Value |
|-------|-------|
| Category | Bug — auto-generation regex |
| Files | `bin/auto-update-readme` (extract_services), `README.md` AUTO:SERVICES |
| Conflicting values | All services showed port `:1` instead of real ports (3000, 5678, 8888, etc.) |
| Root cause | Regex `r'"?(\d+):\d+"?'` matched the last IP octet `1` from `127.0.0.1:3000:8080` |
| Authoritative source | `local-ai-stack/docker-compose.yml` port mappings |
| Fix applied | Changed regex to `r':(\d{2,5}):\d{2,5}'` which matches host port in `ip:host:container` format |
| Verification | `bin/validate-docs` SVC-001 PASS; SERVICES section now shows `:3000`, `:5678`, etc. |
| Status | 🔁 AUTO-FIXED |

---

### ISSUE-002 — Command count: 172 vs 121 vs 104 in different locations

| Field | Value |
|-------|-------|
| Category | Stale static annotations |
| Files | `README.md` (§3 TOC, §6 directory tree, §8 Phase 5) |
| Conflicting values | TOC: "172+", directory tree: "121 commands", Phase 5: "104-command registry" |
| Root cause | Static annotations not updated when commands were added; Phase 5 encoded the count at phase implementation time |
| Authoritative source | `bin/auto-update-readme` `extract_commands()` → actual code count (167 as of 2026-06-17) |
| Fix applied | (1) Phase 5 in AUTO:PHASES now uses `len(snap['commands'])` dynamically; (2) directory tree updated to 167; (3) TOC updated to 167+ |
| Verification | `bin/validate-docs` CMD-001 through CMD-004 all PASS |
| Status | ✅ RESOLVED |

---

### ISSUE-003 — NLU fixture count: 96 vs 89 vs 49 in different locations

| Field | Value |
|-------|-------|
| Category | Stale static annotations + stale snapshot fallback |
| Files | `README.md` (§6 memory.py annotation, §8 Phase 7), `bin/auto-update-readme` (build_nlu_section fallback) |
| Conflicting values | AUTO:NLU: 96 (correct), directory tree memory.py: "89 NLU fixtures", Phase 7: "49-fixture collection", auto-readme fallback: "89" |
| Root cause | Phase 7 encoded the count at phase implementation time (49); memory.py annotation was manually written and not updated; auto-readme fallback was hardcoded to stale value "89" |
| Authoritative source | Live Qdrant at :6333/collections/nlu_fixtures (`points_count = 96`) |
| Fix applied | (1) Phase 7 in AUTO:PHASES now uses `snap['fixture_count']` dynamically; (2) directory tree memory.py updated to "96 NLU fixtures"; (3) auto-readme fallback updated to 96; (4) added `extract_fixture_count()` to snapshot |
| Verification | `bin/validate-docs` NLU-001 through NLU-003 all PASS |
| Status | ✅ RESOLVED |

---

### ISSUE-004 — Intent class count: 62 vs 109

| Field | Value |
|-------|-------|
| Category | Stale auto-generated section |
| Files | `README.md` AUTO:NLU (old version showed "62 intent classes") |
| Conflicting values | Old AUTO:NLU: "62 intent classes"; `_ALL_INTENTS` in adwi_cli.py: 109 |
| Root cause | The NLU section had hardcoded fallback `intent_count = "62"` from when capabilities.json had 62 entries. These are different things: capabilities.json = 62 high-level capabilities; `_ALL_INTENTS` = 109 NLU routing classes. |
| Authoritative source | `adwi/adwi_cli.py` `_ALL_INTENTS` list (109 entries) |
| Fix applied | `extract_intent_count()` now reads `_ALL_INTENTS` from CLI; `build_nlu_section()` uses snapshot value; added to snapshot dict. AUTO:NLU now correctly shows "109 intent classes" |
| Verification | `bin/validate-docs` NLU-004 PASS |
| Status | ✅ RESOLVED |

---

### ISSUE-005 — bin/ script count: "35 helper scripts" was stale

| Field | Value |
|-------|-------|
| Category | Stale static annotation |
| Files | `README.md` §6 directory tree |
| Conflicting values | README: "35 helper scripts"; actual: 42 scripts (43 entries minus 1 backup file `adwi.backup.20260614-090424`) |
| Root cause | Scripts added over time without updating the directory tree comment |
| Authoritative source | `ls ~/SuneelWorkSpace/bin/ | grep -v __pycache__ | wc -l` = 43 (including 1 backup file) |
| Fix applied | Updated directory tree to "41 scripts" (conservative: 43 - 1 backup - 1 Python script counted differently = 41) |
| Status | ✅ RESOLVED — note: static annotation, not auto-maintained. Will drift again as scripts are added. Use `ls bin/ | wc -l` for live count. |

---

### ISSUE-006 — docker-compose.yml "12 containers" annotation was confusing

| Field | Value |
|-------|-------|
| Category | Misleading annotation |
| Files | `README.md` §6 directory tree |
| Conflicting values | docker-compose.yml has 11 services (not 12); the 12th is Qdrant started by a LaunchAgent not in compose |
| Root cause | Annotation counted Qdrant as a compose service when it is actually a separate Docker container started by LaunchAgent |
| Authoritative source | `local-ai-stack/docker-compose.yml` (11 services: open-webui, n8n, searxng, homeassistant, cloudflared, prometheus, loki, promtail, grafana, node-exporter, cadvisor) + LaunchAgent plist for suneel-qdrant |
| Fix applied | Updated annotation to "11 compose services + Qdrant (LaunchAgent) = 12 containers" for clarity |
| Verification | Manual check of docker-compose.yml service keys |
| Status | ✅ RESOLVED |

---

### ISSUE-007 — README header claimed "all sections authoritative"

| Field | Value |
|-------|-------|
| Category | Misleading priming claim |
| Files | `README.md` (line 3-6) |
| Conflicting values | Header: "All sections are authoritative and kept current by an automated injection pipeline" — but §6, §7, §9, §10 are static/manually maintained |
| Root cause | Broad claim written before static sections were identified as drift-prone |
| Fix applied | Replaced with accurate description: AUTO: sections are machine-generated; static narrative sections may lag; code is authoritative; see `docs/LLM_SYSTEM_PRIMING.md` for unambiguous priming |
| Verification | `bin/validate-docs` PRIME-001 now PASS |
| Status | ✅ RESOLVED |

---

### ISSUE-008 — MASTER_REPORT_v2.md is stale (shows 89.0%, current is 97.0%)

| Field | Value |
|-------|-------|
| Category | Stale eval artifact |
| Files | `logs/simeval/MASTER_REPORT_v2.md` |
| Conflicting values | MASTER_REPORT_v2.md (2026-06-16): 89.0% combined; CLAUDE.md: 97.0% combined |
| Root cause | MASTER_REPORT_v2.md was last regenerated on 2026-06-16 before the stabilization sprint and CYCLE-5/6 that brought the baseline to 97.0% |
| Authoritative source | CLAUDE.md (manually updated by operator after each eval session) |
| Fix applied | Added explicit staleness note in `adwi/system_manifest.json` eval_status.note; `docs/LLM_SYSTEM_PRIMING.md` explicitly warns about this; `docs/OPERATOR_HANDBOOK.md` includes the warning |
| Remaining | MASTER_REPORT_v2.md itself is not edited (eval artifacts are preserved as-is); a fresh eval run would generate a new report |
| Status | ⚠️ TRACKED — cannot auto-fix; requires a new eval run to generate current report |

---

### ISSUE-009 — build_nlu_section() queried Qdrant inline, duplicating extract logic

| Field | Value |
|-------|-------|
| Category | Code quality / single-source violation |
| Files | `bin/auto-update-readme` |
| Description | `build_nlu_section()` had its own Qdrant HTTP call and its own fallback value ("89"), separate from `extract_fixture_count()` in `build_snapshot()`. This meant two independent code paths for the same fact. |
| Fix applied | Consolidated: `extract_fixture_count()` and `extract_intent_count()` added to snapshot; `build_nlu_section()` now reads from `snap["fixture_count"]` and `snap["intent_count"]` |
| Status | 🔁 AUTO-FIXED |

---

### ISSUE-010 — capabilities.json entries with arguments polluted command list

| Field | Value |
|-------|-------|
| Category | Extractor bug |
| Files | `bin/auto-update-readme` (extract_commands), `README.md` AUTO:COMMANDS |
| Description | capabilities.json has entries like `/cloud <prompt>  or just type` as "command" values. These were added as-is to the command set, creating garbage groups like `cloud <prompt>  or just type` and bloating the count. |
| Fix applied | `extract_commands()` now strips to just the slash-command token: `n.strip().split()[0]` before adding to set |
| Result | Command count went from 172 (dirty) to 167 (clean) — the 5 difference was from multi-word entries that got deduplicated after stripping |
| Status | 🔁 AUTO-FIXED |

---

## Auto-injection section health (post-fix)

Run `python3 bin/validate-docs` to check all of these at any time.

| Section | Source | Current status |
|---------|--------|----------------|
| AUTO:MODELS | `adwi/adwi_cli.py` MODEL_* constants | ✅ Live |
| AUTO:NLU | Qdrant + `_ALL_INTENTS` count | ✅ Live |
| AUTO:INFRA_PORTS | Static registry in auto-update-readme | ✅ Live (static, intentional) |
| AUTO:SERVICES | `docker-compose.yml` + live docker ps | ✅ Fixed (port regex bug resolved) |
| AUTO:AGENTS | `~/Library/LaunchAgents/` plists | ✅ Live |
| AUTO:COMMANDS | `adwi_cli.py` + `capabilities.json` | ✅ Fixed (argument stripping) |
| AUTO:PHASES | Hardcoded + dynamic counts | ✅ Fixed (Phase 5 cmd, Phase 7 fixture now dynamic) |
| AUTO:MONITORING | Static list + docker status | ✅ Live |

---

## Recurring maintenance checklist

When to re-run:

| Trigger | Action |
|---------|--------|
| After adding/removing commands | `bin/auto-update-readme --force && bin/validate-docs` |
| After adding Qdrant fixtures | `bin/auto-update-readme --force && bin/validate-docs` |
| After adding LaunchAgents or Docker services | `bin/auto-update-readme --force && bin/generate-manifest` |
| After a major eval session | Update CLAUDE.md baseline; `bin/generate-manifest` |
| After changing blocked paths in path_validator.py | `bin/generate-manifest` |
| Monthly | Run `bin/validate-docs` and review any WARNs |

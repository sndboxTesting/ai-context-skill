---
name: adwi-sync-check
description: Verify NLU intent patterns and test case lists are in sync across adwi_cli.py, run_large_eval.py, and run_large_eval_p2.py before committing. Diffs intent names found in each file and reports mismatches.
metadata:
  disable-model-invocation: true
---

```bash
#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=~/SuneelWorkSpace
CLI="$WORKSPACE/adwi/adwi_cli.py"
P1="$WORKSPACE/adwi/adwi/logs/simeval/run_large_eval.py"
P2="$WORKSPACE/adwi/adwi/logs/simeval/run_large_eval_p2.py"

echo "=== Adwi NLU 3-file sync check ==="
echo ""

# 1. Syntax check all three
for f in "$CLI" "$P1" "$P2"; do
  if python3 -m py_compile "$f" 2>&1; then
    echo "✓ syntax OK: $(basename $f)"
  else
    echo "✗ SYNTAX ERROR: $(basename $f)"
    exit 1
  fi
done
echo ""

# 2. Extract intent names from _REGEX_INTENTS in adwi_cli.py
INTENTS_CLI=$(grep -oP '^\s+\(\s*"\K[a-z_]+' "$CLI" | sort -u 2>/dev/null || true)

# 3. Extract scenario intent names referenced in eval files
INTENTS_P1=$(grep -oP '"intent":\s*"\K[a-z_]+' "$P1" | sort -u 2>/dev/null || true)
INTENTS_P2=$(grep -oP '"intent":\s*"\K[a-z_]+' "$P2" | sort -u 2>/dev/null || true)

echo "Intent names in adwi_cli.py _REGEX_INTENTS:  $(echo "$INTENTS_CLI" | wc -l | tr -d ' ')"
echo "Intent names referenced in run_large_eval.py: $(echo "$INTENTS_P1" | wc -l | tr -d ' ')"
echo "Intent names referenced in run_large_eval_p2.py: $(echo "$INTENTS_P2" | wc -l | tr -d ' ')"
echo ""

# 4. Find intents in eval files NOT in cli (potential stale references)
P1_NOT_IN_CLI=$(comm -23 <(echo "$INTENTS_P1") <(echo "$INTENTS_CLI") 2>/dev/null || true)
P2_NOT_IN_CLI=$(comm -23 <(echo "$INTENTS_P2") <(echo "$INTENTS_CLI") 2>/dev/null || true)

if [ -n "$P1_NOT_IN_CLI" ]; then
  echo "⚠ Intents in run_large_eval.py NOT in adwi_cli.py:"
  echo "$P1_NOT_IN_CLI" | sed 's/^/  - /'
else
  echo "✓ run_large_eval.py intents all present in adwi_cli.py"
fi

if [ -n "$P2_NOT_IN_CLI" ]; then
  echo "⚠ Intents in run_large_eval_p2.py NOT in adwi_cli.py:"
  echo "$P2_NOT_IN_CLI" | sed 's/^/  - /'
else
  echo "✓ run_large_eval_p2.py intents all present in adwi_cli.py"
fi

echo ""
echo "Sync check complete. Run /adwi-check for full syntax + Gmail NLU regression test."
```

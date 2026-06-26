#!/bin/bash
# Hook script to embed updated memory files into the vector database.
# Usage: ./memory_write_hook.sh <file_path>

FILE_PATH="$1"
if [ -z "$FILE_PATH" ]; then
    echo "Usage: $0 <file_path>"
    exit 1
fi

WORKSPACE_ROOT="/Users/MAC/SuneelWorkSpace"

# Resolve absolute path
ABS_PATH=$(python3 -c "import os; print(os.path.abspath('$FILE_PATH'))")

if [ -f "$ABS_PATH" ] && [[ "$ABS_PATH" == "$WORKSPACE_ROOT"* ]]; then
    # Only index files that are part of memory, decisions, patterns, insights, or handoffs
    # And specifically exclude Chroma persistent storage and model cache
    LOWER_PATH=$(echo "$FILE_PATH" | tr '[:upper:]' '[:lower:]')
    if [[ "$LOWER_PATH" == *"chroma_store"* || "$LOWER_PATH" == *".hf_cache"* ]]; then
        echo "Skipping hook: Internal vector storage file: $FILE_PATH"
    elif [[ "$LOWER_PATH" == *"memory"* || "$LOWER_PATH" == *"decision"* || "$LOWER_PATH" == *"pattern"* || "$LOWER_PATH" == *"insight"* || "$LOWER_PATH" == *"handoff"* ]]; then
        python3 "$WORKSPACE_ROOT/agent-system/memory/vector/embed_engine.py" --file "$ABS_PATH"
    else
        echo "Skipping hook: File is not memory-related: $FILE_PATH"
    fi
else
    echo "Skipping hook: File outside workspace or not found: $FILE_PATH"
fi

#!/usr/bin/env bash
WORKSPACE="${WORKSPACE:-$HOME/SuneelWorkSpace}"
python3 "$WORKSPACE/autolab/promotion_gate.py" --status

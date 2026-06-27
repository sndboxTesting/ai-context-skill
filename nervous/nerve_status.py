#!/usr/bin/env python3
"""nerve-status — shows health of all 12 organs in the nervous system."""
import json, os, sys

WORKSPACE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
REGISTRY_PATH = os.path.join(WORKSPACE, "nervous/nerve_registry.json")

ORGANS = ["brain","heart","eyes","ears","nervous","skeleton","blood","hands","mouth","dna","lab","spine"]

def main():
    try:
        with open(REGISTRY_PATH) as f:
            registry = json.load(f)
    except Exception:
        print("❌ nerve_registry.json not found"); sys.exit(1)

    print("\n🫀 Nerve System Status\n")
    all_ok = True

    for organ in ORGANS:
        cfg = registry["organs"].get(organ, {})
        organ_path = os.path.join(WORKSPACE, cfg.get("path", organ + "/"))
        inbox_path = os.path.join(WORKSPACE, cfg.get("inbox", organ + "/nerve_inbox/"))
        nerve_json = os.path.join(organ_path, "nerve.json")

        exists      = "✅" if os.path.isdir(organ_path) else "❌"
        nerve_ok    = "✅" if os.path.isfile(nerve_json) else "❌"
        inbox_msgs  = len([f for f in os.listdir(inbox_path) if f.endswith(".json")]) if os.path.isdir(inbox_path) else -1
        inbox_ok    = "✅ clear" if inbox_msgs == 0 else ("❌ missing" if inbox_msgs < 0 else f"📬 {inbox_msgs} msg(s)")

        overall = "✅" if (exists == "✅" and nerve_ok == "✅" and inbox_msgs == 0) else "⚠️"
        if overall != "✅": all_ok = False

        print(f"  {overall} {organ:<12} | dir: {exists} | nerve.json: {nerve_ok} | inbox: {inbox_ok}")

    print()
    if all_ok:
        print("✅ All organs healthy\n")
    else:
        print("⚠️  Some organs need attention\n")

if __name__ == "__main__":
    main()

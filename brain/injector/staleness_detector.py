#!/usr/bin/env python3
"""Brain Notes Staleness Detector. Finds stale and orphan markdown notes."""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(os.environ.get('WORKSPACE', Path(__file__).resolve().parent.parent.parent))
BRAIN_DIR = WORKSPACE / 'brain'
STALE_THRESHOLD_DAYS = 30


def scan_notes() -> list[dict]:
    notes = []
    skip = {'graph', '.obsidian', '__pycache__', 'vector', 'chroma_store', 'nerve_inbox'}
    
    # Track all incoming backlinks
    all_links = set()
    all_stems = {}
    
    # First pass: collect note details and outgoing links
    md_files = list(BRAIN_DIR.rglob('*.md'))
    for md_file in md_files:
        if any(s in md_file.parts for s in skip):
            continue
        rel = str(md_file.relative_to(BRAIN_DIR))
        all_stems[md_file.stem] = rel
        
        try:
            content = md_file.read_text(errors='ignore')
            links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', content)
            links = [l.strip() for l in links]
            
            age_days = (datetime.now().timestamp() - md_file.stat().st_mtime) / 86400
            notes.append({
                'rel': rel,
                'path': md_file,
                'age_days': age_days,
                'links': links,
                'backlink_count': 0
            })
            
            for l in links:
                all_links.add(l)
        except Exception:
            pass

    # Second pass: calculate backlink counts
    for note in notes:
        # Check if this note's stem or relative path is referenced anywhere
        stem = Path(note['rel']).stem
        if stem in all_links or note['rel'] in all_links:
            note['backlink_count'] += 1

    return notes


def main():
    if not BRAIN_DIR.exists():
        print(f"ERROR: brain/ directory not found at {BRAIN_DIR}")
        sys.exit(1)

    notes = scan_notes()
    
    print("\n📝 Brain Notes Staleness and Adjacency Report")
    print(f"Total notes scanned: {len(notes)}\n")

    # Stale notes
    stale_notes = [n for n in notes if n['age_days'] >= STALE_THRESHOLD_DAYS]
    stale_notes.sort(key=lambda x: -x['age_days'])
    
    print(f"⏳ Stale Notes (unmodified for > {STALE_THRESHOLD_DAYS} days):")
    if stale_notes:
        for n in stale_notes[:10]:
            print(f"  - {n['rel']} ({int(n['age_days'])} days old)")
        if len(stale_notes) > 10:
            print(f"  ... and {len(stale_notes) - 10} more.")
    else:
        print("  ✅ No stale notes found!")

    # Orphan notes (no backlinks and no out-links)
    orphans = [n for n in notes if n['backlink_count'] == 0 and len(n['links']) == 0]
    print(f"\n🕸️ Orphan Notes (isolated with no links):")
    if orphans:
        for n in orphans[:10]:
            print(f"  - {n['rel']}")
        if len(orphans) > 10:
            print(f"  ... and {len(orphans) - 10} more.")
    else:
        print("  ✅ No orphan notes found!")
    print()


if __name__ == '__main__':
    main()

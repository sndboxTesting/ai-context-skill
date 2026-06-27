#!/usr/bin/env python3
"""Build a NetworkX knowledge graph from Obsidian-style backlinks in brain/ notes."""
import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(os.environ.get('WORKSPACE', Path.home() / 'SuneelWorkSpace'))
BRAIN_DIR = WORKSPACE / 'brain'
GRAPH_FILE = WORKSPACE / 'brain/graph/knowledge_graph.json'
ORPHAN_FILE = WORKSPACE / 'brain/graph/reports/orphan_notes.md'

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False
    print("INFO: networkx not installed — using fallback adjacency mode.")
    print("      For full features: pip3 install networkx --break-system-packages")


def scan_notes(brain_dir: Path) -> dict:
    notes = {}
    skip = {'graph', '.obsidian', '__pycache__', 'vector', 'chroma_store'}
    for md_file in brain_dir.rglob('*.md'):
        if any(s in md_file.parts for s in skip):
            continue
        rel = str(md_file.relative_to(brain_dir))
        try:
            content = md_file.read_text(errors='ignore')
            links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', content)
            links = [l.strip() for l in links]
            notes[rel] = {'path': str(md_file), 'links': links, 'size': md_file.stat().st_size}
        except Exception:
            pass
    return notes


def build_graph_nx(notes: dict) -> dict:
    import networkx as nx
    G = nx.DiGraph()
    all_stems = {Path(n).stem: n for n in notes}
    all_names = set(notes.keys())

    for note, data in notes.items():
        G.add_node(note, size=data['size'], link_count=len(data['links']))

    for note, data in notes.items():
        for link in data['links']:
            # Try exact match first, then stem match
            target = None
            if link in all_names:
                target = link
            elif link in all_stems:
                target = all_stems[link]
            if target:
                G.add_edge(note, target)

    return nx.node_link_data(G)


def build_graph_simple(notes: dict) -> dict:
    all_stems = {Path(n).stem: n for n in notes}
    all_names = set(notes.keys())
    graph = {'nodes': [], 'links': []}

    for note, data in notes.items():
        graph['nodes'].append({
            'id': note,
            'size': data['size'],
            'link_count': len(data['links'])
        })
        for link in data['links']:
            target = all_names.get(link) if link in all_names else all_stems.get(link)
            if target:
                graph['links'].append({'source': note, 'target': target})

    return graph


def find_orphans(graph_data: dict) -> list:
    nodes = {n['id'] for n in graph_data.get('nodes', [])}
    connected = set()
    for link in graph_data.get('links', []):
        connected.add(link.get('source', ''))
        connected.add(link.get('target', ''))
    return sorted(n for n in nodes if n not in connected)


def main():
    print(f"[{datetime.now():%H:%M:%S}] Scanning brain/ for notes...")
    if not BRAIN_DIR.exists():
        print(f"ERROR: brain/ directory not found at {BRAIN_DIR}")
        sys.exit(1)

    notes = scan_notes(BRAIN_DIR)
    print(f"  Found {len(notes)} notes")

    print(f"[{datetime.now():%H:%M:%S}] Building knowledge graph...")
    if HAS_NX:
        graph = build_graph_nx(notes)
    else:
        graph = build_graph_simple(notes)

    GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GRAPH_FILE, 'w') as f:
        json.dump(graph, f, indent=2)

    orphans = find_orphans(graph)
    links_count = len(graph.get('links', []))

    print(f"  Total notes:  {len(notes)}")
    print(f"  Total links:  {links_count}")
    print(f"  Orphan notes: {len(orphans)}")

    ORPHAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ORPHAN_FILE, 'w') as f:
        f.write(f"# Orphan Notes\nGenerated: {datetime.now().isoformat()}\nTotal: {len(orphans)}\n\n")
        for o in orphans:
            f.write(f"- {o}\n")

    print(f"[{datetime.now():%H:%M:%S}] Graph saved → brain/graph/knowledge_graph.json")
    print(f"[{datetime.now():%H:%M:%S}] Orphans saved → brain/graph/reports/orphan_notes.md")


if __name__ == '__main__':
    main()

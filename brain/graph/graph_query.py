#!/usr/bin/env python3
"""Query the workspace knowledge graph."""
import json
import sys
import argparse
from pathlib import Path
from collections import Counter
import os

WORKSPACE = Path(os.environ.get('WORKSPACE', Path.home() / 'SuneelWorkSpace'))
GRAPH_FILE = WORKSPACE / 'brain/graph/knowledge_graph.json'


def load_graph() -> dict:
    if not GRAPH_FILE.exists():
        print("Graph not built yet. Run: brain-graph-build")
        sys.exit(1)
    with open(GRAPH_FILE) as f:
        return json.load(f)


def get_neighbors(graph: dict, node: str, depth: int = 1) -> set:
    neighbors = set()
    links = graph.get('links', [])
    queue = [node]
    for _ in range(depth):
        next_queue = []
        for n in queue:
            for link in links:
                if link.get('source') == n and link['target'] not in neighbors:
                    neighbors.add(link['target'])
                    next_queue.append(link['target'])
                elif link.get('target') == n and link['source'] not in neighbors:
                    neighbors.add(link['source'])
                    next_queue.append(link['source'])
        queue = next_queue
    return neighbors


def cmd_topic(graph: dict, keyword: str, as_json: bool = False):
    nodes = graph.get('nodes', [])
    matching = [n['id'] for n in nodes if keyword.lower() in n['id'].lower()]
    result = {}
    for m in matching:
        result[m] = sorted(get_neighbors(graph, m, depth=2))
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\nNotes matching '{keyword}' ({len(matching)} found):")
        for note, neighbors in result.items():
            print(f"  📄 {note}")
            for nb in neighbors[:5]:
                print(f"       → {nb}")
            if len(neighbors) > 5:
                print(f"       ... and {len(neighbors) - 5} more")


def cmd_cluster(graph: dict, note_name: str, as_json: bool = False):
    neighbors = sorted(get_neighbors(graph, note_name, depth=3))
    if as_json:
        print(json.dumps({note_name: neighbors}, indent=2))
    else:
        print(f"\nCluster around '{note_name}' ({len(neighbors)} connected notes):")
        for n in neighbors:
            print(f"  {n}")


def cmd_orphans(graph: dict, as_json: bool = False):
    nodes = {n['id'] for n in graph.get('nodes', [])}
    links = graph.get('links', [])
    connected = set()
    for link in links:
        connected.add(link.get('source', ''))
        connected.add(link.get('target', ''))
    orphans = sorted(n for n in nodes if n not in connected)
    if as_json:
        print(json.dumps(orphans, indent=2))
    else:
        print(f"\nOrphan notes ({len(orphans)} total — no incoming or outgoing links):")
        for o in orphans:
            print(f"  {o}")


def cmd_top(graph: dict, n: int = 10, as_json: bool = False):
    links = graph.get('links', [])
    counts = Counter()
    for link in links:
        counts[link.get('source', '')] += 1
        counts[link.get('target', '')] += 1
    top = counts.most_common(n)
    if as_json:
        print(json.dumps([{"note": k, "connections": v} for k, v in top], indent=2))
    else:
        print(f"\nTop {n} most-connected notes:")
        for i, (note, count) in enumerate(top, 1):
            print(f"  {i:2d}. [{count:3d} links] {note}")


def main():
    parser = argparse.ArgumentParser(description='Query workspace knowledge graph')
    parser.add_argument('--topic', help='Find notes matching keyword and their neighbors')
    parser.add_argument('--cluster', help='Find all notes connected to a given note (depth=3)')
    parser.add_argument('--orphans', action='store_true', help='List notes with no connections')
    parser.add_argument('--top', type=int, metavar='N', help='List top N most-connected notes')
    parser.add_argument('--path', nargs=2, metavar=('NOTE_A', 'NOTE_B'), help='Find shortest path between two notes')
    parser.add_argument('--json', action='store_true', dest='as_json', help='Output as JSON')
    args = parser.parse_args()

    graph = load_graph()
    node_count = len(graph.get('nodes', []))
    link_count = len(graph.get('links', []))
    print(f"Graph: {node_count} notes, {link_count} links")

    if args.topic:
        cmd_topic(graph, args.topic, args.as_json)
    elif args.cluster:
        cmd_cluster(graph, args.cluster, args.as_json)
    elif args.orphans:
        cmd_orphans(graph, args.as_json)
    elif args.top:
        cmd_top(graph, args.top, args.as_json)
    elif args.path:
        print(f"\n--path requires networkx. Run: pip3 install networkx --break-system-packages")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

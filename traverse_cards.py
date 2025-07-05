#!/usr/bin/env python3
"""
cards_traverse.py — CLI graph analysis for cards.py networks
Find paths, ancestry, clusters, and more over Links/Sequence/parent relationships.
"""
import sys
import argparse
from pathlib import Path
import yaml
from collections import deque, defaultdict

CARD_DIR = Path.home() / "cards"

def load_cards():
    graph = defaultdict(set)
    parents = {}
    cards = {}
    for file in CARD_DIR.glob("*.yaml"):
        if file.name == "index.yaml": continue
        d = yaml.safe_load(file.read_text())
        cid = d["ID"]
        cards[cid] = d
        # Links (bidirectional)
        for t in d.get("Links", []):
            graph[cid].add(t)
            graph[t].add(cid)
        # SequenceNext (unidirectional)
        seq = d.get("SequenceNext")
        if seq:
            graph[cid].add(seq)
        # Parent (by hierarchical ID, e.g. 7.2.1 → 7.2)
        if "." in cid:
            parent = ".".join(cid.split(".")[:-1])
            parents[cid] = parent
            graph[cid].add(parent)
            graph[parent].add(cid)
    return graph, parents, cards

def bfs_path(graph, start, goal):
    queue = deque([(start, [start])])
    visited = set()
    while queue:
        node, path = queue.popleft()
        if node == goal:
            return path
        visited.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited and neighbor not in path:
                queue.append((neighbor, path + [neighbor]))
    return None

def ancestry(parents, start):
    # Returns the lineage chain up to root (inclusive)
    path = [start]
    curr = start
    while curr in parents:
        curr = parents[curr]
        path.append(curr)
    return list(reversed(path))

def ego_network(graph, start, depth=1):
    # All nodes within N steps from start
    out = set([start])
    frontier = set([start])
    for _ in range(depth):
        nextfront = set()
        for node in frontier:
            nextfront |= set(graph.get(node, []))
        nextfront -= out
        if not nextfront:
            break
        out |= nextfront
        frontier = nextfront
    return out

def sequence_walk(cards, start, backward=False):
    path = [start]
    curr = start
    if backward:
        # Go "backward" via parent (hierarchy) and/or reverse sequence
        prev = [k for k, v in cards.items() if v.get("SequenceNext") == curr]
        while prev:
            curr = prev[0]
            path.insert(0, curr)
            prev = [k for k, v in cards.items() if v.get("SequenceNext") == curr]
    else:
        # Forward via SequenceNext
        while True:
            nxt = cards[curr].get("SequenceNext")
            if not nxt: break
            path.append(nxt)
            curr = nxt
    return path

def main():
    parser = argparse.ArgumentParser(
        description="Traverse cards network via links, sequence, and parent relationships."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Pathfinding
    p = sub.add_parser("path", help="Find shortest path (links/sequence/parent) between two cards")
    p.add_argument("start")
    p.add_argument("end")

    # Ancestry
    a = sub.add_parser("ancestry", help="Show lineage from card to root via parent hierarchy")
    a.add_argument("card")

    # Ego network
    e = sub.add_parser("ego", help="Show N-step neighborhood (ego network) of a card")
    e.add_argument("card")
    e.add_argument("--depth", type=int, default=1)

    # Sequence walk
    s = sub.add_parser("sequence", help="Walk the SequenceNext chain from a card")
    s.add_argument("card")
    s.add_argument("--backward", action="store_true")

    args = parser.parse_args()
    graph, parents, cards = load_cards()

    if args.cmd == "path":
        if args.start not in cards or args.end not in cards:
            print("Card(s) not found.")
            sys.exit(1)
        path = bfs_path(graph, args.start, args.end)
        if path:
            print(" -> ".join(path))
        else:
            print("No path found.")
    elif args.cmd == "ancestry":
        if args.card not in cards:
            print("Card not found.")
            sys.exit(1)
        print(" > ".join(ancestry(parents, args.card)))
    elif args.cmd == "ego":
        if args.card not in cards:
            print("Card not found.")
            sys.exit(1)
        print(", ".join(sorted(ego_network(graph, args.card, args.depth))))
    elif args.cmd == "sequence":
        if args.card not in cards:
            print("Card not found.")
            sys.exit(1)
        seq = sequence_walk(cards, args.card, args.backward)
        arrow = " <- " if args.backward else " -> "
        print(arrow.join(seq))

if __name__ == "__main__":
    main()

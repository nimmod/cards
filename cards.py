#!/usr/bin/env python3
"""
cards.py — Zettelkasten‑style Card System (macOS / POSIX)
========================================================
A self‑contained CLI for managing physical/digital index cards with
atomic IDs, YAML storage, and daily/weekly workflow support.
Guide text lives in *guide.txt* in the same directory.
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import shutil
import sys
from pathlib import Path
import tempfile
import os
import yaml

# ───────────────────────── Configuration ──────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
GUIDE_FILE = SCRIPT_DIR / "guide.txt"

# Default directories (will be overridden in test mode)
CARD_DIR = Path.home() / "cards"
CARD_DIR.mkdir(exist_ok=True)
BACKUP_DIR = CARD_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)
INDEX_FILE = CARD_DIR / "index.yaml"
LOCK_FILE = CARD_DIR / "index.yaml.lock"
BACKUP_LIMIT = 50

IS_TEST_MODE = False

FIELDS = [
    "ID", "Date", "Type", "Title", "Summary", "Tags",
    "Links", "SequenceNext", "Context", "Next", "Body",
]
TYPES = ["idea", "literature"]

def set_test_mode():
    global CARD_DIR, BACKUP_DIR, INDEX_FILE, LOCK_FILE, IS_TEST_MODE
    d = Path(tempfile.mkdtemp(prefix="cards_test_"))
    CARD_DIR = d
    BACKUP_DIR = CARD_DIR / "backups"; BACKUP_DIR.mkdir(exist_ok=True)
    INDEX_FILE = CARD_DIR / "index.yaml"
    LOCK_FILE = CARD_DIR / "index.yaml.lock"
    IS_TEST_MODE = True

# ───────────────────────── Utility ────────────────────────────────

def _lock(path: Path):
    fp = path.open("a+")
    fcntl.flock(fp, fcntl.LOCK_EX)
    return fp

def _backup(path: Path):
    if path.exists():
        ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        dst = BACKUP_DIR / f"{path.stem}_{ts}.yaml"
        shutil.copy2(path, dst)
        # prune
        files = sorted(BACKUP_DIR.glob(f"{path.stem}_*.yaml"))
        for stale in files[:-BACKUP_LIMIT]:
            stale.unlink(missing_ok=True)

def edit_body_with_editor(initial=""):
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False, mode="w+") as tf:
        tf.write(initial)
        tf.flush()
        os.system(f"{editor} {tf.name}")
        tf.seek(0)
        body = tf.read()
    os.unlink(tf.name)
    return body

# ─────────────────────── ID generation ────────────────────────────

def _next_child(parent: str, existing: list[str]) -> str:
    prefix = f"{parent}."
    nums = [int(e[len(prefix):]) for e in existing if e.startswith(prefix) and e[len(prefix):].isdigit()]
    return f"{parent}.{1 if not nums else max(nums)+1}"

def generate_id(parent: str | None = None) -> str:
    """Atomic, lock‑protected ID creation."""
    with _lock(LOCK_FILE):
        existing = [p.stem for p in CARD_DIR.glob("*.yaml") if p.stem != "index"]
        if parent is None:
            tops = [int(e) for e in existing if e.isdigit()]
            return str(1 if not tops else max(tops)+1)
        if not (CARD_DIR / f"{parent}.yaml").exists():
            sys.exit(f"Parent ID '{parent}' not found")
        return _next_child(parent, existing)

# ───────────────────── YAML IO helpers ────────────────────────────

def read_card(cid: str) -> dict | None:
    path = CARD_DIR / f"{cid}.yaml"
    if not path.exists():
        return None
    with _lock(path):
        return yaml.safe_load(path.read_text()) or {}

def write_card(data: dict):
    path = CARD_DIR / f"{data['ID']}.yaml"
    _backup(path)
    with _lock(path):
        yaml.safe_dump(data, path.open("w"))

def load_index() -> dict:
    if not INDEX_FILE.exists():
        return {}
    with _lock(INDEX_FILE):
        return yaml.safe_load(INDEX_FILE.read_text()) or {}

def save_index(idx: dict):
    _backup(INDEX_FILE)
    with _lock(INDEX_FILE):
        yaml.safe_dump(idx, INDEX_FILE.open("w"))

# ─────────────────────── Parser ───────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cards.py", formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--test-mode", action="store_true", help="Run in test mode (uses temp card storage)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("genid").add_argument("parent", nargs="?")

    reg = sub.add_parser("register")
    reg.add_argument("id", nargs="?")
    reg.add_argument("-y", "--type", choices=TYPES, required=True)
    reg.add_argument("-t", "--title", required=True)
    reg.add_argument("-u", "--summary", default="")
    reg.add_argument("-g", "--tags", nargs="*", default=[])
    reg.add_argument("-l", "--links", nargs="*", default=[])
    reg.add_argument("-s", "--sequence", default="")
    reg.add_argument("-p", "--parent")
    reg.add_argument("-c", "--context", default="")
    reg.add_argument("-n", "--next", default="")
    reg.add_argument("-b", "--body", default="")

    upd = sub.add_parser("update")
    upd.add_argument("id")
    upd.add_argument("--title"); upd.add_argument("--summary"); upd.add_argument("--body")
    upd.add_argument("--context"); upd.add_argument("--next"); upd.add_argument("--type", choices=TYPES)
    upd.add_argument("--sequence"); upd.add_argument("--force", action="store_true")
    upd.add_argument("--add-tag", nargs="*"); upd.add_argument("--remove-tag", nargs="*")
    upd.add_argument("--add-link", nargs="*"); upd.add_argument("--remove-link", nargs="*")


    sub.add_parser("list")
    sub.add_parser("index")
    g = sub.add_parser("guide")

    d = sub.add_parser("delete")
    d.add_argument("id", help="Card ID to delete")
    d.add_argument("--force", action="store_true", help="Delete without confirmation")


    s = sub.add_parser("show"); s.add_argument("id")
    f = sub.add_parser("find"); f.add_argument("-g", "--tags", nargs="+", required=True)
    l = sub.add_parser("link"); l.add_argument("source"); l.add_argument("target")
    seq = sub.add_parser("sequence"); seq.add_argument("source"); seq.add_argument("target"); seq.add_argument("--force", action="store_true")
    back = sub.add_parser("backlinks"); back.add_argument("id")
    return p

# ─────────────────── Command handlers ────────────────────────────

def cmd_genid(a):
    print(generate_id(a.parent))


def cmd_register(a):
    if a.id and a.parent:
        sys.exit("Cannot supply both ID and --parent")
    cid = a.id or generate_id(a.parent)
    if not a.title.strip():
        sys.exit("Title cannot be empty")
    body = a.body.strip()
    if not body:
        body = edit_body_with_editor()
        if not body.strip():
            sys.exit("Body cannot be empty")
    idx = load_index()
    if cid in idx:
        sys.exit("ID exists")
    data = {k: None for k in FIELDS}
    data.update(ID=cid, Date=datetime.date.today().isoformat(), Type=a.type,
                Title=a.title.strip(), Summary=a.summary.strip(), Tags=a.tags,
                Links=a.links, SequenceNext=a.sequence, Context=a.context.strip(),
                Next=a.next.strip(), Body=body)
    write_card(data); idx[cid] = data["Title"]; save_index(idx); print(cid)


def cmd_update(a):
    card = read_card(a.id) or sys.exit("Card not found")
    changed = False
    def _set(k, v):
        nonlocal changed
        if v is not None and v != card.get(k):
            card[k] = v; changed = True
    _set("Title", a.title); _set("Summary", a.summary); _set("Body", a.body)
    _set("Context", a.context); _set("Next", a.next); _set("Type", a.type)
    if a.sequence is not None:
        if card.get("SequenceNext") and card["SequenceNext"] != a.sequence and not a.force:
            sys.exit("SequenceNext exists; use --force to overwrite")
        card["SequenceNext"] = a.sequence; changed = True
    # tags
    if a.add_tag:
        card.setdefault("Tags", [])
        for t in a.add_tag:
            if t not in card["Tags"]:
                card["Tags"].append(t); changed = True
    if a.remove_tag:
        before = set(card.get("Tags", []))
        card["Tags"] = [t for t in card.get("Tags", []) if t not in a.remove_tag]
        changed |= before != set(card["Tags"])
    # links
    if a.add_link:
        card.setdefault("Links", [])
        for l in a.add_link:
            if l not in card["Links"]:
                card["Links"].append(l); changed = True
    if a.remove_link:
        before = set(card.get("Links", []))
        card["Links"] = [l for l in card.get("Links", []) if l not in a.remove_link]
        changed |= before != set(card["Links"])
    if not card["Title"].strip() or not card["Body"].strip():
        sys.exit("Title and Body cannot be empty")
    if changed:
        write_card(card); idx = load_index(); idx[card["ID"]] = card["Title"]; save_index(idx)
        print(f"Updated {card['ID']}")
    else:
        print("No changes applied")

def cmd_delete(a):
    path = CARD_DIR / f"{a.id}.yaml"
    if not path.exists():
        sys.exit("Card not found")
    if not a.force:
        resp = input(f"Delete card {a.id} ({path})? [y/N]: ").strip().lower()
        if resp != "y":
            print("Aborted")
            return
    # Remove from index
    idx = load_index()
    idx.pop(a.id, None)
    save_index(idx)
    # Remove file
    path.unlink()
    print(f"Deleted card {a.id}")



def cmd_list(_):
    for f in sorted(CARD_DIR.glob("*.yaml")):
        if f.name == "index.yaml": continue
        d = read_card(f.stem)
        tags = ", ".join(map(str, d.get("Tags", [])))
        print(f"{d['ID']:>6} ({d['Type']}) {d['Title']} [{tags}]")


def cmd_show(a):
    d = read_card(a.id) or sys.exit("Card not found")
    for f in FIELDS:
        print(f"{f}: {d.get(f)}")

def cmd_find(a):
    wanted = set(a.tags)
    for f in CARD_DIR.glob("*.yaml"):
        if f.name == "index.yaml": continue
        d = read_card(f.stem)
        if wanted.issubset(set(d.get("Tags", []))):
            print(d["ID"])

def cmd_link(a):
    if a.source == a.target:
        sys.exit("Cannot link a card to itself")
    s = read_card(a.source); t = read_card(a.target)
    if not s or not t:
        sys.exit("Invalid IDs")
    for c, other in ((s, a.target), (t, a.source)):
        c.setdefault("Links", [])
        if other not in c["Links"]:
            c["Links"].append(other)
            write_card(c)
    print(f"Linked {a.source} ↔ {a.target}")

def cmd_sequence(a):
    s = read_card(a.source); t = read_card(a.target)
    if not s or not t:
        sys.exit("Invalid IDs")
    if s.get("SequenceNext") and s["SequenceNext"] != a.target and not a.force:
        sys.exit("SequenceNext already set; use --force to overwrite")
    s["SequenceNext"] = a.target
    write_card(s)
    print(f"Sequenced {a.source} → {a.target}")

def cmd_backlinks(a):
    refs = []
    for f in CARD_DIR.glob("*.yaml"):
        if f.name == "index.yaml":
            continue
        d = read_card(f.stem)
        if a.id in d.get("Links", []):
            refs.append(f.stem)
    for r in sorted(refs):
        print(r)

def cmd_guide(_):
    if GUIDE_FILE.exists():
        print(GUIDE_FILE.read_text())
    else:
        print("guide.txt file not found next to cards.py")

def cmd_index(_):
    print(INDEX_FILE)

# ─────────────────── Main entry ────────────────────────────

__all__ = [
    "generate_id", "read_card", "write_card", "cmd_register", "cmd_update",
    "cmd_link", "cmd_sequence", "cmd_backlinks", "cmd_show", "cmd_list",
    "cmd_find"
]

def main():
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "test_mode", False):
        set_test_mode()
    dispatch = {
        "genid": cmd_genid,
        "register": cmd_register,
        "update": cmd_update,
        "list": cmd_list,
        "show": cmd_show,
        "find": cmd_find,
        "link": cmd_link,
        "sequence": cmd_sequence,
        "backlinks": cmd_backlinks,
        "index": cmd_index,
        "guide": cmd_guide,
        "delete": cmd_delete,
    }
    dispatch[args.cmd](args)

if __name__ == "__main__":
    main()

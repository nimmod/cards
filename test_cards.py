#!/usr/bin/env python3
"""Pytest suite for cards.py
Run: pytest -q test_cards.py
"""
import importlib
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_cards(tmp_home: Path):
    """Import fresh cards.py with HOME set to tmp_home."""
    os.environ["HOME"] = str(tmp_home)
    sys.modules.pop("cards", None)
    return importlib.import_module("cards")


@pytest.fixture()
def cards(tmp_path):
    return load_cards(tmp_path)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_id_generation_requires_commit(cards):
    # First ID without file
    cid1 = cards.generate_id()
    # Save card so next call increments
    cards.write_card({
        "ID": cid1, "Date": "2025-07-01", "Type": "idea", "Title": "T",
        "Summary": "", "Tags": [], "Links": [], "SequenceNext": "",
        "Context": "", "Next": "", "Body": "b"})

    cid2 = cards.generate_id()
    assert cid2 == "2"

    child = cards.generate_id(cid1)
    assert child == f"{cid1}.1"


def test_register_show_roundtrip(cards, capsys):
    cid = cards.generate_id()
    args = type("A", (), {
        "id": cid, "parent": None, "type": "idea", "title": "T",
        "summary": "S", "tags": ["x"], "links": [], "sequence": "",
        "context": "C", "next": "N", "body": "B"
    })()
    cards.cmd_register(args)

    show = type("S", (), {"id": cid})()
    cards.cmd_show(show)
    out, _ = capsys.readouterr()
    assert "T" in out and "B" in out


def test_update(cards):
    cid = cards.generate_id()
    cards.write_card({
        "ID": cid, "Date": "2025-07-01", "Type": "idea", "Title": "old",
        "Summary": "", "Tags": [], "Links": [], "SequenceNext": "",
        "Context": "", "Next": "", "Body": "b"})

    upd = type("U", (), {
        "id": cid, "title": "new", "summary": None, "body": None,
        "context": None, "next": None, "type": None, "sequence": None,
        "force": False, "add_tag": ["z"], "remove_tag": None,
        "add_link": None, "remove_link": None})()
    cards.cmd_update(upd)
    d = cards.read_card(cid)
    assert d["Title"] == "new" and "z" in d["Tags"]


def test_link_backlinks(cards, capsys):
    a = cards.generate_id()
    cards.write_card({
        "ID": a, "Date": "2025-07-01", "Type": "idea", "Title": "A",
        "Summary": "", "Tags": [], "Links": [], "SequenceNext": "",
        "Context": "", "Next": "", "Body": "b"})
    b = cards.generate_id()
    cards.write_card({
        "ID": b, "Date": "2025-07-01", "Type": "idea", "Title": "B",
        "Summary": "", "Tags": [], "Links": [], "SequenceNext": "",
        "Context": "", "Next": "", "Body": "b"})
    cards.cmd_link(type("L", (), {"source": a, "target": b})())
    assert b in cards.read_card(a)["Links"]

    cards.cmd_backlinks(type("BL", (), {"id": b})())
    out, _ = capsys.readouterr()
    assert a in out



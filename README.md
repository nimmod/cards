# cards.py — User Documentation

---

## Core Concepts

* **Atomic cards**
  Each card records a single idea, reference, or argument; all fields are explicit.

* **ID system**
  Every card receives a unique, concise ID, allowing for flat and hierarchical children (e.g. `7`, `7.2`, `7.2.1`).

* **Types**
  Two only — `idea` (original thought, question, synthesis) and `literature` (summary of external source).

* **Links**
  Cards may link to each other; links are explicit and bidirectional for references, or directional in the case of derivation (`SequenceNext`).

* **Tags**
  Flexible, user‑defined labels for rapid search, retrieval, and thematic grouping.

* **Summary vs. Body**
  *Summary* is a one‑sentence condensation; *Body* is the fully developed statement or note.

* **Process discipline**
  Requires daily and weekly reviews, capture‑to‑integration flow, and explicit closure of cognitive loops.

* **File‑based storage**
  All data lives as plain‑text YAML files in a single folder, easily auditable and portable.

* **No legacy IDs**
  All cards are created and referenced only through the script; ID allocation is automatic.

---

## Installation

Place `cards.py` in a directory on your `$PATH` (e.g. `~/bin`).

Requires Python 3 and PyYAML:

```bash
pip install pyyaml
```

---

## File Structure

* Cards: `~/cards/<ID>.yaml`
* Index: `~/cards/index.yaml` (ID → Title)
* Backups: `~/cards/backups/`
* Guide: `guide.txt` (edit to change the workflow guide)

---

## Data Schema

| Field            | Purpose                                       |
| ---------------- | --------------------------------------------- |
| **ID**           | Unique integer or dotted child (e.g. `3.2.1`) |
| **Date**         | Creation date (YYYY‑MM‑DD)                    |
| **Type**         | `idea` or `literature`                        |
| **Title**        | Concise label (**required**)                  |
| **Summary**      | One‑sentence condensation (optional)          |
| **Tags**         | List of keywords                              |
| **Links**        | List of related card IDs (bidirectional)      |
| **SequenceNext** | ID of direct derivative card (unidirectional) |
| **Context**      | Trigger / source                              |
| **Next**         | Concrete next action                          |
| **Body**         | Full note text (**required**)                 |

---

## Basic Workflow

### Register a new card

```bash
cards.py register -y idea \
                  -t "My First Idea" \
                  -b "A full card body here" \
                  -g inspiration reflection
```

*Omit the ID to auto‑generate.*
Use `--parent <ID>` to create a hierarchical child.

### Update a card

```bash
cards.py update 3 \
            --title "Revised title" \
            --add-tag deepWork \
            --sequence 2.1 --force
```

### Inspect cards

```bash
cards.py list           # list all cards
cards.py show 3         # show one card
cards.py find -g insight research   # IDs with both tags
```

### Relate cards

```bash
cards.py link 3 5           # bidirectional link
cards.py sequence 3 4.1     # derivation chain
cards.py backlinks 5        # who links to 5
```

### Utilities

```bash
cards.py guide   # print workflow guide
cards.py index   # print path to index.yaml
```

---

## Linking and Sequencing

**Links (bidirectional)**
Created with `cards.py link A B`. Both cards list each other in `Links`.
Use for thematic, evidential, or associative connections.

**SequenceNext (unidirectional)**
Created with `cards.py sequence SOURCE TARGET`. The `SOURCE` card’s `SequenceNext` field points to `TARGET`.
Use for logical derivations, argument chains, or chronological steps.

---

## Backlinks

Discover incoming links:

```bash
cards.py backlinks <ID>
```

Outputs all card IDs whose `Links` list contains `<ID>`.

---

## Backup & Restore

* Every write makes a timestamped backup in `~/cards/backups/`.
* The 50 most recent backups per card are retained.
* To restore, copy a backup over the current YAML.

---

## Bash Tab Completion

Add to `~/.bashrc` or `~/.zshrc`:

```bash
_cards_ids() {
  local cur=${COMP_WORDS[COMP_CWORD]}
  if [[ -f "${HOME}/cards/index.yaml" ]]; then
    local ids
    ids=$(grep -E '^[0-9]' "${HOME}/cards/index.yaml" | cut -d':' -f1)
    COMPREPLY=( $(compgen -W "${ids}" -- "$cur") )
  fi
}
complete -F _cards_ids cards.py
```

---

## Safety & Validation

* IDs are generated only by the script.
* Manual YAML edits bypass validation—use CLI commands when possible.

---

## Extending

* Edit `guide.txt` to refine the process guide.
* Run tests with:

```bash
pytest -q test_cards.py
```

---

For the complete daily/weekly workflow, run:

```bash
cards.py guide
```

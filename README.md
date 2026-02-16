# zotero-skill

Utilities and skill definitions for read-only querying of a local Zotero client database (`zotero.sqlite`).

This repository currently includes:
- A Codex skill: `zotero-client-sqlite/SKILL.md`
- A Python CLI tool: `zotero-client-sqlite/scripts/zotero_sqlite_tool.py`
- Arch packaging files: `packaging/arch/`

## What It Does

The CLI provides collection-scoped search and PDF annotation position extraction from Zotero's local SQLite database, with a read-only connection mode.

## Requirements

- Python 3
- A local Zotero database (`zotero.sqlite`)

## Usage

Run from this repository root:

```bash
python3 zotero-client-sqlite/scripts/zotero_sqlite_tool.py locate-db
```

List collections:

```bash
python3 zotero-client-sqlite/scripts/zotero_sqlite_tool.py list-collections --collection "machine learning"
```

Search items in a collection:

```bash
python3 zotero-client-sqlite/scripts/zotero_sqlite_tool.py search-items \
  --collection "AB12CD34" \
  --include-subcollections \
  --query "retrieval augmented generation survey"
```

Get PDF annotation positions for an item:

```bash
python3 zotero-client-sqlite/scripts/zotero_sqlite_tool.py pdf-positions --item-key "QWERTY12"
```

### Environment Variables

- `ZOTERO_DB_PATH`: absolute path to `zotero.sqlite`
- `ZOTERO_DATA_DIR`: Zotero data directory (tool will look for `zotero.sqlite` inside it)

## Install as Command

You can install the script as `zotero-sqlite-tool` with the Arch package recipe in `packaging/arch/PKGBUILD`, or place/copy the script on your `PATH` and make it executable.

## Safety

This tool is intended for **read-only** access. It uses SQLite read-only mode and rejects non-`SELECT`/`WITH` statements.

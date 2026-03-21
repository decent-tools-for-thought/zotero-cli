# zotero-skill

Utilities and skill definitions for read-only querying of a local Zotero client database (`zotero.sqlite`).

This repository currently includes:
- A Codex skill: `zotero-client-sqlite/SKILL.md`
- A Python CLI tool: `zotero-client-sqlite/scripts/zotero_sqlite_tool.py`

## What It Does

The CLI provides collection-scoped search and PDF annotation position extraction from Zotero's local SQLite database, with a read-only connection mode.

## Requirements

- Python 3
- A local Zotero database (`zotero.sqlite`)

## Setup

```bash
uv sync
uv run zotero-sqlite-tool --help
```

## Usage

Run from this repository root:

```bash
uv run zotero-sqlite-tool locate-db
```

List collections:

```bash
uv run zotero-sqlite-tool list-collections --collection "machine learning"
```

Search items in a collection:

```bash
uv run zotero-sqlite-tool search-items \
  --collection "AB12CD34" \
  --include-subcollections \
  --query "retrieval augmented generation survey"
```

Get PDF annotation positions for an item:

```bash
uv run zotero-sqlite-tool pdf-positions --item-key "QWERTY12"
```

### Environment Variables

- `ZOTERO_DB_PATH`: absolute path to `zotero.sqlite`
- `ZOTERO_DATA_DIR`: Zotero data directory (tool will look for `zotero.sqlite` inside it)
- `zotero-client-sqlite/scripts/zotero_sqlite_tool.py ...` still works directly if you need the original path.

## Releases

Tagging `v<version>` publishes a source archive built from the tagged commit:

- `zotero-cli-<version>.tar.gz`
- `SHA256SUMS`

## Safety

This tool is intended for **read-only** access. It uses SQLite read-only mode and rejects non-`SELECT`/`WITH` statements.

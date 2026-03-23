<div align="center">

# zotero-cli

[![Release](https://img.shields.io/github/v/release/decent-tools-for-thought/zotero-cli?sort=semver&color=0f766e)](https://github.com/decent-tools-for-thought/zotero-cli/releases)
![Python](https://img.shields.io/badge/python-3.11%2B-0ea5e9)
![License](https://img.shields.io/badge/license-0BSD-14b8a6)

Read-only command-line client for locating, browsing, and querying a local Zotero SQLite database and its PDF annotations.

</div>

> [!IMPORTANT]
> This codebase is entirely AI-generated. It is useful to me, I hope it might be useful to others, and issues and contributions are welcome.

## Map
- [Install](#install)
- [Functionality](#functionality)
- [Database Resolution](#database-resolution)
- [Quick Start](#quick-start)
- [Development](#development)
- [Credits](#credits)

## Install

From a checkout:

```bash
uv sync
uv run zotero-sqlite-tool --help
```

From a built wheel:

```bash
python -m pip install dist/*.whl
zotero-sqlite-tool --help
```

## Functionality

### Database Discovery
- `zotero-sqlite-tool locate-db`: detect candidate `zotero.sqlite` paths and show the selected default path.
- All commands support `--db-path` to override database resolution.
- All commands support `--library-id` to scope operations to one Zotero library.
- All commands support `--text` for compact text output instead of JSON.

### Collection Browsing
- `zotero-sqlite-tool list-collections`: list collection keys, names, paths, and library IDs.
- `zotero-sqlite-tool list-collections --collection <selector>`: filter collections by key, name, or path fragment.

### Item Search
- `zotero-sqlite-tool search-items --query <text>`: search titles, metadata, creators, tags, notes, and annotations.
- `zotero-sqlite-tool search-items --collection <selector>`: scope search to one collection.
- `zotero-sqlite-tool search-items --include-subcollections`: include descendant collections when collection-scoped.
- `zotero-sqlite-tool search-items --any-term`: switch from all-terms matching to any-term matching.
- Search results are ranked and include matched fields and score metadata.

### PDF Annotation Positions
- `zotero-sqlite-tool pdf-positions`: extract PDF annotation positions and related metadata.
- `zotero-sqlite-tool pdf-positions --item-id <id>`: target one parent item by item ID.
- `zotero-sqlite-tool pdf-positions --item-key <key>`: target one parent item by Zotero item key.
- `zotero-sqlite-tool pdf-positions --query <text>`: either resolve parent items by search query or filter annotations by text/comment content, depending on the selector mode.
- `zotero-sqlite-tool pdf-positions --collection <selector>` and `--include-subcollections`: scope annotation extraction to collection trees.

### Safety
- The client opens the database read-only.
- The client enables SQLite `query_only`.
- The client only permits `SELECT` and `WITH` queries internally.

## Database Resolution

The CLI resolves `zotero.sqlite` in this order:

1. `--db-path`
2. `ZOTERO_DB_PATH`
3. `ZOTERO_DATA_DIR/zotero.sqlite`
4. `~/Zotero/zotero.sqlite`
5. `~/.zotero/zotero/*.default*/zotero.sqlite`
6. `~/.var/app/org.zotero.Zotero/data/Zotero/zotero.sqlite`

## Quick Start

```bash
uv run zotero-sqlite-tool locate-db

uv run zotero-sqlite-tool list-collections --collection "machine learning"

uv run zotero-sqlite-tool search-items \
  --collection "AB12CD34" \
  --include-subcollections \
  --query "retrieval augmented generation"

uv run zotero-sqlite-tool pdf-positions --item-key "QWERTY12"
```

## Development

```bash
uv run ruff format src tests zotero-client-sqlite/scripts
uv run ruff check src tests zotero-client-sqlite/scripts
uv run mypy
uv run pytest
```

Arch packaging notes live in [AUR_VALIDATION.md](AUR_VALIDATION.md).

## Credits

This tool is built for the local Zotero client database and is not affiliated with Zotero.

Credit goes to the Zotero project for the application, schema, and data model this CLI builds on.

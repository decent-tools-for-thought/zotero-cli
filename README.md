# zotero-cli

[![Release](https://img.shields.io/github/v/release/decent-tools-for-thought/zotero-cli?sort=semver)](https://github.com/decent-tools-for-thought/zotero-cli/releases)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-0BSD-green)

Read-only command-line tools for querying a local Zotero database.

> [!IMPORTANT]
> This codebase is largely AI-generated. It is useful to me, I hope it might be useful to others, and issues and contributions are welcome.

## Why This Exists

- Search a local `zotero.sqlite` without poking around manually.
- List collections, search items, and extract PDF annotation positions.
- Keep access read-only by default.

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

## Quick Start

Locate the database:

```bash
uv run zotero-sqlite-tool locate-db
```

List collections:

```bash
uv run zotero-sqlite-tool list-collections --collection "machine learning"
```

Search inside a collection:

```bash
uv run zotero-sqlite-tool search-items \
  --collection "AB12CD34" \
  --include-subcollections \
  --query "retrieval augmented generation"
```

Extract PDF annotation positions:

```bash
uv run zotero-sqlite-tool pdf-positions --item-key "QWERTY12"
```

## Database Resolution

The CLI resolves `zotero.sqlite` in this order:

1. `--db-path`
2. `ZOTERO_DB_PATH`
3. `ZOTERO_DATA_DIR/zotero.sqlite`
4. `~/Zotero/zotero.sqlite`
5. `~/.zotero/zotero/*.default*/zotero.sqlite`
6. `~/.var/app/org.zotero.Zotero/data/Zotero/zotero.sqlite`

## Development

```bash
uv run ruff format src tests zotero-client-sqlite/scripts
uv run ruff check src tests zotero-client-sqlite/scripts
uv run mypy
uv run pytest
```

Arch packaging notes live in [AUR_VALIDATION.md](AUR_VALIDATION.md).

## Credits

This tool is built for the local Zotero client database and is not affiliated with Zotero. Credit goes to the Zotero project for the application and data model this CLI builds on.

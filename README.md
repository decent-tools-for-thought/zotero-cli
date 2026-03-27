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
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Credits](#credits)

## Install
$$\color{#0EA5E9}Install \space \color{#14B8A6}Tool$$

From a checkout:

```bash
uv sync                            # install project dependencies
uv run zotero-sqlite-tool --help   # inspect the CLI
```

From a built wheel:

```bash
python -m pip install dist/*.whl   # install from a built wheel
zotero-sqlite-tool --help          # inspect the installed entry point
```

## Functionality
$$\color{#0EA5E9}Database \space \color{#14B8A6}Discovery$$
- `zotero-sqlite-tool locate-db`: detect candidate `zotero.sqlite` paths and show the selected default path.
- All commands support `--db-path` to override database resolution.
- All commands support `--library-id` to scope operations to one Zotero library.
- All commands support `--text` for compact text output instead of JSON.

$$\color{#0EA5E9}Collection \space \color{#14B8A6}Browse$$
- `zotero-sqlite-tool list-collections`: list collection keys, names, paths, and library IDs.
- `zotero-sqlite-tool list-collections --collection <selector>`: filter collections by key, name, or path fragment.

$$\color{#0EA5E9}Item \space \color{#14B8A6}Search$$
- `zotero-sqlite-tool search-items --query <text>`: search titles, metadata, creators, tags, notes, and annotations.
- `zotero-sqlite-tool search-items --collection <selector>`: scope search to one collection.
- `zotero-sqlite-tool search-items --include-subcollections`: include descendant collections when collection-scoped.
- `zotero-sqlite-tool search-items --any-term`: switch from all-terms matching to any-term matching.
- Search results are ranked and include matched fields and score metadata.

$$\color{#0EA5E9}PDF \space \color{#14B8A6}Annotations$$
- `zotero-sqlite-tool pdf-positions`: extract PDF annotation positions and related metadata.
- `zotero-sqlite-tool pdf-positions --item-id <id>`: target one parent item by item ID.
- `zotero-sqlite-tool pdf-positions --item-key <key>`: target one parent item by Zotero item key.
- `zotero-sqlite-tool pdf-positions --query <text>`: either resolve parent items by search query or filter annotations by text/comment content, depending on the selector mode.
- `zotero-sqlite-tool pdf-positions --collection <selector>` and `--include-subcollections`: scope annotation extraction to collection trees.

$$\color{#0EA5E9}Read \space \color{#14B8A6}Safety$$
- The client opens the database read-only.
- The client enables SQLite `query_only`.
- The client only permits `SELECT` and `WITH` queries internally.

## Configuration
$$\color{#0EA5E9}Lookup \space \color{#14B8A6}Order$$

The CLI resolves `zotero.sqlite` in this order:

1. `--db-path`
2. `ZOTERO_DB_PATH`
3. `ZOTERO_DATA_DIR/zotero.sqlite`
4. `~/Zotero/zotero.sqlite`
5. `~/.zotero/zotero/*.default*/zotero.sqlite`
6. `~/.var/app/org.zotero.Zotero/data/Zotero/zotero.sqlite`

## Quick Start
$$\color{#0EA5E9}Try \space \color{#14B8A6}Search$$

```bash
uv run zotero-sqlite-tool locate-db    # find candidate Zotero databases

uv run zotero-sqlite-tool list-collections --collection "machine learning"    # filter collection names and paths

uv run zotero-sqlite-tool search-items \    # search item metadata inside one collection tree
  --collection "AB12CD34" \
  --include-subcollections \
  --query "retrieval augmented generation"

uv run zotero-sqlite-tool pdf-positions --item-key "QWERTY12"    # extract PDF annotation positions
```

Arch packaging notes live in [AUR_VALIDATION.md](AUR_VALIDATION.md).

## Credits

This tool is built for the local Zotero client database and is not affiliated with Zotero.

Credit goes to the Zotero project for the application, schema, and data model this CLI builds on.

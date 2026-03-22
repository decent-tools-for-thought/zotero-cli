# zotero-cli

Read-only tools for querying a local Zotero client database (`zotero.sqlite`).

This repository currently includes:
- A Codex skill: `zotero-client-sqlite/SKILL.md`
- A Python CLI package with the `zotero-sqlite-tool` entry point

## What It Does

The CLI provides collection-scoped search and PDF annotation position extraction from Zotero's local SQLite database, with a read-only connection mode.

## Requirements

- Python 3.11+
- A local Zotero database (`zotero.sqlite`)

## Install

For local development:

```bash
uv sync
uv run zotero-sqlite-tool --help
```

For an isolated smoke install from a built artifact:

```bash
python -m build
python -m venv .venv-smoke
.venv-smoke/bin/python -m pip install --no-deps dist/*.whl
.venv-smoke/bin/python -c "import zotero_sqlite_tool"
.venv-smoke/bin/zotero-sqlite-tool --help
```

## Database Detection

The CLI resolves `zotero.sqlite` in this order:

1. `--db-path`
2. `ZOTERO_DB_PATH`
3. `ZOTERO_DATA_DIR/zotero.sqlite`
4. `~/Zotero/zotero.sqlite`
5. `~/.zotero/zotero/*.default*/zotero.sqlite`
6. `~/.var/app/org.zotero.Zotero/data/Zotero/zotero.sqlite`

To inspect what the tool can currently detect:

```bash
uv run zotero-sqlite-tool locate-db
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

## Quality Checks

The fast local verification loop is:

```bash
uv run ruff format src tests zotero-client-sqlite/scripts
uv run ruff check src tests zotero-client-sqlite/scripts
uv run mypy
uv run pytest
```

Fixture databases for tests live under `tests/fixtures/` and can be regenerated with:

```bash
python tests/fixtures/build_fixtures.py
```

## Releases

Tagging `v<version>` publishes Python distribution artifacts built from the tagged commit:

- `zotero_cli-<version>.tar.gz`
- `zotero_cli-<version>-py3-none-any.whl`
- `SHA256SUMS`

## Safety

This tool is intended for **read-only** access. It uses SQLite read-only mode and rejects non-`SELECT`/`WITH` statements.

## Packaging Discipline

Release CI verifies wheel and sdist installs, confirms the library imports, and checks the installed CLI entry point.

For the Arch package validation routine, use [AUR_VALIDATION.md](AUR_VALIDATION.md).

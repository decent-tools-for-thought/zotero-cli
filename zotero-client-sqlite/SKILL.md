---
name: zotero-client-sqlite
description: Read-only querying of Zotero Client's local SQLite database (`zotero.sqlite`) for collection-scoped discovery and extraction. Use when Codex must search Zotero library items by collection (optionally including subcollections) with lenient matching across metadata, tags, child notes, annotation text, and annotation comments, or when Codex must retrieve PDF annotation positions/page labels for matching items.
---

# Zotero Client SQLite

Use `scripts/zotero_sqlite_tool.py` as the only interface to the Zotero client DB.

## Quick Start

1. Locate the DB:
```bash
python3 scripts/zotero_sqlite_tool.py locate-db
```

2. Inspect collection selectors (key, name, or full path):
```bash
python3 scripts/zotero_sqlite_tool.py list-collections --collection "machine learning"
```

3. Search items in a collection (including metadata, tags, child notes, annotation text/comments):
```bash
python3 scripts/zotero_sqlite_tool.py search-items \
  --collection "AB12CD34" \
  --include-subcollections \
  --query "retrieval augmented generation survey"
```

4. Retrieve PDF annotation positions for an item:
```bash
python3 scripts/zotero_sqlite_tool.py pdf-positions --item-key "QWERTY12"
```

5. Retrieve PDF positions only for annotations matching a query in a collection scope:
```bash
python3 scripts/zotero_sqlite_tool.py pdf-positions \
  --collection "AB12CD34" \
  --include-subcollections \
  --query "hallucination"
```

## Command Reference

- `locate-db`
  - Detect `zotero.sqlite` candidates from default paths and env vars.

- `list-collections`
  - Show collection keys and canonical paths for selector disambiguation.
  - Use `--collection` to filter.

- `search-items`
  - Required: `--query`.
  - Optional scope: `--collection`, `--include-subcollections`, `--library-id`.
  - Matching defaults to all terms; use `--any-term` for broader matches.

- `pdf-positions`
  - Target a single item with `--item-id` or `--item-key`, or provide scope/query.
  - `--query` behavior:
    - With `--item-id/--item-key`: filter returned annotations.
    - Without item target: perform search-first item selection in scope.

## Output Contract

- Default output is JSON.
- Add `--text` for line-oriented compact output.
- `pdf-positions` returns parsed `position` JSON when valid; otherwise raw string.

## Guardrails

- Keep this workflow read-only; do not run write SQL.
- Prefer collection key selectors when ambiguity exists.
- Assume Zotero schema may change; if a table is missing, inspect with:
```bash
python3 scripts/zotero_sqlite_tool.py --text list-collections
```

## Troubleshooting

- DB not found:
  - Pass `--db-path /path/to/zotero.sqlite`, or set `ZOTERO_DB_PATH`/`ZOTERO_DATA_DIR`.

- Ambiguous collection selector:
  - Use `list-collections` and switch to exact collection key.

- No PDF positions returned:
  - Confirm item has a PDF attachment and annotations with stored positions.

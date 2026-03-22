from __future__ import annotations

import io
import sqlite3
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from zotero_sqlite_tool.core import (
    ZoteroSQLite,
    detect_db_candidates,
    list_collections,
    parse_position,
    pdf_positions,
    print_output,
    resolve_collection,
    resolve_db_path,
    search_items,
    to_serializable,
)


def test_detect_db_candidates_prefers_existing_env_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_db = tmp_path / "env.sqlite"
    env_db.touch()
    env_dir = tmp_path / "data-dir"
    env_dir.mkdir()
    env_dir_db = env_dir / "zotero.sqlite"
    env_dir_db.touch()

    monkeypatch.setenv("ZOTERO_DB_PATH", str(env_db))
    monkeypatch.setenv("ZOTERO_DATA_DIR", str(env_dir))
    monkeypatch.setattr(
        "zotero_sqlite_tool.core.glob.glob", lambda pattern: [str(env_db), str(env_dir_db)]
    )

    assert detect_db_candidates() == [str(env_db.resolve()), str(env_dir_db.resolve())]


def test_resolve_db_path_raises_when_no_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ZOTERO_DB_PATH", raising=False)
    monkeypatch.delenv("ZOTERO_DATA_DIR", raising=False)
    monkeypatch.setattr("zotero_sqlite_tool.core.glob.glob", lambda pattern: [])

    with pytest.raises(FileNotFoundError, match="Could not find zotero.sqlite"):
        resolve_db_path(None)


def test_connect_read_only_rejects_writes(temp_db_copy: Path) -> None:
    db = ZoteroSQLite(str(temp_db_copy))
    try:
        with pytest.raises(sqlite3.OperationalError):
            db.conn.execute("CREATE TABLE forbidden (id INTEGER)")
    finally:
        db.close()


def test_fetchall_rejects_non_select_statements(fixture_db_path: Path) -> None:
    db = ZoteroSQLite(str(fixture_db_path))
    try:
        with pytest.raises(ValueError, match="Only SELECT/WITH statements"):
            db.fetchall("DELETE FROM items")
    finally:
        db.close()


def test_resolve_collection_reports_ambiguity(fixture_db_path: Path) -> None:
    db = ZoteroSQLite(str(fixture_db_path))
    try:
        with pytest.raises(ValueError, match="ambiguous"):
            resolve_collection(db, "Shared Name", library_id=None)
    finally:
        db.close()


def test_search_items_handles_selector_resolution_and_serialization(
    fixture_db_path: Path,
) -> None:
    db = ZoteroSQLite(str(fixture_db_path))
    try:
        data = search_items(
            db=db,
            query="retrieval survey",
            collection_selector="Machine Learning / Retrieval",
            include_subcollections=False,
            library_id=1,
            any_term=False,
            limit=10,
        )
    finally:
        db.close()

    assert data["resultCount"] == 1
    result = data["results"][0]
    assert result["key"] == "PARENT001"
    assert result["matchedFields"]["title"] == ["retrieval", "survey"]
    assert result["matchedFields"]["annotations"] == ["retrieval", "survey"]


def test_pdf_positions_parses_json_and_raw_positions(fixture_db_path: Path) -> None:
    db = ZoteroSQLite(str(fixture_db_path))
    try:
        data = pdf_positions(db, parent_item_ids=[1], annotation_query=None, any_term=False)
    finally:
        db.close()

    assert data["resultCount"] == 2
    assert data["results"][0]["position"] == {"pageIndex": 0, "rects": [[1, 2, 3, 4]]}
    assert data["results"][1]["position"] == "page=2"


def test_pdf_positions_handles_missing_date_modified_column(schema_variant_db_path: Path) -> None:
    db = ZoteroSQLite(str(schema_variant_db_path))
    try:
        data = pdf_positions(db, parent_item_ids=[1], annotation_query="highlight", any_term=False)
    finally:
        db.close()

    assert data["resultCount"] == 1
    assert data["results"][0]["dateModified"] is None


def test_list_collections_returns_empty_when_table_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "missing-collections.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE items ("
            "itemID INTEGER PRIMARY KEY, "
            "key TEXT, "
            "libraryID INTEGER, "
            "itemTypeID INTEGER"
            ")"
        )

    db = ZoteroSQLite(str(db_path))
    try:
        data = list_collections(db, selector=None, library_id=None, limit=10)
    finally:
        db.close()

    assert data == {"resultCount": 0, "results": []}


def test_search_items_survives_missing_metadata_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "minimal.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE items (
                itemID INTEGER PRIMARY KEY,
                key TEXT,
                libraryID INTEGER,
                itemTypeID INTEGER,
                dateAdded TEXT,
                dateModified TEXT
            );
            INSERT INTO items VALUES (1, 'ITEM0001', 1, 1, '2024-01-01', '2024-01-02');
            """
        )

    db = ZoteroSQLite(str(db_path))
    try:
        data = search_items(
            db=db,
            query="",
            collection_selector=None,
            include_subcollections=False,
            library_id=None,
            any_term=False,
            limit=10,
        )
    finally:
        db.close()

    assert data["resultCount"] == 1
    assert data["results"][0]["title"] == ""


def test_parse_position_and_to_serializable_cover_output_helpers() -> None:
    assert parse_position('{"pageIndex": 1}') == {"pageIndex": 1}
    assert parse_position("not json") == "not json"

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT 1 AS value").fetchone()
    assert row is not None
    assert to_serializable([row]) == [{"value": 1}]


def test_print_output_text_mode_emits_compact_lines() -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_output({"resultCount": 1, "results": [{"key": "ITEM0001"}]}, as_json=False)

    assert buffer.getvalue().splitlines() == ["resultCount: 1", '{"key": "ITEM0001"}']

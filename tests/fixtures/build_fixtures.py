from __future__ import annotations

import sqlite3
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent
MAIN_DB = FIXTURE_DIR / "zotero-fixture.sqlite"
SCHEMA_VARIANT_DB = FIXTURE_DIR / "zotero-fixture-schema-variant.sqlite"


MAIN_SCHEMA = """
PRAGMA foreign_keys = OFF;

CREATE TABLE collections (
    collectionID INTEGER PRIMARY KEY,
    collectionName TEXT NOT NULL,
    parentCollectionID INTEGER,
    libraryID INTEGER NOT NULL,
    key TEXT NOT NULL
);

CREATE TABLE collectionItems (
    collectionID INTEGER NOT NULL,
    itemID INTEGER NOT NULL
);

CREATE TABLE itemTypes (
    itemTypeID INTEGER PRIMARY KEY,
    typeName TEXT NOT NULL
);

CREATE TABLE items (
    itemID INTEGER PRIMARY KEY,
    key TEXT NOT NULL,
    libraryID INTEGER NOT NULL,
    itemTypeID INTEGER NOT NULL,
    dateAdded TEXT,
    dateModified TEXT
);

CREATE TABLE itemData (
    itemID INTEGER NOT NULL,
    fieldID INTEGER NOT NULL,
    valueID INTEGER NOT NULL
);

CREATE TABLE itemDataValues (
    valueID INTEGER PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE fieldsCombined (
    fieldID INTEGER PRIMARY KEY,
    fieldName TEXT NOT NULL
);

CREATE TABLE itemCreators (
    itemID INTEGER NOT NULL,
    creatorID INTEGER NOT NULL
);

CREATE TABLE creators (
    creatorID INTEGER PRIMARY KEY,
    firstName TEXT,
    lastName TEXT
);

CREATE TABLE itemTags (
    itemID INTEGER NOT NULL,
    tagID INTEGER NOT NULL
);

CREATE TABLE tags (
    tagID INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE itemNotes (
    itemID INTEGER PRIMARY KEY,
    parentItemID INTEGER NOT NULL,
    note TEXT NOT NULL
);

CREATE TABLE itemAttachments (
    itemID INTEGER PRIMARY KEY,
    parentItemID INTEGER NOT NULL,
    path TEXT,
    contentType TEXT
);

CREATE TABLE itemAnnotations (
    itemID INTEGER PRIMARY KEY,
    parentItemID INTEGER NOT NULL,
    type TEXT,
    text TEXT,
    comment TEXT,
    color TEXT,
    pageLabel TEXT,
    sortIndex TEXT,
    position TEXT,
    dateModified TEXT
);
"""


MAIN_DATA = """
INSERT INTO collections VALUES
    (1, 'Machine Learning', NULL, 1, 'MLROOT01'),
    (2, 'Retrieval', 1, 1, 'RETRIEV1'),
    (3, 'Shared Name', NULL, 1, 'SHARED01'),
    (4, 'Shared Name', NULL, 2, 'SHARED02');

INSERT INTO itemTypes VALUES
    (1, 'journalArticle'),
    (2, 'attachment'),
    (3, 'annotation');

INSERT INTO items VALUES
    (1, 'PARENT001', 1, 1, '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z'),
    (2, 'ATTACH001', 1, 2, '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z'),
    (3, 'ANNOTE01', 1, 3, '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z'),
    (4, 'ANNOTE02', 1, 3, '2024-01-01T00:00:00Z', '2024-01-03T00:00:00Z'),
    (5, 'OTHER001', 2, 1, '2024-01-04T00:00:00Z', '2024-01-05T00:00:00Z');

INSERT INTO collectionItems VALUES
    (2, 1),
    (4, 5);

INSERT INTO fieldsCombined VALUES
    (1, 'title'),
    (2, 'abstractNote');

INSERT INTO itemDataValues VALUES
    (1, 'Retrieval Augmented Generation Survey'),
    (2, 'Dense retrieval study'),
    (3, 'Cross-library note');

INSERT INTO itemData VALUES
    (1, 1, 1),
    (1, 2, 2),
    (5, 1, 3);

INSERT INTO creators VALUES
    (1, 'Ada', 'Lovelace');

INSERT INTO itemCreators VALUES
    (1, 1);

INSERT INTO tags VALUES
    (1, 'retrieval'),
    (2, 'survey');

INSERT INTO itemTags VALUES
    (1, 1),
    (1, 2);

INSERT INTO itemNotes VALUES
    (10, 1, '<p>Survey note about retrieval</p>');

INSERT INTO itemAttachments VALUES
    (2, 1, 'storage:paper.pdf', 'application/pdf');

INSERT INTO itemAnnotations VALUES
    (
        3,
        2,
        'highlight',
        'Retrieval highlighted passage',
        'Useful survey context',
        '#ffff00',
        '1',
        '00001',
        '{"pageIndex": 0, "rects": [[1, 2, 3, 4]]}',
        '2024-01-02T00:00:00Z'
    ),
    (
        4,
        2,
        'note',
        'Second note',
        'Page string fallback',
        '#00ff00',
        '2',
        '00002',
        'page=2',
        '2024-01-03T00:00:00Z'
    );
"""


SCHEMA_VARIANT_SCHEMA = """
PRAGMA foreign_keys = OFF;

CREATE TABLE itemTypes (
    itemTypeID INTEGER PRIMARY KEY,
    typeName TEXT NOT NULL
);

CREATE TABLE items (
    itemID INTEGER PRIMARY KEY,
    key TEXT NOT NULL,
    libraryID INTEGER NOT NULL,
    itemTypeID INTEGER NOT NULL,
    dateAdded TEXT,
    dateModified TEXT
);

CREATE TABLE itemAttachments (
    itemID INTEGER PRIMARY KEY,
    parentItemID INTEGER NOT NULL,
    path TEXT,
    contentType TEXT
);

CREATE TABLE itemAnnotations (
    itemID INTEGER PRIMARY KEY,
    parentItemID INTEGER NOT NULL,
    type TEXT,
    text TEXT,
    comment TEXT,
    color TEXT,
    pageLabel TEXT,
    sortIndex TEXT,
    position TEXT
);
"""


SCHEMA_VARIANT_DATA = """
INSERT INTO itemTypes VALUES
    (1, 'journalArticle'),
    (2, 'attachment');

INSERT INTO items VALUES
    (1, 'PARENT001', 1, 1, '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z'),
    (2, 'ATTACH001', 1, 2, '2024-01-01T00:00:00Z', '2024-01-02T00:00:00Z');

INSERT INTO itemAttachments VALUES
    (2, 1, 'storage:paper.pdf', 'application/pdf');

INSERT INTO itemAnnotations VALUES
    (3, 2, 'highlight', 'Highlight only', NULL, '#ffff00', '1', '00001', '{"pageIndex": 0}');
"""


def build_database(path: Path, schema: str, data: str) -> None:
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as conn:
        conn.executescript(schema)
        conn.executescript(data)
        conn.commit()


def main() -> None:
    build_database(MAIN_DB, MAIN_SCHEMA, MAIN_DATA)
    build_database(SCHEMA_VARIANT_DB, SCHEMA_VARIANT_SCHEMA, SCHEMA_VARIANT_DATA)


if __name__ == "__main__":
    main()

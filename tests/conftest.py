from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def fixture_db_path() -> Path:
    return FIXTURE_DIR / "zotero-fixture.sqlite"


@pytest.fixture()
def schema_variant_db_path() -> Path:
    return FIXTURE_DIR / "zotero-fixture-schema-variant.sqlite"


@pytest.fixture()
def temp_db_copy(tmp_path: Path, fixture_db_path: Path) -> Iterator[Path]:
    destination = tmp_path / "copy.sqlite"
    with sqlite3.connect(fixture_db_path) as source, sqlite3.connect(destination) as target:
        source.backup(target)
    yield destination

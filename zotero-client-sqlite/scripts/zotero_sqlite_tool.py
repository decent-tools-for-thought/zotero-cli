#!/usr/bin/env python3
"""Read-only CLI for querying Zotero's client SQLite database."""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sqlite3
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

KEY_PATTERN = re.compile(r"^[A-Z0-9]{8}$")
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")
NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = HTML_TAG_PATTERN.sub(" ", text)
    text = WHITESPACE_PATTERN.sub(" ", text)
    return text.strip().lower()


def split_terms(query: str) -> List[str]:
    terms = [t.strip().lower() for t in re.split(r"\s+", query or "") if t.strip()]
    return list(dict.fromkeys(terms))


def canonicalize(value: str) -> str:
    return NON_ALNUM_PATTERN.sub("", value.lower())


def term_variants(term: str) -> List[str]:
    canon = canonicalize(term)
    variants = {term.lower()}
    if canon:
        variants.add(canon)
        if len(canon) >= 5 and canon.endswith("s"):
            variants.add(canon[:-1])
        if len(canon) >= 7 and canon.endswith("ing"):
            variants.add(canon[:-3])
    return sorted(v for v in variants if v)


def term_occurrences(text: str, term: str) -> int:
    if not text or not term:
        return 0

    raw = text.count(term)
    canon_term = canonicalize(term)
    if not canon_term:
        return raw

    canon_text = canonicalize(text)
    canon = canon_text.count(canon_term)
    return max(raw, canon)


def parse_position(raw: Any) -> Any:
    if raw is None:
        return None
    if not isinstance(raw, str):
        return raw
    raw = raw.strip()
    if not raw:
        return ""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def to_serializable(rows: Sequence[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(row) for row in rows]


class ZoteroSQLite:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = self._connect_read_only(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA query_only = ON")
        self.conn.execute("PRAGMA foreign_keys = OFF")
        self._table_cache: Dict[str, bool] = {}
        self._column_cache: Dict[str, set] = {}

    @staticmethod
    def _connect_read_only(path: str) -> sqlite3.Connection:
        uri_base = f"file:{path}?mode=ro"
        try:
            return sqlite3.connect(uri_base + "&immutable=1", uri=True)
        except sqlite3.OperationalError:
            return sqlite3.connect(uri_base, uri=True)

    def close(self) -> None:
        self.conn.close()

    def has_table(self, name: str) -> bool:
        if name in self._table_cache:
            return self._table_cache[name]
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ? LIMIT 1",
            (name,),
        ).fetchone()
        present = row is not None
        self._table_cache[name] = present
        return present

    def fetchall(self, sql: str, params: Sequence[Any] = ()) -> List[sqlite3.Row]:
        if not sql.lstrip().upper().startswith(("SELECT", "WITH")):
            raise ValueError("Only SELECT/WITH statements are allowed.")
        return self.conn.execute(sql, params).fetchall()

    def has_column(self, table: str, column: str) -> bool:
        if table not in self._column_cache:
            cols = self.conn.execute(f"PRAGMA table_info({table})").fetchall()
            self._column_cache[table] = {str(row[1]) for row in cols}
        return column in self._column_cache[table]


def detect_db_candidates() -> List[str]:
    candidates = []

    env_path = os.environ.get("ZOTERO_DB_PATH")
    if env_path:
        candidates.append(os.path.expanduser(env_path))

    env_dir = os.environ.get("ZOTERO_DATA_DIR")
    if env_dir:
        candidates.append(os.path.join(os.path.expanduser(env_dir), "zotero.sqlite"))

    home = os.path.expanduser("~")
    globs = [
        os.path.join(home, "Zotero", "zotero.sqlite"),
        os.path.join(home, ".zotero", "zotero", "*.default*", "zotero.sqlite"),
        os.path.join(home, ".var", "app", "org.zotero.Zotero", "data", "Zotero", "zotero.sqlite"),
    ]

    for pattern in globs:
        candidates.extend(glob.glob(pattern))

    seen = set()
    existing = []
    for path in candidates:
        full = os.path.abspath(os.path.expanduser(path))
        if full in seen:
            continue
        seen.add(full)
        if os.path.exists(full):
            existing.append(full)
    return existing


def placeholders(values: Sequence[Any]) -> str:
    return ",".join(["?"] * len(values))


def resolve_db_path(cli_path: Optional[str]) -> str:
    if cli_path:
        resolved = os.path.abspath(os.path.expanduser(cli_path))
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"Database not found: {resolved}")
        return resolved

    candidates = detect_db_candidates()
    if not candidates:
        raise FileNotFoundError(
            "Could not find zotero.sqlite. Pass --db-path or set ZOTERO_DB_PATH/ZOTERO_DATA_DIR."
        )
    return candidates[0]


def get_collection_tree(db: ZoteroSQLite) -> List[sqlite3.Row]:
    if not db.has_table("collections"):
        return []
    sql = """
    WITH RECURSIVE ctree AS (
      SELECT
        c.collectionID,
        c.collectionName,
        c.parentCollectionID,
        c.libraryID,
        c.key,
        c.collectionName AS path
      FROM collections c
      WHERE c.parentCollectionID IS NULL

      UNION ALL

      SELECT
        c.collectionID,
        c.collectionName,
        c.parentCollectionID,
        c.libraryID,
        c.key,
        ctree.path || ' / ' || c.collectionName AS path
      FROM collections c
      JOIN ctree ON c.parentCollectionID = ctree.collectionID
    )
    SELECT * FROM ctree
    ORDER BY path
    """
    return db.fetchall(sql)


def resolve_collection(db: ZoteroSQLite, selector: Optional[str], library_id: Optional[int]) -> Optional[Dict[str, Any]]:
    if not selector:
        return None

    selector = selector.strip()
    rows = get_collection_tree(db)
    if not rows:
        raise ValueError("collections table is missing.")

    filtered = [dict(r) for r in rows if library_id is None or r["libraryID"] == library_id]

    if KEY_PATTERN.match(selector.upper()):
        exact_key = [r for r in filtered if (r.get("key") or "").upper() == selector.upper()]
        if len(exact_key) == 1:
            return exact_key[0]
        if len(exact_key) > 1:
            raise ValueError(f"Collection key '{selector}' is ambiguous across libraries. Use --library-id.")

    lower = selector.lower()
    exact_path = [r for r in filtered if (r.get("path") or "").lower() == lower]
    if len(exact_path) == 1:
        return exact_path[0]

    exact_name = [r for r in filtered if (r.get("collectionName") or "").lower() == lower]
    if len(exact_name) == 1:
        return exact_name[0]

    fuzzy = [
        r
        for r in filtered
        if lower in (r.get("collectionName") or "").lower() or lower in (r.get("path") or "").lower()
    ]
    if len(fuzzy) == 1:
        return fuzzy[0]
    if len(fuzzy) > 1:
        options = [f"{r['key']} | {r['path']} (library {r['libraryID']})" for r in fuzzy[:10]]
        raise ValueError(
            "Collection selector is ambiguous. Be more specific or use collection key. Matches: "
            + "; ".join(options)
        )

    raise ValueError(f"Collection '{selector}' not found.")


def descendant_collection_ids(db: ZoteroSQLite, root_collection_id: int, include_subcollections: bool) -> List[int]:
    if not include_subcollections:
        return [root_collection_id]
    sql = """
    WITH RECURSIVE subtree AS (
      SELECT collectionID FROM collections WHERE collectionID = ?
      UNION ALL
      SELECT c.collectionID
      FROM collections c
      JOIN subtree s ON c.parentCollectionID = s.collectionID
    )
    SELECT collectionID FROM subtree
    """
    rows = db.fetchall(sql, (root_collection_id,))
    return [int(r["collectionID"]) for r in rows]


def scoped_item_rows(
    db: ZoteroSQLite,
    collection_ids: Optional[List[int]],
    library_id: Optional[int],
) -> List[sqlite3.Row]:
    where = []
    params: List[Any] = []

    if library_id is not None:
        where.append("i.libraryID = ?")
        params.append(library_id)

    if collection_ids:
        if not db.has_table("collectionItems"):
            raise ValueError("collectionItems table is required for collection-scoped search.")
        where.append(f"i.itemID IN (SELECT itemID FROM collectionItems WHERE collectionID IN ({placeholders(collection_ids)}))")
        params.extend(collection_ids)

    base_where = " AND ".join(where) if where else "1=1"

    item_type_filter = ""
    if db.has_table("itemTypes"):
        item_type_filter = "AND COALESCE(it.typeName, '') NOT IN ('attachment', 'note', 'annotation')"

    sql = f"""
    SELECT
      i.itemID,
      i.key,
      i.libraryID,
      i.itemTypeID,
      i.dateAdded,
      i.dateModified,
      COALESCE(it.typeName, '') AS itemType
    FROM items i
    LEFT JOIN itemTypes it ON it.itemTypeID = i.itemTypeID
    WHERE {base_where}
      {item_type_filter}
    ORDER BY i.dateModified DESC
    """
    return db.fetchall(sql, params)


def fetch_titles(db: ZoteroSQLite, item_ids: List[int]) -> Dict[int, str]:
    if not item_ids:
        return {}
    if not (db.has_table("itemData") and db.has_table("itemDataValues") and db.has_table("fieldsCombined")):
        return {}

    sql = f"""
    SELECT
      id.itemID,
      MIN(idv.value) AS title
    FROM itemData id
    JOIN itemDataValues idv ON idv.valueID = id.valueID
    JOIN fieldsCombined fc ON fc.fieldID = id.fieldID
    WHERE id.itemID IN ({placeholders(item_ids)})
      AND lower(fc.fieldName) = 'title'
    GROUP BY id.itemID
    """
    rows = db.fetchall(sql, item_ids)
    return {int(r["itemID"]): r["title"] or "" for r in rows}


def fetch_metadata_text(db: ZoteroSQLite, item_ids: List[int]) -> Dict[int, Dict[str, str]]:
    data: Dict[int, Dict[str, str]] = {
        item_id: {
            "metadata": "",
            "creators": "",
            "tags": "",
            "notes": "",
            "annotations": "",
        }
        for item_id in item_ids
    }

    if not item_ids:
        return data

    id_params: List[Any] = list(item_ids)
    in_clause = placeholders(item_ids)

    if db.has_table("itemData") and db.has_table("itemDataValues") and db.has_table("fieldsCombined"):
        sql = f"""
        SELECT
          id.itemID,
          group_concat(fc.fieldName || ': ' || idv.value, ' || ') AS text
        FROM itemData id
        JOIN itemDataValues idv ON idv.valueID = id.valueID
        JOIN fieldsCombined fc ON fc.fieldID = id.fieldID
        WHERE id.itemID IN ({in_clause})
        GROUP BY id.itemID
        """
        for row in db.fetchall(sql, id_params):
            data[int(row["itemID"])]["metadata"] = normalize_text(row["text"])

    if db.has_table("itemCreators") and db.has_table("creators"):
        sql = f"""
        SELECT
          ic.itemID,
          group_concat(trim(coalesce(c.firstName, '') || ' ' || coalesce(c.lastName, '')), ' || ') AS text
        FROM itemCreators ic
        JOIN creators c ON c.creatorID = ic.creatorID
        WHERE ic.itemID IN ({in_clause})
        GROUP BY ic.itemID
        """
        for row in db.fetchall(sql, id_params):
            data[int(row["itemID"])]["creators"] = normalize_text(row["text"])

    if db.has_table("itemTags") and db.has_table("tags"):
        sql = f"""
        SELECT
          it.itemID,
          group_concat(t.name, ' || ') AS text
        FROM itemTags it
        JOIN tags t ON t.tagID = it.tagID
        WHERE it.itemID IN ({in_clause})
        GROUP BY it.itemID
        """
        for row in db.fetchall(sql, id_params):
            data[int(row["itemID"])]["tags"] = normalize_text(row["text"])

    if db.has_table("itemNotes"):
        sql = f"""
        SELECT
          n.parentItemID AS itemID,
          group_concat(n.note, ' || ') AS text
        FROM itemNotes n
        WHERE n.parentItemID IN ({in_clause})
        GROUP BY n.parentItemID
        """
        for row in db.fetchall(sql, id_params):
            data[int(row["itemID"])]["notes"] = normalize_text(row["text"])

    if db.has_table("itemAttachments") and db.has_table("itemAnnotations"):
        sql = f"""
        SELECT
          a.parentItemID AS itemID,
          group_concat(coalesce(ann.text, '') || ' ' || coalesce(ann.comment, ''), ' || ') AS text
        FROM itemAttachments a
        JOIN itemAnnotations ann ON ann.parentItemID = a.itemID
        WHERE a.parentItemID IN ({in_clause})
        GROUP BY a.parentItemID
        """
        for row in db.fetchall(sql, id_params):
            data[int(row["itemID"])]["annotations"] = normalize_text(row["text"])

    return data


FIELD_WEIGHTS = {
    "title": 10,
    "metadata": 4,
    "creators": 4,
    "tags": 4,
    "notes": 2,
    "annotations": 2,
}


def match_terms(
    parts: Dict[str, str],
    terms: List[str],
    any_term: bool,
    query_phrase: str = "",
) -> Tuple[bool, int, Dict[str, List[str]]]:
    merged = "\n".join(parts.values())
    if not terms:
        return True, 0, {}

    field_hits: Dict[str, List[str]] = {}
    matched_terms = 0
    score = 0

    for term in terms:
        variants = term_variants(term)
        present = any(term_occurrences(merged, variant) > 0 for variant in variants)
        if present:
            matched_terms += 1

        for field, text in parts.items():
            occurrences = max(term_occurrences(text, variant) for variant in variants)
            if occurrences > 0:
                field_hits.setdefault(field, []).append(term)
                weight = FIELD_WEIGHTS.get(field, 1)
                # Give a base hit score and a capped frequency bonus.
                score += weight + min(occurrences, 3)
                # Prefix/word-boundary-ish match bonus.
                if any((f" {variant}" in text or text.startswith(variant)) for variant in variants):
                    score += 1

    # Reward full phrase matches and complete coverage of query terms.
    if query_phrase:
        phrase = query_phrase.strip().lower()
        if phrase and phrase in merged:
            score += 8
    if matched_terms == len(terms):
        score += 3 * len(terms)

    if any_term:
        is_match = matched_terms > 0
    else:
        is_match = matched_terms == len(terms)

    return is_match, score, field_hits


def search_items(
    db: ZoteroSQLite,
    query: str,
    collection_selector: Optional[str],
    include_subcollections: bool,
    library_id: Optional[int],
    any_term: bool,
    limit: int,
) -> Dict[str, Any]:
    collection = resolve_collection(db, collection_selector, library_id) if collection_selector else None
    collection_ids = None
    if collection:
        collection_ids = descendant_collection_ids(db, int(collection["collectionID"]), include_subcollections)

    items = scoped_item_rows(db, collection_ids, library_id)
    item_ids = [int(r["itemID"]) for r in items]
    titles = fetch_titles(db, item_ids)
    parts_by_item = fetch_metadata_text(db, item_ids)

    terms = split_terms(query)
    results: List[Dict[str, Any]] = []

    for row in items:
        item_id = int(row["itemID"])
        parts = parts_by_item.get(item_id, {}).copy()
        parts["title"] = normalize_text(titles.get(item_id, ""))
        is_match, score, field_hits = match_terms(parts, terms, any_term, query)
        if not is_match:
            continue

        results.append(
            {
                "itemID": item_id,
                "key": row["key"],
                "libraryID": row["libraryID"],
                "itemType": row["itemType"],
                "title": titles.get(item_id, ""),
                "dateAdded": row["dateAdded"],
                "dateModified": row["dateModified"],
                "score": score,
                "matchedFields": {k: sorted(set(v)) for k, v in field_hits.items()},
            }
        )

    results.sort(key=lambda r: (-r["score"], r.get("title") or "", r["key"]))
    if limit > 0:
        results = results[:limit]

    return {
        "query": query,
        "terms": terms,
        "anyTerm": any_term,
        "collection": collection,
        "includeSubcollections": include_subcollections,
        "resultCount": len(results),
        "results": results,
    }


def resolve_parent_item_ids(
    db: ZoteroSQLite,
    item_id: Optional[int],
    item_key: Optional[str],
    library_id: Optional[int],
    search_query: Optional[str],
    collection_selector: Optional[str],
    include_subcollections: bool,
    limit: int,
) -> List[int]:
    if item_id is not None:
        return [item_id]

    if item_key:
        params: List[Any] = [item_key]
        sql = "SELECT itemID FROM items WHERE key = ?"
        if library_id is not None:
            sql += " AND libraryID = ?"
            params.append(library_id)
        rows = db.fetchall(sql, params)
        if not rows:
            raise ValueError(f"Item key '{item_key}' not found.")
        return [int(r["itemID"]) for r in rows]

    if search_query:
        search_data = search_items(
            db,
            query=search_query,
            collection_selector=collection_selector,
            include_subcollections=include_subcollections,
            library_id=library_id,
            any_term=False,
            limit=limit,
        )
        return [int(row["itemID"]) for row in search_data["results"]]

    collection = resolve_collection(db, collection_selector, library_id) if collection_selector else None
    collection_ids = None
    if collection:
        collection_ids = descendant_collection_ids(db, int(collection["collectionID"]), include_subcollections)

    return [int(r["itemID"]) for r in scoped_item_rows(db, collection_ids, library_id)]


def pdf_positions(
    db: ZoteroSQLite,
    parent_item_ids: List[int],
    annotation_query: Optional[str],
    any_term: bool,
) -> Dict[str, Any]:
    if not parent_item_ids:
        return {"resultCount": 0, "results": []}

    if not db.has_table("itemAttachments"):
        raise ValueError("itemAttachments table is missing.")
    if not db.has_table("itemAnnotations"):
        raise ValueError("itemAnnotations table is missing.")

    terms = split_terms(annotation_query or "")
    id_clause = placeholders(parent_item_ids)
    has_date_modified = db.has_column("itemAnnotations", "dateModified")
    date_modified_expr = "ann.dateModified" if has_date_modified else "NULL"

    sql = f"""
    SELECT
      p.itemID AS parentItemID,
      p.key AS parentItemKey,
      a.itemID AS attachmentItemID,
      a.key AS attachmentItemKey,
      at.path AS attachmentPath,
      at.contentType,
      ann.itemID AS annotationItemID,
      ann.type,
      ann.text,
      ann.comment,
      ann.color,
      ann.pageLabel,
      ann.sortIndex,
      ann.position,
      {date_modified_expr} AS dateModified
    FROM items p
    JOIN itemAttachments at ON at.parentItemID = p.itemID
    JOIN items a ON a.itemID = at.itemID
    LEFT JOIN itemAnnotations ann ON ann.parentItemID = a.itemID
    WHERE p.itemID IN ({id_clause})
      AND (
        lower(coalesce(at.contentType, '')) LIKE 'application/pdf%'
        OR lower(coalesce(at.path, '')) LIKE '%.pdf'
      )
    ORDER BY p.itemID, a.itemID, ann.sortIndex, ann.itemID
    """

    rows = db.fetchall(sql, parent_item_ids)
    results: List[Dict[str, Any]] = []

    for row in rows:
        ann_text = normalize_text((row["text"] or "") + " " + (row["comment"] or ""))
        is_match, _, _ = match_terms({"annotation": ann_text}, terms, any_term)
        if terms and not is_match:
            continue

        result = {
            "parentItemID": row["parentItemID"],
            "parentItemKey": row["parentItemKey"],
            "attachmentItemID": row["attachmentItemID"],
            "attachmentItemKey": row["attachmentItemKey"],
            "attachmentPath": row["attachmentPath"],
            "contentType": row["contentType"],
            "annotationItemID": row["annotationItemID"],
            "annotationType": row["type"],
            "text": row["text"],
            "comment": row["comment"],
            "color": row["color"],
            "pageLabel": row["pageLabel"],
            "sortIndex": row["sortIndex"],
            "position": parse_position(row["position"]),
            "dateModified": row["dateModified"],
        }
        results.append(result)

    return {
        "query": annotation_query or "",
        "terms": terms,
        "anyTerm": any_term,
        "parentItemCount": len(parent_item_ids),
        "resultCount": len(results),
        "results": results,
    }


def list_collections(db: ZoteroSQLite, selector: Optional[str], library_id: Optional[int], limit: int) -> Dict[str, Any]:
    rows = [dict(r) for r in get_collection_tree(db)]
    if library_id is not None:
        rows = [r for r in rows if r["libraryID"] == library_id]

    if selector:
        needle = selector.lower()
        rows = [
            r
            for r in rows
            if needle in (r.get("path") or "").lower()
            or needle in (r.get("collectionName") or "").lower()
            or needle in (r.get("key") or "").lower()
        ]

    if limit > 0:
        rows = rows[:limit]

    return {"resultCount": len(rows), "results": rows}


def print_output(data: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=True))
        return

    if "results" in data:
        print(f"resultCount: {data.get('resultCount', 0)}")
        for row in data["results"]:
            if isinstance(row, dict):
                print(json.dumps(row, ensure_ascii=True))
            else:
                print(row)
    else:
        print(json.dumps(data, indent=2, ensure_ascii=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Zotero sqlite helper")
    parser.add_argument("--db-path", help="Path to zotero.sqlite")
    parser.add_argument("--library-id", type=int, help="Limit to one libraryID")
    parser.add_argument("--text", action="store_true", help="Print compact text output instead of JSON")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("locate-db", help="Detect zotero.sqlite candidates")

    col = sub.add_parser("list-collections", help="List collection keys and paths")
    col.add_argument("--collection", help="Filter collections by key/name/path fragment")
    col.add_argument("--limit", type=int, default=50)

    search = sub.add_parser("search-items", help="Search metadata/tags/notes/annotations")
    search.add_argument("--query", required=True, help="Search query")
    search.add_argument("--collection", help="Collection key/name/path")
    search.add_argument("--include-subcollections", action="store_true")
    search.add_argument("--any-term", action="store_true", help="Match any term (default: all terms)")
    search.add_argument("--limit", type=int, default=100)

    pos = sub.add_parser("pdf-positions", help="Retrieve PDF annotation positions")
    pos.add_argument("--item-id", type=int)
    pos.add_argument("--item-key")
    pos.add_argument("--query", help="Filter annotations by text/comment query")
    pos.add_argument("--collection", help="Collection key/name/path")
    pos.add_argument("--include-subcollections", action="store_true")
    pos.add_argument("--any-term", action="store_true")
    pos.add_argument("--limit", type=int, default=100)

    return parser


def run(args: argparse.Namespace) -> Dict[str, Any]:
    if args.command == "locate-db":
        candidates = detect_db_candidates()
        return {
            "resultCount": len(candidates),
            "selected": candidates[0] if candidates else None,
            "candidates": candidates,
        }

    db_path = resolve_db_path(args.db_path)
    db = ZoteroSQLite(db_path)
    try:
        if args.command == "list-collections":
            data = list_collections(db, args.collection, args.library_id, args.limit)
            data["dbPath"] = db_path
            return data

        if args.command == "search-items":
            data = search_items(
                db=db,
                query=args.query,
                collection_selector=args.collection,
                include_subcollections=args.include_subcollections,
                library_id=args.library_id,
                any_term=args.any_term,
                limit=args.limit,
            )
            data["dbPath"] = db_path
            return data

        if args.command == "pdf-positions":
            parent_ids = resolve_parent_item_ids(
                db=db,
                item_id=args.item_id,
                item_key=args.item_key,
                library_id=args.library_id,
                search_query=args.query if not args.item_id and not args.item_key else None,
                collection_selector=args.collection,
                include_subcollections=args.include_subcollections,
                limit=args.limit,
            )
            data = pdf_positions(
                db=db,
                parent_item_ids=parent_ids,
                annotation_query=args.query if args.item_id or args.item_key else None,
                any_term=args.any_term,
            )
            data["dbPath"] = db_path
            return data

        raise ValueError(f"Unsupported command: {args.command}")
    finally:
        db.close()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        data = run(args)
        print_output(data, as_json=not args.text)
        return 0
    except Exception as exc:
        eprint(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

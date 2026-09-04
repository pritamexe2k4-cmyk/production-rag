# ============================================================
#  ingestion/pipeline_structured.py
#
#  PIPELINE 3 — STRUCTURED DATA (Row-by-Row)
#
#  HANDLES:
#    - CSV files where each ROW is a separate retrievable record
#    - JSON files (array of objects or a single object)
#    - JSONL files (one JSON object per line)
#
#  DIFFERENCE FROM pipeline_table.py:
#    pipeline_table.py  → treats entire CSV as ONE table (for lookup)
#    pipeline_structured.py → treats each CSV ROW as ONE Document (for retrieval)
#
#    Use this when:
#      - You want to find specific records ("what is the price of iPhone 15?")
#      - The CSV has many rows and you want semantic row-level search
#
#    Use pipeline_table.py when:
#      - The CSV is a small reference table
#      - You want the LLM to see the whole table together
#
#  WHAT IT DOES:
#  1. Reads CSV / JSON data with pandas or json
#  2. For each row/record: converts key-value pairs to a natural language sentence
#     "Product: iPhone 15, Category: Smartphone, Price: $999, Stock: 42 units"
#  3. Prepends schema context (column names) so the LLM knows what each value is
#  4. Wraps each sentence as a Document (one Document per row)
#
#  WHY CONVERT TO NATURAL LANGUAGE SENTENCES?
#    The embedding model doesn't understand raw structured data.
#    "999" tells it nothing. But "Product: iPhone 15, Price: $999"
#    has semantic meaning the embedding model can capture and retrieve.
#
#  OUTPUT:
#    List[Document] — one Document per row/record
#    page_content = natural language sentence describing the record
# ============================================================

import json
from pathlib import Path
from typing import List

from langchain_core.documents import Document


# ─────────────────────────────────────────────────────────────────────────────
#  Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def load_structured(source: str) -> List[Document]:
    """
    Load structured data (CSV, JSON, JSONL) and convert each record to a Document.

    Each row/record becomes a natural language sentence so it can be
    semantically searched in the vector store.

    Args:
        source: File path to a .csv, .json, or .jsonl file

    Returns:
        List of Documents, one per row/record.
        Each has metadata: content_type="structured", row_index=N
    """
    ext = Path(source).suffix.lower()

    if ext == ".csv":
        return _load_csv_rows(source)
    elif ext == ".json":
        return _load_json(source)
    elif ext == ".jsonl":
        return _load_jsonl(source)
    else:
        raise ValueError(
            f"[pipeline_structured] Unsupported format: '{ext}'. "
            f"Supported: .csv, .json, .jsonl"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  CSV Row-by-Row Loader
# ─────────────────────────────────────────────────────────────────────────────

def _load_csv_rows(path: str) -> List[Document]:
    """
    Load a CSV file and convert each row to a natural language sentence Document.

    The column headers are used as field names in the sentence.
    Each row becomes: "ColumnA: value1, ColumnB: value2, ColumnC: value3"

    Args:
        path: File path to a .csv file

    Returns:
        List of Documents, one per row
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "[pipeline_structured] pandas is not installed.\n"
            "Run: pip install pandas"
        )

    print(f"[pipeline_structured] Loading CSV rows: {path}")
    df = pd.read_csv(path)

    if df.empty:
        print(f"[pipeline_structured] ⚠ CSV is empty: {path}")
        return []

    docs = []
    columns = list(df.columns)

    for row_idx, row in df.iterrows():
        # Convert row to "Key: value, Key: value, ..." sentence
        parts = []
        for col in columns:
            val = row[col]
            if str(val).strip() and str(val).lower() != "nan":
                parts.append(f"{col}: {val}")

        sentence = ", ".join(parts)

        if not sentence.strip():
            continue

        docs.append(Document(
            page_content=sentence,
            metadata={
                "source":       path,
                "content_type": "structured",
                "page":         0,
                "format":       "csv",
                "row_index":    int(row_idx),
                "columns":      ", ".join(columns),  # schema context in metadata
            }
        ))

    print(f"[pipeline_structured] ✓ CSV loaded: {len(docs)} row Documents created")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
#  JSON Loader
# ─────────────────────────────────────────────────────────────────────────────

def _load_json(path: str) -> List[Document]:
    """
    Load a JSON file.

    Handles two JSON structures:
      1. Array of objects: [ {...}, {...}, {...} ]  → one Document per object
      2. Single object:    { "key": "value", ... } → one Document total

    Each object is converted to: "key: value, key: value, ..."

    Args:
        path: File path to a .json file

    Returns:
        List of Documents
    """
    print(f"[pipeline_structured] Loading JSON: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize to list of records
    if isinstance(data, dict):
        records = [data]        # single object → wrap in list
    elif isinstance(data, list):
        records = data          # already a list of objects
    else:
        raise ValueError(f"[pipeline_structured] Unsupported JSON root type: {type(data)}")

    return _records_to_documents(records, source=path, file_format="json")


# ─────────────────────────────────────────────────────────────────────────────
#  JSONL Loader
# ─────────────────────────────────────────────────────────────────────────────

def _load_jsonl(path: str) -> List[Document]:
    """
    Load a JSONL (JSON Lines) file — one JSON object per line.

    Common format for large datasets, LLM training data, and API logs.

    Args:
        path: File path to a .jsonl file

    Returns:
        List of Documents, one per line/record
    """
    print(f"[pipeline_structured] Loading JSONL: {path}")
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[pipeline_structured] ⚠ Skipping malformed line {line_num}: {e}")

    return _records_to_documents(records, source=path, file_format="jsonl")


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: List of records → List of Documents
# ─────────────────────────────────────────────────────────────────────────────

def _records_to_documents(records: list, source: str, file_format: str) -> List[Document]:
    """
    Convert a list of dicts (records) into Documents.

    Each dict is flattened into a "key: value, key: value" sentence.
    Nested dicts/lists are JSON-stringified for readability.

    Args:
        records    : List of dict records
        source     : Original file path (for metadata)
        file_format: "json" or "jsonl" (for metadata)

    Returns:
        List of Documents
    """
    docs = []

    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            continue

        parts = []
        for key, value in record.items():
            if value is None or str(value).strip() == "":
                continue
            # Stringify nested structures
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            parts.append(f"{key}: {value}")

        sentence = ", ".join(parts)
        if not sentence.strip():
            continue

        docs.append(Document(
            page_content=sentence,
            metadata={
                "source":       source,
                "content_type": "structured",
                "page":         0,
                "format":       file_format,
                "row_index":    idx,
            }
        ))

    print(f"[pipeline_structured] ✓ {file_format.upper()} loaded: {len(docs)} record Documents")
    return docs

# ============================================================
#  ingestion/pipeline_table.py
#
#  PIPELINE 2 — TABLES
#
#  HANDLES:
#    - Tables embedded inside PDFs (extracted via Docling)
#    - Excel files (.xlsx, .xls) — each sheet becomes Documents
#    - CSV files used as lookup tables (entire file = one table)
#
#  THE KEY RULE:
#    Tables are NEVER split across chunks.
#    Each table = exactly ONE Document.
#    The metadata key "skip_chunking": True signals chunking step to skip it.
#
#  WHY TABLES NEED SPECIAL HANDLING:
#    If you flatten a table to plain text:
#      "Q1 2.1M Q2 2.8M Q3 3.4M Q4 4.1M"
#    → the LLM has no idea what those numbers mean or how they relate.
#
#    If you serialize as Markdown table:
#      "| Quarter | Revenue |
#       |---------|---------|
#       | Q1      | $2.1M   |"
#    → LLM can read this like a human would.
#
#  WHAT IT DOES:
#  1. For PDFs: uses Docling to detect and extract tables as Markdown
#  2. For Excel: uses pandas to read sheets → Markdown table
#  3. For CSV: reads entire file → Markdown table (best for small lookup tables)
#  4. Prepends the table heading/context so the LLM knows what the table is about
#  5. Wraps each table as a single Document with skip_chunking=True
#
#  OUTPUT:
#    List[Document] where page_content is a Markdown table string
#    metadata["skip_chunking"] = True  ← tells 2_chunking.py to leave it alone
# ============================================================

from pathlib import Path
from typing import List

from langchain_core.documents import Document


# ─────────────────────────────────────────────────────────────────────────────
#  Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def load_tables(source: str) -> List[Document]:
    """
    Extract all tables from a PDF, Excel, or CSV file.

    Each table becomes exactly ONE Document (never split).
    Tables are serialized to Markdown format for LLM readability.

    Args:
        source: File path to a .pdf, .xlsx, .xls, or .csv file

    Returns:
        List of Documents, one per table.
        Each has metadata: content_type="table", skip_chunking=True
    """
    ext = Path(source).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf_tables(source)
    elif ext in (".xlsx", ".xls"):
        return _extract_excel_tables(source)
    elif ext == ".csv":
        return _extract_csv_table(source)
    else:
        raise ValueError(
            f"[pipeline_table] Unsupported format: '{ext}'. "
            f"Supported: .pdf, .xlsx, .xls, .csv"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  PDF Table Extractor (via Docling)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_pdf_tables(path: str) -> List[Document]:
    """
    Extract all tables from a PDF using Docling.

    Docling's table detection model identifies table regions in the PDF,
    reconstructs the row-column structure, and exports each table
    as a properly formatted Markdown table string.

    For each table, we also capture the text immediately above the table
    (the table heading/caption) and prepend it as context so the LLM
    understands what the table is about.

    Args:
        path: File path to a .pdf file

    Returns:
        List of Documents, one per table found in the PDF
    """
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        raise ImportError(
            "[pipeline_table] Docling is not installed.\n"
            "Run: pip install docling"
        )

    print(f"[pipeline_table] Extracting tables from PDF: {path}")
    converter = DocumentConverter()
    result = converter.convert(path)

    docs = []
    tables_found = 0

    # Docling's result.document.tables gives us all detected tables
    for table_idx, table in enumerate(result.document.tables):
        tables_found += 1

        # Export table to Markdown format  (preserves rows and columns)
        table_markdown = table.export_to_markdown()

        # Try to find the caption/heading that appears above this table
        # Docling stores table captions in table.caption_text when available
        caption = ""
        if hasattr(table, "caption_text") and table.caption_text:
            caption = f"**Table: {table.caption_text}**\n\n"

        # Build the final content: optional heading + Markdown table
        content = caption + table_markdown

        # Get page number where this table lives
        page_num = 0
        if hasattr(table, "prov") and table.prov:
            page_num = table.prov[0].page_no if table.prov else 0

        docs.append(Document(
            page_content=content,
            metadata={
                "source":        path,
                "content_type":  "table",
                "page":          page_num,
                "table_index":   table_idx,
                "format":        "pdf",
                "skip_chunking": True,   # ← CRITICAL: keep table whole
            }
        ))

    print(f"[pipeline_table] ✓ PDF table extraction complete: {tables_found} tables found")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
#  Excel Table Extractor (via pandas)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_excel_tables(path: str) -> List[Document]:
    """
    Load an Excel file and convert each sheet to a Markdown table Document.

    Each sheet in the Excel file becomes one Document.
    The sheet name is used as the table heading for context.

    Args:
        path: File path to a .xlsx or .xls file

    Returns:
        List of Documents, one per non-empty sheet
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "[pipeline_table] pandas is not installed.\n"
            "Run: pip install pandas openpyxl"
        )

    print(f"[pipeline_table] Loading Excel: {path}")
    excel_file = pd.ExcelFile(path)
    docs = []

    for sheet_name in excel_file.sheet_names:
        df = excel_file.parse(sheet_name)

        # Skip empty sheets
        if df.empty:
            print(f"[pipeline_table] ⚠ Skipping empty sheet: '{sheet_name}'")
            continue

        # Convert DataFrame to Markdown table string
        table_markdown = _dataframe_to_markdown(df)

        # Prepend sheet name as heading/context
        content = f"**Table: {sheet_name}**\n\n{table_markdown}"

        docs.append(Document(
            page_content=content,
            metadata={
                "source":        path,
                "content_type":  "table",
                "page":          0,
                "sheet_name":    sheet_name,
                "format":        "excel",
                "skip_chunking": True,   # ← keep table whole
            }
        ))

    print(f"[pipeline_table] ✓ Excel loaded: {len(docs)} sheets as tables")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
#  CSV Table Loader (via pandas)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_csv_table(path: str) -> List[Document]:
    """
    Load a CSV file as a single Markdown table Document.

    This treats the CSV as a LOOKUP TABLE (not row-by-row records).
    Use pipeline_structured.py instead if you want each row as
    a separate natural language sentence for row-level retrieval.

    Args:
        path: File path to a .csv file

    Returns:
        List with a single Document containing the full CSV as a Markdown table
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "[pipeline_table] pandas is not installed.\n"
            "Run: pip install pandas"
        )

    print(f"[pipeline_table] Loading CSV as table: {path}")
    df = pd.read_csv(path)

    if df.empty:
        print(f"[pipeline_table] ⚠ CSV is empty: {path}")
        return []

    table_markdown = _dataframe_to_markdown(df)
    filename = Path(path).stem.replace("_", " ").title()
    content = f"**Table: {filename}**\n\n{table_markdown}"

    docs = [Document(
        page_content=content,
        metadata={
            "source":        path,
            "content_type":  "table",
            "page":          0,
            "format":        "csv",
            "num_rows":      len(df),
            "num_cols":      len(df.columns),
            "skip_chunking": True,   # ← keep table whole
        }
    )]

    print(f"[pipeline_table] ✓ CSV loaded as table: {len(df)} rows × {len(df.columns)} cols")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: DataFrame → Markdown Table
# ─────────────────────────────────────────────────────────────────────────────

def _dataframe_to_markdown(df) -> str:
    """
    Convert a pandas DataFrame to a properly formatted Markdown table string.

    Example output:
        | Name    | Age | City     |
        |---------|-----|----------|
        | Alice   | 30  | New York |
        | Bob     | 25  | London   |

    This format is natively understood by LLMs and preserves
    the row-column relationships of the original table.

    Args:
        df: A pandas DataFrame

    Returns:
        Markdown table as a string
    """
    import pandas as pd

    # Fill NaN values with empty string for cleaner output
    df = df.fillna("")

    # Build header row
    headers = list(df.columns)
    header_row = "| " + " | ".join(str(h) for h in headers) + " |"
    separator  = "| " + " | ".join("---" for _ in headers) + " |"

    # Build data rows
    data_rows = []
    for _, row in df.iterrows():
        row_str = "| " + " | ".join(str(v) for v in row.values) + " |"
        data_rows.append(row_str)

    return "\n".join([header_row, separator] + data_rows)

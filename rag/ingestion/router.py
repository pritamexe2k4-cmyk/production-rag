# ============================================================
#  ingestion/router.py
#
#  DOCUMENT ROUTER
#
#  Detects the file type (or URL) and calls the correct pipeline(s).
#  Mixed documents (e.g. PDF with text + tables + images) run
#  multiple pipelines and merge the results.
#
#  ROUTING RULES:
#  --------------
#  URL / .md / .txt / .docx / .doc  → pipeline_text
#  .pdf                             → pipeline_text + pipeline_table + pipeline_image
#  .xlsx / .xls                     → pipeline_table
#  .csv                             → pipeline_structured OR pipeline_table (user choice)
#  .json / .jsonl                   → pipeline_structured
#  .py / .js / .ts / .sql / ...     → pipeline_code
#  .png / .jpg / .webp / ...        → pipeline_image
# ============================================================

from pathlib import Path
from typing import List, Literal

from langchain_core.documents import Document

from .normalizer import normalize
from .pipeline_code import load_code
from .pipeline_image import load_images
from .pipeline_structured import load_structured
from .pipeline_table import load_tables
from .pipeline_text import load_text


# File extensions grouped by primary pipeline
TEXT_EXTENSIONS = {".pdf", ".docx", ".doc", ".md", ".txt"}
TABLE_EXTENSIONS = {".xlsx", ".xls"}
STRUCTURED_EXTENSIONS = {".json", ".jsonl"}
CSV_EXTENSION = ".csv"

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".rb", ".cpp", ".c", ".h", ".cs",
    ".sql", ".sh", ".bash", ".yaml", ".yml", ".toml",
    ".html", ".css", ".scss",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}


CsvMode = Literal["structured", "table"]


def route_and_ingest(
    source: str,
    csv_mode: CsvMode = "structured",
    include_images: bool = True,
    vision_model: str = "llava",
    image_output_dir: str | None = None,
) -> List[Document]:
    """
    Main router: detect source type and run the appropriate pipeline(s).

    Args:
        source:           File path or URL
        csv_mode:         How to handle CSV files:
                            "structured" → one Document per row (default)
                            "table"      → entire CSV as one Markdown table
        include_images:   Extract and caption images from PDFs (requires Ollama)
        vision_model:     Ollama vision model name (default: "llava")
        image_output_dir: Folder to save extracted images (default: ./rag_artifacts/images/)

    Returns:
        List of normalized Document objects ready for chunking
    """
    source = source.strip()
    print(f"\n[router] Ingesting: {source}")

    if source.startswith("http://") or source.startswith("https://"):
        return normalize(load_text(source), pipeline_name="text", source=source)

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"[router] File not found: {source}")

    ext = path.suffix.lower()
    all_docs: List[Document] = []

    # ── Code files ────────────────────────────────────────────────────────────
    if ext in CODE_EXTENSIONS:
        return normalize(load_code(source), pipeline_name="code", source=source)

    # ── Standalone images ─────────────────────────────────────────────────────
    if ext in IMAGE_EXTENSIONS:
        return normalize(
            load_images(
                source,
                vision_model=vision_model,
                output_dir=image_output_dir,
            ),
            pipeline_name="image",
            source=source,
        )

    # ── Structured data (JSON / JSONL) ────────────────────────────────────────
    if ext in STRUCTURED_EXTENSIONS:
        return normalize(
            load_structured(source),
            pipeline_name="structured",
            source=source,
        )

    # ── CSV (user chooses row-by-row vs whole-table mode) ─────────────────────
    if ext == CSV_EXTENSION:
        if csv_mode == "table":
            return normalize(load_tables(source), pipeline_name="table", source=source)
        return normalize(
            load_structured(source),
            pipeline_name="structured",
            source=source,
        )

    # ── Excel (always table mode) ─────────────────────────────────────────────
    if ext in TABLE_EXTENSIONS:
        return normalize(load_tables(source), pipeline_name="table", source=source)

    # ── PDF: text + tables + images (multi-pipeline) ──────────────────────────
    if ext == ".pdf":
        all_docs.extend(normalize(load_text(source), pipeline_name="text", source=source))
        all_docs.extend(normalize(load_tables(source), pipeline_name="table", source=source))
        if include_images:
            all_docs.extend(
                normalize(
                    load_images(
                        source,
                        vision_model=vision_model,
                        output_dir=image_output_dir,
                    ),
                    pipeline_name="image",
                    source=source,
                )
            )
        print(f"[router] ✓ PDF complete: {len(all_docs)} total Documents")
        return all_docs

    # ── Plain text formats (DOCX, MD, TXT) ────────────────────────────────────
    if ext in TEXT_EXTENSIONS:
        return normalize(load_text(source), pipeline_name="text", source=source)

    raise ValueError(
        f"[router] Unsupported file type: '{ext}' for file '{source}'.\n"
        f"Supported: PDF, DOCX, MD, TXT, CSV, JSON, JSONL, Excel, code files, "
        f"images, or a URL."
    )

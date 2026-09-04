# ============================================================
#  ingestion/normalizer.py
#
#  ROLE: Quality gate between every pipeline and the rest of the RAG system.
#
#  WHAT IT DOES:
#  - Every pipeline outputs raw Document objects.
#  - This normalizer enforces a UNIFORM schema on all of them.
#  - Validates: page_content is non-empty string.
#  - Ensures: required metadata keys are always present.
#  - Removes: any Document that is empty or garbage.
#  - Tags: which pipeline produced each Document (for debugging).
#
#  WHY IT EXISTS:
#  - Downstream steps (chunking, embedding, vector store) must trust
#    that every Document they receive has the same shape.
#  - Without this, one bad pipeline can silently corrupt the whole system.
#
#  REQUIRED METADATA SCHEMA (every Document must have these):
#  ----------------------------------------------------------
#  {
#    "source":       str   — filename or URL the document came from
#    "content_type": str   — "text" | "table" | "image" | "structured" | "code"
#    "pipeline":     str   — which pipeline produced this Document
#    "page":         int   — page number (0 if not applicable)
#    "skip_chunking": bool — True for tables/images that must stay whole
#  }
# ============================================================

from langchain_core.documents import Document
from typing import List


# Required metadata keys every Document must have after normalization
REQUIRED_METADATA_KEYS = {
    "source": "",
    "content_type": "text",
    "pipeline": "unknown",
    "page": 0,
    "skip_chunking": False,
}


def normalize(docs: List[Document], pipeline_name: str, source: str) -> List[Document]:
    """
    Normalize a list of Documents from any pipeline.

    Steps:
    1. Filter out Documents with empty page_content.
    2. Fill in any missing metadata keys with defaults.
    3. Tag every Document with the pipeline that produced it.
    4. Return the cleaned, uniform list.

    Args:
        docs         : Raw Documents from a pipeline
        pipeline_name: Name of the pipeline (e.g. "text", "table", "image")
        source       : The original source file path or URL

    Returns:
        List of normalized Documents ready for chunking
    """
    normalized = []

    for doc in docs:
        # ── Step 1: Skip empty or whitespace-only Documents ──────────
        if not doc.page_content or not doc.page_content.strip():
            print(f"[normalizer] ⚠ Skipping empty Document from pipeline='{pipeline_name}' source='{source}'")
            continue

        # ── Step 2: Start with defaults, then overlay doc's own metadata ──
        final_metadata = dict(REQUIRED_METADATA_KEYS)      # start with all defaults
        final_metadata.update(doc.metadata)                 # override with actual values

        # ── Step 3: Always enforce source and pipeline tag ────────────
        final_metadata["source"]   = final_metadata.get("source") or source
        final_metadata["pipeline"] = pipeline_name

        # ── Step 4: Build the clean Document ──────────────────────────
        normalized.append(
            Document(
                page_content=doc.page_content.strip(),
                metadata=final_metadata,
            )
        )

    print(f"[normalizer] ✓ pipeline='{pipeline_name}' | input={len(docs)} docs | output={len(normalized)} docs after normalization")
    return normalized

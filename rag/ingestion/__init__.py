# ============================================================
#  ingestion/ — Multi-Modal Document Ingestion Package
#
#  USAGE:
#    from rag.ingestion import ingest
#
#    docs = ingest("report.pdf")                          # PDF: text + tables + images
#    docs = ingest("products.csv")                        # CSV: row-by-row (default)
#    docs = ingest("products.csv", csv_mode="table")      # CSV: whole table
#    docs = ingest("https://docs.example.com/page")       # Web page
#    docs = ingest("utils.py")                            # Code file
#    docs = ingest("diagram.png")                         # Standalone image
#
#  OUTPUT:
#    List[Document] — normalized, ready for 2_chunking.py
#
#  PIPELINES:
#    pipeline_text.py       — PDF, DOCX, URL, Markdown
#    pipeline_table.py      — PDF/Excel/CSV tables (Markdown, never split)
#    pipeline_structured.py — CSV/JSON rows as natural language sentences
#    pipeline_image.py      — Images/charts via Ollama LLaVA captions
#    pipeline_code.py       — Source code with function-aware splitting
#    normalizer.py          — Quality gate, uniform metadata on all Documents
#    router.py              — Detects format, calls the right pipeline(s)
# ============================================================

from .router import route_and_ingest

ingest = route_and_ingest

__all__ = ["ingest", "route_and_ingest"]

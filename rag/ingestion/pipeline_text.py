# ============================================================
#  ingestion/pipeline_text.py
#
#  PIPELINE 1 — PLAIN TEXT
#
#  HANDLES:
#    - Digital PDFs (those with a text layer — not scanned)
#    - Word documents (.docx)
#    - Web pages / URLs
#    - Markdown files (.md)
#
#  WHAT IT DOES:
#  1. Loads the source using the right loader for its format
#  2. Extracts text while preserving structure (headings, paragraphs, lists)
#  3. Converts everything to clean Markdown strings
#  4. Wraps each logical section in a LangChain Document object
#  5. Attaches metadata: source, page number, content_type = "text"
#
#  OUTPUT:
#    List[Document] where each Document.page_content is a clean Markdown string
#
#  HOW EACH FORMAT IS LOADED:
#  --------------------------
#  PDF    → Docling (IBM open source): layout-aware, preserves headings/structure
#  DOCX   → Docling or python-docx: extracts text + heading levels
#  URL    → Jina Reader API (r.jina.ai prefix): zero setup, outputs clean Markdown
#           Fallback: LangChain WebBaseLoader (static pages only)
#  MD     → Read directly as plain text (already Markdown)
#
#  DOCLING INSTALL:
#    pip install docling
#
#  NOTE: This pipeline does NOT handle tables or images inside PDFs.
#  Those are handled by pipeline_table.py and pipeline_image.py.
#  Docling extracts those separately; this pipeline only takes the text body.
# ============================================================

import re
import urllib.request
from pathlib import Path
from typing import List

from langchain_core.documents import Document

try:
    from langchain_community.document_loaders import WebBaseLoader
except ImportError:
    WebBaseLoader = None


# ── Jina Reader base URL ─────────────────────────────────────────────────────
# Prefix any URL with this to get clean Markdown back (no API key needed)
JINA_READER_PREFIX = "https://r.jina.ai/"


# ─────────────────────────────────────────────────────────────────────────────
#  Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def load_text(source: str) -> List[Document]:
    """
    Load plain text content from a PDF, DOCX, URL, or Markdown file.

    Detects the source type automatically and routes to the correct loader.

    Args:
        source: File path (str) or URL (str)

    Returns:
        List of Documents with page_content as clean Markdown text.
        Metadata includes: source, page, content_type="text"
    """
    source = source.strip()

    if source.startswith("http://") or source.startswith("https://"):
        return _load_url(source)

    ext = Path(source).suffix.lower()

    if ext == ".pdf":
        return _load_pdf(source)
    elif ext in (".docx", ".doc"):
        return _load_docx(source)
    elif ext in (".md", ".txt"):
        return _load_markdown(source)
    else:
        raise ValueError(
            f"[pipeline_text] Unsupported file type: '{ext}'. "
            f"Supported: .pdf, .docx, .doc, .md, .txt, or a URL."
        )


# ─────────────────────────────────────────────────────────────────────────────
#  PDF Loader (via Docling)
# ─────────────────────────────────────────────────────────────────────────────

def _load_pdf(path: str) -> List[Document]:
    """
    Load a digital PDF using Docling.

    Docling is layout-aware — it understands multi-column layouts,
    reading order, heading levels, and paragraph boundaries.
    It outputs clean Markdown that preserves document structure.

    Tables and images found inside the PDF are intentionally SKIPPED here.
    They are handled by pipeline_table.py and pipeline_image.py respectively.

    Args:
        path: Absolute or relative file path to a .pdf file

    Returns:
        List of Documents (one per page or logical section)
    """
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        raise ImportError(
            "[pipeline_text] Docling is not installed.\n"
            "Run: pip install docling"
        )

    print(f"[pipeline_text] Loading PDF: {path}")
    converter = DocumentConverter()
    result = converter.convert(path)

    # Docling's export_to_markdown() returns the full doc as one Markdown string
    # We split it into per-page Documents using the page map
    docs = []

    # Export full Markdown then split by page boundaries
    full_markdown = result.document.export_to_markdown()

    # Split by page: Docling marks page breaks with <!-- page break --> or similar
    # Fallback: treat entire document as one Document if no page markers
    pages = full_markdown.split("\n\n---\n\n")  # Docling inserts --- between pages

    for page_num, page_text in enumerate(pages, start=1):
        page_text = page_text.strip()
        if not page_text:
            continue
        docs.append(Document(
            page_content=page_text,
            metadata={
                "source":       path,
                "content_type": "text",
                "page":         page_num,
                "format":       "pdf",
            }
        ))

    print(f"[pipeline_text] ✓ PDF loaded: {len(docs)} page sections extracted")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
#  DOCX Loader (via Docling)
# ─────────────────────────────────────────────────────────────────────────────

def _load_docx(path: str) -> List[Document]:
    """
    Load a Word document (.docx) using Docling.

    Docling handles DOCX natively — it extracts text with heading levels
    preserved (# for Heading 1, ## for Heading 2, etc.) and outputs Markdown.

    Args:
        path: Absolute or relative file path to a .docx file

    Returns:
        List of Documents (one per logical section / heading block)
    """
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        raise ImportError(
            "[pipeline_text] Docling is not installed.\n"
            "Run: pip install docling"
        )

    print(f"[pipeline_text] Loading DOCX: {path}")
    converter = DocumentConverter()
    result = converter.convert(path)

    full_markdown = result.document.export_to_markdown()

    # Split on heading level 1 or 2 to create logical sections
    # Each section = one Document so retrieval can find precise sections
    # Split on any line that starts with # (heading)
    sections = re.split(r'(?m)^(?=#{1,2} )', full_markdown)
    sections = [s.strip() for s in sections if s.strip()]

    docs = []
    for idx, section in enumerate(sections):
        docs.append(Document(
            page_content=section,
            metadata={
                "source":       path,
                "content_type": "text",
                "page":         idx,   # section index (DOCX has no page numbers)
                "format":       "docx",
            }
        ))

    print(f"[pipeline_text] ✓ DOCX loaded: {len(docs)} sections extracted")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
#  URL / Web Page Loader (via Jina Reader)
# ─────────────────────────────────────────────────────────────────────────────

def _load_url(url: str) -> List[Document]:
    """
    Load a web page using the Jina Reader API.

    Jina Reader works by prefixing any URL with https://r.jina.ai/
    It strips all HTML boilerplate (nav, footer, ads, scripts) and
    returns clean Markdown content ready for RAG ingestion.

    No API key or installation required — completely free.

    Args:
        url: Any public web URL

    Returns:
        List with a single Document containing the page's clean Markdown
    """
    jina_url = JINA_READER_PREFIX + url
    print(f"[pipeline_text] Fetching URL via Jina Reader: {url}")

    try:
        req = urllib.request.Request(
            jina_url,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "text/markdown"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            markdown_content = response.read().decode("utf-8")
    except Exception as e:
        # Fallback: try LangChain WebBaseLoader for simpler static pages
        print(f"[pipeline_text] Jina Reader failed ({e}), trying WebBaseLoader fallback...")
        return _load_url_fallback(url)

    if not markdown_content.strip():
        raise ValueError(f"[pipeline_text] Jina Reader returned empty content for URL: {url}")

    docs = [Document(
        page_content=markdown_content.strip(),
        metadata={
            "source":       url,
            "content_type": "text",
            "page":         0,
            "format":       "web",
        }
    )]

    print(f"[pipeline_text] ✓ URL loaded: {len(markdown_content)} characters extracted")
    return docs


def _load_url_fallback(url: str) -> List[Document]:
    """
    Fallback web loader using LangChain's WebBaseLoader.
    Used when Jina Reader is unavailable (e.g., for intranet URLs).
    Less clean than Jina Reader — may include some HTML noise.
    """
    if WebBaseLoader is None:
        raise ImportError(
            "[pipeline_text] langchain_community is not installed.\n"
            "Run: pip install langchain-community"
        )
    loader = WebBaseLoader(url)
    raw_docs = loader.load()

    for doc in raw_docs:
        doc.metadata["source"]       = url
        doc.metadata["content_type"] = "text"
        doc.metadata["format"]       = "web_fallback"
        doc.metadata.setdefault("page", 0)

    print(f"[pipeline_text] ✓ URL loaded via fallback: {len(raw_docs)} docs")
    return raw_docs


# ─────────────────────────────────────────────────────────────────────────────
#  Markdown / Plain Text Loader
# ─────────────────────────────────────────────────────────────────────────────

def _load_markdown(path: str) -> List[Document]:
    """
    Load a Markdown or plain text file directly.

    No conversion needed — Markdown is already the ideal format for RAG.
    We split on heading boundaries to create logical section Documents.

    Args:
        path: Absolute or relative file path to a .md or .txt file

    Returns:
        List of Documents (one per heading section)
    """
    print(f"[pipeline_text] Loading Markdown/Text: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on heading level 1 or 2
    sections = re.split(r'(?m)^(?=#{1,2} )', content)
    sections = [s.strip() for s in sections if s.strip()]

    # If no headings found (plain .txt), treat entire file as one Document
    if not sections:
        sections = [content.strip()]

    docs = []
    for idx, section in enumerate(sections):
        docs.append(Document(
            page_content=section,
            metadata={
                "source":       path,
                "content_type": "text",
                "page":         idx,
                "format":       Path(path).suffix.lstrip("."),
            }
        ))

    print(f"[pipeline_text] ✓ Markdown loaded: {len(docs)} sections extracted")
    return docs

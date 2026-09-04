# ============================================================
#  ingestion/pipeline_code.py
#
#  PIPELINE 5 — CODE
#
#  HANDLES:
#    - Python (.py), JavaScript/TypeScript (.js, .ts, .jsx, .tsx)
#    - Java, Go, Rust, C/C++, SQL, Shell, YAML, HTML, CSS
#
#  THE KEY RULE:
#    Never split in the middle of a function or class.
#    Code chunks must be semantically whole so the LLM can understand them.
#
#  WHAT IT DOES:
#  1. Reads the source file
#  2. Splits on function/class boundaries (language-aware)
#  3. Attaches metadata: language, filename, chunk_index, symbol names
#  4. Wraps each chunk as a Document
#
#  OUTPUT:
#    List[Document] where page_content is a code chunk string
#    metadata["content_type"] = "code"
# ============================================================

import re
from pathlib import Path
from typing import List

from langchain_core.documents import Document


LANGUAGE_MAP = {
    ".py":   "python",
    ".js":   "javascript",
    ".jsx":  "javascript",
    ".ts":   "typescript",
    ".tsx":  "typescript",
    ".java": "java",
    ".go":   "go",
    ".rs":   "rust",
    ".rb":   "ruby",
    ".cpp":  "cpp",
    ".c":    "c",
    ".h":    "c",
    ".cs":   "csharp",
    ".sql":  "sql",
    ".sh":   "shell",
    ".bash": "shell",
    ".yaml": "yaml",
    ".yml":  "yaml",
    ".toml": "toml",
    ".html": "html",
    ".css":  "css",
    ".scss": "css",
}

# Regex patterns that mark the start of a logical code unit per language
SPLIT_PATTERNS = {
    "python":     r"(?=^(?:def |class |async def ))",
    "javascript": r"(?=^(?:function |class |export (?:default )?(?:function |class |const |let |var )))",
    "typescript": r"(?=^(?:function |class |export (?:default )?(?:function |class |const |let |interface |type )))",
    "java":       r"(?=^(?:public |private |protected |class |interface |enum ))",
    "go":         r"(?=^(?:func |type |package ))",
    "rust":       r"(?=^(?:fn |pub fn |struct |enum |impl |trait |mod ))",
    "sql":        r"(?=(?:^CREATE |^ALTER |^INSERT |^SELECT |^UPDATE |^DELETE |^DROP ))",
}

MAX_CHUNK_CHARS = 3000


def load_code(source: str) -> List[Document]:
    """
    Load a source code file and split it into semantically meaningful chunks.

    Args:
        source: File path to a code file

    Returns:
        List of Documents, one per function/class/logical block
    """
    path = Path(source)
    ext = path.suffix.lower()
    language = LANGUAGE_MAP.get(ext, "text")

    print(f"[pipeline_code] Loading {language} file: {source}")

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1")

    if not content.strip():
        print(f"[pipeline_code] ⚠ File is empty: {source}")
        return []

    chunks = _split_code(content, language)

    docs = []
    for idx, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk:
            continue

        symbol_name = _extract_symbol_name(chunk, language)

        docs.append(Document(
            page_content=chunk,
            metadata={
                "source":       str(source),
                "content_type": "code",
                "page":         idx,
                "format":       ext.lstrip("."),
                "language":     language,
                "chunk_index":  idx,
                "symbol_name":  symbol_name,
            },
        ))

    print(f"[pipeline_code] ✓ Code loaded: {len(docs)} chunks from '{path.name}'")
    return docs


def _split_code(content: str, language: str) -> List[str]:
    """
    Split code on function/class boundaries for the given language.
    Falls back to size-based splitting if no boundaries are found.
    """
    pattern = SPLIT_PATTERNS.get(language)

    if pattern:
        parts = re.split(pattern, content, flags=re.MULTILINE)
        parts = [p for p in parts if p.strip()]
        if len(parts) > 1:
            return _enforce_max_size(parts)

    # Fallback: split on double newlines, then enforce max size
    parts = [p for p in content.split("\n\n") if p.strip()]
    return _enforce_max_size(parts)


def _enforce_max_size(chunks: List[str]) -> List[str]:
    """Split any chunk that exceeds MAX_CHUNK_CHARS without breaking mid-line."""
    result = []
    for chunk in chunks:
        if len(chunk) <= MAX_CHUNK_CHARS:
            result.append(chunk)
            continue
        lines = chunk.split("\n")
        current: List[str] = []
        current_len = 0
        for line in lines:
            if current_len + len(line) > MAX_CHUNK_CHARS and current:
                result.append("\n".join(current))
                current = [line]
                current_len = len(line)
            else:
                current.append(line)
                current_len += len(line) + 1
        if current:
            result.append("\n".join(current))
    return result


def _extract_symbol_name(chunk: str, language: str) -> str:
    """Extract the primary function or class name from a code chunk."""
    patterns = {
        "python":     r"^(?:async )?def (\w+)|^class (\w+)",
        "javascript": r"^(?:export (?:default )?)?(?:async )?function (\w+)|^class (\w+)|^(?:export )?(?:const|let|var) (\w+)",
        "typescript": r"^(?:export (?:default )?)?(?:async )?function (\w+)|^class (\w+)|^interface (\w+)",
        "java":       r"^(?:public |private )?(?:static )?(?:class|interface|enum) (\w+)|^(?:public |private )?(?:static )?\w+ (\w+)\(",
        "go":         r"^func (?:\([^)]*\) )?(\w+)|^type (\w+)",
        "rust":       r"^(?:pub )?fn (\w+)|^(?:pub )?struct (\w+)|^(?:pub )?enum (\w+)",
        "sql":        r"^(?:CREATE|ALTER|DROP)\s+(?:TABLE|VIEW|INDEX)\s+(?:IF NOT EXISTS\s+)?(\w+)",
    }

    regex = patterns.get(language)
    if not regex:
        return ""

    match = re.search(regex, chunk, re.MULTILINE)
    if match:
        return next(g for g in match.groups() if g)
    return ""

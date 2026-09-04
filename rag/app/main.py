"""
FastAPI server for the RAG document ingestion pipeline.

Run:
    uvicorn rag.app.main:app --reload --port 8000

Then open: http://localhost:8000
"""

import sys
import uuid
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.ingestion import ingest

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
UPLOAD_DIR = PROJECT_ROOT / "rag_artifacts" / "uploads"
IMAGE_DIR = PROJECT_ROOT / "rag_artifacts" / "images"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".md", ".txt",
    ".csv", ".json", ".jsonl", ".xlsx", ".xls",
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".cpp", ".c", ".h", ".cs", ".sql", ".sh", ".bash", ".yaml", ".yml",
    ".html", ".css", ".scss", ".toml",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff",
}

MAX_FILE_SIZE_MB = 50

app = FastAPI(
    title="RAG Ingestion Uploader",
    description="Upload documents into the multi-modal RAG ingestion pipeline.",
    version="1.0.0",
)


class UrlIngestRequest(BaseModel):
    url: HttpUrl
    include_images: bool = True
    vision_model: str = "llava"


def _document_preview(content: str, limit: int = 280) -> str:
    text = " ".join(content.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _serialize_documents(docs, source_label: str) -> dict:
    pipeline_counts = Counter(doc.metadata.get("pipeline", "unknown") for doc in docs)
    content_counts = Counter(doc.metadata.get("content_type", "unknown") for doc in docs)

    previews = []
    for doc in docs[:5]:
        previews.append({
            "pipeline": doc.metadata.get("pipeline"),
            "content_type": doc.metadata.get("content_type"),
            "page": doc.metadata.get("page"),
            "skip_chunking": doc.metadata.get("skip_chunking", False),
            "preview": _document_preview(doc.page_content),
        })

    return {
        "source": source_label,
        "total_documents": len(docs),
        "pipelines": dict(pipeline_counts),
        "content_types": dict(content_counts),
        "previews": previews,
    }


@app.get("/")
async def serve_frontend():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "rag-ingestion-uploader"}


@app.get("/api/supported-formats")
async def supported_formats():
    return {
        "extensions": sorted(ALLOWED_EXTENSIONS),
        "csv_modes": ["structured", "table"],
        "notes": {
            "pdf": "Runs text + table + image pipelines",
            "csv": "Use structured for row-level search, table for lookup tables",
            "images": "Requires Ollama with a vision model (e.g. llava) for captions",
        },
    }


@app.post("/api/upload")
async def upload_and_ingest(
    files: list[UploadFile] = File(...),
    csv_mode: str = Form("structured"),
    include_images: bool = Form(True),
    vision_model: str = Form("llava"),
):
    if csv_mode not in {"structured", "table"}:
        raise HTTPException(status_code=400, detail="csv_mode must be 'structured' or 'table'")

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    results = []
    errors = []

    for upload in files:
        filename = upload.filename or "unnamed"
        ext = Path(filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            errors.append({
                "filename": filename,
                "error": f"Unsupported file type: {ext or '(no extension)'}",
            })
            continue

        contents = await upload.read()
        size_mb = len(contents) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            errors.append({
                "filename": filename,
                "error": f"File too large ({size_mb:.1f} MB). Max is {MAX_FILE_SIZE_MB} MB.",
            })
            continue

        saved_name = f"{uuid.uuid4().hex}{ext}"
        saved_path = UPLOAD_DIR / saved_name

        try:
            saved_path.write_bytes(contents)
            docs = ingest(
                str(saved_path),
                csv_mode=csv_mode,
                include_images=include_images,
                vision_model=vision_model,
                image_output_dir=str(IMAGE_DIR),
            )
            result = _serialize_documents(docs, filename)
            result["saved_path"] = str(saved_path)
            results.append(result)
        except Exception as exc:
            errors.append({"filename": filename, "error": str(exc)})
        finally:
            if upload.file:
                upload.file.close()

    if not results and errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "All uploads failed", "errors": errors},
        )

    return {
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


@app.post("/api/ingest-url")
async def ingest_url(request: UrlIngestRequest):
    url = str(request.url)

    try:
        docs = ingest(
            url,
            include_images=request.include_images,
            vision_model=request.vision_model,
            image_output_dir=str(IMAGE_DIR),
        )
        return _serialize_documents(docs, url)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

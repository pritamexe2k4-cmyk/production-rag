# ============================================================
#  ingestion/pipeline_image.py
#
#  PIPELINE 4 — IMAGES & CHARTS
#
#  HANDLES:
#    - Standalone image files (.png, .jpg, .webp, etc.)
#    - Images and charts embedded inside PDFs (extracted via Docling)
#
#  WHAT IT DOES:
#  1. Extracts images from the source (file or PDF)
#  2. Saves each image to disk (rag_artifacts/images/ by default)
#  3. Sends each image to a Vision LLM (Ollama + LLaVA) for captioning
#  4. Stores the caption as page_content (for embedding/search)
#  5. Stores the image file path in metadata (for display to user)
#
#  REQUIRES (optional but recommended):
#    - Ollama running locally: ollama pull llava
#    - Docling for PDF image extraction: pip install docling
#
#  FALLBACK:
#    If Ollama is not available, images are still saved but get a
#    placeholder caption so ingestion does not fail.
#
#  OUTPUT:
#    List[Document] where page_content = vision LLM caption text
#    metadata["image_path"] = path to saved image file
#    metadata["skip_chunking"] = True
# ============================================================

import base64
import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import List

from langchain_core.documents import Document

DEFAULT_IMAGE_DIR = Path("rag_artifacts/images")
DEFAULT_VISION_MODEL = "llava"
OLLAMA_URL = "http://localhost:11434/api/generate"

CAPTION_PROMPT = (
    "Describe this image in detail for a search index. "
    "If it is a chart or graph, include all data values, axis labels, "
    "and trends. If it is a diagram, explain what it shows and how parts connect. "
    "If it contains text, transcribe it. Be factual and thorough."
)


def load_images(
    source: str,
    vision_model: str = DEFAULT_VISION_MODEL,
    output_dir: str | None = None,
) -> List[Document]:
    """
    Extract images from a file and generate text captions for each.

    Args:
        source:       Path to an image file or a PDF containing images
        vision_model: Ollama vision model name (default: "llava")
        output_dir:   Directory to save extracted images

    Returns:
        List of Documents with caption text and image_path metadata
    """
    ext = Path(source).suffix.lower()
    save_dir = Path(output_dir) if output_dir else DEFAULT_IMAGE_DIR
    save_dir.mkdir(parents=True, exist_ok=True)

    if ext == ".pdf":
        return _extract_pdf_images(source, save_dir, vision_model)

    if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}:
        return [_caption_single_image(source, save_dir, vision_model, index=0)]

    raise ValueError(
        f"[pipeline_image] Unsupported format: '{ext}'. "
        f"Supported: .pdf or image files (.png, .jpg, .webp, etc.)"
    )


def _extract_pdf_images(
    path: str,
    save_dir: Path,
    vision_model: str,
) -> List[Document]:
    """Extract all pictures from a PDF using Docling and caption each one."""
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling_core.types.doc import PictureItem
    except ImportError:
        raise ImportError(
            "[pipeline_image] Docling is not installed.\n"
            "Run: pip install docling"
        )

    print(f"[pipeline_image] Extracting images from PDF: {path}")

    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True
    pipeline_options.images_scale = 2.0

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    result = converter.convert(path)
    doc_filename = Path(path).stem

    docs: List[Document] = []
    picture_counter = 0

    for element, _level in result.document.iterate_items():
        if not isinstance(element, PictureItem):
            continue

        picture_counter += 1
        pil_image = element.get_image(result.document)
        if pil_image is None:
            print(f"[pipeline_image] ⚠ Could not extract picture #{picture_counter}, skipping")
            continue

        image_filename = save_dir / f"{doc_filename}-picture-{picture_counter}.png"
        pil_image.save(image_filename, format="PNG")

        page_num = 0
        if hasattr(element, "prov") and element.prov:
            page_num = element.prov[0].page_no

        caption = _caption_with_ollama(str(image_filename), vision_model)
        content = f"**Image from page {page_num}**\n\n{caption}"

        docs.append(Document(
            page_content=content,
            metadata={
                "source":        path,
                "content_type":  "image",
                "page":          page_num,
                "image_path":    str(image_filename),
                "image_index":   picture_counter,
                "format":        "pdf",
                "vision_model":  vision_model,
                "skip_chunking": True,
            },
        ))

    print(f"[pipeline_image] ✓ PDF image extraction: {len(docs)} images captioned")
    return docs


def _caption_single_image(
    path: str,
    save_dir: Path,
    vision_model: str,
    index: int,
) -> Document:
    """Caption a standalone image file."""
    src = Path(path)
    dest = save_dir / src.name
    if src.resolve() != dest.resolve():
        shutil.copy2(src, dest)

    print(f"[pipeline_image] Captioning image: {path}")
    caption = _caption_with_ollama(str(dest), vision_model)

    return Document(
        page_content=caption,
        metadata={
            "source":        path,
            "content_type":  "image",
            "page":          0,
            "image_path":    str(dest),
            "image_index":   index,
            "format":        src.suffix.lstrip("."),
            "vision_model":  vision_model,
            "skip_chunking": True,
        },
    )


def _caption_with_ollama(image_path: str, model: str) -> str:
    """
    Send an image to Ollama's vision API and return the generated caption.
    Returns a placeholder string if Ollama is unavailable.
    """
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
    except OSError as e:
        return f"[Image could not be read: {e}]"

    payload = json.dumps({
        "model":  model,
        "prompt": CAPTION_PROMPT,
        "images": [img_b64],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        caption = result.get("response", "").strip()
        if caption:
            return caption
        return f"[Vision model '{model}' returned an empty caption for {Path(image_path).name}]"

    except urllib.error.URLError:
        print(
            f"[pipeline_image] ⚠ Ollama not reachable at {OLLAMA_URL}. "
            f"Image saved but not captioned. Run: ollama pull {model}"
        )
        return (
            f"[Image: {Path(image_path).name} — Ollama vision model not available. "
            f"Start Ollama and run 'ollama pull {model}' to enable captioning.]"
        )
    except Exception as e:
        print(f"[pipeline_image] ⚠ Caption failed for {image_path}: {e}")
        return f"[Image: {Path(image_path).name} — caption generation failed: {e}]"

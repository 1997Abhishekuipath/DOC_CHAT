"""Document text extraction.

Supported formats (feature-flag gated for new types):
  - PDF        (always, with optional OCR fallback for scanned pages)
  - DOCX       (always)
  - TXT / MD   (always)
  - PPTX       (ENABLE_PPTX_SUPPORT)
  - XLSX / CSV (ENABLE_EXCEL_SUPPORT)
  - Images     (ENABLE_IMAGE_OCR)  - .png / .jpg / .jpeg
  - Scanned PDF fallback (ENABLE_SCANNED_PDF_OCR)
  - Google Slides (ENABLE_GOOGLE_SLIDES) - STUB only

Each returned unit carries (unit_number, text) where unit_number is:
  - page number for PDF
  - slide number for PPTX
  - sheet-row-group number for XLSX (always 1 per sheet)
  - always 1 for DOCX/TXT/MD/CSV/image
"""
from __future__ import annotations

import csv as _csv
from pathlib import Path
from typing import List, Tuple

from core.config import is_enabled

# Always-supported (core MVP)
_CORE_EXTS = {".pdf", ".docx", ".txt", ".md"}

# Feature-flagged
_PPTX_EXTS = {".pptx"}
_EXCEL_EXTS = {".xlsx", ".csv"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
_GSLIDES_EXTS: set[str] = set()  # google slides are URL-based, not file-based

# Full catalog across all possible supported types (used for frontend / docs)
ALL_KNOWN_EXTENSIONS = _CORE_EXTS | _PPTX_EXTS | _EXCEL_EXTS | _IMAGE_EXTS


class UnsupportedFormatError(ValueError):
    """Raised when a file type is not enabled or not supported."""


def current_supported_extensions() -> set[str]:
    """Extensions currently accepted given active feature flags."""
    exts = set(_CORE_EXTS)
    if is_enabled("ENABLE_PPTX_SUPPORT"):
        exts |= _PPTX_EXTS
    if is_enabled("ENABLE_EXCEL_SUPPORT"):
        exts |= _EXCEL_EXTS
    if is_enabled("ENABLE_IMAGE_OCR"):
        exts |= _IMAGE_EXTS
    return exts


# Backwards-compat alias used elsewhere in the codebase
SUPPORTED_EXTENSIONS = current_supported_extensions()


def file_type_label(filename: str) -> str:
    """Human-friendly file type tag, stored in document metadata."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext == ".docx":
        return "docx"
    if ext == ".pptx":
        return "pptx"
    if ext == ".xlsx":
        return "xlsx"
    if ext == ".csv":
        return "csv"
    if ext in (".png", ".jpg", ".jpeg"):
        return "image"
    if ext == ".md":
        return "markdown"
    if ext == ".txt":
        return "text"
    return ext.lstrip(".") or "unknown"


def extract_text(file_path: Path, filename: str) -> List[Tuple[int, str]]:
    """Dispatch extraction. Raises UnsupportedFormatError for disabled/unknown types."""
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(file_path)
    if ext == ".docx":
        return _extract_docx(file_path)
    if ext in (".txt", ".md"):
        return _extract_text(file_path)

    if ext == ".pptx":
        if not is_enabled("ENABLE_PPTX_SUPPORT"):
            raise UnsupportedFormatError(
                "PPTX support is disabled. Enable ENABLE_PPTX_SUPPORT to ingest PowerPoint files."
            )
        return _extract_pptx(file_path)

    if ext == ".xlsx":
        if not is_enabled("ENABLE_EXCEL_SUPPORT"):
            raise UnsupportedFormatError(
                "Excel support is disabled. Enable ENABLE_EXCEL_SUPPORT to ingest .xlsx files."
            )
        return _extract_xlsx(file_path)

    if ext == ".csv":
        if not is_enabled("ENABLE_EXCEL_SUPPORT"):
            raise UnsupportedFormatError(
                "CSV support is disabled. Enable ENABLE_EXCEL_SUPPORT to ingest .csv files."
            )
        return _extract_csv(file_path)

    if ext in _IMAGE_EXTS:
        if not is_enabled("ENABLE_IMAGE_OCR"):
            raise UnsupportedFormatError(
                "Image OCR is disabled. Enable ENABLE_IMAGE_OCR to ingest images."
            )
        return _extract_image_ocr(file_path)

    raise UnsupportedFormatError(f"Unsupported file type: {ext}")


# ---------------------------------------------------------------------------
# PDF (with optional OCR fallback for scanned / image-based PDFs)
# ---------------------------------------------------------------------------
def _extract_pdf(file_path: Path) -> List[Tuple[int, str]]:
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    result: List[Tuple[int, str]] = []
    empty_pages: List[int] = []

    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            result.append((i, text))
        else:
            empty_pages.append(i)

    # If no text at all, attempt OCR fallback on every page (scanned PDF).
    # If SOME pages extracted text but others didn't, leave as-is — mixed PDFs
    # usually have blank / illustration pages and running OCR on every empty
    # page would be slow and noisy. Adjust via future enhancement if needed.
    if not result and empty_pages and is_enabled("ENABLE_SCANNED_PDF_OCR"):
        return _ocr_pdf_pages(file_path, empty_pages)

    return result


def _ocr_pdf_pages(file_path: Path, page_numbers: List[int]) -> List[Tuple[int, str]]:
    """Render selected PDF pages to images and run tesseract OCR."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        return []

    # pdf2image's first_page/last_page are 1-indexed inclusive.
    first = min(page_numbers)
    last = max(page_numbers)
    try:
        images = convert_from_path(str(file_path), dpi=200, first_page=first, last_page=last)
    except Exception:
        return []

    wanted = set(page_numbers)
    out: List[Tuple[int, str]] = []
    for offset, img in enumerate(images):
        page_num = first + offset
        if page_num not in wanted:
            continue
        try:
            text = pytesseract.image_to_string(img) or ""
        except Exception:
            text = ""
        if text.strip():
            out.append((page_num, text.strip()))
    return out


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------
def _extract_docx(file_path: Path) -> List[Tuple[int, str]]:
    from docx import Document as DocxDocument

    doc = DocxDocument(str(file_path))
    parts: List[str] = []
    for p in doc.paragraphs:
        if p.text.strip():
            parts.append(p.text)
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            parts.append("\t".join(cells))
    text = "\n".join(parts)
    return [(1, text)] if text.strip() else []


# ---------------------------------------------------------------------------
# TXT / MD
# ---------------------------------------------------------------------------
def _extract_text(file_path: Path) -> List[Tuple[int, str]]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return [(1, text)] if text.strip() else []


# ---------------------------------------------------------------------------
# PPTX — basic slide text, one unit per slide
# ---------------------------------------------------------------------------
def _extract_pptx(file_path: Path) -> List[Tuple[int, str]]:
    from pptx import Presentation

    prs = Presentation(str(file_path))
    out: List[Tuple[int, str]] = []
    for i, slide in enumerate(prs.slides, start=1):
        fragments: List[str] = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    line = "".join(r.text for r in para.runs).strip()
                    if line:
                        fragments.append(line)
        # Notes (speaker notes) append for better grounding
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = (slide.notes_slide.notes_text_frame.text or "").strip()
            if notes:
                fragments.append(f"[Notes] {notes}")
        text = "\n".join(fragments).strip()
        if text:
            out.append((i, text))
    return out


# ---------------------------------------------------------------------------
# XLSX — rows as tab-separated plain text; one unit per sheet
# ---------------------------------------------------------------------------
def _extract_xlsx(file_path: Path) -> List[Tuple[int, str]]:
    from openpyxl import load_workbook

    wb = load_workbook(filename=str(file_path), read_only=True, data_only=True)
    out: List[Tuple[int, str]] = []
    for idx, sheet_name in enumerate(wb.sheetnames, start=1):
        ws = wb[sheet_name]
        lines: List[str] = [f"Sheet: {sheet_name}"]
        for row in ws.iter_rows(values_only=True):
            cells = ["" if c is None else str(c).strip() for c in row]
            if any(cells):
                lines.append("\t".join(cells))
        text = "\n".join(lines)
        if text.strip() and len(lines) > 1:
            out.append((idx, text))
    return out


# ---------------------------------------------------------------------------
# CSV — rows as tab-separated text
# ---------------------------------------------------------------------------
def _extract_csv(file_path: Path) -> List[Tuple[int, str]]:
    lines: List[str] = []
    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = _csv.reader(f)
        for row in reader:
            if any((c or "").strip() for c in row):
                lines.append("\t".join(row))
    text = "\n".join(lines)
    return [(1, text)] if text.strip() else []


# ---------------------------------------------------------------------------
# Image OCR
# ---------------------------------------------------------------------------
def _extract_image_ocr(file_path: Path) -> List[Tuple[int, str]]:
    """Extract text from image using Tesseract OCR.
    Falls back to a metadata description if no text is found, so the image
    is still indexed and discoverable by filename.
    """
    ocr_text = ""
    try:
        from PIL import Image
        import pytesseract
        try:
            with Image.open(str(file_path)) as img:
                # Improve OCR accuracy: convert to grayscale
                gray = img.convert("L")
                ocr_text = pytesseract.image_to_string(gray) or ""
                ocr_text = ocr_text.strip()
        except Exception:
            ocr_text = ""
    except ImportError:
        pass

    if ocr_text:
        return [(1, ocr_text)]

    # Fallback: index with filename metadata so the image is still discoverable
    name = file_path.stem
    fallback = f"[Image file: {name}] This is an image document. No machine-readable text was detected."
    try:
        from PIL import Image
        with Image.open(str(file_path)) as img:
            w, h = img.size
            mode = img.mode
            fallback = (
                f"[Image file: {name}] Format: {img.format or 'unknown'}, "
                f"Size: {w}x{h}px, Mode: {mode}. "
                f"No machine-readable text was detected by OCR."
            )
    except Exception:
        pass
    return [(1, fallback)]


# ---------------------------------------------------------------------------
# Google Slides — STUB (API-ready scaffold, not implemented)
# ---------------------------------------------------------------------------
def extract_google_slides(presentation_id: str) -> List[Tuple[int, str]]:
    """Stub for Google Slides ingestion.

    Wiring this up requires:
      - Google API credentials (service account or OAuth)
      - google-api-python-client + google-auth libraries
      - presentations.get() call, walk each slide's pageElements for textRun content
    When ENABLE_GOOGLE_SLIDES is flipped on, implement here and call from the
    /v2/documents/ingest-google-slides endpoint (also stubbed below).
    """
    if not is_enabled("ENABLE_GOOGLE_SLIDES"):
        raise UnsupportedFormatError(
            "Google Slides ingestion is disabled. Enable ENABLE_GOOGLE_SLIDES and configure Google API credentials."
        )
    raise NotImplementedError(
        "Google Slides ingestion is not yet implemented. "
        "Flag is on but integration stub has no credentials configured."
    )

"""Document text extraction for PDF, DOCX, TXT, MD."""
import io
from pathlib import Path
from typing import List, Tuple

from pypdf import PdfReader
from docx import Document as DocxDocument


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def extract_text(file_path: Path, filename: str) -> List[Tuple[int, str]]:
    """
    Returns list of (page_number, text) tuples.
    For non-paginated formats, page_number is always 1.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(file_path)
    if ext == ".docx":
        return _extract_docx(file_path)
    if ext in (".txt", ".md"):
        return _extract_text(file_path)
    raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(file_path: Path) -> List[Tuple[int, str]]:
    reader = PdfReader(str(file_path))
    result = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            result.append((i, text))
    return result


def _extract_docx(file_path: Path) -> List[Tuple[int, str]]:
    doc = DocxDocument(str(file_path))
    parts = []
    for p in doc.paragraphs:
        if p.text.strip():
            parts.append(p.text)
    # Tables as tab-separated rows
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            parts.append("\t".join(cells))
    text = "\n".join(parts)
    return [(1, text)] if text.strip() else []


def _extract_text(file_path: Path) -> List[Tuple[int, str]]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return [(1, text)] if text.strip() else []

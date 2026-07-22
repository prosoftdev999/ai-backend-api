from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedDocumentTypeError(ValueError):
    pass


def extract_text(file_path: Path, content_type: str) -> str:
    suffix = file_path.suffix.lower()

    if content_type == "application/pdf" or suffix == ".pdf":
        return _extract_pdf(file_path)

    if (
        content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or suffix == ".docx"
    ):
        return _extract_docx(file_path)

    if content_type.startswith("text/") or suffix in {".txt", ".md", ".markdown"}:
        return file_path.read_text(encoding="utf-8", errors="replace")

    raise UnsupportedDocumentTypeError(
        f"Unsupported document type: {content_type or suffix}"
    )


def _extract_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())

    return "\n\n".join(pages)


def _extract_docx(file_path: Path) -> str:
    document = DocxDocument(str(file_path))
    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]
    return "\n\n".join(paragraphs)

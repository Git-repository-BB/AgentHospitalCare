"""Document storage, lightweight parsing, and duplicate detection."""
from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.database.models import Document

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


def _detect_doc_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    return suffix or "unknown"


def store_document(db: Session, patient_id: str, filename: str, content: bytes) -> Document:
    """Persist an uploaded file to disk and record its metadata, flagging duplicates."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    content_hash = hashlib.sha256(content).hexdigest()

    is_duplicate = (
        db.query(Document)
        .filter(Document.patient_id == patient_id, Document.content_hash == content_hash)
        .first()
        is not None
    )

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    safe_name = f"{patient_id}_{timestamp}_{Path(filename).name}"
    dest_path = UPLOADS_DIR / safe_name
    dest_path.write_bytes(content)

    document = Document(
        patient_id=patient_id,
        filename=filename,
        path=str(dest_path),
        doc_type=_detect_doc_type(filename),
        content_hash=content_hash,
        is_duplicate=is_duplicate,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def parse_document(path: str) -> dict:
    """Extract lightweight metadata from a stored document (page count for PDFs, size for others)."""
    file_path = Path(path)
    info: dict = {
        "filename": file_path.name,
        "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
    }
    if file_path.suffix.lower() == ".pdf":
        try:
            import fitz  # PyMuPDF

            with fitz.open(file_path) as pdf:
                info["page_count"] = pdf.page_count
        except Exception:
            info["page_count"] = None
    return info


def list_documents(db: Session, patient_id: str) -> list[Document]:
    return db.query(Document).filter(Document.patient_id == patient_id).all()

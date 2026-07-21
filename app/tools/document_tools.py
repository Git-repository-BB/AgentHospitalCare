"""Tools the Document Agent uses to parse, store, and de-duplicate uploaded files."""
from __future__ import annotations

from pathlib import Path

from crewai.tools import tool

from app.database.db import SessionLocal
from app.services import document_service


@tool("Document Parser Tool")
def document_parser_tool(file_path: str) -> str:
    """Extract lightweight metadata (size, page count for PDFs) from a stored document.

    Args:
        file_path: Absolute path to a previously stored document.

    Returns:
        A human-readable summary of the file's metadata.
    """
    info = document_service.parse_document(file_path)
    return ", ".join(f"{key}={value}" for key, value in info.items())


@tool("Document Storage Tool")
def document_storage_tool(patient_id: str, file_path: str) -> str:
    """Store an already-uploaded file (given its temp path) against a patient record.

    Args:
        patient_id: Identifier of the patient the document belongs to.
        file_path: Path to the file on disk to be stored/registered.

    Returns:
        A string "document_id|is_duplicate" describing the stored record.
    """
    db = SessionLocal()
    try:
        path = Path(file_path)
        content = path.read_bytes()
        document = document_service.store_document(db, patient_id, path.name, content)
        return f"{document.id}|{document.is_duplicate}"
    finally:
        db.close()


@tool("Duplicate Detection Tool")
def duplicate_detection_tool(patient_id: str, file_path: str) -> str:
    """Check whether a file's content already exists for a patient (by content hash).

    Args:
        patient_id: Identifier of the patient the document belongs to.
        file_path: Path to the file to check.

    Returns:
        "duplicate" or "unique".
    """
    import hashlib

    db = SessionLocal()
    try:
        content = Path(file_path).read_bytes()
        content_hash = hashlib.sha256(content).hexdigest()
        existing = document_service.list_documents(db, patient_id)
        is_duplicate = any(doc.content_hash == content_hash for doc in existing)
        return "duplicate" if is_duplicate else "unique"
    finally:
        db.close()

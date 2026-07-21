from app.services import document_service


def test_store_document_detects_duplicates(db_session, tmp_path) -> None:
    document_service.UPLOADS_DIR = tmp_path / "uploads"

    first = document_service.store_document(db_session, "patient-1", "report.txt", b"hello world")
    second = document_service.store_document(db_session, "patient-1", "report-copy.txt", b"hello world")
    different = document_service.store_document(db_session, "patient-1", "other.txt", b"different content")

    assert first.is_duplicate is False
    assert second.is_duplicate is True
    assert different.is_duplicate is False


def test_parse_document_reports_size(tmp_path) -> None:
    file_path = tmp_path / "note.txt"
    file_path.write_bytes(b"some content")

    info = document_service.parse_document(str(file_path))

    assert info["filename"] == "note.txt"
    assert info["size_bytes"] == len(b"some content")

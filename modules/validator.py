from pathlib import Path
from config import MAX_FILE_SIZE_MB, MAX_PAGE_COUNT


def validate(pdf_path: str | Path, max_size_mb: float = None, max_pages: int = None) -> dict:
    path = Path(pdf_path)
    max_size = max_size_mb or MAX_FILE_SIZE_MB
    max_pg = max_pages or MAX_PAGE_COUNT
    errors = []

    # File size check
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size:
        errors.append(f"File size {size_mb:.1f} MB exceeds maximum {max_size} MB")

    # Try to open as PDF
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))

        # Password-protected check
        if reader.is_encrypted:
            errors.append("Document is password-protected")
            return {"valid": False, "errors": errors, "pageCount": None}

        # Empty document check
        page_count = len(reader.pages)
        if page_count == 0:
            errors.append("Document has no pages")

        # Page count check
        if page_count > max_pg:
            errors.append(f"Page count {page_count} exceeds maximum {max_pg}")

    except Exception as e:
        errors.append(f"Document appears corrupted or unreadable: {e}")
        return {"valid": False, "errors": errors, "pageCount": None}

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "pageCount": page_count,
        "sizeMB": round(size_mb, 2),
    }

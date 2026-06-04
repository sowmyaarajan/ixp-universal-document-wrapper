from pathlib import Path
from converter.utils.file_detector import FileDetector

# Extension → canonical type name
_EXT_MAP = {
    ".pdf":  "PDF",
    ".docx": "DOCX", ".doc": "DOC",
    ".xlsx": "XLSX", ".xls": "XLS",
    ".pptx": "PPTX", ".ppt": "PPT",
    ".csv":  "CSV",
    ".png":  "PNG",  ".jpg": "JPG", ".jpeg": "JPEG",
    ".tiff": "TIFF", ".tif": "TIFF",
    ".bmp":  "BMP",  ".gif": "GIF", ".webp": "WEBP",
    ".zip":  "ZIP",
    ".msg":  "MSG",
    ".eml":  "EML",
}


def analyze(file_path: str | Path) -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = FileDetector.get_extension(path)
    size_bytes = path.stat().st_size

    return {
        "fileName": path.name,
        "extension": ext,
        "fileType": _EXT_MAP.get(ext, ext.lstrip(".").upper()),
        "sizeBytes": size_bytes,
        "sizeMB": round(size_bytes / (1024 * 1024), 2),
        "isAlreadyPDF": FileDetector.is_pdf(path),
        "magicType": FileDetector.detect_magic(path),
    }

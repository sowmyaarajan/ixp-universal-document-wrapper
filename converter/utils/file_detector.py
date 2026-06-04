from pathlib import Path


class FileDetector:

    _MAGIC: dict[bytes, str] = {
        b"\x50\x4B\x03\x04": "zip_based",   # DOCX/XLSX/PPTX
        b"\xD0\xCF\x11\xE0": "ole2",         # Legacy .doc/.xls/.ppt
        b"\xFF\xD8\xFF":      "jpeg",
        b"\x89PNG":           "png",
        b"\x47\x49\x46":      "gif",
        b"RIFF":              "riff",         # WebP container
        b"II\x2A\x00":        "tiff_le",
        b"MM\x00\x2A":        "tiff_be",
        b"BM":                "bmp",
        b"%PDF":              "pdf",
    }

    @staticmethod
    def get_extension(file_path: Path) -> str:
        return file_path.suffix.lower()

    @staticmethod
    def is_pdf(file_path: Path) -> bool:
        try:
            with open(file_path, "rb") as f:
                return f.read(4) == b"%PDF"
        except OSError:
            return False

    @classmethod
    def detect_magic(cls, file_path: Path) -> str | None:
        try:
            with open(file_path, "rb") as f:
                header = f.read(8)
            for magic, fmt in cls._MAGIC.items():
                if header.startswith(magic):
                    return fmt
        except OSError:
            pass
        return None

import logging
import shutil
from pathlib import Path

from converter.converters.base_converter import BaseConverter
from converter.converters.docx_converter import DocxConverter
from converter.converters.office_converter import OfficeConverter
from converter.converters.image_converter import ImageConverter
from converter.exceptions import (
    ConversionError,
    UnsupportedFormatError,
)
from converter.utils.file_detector import FileDetector
from converter.utils.libreoffice_finder import LibreOfficeFinder

logger = logging.getLogger(__name__)


class DocumentConverter:
    """
    Unified PDF converter — uses LibreOffice for Office formats, Pillow for images.
    No MS Office installation required.

    Usage:
        converter = DocumentConverter()
        pdf_path = converter.convert_to_pdf("invoice.docx", "invoice.pdf")
    """

    def __init__(self):
        self._converters: list[BaseConverter] = [
            DocxConverter(),      # DOCX/DOC → docx2pdf → LibreOffice fallback
            OfficeConverter(),    # XLSX/XLS/PPTX/PPT/CSV → LibreOffice
            ImageConverter(),     # PNG/JPG/BMP/GIF/TIFF/WebP → Pillow
        ]

    def convert_to_pdf(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
    ) -> Path:
        input_path = Path(input_path).resolve()
        resolved_output = self._resolve_output_path(input_path, output_path)

        if FileDetector.is_pdf(input_path):
            logger.info("Input is already a PDF, copying to %s", resolved_output)
            resolved_output.parent.mkdir(parents=True, exist_ok=True)
            if input_path != resolved_output:
                shutil.copy2(input_path, resolved_output)
            return resolved_output

        ext = FileDetector.get_extension(input_path)
        converter = self._resolve_converter(ext)
        return converter.convert(input_path, resolved_output)

    def is_already_pdf(self, input_path: str | Path) -> bool:
        return FileDetector.is_pdf(Path(input_path))

    def get_supported_extensions(self) -> set[str]:
        result: set[str] = set()
        for c in self._converters:
            result |= c.SUPPORTED_EXTENSIONS
        return result

    @staticmethod
    def check_dependencies() -> dict[str, bool]:
        deps: dict[str, bool] = {}

        try:
            import PIL  # noqa: F401
            deps["pillow"] = True
        except ImportError:
            deps["pillow"] = False

        try:
            import docx2pdf  # noqa: F401
            deps["docx2pdf"] = True
        except ImportError:
            deps["docx2pdf"] = False

        deps["libreoffice"] = LibreOfficeFinder.is_available()

        return deps

    def _resolve_converter(self, extension: str) -> BaseConverter:
        for c in self._converters:
            if c.supports(extension):
                return c
        raise UnsupportedFormatError(
            f"No converter registered for '{extension}'. "
            f"Supported: {sorted(self.get_supported_extensions())}"
        )

    @staticmethod
    def _resolve_output_path(input_path: Path, output_path: str | Path | None) -> Path:
        if output_path is None:
            return input_path.with_suffix(".pdf")
        return Path(output_path).resolve()

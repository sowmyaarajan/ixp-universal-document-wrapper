import logging
from pathlib import Path

from converter.converters.base_converter import BaseConverter
from converter.exceptions import ConversionError

logger = logging.getLogger(__name__)


class DocxConverter(BaseConverter):

    SUPPORTED_EXTENSIONS = {".docx", ".doc"}

    def convert(self, input_path: Path, output_path: Path) -> Path:
        self._validate_input(input_path)
        logger.info("Converting DOCX %s -> %s", input_path, output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            return self._convert_via_docx2pdf(input_path, output_path)
        except Exception as e:
            logger.warning("docx2pdf failed (%s), falling back to LibreOffice", e)
            return self._convert_via_libreoffice(input_path, output_path)

    def _convert_via_docx2pdf(self, input_path: Path, output_path: Path) -> Path:
        try:
            from docx2pdf import convert
        except ImportError:
            raise ConversionError("docx2pdf is not installed. Run: pip install docx2pdf")

        try:
            convert(str(input_path), str(output_path))
        except Exception as e:
            raise ConversionError(f"docx2pdf conversion failed for {input_path}: {e}") from e

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ConversionError(f"docx2pdf produced no output for {input_path}")

        return output_path

    def _convert_via_libreoffice(self, input_path: Path, output_path: Path) -> Path:
        from converter.converters.office_converter import OfficeConverter
        return OfficeConverter().convert(input_path, output_path)

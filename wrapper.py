import logging
import tempfile
import time
from pathlib import Path

from converter import DocumentConverter
from modules import file_analyzer, validator, ixp_connector, response_formatter
import config

logger = logging.getLogger(__name__)


class IXPWrapper:

    def __init__(self):
        self._converter = DocumentConverter()

    def process(self, file_path: str | Path, document_type: str = None) -> dict:
        start = time.time()
        file_path = Path(file_path).resolve()

        logger.info("Processing: %s", file_path.name)

        # Module 1: Analyze
        analysis = file_analyzer.analyze(file_path)
        logger.info("File type: %s  Size: %s MB", analysis["fileType"], analysis["sizeMB"])

        # Module 2: Normalize to PDF
        with tempfile.TemporaryDirectory(prefix="ixp_wrap_") as tmp:
            pdf_path = Path(tmp) / (file_path.stem + ".pdf")
            normalized_pdf = self._converter.convert_to_pdf(file_path, pdf_path)
            logger.info("Normalized to PDF: %s", normalized_pdf)

            # Module 3: Validate
            validation = validator.validate(normalized_pdf)
            if not validation["valid"]:
                elapsed = int((time.time() - start) * 1000)
                return response_formatter.format_response(
                    analysis, validation, {}, normalized_pdf, elapsed
                )
            logger.info("Validation passed — %d pages", validation["pageCount"])

            # Module 5: IXP
            ixp_result = ixp_connector.process(normalized_pdf, document_type)
            logger.info("IXP processing complete")

            # Module 6: Format
            elapsed = int((time.time() - start) * 1000)
            result = response_formatter.format_response(
                analysis, validation, ixp_result, normalized_pdf, elapsed
            )

        logger.info("Done in %d ms", elapsed)
        return result

    def get_supported_extensions(self) -> list[str]:
        return sorted(self._converter.get_supported_extensions())

    @staticmethod
    def check_dependencies() -> dict:
        return {
            **DocumentConverter.check_dependencies(),
            "ixp_configured": config.ixp_configured(),
        }

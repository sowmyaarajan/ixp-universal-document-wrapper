import logging
import subprocess
import tempfile
import uuid
import sys
from pathlib import Path

from converter.converters.base_converter import BaseConverter
from converter.exceptions import ConversionError, ConversionTimeoutError
from converter.utils.libreoffice_finder import LibreOfficeFinder

logger = logging.getLogger(__name__)


class OfficeConverter(BaseConverter):
    """LibreOffice subprocess converter for XLSX, XLS, PPTX, PPT."""

    SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".pptx", ".ppt", ".csv"}
    DEFAULT_TIMEOUT = 120

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self._soffice: Path | None = None

    def _get_soffice(self) -> Path:
        if self._soffice is None:
            self._soffice = LibreOfficeFinder.find()
        return self._soffice

    def convert(self, input_path: Path, output_path: Path) -> Path:
        self._validate_input(input_path)
        soffice = self._get_soffice()
        logger.info("Converting %s -> %s via LibreOffice", input_path, output_path)

        with tempfile.TemporaryDirectory(prefix="ixp_lo_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            profile_dir = tmp_path / f"profile_{uuid.uuid4().hex}"
            profile_dir.mkdir()
            out_dir = tmp_path / "output"
            out_dir.mkdir()

            cmd = self._build_command(input_path, out_dir, profile_dir, soffice)
            self._run_subprocess(cmd)

            lo_output = out_dir / (input_path.stem + ".pdf")
            if not lo_output.exists() or lo_output.stat().st_size == 0:
                raise ConversionError(
                    f"LibreOffice did not produce output for {input_path}. "
                    "File may be password-protected or corrupted."
                )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            lo_output.replace(output_path)

        logger.info("Office conversion complete: %s", output_path)
        return output_path

    def _build_command(self, input_path: Path, out_dir: Path, profile_dir: Path, soffice: Path) -> list[str]:
        profile_uri = profile_dir.as_uri()
        return [
            str(soffice),
            "--headless",
            f"-env:UserInstallation={profile_uri}",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(input_path),
        ]

    def _run_subprocess(self, cmd: list[str]) -> None:
        logger.debug("Running: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise ConversionTimeoutError(
                f"LibreOffice conversion timed out after {self.timeout}s"
            ) from e

        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")
            raise ConversionError(f"LibreOffice failed (code {result.returncode}): {stderr}")

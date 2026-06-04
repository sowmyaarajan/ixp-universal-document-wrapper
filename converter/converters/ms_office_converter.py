import logging
from pathlib import Path

from converter.converters.base_converter import BaseConverter
from converter.exceptions import ConversionError, ConverterNotAvailableError

logger = logging.getLogger(__name__)

# COM export constants
_WD_EXPORT_FORMAT_PDF = 17
_XL_TYPE_PDF = 0
_PP_SAVE_AS_PDF = 32


class MSOfficeConverter(BaseConverter):
    """Converts DOCX, XLSX, PPTX to PDF using MS Office COM automation (win32com)."""

    SUPPORTED_EXTENSIONS = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".csv"}

    def convert(self, input_path: Path, output_path: Path) -> Path:
        self._validate_input(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        ext = input_path.suffix.lower()
        if ext in {".docx", ".doc"}:
            return self._convert_word(input_path, output_path)
        elif ext in {".xlsx", ".xls", ".csv"}:
            return self._convert_excel(input_path, output_path)
        elif ext in {".pptx", ".ppt"}:
            return self._convert_powerpoint(input_path, output_path)
        else:
            raise ConversionError(f"MSOfficeConverter does not handle extension: {ext}")

    def _convert_word(self, input_path: Path, output_path: Path) -> Path:
        logger.info("Converting DOCX via Word COM: %s", input_path)
        win32com, pythoncom = _get_com_modules()
        pythoncom.CoInitialize()
        app = win32com.client.Dispatch("Word.Application")
        app.Visible = False
        doc = None
        try:
            doc = app.Documents.Open(str(input_path.resolve()))
            doc.ExportAsFixedFormat(
                OutputFileName=str(output_path.resolve()),
                ExportFormat=_WD_EXPORT_FORMAT_PDF,
            )
        except Exception as e:
            raise ConversionError(f"Word COM conversion failed for {input_path}: {e}") from e
        finally:
            if doc is not None:
                try:
                    doc.Close(False)
                except Exception:
                    pass
            try:
                app.Quit()
            except Exception:
                pass
            pythoncom.CoUninitialize()

        _verify_output(output_path, input_path)
        logger.info("Word conversion complete: %s", output_path)
        return output_path

    def _convert_excel(self, input_path: Path, output_path: Path) -> Path:
        logger.info("Converting XLSX via Excel COM: %s", input_path)
        win32com, pythoncom = _get_com_modules()
        pythoncom.CoInitialize()
        app = win32com.client.Dispatch("Excel.Application")
        app.Visible = False
        app.DisplayAlerts = False
        wb = None
        try:
            wb = app.Workbooks.Open(str(input_path.resolve()))
            wb.ExportAsFixedFormat(
                Type=_XL_TYPE_PDF,
                Filename=str(output_path.resolve()),
                IncludeDocProperties=True,
                IgnorePrintAreas=False,
            )
        except Exception as e:
            raise ConversionError(f"Excel COM conversion failed for {input_path}: {e}") from e
        finally:
            if wb is not None:
                try:
                    wb.Close(False)
                except Exception:
                    pass
            try:
                app.Quit()
            except Exception:
                pass
            pythoncom.CoUninitialize()

        _verify_output(output_path, input_path)
        logger.info("Excel conversion complete: %s", output_path)
        return output_path

    def _convert_powerpoint(self, input_path: Path, output_path: Path) -> Path:
        logger.info("Converting PPTX via PowerPoint COM: %s", input_path)
        win32com, pythoncom = _get_com_modules()
        pythoncom.CoInitialize()
        app = win32com.client.Dispatch("PowerPoint.Application")
        prs = None
        try:
            prs = app.Presentations.Open(str(input_path.resolve()))
            prs.SaveAs(str(output_path.resolve()), _PP_SAVE_AS_PDF)
        except Exception as e:
            raise ConversionError(f"PowerPoint COM conversion failed for {input_path}: {e}") from e
        finally:
            if prs is not None:
                try:
                    prs.Close()
                except Exception:
                    pass
            try:
                app.Quit()
            except Exception:
                pass
            pythoncom.CoUninitialize()

        _verify_output(output_path, input_path)
        logger.info("PowerPoint conversion complete: %s", output_path)
        return output_path


def _get_com_modules():
    try:
        import win32com.client  # noqa: F401
        import win32com
        import pythoncom
        return win32com, pythoncom
    except ImportError:
        raise ConverterNotAvailableError(
            "pywin32 is not installed. Run: pip install pywin32"
        )


def _verify_output(output_path: Path, input_path: Path) -> None:
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConversionError(
            f"MS Office COM produced no output for {input_path}. "
            "File may be password-protected or corrupted."
        )


def is_ms_office_available(app_prog_id: str) -> bool:
    """Non-raising probe for a specific Office COM application."""
    try:
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()
        try:
            app = win32com.client.Dispatch(app_prog_id)
            app.Quit()
            return True
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        return False

from abc import ABC, abstractmethod
from pathlib import Path

from converter.exceptions import ConversionError


class BaseConverter(ABC):

    SUPPORTED_EXTENSIONS: set[str] = set()

    @abstractmethod
    def convert(self, input_path: Path, output_path: Path) -> Path:
        ...

    @classmethod
    def supports(cls, extension: str) -> bool:
        return extension.lower() in cls.SUPPORTED_EXTENSIONS

    def _validate_input(self, input_path: Path) -> None:
        if not input_path.exists():
            raise ConversionError(f"Input file not found: {input_path}")
        if not input_path.is_file():
            raise ConversionError(f"Input path is not a file: {input_path}")
        if input_path.stat().st_size == 0:
            raise ConversionError(f"Input file is empty: {input_path}")

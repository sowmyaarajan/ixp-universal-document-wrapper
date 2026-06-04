import os
import shutil
import sys
from pathlib import Path

from converter.exceptions import ConverterNotAvailableError


class LibreOfficeFinder:

    _WINDOWS_PATHS = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    ]
    _LINUX_NAMES = ["soffice", "libreoffice"]

    @classmethod
    def find(cls) -> Path:
        env_path = os.environ.get("LIBREOFFICE_PATH")
        if env_path:
            p = Path(env_path)
            if p.is_file():
                return p

        if sys.platform == "win32":
            for candidate in cls._WINDOWS_PATHS:
                if candidate.is_file():
                    return candidate
            via_which = shutil.which("soffice")
            if via_which:
                return Path(via_which)
        else:
            for name in cls._LINUX_NAMES:
                via_which = shutil.which(name)
                if via_which:
                    return Path(via_which)

        raise ConverterNotAvailableError(
            "LibreOffice (soffice) not found. "
            "Install from https://www.libreoffice.org/download/ "
            "or set the LIBREOFFICE_PATH environment variable."
        )

    @classmethod
    def is_available(cls) -> bool:
        try:
            cls.find()
            return True
        except ConverterNotAvailableError:
            return False

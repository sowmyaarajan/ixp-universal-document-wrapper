class ConversionError(Exception):
    """Base for all converter errors."""


class UnsupportedFormatError(ConversionError):
    """File extension has no registered converter."""


class ConverterNotAvailableError(ConversionError):
    """Required backend (LibreOffice, MS Office) is not installed."""


class CorruptedFileError(ConversionError):
    """Source file cannot be opened or is structurally invalid."""


class ConversionTimeoutError(ConversionError):
    """Subprocess-based conversion exceeded the configured timeout."""

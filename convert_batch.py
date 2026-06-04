"""
Batch converter — converts multiple files to PDF.

Usage:
    python convert_batch.py file1.docx file2.xlsx file3.png
    python convert_batch.py "C:\\Docs\\*.docx"
"""

import sys
import glob
from pathlib import Path
from converter import DocumentConverter, ConversionError, UnsupportedFormatError

def batch_convert(file_patterns: list[str]):
    converter = DocumentConverter()

    # Expand any glob patterns (e.g. *.docx)
    files = []
    for pattern in file_patterns:
        expanded = glob.glob(pattern)
        files.extend(expanded if expanded else [pattern])

    if not files:
        print("No files found.")
        return

    print(f"Converting {len(files)} file(s)...\n")
    success, skipped, failed = 0, 0, 0

    for file in files:
        input_path = Path(file)
        output_path = input_path.with_suffix(".pdf")
        try:
            result = converter.convert_to_pdf(input_path, output_path)
            print(f"  OK  {input_path.name} -> {result.name} ({result.stat().st_size:,} bytes)")
            success += 1
        except UnsupportedFormatError:
            print(f"  SKIP  {input_path.name} (unsupported format)")
            skipped += 1
        except ConversionError as e:
            print(f"  FAIL  {input_path.name}: {e}")
            failed += 1

    print(f"\nDone: {success} converted, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_batch.py file1.docx file2.xlsx ...")
        print('       python convert_batch.py "C:\\Docs\\*.docx"')
        sys.exit(1)
    batch_convert(sys.argv[1:])

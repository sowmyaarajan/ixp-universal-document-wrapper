import logging
import zipfile
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Extensions the wrapper can convert (skip system files)
_SKIP = {".ds_store", ".thumbs.db", ""}


def process_zip(zip_path: Path, wrapper) -> list[dict]:
    results = []
    with tempfile.TemporaryDirectory(prefix="ixp_zip_") as tmp:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp)
        for f in Path(tmp).rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() in _SKIP or f.name.startswith("__"):
                continue
            logger.info("Processing ZIP entry: %s", f.name)
            try:
                result = wrapper.process(f)
                results.append({"file": f.name, "result": result})
            except Exception as e:
                results.append({"file": f.name, "error": str(e)})
    return results

import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from wrapper import IXPWrapper
from ingestion.zip_handler import process_zip
from ingestion.email_handler import process_email

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="IXP Universal Document Wrapper", version="1.0.0")
_wrapper = IXPWrapper()

# Serve static UI
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

_EMAIL_EXTS = {".msg", ".eml"}
_ZIP_EXTS = {".zip"}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "dependencies": IXPWrapper.check_dependencies()}


@app.get("/supported-formats")
def supported_formats():
    return {
        "extensions": _wrapper.get_supported_extensions(),
        "specialFormats": [".zip", ".msg", ".eml"],
    }


@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    document_type: str = Form(default=None),
):
    ext = Path(file.filename).suffix.lower()

    with tempfile.TemporaryDirectory(prefix="ixp_api_") as tmp:
        saved = Path(tmp) / file.filename
        saved.write_bytes(await file.read())

        try:
            if ext in _ZIP_EXTS:
                results = process_zip(saved, _wrapper)
                return JSONResponse({"type": "batch", "results": results})
            elif ext in _EMAIL_EXTS:
                results = process_email(saved, _wrapper)
                return JSONResponse({"type": "batch", "results": results})
            else:
                result = _wrapper.process(saved, document_type or None)
                return JSONResponse(result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch")
async def batch_process(
    files: list[UploadFile] = File(...),
    document_type: str = Form(default=None),
):
    results = []
    with tempfile.TemporaryDirectory(prefix="ixp_batch_") as tmp:
        for f in files:
            saved = Path(tmp) / f.filename
            saved.write_bytes(await f.read())
            try:
                result = _wrapper.process(saved, document_type or None)
                results.append({"file": f.filename, "result": result})
            except Exception as e:
                results.append({"file": f.filename, "error": str(e)})
    return JSONResponse({"type": "batch", "results": results})

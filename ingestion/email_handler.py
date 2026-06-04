import email as email_lib
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def process_email(email_path: Path, wrapper) -> list[dict]:
    ext = email_path.suffix.lower()
    if ext == ".msg":
        return _process_msg(email_path, wrapper)
    elif ext == ".eml":
        return _process_eml(email_path, wrapper)
    else:
        raise ValueError(f"Unsupported email format: {ext}")


def _process_msg(msg_path: Path, wrapper) -> list[dict]:
    try:
        import extract_msg
    except ImportError:
        return [{"file": msg_path.name, "error": "extract-msg not installed. Run: pip install extract-msg"}]

    results = []
    with tempfile.TemporaryDirectory(prefix="ixp_msg_") as tmp:
        msg = extract_msg.Message(str(msg_path))
        try:
            # Read filename + data eagerly while OLE file is still open
            attachments = [
                (
                    (att.longFilename or att.shortFilename or "").replace("\x00", "").strip(),
                    att.data or b"",
                )
                for att in msg.attachments
            ]
        finally:
            msg.close()

        for filename, data in attachments:
            if not filename:
                continue
            att_path = Path(tmp) / filename
            try:
                att_path.write_bytes(data)
            except (ValueError, TypeError):
                continue
            # Skip small images — likely inline signatures/logos
            if att_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp"} and len(data) < 50_000:
                logger.info("Skipping small image %s (%d bytes)", filename, len(data))
                continue
            logger.info("Processing MSG attachment: %s", filename)
            try:
                result = wrapper.process(att_path)
                results.append({"file": filename, "result": result})
            except Exception as e:
                results.append({"file": filename, "error": str(e)})
    return results


def _process_eml(eml_path: Path, wrapper) -> list[dict]:
    results = []
    with tempfile.TemporaryDirectory(prefix="ixp_eml_") as tmp:
        msg = email_lib.message_from_bytes(eml_path.read_bytes())
        for part in msg.walk():
            filename = part.get_filename()
            if not filename:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            att_path = Path(tmp) / filename
            att_path.write_bytes(payload)
            # Skip small images — likely inline signatures/logos
            if att_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp"} and len(payload) < 50_000:
                logger.info("Skipping small image %s (%d bytes)", filename, len(payload))
                continue
            logger.info("Processing EML attachment: %s", filename)
            try:
                result = wrapper.process(att_path)
                results.append({"file": filename, "result": result})
            except Exception as e:
                results.append({"file": filename, "error": str(e)})
    return results

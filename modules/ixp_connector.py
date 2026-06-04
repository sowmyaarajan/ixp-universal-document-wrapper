import logging
import time
from pathlib import Path

import requests

import config

logger = logging.getLogger(__name__)

_POLL_INTERVAL       = 5    # seconds between polls
_MAX_POLLS_DIGITIZE  = 60   # 5 min — image OCR can be slow
_MAX_POLLS_EXTRACT   = 24   # 2 min — extraction is faster


def process(pdf_path: str | Path, document_type: str = None) -> dict:
    if not config.ixp_configured():
        logger.warning("IXP not configured — returning mock result")
        return _mock_result()

    token   = _get_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Step 1: Digitize
    doc_id = _digitize(pdf_path, headers)
    logger.info("Digitized: %s", doc_id)

    _poll(f"{config.DU_API_BASE}/digitization/result/{doc_id}?api-version=1",
          headers, "Digitization", _MAX_POLLS_DIGITIZE)

    # Step 2: Extract
    json_headers = {**headers, "Content-Type": "application/json"}
    r = requests.post(
        f"{config.DU_API_BASE}/extractors/{config.DU_EXTRACTOR_ID}/extraction/start?api-version=1",
        headers=json_headers,
        json={"documentId": doc_id},
        timeout=30,
    )
    r.raise_for_status()
    result_url = r.json()["resultUrl"]

    result = _poll(result_url, headers, "Extraction", _MAX_POLLS_EXTRACT)
    result["_doc_id"] = doc_id
    return result


def _get_token() -> str:
    resp = requests.post(
        config.UIPATH_TOKEN_URL,
        data={
            "grant_type":    "client_credentials",
            "client_id":     config.UIPATH_CLIENT_ID,
            "client_secret": config.UIPATH_CLIENT_SECRET,
            "scope":         "Du.Digitization.Api Du.Extraction.Api",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _digitize(pdf_path: str | Path, headers: dict) -> str:
    with open(pdf_path, "rb") as f:
        resp = requests.post(
            f"{config.DU_API_BASE}/digitization/start?api-version=1",
            headers={k: v for k, v in headers.items() if k != "Content-Type"},
            files={"file": (Path(pdf_path).name, f, "application/pdf")},
            timeout=60,
        )
    resp.raise_for_status()
    return resp.json()["documentId"]


def _poll(url: str, headers: dict, label: str, max_polls: int) -> dict:
    for i in range(max_polls):
        time.sleep(_POLL_INTERVAL)
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data   = resp.json()
        status = data.get("status", "")
        logger.info("%s poll %d/%d: %s", label, i + 1, max_polls, status)
        if status == "Succeeded":
            return data
        if status == "Failed":
            error = data.get("error", {}).get("message", "Unknown error")
            raise RuntimeError(f"{label} failed: {error}")
    raise TimeoutError(f"{label} timed out after {max_polls * _POLL_INTERVAL}s")


def _mock_result() -> dict:
    return {
        "status": "Succeeded",
        "_mock": True,
        "_note": "IXP not configured — add credentials to .env",
        "result": {"extractionResult": {"ResultsDocument": {"Fields": []}}},
    }

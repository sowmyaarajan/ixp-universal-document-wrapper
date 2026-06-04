from pathlib import Path


def format_response(
    file_analysis: dict,
    validation: dict,
    ixp_result: dict,
    normalized_pdf_path: Path,
    processing_time_ms: int,
) -> dict:
    if not validation["valid"]:
        return {
            "status": "ValidationFailed",
            "documentId": "",
            "documentType": file_analysis.get("fileType", "Unknown"),
            "confidence": 0.0,
            "pages": validation.get("pageCount"),
            "fields": {},
            "entities": [],
            "fileInfo": _file_info(file_analysis),
            "normalizedPdfPath": str(normalized_pdf_path),
            "validationErrors": validation.get("errors", []),
            "processingTimeMs": processing_time_ms,
        }

    fields, entities, confidence = _parse_du_result(ixp_result)
    is_mock = ixp_result.get("_mock", False)

    return {
        "status": "Success" if not is_mock else "MockResult",
        "documentId": ixp_result.get("_doc_id", ""),
        "documentType": _guess_doc_type(fields, file_analysis),
        "confidence": round(confidence, 4),
        "pages": validation.get("pageCount"),
        "fields": fields,
        "entities": entities,
        "fileInfo": _file_info(file_analysis),
        "normalizedPdfPath": str(normalized_pdf_path),
        "validationErrors": validation.get("errors", []),
        "processingTimeMs": processing_time_ms,
        **({"_note": ixp_result["_note"]} if is_mock else {}),
    }


def _parse_du_result(ixp_result: dict) -> tuple[dict, list, float]:
    fields: dict      = {}
    entities: list    = []
    confidences: list = []

    try:
        du_fields = (
            ixp_result.get("result", {})
            .get("extractionResult", {})
            .get("ResultsDocument", {})
            .get("Fields", [])
        )

        for field in du_fields:
            for val_group in field.get("Values", []):
                for component in val_group.get("Components", []):
                    if component.get("FieldType") == "Internal":
                        for sub in component.get("Values", [{}])[0].get("Components", []):
                            name = sub.get("FieldName", "")
                            for v in sub.get("Values", []):
                                value = v.get("Value", "")
                                conf  = v.get("Confidence", 0.0) or 0.0
                                if value and value != name:
                                    fields[name] = value
                                    entities.append({
                                        "field": name,
                                        "value": value,
                                        "confidence": round(conf, 4),
                                    })
                                    if conf > 0:
                                        confidences.append(conf)
    except (KeyError, TypeError, IndexError):
        pass

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return fields, entities, avg_conf


def _file_info(analysis: dict) -> dict:
    return {
        "fileName": analysis["fileName"],
        "originalFormat": analysis["fileType"],
        "sizeMB": analysis["sizeMB"],
    }


def _guess_doc_type(fields: dict, analysis: dict) -> str:
    keys_lower = {k.lower() for k in fields}
    if any(k in keys_lower for k in ("invoicenumber", "invoice_number", "inv")):
        return "Invoice"
    if any(k in keys_lower for k in ("purchaseorder", "po_number", "order")):
        return "PurchaseOrder"
    if any(k in keys_lower for k in ("contract", "agreement")):
        return "Contract"
    return analysis.get("fileType", "Unknown")

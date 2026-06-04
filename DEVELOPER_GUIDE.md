# IXP Universal Document Wrapper — Developer Guide

## What This Project Does

A reusable Python FastAPI service that accepts any document (DOCX, XLSX, PPTX, CSV, images, ZIP, MSG, EML) and returns structured JSON with extracted fields — powered by UiPath IXP and Gemini 2.5 Flash.

**Core value:** Eliminates repetitive DU API plumbing for every developer. Drop any file in, get structured JSON out.

## How to Start

```bash
python -m uvicorn api.main:app --reload --port 8080
```

Open browser at `http://localhost:8080`

## After IXP Portal Changes (add fields + deploy)

```bash
python setup.py
```

## Key Files

```
IXP_Wrapper/
├── wrapper.py                  # Main orchestrator — entry point for all processing
├── config.py                   # All config loaded from .env
├── setup.py                    # Auto-discovers extractor ID, updates .env, validates taxonomy
├── .env.example                # Template for new developers
│
├── modules/
│   ├── file_analyzer.py        # Module 1: detect file type/size
│   ├── validator.py            # Module 3: corruption/size/page checks
│   ├── ixp_connector.py        # Module 5: DU API (digitize + extract)
│   ├── response_formatter.py   # Module 6: normalize to standard JSON
│   └── taxonomy_manager.py     # Define and validate IXP field taxonomy as code
│
├── converter/                  # Module 2: any file -> PDF
│   ├── document_converter.py   # Main converter (LibreOffice + Pillow)
│   └── converters/
│       ├── office_converter.py # XLSX/PPTX/CSV via LibreOffice subprocess
│       ├── docx_converter.py   # DOCX via docx2pdf -> LibreOffice fallback
│       └── image_converter.py  # PNG/JPG/etc via Pillow
│
├── ingestion/                  # Phase 2: ZIP/MSG/EML handling
│   ├── zip_handler.py
│   └── email_handler.py
│
└── api/
    ├── main.py                 # FastAPI routes: /process, /batch, /health
    └── static/index.html       # Bootstrap UI
```

## Processing Pipeline

```
Any file
   -> file_analyzer.py      detect type, size
   -> document_converter.py convert to PDF (LibreOffice / Pillow)
   -> validator.py           check corruption, password, size, pages
   -> ixp_connector.py       DU API: digitize -> poll -> extract -> poll
   -> response_formatter.py  parse nested DU response -> clean JSON
   ->
{ "fields": { "InvoiceNumber": "...", "VendorName": "..." }, "confidence": 0.93 }
```

## Environment Variables (.env)

See `.env.example` for all required values and how to find them.

```
UIPATH_HOST             # https://staging.uipath.com or https://cloud.uipath.com
UIPATH_ACCOUNT_NAME     # org name
UIPATH_TENANT_NAME      # tenant name
UIPATH_CLIENT_ID        # from External Application in UiPath Cloud Admin
UIPATH_CLIENT_SECRET    # from External Application
DU_ORG_UUID             # discovered via DU API (see README setup script)
DU_TENANT_UUID          # discovered via DU API
DU_PROJECT_ID           # IXP project UUID
DU_EXTRACTOR_ID         # gpt_ixp_{version} — auto-set by python setup.py
IXP_DATASET_OWNER       # from IXP project URL
IXP_DATASET_NAME        # from IXP project URL
```

## IXP Project Prerequisites

1. Create IXP project in UiPath portal
2. Add field definitions (Build -> Fields) — see `modules/taxonomy_manager.py` for reference
3. Deploy the project (Deploy tab -> Deploy button)
4. Run `python setup.py` — auto-discovers extractor ID

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI |
| GET | `/health` | Dependencies status |
| GET | `/supported-formats` | List of supported extensions |
| POST | `/process` | Single file -> JSON |
| POST | `/batch` | Multiple files -> list of JSON |

## Supported Formats

- **Images:** PNG, JPG, JPEG, BMP, GIF, TIFF, WebP -> Pillow
- **Office:** DOCX, DOC -> docx2pdf/LibreOffice; XLSX, XLS, CSV -> LibreOffice; PPTX, PPT -> LibreOffice
- **Bundles:** ZIP -> extract + process each; MSG/EML -> extract attachments + process each
- **PDF:** pass-through

## Dependencies

- Python 3.10+
- LibreOffice (for Office format conversion) — install once on robot template
- `pip install -r requirements.txt`

## Run Tests

```bash
python -m pytest tests/ -v
```

## Check Dependencies

```bash
python -c "from wrapper import IXPWrapper; import json; print(json.dumps(IXPWrapper.check_dependencies(), indent=2))"
```

## Validate Taxonomy

```bash
python -m modules.taxonomy_manager
```

## Project Status

- Phase 1 done — File analysis, normalization, validation, IXP extraction, web UI
- Phase 2 done — ZIP, EML, MSG ingestion
- Phase 3 pending — Document Splitter (future, when IXP API available)
- Phase 4 pending — .NET Activity Library for UiPath Studio

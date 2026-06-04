# IXP Universal Document Wrapper

A reusable Python service that accepts any document (DOCX, XLSX, PPTX, CSV, images, ZIP, MSG, EML) and returns structured JSON with extracted fields — powered by UiPath IXP and Gemini.

> Drop any file in. Get structured JSON out.

## Quick Start

```bash
cd "C:\path\to\IXP_Wrapper"
python -m uvicorn api.main:app --reload --port 8080
```

Open **`http://localhost:8080`** in your browser.

---

## What It Does

```
Your file (any format)
        ↓
   IXP Wrapper
   ├── Detects file type
   ├── Converts to PDF (MS Office COM / Pillow)
   ├── Validates (size, pages, corruption)
   ├── Calls UiPath DU API (digitize → extract)
   └── Returns structured JSON
        ↓
{ "InvoiceNumber": "INV-001", "VendorName": "Acme Ltd", ... }
```

---

## Supported Formats

```
┌─────────────────────────────────────────┬──────────────────────┐
│ Format                                  │ Backend              │
├─────────────────────────────────────────┼──────────────────────┤
│ .png .jpg .jpeg .bmp .gif .tiff .webp   │ Pillow               │
│ .docx .doc                              │ docx2pdf → LibreOffice│
│ .xlsx .xls .csv                         │ LibreOffice          │
│ .pptx .ppt                              │ LibreOffice          │
│ .pdf                                    │ Pass-through         │
│ .zip                                    │ Extracts + processes │
│ .msg .eml                               │ Extracts attachments │
└─────────────────────────────────────────┴──────────────────────┘
```

---

## Prerequisites

- Python 3.10+
- **LibreOffice** — for Office format conversion (DOCX, XLSX, PPTX, CSV)
  - Windows: `winget install TheDocumentFoundation.LibreOffice`
  - Linux: `apt-get install -y libreoffice`
  - Install once on the robot template — no MS Office required
- UiPath Automation Cloud account with an IXP project deployed

---

## 5-Minute Setup

**1. Clone and install dependencies**
```bash
pip install -r requirements.txt
```

**2. Create your environment file**
```bash
copy .env.example .env
```

**3. Fill in `.env`** (see section below for how to get each value)

**4. Start the server**
```bash
python -m uvicorn api.main:app --reload --port 8080
```

**5. Open the UI**
```
http://localhost:8080
```
Upload any document and click **Process**.

---

## Getting Your UiPath Credentials

### OAuth Client ID & Secret
1. Go to `https://cloud.uipath.com` → **Admin → External Applications → Add**
2. Name: `IXP Wrapper` | Type: **Confidential**
3. Add scopes: `Du.Digitization.Api` and `Du.Extraction.Api` (Application type)
4. Copy **Client ID** and **Client Secret**

### DU Project IDs (DU_ORG_UUID, DU_TENANT_UUID, DU_PROJECT_ID, DU_EXTRACTOR_ID)
Run this once after filling in your OAuth credentials:
```bash
python -c "
import requests, os, json
from dotenv import load_dotenv; load_dotenv('.env')
host = os.getenv('UIPATH_HOST')
token = requests.post(f'{host}/identity_/connect/token', data={
    'grant_type': 'client_credentials',
    'client_id': os.getenv('UIPATH_CLIENT_ID'),
    'client_secret': os.getenv('UIPATH_CLIENT_SECRET'),
    'scope': 'Du.Digitization.Api Du.Extraction.Api',
}).json()['access_token']
account = os.getenv('UIPATH_ACCOUNT_NAME')
tenant  = os.getenv('UIPATH_TENANT_NAME')
r = requests.get(f'{host}/{account}/{tenant}/du_/api/framework/projects?api-version=1',
    headers={'Authorization': f'Bearer {token}'})
for p in r.json().get('projects', []):
    if p['type'] == 'IXP':
        url = p['detailsUrl']
        parts = url.split('/')
        print(f'Project: {p[\"name\"]}')
        print(f'  DU_ORG_UUID    = {parts[3]}')
        print(f'  DU_TENANT_UUID = {parts[4]}')
        print(f'  DU_PROJECT_ID  = {p[\"id\"]}')
        for e in p.get('extractors', []):
            print(f'  DU_EXTRACTOR_ID= {e[\"id\"]}')
        print()
"
```

### IXP Project Setup
1. Create a project at your UiPath IXP portal
2. Add field definitions (InvoiceNumber, VendorName, etc.) with instructions
3. **Deploy** the project: IXP UI → **Deploy** tab → click **Deploy** button
4. Run the discovery script above to get `DU_EXTRACTOR_ID`

---

## API Reference

### Process a single file
```http
POST /process
Content-Type: multipart/form-data

file: <your file>
document_type: Invoice   (optional)
```

**Response:**
```json
{
  "status": "Success",
  "documentId": "...",
  "documentType": "Invoice",
  "confidence": 0.93,
  "pages": 1,
  "fields": {
    "InvoiceNumber": "INV-2026-001",
    "VendorName": "Acme Ltd",
    "TotalAmount": "6000.00 GBP",
    "InvoiceDate": "2026-06-02"
  },
  "entities": [...],
  "fileInfo": { "fileName": "...", "originalFormat": "DOCX", "sizeMB": 0.04 },
  "processingTimeMs": 15000
}
```

### Process multiple files
```http
POST /batch
Content-Type: multipart/form-data

files: <file1>, <file2>, ...
```

### Health check
```http
GET /health
```

### Supported formats
```http
GET /supported-formats
```

---

## CLI Usage

```bash
# Single file
python convert_batch.py "invoice.docx"

# Multiple files
python convert_batch.py "file1.docx" "file2.xlsx" "photo.png"

# Entire folder
python convert_batch.py "C:\Docs\*"
```

---

## Processing Times (approximate)

| Format | Time |
|--------|------|
| DOCX, XLSX, PPTX | 20–40 seconds |
| Image (JPEG, PNG) | 2–3 minutes (OCR on staging) |
| PDF (text-based) | 15–25 seconds |

> Note: Staging environment is slower than production.

---

## Check Dependencies
```bash
python -c "
from wrapper import IXPWrapper
import json
print(json.dumps(IXPWrapper.check_dependencies(), indent=2))
"
```

---

## Run Tests
```bash
python -m pytest tests/ -v
```

---

## Using in a UiPath Studio Workflow

The wrapper runs as a service. Call it from any RPA workflow using the **HTTP Request** activity:

**Prerequisites:** Install `UiPath.WebAPI.Activities` from Manage Packages.

**Workflow steps:**

1. **HTTP Request** activity:
   - URL: `http://localhost:8080/process`
   - Method: `POST`
   - Headers: `Accept: application/json`
   - Body Type: `application/x-www-form-urlencoded` → switch to `multipart/form-data`
   - Add field `file` → type: File, value: full path to your document
   - Output: `responseContent` (String)

2. **Deserialize JSON** activity:
   - Input: `responseContent`
   - Output: `jsonResult` (JObject)

3. **Access fields:**
   ```
   jsonResult("status").ToString()                    → "Success"
   jsonResult("fields")("InvoiceNumber").ToString()   → "INV-2026-001"
   jsonResult("fields")("VendorName").ToString()      → "Acme Ltd"
   jsonResult("confidence").ToObject(Of Double)()     → 0.93
   ```

**Note:** The wrapper service must be running before the robot executes.

---

## IXP Project Prerequisites

Before extracted fields appear:
1. Create an IXP project in UiPath portal
2. Add field definitions with instructions (**Build -> Fields**) -- see Taxonomy section below
3. Deploy the project (**Deploy tab -> Deploy button**)
4. Run the discovery script (see "Getting Your UiPath Credentials" above) to get `DU_EXTRACTOR_ID`
5. Update `.env` with the extractor ID and restart the service

---

## Taxonomy Management

Field definitions (what to extract) are defined as code in `modules/taxonomy_manager.py`.

### Validate your IXP project matches the code definition
```bash
python -m modules.taxonomy_manager
```

Example output:
```
Expected taxonomy (defined in code):
  [default]
    - InvoiceNumber (Exact Text)
    - VendorName (Inferred Text)
    - TotalAmount (Monetary Quantity)
    - InvoiceDate (Date)
    - DueDate (Date)

Validating against IXP project...
OK  IXP project is IN SYNC with code definition.
```

### Adding or changing fields

1. Edit `TAXONOMY` in `modules/taxonomy_manager.py`
2. Run `python -m modules.taxonomy_manager` to see what's missing
3. Add the missing fields manually in the IXP portal: **Build -> Fields**
4. Re-run the validator to confirm in sync
5. Re-deploy the IXP project and update `DU_EXTRACTOR_ID` in `.env`

> **Known limitation:** The IXP taxonomy write API is not yet publicly available.
> Fields must currently be added manually in the portal. Once UiPath exposes
> the write API, this step will be automated. The `taxonomy_manager.py` is
> ready to support it when available.

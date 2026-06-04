# IXP Universal Document Wrapper

## Executive Summary

Organizations implementing UiPath IXP often need to build repetitive workflows to handle document ingestion, normalization, conversion, splitting, validation, and API integration before documents can be processed.

The **IXP Universal Document Wrapper** aims to eliminate this repeated effort by providing a reusable abstraction layer that accepts any supported document format and returns standardized structured JSON results.

Instead of every project implementing custom preprocessing logic, developers simply submit a file to the wrapper and receive extraction results in a common format.

---

# Problem Statement

Current implementations typically require developers to build workflows for:

* File type detection
* Document conversion
* ZIP extraction
* Email attachment processing
* Document splitting
* Validation checks
* IXP API integration
* Result formatting

This results in:

* Duplicate development effort
* Increased maintenance overhead
* Inconsistent implementations
* Longer project delivery timelines

---

# Vision

## Current State

```text
Input File
    │
    ├─ Detect Type
    ├─ Convert
    ├─ Split
    ├─ Prepare Payload
    ├─ Call IXP
    └─ Parse Results
```

## Future State

```text
Input File
    │
    ▼
IXP Wrapper
    │
    ▼
Structured JSON
```

Developers interact with a single component while the wrapper handles all preprocessing and integration logic.

---

# Solution Architecture

```text
┌─────────────────────┐
│ Input Document      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ File Analyzer       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Normalization Layer │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Document Splitter   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ IXP Connector       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Response Formatter  │
└──────────┬──────────┘
           │
           ▼
      Standard JSON
```

---

# Module 1: File Analyzer

## Purpose

Identify the document type and determine the required processing path.

## Supported Formats

* PDF
* DOC
* DOCX
* XLS
* XLSX
* PPT
* PPTX
* PNG
* JPG
* JPEG
* TIFF
* ZIP
* MSG
* EML

## Example Output

```json
{
  "fileType": "DOCX",
  "size": "2.4MB",
  "extension": ".docx"
}
```

---

# Module 2: Normalization Layer

The normalization layer converts all supported input formats into a standard processing format.

## PDF

```text
PDF
 │
 ▼
Pass Through
```

## Word Documents

```text
DOCX
 │
 ▼
LibreOffice / Aspose
 │
 ▼
PDF
```

## Excel Documents

```text
XLSX
 │
 ▼
Worksheet Rendering
 │
 ▼
PDF
```

## PowerPoint Documents

```text
PPTX
 │
 ▼
PDF
```

## Images

```text
PNG / JPG / TIFF
 │
 ▼
PDF
```

## ZIP Files

```text
ZIP
 │
 ▼
Extract Files
 │
 ▼
Recursive Processing
```

## Email Files

```text
MSG / EML
 │
 ▼
Extract Attachments
 │
 ▼
Process Attachments
```

---

# Module 3: Validation Layer

Validation is performed before consuming IXP resources.

## Validation Checks

### Corrupted File Detection

```text
Can File Be Opened?
```

### Password-Protected Documents

```text
Is Document Locked?
```

### Empty Documents

```text
Page Count = 0?
```

### File Size Validation

```text
Maximum Size Threshold
```

### Page Count Validation

```text
Maximum Page Threshold
```

### Optional Future Enhancements

* DPI validation
* Image quality scoring
* Rotation detection
* Blur detection

---

# Module 4: Document Splitter

Many uploads contain multiple logical documents.

## Example

```text
100 Page PDF

Invoice
Invoice
Invoice
PO
PO
Contract
```

## Output

```text
Invoice_1.pdf
Invoice_2.pdf
PO_1.pdf
Contract_1.pdf
```

## Potential Technologies

* UiPath Document Splitter
* Classification-based splitting
* LLM-assisted page grouping

---

# Module 5: IXP Connector

The connector abstracts all IXP implementation complexity.

Developers should not need to manage:

* Authentication
* Dataset configuration
* Schema selection
* Upload APIs
* Polling APIs
* Result APIs

## Example Usage

### C#

```csharp
var result = IxpWrapper.Process(filePath);
```

### Python

```python
result = ixp_wrapper.process(file_path)
```

---

# Module 6: Standard Response Layer

The wrapper should always return a consistent response schema.

## Example Response

```json
{
  "documentId": "12345",
  "status": "Success",
  "documentType": "Invoice",
  "confidence": 0.94,
  "pages": 3,
  "fields": {
    "InvoiceNumber": "INV-001",
    "VendorName": "ABC Ltd",
    "Amount": "5000"
  }
}
```

Benefits:

* Consistent integration experience
* Reduced downstream complexity
* Vendor independence

---

# Recommended Development Roadmap

## Phase 1 - MVP

### Features

* PDF Support
* DOCX Support
* XLSX Support
* PPTX Support
* PNG Support
* JPG Support
* IXP Integration
* Standard JSON Response

### Goal

```text
Any Common File
      │
      ▼
     IXP
      │
      ▼
     JSON
```

---

## Phase 2 - Enhanced Ingestion

### Features

* ZIP Processing
* MSG Processing
* EML Processing
* Validation Framework
* Duplicate Detection

---

## Phase 3 - Advanced Processing

### Features

* Document Splitting
* Multi-Document Handling
* Quality Scoring
* Intelligent Routing

---

## Phase 4 - Universal IDP Wrapper

Extend beyond UiPath IXP.

```text
Input
 │
 ▼
Wrapper
 │
 ├─ UiPath IXP
 ├─ Azure Document Intelligence
 ├─ Google Document AI
 └─ ABBYY
```

Maintain the same standardized output contract regardless of backend extraction engine.

---

# UiPath Implementation Strategy

Package the solution as a reusable UiPath Library.

## Exposed Activity

```text
Process Document
```

## Inputs

```text
FilePath
DocumentType
Options
```

## Outputs

```text
NormalizedPDF
ExtractionJSON
Status
Confidence
```

---

# Business Benefits

* Reduced implementation effort
* Faster project delivery
* Consistent document processing architecture
* Reduced onboarding time for developers
* Standardized IXP integration
* Improved maintainability
* Reusable across multiple customer implementations

---

# Key Value Proposition

Instead of asking developers to understand document conversion, splitting, validation, and IXP APIs, the wrapper provides a single experience:

```text
Input File
    │
    ▼
IXP Wrapper
    │
    ▼
Structured JSON
```

This enables teams to focus on business processes rather than document ingestion plumbing.

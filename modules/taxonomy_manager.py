"""
Taxonomy Manager -- push field definitions to IXP project via CM API.
Uses OAuth (no personal API key needed, auto-refreshes).

Usage:
    python -m modules.taxonomy_manager
"""
import logging
import requests
import config

logger = logging.getLogger(__name__)

# ── Define your taxonomy here ──────────────────────────────────────────
# Add / edit field groups and fields as needed.
# kind options: "Exact Text", "Inferred Text", "Date", "Monetary Quantity", "Number", "Boolean"

TAXONOMY = [
    {
        "name": "default",
        "instructions": "Extract key fields from invoice documents including invoice number, vendor details, amounts and dates.",
        "fields": [
            {
                "name": "InvoiceNumber",
                "kind": "Exact Text",
                "instructions": "Extract the invoice number, invoice #, inv. no, or document reference number.",
            },
            {
                "name": "VendorName",
                "kind": "Inferred Text",
                "instructions": "Extract the name of the vendor, supplier, seller or company issuing this invoice.",
            },
            {
                "name": "TotalAmount",
                "kind": "Monetary Quantity",
                "instructions": "Extract the total amount due, grand total, or final payable amount including all taxes and fees.",
            },
            {
                "name": "InvoiceDate",
                "kind": "Date",
                "instructions": "Extract the invoice date, date of issue, or billing date.",
            },
            {
                "name": "DueDate",
                "kind": "Date",
                "instructions": "Extract the payment due date or payment deadline.",
            },
        ],
    }
]
# ───────────────────────────────────────────────────────────────────────


def _get_token() -> str:
    resp = requests.post(
        config.UIPATH_TOKEN_URL,
        data={
            "grant_type":    "client_credentials",
            "client_id":     config.UIPATH_CLIENT_ID,
            "client_secret": config.UIPATH_CLIENT_SECRET,
            "scope":         config.CM_API_SCOPE,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _build_label_defs(taxonomy: list) -> list:
    """Convert our simple taxonomy format to CM API moon_form structure."""
    label_defs = []
    for group in taxonomy:
        moon_form = [
            {
                "name": f["name"],
                "kind": f["kind"],
                "instructions": f.get("instructions", ""),
            }
            for f in group["fields"]
        ]
        label_defs.append({
            "name": group["name"],
            "instructions": group.get("instructions", ""),
            "moon_form": moon_form,
        })
    return label_defs



def get_taxonomy() -> dict:
    """Fetch current taxonomy from IXP project."""
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    url = f"{config.CM_API_BASE}/datasets/{config.IXP_DATASET_OWNER}/{config.IXP_DATASET_NAME}"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json().get("dataset", {})
    return {
        "name": data.get("name"),
        "label_defs": data.get("label_defs", []),
    }


def validate_taxonomy() -> dict:
    """
    Compare code-defined taxonomy against what's actually in IXP.
    Returns a diff showing what's missing or extra.
    Note: Pushing taxonomy programmatically is not yet supported by IXP API.
          Use this to validate your IXP project matches the code definition.
    """
    current = get_taxonomy()
    current_groups = {g["name"]: {f["name"]: f["kind"] for f in g.get("moon_form", [])}
                      for g in current.get("label_defs", [])}

    expected_groups = {g["name"]: {f["name"]: f["kind"] for f in g["fields"]}
                       for g in TAXONOMY}

    issues = []
    for group_name, expected_fields in expected_groups.items():
        if group_name not in current_groups:
            issues.append(f"MISSING group: [{group_name}]")
            continue
        current_fields = current_groups[group_name]
        for field_name, kind in expected_fields.items():
            if field_name not in current_fields:
                issues.append(f"MISSING field: [{group_name}] -> {field_name} ({kind})")
            elif current_fields[field_name] != kind:
                issues.append(f"WRONG TYPE: [{group_name}] -> {field_name} is {current_fields[field_name]}, expected {kind}")

    return {"in_sync": len(issues) == 0, "issues": issues, "current": current_groups}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("IXP Taxonomy Validator")
    print("=" * 60)
    print("\nExpected taxonomy (defined in code):")
    for group in TAXONOMY:
        print(f"\n  [{group['name']}]  --  {group['instructions'][:60]}")
        for f in group["fields"]:
            print(f"    - {f['name']} ({f['kind']})")

    print("\nValidating against IXP project...")
    result = validate_taxonomy()

    if result["in_sync"]:
        print("\nOK IXP project is IN SYNC with code definition.")
    else:
        print(f"\nMISMATCH {len(result['issues'])} issue(s) found:")
        for issue in result["issues"]:
            print(f"  • {issue}")
        print("\nTo fix: go to your IXP project -> Build -> Fields and add the missing fields.")
        print("IXP project URL: see README for portal link.")

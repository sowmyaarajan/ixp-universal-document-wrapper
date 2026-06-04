"""
IXP Wrapper Setup Script
Runs after you deploy a new version in the IXP portal.

Usage:
    python setup.py

What it does:
    1. Discovers the latest deployed extractor ID from DU API
    2. Updates DU_EXTRACTOR_ID in .env automatically
    3. Validates taxonomy is in sync with code definition
    4. Reports status — server reloads automatically if running with --reload
"""
import os
import re
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def get_token() -> str:
    host   = os.getenv("UIPATH_HOST")
    resp   = requests.post(f"{host}/identity_/connect/token", data={
        "grant_type":    "client_credentials",
        "client_id":     os.getenv("UIPATH_CLIENT_ID"),
        "client_secret": os.getenv("UIPATH_CLIENT_SECRET"),
        "scope":         "Du.Digitization.Api Du.Extraction.Api",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def discover_latest_extractor() -> dict:
    host        = os.getenv("UIPATH_HOST")
    org_uuid    = os.getenv("DU_ORG_UUID")
    tenant_uuid = os.getenv("DU_TENANT_UUID")
    project_id  = os.getenv("DU_PROJECT_ID")

    headers = {"Authorization": f"Bearer {get_token()}", "Accept": "application/json"}
    url = f"{host}/{org_uuid}/{tenant_uuid}/du_/api/framework/projects/{project_id}?api-version=1"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    data       = resp.json()
    extractors = data.get("extractors", [])
    versions   = data.get("projectVersions", [])

    if not extractors:
        print("ERROR: No extractors found. Deploy your IXP project first.")
        sys.exit(1)

    # Pick extractor with highest version number
    latest = max(extractors, key=lambda e: e.get("projectVersion", 0))
    tag    = next((v.get("tag") for v in versions if v.get("version") == latest["projectVersion"]), "untagged")

    return {"id": latest["id"], "version": latest["projectVersion"], "tag": tag}


def update_env(extractor_id: str) -> bool:
    env_path = Path(__file__).parent / ".env"
    content  = env_path.read_text()
    current  = os.getenv("DU_EXTRACTOR_ID", "")

    if current == extractor_id:
        return False  # no change needed

    new_content = re.sub(
        r"^DU_EXTRACTOR_ID=.*$",
        f"DU_EXTRACTOR_ID={extractor_id}",
        content,
        flags=re.MULTILINE,
    )
    env_path.write_text(new_content)
    return True


def validate_taxonomy() -> bool:
    try:
        from modules.taxonomy_manager import validate_taxonomy as _validate
        result = _validate()
        return result["in_sync"], result.get("issues", [])
    except Exception as e:
        return False, [str(e)]


def main():
    print("=" * 50)
    print("IXP Wrapper Setup")
    print("=" * 50)

    # Step 1: Discover latest extractor
    print("\n[1/3] Discovering latest deployed extractor...")
    extractor = discover_latest_extractor()
    print(f"      Found: {extractor['id']}  (version {extractor['version']}, tag: {extractor['tag']})")

    # Step 2: Update .env
    print("\n[2/3] Updating .env...")
    changed = update_env(extractor["id"])
    if changed:
        print(f"      DU_EXTRACTOR_ID updated to {extractor['id']}")
        print("      Server will auto-reload if running with --reload flag.")
    else:
        print(f"      DU_EXTRACTOR_ID already set to {extractor['id']} -- no change.")

    # Step 3: Validate taxonomy
    print("\n[3/3] Validating taxonomy...")
    in_sync, issues = validate_taxonomy()
    if in_sync:
        print("      OK -- IXP project is in sync with code definition.")
    else:
        print(f"      WARNING -- {len(issues)} issue(s) found:")
        for issue in issues:
            print(f"        - {issue}")
        print("      Fix: add missing fields in IXP portal -> Build -> Fields, then redeploy.")

    print("\n" + "=" * 50)
    if in_sync:
        print("Setup complete. Wrapper is ready.")
    else:
        print("Setup done with warnings. Fix taxonomy issues above.")
    print("=" * 50)


if __name__ == "__main__":
    main()

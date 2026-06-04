import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# UiPath host
UIPATH_HOST         = os.getenv("UIPATH_HOST", "https://staging.uipath.com")
UIPATH_ACCOUNT_NAME = os.getenv("UIPATH_ACCOUNT_NAME", "")
UIPATH_TENANT_NAME  = os.getenv("UIPATH_TENANT_NAME", "")

# OAuth credentials
UIPATH_CLIENT_ID     = os.getenv("UIPATH_CLIENT_ID", "")
UIPATH_CLIENT_SECRET = os.getenv("UIPATH_CLIENT_SECRET", "")
UIPATH_TOKEN_URL     = f"{UIPATH_HOST}/identity_/connect/token"

# DU API — org/tenant UUIDs and project identifiers
# Get these by calling: GET /du_/api/framework/projects?api-version=1
DU_ORG_UUID     = os.getenv("DU_ORG_UUID",     "")
DU_TENANT_UUID  = os.getenv("DU_TENANT_UUID",  "")
DU_PROJECT_ID   = os.getenv("DU_PROJECT_ID",   "")
DU_EXTRACTOR_ID = os.getenv("DU_EXTRACTOR_ID", "")

DU_API_BASE  = f"{UIPATH_HOST}/{DU_ORG_UUID}/{DU_TENANT_UUID}/du_/api/framework/projects/{DU_PROJECT_ID}"
CM_API_BASE  = f"{UIPATH_HOST}/{DU_ORG_UUID}/{DU_TENANT_UUID}/reinfer_/api/v1"
CM_API_SCOPE = "Ixp.ApiAccess PM.User PM.User.Read"

# IXP project identifiers for CM API
IXP_DATASET_OWNER = os.getenv("IXP_DATASET_OWNER", "")
IXP_DATASET_NAME  = os.getenv("IXP_DATASET_NAME",  "")

# Validation thresholds
MAX_FILE_SIZE_MB = float(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_PAGE_COUNT   = int(os.getenv("MAX_PAGE_COUNT", "200"))

# Temp directory (optional)
_temp    = os.getenv("TEMP_DIR", "")
TEMP_DIR = Path(_temp) if _temp else None


def ixp_configured() -> bool:
    return all([UIPATH_CLIENT_ID, UIPATH_CLIENT_SECRET, DU_ORG_UUID, DU_TENANT_UUID, DU_PROJECT_ID, DU_EXTRACTOR_ID])

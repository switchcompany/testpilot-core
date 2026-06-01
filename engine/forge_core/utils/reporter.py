"""Upload run reports to the SaaS API."""

from __future__ import annotations

from typing import Any

import httpx

from forge_core.models.config import ForgeConfig
from forge_core.utils import logger


async def upload_report(config: ForgeConfig, report: dict[str, Any]) -> bool:
    """Upload a run report to the SaaS dashboard.

    Returns True if upload succeeded, False otherwise.
    Reports are optional — engine works fully offline.
    """
    if not config.auth_token:
        logger.info("No auth token — skipping report upload (offline mode)")
        return False

    url = f"{config.saas_api_url}/api/v1/runs"
    headers = {
        "Authorization": f"Bearer {config.auth_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "org_id": config.tenant.org_id,
        "user_id": config.tenant.user_id,
        "project_id": config.tenant.project_id,
        "report": report,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                report_url = data.get("url", "")
                logger.success(f"Report uploaded: {report_url}")
                return True
            else:
                logger.warn(f"Report upload failed ({resp.status_code}): {resp.text[:200]}")
                return False
    except Exception as e:
        logger.warn(f"Report upload failed (network): {e}")
        return False


async def check_license(config: ForgeConfig) -> dict[str, Any]:
    """Check license and plan limits with the SaaS API.

    Returns plan info dict or empty dict if offline/failed.
    """
    if not config.auth_token:
        return {}

    url = f"{config.saas_api_url}/api/v1/license"
    headers = {"Authorization": f"Bearer {config.auth_token}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.warn(f"License API returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warn(f"License API unreachable: {e}")

    return {}

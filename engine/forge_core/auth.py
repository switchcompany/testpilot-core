"""SaaS API authentication and license verification."""

from __future__ import annotations

import asyncio
from pathlib import Path

from forge_core.models.config import ForgeConfig, Plan, PlanLimits
from forge_core.utils import logger
from forge_core.utils.reporter import check_license


def verify_license(config: ForgeConfig) -> ForgeConfig:
    """Verify license with SaaS API and update plan limits.

    If no auth token is set, runs in free/offline mode.
    """
    if not config.auth_token:
        logger.info("Running in offline mode (no auth token)")
        config.limits = PlanLimits.for_plan(Plan.FREE)
        return config

    # Check with SaaS API
    logger.info("Verifying license with SaaS API...")
    try:
        license_info = asyncio.run(check_license(config))
    except Exception:
        license_info = {}

    if not license_info:
        logger.warn("Could not verify license — falling back to free tier limits")
        config.limits = PlanLimits.for_plan(Plan.FREE)
        return config

    # Update config from license response
    plan_str = license_info.get("plan", "free")
    try:
        plan = Plan(plan_str)
    except ValueError:
        plan = Plan.FREE

    config.limits = PlanLimits.for_plan(plan)
    config.tenant.org_id = license_info.get("org_id", config.tenant.org_id)
    config.tenant.org_name = license_info.get("org_name", config.tenant.org_name)

    # If Pro/Enterprise, use SaaS proxy for AI calls
    if plan in (Plan.PRO, Plan.ENTERPRISE):
        config.ai.use_saas_proxy = True
        if not config.ai.api_key:
            config.ai.api_key = config.auth_token  # SaaS proxy uses auth token
            config.ai.base_url = f"{config.saas_api_url}/api/v1/ai"

    logger.success(f"License verified: {plan.value} plan ({config.tenant.org_name})")
    return config


def save_auth_token(token: str) -> None:
    """Save auth token to ~/.forge-core/auth."""
    auth_dir = Path.home() / ".forge-core"
    auth_dir.mkdir(exist_ok=True)
    auth_file = auth_dir / "auth"
    auth_file.write_text(token, encoding="utf-8")
    auth_file.chmod(0o600)
    logger.success("Auth token saved")


def load_auth_token() -> str:
    """Load auth token from ~/.forge-core/auth."""
    auth_file = Path.home() / ".forge-core" / "auth"
    if auth_file.exists():
        return auth_file.read_text(encoding="utf-8").strip()
    return ""

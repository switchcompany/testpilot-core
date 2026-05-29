"""Pydantic models for configuration and tenant/plan data."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Plan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    BEDROCK = "bedrock"
    OLLAMA = "ollama"
    AUTO = "auto"


class RunMode(str, Enum):
    FULL = "full"
    TARGETED = "targeted"
    ANALYZE_ONLY = "analyze_only"
    ANALYZE_REVIEW = "analyze_review"


class TenantInfo(BaseModel):
    """Multi-tenant identification — populated by SaaS or CLI."""

    org_id: str = ""
    org_name: str = ""
    user_id: str = ""
    project_id: str = ""


class PlanLimits(BaseModel):
    """Usage limits per plan tier."""

    plan: Plan = Plan.FREE
    max_tests_per_month: int = 500
    max_repos: int = 1
    ci_cd_enabled: bool = False
    cross_project_learning: bool = False
    max_parallel_agents: int = 2

    @classmethod
    def for_plan(cls, plan: Plan) -> PlanLimits:
        if plan == Plan.PRO:
            return cls(
                plan=plan,
                max_tests_per_month=-1,  # unlimited
                max_repos=-1,
                ci_cd_enabled=True,
                cross_project_learning=True,
                max_parallel_agents=4,
            )
        elif plan == Plan.ENTERPRISE:
            return cls(
                plan=plan,
                max_tests_per_month=-1,
                max_repos=-1,
                ci_cd_enabled=True,
                cross_project_learning=True,
                max_parallel_agents=8,
            )
        return cls()


class AIConfig(BaseModel):
    """AI provider configuration."""

    provider: AIProvider = AIProvider.AUTO
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.1
    max_tokens: int = 4096
    use_saas_proxy: bool = False  # True = use our API key via SaaS


class ForgeConfig(BaseModel):
    """Top-level engine configuration."""

    # Project
    project_path: Path = Field(default_factory=lambda: Path("."))
    target_coverage: float = 90.0
    max_iterations: int = 10
    mode: RunMode = RunMode.FULL
    target_files: list[str] = Field(default_factory=list)

    # AI
    ai: AIConfig = Field(default_factory=AIConfig)

    # Tenant
    tenant: TenantInfo = Field(default_factory=TenantInfo)

    # Plan
    limits: PlanLimits = Field(default_factory=PlanLimits)

    # Engine
    central_agent_path: str = ""
    knowledge_packs_dir: str = "knowledge-packs"
    cache_dir: str = ".forge-cache"
    prompts_dir: str = ".github/prompts"

    # SaaS
    saas_api_url: str = "https://api.theswitchcompany.online"
    auth_token: str = ""

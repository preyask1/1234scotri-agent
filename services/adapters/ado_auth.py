"""Shared helper for resolving the right read-only ADO PAT per org.

Azure DevOps PATs are normally scoped to a single organization unless created as "All accessible
organizations." Confirmed 2026-09-17: the PAT in this deployment's .env covers acme-data but returns
a clean 401 against AcmeFabricReports — two orgs, two PATs needed. `ADO_PAT_READONLY` remains the
fallback (a PAT that does span multiple orgs, or a deployment with only one org to worry about);
`ADO_PAT_READONLY_<ORG>` overrides it per org when needed.

Used by both adapters/repo_content/live_ado_adapter.py and adapters/mirror_sync/git_adapter.py so
the resolution logic lives in exactly one place.
"""
from __future__ import annotations

import re

from ports.secret_provider import SecretProvider


def _env_suffix_for_org(org: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", org).upper()


def resolve_ado_pat(secrets: SecretProvider, org: str) -> str:
    """Look for an org-specific PAT first (ADO_PAT_READONLY_<ORG>), fall back to the shared one."""
    per_org_var = f"ADO_PAT_READONLY_{_env_suffix_for_org(org)}"
    pat = secrets.get_optional(per_org_var)
    if pat:
        return pat
    return secrets.get("ADO_PAT_READONLY")

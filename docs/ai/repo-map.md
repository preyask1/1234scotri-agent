---
description: "Fabric Git-integration mapping, Entra tenants, and the doc index for this workspace. The authoritative repo/branch/environment/mirror-scope table lives in repo-registry.md, not here."
last-validated-commit: n/a — reference doc for the fictional Acme Retail platform
---

# Repo map — tenants, Fabric Git integration, and the doc index

**For which repos/branches exist, which are mirrored vs read live, and the Dev/UAT/Prod mapping, see
[`repo-registry.md`](repo-registry.md) — the single source of truth.** This file covers what changes
less often: tenants, the Fabric Git-integration list, and where to find each domain doc.

This workspace holds **no product code and no push-capable credential for any product repo**, but it
does hold a **read-only mirror of every Prod branch** the registry lists, refreshed by a separate sync
service. Dev/UAT branches are read live, on demand, never mirrored.

## Fabric Git integration — workspace → repo/branch

Every connection syncs directory `/` (the whole repo root). Workspace ids are deployment-specific; put
yours in this table.

| Fabric workspace | Repo | Branch |
|---|---|---|
| `ACME-Fabric-Prod` | `Acme-PowerBIReports` | `main` |
| `ACME-Fabric-HO-Prod` | `Acme-PowerBIReports` | `hq_live` |
| `ACME-Fabric-Prod-2` | `AcmeFabricReports` | `regional_main` |
| `ACME-Fabric-QA-2` | `AcmeFabricReports` | `main` |
| `ACME-HQ-Prod` / `ACME-Field-Prod` / `ACME-Regional-Prod` | the three new repos | `main` |

**Consequences to respect:**
- **`Acme-PowerBIReports` has two live production branches, not one.** `main` and `hq_live`
  are independent content sets, not environment variants of each other.
- A Fabric workspace with no Git integration cannot be read from the mirror at all; don't assume it
  tracks a dev branch.

## Entra tenants — pick the right one or calls fail confusingly

A common enterprise shape, and the one this code supports: the data plane and the BI plane sit in
different Entra tenants.

| Plane | Tenant | Used for |
|---|---|---|
| **Azure DevOps** | data tenant | ADO Git REST, used only by the sync service to refresh the mirror — **read-only PAT only** |
| **Azure Data Factory** | data tenant | ARM run-history reads via a dedicated service principal in that tenant (`ADF_*` in `.env`), using a federated assertion from the host's identity |
| **Databricks** | data tenant | Databricks SDK, service-principal M2M OAuth (`databricks-query`), via the query governor |
| **Fabric / Power BI** | BI tenant (where Scotri is hosted) | Fabric REST, PBI XMLA (`dax-debug`), via the query governor |

🔴 **A wrong-tenant token returns HTTP 203 with an HTML sign-in page — not a 401.** Always assert
`http=200` **and** that the body is valid JSON or AS-protocol data. Never persist a token to a file:
tokens are minted per call from vault-sourced service-principal credentials.

## Which doc covers what

| Topic | Doc |
|------|-----|
| **Repo/branch/environment registry** | [`repo-registry.md`](repo-registry.md) — check this first, always |
| Fabric / Power BI architecture | [`fabric-architecture.md`](fabric-architecture.md) |
| Fabric conventions (folder map, PBIP formats) | [`fabric-conventions.md`](fabric-conventions.md) |
| Fabric/Databricks tool access | [`fabric-tool-access.md`](fabric-tool-access.md) |
| Databricks architecture | [`databricks-architecture.md`](databricks-architecture.md) |
| Cross-repo lineage | [`lineage-map.md`](lineage-map.md) + [`lineage-graph.yaml`](lineage-graph.yaml) |
| Jira | [`jira-access.md`](jira-access.md) |
| Caller identity and access | [`identity-model.md`](identity-model.md) |
| Retrieval and the lineage graph index | [`retrieval-and-graph-design.md`](retrieval-and-graph-design.md) |

## Guardrail note

Reading is always safe and is this agent's entire job. Writing to any product repo's files — mirrored
or not — or to any live system (Databricks tables, Fabric models, Jira beyond `jira-write`) is never
this agent's job. Because several branches are live-synced to Fabric workspaces, even a hypothetical
write would be a production deployment — one more reason this agent has no write path to them.

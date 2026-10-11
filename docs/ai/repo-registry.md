---
description: "The single source of truth for which repos/branches/workspaces exist, per environment, and how this agent reads each one (persistent mirror vs on-demand live read). Every skill that enumerates repos (fabric-read, adf-databricks-read, impact-analysis, lineage-trace) reads from this table rather than hardcoding repo names, so a repo/branch change is a one-row edit here, not a rewrite of every skill's prose."
last-validated-commit: n/a — hand-maintained registry, update directly as the platform's repo/branch/workspace structure changes
---

# Repo registry (read this before assuming a repo name in any skill)

> The platform described here, **Acme Retail**, is fictional. It is a realistic reference shape for
> an ADF → Databricks → Power BI/Fabric estate mid-migration; swap these rows for your own.

This table is the one place repo/branch/workspace facts live. If a skill's prose names a specific
repo or branch directly instead of saying "per the registry," that skill is out of date — fix the
prose to point here rather than duplicating the fact. Machine-readable twin:
[`../../services/config/repo_registry.yaml`](../../services/config/repo_registry.yaml).

## Read-access rule (applies to every row below, no exceptions)

- **Prod branches are persistently mirrored** at `mirror-active/<repo>/<branch>/`, refreshed by the
  sync service (scheduled + manual, atomic swap) — see `agent-instructions.md`.
- **Where that is on disk:** `mirror-active/` is **not** at the workspace root. It lives under the
  services mirror root (`MIRROR_ROOT`, default `./mirror`, relative to `services/`), i.e.
  `services/mirror/mirror-active/<repo>/<branch>/` — with `mirror-staging/` and `status.json` beside it.
  Use `mirror-list` / `mirror-read --repo-key <key>` (they resolve this for you and check the
  maintenance flag). Layout for the ADF Prod repo: `AcmeAdfProd/main/{pipeline,trigger,dataset,
  linkedService,...}`; ignore the generated ARM-template folder — it is a build output, not source.
- **Dev and UAT branches are read on-demand, live, never mirrored.** A developer's Dev branch changes
  while they work on it, a scheduled mirror would go stale between refreshes, and Dev is someone's
  active workspace, not a standing snapshot for this agent to poll. It is read only when a ticket or
  user explicitly names that environment.
- **Before any Dev/UAT read, check `presence-claim` first.** If someone has an active claim on that
  ticket/branch, surface it before reading their in-progress work.
- **A live Dev/UAT read still goes through the query governor** — rate-limited and logged.
- **Default scope for `impact-analysis` and every debugging skill is Prod**, unless the ticket or the
  user explicitly names Dev or UAT.

## Fabric — new repo structure (live alongside legacy)

Three audience-scoped repos replace the two legacy ones over a transition period. **The mapping from
a legacy repo/branch to a new repo is not assumed** — treat old and new as two independent,
coexisting structures. An empty tree in a new repo means nothing has been published to it yet, not
that a report is missing. None of the three has a `uat` branch, so a UAT question about them has no
tree to read; say so rather than falling back to another branch.

| Repo (`--repo-key`) | ADO org / project | Workspace (Dev) | Workspace (Prod) | Branch (Dev / Prod) | Mirrored? |
|---|---|---|---|---|---|
| `PowerBI_Acme_HQ` (`fabric_hq`) | `acme-data` / `Data-Platform` | `ACME-HQ-Dev` | `ACME-HQ-Prod` | `dev` / `main` | Prod (`main`) only |
| `PowerBI_Acme_Field` (`fabric_stores`) | `acme-data` / `Data-Platform` | `ACME-Field-Dev` | `ACME-Field-Prod` | `dev` / `main` | Prod (`main`) only |
| `PowerBI_Acme_Regional` (`fabric_regional`) | `acme-data` / `Data-Platform` | `ACME-Regional-Dev` | `ACME-Regional-Prod` | `dev` / `main` | Prod (`main`) only |

## Fabric — legacy structure (still live, dual-support)

| Repo (`--repo-key`) | ADO org / project | Live branch(es) | Mirrored? |
|---|---|---|---|
| `Acme-PowerBIReports` (`fabric_core`) | `AcmeFabricReports` / `AcmeFabricReports` | `main` (Prod), `hq_live` (head-office Prod) — two independent live content sets | Both |
| `AcmeFabricReports` (`fabric_secondary`) | `AcmeFabricReports` / `AcmeFabricReports` | `regional_main` (Prod_2); `main` is the QA workspace | `regional_main` only |

## ADF — two separate repos per environment, not two branches of one repo

ADF's Dev and Prod are **entirely separate repos**. Don't look for a `dev` branch inside
`AcmeAdfProd` — it isn't there.

| Environment | Repo | ADO org / project | Branch | Factory | Mirrored? |
|---|---|---|---|---|---|
| Dev | `Data-Platform` (same name as the ADO project) | `acme-data` / `Data-Platform` | `main` | `acme-adf` | No — on-demand live read only |
| Prod | `AcmeAdfProd` | `acme-data` / `Data-Platform` | `main` | `acme-adf-prod` | Yes |

**No UAT tier exists for ADF.**

## Databricks — one repo, two branches, no UAT

| Environment | Repo | ADO org / project | Branch | Catalog | Mirrored? |
|---|---|---|---|---|---|
| Prod | `Acme_Databricks_WS` | `acme-data` / `Data-Platform` | `release_main` | `acme_prod` | Yes |
| Dev | `Acme_Databricks_WS` | `acme-data` / `Data-Platform` | `develop_main` | `acme_dev` | No — on-demand live read only |

**No UAT tier exists for Databricks.** There is no `acme_uat` catalog; a UAT-labelled question about
Databricks data means `acme_dev`.

## What this means for a query/read, concretely

- A ticket about a **Prod** number, model, pipeline, or notebook → read from the mirror.
- A ticket that explicitly says **Dev** or **UAT** → check `presence-claim` first, then read live
  through the query governor.
- A ticket that doesn't say which environment → **assume Prod**, and say so explicitly.
- A repo not listed here → say `not yet in the repo registry — hand back to a human to confirm the
  mapping` rather than guessing at a name.

---
artifact: TASK
schema_version: fitflow-task/v2
task_id: FF-EXAMPLE-001
title: Ejemplo de task vNext
status: READY
task_type: docs
area: docs
scope: docs_tooling
lane: developer
risk: low
priority: P2
created_at: "2026-08-18T00:00:00-03:00"
author_role: developer
baseline:
  revision: NO_COMMIT
  fingerprint_status: captured
  working_tree_fingerprint: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  fingerprint_reason: null
github_issue: null
openspec_change: null
ownership_keys: ["doc:example"]
required_docs: ["docs/SOURCE_OF_TRUTH.md"]
---

# Objetivo

Demostrar el formato de una task v2 sin crear trabajo real.

## Scope

- `.ai/templates/`

## Fuera de scope

- codigo de producto

## Criterios de aceptacion

| ID | Criterio | Evidencia esperada |
| --- | --- | --- |
| AC-1 | El ejemplo usa terminologia v2 | inspeccion |

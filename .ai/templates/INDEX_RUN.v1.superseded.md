---
artifact: INDEX_RUN
schema_version: fitflow-index-run/v1
task_id: "<TASK-ID>"
status: superseded
machine_context: false
superseded_by: .ai/backlog/vnext.yaml#FF-AI-VNEXT-011
created_at: "<ISO-8601>"
baseline_revision: "<revision>"
working_tree_fingerprint: "sha256:<hash>"
author_role: indexer
run_id: "<index-run-id>"
scope: backend
mode: incremental
---

# Versiones

| Componente | Versión/hash |
| --- | --- |
| discovery | `<version>` |
| repo-packager | `<version|UNAVAILABLE>` |
| Repomix | `<version>` |
| LlamaIndex | `<version>` |
| embedding | `EmbeddingGemma-300M:<revision>` |
| Qdrant | `<version>` |

## Inputs y outputs

- dirty paths: `<manifest>`
- inventory: `<path + hash>`
- class graph: `<path + hash>`
- snapshot: `<path + hash>`
- collection: `fitflow_context_v1`

## Conteos

| Descubiertos | Parsed | Unparsed | Insert | Update | Delete | Errors |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Verificación

| Check | Estado | Evidencia |
| --- | --- | --- |
| schema/hashes | PASS/FAIL | <detalle> |
| filters | PASS/FAIL | <detalle> |
| smoke queries | PASS/FAIL | <detalle> |

## Promoción

Historico: `working_only|pending_developer_acceptance|promoted`.

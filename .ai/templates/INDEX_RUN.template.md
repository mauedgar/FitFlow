---
artifact: INDEX_RUN
schema_version: fitflow-index-run/v1
task_id: "<TASK-ID>"
status: PASS
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

`working_only|pending_human_acceptance|promoted`.

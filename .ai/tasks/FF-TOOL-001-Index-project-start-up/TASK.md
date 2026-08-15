---
id: FF-TOOL-001
title: Poner en marcha Project Index v1
status: Ready
priority: Medium
area: ai-tooling
execution_lane: human
type: tooling
baseline_revision: pending
---

# Objetivo

Construir un Project Index local, reproducible e incremental que permita
consultar la estructura de FitFlow sin convertir el índice en fuente de verdad
ni definir todavía el Context Bundle definitivo.

# Scope

- project-index.toml
- tooling/scripts del indexador
- .index/ como output derivado
- discovery
- manifest
- AST Python
- símbolos
- imports
- relaciones estructurales iniciales
- consultas locales básicas

# Fuera de scope

- MCP
- Context Bundle v1 definitivo
- autonomía de agentes
- EmbeddingGemma obligatorio
- vector DB pesada
- reemplazar navegación de Codex/Aider
- cambios de dominio FitFlow

# Etapa 1 — Discovery

Leer project-index.toml.

Generar manifest de archivos incluidos/excluidos.

Registrar:

- repository revision;
- generated_at;
- paths;
- hashes;
- lenguaje;
- exclusions.

# Etapa 2 — Symbols

Para Python extraer:

- module
- class
- function
- async function
- method
- property
- decorator
- imports
- type annotations
- docstring
- path
- start_line
- end_line

# Etapa 3 — Relations

Normalizar cuando sea posible:

- imports
- contains
- inherits
- references
- uses_schema
- persists
- belongs_to

Cada relación debe conservar fuente/confidence cuando no sea determinista.

# Etapa 4 — Storage

Output regenerable dentro de `.index/`.

Como mínimo:

.index/
  metadata.json
  manifest.json
  symbols.jsonl
  relations.jsonl

Puede incorporarse SQLite posteriormente si simplifica las consultas.

# Etapa 5 — Query mínima

Implementar una interfaz local capaz de responder al menos:

- find symbol
- find references/dependents básicos
- buscar por nombre/texto
- obtener metadata de un símbolo

La salida puede evolucionar durante esta etapa.

# Etapa 6 — Medición

Probar consultas FitFlow reales:

- dónde se evita overbooking
- qué valida membership
- qué depende de ClassSchedule
- dónde se representa Front Desk
- dónde se determina capacity

Medir:

- candidate recall
- top results
- tiempo
- volumen de salida
- archivos que Codex todavía debe explorar

# Semántica

No habilitar EmbeddingGemma por defecto.

Después de tener baseline estructural/textual, comparar:

A = symbols + relations + textual
B = A + semantic

Mantener semantic sólo si mejora recuperación de forma medible.

# Definition of Done v1

- [ ] configuración versionada
- [ ] outputs regenerables
- [ ] exclusiones correctas
- [ ] snapshot ligado a Git revision
- [ ] incremental o estrategia clara de invalidación
- [ ] símbolos consultables
- [ ] relaciones consultables
- [ ] pruebas con queries FitFlow
- [ ] índice no modifica el proyecto
- [ ] ningún agente depende todavía de MCP
- [ ] hallazgos para futuro Context Bundle documentados
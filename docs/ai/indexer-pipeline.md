# Project Index - Pipeline estructural y semantico v2

**Estado:** Activo como diseno de tooling  
**Relacion con producto:** no bloqueante para el MVP

## 1. Proposito

Construir una memoria tecnica local, incremental y reutilizable que permita a agentes potentes localizar rapidamente codigo y relaciones sin repetir exploraciones completas. El indice no reemplaza al agente ni al codigo.

## 2. Principio

```text
Git repository
  -> snapshot/manifest
  -> AST + symbols
  -> normalized relations
  -> docstrings / docs metadata
  -> optional semantic chunks + embeddings
  -> local storage
  -> small query tools
  -> Context Package
  -> agent reads real source
```

## 3. Responsabilidades v1

1. Discovery reproducible del repo y revision Git.
2. Extraer simbolos Python mediante AST.
3. Extraer imports, decorators, tipos, docstrings y rangos de lineas.
4. Normalizar relaciones; conservar pyreverse donde aporte informacion real.
5. Asociar metadatos de capa: router/schema/service/crud/model/test/docs.
6. Indexar docs canonicos y ADRs activos con procedencia.
7. Permitir actualizacion incremental por hash/git diff.
8. Producir `Context Package` limitado por presupuesto.

## 4. Capa semantica

EmbeddingGemma queda como **canal opcional**. Se activa si las pruebas reales muestran que mejora recall/precision frente a simbolos, grafo y busqueda textual.

No es requisito de AiderDesk ni de RepoMap. Puede ejecutarse bajo demanda y sus vectores permanecen separados del dominio del producto.

Reglas de chunking:
- respetar modulo/clase/metodo/funcion/schema/model/test;
- no cortar arbitrariamente funciones pequenas;
- enriquecer con metadata estructural;
- no embeddear archivos completos por comodidad;
- no duplicar codigo generado o dependencias externas.

## 5. Canales de recuperacion

- **Symbol:** maxima precision para nombres reales.
- **Graph:** relaciones/dependencias/callers/dependents cuando puedan inferirse.
- **Semantic:** conceptos equivalentes cuando el wording difiere.
- **Textual:** literal/regex/identificadores y mensajes.
- **Docs:** ADRs y arquitectura, siempre marcados como documentacion y no como prueba de implementacion.

El ranking debe medirse con consultas reales de FitFlow, no fijarse por intuicion.

## 6. Almacenamiento

Mantenerlo local y regenerable. Un prototipo puede usar SQLite + archivos JSON y un vector store local solo si la capa semantica lo necesita.

Artefactos sugeridos:

```text
.index/fitflow/
├── metadata.json
├── manifest.json
├── symbols.json
├── relations.json
├── architecture.json
├── repo_summary.json
├── index.db
└── vectors/              # opcional
```

La carpeta es derivada y debe poder borrarse/regenerarse.

## 7. Query tools

Contrato inicial:
- `find_symbol(query, scope)`
- `get_symbol(id)`
- `find_relations(id, type?)`
- `get_dependencies(id)`
- `get_dependents(id)`
- `search_context(query, scope, budget)`
- `get_context_bundle(query, scope, budget)`

Las tools deben devolver rutas y rangos verificables; no grandes narrativas.

## 8. Integracion con Codex

El indice se expone como herramientas locales/MCP cuando la implementacion este estable. Flujo:

```text
Codex
  -> consulta indice
  -> recibe candidatos/bundle
  -> lee archivos reales
  -> implementa
  -> valida
```

La documentacion del proyecto y AGENTS fijan limites de autonomia; el indice no toma decisiones arquitectonicas.

## 9. Relacion con Aider RepoMap

No se intentara convertir el formato interno de RepoMap de Aider en contrato compartido.

- AiderDesk puede usar RepoMap nativo como hint runtime.
- Project Index produce `repo_summary` neutral y reutilizable.
- Si mas adelante existe una forma estable de importar/exportar mapas, se integra como adaptador, no como dependencia central.

## 10. Exclusiones

Excluir `.venv`, `backend/.venv_backend`, `node_modules`, `.git`, `__pycache__`, `docs/archive`, secretos, `.env*`, binarios, build/dist y artefactos generados.

## 11. Criterios de exito

- regenerable desde una revision Git;
- incremental por archivo/simbolo;
- encuentra servicios/entidades relevantes en consultas reales;
- conserva relaciones suficientes para expandir contexto;
- bundle de salida compacto y con provenance;
- no introduce infraestructura pesada;
- nunca sustituye la lectura del codigo antes de editar.

## 12. Testing y tasks

El indice puede indexar tests activos como evidencia estructural, pero no debe tratar un test como prueba de un comportamiento que no cubre. Los bundles deben registrar revision Git. La integracion MCP se estudia despues de estabilizar Codex, validation baseline e indice; no es prerequisito de v1.

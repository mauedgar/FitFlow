# MCP - candidato de integracion futura

**Estado:** Study later / no implementar aun

MCP (Model Context Protocol) es una interfaz estandar para conectar modelos con herramientas y fuentes de contexto.

Para FitFlow, el candidato principal es exponer funciones del Project Index, por ejemplo:
- `find_symbol`
- `get_symbol`
- `find_relations`
- `get_dependencies`
- `get_dependents`
- `search_context`
- `get_context_bundle`

MCP no ahorra tokens por si solo. Puede ahorrar si una tool precisa devuelve evidencia compacta en lugar de obligar al agente a explorar muchos archivos.

Orden acordado:
1. Codex funcional;
2. pytest/validation baseline;
3. Project Index suficientemente estable;
4. evaluar MCP;
5. implementar solo si mejora precision, mantenibilidad o costo de contexto.

Ver prompt de investigacion en `.ai/prompts/MCP_FUTURE_RESEARCH.prompt.md`.

# Prompt - Investigar MCP para FitFlow (futuro, no implementar)

Quiero investigar si MCP (Model Context Protocol) aporta valor futuro a FitFlow, pero NO quiero implementarlo todavia.

Precondiciones:
- primero Codex debe estar funcional;
- debe existir un baseline pytest confiable;
- el Project Index debe estar suficientemente estable.

Contexto:
El Project Index previsto puede ofrecer:
- `find_symbol`
- `get_symbol`
- `find_relations`
- `get_dependencies`
- `get_dependents`
- `search_context`
- `get_context_bundle`

El indice combina estructura/simbolos/grafo y, solo si las mediciones lo justifican, semantica con embeddings. Su salida debe ser compacta y ligada a revision Git. Codex siempre verifica el archivo real antes de editar.

Investiga usando documentacion oficial actual de OpenAI para Codex/MCP y, para el protocolo MCP, fuentes primarias/oficiales.

Quiero un informe que responda:
1. que problema resolveria MCP en ESTE diseño;
2. que NO resolveria;
3. si puede reducir tokens o solo cambiar la interfaz;
4. coste de contexto de registrar muchas tools;
5. seguridad/permisos;
6. transporte/proceso local recomendado;
7. contrato ideal de tools y payloads compactos;
8. como versionar/cachear resultados por Git revision;
9. como evitar que MCP convierta el indice derivado en source of truth;
10. comparativa: MCP vs ejecutar herramientas locales directamente desde Codex;
11. MVP minimo del servidor MCP si finalmente se justifica;
12. criterios medibles para decidir GO / NO-GO.

No generes codigo de implementacion salvo pseudocodigo breve. El objetivo es tomar la decision arquitectonica, no construir el servidor.

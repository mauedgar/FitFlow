import json
import subprocess

# ==========================================
# CONFIGURACIÓN GENERAL (Modifica con tus datos)
# ==========================================
REPO = "mauedgar/fitflow"  # Cambia por tu repositorio real
PROJECT_NUMBER = 1                 # El número de tu GitHub Project (ej: #1)

# Estructura del Backlog Inicial Rectificado de FitFlow
TASKS = [
    {
        "id": "FF-AI-000",
        "title": "Congelar contratos de la arquitectura y set dorado inicial",
        "scope": "mixed", "risk": 2, "reasoning": "medium", "executor": "coderA",
        "objective": "Definir la fuente de verdad (SOURCE_OF_TRUTH), exclusiones de carpetas y esquemas base.",
        "refs": "['architecture#1.0', 'domain#core']",
        "budget": 4000,
        "evidence": "- Fichero de configuración congelado\n- JSON schema validado",
        "acceptance": "- El script de validación corre localmente sin errores\n- Documentos normativos separados de explicaciones humanas"
    },
    {
        "id": "FF-AI-001",
        "title": "Implementar CLI de contexto nativo (Node/TS)",
        "scope": "mixed", "risk": 4, "reasoning": "high", "executor": "coderA-strong",
        "objective": "Generar paquetes de contexto emitiendo XML estructurado mediante Repomix.",
        "refs": "['architecture#section-3', 'ADR-002']",
        "budget": 8000,
        "evidence": "- CLI ejecutable en env_tools\n- XML generado con etiquetas claras",
        "acceptance": "- Soporta flags --scope backend|frontend|mixed de forma estricta\n- No importa librerías del runtime del backend"
    },
    {
        "id": "FF-AI-002",
        "title": "Desarrollar manifiesto estructural y hashes incrementales",
        "scope": "backend", "risk": 3, "reasoning": "medium", "executor": "coderA",
        "objective": "Implementar extractor AST de Python y mapeo de encabezados Markdown con hashes de estado.",
        "refs": "['architecture#section-5']",
        "budget": 6000,
        "evidence": "- Módulo python_ast en env_tools\n- Manifiesto JSON generado tras confirmación",
        "acceptance": "- Detecta cambios en las firmas de funciones sin reindexar todo el repositorio"
    }
    # NOTA: Puedes agregar de la FF-AI-003 a la FF-AI-008 siguiendo este mismo patrón de diccionario de Python
]

def run_command(cmd):
    """Ejecuta comandos del sistema de forma segura y retorna la salida."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def create_fitflow_backlog():
    print("🚀 Iniciando migración masiva a GitHub Projects...")
    
    for task in TASKS:
        print(f"\n📦 Creando {task['id']}: {task['title']}...")
        
        # 1. Construir el cuerpo en Markdown (Tu contrato de tarea estricto)
        body_content = f"""## 🎯 Objective
{task['objective']}

## 📜 Authority Refs
- {task['refs']}

## ⚙️ Execution Parameters
- **Baseline Revision:** `PENDING_SHA`
- **Context Budget Tokens:** {task['budget']}
- **Max Context Expansions:** 2
- **Max Implementation Retries:** 2

## 🔍 Evidence & Acceptance
### Evidence Required
{task['evidence']}

### Acceptance Criteria
{task['acceptance']}

### 🛑 Stop Conditions
- [ ] Crecimiento desmedido del alcance (scope growth)
- [ ] Conflicto directo con la doctrina documental activa
- [ ] Detección de una revisión obsoleta o obsoleta (stale revision)
"""

        # 2. Crear el Issue en el repositorio usando GitHub CLI
        issue_title = f"{task['id']}: {task['title']}"
        create_issue_cmd = [
            "gh", "issue", "create",
            "--repo", REPO,
            "--title", issue_title,
            "--body", body_content,
            "--label", "task"
        ]
        issue_url = run_command(create_issue_cmd)
        print(f"✅ Issue creado: {issue_url}")

        # 3. Vincular el Issue al proyecto Kanban
        add_to_project_cmd = [
            "gh", "project", "item-add", str(PROJECT_NUMBER),
            "--owner", REPO.split("/")[0],
            "--url", issue_url,
            "--format", "json"
        ]
        # Capturamos el ID del elemento en el proyecto para poder asignarle campos personalizados después
        item_output = json.loads(run_command(add_to_project_cmd))
        item_id = item_output["id"] if "id" in item_output else item_output.get("itemId")

        # 4. Asignar los Custom Fields en el tablero de GitHub Projects
        owner = REPO.split("/")[0]
        
        # Configurar Scope
        run_command(["gh", "project", "item-edit", str(PROJECT_NUMBER), "--id", item_id, "--owner", owner, "--field", "Scope", "--value", task["scope"]])
        # Configurar Risk Score
        run_command(["gh", "project", "item-edit", str(PROJECT_NUMBER), "--id", item_id, "--owner", owner, "--field", "Risk Score", "--value", str(task["risk"])])
        # Configurar Executor Class
        run_command(["gh", "project", "item-edit", str(PROJECT_NUMBER), "--id", item_id, "--owner", owner, "--field", "Executor Class", "--value", task["executor"]])
        # Configurar Reasoning Level
        run_command(["gh", "project", "item-edit", str(PROJECT_NUMBER), "--id", item_id, "--owner", owner, "--field", "Reasoning Level", "--value", task["reasoning"]])
        
        print(f"📊 Campos asignados correctamente en el tablero para {task['id']}.")

    print("\n🎉 ¡Migración completa! Ya tienes tu entorno Scrum optimizado para tu SaaS con IA sin rastro de Jira.")

if __name__ == "__main__":
    create_fitflow_backlog()
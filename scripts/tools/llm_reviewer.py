import subprocess
import sys
import os
from openai import OpenAI

# Inicializar el cliente (Asegúrate de tener OPENAI_API_KEY en tus variables globales)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_git_diff():
    """Obtiene el código exacto que modificaste y estás intentando guardar."""
    cmd = ["git", "diff", "--cached"]
    return subprocess.run(cmd, capture_output=True, text=True).stdout

def review_code_with_llm(diff_content):
    if not diff_content.strip():
        return True

    # El prompt del sistema con la "Doctrina Normativa" de FitFlow
    system_prompt = """
    Eres el Linter/Revisor de código de Inteligencia Artificial para el SaaS 'FitFlow'.
    Tu objetivo es inspeccionar el código modificado (Git Diff) del programador y evaluar si viola la arquitectura.
    Reglas estrictas de FitFlow:
    1. En Python, la estructura debe respetar estrictamente: Router -> Service -> CRUD -> Model. No mezclar lógica de base de datos en los routers.
    2. Las llamadas a LLMs deben incluir manejo de excepciones y límites de tokens obligatorios.
    3. En TypeScript, no se permiten tipos 'any'. Todo debe estar estrictamente tipado.
    
    Responde ÚNICAMENTE en formato JSON con la siguiente estructura:
    {
      "status": "APPROVED" o "REJECTED",
      "reason": "Explicación detallada del motivo si fue rechazado, o un mensaje de éxito si fue aprobado."
    }
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Usamos un modelo rápido y económico para linters locales
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analiza el siguiente cambio de código:\n\n{diff_content}"}
            ],
            temperature=0.1 # Temperatura baja para que sea determinista
        )
        
        # Procesar respuesta
        import json
        result = json.loads(response.choices[0].message.content)
        
        if result["status"] == "REJECTED":
            print("\n🤖 [FitFlow LLM Skill - RECHAZADO]:")
            print(f"⚠️ {result['reason']}\n")
            return False
        else:
            print("\n🤖 [FitFlow LLM Skill - APROBADO]: El código cumple con las directrices de FitFlow.")
            return True
            
    except Exception as e:
        print(f"⚠️ Alerta: No se pudo conectar con la Skill LLM ({str(e)}). Permitiendo commit por defecto.")
        return True

if __name__ == "__main__":
    diff = get_git_diff()
    if not review_code_with_llm(diff):
        sys.exit(1) # Cancela el commit si el LLM encuentra fallas graves
    sys.exit(0)

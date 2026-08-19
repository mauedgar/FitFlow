import sys
import re

def validate_commit_and_contract(commit_msg):
    # 1. Validar formato de Conventional Commits
    pattern = r"^(feat|fix|docs|style|refactor|perf|test|chore)(\(.+\))?: .{5,}"
    if not re.match(pattern, commit_msg):
        print("❌ [FitFlow Skill ERROR]: El mensaje no cumple con Conventional Commits.")
        print("💡 Ejemplo válido: 'feat: agregar streaming de respuestas de la IA'")
        return False

    # 2. Validar si el commit intenta cerrar un issue de FitFlow de forma correcta
    if "fixes #" in commit_msg.lower() or "closes #" in commit_msg.lower():
        print("✨ [FitFlow Skill]: Vínculo automático a GitHub Projects detectado.")
    return True

if __name__ == "__main__":
    # Git pasa el mensaje del commit temporal en un archivo cuyo path es el primer argumento
    commit_msg_filepath = sys.argv[1]
    with open(commit_msg_filepath, "r") as f:
        msg = f.read().strip()

    if not validate_commit_and_contract(msg):
        sys.exit(1)  # Cancela el commit

    print("✅ [FitFlow Skill]: Formato y contrato validados correctamente.")
    sys.exit(0)  # Permite el commit

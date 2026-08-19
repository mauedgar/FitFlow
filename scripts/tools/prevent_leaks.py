import subprocess
import sys
import re

# Patrones para OpenAI, Anthropic, HuggingFace y cadenas genéricas de conexión
LEAK_PATTERNS = [
    r"sk-[a-zA-Z0-9]{48}",          # OpenAI API Keys
    r"sk-ant-api03-[a-zA-Z0-9_-]{95}", # Anthropic Claude
    r"hf_[a-zA-Z0-9]{34}",          # Hugging Face
    r"postgres://[^:]+:[^@]+@[^/]+/[^?]+" # Cadenas de Base de Datos
]

def check_staged_files():
    # Obtener la lista de archivos que vas a incluir en el commit
    files = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True).stdout.splitlines()
    
    for file_path in files:
        if not file_path or ".env" in file_path:  # Ignorar el archivo .env legítimo
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                for pattern in LEAK_PATTERNS:
                    if re.search(pattern, content):
                        print(f"❌ [FitFlow Leak Skill]: ¡Se detectó una posible clave expuesta en {file_path}!")
                        print("⚠️ Cancela el commit, mueve la clave a tu archivo .env e inténtalo de nuevo.")
                        return False
        except Exception:
            continue
    return True

if __name__ == "__main__":
    if not check_staged_files():
        sys.exit(1) # Bloquea el commit
    print("🛡️ [FitFlow Leak Skill]: No se detectaron credenciales expuestas.")
    sys.exit(0)
